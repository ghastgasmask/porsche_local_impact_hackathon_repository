# Eto Cash Flow Predictor...
# Прогнозирование денежных потоков с учетом задержек клиринга

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json

class CashFlowPredictor:
    # Прогнозирует денежные потоки и выявляет кассовые разрывы
    
    def __init__(self, accounts_df, transactions_df, scheduled_payments_df, 
                 expected_inflows_df, holidays_df, clearing_rules_path='data/clearing_rules.json'):
        # Инициализация модуля прогнозирования
        self.accounts = accounts_df.copy()
        self.transactions = transactions_df.copy()
        self.scheduled_payments = scheduled_payments_df.copy()
        self.expected_inflows = expected_inflows_df.copy()
        self.holidays = holidays_df.copy()
        
        # Загружаем правила задержек
        with open(clearing_rules_path, 'r', encoding='utf-8') as f:
            self.clearing_rules = json.load(f)
        
        # Преобразуем даты
        self.transactions['datetime'] = pd.to_datetime(self.transactions['datetime'])
        self.scheduled_payments['due_date'] = pd.to_datetime(self.scheduled_payments['due_date'])
        self.expected_inflows['sent_date'] = pd.to_datetime(self.expected_inflows['sent_date'])
        self.expected_inflows['expected_arrival_date'] = pd.to_datetime(self.expected_inflows['expected_arrival_date'])
        self.holidays['date'] = pd.to_datetime(self.holidays['date'])
    
    def is_banking_day(self, date):
        # Проверяет, является ли день банковским (рабочим)
        # Проверяем выходные
        if date.weekday() >= 5:  # Суббота или воскресенье
            return False
        
        # Проверяем праздники
        date_str = date.strftime('%Y-%m-%d')
        if date_str in self.holidays['date'].astype(str).values:
            holiday_row = self.holidays[self.holidays['date'].astype(str) == date_str].iloc[0]
            return holiday_row['is_banking_day']
        
        return True
    
    def get_next_banking_day(self, date):
        # Возвращает следующий банковский день после указанной даты
        next_day = date + timedelta(days=1)
        while not self.is_banking_day(next_day):
            next_day += timedelta(days=1)
        return next_day
    
    def calculate_actual_arrival_date(self, sent_date, payment_system):
        # Рассчитывает реальную дату поступления с учетом выходных и праздников
        # Получаем задержку из правил
        delay_info = self.clearing_rules.get(payment_system, {"min_days": 1, "max_days": 1})
        delay_days = delay_info['max_days']  # Берем максимальную задержку для безопасности
        
        # Добавляем задержку
        arrival_date = sent_date + timedelta(days=delay_days)
        
        # Если попадает на выходной/праздник, переносим на следующий рабочий день
        while not self.is_banking_day(arrival_date):
            arrival_date += timedelta(days=1)
        
        return arrival_date
    
    def predict_daily_cash_flow(self, days_ahead=30):
        # Прогнозирует денежные потоки на каждый день
        #
        # Возвращает DataFrame с колонками:
        # - date: дата
        # - inflows: ожидаемые поступления
        # - outflows: ожидаемые расходы
        # - net_flow: чистый поток (inflows - outflows)
        # - cumulative_flow: накопительный поток
        today = datetime.now().date()
        forecast_dates = [today + timedelta(days=i) for i in range(days_ahead)]
        
        forecast = []
        
        for date in forecast_dates:
            date_dt = pd.Timestamp(date)
            
            # 1. ОЖИДАЕМЫЕ ПОСТУПЛЕНИЯ на эту дату
            # Смотрим expected_inflows с этой датой
            inflows_on_date = self.expected_inflows[
                self.expected_inflows['expected_arrival_date'].dt.date == date
            ]['amount'].sum()
            
            # 2. ЗАПЛАНИРОВАННЫЕ ПЛАТЕЖИ на эту дату
            outflows_on_date = self.scheduled_payments[
                self.scheduled_payments['due_date'].dt.date == date
            ]['amount'].sum()
            
            # 3. СРЕДНЯЯ ДНЕВНАЯ АКТИВНОСТЬ (из истории)
            # Берем транзакции за тот же день недели из истории
            weekday = date_dt.weekday()
            historical_same_weekday = self.transactions[
                self.transactions['datetime'].dt.weekday == weekday
            ]
            
            # Средние поступления
            avg_inflows = historical_same_weekday[
                historical_same_weekday['direction'] == 'inflow'
            ]['amount'].mean() if len(historical_same_weekday) > 0 else 0
            
            # Средние расходы
            avg_outflows = historical_same_weekday[
                historical_same_weekday['direction'] == 'outflow'
            ]['amount'].mean() if len(historical_same_weekday) > 0 else 0
            
            # Итоговые потоки = запланированные + средние
            total_inflows = inflows_on_date + (avg_inflows * 0.3)  # 30% от средней активности добавляем
            total_outflows = outflows_on_date + (avg_outflows * 0.3)
            
            net_flow = total_inflows - total_outflows
            
            forecast.append({
                'date': date,
                'inflows': round(total_inflows, 2),
                'outflows': round(total_outflows, 2),
                'net_flow': round(net_flow, 2),
                'is_banking_day': self.is_banking_day(date_dt)
            })
        
        df = pd.DataFrame(forecast)
        
        # Добавляем накопительный поток
        df['cumulative_flow'] = df['net_flow'].cumsum()
        
        return df
    
    def identify_cash_gaps(self, days_ahead=30, accounts_df=None):
        # Выявляет кассовые разрывы (дни когда денег не хватит)
        #
        # Возвращает список дней с потенциальными проблемами
        # Получаем прогноз
        forecast_df = self.predict_daily_cash_flow(days_ahead)
        
        # Текущий общий баланс
        if accounts_df is None:
            accounts_df = self.accounts
        
        total_balance = accounts_df['current_balance'].sum()
        
        gaps = []
        running_balance = total_balance
        
        for _, row in forecast_df.iterrows():
            # Обновляем баланс
            running_balance += row['net_flow']
            
            # Определяем минимальный необходимый резерв (10% от текущего баланса)
            min_reserve = total_balance * 0.1
            
            # Проверяем на кассовый разрыв
            if running_balance < min_reserve:
                severity = 'CRITICAL' if running_balance < 0 else 'WARNING'
                gap_amount = min_reserve - running_balance
                
                gaps.append({
                    'date': row['date'],
                    'forecasted_balance': round(running_balance, 2),
                    'required_minimum': round(min_reserve, 2),
                    'gap_amount': round(gap_amount, 2),
                    'severity': severity,
                    'inflows': row['inflows'],
                    'outflows': row['outflows'],
                    'net_flow': row['net_flow'],
                    'is_banking_day': row['is_banking_day']
                })
        
        return pd.DataFrame(gaps)
    
    def analyze_clearing_delays(self):
        # Анализирует влияние задержек клиринга на потоки
        #
        # Показывает сколько денег "застряло" в разных платежных системах
        # Группируем ожидаемые поступления по платежным системам
        delays_by_system = []
        
        for system in self.expected_inflows['payment_system'].unique():
            system_inflows = self.expected_inflows[
                self.expected_inflows['payment_system'] == system
            ]
            
            # Сколько денег в пути
            total_in_transit = system_inflows[
                system_inflows['status'] == 'in_transit'
            ]['amount'].sum()
            
            # Сколько задержано
            total_delayed = system_inflows[
                system_inflows['status'] == 'delayed'
            ]['amount'].sum()
            
            # Средняя задержка
            avg_delay = system_inflows['actual_delay_days'].mean()
            
            # Правила этой системы
            rules = self.clearing_rules.get(system, {})
            expected_delay = rules.get('max_days', 1)
            
            delays_by_system.append({
                'payment_system': system,
                'total_in_transit': round(total_in_transit, 2),
                'total_delayed': round(total_delayed, 2),
                'num_transactions': len(system_inflows),
                'avg_delay_days': round(avg_delay, 2),
                'expected_delay_days': expected_delay,
                'delay_difference': round(avg_delay - expected_delay, 2)
            })
        
        return pd.DataFrame(delays_by_system)
    
    def get_weekly_forecast_summary(self):
        # Возвращает еженедельный прогноз в удобном формате
        forecast_df = self.predict_daily_cash_flow(days_ahead=30)
        
        # Группируем по неделям
        forecast_df['week'] = pd.to_datetime(forecast_df['date']).dt.isocalendar().week
        
        weekly_summary = forecast_df.groupby('week').agg({
            'inflows': 'sum',
            'outflows': 'sum',
            'net_flow': 'sum'
        }).reset_index()
        
        weekly_summary['week_label'] = [f"Неделя {i+1}" for i in range(len(weekly_summary))]
        
        return weekly_summary
    
    def predict_account_specific_flow(self, account_id, days_ahead=14):
        # Прогноз для конкретного счета
        # Находим информацию о счете
        account = self.accounts[self.accounts['account_id'] == account_id].iloc[0]
        currency = account['currency']
        current_balance = account['current_balance']
        
        # Прогноз по дням
        forecast = []
        today = datetime.now().date()
        
        for i in range(days_ahead):
            date = today + timedelta(days=i)
            date_dt = pd.Timestamp(date)
            
            # Ожидаемые поступления на этот счет
            inflows = self.expected_inflows[
                (self.expected_inflows['to_account'] == account_id) &
                (self.expected_inflows['expected_arrival_date'].dt.date == date) &
                (self.expected_inflows['currency'] == currency)
            ]['amount'].sum()
            
            # Запланированные платежи с этого счета
            outflows = self.scheduled_payments[
                (self.scheduled_payments['account_from'] == account_id) &
                (self.scheduled_payments['due_date'].dt.date == date) &
                (self.scheduled_payments['currency'] == currency)
            ]['amount'].sum()
            
            # Средняя активность
            historical = self.transactions[
                (self.transactions['account_id'] == account_id) &
                (self.transactions['currency'] == currency)
            ]
            
            avg_daily_inflow = historical[historical['direction'] == 'inflow']['amount'].mean() if len(historical) > 0 else 0
            avg_daily_outflow = historical[historical['direction'] == 'outflow']['amount'].mean() if len(historical) > 0 else 0
            
            total_inflows = inflows + (avg_daily_inflow * 0.2)
            total_outflows = outflows + (avg_daily_outflow * 0.2)
            
            net_flow = total_inflows - total_outflows
            current_balance += net_flow
            
            forecast.append({
                'date': date,
                'inflows': round(total_inflows, 2),
                'outflows': round(total_outflows, 2),
                'net_flow': round(net_flow, 2),
                'forecasted_balance': round(current_balance, 2)
            })
        
        return pd.DataFrame(forecast)
    
    def generate_gap_solutions(self, gaps_df):
        # Генерирует решения для выявленных кассовых разрывов
        if len(gaps_df) == 0:
            return pd.DataFrame()
        
        solutions = []
        
        for _, gap in gaps_df.iterrows():
            date = gap['date']
            gap_amount = gap['gap_amount']
            severity = gap['severity']
            
            # Предлагаем решения в зависимости от серьезности
            if severity == 'CRITICAL':
                solutions.append({
                    'gap_date': date,
                    'gap_amount': gap_amount,
                    'solution': 'URGENT_TRANSFER',
                    'action': f'Срочно перевести ${gap_amount:,.0f} на счета за 1-2 дня до {date}',
                    'source': 'Использовать резервы или краткосрочный кредит',
                    'priority': 1
                })
            else:
                solutions.append({
                    'gap_date': date,
                    'gap_amount': gap_amount,
                    'solution': 'PLANNED_TRANSFER',
                    'action': f'Запланировать перевод ${gap_amount:,.0f} до {date}',
                    'source': 'Перераспределить с счетов с избытком',
                    'priority': 2
                })
        
        return pd.DataFrame(solutions)
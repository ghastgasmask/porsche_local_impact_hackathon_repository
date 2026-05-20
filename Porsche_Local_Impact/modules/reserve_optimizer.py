# Модуль 4: Reserve Optimizer
# Оптимизация резервов ликвидности

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from scipy import stats

class ReserveOptimizer:
    # Оптимизирует размер резервов на основе статистического анализа
    
    def __init__(self, accounts_df, transactions_df, scheduled_payments_df, expected_inflows_df):
        # Инициализация оптимизатора резервов
        self.accounts = accounts_df.copy()
        self.transactions = transactions_df.copy()
        self.scheduled_payments = scheduled_payments_df.copy()
        self.expected_inflows = expected_inflows_df.copy()
        
        # Преобразуем даты
        self.transactions['datetime'] = pd.to_datetime(self.transactions['datetime'])
        self.scheduled_payments['due_date'] = pd.to_datetime(self.scheduled_payments['due_date'])
        
        # Параметры для расчетов
        self.confidence_level = 0.99  # 99% уверенности
        self.deposit_rate = 0.04  # 4% годовых
    
    def calculate_historical_volatility(self, account_id=None, days=90):
        # Рассчитывает волатильность денежных потоков
        #
        # Волатильность = насколько сильно "скачут" денежные потоки
        # Фильтруем транзакции
        if account_id:
            transactions = self.transactions[self.transactions['account_id'] == account_id]
        else:
            transactions = self.transactions
        
        # Берем последние N дней
        cutoff_date = datetime.now() - timedelta(days=days)
        recent_transactions = transactions[transactions['datetime'] >= cutoff_date]
        
        if len(recent_transactions) == 0:
            return {'daily_std': 0, 'daily_mean': 0, 'volatility_coefficient': 0}
        
        # Группируем по дням
        daily_flows = recent_transactions.groupby(
            recent_transactions['datetime'].dt.date
        ).agg({
            'amount': lambda x: x[recent_transactions.loc[x.index, 'direction'] == 'inflow'].sum() - 
                               x[recent_transactions.loc[x.index, 'direction'] == 'outflow'].sum()
        }).reset_index()
        daily_flows.columns = ['date', 'net_flow']
        
        # Статистика
        daily_std = daily_flows['net_flow'].std()
        daily_mean = daily_flows['net_flow'].mean()
        
        # Коэффициент волатильности (std / mean)
        volatility_coefficient = abs(daily_std / daily_mean) if daily_mean != 0 else 0
        
        return {
            'daily_std': round(daily_std, 2),
            'daily_mean': round(daily_mean, 2),
            'volatility_coefficient': round(volatility_coefficient, 2),
            'num_days': len(daily_flows)
        }
    
    def calculate_value_at_risk(self, account_id=None, confidence_level=0.99):
        # Value at Risk (VaR) - максимальная потенциальная потеря с заданной вероятностью
        #
        # Например: VaR 99% = $100,000 означает:
        # "С вероятностью 99% потери не превысят $100,000"
        # Получаем исторические данные
        if account_id:
            transactions = self.transactions[self.transactions['account_id'] == account_id]
        else:
            transactions = self.transactions
        
        # Группируем по дням
        daily_flows = transactions.groupby(
            transactions['datetime'].dt.date
        ).agg({
            'amount': lambda x: x[transactions.loc[x.index, 'direction'] == 'inflow'].sum() - 
                               x[transactions.loc[x.index, 'direction'] == 'outflow'].sum()
        }).reset_index()
        daily_flows.columns = ['date', 'net_flow']
        
        if len(daily_flows) < 30:
            return {'var': 0, 'confidence': confidence_level}
        
        # Считаем VaR (квантиль распределения)
        var = np.percentile(daily_flows['net_flow'], (1 - confidence_level) * 100)
        
        return {
            'var': round(abs(var), 2),
            'confidence': confidence_level,
            'interpretation': f"С вероятностью {confidence_level*100}% дневные потери не превысят ${abs(var):,.0f}"
        }
    
    def calculate_optimal_reserve(self, account_id=None, holding_period_days=7):
        # Рассчитывает оптимальный размер резерва
        #
        # Метод:
        # 1. VaR для оценки максимальных потерь
        # 2. Средние дневные расходы
        # 3. Волатильность
        # 4. Буфер безопасности
        # Получаем данные о счете
        if account_id:
            account = self.accounts[self.accounts['account_id'] == account_id].iloc[0]
            currency = account['currency']
        else:
            currency = None
        
        # 1. Value at Risk
        var_info = self.calculate_value_at_risk(account_id, confidence_level=self.confidence_level)
        var = var_info['var']
        
        # 2. Средние дневные расходы
        if account_id:
            outflows = self.transactions[
                (self.transactions['account_id'] == account_id) &
                (self.transactions['direction'] == 'outflow')
            ]
        else:
            outflows = self.transactions[self.transactions['direction'] == 'outflow']
        
        # Группируем по дням
        daily_outflows = outflows.groupby(
            outflows['datetime'].dt.date
        )['amount'].sum()
        
        avg_daily_outflow = daily_outflows.mean() if len(daily_outflows) > 0 else 0
        
        # 3. Ожидаемые расходы на период
        expected_outflows = avg_daily_outflow * holding_period_days
        
        # 4. Волатильность
        volatility = self.calculate_historical_volatility(account_id)
        volatility_buffer = volatility['daily_std'] * np.sqrt(holding_period_days)
        
        # 5. Запланированные критические платежи
        future_date = datetime.now() + timedelta(days=holding_period_days)
        
        if account_id:
            critical_payments = self.scheduled_payments[
                (self.scheduled_payments['account_from'] == account_id) &
                (self.scheduled_payments['due_date'] <= future_date) &
                (self.scheduled_payments['priority'] == 'critical')
            ]['amount'].sum()
        else:
            critical_payments = self.scheduled_payments[
                (self.scheduled_payments['due_date'] <= future_date) &
                (self.scheduled_payments['priority'] == 'critical')
            ]['amount'].sum()
        
        # ФОРМУЛА ОПТИМАЛЬНОГО РЕЗЕРВА:
        # Резерв = max(VaR, Средние расходы + Волатильность) + Критические платежи + 10% буфер
        
        base_reserve = max(var, expected_outflows + volatility_buffer)
        optimal_reserve = (base_reserve + critical_payments) * 1.10  # +10% буфер
        
        return {
            'optimal_reserve': round(optimal_reserve, 2),
            'var_component': round(var, 2),
            'expected_outflows': round(expected_outflows, 2),
            'volatility_buffer': round(volatility_buffer, 2),
            'critical_payments': round(critical_payments, 2),
            'safety_buffer': round(optimal_reserve * 0.10, 2),
            'holding_period_days': holding_period_days,
            'confidence_level': self.confidence_level
        }
    
    def analyze_current_vs_optimal_reserves(self):
        # Сравнивает текущие резервы с оптимальными
        #
        # Показывает где избыток, где дефицит
        results = []
        
        for _, account in self.accounts.iterrows():
            account_id = account['account_id']
            current_balance = account['current_balance']
            
            # Рассчитываем оптимальный резерв
            optimal_info = self.calculate_optimal_reserve(account_id, holding_period_days=7)
            optimal_reserve = optimal_info['optimal_reserve']
            
            # Разница
            difference = current_balance - optimal_reserve
            difference_pct = (difference / optimal_reserve * 100) if optimal_reserve > 0 else 0
            
            # Статус
            if difference > optimal_reserve * 0.3:  # Избыток > 30%
                status = 'EXCESS'
                recommendation = 'Можно высвободить часть средств'
            elif difference < 0:  # Дефицит
                status = 'DEFICIT'
                recommendation = 'Необходимо увеличить резерв'
            else:
                status = 'OPTIMAL'
                recommendation = 'Резерв в норме'
            
            results.append({
                'account_id': account_id,
                'currency': account['currency'],
                'bank': account['bank_name'],
                'current_balance': round(current_balance, 2),
                'optimal_reserve': round(optimal_reserve, 2),
                'difference': round(difference, 2),
                'difference_pct': round(difference_pct, 1),
                'status': status,
                'recommendation': recommendation,
                'can_free_up': round(max(0, difference * 0.8), 2)  # 80% от избытка можно высвободить
            })
        
        return pd.DataFrame(results)
    
    def calculate_total_excess_reserves(self):
        # Считает общий объем избыточных резервов по всем счетам
        analysis_df = self.analyze_current_vs_optimal_reserves()
        
        # Фильтруем счета с избытком
        excess_accounts = analysis_df[analysis_df['status'] == 'EXCESS']
        
        if len(excess_accounts) == 0:
            return {
                'total_excess': 0,
                'can_free_up': 0,
                'num_accounts': 0,
                'potential_income': 0,
                'currencies': []
            }
        
        total_excess = excess_accounts['difference'].sum()
        can_free_up = excess_accounts['can_free_up'].sum()
        
        # Потенциальный доход (4% годовых)
        monthly_income = can_free_up * (self.deposit_rate / 12)
        yearly_income = can_free_up * self.deposit_rate
        
        return {
            'total_excess': round(total_excess, 2),
            'can_free_up': round(can_free_up, 2),
            'num_accounts': len(excess_accounts),
            'currencies': excess_accounts['currency'].unique().tolist(),
            'monthly_income': round(monthly_income, 2),
            'yearly_income': round(yearly_income, 2),
            'roi_percentage': self.deposit_rate * 100
        }
    
    def stress_test_reserves(self, scenario='moderate'):
        # Стресс-тестирование резервов
        #
        # Сценарии:
        # - mild: +20% волатильности
        # - moderate: +50% волатильности, -30% поступлений
        # - severe: +100% волатильности, -50% поступлений
        scenarios = {
            'mild': {'volatility_multiplier': 1.2, 'inflow_reduction': 0.0},
            'moderate': {'volatility_multiplier': 1.5, 'inflow_reduction': 0.3},
            'severe': {'volatility_multiplier': 2.0, 'inflow_reduction': 0.5}
        }
        
        params = scenarios.get(scenario, scenarios['moderate'])
        
        results = []
        
        for _, account in self.accounts.iterrows():
            account_id = account['account_id']
            current_balance = account['current_balance']
            
            # Базовый расчет
            optimal_info = self.calculate_optimal_reserve(account_id, holding_period_days=7)
            base_reserve = optimal_info['optimal_reserve']
            
            # Стресс-сценарий
            volatility = self.calculate_historical_volatility(account_id)
            stressed_volatility = volatility['daily_std'] * params['volatility_multiplier']
            stressed_buffer = stressed_volatility * np.sqrt(7)
            
            # Пересчитываем резерв
            stressed_reserve = base_reserve + stressed_buffer
            
            # Проверяем достаточность
            is_sufficient = current_balance >= stressed_reserve
            shortfall = max(0, stressed_reserve - current_balance)
            
            results.append({
                'account_id': account_id,
                'currency': account['currency'],
                'current_balance': round(current_balance, 2),
                'normal_reserve': round(base_reserve, 2),
                'stressed_reserve': round(stressed_reserve, 2),
                'is_sufficient': is_sufficient,
                'shortfall': round(shortfall, 2),
                'scenario': scenario
            })
        
        return pd.DataFrame(results)
    
    def generate_reserve_recommendations(self):
        # Генерирует конкретные рекомендации по резервам
        analysis_df = self.analyze_current_vs_optimal_reserves()
        
        recommendations = []
        
        for _, row in analysis_df.iterrows():
            if row['status'] == 'EXCESS':
                recommendations.append({
                    'priority': 3,
                    'account_id': row['account_id'],
                    'action': 'REDUCE_RESERVE',
                    'message': f"Можно высвободить ${row['can_free_up']:,.0f} с счета {row['account_id']}",
                    'details': f"Текущий: ${row['current_balance']:,.0f}, Оптимальный: ${row['optimal_reserve']:,.0f}",
                    'benefit': f"Потенциальный доход: ${row['can_free_up'] * self.deposit_rate:,.0f}/год"
                })
            
            elif row['status'] == 'DEFICIT':
                recommendations.append({
                    'priority': 1 if row['difference'] < -row['optimal_reserve'] * 0.2 else 2,
                    'account_id': row['account_id'],
                    'action': 'INCREASE_RESERVE',
                    'message': f"Необходимо пополнить резерв на ${abs(row['difference']):,.0f} для {row['account_id']}",
                    'details': f"Текущий: ${row['current_balance']:,.0f}, Требуется: ${row['optimal_reserve']:,.0f}",
                    'benefit': "Снизит риск кассового разрыва"
                })
        
        return pd.DataFrame(recommendations).sort_values('priority') if recommendations else pd.DataFrame()
    
    def calculate_reserve_efficiency_score(self):
        # Оценка эффективности использования резервов (0-100)
        #
        # 100 = идеально оптимизировано
        # 0 = очень неэффективно
        analysis_df = self.analyze_current_vs_optimal_reserves()
        
        # Считаем отклонения
        deviations = analysis_df['difference_pct'].abs()
        
        # Средний процент отклонения
        avg_deviation = deviations.mean()
        
        # Формула оценки: 100 - (среднее отклонение / 2)
        # Если отклонение 0% = 100 баллов
        # Если отклонение 100% = 50 баллов
        # Если отклонение 200% = 0 баллов
        
        efficiency_score = max(0, 100 - (avg_deviation / 2))
        
        # Оценка в категориях
        if efficiency_score >= 90:
            rating = "Отлично"
            color = "green"
        elif efficiency_score >= 75:
            rating = "Хорошо"
            color = "lightgreen"
        elif efficiency_score >= 60:
            rating = "Удовлетворительно"
            color = "orange"
        else:
            rating = "Требуется оптимизация"
            color = "red"
        
        return {
            'score': round(efficiency_score, 1),
            'rating': rating,
            'color': color,
            'avg_deviation': round(avg_deviation, 1),
            'num_optimal': len(analysis_df[analysis_df['status'] == 'OPTIMAL']),
            'num_excess': len(analysis_df[analysis_df['status'] == 'EXCESS']),
            'num_deficit': len(analysis_df[analysis_df['status'] == 'DEFICIT'])
        }
    
    def project_reserve_impact(self, months=12):
        # Проецирует влияние оптимизации резервов на N месяцев
        excess_info = self.calculate_total_excess_reserves()
        
        projection = []
        
        for month in range(1, months + 1):
            cumulative_income = excess_info['monthly_income'] * month
            
            projection.append({
                'month': month,
                'cumulative_income': round(cumulative_income, 2),
                'freed_capital': excess_info['can_free_up'],
                'roi': round((cumulative_income / excess_info['can_free_up'] * 100), 2) if excess_info['can_free_up'] > 0 else 0
            })
        
        return pd.DataFrame(projection)
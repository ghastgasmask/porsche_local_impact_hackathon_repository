# Smart Cash Allocator
# Перераспределение ликвидности между счетами

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json
import streamlit as st

class SmartCashAllocator:
    # Оптимизирует распределение денег между счетами компании
    
    def __init__(self, accounts_df, transactions_df, scheduled_payments_df):
        # Initialization модуля
        #
        # Параметры
        # accounts_df: DataFrame с информацией о счетах
        # transactions_df: DataFrame с историей транзакций
        # scheduled_payments_df: DataFrame с запланированными платежами
        self.accounts = accounts_df.copy()
        self.transactions = transactions_df.copy()
        self.scheduled_payments = scheduled_payments_df.copy()
        
        # preobrazovat' dannie
        self.transactions['datetime'] = pd.to_datetime(self.transactions['datetime'])
        self.scheduled_payments['due_date'] = pd.to_datetime(self.scheduled_payments['due_date'])
    
    def calculate_required_balance(self, account_id, days_ahead=7):
        # Рассчитывает необходимый остаток на счете. Например тут на 7 дней. Вообще на N дней.
        #
        # Как убрать синии линии у меня грамматика типо
        #
        # Логика
        # 1. Смотрим запланированные платежи с этого счета
        # 2. Смотрим среднюю дневную активность (из истории)
        # 3. Добавляем буфер безопасности 20%
        
        account = self.accounts[self.accounts['account_id'] == account_id].iloc[0]
        currency = account['currency']
        # Находим информацию о счете
        
        # запланированнie платежi
        future_date = datetime.now() + timedelta(days=days_ahead)
        upcoming_payments = self.scheduled_payments[
            (self.scheduled_payments['account_from'] == account_id) &
            (self.scheduled_payments['due_date'] <= future_date) &
            (self.scheduled_payments['currency'] == currency)
        ]
        total_scheduled = upcoming_payments['amount'].sum()
        
        # Средняя дневная активность (расходы) за последний месяц
    
        one_month_ago = datetime.now() - timedelta(days=30)
        recent_out_flows = self.transactions[
            (self.transactions['account_id'] == account_id) &
            (self.transactions['direction'] == 'outflow') &
            (self.transactions['datetime'] >= one_month_ago) &
            (self.transactions['currency'] == currency)
        ]
        
        if len(recent_out_flows) > 0:
            avg_daily_outflow = recent_out_flows['amount'].sum() / 30
            expected_outflows = avg_daily_outflow * days_ahead
        else:
            expected_outflows = 0
        
        # Необходимый остаток = max(запланированное, ожидаемое) + например буфер ~20%
        required = max(total_scheduled, expected_outflows) * 1.2
        # Минимум = минимальный остаток из данных счета
        minimum = account['minimum_balance']
        
        return max(required, minimum)
    
    def identify_excess_liquidity(self):
        # Находит счета с избыточной ликвидностью
        #
        # Возвращает список счетов где денег больше чем нужно
        excess_accounts = []
        
        for i, account in self.accounts.iterrows():
            account_id = account['account_id']
            current_balance = account['current_balance']
            
            # Рассчитываем необходимый остаток
            required_balance = self.calculate_required_balance(account_id, days_ahead=7)
            
            # Избыток = текущий баланс - необходимый
            excess = current_balance - required_balance
            
            # Если избыток > 10% от необходимого, считаем это проблемой
            if excess > required_balance * 0.1:
                excess_accounts.append({
                    'account_id': account_id,
                    'currency': account['currency'],
                    'bank': account['bank_name'],
                    'current_balance': current_balance,
                    'required_balance': required_balance,
                    'excess_amount': excess,
                    'excess_percentage': (excess / current_balance) * 100
                })
        
        return pd.DataFrame(excess_accounts)
    
    def identify_deficit_accounts(self):
        # Находит счета с нехваткой ликвидности
        #
        # Возвращает список счетов, где денег может не хватить
        deficit_accounts = []
        
        for i, account in self.accounts.iterrows():
            account_id = account['account_id']
            current_balance = account['current_balance']
            
            # Рассчитываем необходимый остаток
            required_balance = self.calculate_required_balance(account_id, days_ahead=7)
            
            # Дефицит = необходимый - текущий
            deficit = required_balance - current_balance
            
            # Если дефицит > 0, значит не хватает
            if deficit > 0:
                deficit_accounts.append({
                    'account_id': account_id,
                    'currency': account['currency'],
                    'bank': account['bank_name'],
                    'current_balance': current_balance,
                    'required_balance': required_balance,
                    'deficit_amount': deficit,
                    'urgency': 'CRITICAL' if deficit > current_balance * 0.5 else 'WARNING'
                })
        
        return pd.DataFrame(deficit_accounts)
    
    def generate_reallocation_recommendations(self):
        # Генерирует рекомендации по перераспределению денег
        #
        # Логика:
        # 1. Находим избыточные счета
        # 2. Находим счета с дефицитом
        # 3. Составляем план переводов (учитывая валюту)
        excess_df = self.identify_excess_liquidity()
        deficit_df = self.identify_deficit_accounts()
        
        recommendations = []
        
        if len(excess_df) == 0 and len(deficit_df) == 0:
            return pd.DataFrame(recommendations)  # Все ОК, рекомендаций нет
        
        # Группируем по валютам
        currencies = set(excess_df['currency'].unique()) | set(deficit_df['currency'].unique()) if len(excess_df) > 0 or len(deficit_df) > 0 else set()
        
        for currency in currencies:
            # Избытки в этой валюте
            excess_in_currency = excess_df[excess_df['currency'] == currency] if len(excess_df) > 0 else pd.DataFrame()
            # Дефициты в этой валюте
            deficit_in_currency = deficit_df[deficit_df['currency'] == currency] if len(deficit_df) > 0 else pd.DataFrame()
            
            # Если есть и избытки, и дефициты - делаем перевод
            if len(excess_in_currency) > 0 and len(deficit_in_currency) > 0:
                for _, deficit_acc in deficit_in_currency.iterrows():
                    # Берем первый счет с избытком
                    if len(excess_in_currency) > 0:
                        excess_acc = excess_in_currency.iloc[0]
                        
                        # Сумма перевода = минимум из (избыток, дефицит)
                        transfer_amount = min(
                            excess_acc['excess_amount'],
                            deficit_acc['deficit_amount']
                        )
                        
                        recommendations.append({
                            'priority': 1 if deficit_acc['urgency'] == 'CRITICAL' else 2,
                            'action': 'TRANSFER',
                            'from_account': excess_acc['account_id'],
                            'to_account': deficit_acc['account_id'],
                            'amount': round(transfer_amount, 2),
                            'currency': currency,
                            'reason': f"Покрыть дефицит на {deficit_acc['account_id']}",
                            'expected_benefit': f"Освободить {excess_acc['excess_percentage']:.1f}% избытка"
                        })
                        
                        # Обновляем избыток (убираем переведенную сумму)
                        excess_in_currency.loc[excess_in_currency.index[0], 'excess_amount'] -= transfer_amount
                        if excess_in_currency.iloc[0]['excess_amount'] <= 0:
                            excess_in_currency = excess_in_currency.iloc[1:]
            
            # Если остались только избытки (нет дефицитов) - рекомендуем вложить
            elif len(excess_in_currency) > 0:
                for _, excess_acc in excess_in_currency.iterrows():
                    recommendations.append({
                        'priority': 3,
                        'action': 'INVEST',
                        'from_account': excess_acc['account_id'],
                        'to_account': 'DEPOSIT_ACCOUNT',
                        'amount': round(excess_acc['excess_amount'] * 0.8, 2),  # 80% избытка
                        'currency': currency,
                        'reason': f"Избыток {excess_acc['excess_percentage']:.1f}% не используется",
                        'expected_benefit': "Можно получить доход под проценты"
                    })
        
        return pd.DataFrame(recommendations).sort_values('priority') if recommendations else pd.DataFrame()
    
    def calculate_optimization_impact(self):
        # Рассчитывает эффект от оптимизации
        #
        # Показывает сколько денег "заморожено" и сколько можно высвободить
        excess_df = self.identify_excess_liquidity()
        
        if len(excess_df) == 0:
            return {
                'total_excess': 0,
                'potential_savings': 0,
                'num_inefficient_accounts': 0
            }
        
        total_excess = excess_df['excess_amount'].sum()
        
        # Предполагаем 4% годовых на депозите
        # За месяц это примерно 0.33%
        potential_monthly_income = total_excess * 0.0033
        
        return {
            'total_excess': round(total_excess, 2),
            'potential_monthly_income': round(potential_monthly_income, 2),
            'potential_yearly_income': round(potential_monthly_income * 12, 2),
            'num_inefficient_accounts': len(excess_df),
            'currencies_affected': excess_df['currency'].unique().tolist()
        }
    
    def get_account_health_status(self):
        # Возвращает "здоровье" каждого счета
        #
        # Статус: OPTIMAL, EXCESS, DEFICIT, CRITICAL
        health_status = []
        
        for _, account in self.accounts.iterrows():
            account_id = account['account_id']
            current_balance = account['current_balance']
            required_balance = self.calculate_required_balance(account_id, days_ahead=7)
            
            excess = current_balance - required_balance
            
            # Определяем статус
            if excess > required_balance * 0.2:  # Избыток > 20%
                status = 'EXCESS'
                color = 'orange'
            elif excess < 0:  # Дефицит
                if abs(excess) > current_balance * 0.5:
                    status = 'CRITICAL'
                    color = 'red'
                else:
                    status = 'DEFICIT'
                    color = 'yellow'
            else:  # Все в норме
                status = 'OPTIMAL'
                color = 'green'
            
            health_status.append({
                'account_id': account_id,
                'currency': account['currency'],
                'bank': account['bank_name'],
                'current_balance': current_balance,
                'required_balance': required_balance,
                'difference': excess,
                'utilization_rate': (required_balance / current_balance * 100) if current_balance > 0 else 0,
                'status': status,
                'status_color': color
            })
        
        return pd.DataFrame(health_status)
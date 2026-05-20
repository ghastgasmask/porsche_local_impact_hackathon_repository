#Модуль 5: Automated Treasury Control Center
#Автоматизация treasury-операций и система алертов
#

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json

class AutomationCenter:
    #Центр автоматизации treasury-операций
    #Мониторинг, алерты, автоматические действия
    
    def __init__(self, accounts_df, transactions_df, scheduled_payments_df, expected_inflows_df):
        #Инициализация центра автоматизации
        self.accounts = accounts_df.copy()
        self.transactions = transactions_df.copy()
        self.scheduled_payments = scheduled_payments_df.copy()
        self.expected_inflows = expected_inflows_df.copy()
        
        # Преобразуем даты
        self.transactions['datetime'] = pd.to_datetime(self.transactions['datetime'])
        self.scheduled_payments['due_date'] = pd.to_datetime(self.scheduled_payments['due_date'])
        self.expected_inflows['expected_arrival_date'] = pd.to_datetime(self.expected_inflows['expected_arrival_date'])
        
        # Правила автоматизации
        self.automation_rules = {
            'excess_threshold': 0.2,  # Если избыток > 20% - действовать
            'deficit_threshold': 0.1,  # Если дефицит > 10% - алерт
            'critical_balance_ratio': 0.15,  # Критический уровень = 15% от оптимального
            'auto_transfer_limit': 1000000,  # Максимальная сумма автоперевода без подтверждения
            'alert_hours_before': 48,  # За сколько часов до проблемы делать алерт
        }
        
        # История алертов и действий
        self.alerts_history = []
        self.actions_log = []
    
    def generate_real_time_alerts(self):
        #Генерирует алерты
        #Типы алертов:
        #1. Критический дефицит ликвидности
        #2. Приближающийся кассовый разрыв
        #3. Избыточная ликвидность
        #4. Аномальная активность
        #5. Задержка платежей
        alerts = []
        now = datetime.now()
        
        # 1 Проверка критических балансов
        for _, account in self.accounts.iterrows():
            balance = account['current_balance']
            min_balance = account['minimum_balance']
            
            if balance < min_balance:
                alerts.append({
                    'severity': 'CRITICAL',
                    'type': 'LOW_BALANCE',
                    'account': account['account_id'],
                    'message': f"Баланс на {account['account_id']} ниже минимума: ${balance:,.0f} < ${min_balance:,.0f}",
                    'timestamp': now,
                    'action_required': True,
                    'suggested_action': f"Срочно пополнить на ${(min_balance - balance):,.0f}"
                })
            elif balance < min_balance * 1.2:
                alerts.append({
                    'severity': 'WARNING',
                    'type': 'LOW_BALANCE',
                    'account': account['account_id'],
                    'message': f"Баланс на {account['account_id']} приближается к минимуму: ${balance:,.0f}",
                    'timestamp': now,
                    'action_required': False,
                    'suggested_action': "Подготовить резервы"
                })
        
        # 2 Проверка приближающихся критичных платежей
        alert_threshold = now + timedelta(hours=self.automation_rules['alert_hours_before'])
        
        upcoming_critical = self.scheduled_payments[
            (self.scheduled_payments['due_date'] <= alert_threshold) &
            (self.scheduled_payments['priority'] == 'critical')
        ]
        
        for _, payment in upcoming_critical.iterrows():
            
            account = self.accounts[self.accounts['account_id'] == payment['account_from']].iloc[0]
            
            if account['current_balance'] < payment['amount']:
                alerts.append({
                    'severity': 'CRITICAL',
                    'type': 'INSUFFICIENT_FUNDS',
                    'account': payment['account_from'],
                    'message': f"Недостаточно средств для платежа {payment['payment_id']}: нужно ${payment['amount']:,.0f}, есть ${account['current_balance']:,.0f}",
                    'timestamp': now,
                    'action_required': True,
                    'suggested_action': f"Перевести ${(payment['amount'] - account['current_balance']):,.0f} до {payment['due_date']}"
                })
        
        # 3 Проверка задержанных поступлений
        delayed_inflows = self.expected_inflows[
            (self.expected_inflows['status'] == 'delayed') &
            (self.expected_inflows['expected_arrival_date'] < now)
        ]
        
        if len(delayed_inflows) > 0:
            total_delayed = delayed_inflows['amount'].sum()
            alerts.append({
                'severity': 'WARNING',
                'type': 'DELAYED_INFLOWS',
                'account': 'ALL',
                'message': f"Задержано {len(delayed_inflows)} поступлений на общую сумму ${total_delayed:,.0f}",
                'timestamp': now,
                'action_required': True,
                'suggested_action': "Проверить статус с партнерами"
            })
        
        # 4 Проверка избыточной ликвидности
        for _, account in self.accounts.iterrows():
            balance = account['current_balance']
            optimal = account['optimal_balance']
            
            if balance > optimal * 1.5:
                excess = balance - optimal
                alerts.append({
                    'severity': 'INFO',
                    'type': 'EXCESS_LIQUIDITY',
                    'account': account['account_id'],
                    'message': f"Избыток ликвидности на {account['account_id']}: ${excess:,.0f}",
                    'timestamp': now,
                    'action_required': False,
                    'suggested_action': f"Рассмотреть вложение ${excess * 0.8:,.0f} под проценты"
                })
        
        # 5 Проверка аномальной активности (последние 24 часа)
        last_24h = self.transactions[
            self.transactions['datetime'] >= (now - timedelta(hours=24))
        ]
        
        if len(last_24h) > 0:
            # Средняя дневная активность
            avg_daily_count = self.transactions.groupby(
                self.transactions['datetime'].dt.date
            ).size().mean()
            
            last_24h_count = len(last_24h)
            
            if last_24h_count < avg_daily_count * 0.3:
                alerts.append({
                    'severity': 'WARNING',
                    'type': 'LOW_ACTIVITY',
                    'account': 'ALL',
                    'message': f"Низкая активность: {last_24h_count} транзакций за 24ч (обычно {avg_daily_count:.0f})",
                    'timestamp': now,
                    'action_required': True,
                    'suggested_action': "Проверить системы обработки платежей"
                })
        
        return pd.DataFrame(alerts) if alerts else pd.DataFrame()
    
    def create_automated_actions(self, enable_auto=False):
        # Создает список автоматических действий
        #Если enable_auto=True, действия выполняются автоматически
        #Если False, только рекомендации
        
        actions = []
        now = datetime.now()
        
        # Действие 1 Автоматическое перераспределение избытков
        for _, account in self.accounts.iterrows():
            balance = account['current_balance']
            optimal = account['optimal_balance']
            excess = balance - optimal
            
            if excess > optimal * self.automation_rules['excess_threshold']:
                # Можно автоматически перевести 70% избытка
                transfer_amount = excess * 0.7
                
                if transfer_amount <= self.automation_rules['auto_transfer_limit']:
                    action_status = 'EXECUTED' if enable_auto else 'PENDING_APPROVAL'
                else:
                    action_status = 'REQUIRES_MANUAL_APPROVAL'
                
                actions.append({
                    'action_id': f"AUTO_{len(actions)+1:04d}",
                    'type': 'AUTO_TRANSFER',
                    'from_account': account['account_id'],
                    'to_account': 'DEPOSIT_ACCOUNT',
                    'amount': round(transfer_amount, 2),
                    'currency': account['currency'],
                    'reason': 'Избыточная ликвидность',
                    'status': action_status,
                    'created_at': now,
                    'executed_at': now if enable_auto else None,
                    'auto_executable': transfer_amount <= self.automation_rules['auto_transfer_limit']
                })
        
        # Действие 2  бронирование под критичные платежи
        critical_payments_48h = self.scheduled_payments[
            (self.scheduled_payments['due_date'] <= now + timedelta(hours=48)) &
            (self.scheduled_payments['priority'] == 'critical')
        ]
        
        for _, payment in critical_payments_48h.iterrows():
            actions.append({
                'action_id': f"AUTO_{len(actions)+1:04d}",
                'type': 'RESERVE_FUNDS',
                'from_account': payment['account_from'],
                'to_account': 'RESERVED',
                'amount': payment['amount'],
                'currency': payment['currency'],
                'reason': f"Резерв для платежа {payment['payment_id']}",
                'status': 'RESERVED',
                'created_at': now,
                'release_date': payment['due_date'],
                'auto_executable': True
            })
        
        return pd.DataFrame(actions) if actions else pd.DataFrame()
    
    def get_system_health_status(self):
        #Общий статус "здоровья" системы
        #Возвращает:
        #- Общий статус (OK, WARNING, CRITICAL)
        #- Метрики по различным компонентам
        
        alerts_df = self.generate_real_time_alerts()
        
        # Подсчет алертов по серьезности
        if len(alerts_df) == 0:
            overall_status = 'OK'
            num_critical = 0
            num_warnings = 0
            num_info = 0
        else:
            num_critical = len(alerts_df[alerts_df['severity'] == 'CRITICAL'])
            num_warnings = len(alerts_df[alerts_df['severity'] == 'WARNING'])
            num_info = len(alerts_df[alerts_df['severity'] == 'INFO'])
            
            if num_critical > 0:
                overall_status = 'CRITICAL'
            elif num_warnings > 0:
                overall_status = 'WARNING'
            else:
                overall_status = 'OK'
        
        # Метрики компонентов
        components = {
            'liquidity': self._check_liquidity_health(),
            'cash_flow': self._check_cash_flow_health(),
            'reserves': self._check_reserves_health(),
            'activity': self._check_activity_health()
        }
        
        return {
            'overall_status': overall_status,
            'num_critical_alerts': num_critical,
            'num_warnings': num_warnings,
            'num_info': num_info,
            'total_alerts': len(alerts_df),
            'components': components,
            'last_check': datetime.now()
        }
    
    def _check_liquidity_health(self):
        #Проверка здоровья ликвидности#
        total_balance = self.accounts['current_balance'].sum()
        total_minimum = self.accounts['minimum_balance'].sum()
        
        if total_balance >= total_minimum * 1.5:
            return {'status': 'GOOD', 'score': 100}
        elif total_balance >= total_minimum:
            return {'status': 'OK', 'score': 70}
        else:
            return {'status': 'CRITICAL', 'score': 30}
    
    def _check_cash_flow_health(self):
        #Проверка здоровья денежных потоков#
        # Проверяем соотношение поступлений/расходов за последние 7 дней
        last_week = datetime.now() - timedelta(days=7)
        recent = self.transactions[self.transactions['datetime'] >= last_week]
        
        inflows = recent[recent['direction'] == 'inflow']['amount'].sum()
        outflows = recent[recent['direction'] == 'outflow']['amount'].sum()
        
        ratio = inflows / outflows if outflows > 0 else 1
        
        if ratio >= 1.2:
            return {'status': 'GOOD', 'score': 100, 'ratio': round(ratio, 2)}
        elif ratio >= 0.9:
            return {'status': 'OK', 'score': 70, 'ratio': round(ratio, 2)}
        else:
            return {'status': 'WARNING', 'score': 40, 'ratio': round(ratio, 2)}
    
    def _check_reserves_health(self):
        #Проверка здоровья резервов#
        # Проверяем сколько счетов имеют достаточные резервы
        sufficient = 0
        for _, account in self.accounts.iterrows():
            if account['current_balance'] >= account['minimum_balance']:
                sufficient += 1
        
        pct_sufficient = (sufficient / len(self.accounts)) * 100
        
        if pct_sufficient >= 90:
            return {'status': 'GOOD', 'score': 100}
        elif pct_sufficient >= 70:
            return {'status': 'OK', 'score': 70}
        else:
            return {'status': 'WARNING', 'score': 40}
    
    def _check_activity_health(self):
        #Проверка активности
        last_24h = self.transactions[
            self.transactions['datetime'] >= (datetime.now() - timedelta(hours=24))
        ]
        
        avg_daily = self.transactions.groupby(
            self.transactions['datetime'].dt.date
        ).size().mean()
        
        current_count = len(last_24h)
        
        if current_count >= avg_daily * 0.7:
            return {'status': 'GOOD', 'score': 100}
        elif current_count >= avg_daily * 0.4:
            return {'status': 'OK', 'score': 70}
        else:
            return {'status': 'WARNING', 'score': 40}
    
    def generate_daily_report(self):
        #Генерирует ежедневный отчет для treasury команды
        
        today = datetime.now().date()
        yesterday = today - timedelta(days=1)
        
        # Транзакции за вчера
        yesterday_transactions = self.transactions[
            self.transactions['datetime'].dt.date == yesterday
        ]
        
        inflows_yesterday = yesterday_transactions[
            yesterday_transactions['direction'] == 'inflow'
        ]['amount'].sum()
        
        outflows_yesterday = yesterday_transactions[
            yesterday_transactions['direction'] == 'outflow'
        ]['amount'].sum()
        
        net_flow = inflows_yesterday - outflows_yesterday
        
        # Текущий статус
        health = self.get_system_health_status()
        alerts = self.generate_real_time_alerts()
        
        report = {
            'report_date': today,
            'period': 'Yesterday',
            'summary': {
                'total_inflows': round(inflows_yesterday, 2),
                'total_outflows': round(outflows_yesterday, 2),
                'net_flow': round(net_flow, 2),
                'num_transactions': len(yesterday_transactions),
                'total_balance': self.accounts['current_balance'].sum()
            },
            'health_status': health,
            'active_alerts': len(alerts),
            'critical_issues': len(alerts[alerts['severity'] == 'CRITICAL']) if len(alerts) > 0 else 0
        }
        
        return report
    
    def get_automation_statistics(self):
        #Статистика работы автоматизации
        
        actions_df = self.create_automated_actions(enable_auto=False)
        
        if len(actions_df) == 0:
            return {
                'total_actions': 0,
                'auto_executable': 0,
                'requires_approval': 0,
                'potential_savings': 0
            }
        
        auto_executable = len(actions_df[actions_df['auto_executable'] == True])
        requires_approval = len(actions_df[actions_df['auto_executable'] == False])
        
        # Потенциальная экономия от автоматизации
        # (предполагаем что ручная обработка стоит $50 за действие)
        potential_savings = auto_executable * 50
        
        return {
            'total_actions': len(actions_df),
            'auto_executable': auto_executable,
            'requires_approval': requires_approval,
            'potential_savings': potential_savings,
            'automation_rate': round((auto_executable / len(actions_df)) * 100, 1) if len(actions_df) > 0 else 0
        }
        
    def execute_automated_actions(self, enable_auto=False, accounts_df=None):
        #Выполняет автоматические действия
        #Если enable_auto=False, возвращает пустой список
        #Если enable_auto=True, выполняет действия и возвращает результаты
        
        if not enable_auto:
            return []
            
        from modules.action_executor import ActionExecutor
        executor = ActionExecutor()
        
        if accounts_df is None:
            import streamlit as st
            if 'accounts_df' in st.session_state:
                accounts_df = st.session_state.accounts_df
            else:
                accounts_df = self.accounts
                
        actions_df = self.create_automated_actions(enable_auto=True)
        if len(actions_df) == 0:
            return []
            
        results = []
        for _, action in actions_df.iterrows():
            # Если действие не может быть выполнено автоматически (больше лимита)
            if not action.get('auto_executable', True):
                results.append({
                    'action_id': action['action_id'],
                    'type': action['type'],
                    'from_account': action['from_account'],
                    'to_account': action['to_account'],
                    'amount': action['amount'],
                    'currency': action['currency'],
                    'success': False,
                    'message': f"❌ Превышен лимит автоматического перевода: {action['currency']} {action['amount']:,.2f} > {action['currency']} {self.automation_rules['auto_transfer_limit']:,.2f}"
                })
                continue
                
            if action['type'] == 'AUTO_TRANSFER':
                res = executor.execute_transfer(
                    from_account=action['from_account'],
                    to_account=action['to_account'],
                    amount=action['amount'],
                    currency=action['currency'],
                    accounts_df=accounts_df,
                    description=action['reason'],
                    executed_by="Automation Center"
                )
                results.append({
                    'action_id': action['action_id'],
                    'type': action['type'],
                    'from_account': action['from_account'],
                    'to_account': action['to_account'],
                    'amount': action['amount'],
                    'currency': action['currency'],
                    'success': res.get('success', False),
                    'message': res.get('message', "Ошибка выполнения перевода")
                })
            elif action['type'] == 'RESERVE_FUNDS':
                res = executor.reserve_funds(
                    account_id=action['from_account'],
                    amount=action['amount'],
                    currency=action['currency'],
                    reason=action['reason'],
                    accounts_df=accounts_df,
                    executed_by="Automation Center"
                )
                results.append({
                    'action_id': action['action_id'],
                    'type': action['type'],
                    'from_account': action['from_account'],
                    'to_account': action['to_account'],
                    'amount': action['amount'],
                    'currency': action['currency'],
                    'success': res.get('success', False),
                    'message': res.get('message', "Ошибка при резервировании средств")
                })
                
        # После успешных переводов обновить accounts_df и сохранить в CSV
        accounts_df.to_csv('data/accounts_balances.csv', index=False)
        return results

        # its just math?
        # yeah i admit it
        # i aint tryna deny it or anythin
        # jjk ref
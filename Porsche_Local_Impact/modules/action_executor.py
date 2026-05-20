#Модуль для выполнения и управления действиями treasury
#

import pandas as pd
import json
from datetime import datetime, timedelta
import os

class ActionExecutor:
    #Управляет выполнением действий: переводы, резервирования, изменения данных
    #
    
    def __init__(self):
        #Инициализация#
        self.actions_log_file = 'data/actions_log.csv'
        self.transfers_log_file = 'data/transfers_log.csv'
        self.actions_history = self._load_actions_log()
    
    def _load_actions_log(self):
        #Загружает историю действий#
        if os.path.exists(self.actions_log_file):
            return pd.read_csv(self.actions_log_file)
        else:
            # Создаем пустой файл с заголовками
            empty_df = pd.DataFrame(columns=[
                'action_id', 'timestamp', 'action_type', 'status', 
                'from_account', 'to_account', 'amount', 'currency', 
                'description', 'executed_by', 'notes'
            ])
            empty_df.to_csv(self.actions_log_file, index=False)
            return empty_df
    
    def execute_transfer(self, from_account, to_account, amount, currency, 
                        accounts_df, description="", executed_by="System"):
        #Выполняет перевод средств между счетами
        
        #Проверяет
        
        # Проверка счетов
        from_acc = accounts_df[accounts_df['account_id'] == from_account]
        
        if to_account == 'DEPOSIT_ACCOUNT':
            to_acc = pd.DataFrame([{
                'account_id': 'DEPOSIT_ACCOUNT',
                'currency': from_acc.iloc[0]['currency'] if len(from_acc) > 0 else currency,
                'current_balance': 0.0
            }])
        else:
            to_acc = accounts_df[accounts_df['account_id'] == to_account]
        
        if len(from_acc) == 0:
            return {
                'success': False,
                'message': f"Счет {from_account} не найден",
                'action_id': None
            }
        
        if len(to_acc) == 0:
            return {
                'success': False,
                'message': f"Счет {to_account} не найден",
                'action_id': None
            }
        
        # Проверка валюты
        if from_acc.iloc[0]['currency'] != currency:
            return {
                'success': False,
                'message': f"Валюта на счете {from_account}: {from_acc.iloc[0]['currency']}, требуется {currency}",
                'action_id': None
            }
        
        # Проверка средств
        from_balance = from_acc.iloc[0]['current_balance']
        
        if from_balance < amount:
            return {
                'success': False,
                'message': f"Недостаточно средств. Доступно: ${from_balance:,.2f}, требуется: ${amount:,.2f}",
                'action_id': None
            }
        
        # ВЫПОЛНЯЕМ ПЕРЕВОД
        action_id = self._generate_action_id()
        timestamp = datetime.now()
        
        # Обновляем балансы в DataFrame
        accounts_df.loc[accounts_df['account_id'] == from_account, 'current_balance'] -= amount
        if to_account != 'DEPOSIT_ACCOUNT':
            accounts_df.loc[accounts_df['account_id'] == to_account, 'current_balance'] += amount
        
        # Сохраняем измененные данные
        accounts_df.to_csv('data/accounts_balances.csv', index=False)
        
        # Логируем действие
        action_record = {
            'action_id': action_id,
            'timestamp': timestamp.isoformat(),
            'action_type': 'TRANSFER',
            'status': 'EXECUTED',
            'from_account': from_account,
            'to_account': to_account,
            'amount': round(amount, 2),
            'currency': currency,
            'description': description,
            'executed_by': executed_by,
            'notes': 'Успешно выполнено'
        }
        
        self._log_action(action_record)
        
        to_new_balance = 0.0
        if to_account != 'DEPOSIT_ACCOUNT':
            to_new_balance = round(accounts_df[accounts_df['account_id'] == to_account].iloc[0]['current_balance'], 2)
            
        return {
            'success': True,
            'message': f"✅ Перевод ${amount:,.2f} {currency} выполнен успешно",
            'action_id': action_id,
            'from_account': from_account,
            'from_new_balance': round(accounts_df[accounts_df['account_id'] == from_account].iloc[0]['current_balance'], 2),
            'to_account': to_account,
            'to_new_balance': to_new_balance
        }
    
    def reserve_funds(self, account_id, amount, currency, reason, accounts_df, executed_by="System"):
        # Резервирует 

        account = accounts_df[accounts_df['account_id'] == account_id]
        
        if len(account) == 0:
            return {
                'success': False,
                'message': f"Счет {account_id} не найден",
                'action_id': None
            }
        
        if account.iloc[0]['current_balance'] < amount:
            return {
                'success': False,
                'message': f"Недостаточно средств для резервирования",
                'action_id': None
            }
        
        action_id = self._generate_action_id()
        timestamp = datetime.now()
        
        action_record = {
            'action_id': action_id,
            'timestamp': timestamp.isoformat(),
            'action_type': 'RESERVE',
            'status': 'RESERVED',
            'from_account': account_id,
            'to_account': 'RESERVED_POOL',
            'amount': round(amount, 2),
            'currency': currency,
            'description': reason,
            'executed_by': executed_by,
            'notes': 'Средства зарезервированы'
        }
        
        self._log_action(action_record)
        
        return {
            'success': True,
            'message': f"✅ Зарезервировано ${amount:,.2f} {currency}",
            'action_id': action_id
        }
    
    def release_reserved_funds(self, action_id, accounts_df, executed_by="System"):
        # Освобождает зарезервированные средства
        #
        # Ищем в логе
        log_df = pd.read_csv(self.actions_log_file)
        action = log_df[log_df['action_id'] == action_id]
        
        if len(action) == 0:
            return {
                'success': False,
                'message': f"Действие {action_id} не найдено",
            }
        
        action_record = {
            'action_id': self._generate_action_id(),
            'timestamp': datetime.now().isoformat(),
            'action_type': 'RELEASE_RESERVE',
            'status': 'EXECUTED',
            'from_account': 'RESERVED_POOL',
            'to_account': action.iloc[0]['from_account'],
            'amount': action.iloc[0]['amount'],
            'currency': action.iloc[0]['currency'],
            'description': f"Освобождение резерва {action_id}",
            'executed_by': executed_by,
            'notes': 'Средства освобождены'
        }
        
        self._log_action(action_record)
        
        return {
            'success': True,
            'message': f"✅ Зарезервированные средства освобождены",
        }
    
    def invest_funds(self, account_id, amount, currency, investment_type, 
                    annual_rate, accounts_df, executed_by="System"):
        # Вкладывает средства (типо инвестиция)
        # оо криптовалюта брат, темку нашел
        account = accounts_df[accounts_df['account_id'] == account_id]
        
        if len(account) == 0:
            return {
                'success': False,
                'message': f"Счет {account_id} не найден",
                'action_id': None
            }
        
        if account.iloc[0]['current_balance'] < amount:
            return {
                'success': False,
                'message': f"Недостаточно средств",
                'action_id': None
            }
        
        # Уменьшаем баланс
        accounts_df.loc[accounts_df['account_id'] == account_id, 'current_balance'] -= amount
        accounts_df.to_csv('data/accounts_balances.csv', index=False)
        
        action_id = self._generate_action_id()
        monthly_income = amount * (annual_rate / 100) / 12
        
        action_record = {
            'action_id': action_id,
            'timestamp': datetime.now().isoformat(),
            'action_type': 'INVEST',
            'status': 'ACTIVE',
            'from_account': account_id,
            'to_account': f'INVESTMENT_{investment_type}',
            'amount': round(amount, 2),
            'currency': currency,
            'description': f"Инвестирование в {investment_type} под {annual_rate}% годовых (${monthly_income:.2f}/месяц)",
            'executed_by': executed_by,
            'notes': f"Годовая доходность: ${amount * annual_rate / 100:,.2f}"
        }
        
        self._log_action(action_record)
        
        return {
            'success': True,
            'message': f"✅ Инвестировано ${amount:,.2f} {currency}",
            'action_id': action_id,
            'monthly_income': round(monthly_income, 2),
            'yearly_income': round(amount * annual_rate / 100, 2)
        }
    
    def _log_action(self, action_record):
        #Логирует действие в файл#
        log_df = pd.read_csv(self.actions_log_file)
        new_record = pd.DataFrame([action_record])
        log_df = pd.concat([log_df, new_record], ignore_index=True)
        log_df.to_csv(self.actions_log_file, index=False)
    
    def _generate_action_id(self):
        #Генерирует уникальный айди#
        log_df = pd.read_csv(self.actions_log_file)
        if len(log_df) == 0:
            return "ACT0000001"
        
        last_id = log_df.iloc[-1]['action_id']
        num = int(last_id[3:]) + 1
        return f"ACT{num:07d}"
    
    def get_actions_history(self, status_filter=None, action_type_filter=None, limit=50):
        #Возвращает историю действий#
        log_df = pd.read_csv(self.actions_log_file)
        
        if len(log_df) == 0:
            return pd.DataFrame()
        
        log_df['timestamp'] = pd.to_datetime(log_df['timestamp'])
        
        if status_filter:
            log_df = log_df[log_df['status'].isin(status_filter)]
        
        if action_type_filter:
            log_df = log_df[log_df['action_type'].isin(action_type_filter)]
        
        return log_df.tail(limit).sort_values('timestamp', ascending=False)
    
    def get_statistics(self):
        #Возвращает статистику по действиям#
        log_df = pd.read_csv(self.actions_log_file)
        
        if len(log_df) == 0:
            return {
                'total_actions': 0,
                'executed': 0,
                'pending': 0,
                'total_transferred': 0,
                'total_invested': 0
            }
        
        executed = len(log_df[log_df['status'] == 'EXECUTED'])
        pending = len(log_df[log_df['status'].isin(['PENDING', 'PENDING_APPROVAL'])])
        
        transfers = log_df[log_df['action_type'] == 'TRANSFER']
        total_transferred = transfers['amount'].sum() if len(transfers) > 0 else 0
        
        investments = log_df[log_df['action_type'] == 'INVEST']
        total_invested = investments['amount'].sum() if len(investments) > 0 else 0
        
        return {
            'total_actions': len(log_df),
            'executed': executed,
            'pending': pending,
            'total_transferred': round(total_transferred, 2),
            'total_invested': round(total_invested, 2)
        }
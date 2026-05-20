# Модуль 3: ML Anomaly Detector & Pattern Analyzer
# Машинное обучение для прогнозирования и выявления аномалий

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from sklearn.ensemble import IsolationForest, RandomForestRegressor
from sklearn.preprocessing import StandardScaler
import warnings
warnings.filterwarnings('ignore')

class MLAnalyzer:
    # ML-модуль для анализа паттернов и выявления аномалий
    
    def __init__(self, transactions_df, accounts_df):
        # Инициализация ML-анализатора
        self.transactions = transactions_df.copy()
        self.accounts = accounts_df.copy()
        
        # Преобразуем даты
        self.transactions['datetime'] = pd.to_datetime(self.transactions['datetime'])
        
        # Модели
        self.anomaly_detector = None
        self.volume_predictor = None
        self.scaler = StandardScaler()
        
        # Обучаем модели при инициализации
        self._prepare_data()
        self._train_models()
    
    def _prepare_data(self):
        # Подготовка данных для ML
        # Добавляем временные признаки
        self.transactions['hour'] = self.transactions['datetime'].dt.hour
        self.transactions['day_of_week'] = self.transactions['datetime'].dt.dayofweek
        self.transactions['day_of_month'] = self.transactions['datetime'].dt.day
        self.transactions['month'] = self.transactions['datetime'].dt.month
        self.transactions['is_weekend'] = self.transactions['day_of_week'].isin([5, 6]).astype(int)
        
        # Добавляем признак "время суток"
        self.transactions['time_of_day'] = pd.cut(
            self.transactions['hour'],
            bins=[0, 6, 12, 18, 24],
            labels=['night', 'morning', 'afternoon', 'evening'],
            include_lowest=True
        )
    
    def _train_models(self):
        # Обучение ML-моделей
        # 1. Модель для выявления аномалий (Isolation Forest)
        features_for_anomaly = self.transactions[
            ['amount', 'hour', 'day_of_week', 'is_weekend']
        ].copy()
        
        # Обрабатываем пропуски
        features_for_anomaly = features_for_anomaly.fillna(0)
        
        self.anomaly_detector = IsolationForest(
            contamination=0.05,  # 5% аномалий ожидаем
            random_state=42,
            n_estimators=100
        )
        self.anomaly_detector.fit(features_for_anomaly)
        
        # 2. Модель для предсказания объема транзакций (Random Forest)
        # Агрегируем по дням
        daily_volumes = self.transactions.groupby(
            self.transactions['datetime'].dt.date
        ).agg({
            'amount': 'sum',
            'transaction_id': 'count'
        }).reset_index()
        daily_volumes.columns = ['date', 'total_amount', 'num_transactions']
        daily_volumes['date'] = pd.to_datetime(daily_volumes['date'])
        
        # Добавляем признаки
        daily_volumes['day_of_week'] = daily_volumes['date'].dt.dayofweek
        daily_volumes['day_of_month'] = daily_volumes['date'].dt.day
        daily_volumes['is_weekend'] = daily_volumes['day_of_week'].isin([5, 6]).astype(int)
        
        # Признаки для предсказания
        X = daily_volumes[['day_of_week', 'day_of_month', 'is_weekend']]
        y = daily_volumes['total_amount']
        
        self.volume_predictor = RandomForestRegressor(
            n_estimators=100,
            random_state=42,
            max_depth=10
        )
        self.volume_predictor.fit(X, y)
    
    def detect_anomalies(self, recent_days=30):
        # Выявляет аномальные транзакции за последние N дней
        # Фильтруем недавние транзакции
        cutoff_date = datetime.now() - timedelta(days=recent_days)
        recent_transactions = self.transactions[
            self.transactions['datetime'] >= cutoff_date
        ].copy()
        
        if len(recent_transactions) == 0:
            return pd.DataFrame()
        
        # Подготовка признаков
        features = recent_transactions[
            ['amount', 'hour', 'day_of_week', 'is_weekend']
        ].fillna(0)
        
        # Предсказываем аномалии (-1 = аномалия, 1 = норма)
        predictions = self.anomaly_detector.predict(features)
        anomaly_scores = self.anomaly_detector.score_samples(features)
        
        # Добавляем результаты
        recent_transactions['is_anomaly'] = predictions == -1
        recent_transactions['anomaly_score'] = anomaly_scores
        
        # Фильтруем только аномалии
        anomalies = recent_transactions[recent_transactions['is_anomaly']].copy()
        
        # Определяем тип аномалии
        anomalies['anomaly_type'] = anomalies.apply(self._classify_anomaly, axis=1)
        
        return anomalies[[
            'transaction_id', 'datetime', 'type', 'amount', 'currency',
            'payment_system', 'category', 'anomaly_score', 'anomaly_type'
        ]].sort_values('anomaly_score')
    
    def _classify_anomaly(self, row):
        # Классифицирует тип аномалии
        # Вычисляем средние значения
        avg_amount = self.transactions['amount'].mean()
        std_amount = self.transactions['amount'].std()
        
        if row['amount'] > avg_amount + 3 * std_amount:
            return "Необычно большая сумма"
        elif row['hour'] < 6 or row['hour'] > 22:
            return "Необычное время (ночь)"
        elif row['is_weekend'] and row['type'] in ['merchant_settlement', 'salary']:
            return "Бизнес-операция в выходной"
        else:
            return "Необычная комбинация параметров"
    
    def analyze_transaction_patterns(self):
        # Анализирует паттерны транзакций
        #
        # Возвращает статистику по:
        # - Времени суток
        # - Дням недели
        # - Типам транзакций
        # - Валютам
        patterns = {}
        
        # 1. Паттерн по времени суток
        hourly_pattern = self.transactions.groupby('hour').agg({
            'amount': ['sum', 'mean', 'count']
        }).reset_index()
        hourly_pattern.columns = ['hour', 'total_amount', 'avg_amount', 'num_transactions']
        patterns['hourly'] = hourly_pattern
        
        # 2. Паттерн по дням недели
        weekday_pattern = self.transactions.groupby('day_of_week').agg({
            'amount': ['sum', 'mean', 'count']
        }).reset_index()
        weekday_pattern.columns = ['day_of_week', 'total_amount', 'avg_amount', 'num_transactions']
        weekday_pattern['day_name'] = weekday_pattern['day_of_week'].map({
            0: 'Понедельник', 1: 'Вторник', 2: 'Среда', 3: 'Четверг',
            4: 'Пятница', 5: 'Суббота', 6: 'Воскресенье'
        })
        patterns['weekday'] = weekday_pattern
        
        # 3. Паттерн по типам транзакций
        type_pattern = self.transactions.groupby('type').agg({
            'amount': ['sum', 'mean', 'count']
        }).reset_index()
        type_pattern.columns = ['type', 'total_amount', 'avg_amount', 'num_transactions']
        patterns['type'] = type_pattern
        
        # 4. Паттерн по валютам
        currency_pattern = self.transactions.groupby('currency').agg({
            'amount': ['sum', 'mean', 'count']
        }).reset_index()
        currency_pattern.columns = ['currency', 'total_amount', 'avg_amount', 'num_transactions']
        patterns['currency'] = currency_pattern
        
        # 5. Паттерн по времени суток (категории)
        time_of_day_pattern = self.transactions.groupby('time_of_day').agg({
            'amount': ['sum', 'mean', 'count']
        }).reset_index()
        time_of_day_pattern.columns = ['time_of_day', 'total_amount', 'avg_amount', 'num_transactions']
        patterns['time_of_day'] = time_of_day_pattern
        
        return patterns
    
    def predict_future_volumes(self, days_ahead=30):
        # Предсказывает объемы транзакций на будущее
        predictions = []
        today = datetime.now().date()
        
        for i in range(days_ahead):
            future_date = today + timedelta(days=i)
            future_dt = pd.Timestamp(future_date)
            
            # Создаем признаки
            features = pd.DataFrame({
                'day_of_week': [future_dt.dayofweek],
                'day_of_month': [future_dt.day],
                'is_weekend': [1 if future_dt.dayofweek >= 5 else 0]
            })
            
            # Предсказываем
            predicted_volume = self.volume_predictor.predict(features)[0]
            
            predictions.append({
                'date': future_date,
                'predicted_volume': round(predicted_volume, 2),
                'day_of_week': future_dt.day_name(),
                'is_weekend': future_dt.dayofweek >= 5
            })
        
        return pd.DataFrame(predictions)
    
    def detect_trend_changes(self, window_days=7):
        # Выявляет изменения трендов (рост/спад активности)
        # Группируем по дням
        daily_data = self.transactions.groupby(
            self.transactions['datetime'].dt.date
        ).agg({
            'amount': 'sum',
            'transaction_id': 'count'
        }).reset_index()
        daily_data.columns = ['date', 'total_amount', 'num_transactions']
        daily_data['date'] = pd.to_datetime(daily_data['date'])
        
        # Сортируем по дате
        daily_data = daily_data.sort_values('date')
        
        # Считаем скользящее среднее
        daily_data['amount_ma'] = daily_data['total_amount'].rolling(window=window_days).mean()
        daily_data['count_ma'] = daily_data['num_transactions'].rolling(window=window_days).mean()
        
        # Вычисляем изменения
        daily_data['amount_change'] = daily_data['amount_ma'].pct_change() * 100
        daily_data['count_change'] = daily_data['count_ma'].pct_change() * 100
        
        # Фильтруем значительные изменения (>20%)
        recent_data = daily_data.tail(30)  # Последние 30 дней
        
        significant_changes = recent_data[
            (abs(recent_data['amount_change']) > 20) |
            (abs(recent_data['count_change']) > 20)
        ].copy()
        
        # Классифицируем тренды
        significant_changes['trend'] = significant_changes.apply(
            lambda row: 'Резкий рост' if row['amount_change'] > 20 else 'Резкий спад',
            axis=1
        )
        
        return significant_changes[[
            'date', 'total_amount', 'num_transactions', 
            'amount_change', 'count_change', 'trend'
        ]]
    
    def identify_seasonal_patterns(self):
        # Выявляет сезонные паттерны (например, рост в определенные числа месяца)
        # Группируем по дням месяца
        monthly_pattern = self.transactions.groupby('day_of_month').agg({
            'amount': ['sum', 'mean', 'count']
        }).reset_index()
        monthly_pattern.columns = ['day_of_month', 'total_amount', 'avg_amount', 'num_transactions']
        
        # Находим пики активности
        avg_amount = monthly_pattern['total_amount'].mean()
        monthly_pattern['is_peak'] = monthly_pattern['total_amount'] > avg_amount * 1.5
        
        # Выявляем паттерны
        peak_days = monthly_pattern[monthly_pattern['is_peak']]['day_of_month'].tolist()
        
        insights = {
            'peak_days': peak_days,
            'monthly_pattern': monthly_pattern,
            'insights': []
        }
        
        # Генерируем инсайты
        if 1 in peak_days or 2 in peak_days:
            insights['insights'].append("Высокая активность в начале месяца (возможно зарплаты/платежи)")
        
        if 15 in peak_days or 16 in peak_days:
            insights['insights'].append("Пик активности в середине месяца (вторая волна зарплат)")
        
        if any(d in peak_days for d in [28, 29, 30, 31]):
            insights['insights'].append("Рост активности в конце месяца (закрытие периода)")
        
        return insights
    
    def calculate_prediction_accuracy(self):
        # Оценивает точность предсказаний модели
        # Берем последние 30 дней для теста
        test_data = self.transactions[
            self.transactions['datetime'] >= (datetime.now() - timedelta(days=30))
        ]
        
        # Группируем по дням
        actual_daily = test_data.groupby(
            test_data['datetime'].dt.date
        )['amount'].sum().reset_index()
        actual_daily.columns = ['date', 'actual_amount']
        actual_daily['date'] = pd.to_datetime(actual_daily['date'])
        
        # Предсказываем
        predictions = []
        for _, row in actual_daily.iterrows():
            features = pd.DataFrame({
                'day_of_week': [row['date'].dayofweek],
                'day_of_month': [row['date'].day],
                'is_weekend': [1 if row['date'].dayofweek >= 5 else 0]
            })
            pred = self.volume_predictor.predict(features)[0]
            predictions.append(pred)
        
        actual_daily['predicted_amount'] = predictions
        actual_daily['error'] = abs(actual_daily['actual_amount'] - actual_daily['predicted_amount'])
        actual_daily['error_percentage'] = (actual_daily['error'] / actual_daily['actual_amount'] * 100)
        
        # Средняя точность
        avg_accuracy = 100 - actual_daily['error_percentage'].mean()
        
        return {
            'accuracy': round(avg_accuracy, 2),
            'mean_absolute_error': round(actual_daily['error'].mean(), 2),
            'predictions_df': actual_daily
        }
    
    def get_top_accounts_by_activity(self, top_n=10):
        # Топ самых активных счетов
        account_activity = self.transactions.groupby('account_id').agg({
            'amount': ['sum', 'mean', 'count'],
            'transaction_id': 'count'
        }).reset_index()
        account_activity.columns = ['account_id', 'total_amount', 'avg_amount', 'num_transactions_sum', 'num_transactions']
        account_activity = account_activity.sort_values('total_amount', ascending=False).head(top_n)
        
        return account_activity
    
    def detect_unusual_patterns_realtime(self):
        # Обнаруживает необычные паттерны в реальном времени
        # (последние 24 часа)
        # Берем последние 24 часа
        last_24h = self.transactions[
            self.transactions['datetime'] >= (datetime.now() - timedelta(hours=24))
        ]
        
        if len(last_24h) == 0:
            return {"alerts": [], "status": "no_data"}
        
        alerts = []
        
        # 1. Проверка объема
        last_24h_volume = last_24h['amount'].sum()
        avg_daily_volume = self.transactions.groupby(
            self.transactions['datetime'].dt.date
        )['amount'].sum().mean()
        
        if last_24h_volume > avg_daily_volume * 1.5:
            alerts.append({
                'type': 'HIGH_VOLUME',
                'severity': 'WARNING',
                'message': f"Объем транзакций за последние 24ч выше обычного на {((last_24h_volume/avg_daily_volume - 1) * 100):.0f}%",
                'value': last_24h_volume
            })
        elif last_24h_volume < avg_daily_volume * 0.5:
            alerts.append({
                'type': 'LOW_VOLUME',
                'severity': 'WARNING',
                'message': f"Объем транзакций за последние 24ч ниже обычного на {((1 - last_24h_volume/avg_daily_volume) * 100):.0f}%",
                'value': last_24h_volume
            })
        
        # 2. Проверка количества транзакций
        last_24h_count = len(last_24h)
        avg_daily_count = self.transactions.groupby(
            self.transactions['datetime'].dt.date
        ).size().mean()
        
        if last_24h_count < avg_daily_count * 0.5:
            alerts.append({
                'type': 'LOW_TRANSACTION_COUNT',
                'severity': 'WARNING',
                'message': f"Количество транзакций снизилось на {((1 - last_24h_count/avg_daily_count) * 100):.0f}% (возможна техническая проблема)",
                'value': last_24h_count
            })
        
        return {
            'alerts': alerts,
            'status': 'ok' if len(alerts) == 0 else 'issues_detected',
            'last_24h_volume': last_24h_volume,
            'last_24h_count': last_24h_count
        }
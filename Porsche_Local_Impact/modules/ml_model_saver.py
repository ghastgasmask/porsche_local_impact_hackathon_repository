# Модуль для сохранения и загрузки ML-моделей

import pickle
import os
from datetime import datetime
from modules.ml_analyzer import MLAnalyzer

class MLModelSaver:
    # Сохраняет и загружает обученные ML-модели
    
    MODEL_DIR = 'models'
    
    def __init__(self):
        # Создает директорию для моделей если её NETTTTTTTTTTTTTTTTTTTTTTTTTTTTT
        if not os.path.exists(self.MODEL_DIR):
            os.makedirs(self.MODEL_DIR)
    
    def save_models(self, ml_analyzer, filename='ml_models'):
        # Сохраняет обученные ML-модели в pickle
        #
        # Параметры:
        # - ml_analyzer: объект MLAnalyzer
        # - filename: имя файла (без расширения)
        filepath = os.path.join(self.MODEL_DIR, f'{filename}.pickle')
        
        models_dict = {
            'anomaly_detector': ml_analyzer.anomaly_detector,
            'volume_predictor': ml_analyzer.volume_predictor,
            'scaler': ml_analyzer.scaler,
            'saved_at': datetime.now().isoformat()
        }
        
        with open(filepath, 'wb') as f:
            pickle.dump(models_dict, f)
        
        print(f"✅ Модели сохранены в {filepath}")
        return filepath
    
    def load_models(self, filename='ml_models'):
        # Загружает сохраненные ML-модел
        filepath = os.path.join(self.MODEL_DIR, f'{filename}.pickle')
        
        if not os.path.exists(filepath):
            print(f"⚠️ Файл {filepath} не найден!")
            return None
        
        with open(filepath, 'rb') as f:
            models_dict = pickle.load(f)
        
        print(f"✅ Модели загружены из {filepath}")
        return models_dict
    
    def create_ml_analyzer_from_saved(self, transactions_df, accounts_df, filename='ml_models'):
        # Создает MLAnalyzer с загруженными модел
        ml_analyzer = MLAnalyzer(transactions_df, accounts_df)
        
        models_dict = self.load_models(filename)
        
        if models_dict is not None:
            ml_analyzer.anomaly_detector = models_dict['anomaly_detector']
            ml_analyzer.volume_predictor = models_dict['volume_predictor']
            ml_analyzer.scaler = models_dict['scaler']
            return ml_analyzer
        
        return ml_analyzer
    
    def model_exists(self, filename='ml_models'):
        # Проверяет существование сохраненной модели
        filepath = os.path.join(self.MODEL_DIR, f'{filename}.pickle')
        return os.path.exists(filepath)
    
    def get_model_info(self, filename='ml_models'):
        # Возвращает информацию о сохраненной модели
        filepath = os.path.join(self.MODEL_DIR, f'{filename}.pickle')
        
        if not os.path.exists(filepath):
            return None
        
        models_dict = self.load_models(filename)
        
        return {
            'filename': filename,
            'filepath': filepath,
            'saved_at': models_dict.get('saved_at'),
            'file_size_mb': os.path.getsize(filepath) / (1024 * 1024)
        }
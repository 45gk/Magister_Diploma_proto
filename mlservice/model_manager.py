"""
Модуль для управления моделью ML-сервиса.
Загрузка модели, предсказания, валидация данных.
"""

import os
import json
import pickle
from pathlib import Path
from datetime import datetime
import logging

import pandas as pd
import numpy as np
from catboost import CatBoostClassifier
import joblib

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Пути
MODEL_DIR = Path('/app/models')

MODEL_PATH = MODEL_DIR / 'catboost_default_risk.pkl'
ENCODER_PATH = MODEL_DIR / 'label_encoder.pkl'
FEATURES_PATH = MODEL_DIR / 'feature_columns.json'
STATUS_PATH = MODEL_DIR / 'model_status.json'

# Глобальная переменная для кэширования модели
_model_cache = None
_encoders_cache = None
_features_cache = None


def load_model() -> CatBoostClassifier:
    """Загрузка модели из файла"""
    global _model_cache
    
    if _model_cache is not None:
        return _model_cache
    
    if not MODEL_PATH.exists():
        raise FileNotFoundError(f"Model file not found: {MODEL_PATH}")
    
    _model_cache = joblib.load(MODEL_PATH)
    logger.info(f"Model loaded from {MODEL_PATH}")
    
    return _model_cache


def load_encoders() -> dict:
    """Загрузка label encoders"""
    global _encoders_cache
    
    if _encoders_cache is not None:
        return _encoders_cache
    
    if not ENCODER_PATH.exists():
        raise FileNotFoundError(f"Encoders file not found: {ENCODER_PATH}")
    
    with open(ENCODER_PATH, 'rb') as f:
        _encoders_cache = pickle.load(f)
    
    logger.info(f"Encoders loaded from {ENCODER_PATH}")
    
    return _encoders_cache


def load_features() -> dict:
    """Загрузка информации о признаках"""
    global _features_cache
    
    if _features_cache is not None:
        return _features_cache
    
    if not FEATURES_PATH.exists():
        raise FileNotFoundError(f"Features info not found: {FEATURES_PATH}")
    
    with open(FEATURES_PATH, 'r') as f:
        _features_cache = json.load(f)
    
    logger.info(f"Features info loaded from {FEATURES_PATH}")
    
    return _features_cache


def get_model_status() -> dict:
    """Получение статуса модели"""
    status = {
        'version': 'v1.0.0',
        'status': 'not_loaded',
        'last_trained': None,
        'metrics': {},
        'loaded_at': datetime.now().isoformat()
    }
    
    if STATUS_PATH.exists():
        with open(STATUS_PATH, 'r') as f:
            status = json.load(f)
    
    # Обновляем статус загрузки
    if _model_cache is not None:
        status['status'] = 'loaded_in_memory'
    
    return status


def preprocess_input_features(features: dict) -> pd.DataFrame:
    """
    Предобработка входных признаков для предсказания.
    Приводит к формату, который использовался при обучении.
    """
    # Создаем DataFrame
    df = pd.DataFrame([features])
    
    # Загружаем информацию о признаках
    features_info = load_features()
    cat_features = [col for col, idx in 
                   zip(features_info['columns'], features_info['categorical_indices'])]
    
    # Загружаем encoders
    encoders = load_encoders()
    
    # Кодируем категориальные признаки
    le = None
    for col in cat_features:
        if col in df.columns:
            df[col] = df[col].astype(str)
            if col in encoders:
                le = pickle.loads(encoders[col])
                df[col] = le.transform(df[col])
    
    # Заполняем пропуски
    df = df.fillna(-1)
    
    # Выбираем только нужные колонки в правильном порядке
    expected_columns = features_info['columns']
    df = df[expected_columns]
    
    return df


def predict_single(features: dict) -> dict:
    """
    Предсказание для одной записи.
    Возвращает вероятность дефолта и дополнительную информацию.
    """
    try:
        # Загружаем модель
        model = load_model()
        
        # Предобрабатываем входные данные
        df = preprocess_input_features(features)
        
        # Делаем предсказание
        proba = model.predict_proba(df)[0, 1]
        prediction = int(proba >= 0.5)
        
        # Получаем feature importances
        importances = model.get_feature_importance(df)
        feature_importances = dict(zip(df.columns, importances.tolist()))
        
        # Нормализуем importances
        total = sum(abs(v) for v in feature_importances.values())
        if total > 0:
            feature_importances = {k: round(v / total, 4) for k, v in feature_importances.items()}
        
        return {
            'success': True,
            'default_probability': round(float(proba), 4),
            'prediction': prediction,
            'confidence': round(max(0.01, min(0.99, 0.65 + 0.3 * abs(0.5 - proba))), 4),
            'feature_importances': feature_importances,
            'model_version': 'v1.0.0',
            'generated_at': datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Prediction failed: {e}")
        return {
            'success': False,
            'error': str(e)
        }


def predict_batch(features_list: list) -> dict:
    """
    Батч предсказание для нескольких записей.
    """
    try:
        model = load_model()
        
        # Предобрабатываем все данные
        dfs = []
        for features in features_list:
            df = preprocess_input_features(features)
            dfs.append(df)
        
        combined_df = pd.concat(dfs, ignore_index=True)
        
        # Делаем предсказания
        probas = model.predict_proba(combined_df)[:, 1]
        predictions = (probas >= 0.5).astype(int)
        
        results = []
        for i, (proba, pred) in enumerate(zip(probas, predictions)):
            results.append({
                'index': i,
                'default_probability': round(float(proba), 4),
                'prediction': int(pred),
                'confidence': round(max(0.01, min(0.99, 0.65 + 0.3 * abs(0.5 - proba))), 4)
            })
        
        return {
            'success': True,
            'total_predictions': len(results),
            'predictions': results,
            'model_version': 'v1.0.0',
            'generated_at': datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Batch prediction failed: {e}")
        return {
            'success': False,
            'error': str(e)
        }


def validate_model() -> bool:
    """Проверка доступности модели"""
    try:
        model = load_model()
        features = load_features()
        return model is not None and features is not None
    except Exception as e:
        logger.error(f"Model validation failed: {e}")
        return False


if __name__ == '__main__':
    # Тестовая функция
    print("Testing model manager...")
    
    status = get_model_status()
    print(f"Model status: {status}")
    
    if validate_model():
        print("Model is ready for predictions")
        
        # Тестовое предсказание
        test_features = {
            'amt_income_total': 50000,
            'amt_credit': 200000,
            'amt_annuity': 5000,
            'cnt_children': 1,
            'code_gender': 'F',
            'flag_own_car': 'N',
            'flag_own_realty': 'Y',
            'days_birth': -15000,
            'days_employed': -5000,
            'ext_source_1': 0.5,
            'ext_source_2': 0.6,
            'ext_source_3': 0.4,
            'region_rating_client': 2,
            'organization_type': 'Business Entity',
            'pos_cash_balance_avg': 10000,
            'credit_card_balance_avg': 20000,
            'bureau_credit_sum_avg': 50000,
            'prev_app_annuity_avg': 3000,
        }
        
        result = predict_single(test_features)
        print(f"Test prediction: {result}")
    else:
        print("Model is not ready")

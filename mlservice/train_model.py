"""
Модуль для обучения ML-модели предсказания дефолта.
Использует CatBoostClassifier как в original notebook.
"""

import os
import pickle
import json
from pathlib import Path
from datetime import datetime
import logging

import pandas as pd
import numpy as np
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import train_test_split
from sklearn.metrics import roc_auc_score
from catboost import CatBoostClassifier
import joblib

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Пути
MODEL_DIR = Path('/app/models')
MODEL_DIR.mkdir(parents=True, exist_ok=True)

MODEL_PATH = MODEL_DIR / 'catboost_default_risk.pkl'
ENCODER_PATH = MODEL_DIR / 'label_encoder.pkl'
FEATURES_PATH = MODEL_DIR / 'feature_columns.json'

# Статус модели
MODEL_STATUS = {
    'version': 'v1.0.0',
    'status': 'not_trained',
    'last_trained': None,
    'metrics': {}
}


def load_training_data_from_csv(csv_path: str = None) -> pd.DataFrame:
    """Загрузка данных из CSV файла (для прототипа)"""
    if csv_path is None:
        # Прототипные данные
        logger.info("Using prototype data (no CSV provided)")
        return None
    
    if os.path.exists(csv_path):
        return pd.read_csv(csv_path)
    return None


def load_training_data_from_greenplum():
    """Загрузка данных из Greenplum training_mart"""
    try:
        import psycopg2
        from psycopg2.extras import RealDictCursor
        
        conn = psycopg2.connect(
            host=os.environ.get('GREENPLUM_HOST', 'gpdb'),
            port=os.environ.get('GREENPLUM_PORT', '5432'),
            database=os.environ.get('GREENPLUM_DB', 'bank_dwh'),
            user=os.environ.get('GREENPLUM_USER', 'bank_user'),
            password=os.environ.get('GREENPLUM_PASSWORD', 'bank_pass')
        )
        
        query = """
            SELECT * FROM training_mart.homecredit_features
        """
        
        df = pd.read_sql(query, conn)
        conn.close()
        
        logger.info(f"Loaded {len(df)} records from Greenplum")
        return df
        
    except Exception as e:
        logger.error(f"Error loading from Greenplum: {e}")
        return None


def preprocess_data(df: pd.DataFrame):
    """
    Предобработка данных как в original notebook.
    Возвращает: X_train, X_valid, y_train, y_valid, features_columns, cat_features_indices
    """
    if df is None or df.empty:
        raise ValueError("Empty dataframe provided")
    
    # Проверяем наличие целевой переменной
    if 'target' not in df.columns:
        raise ValueError("Target column not found in dataframe")
    
    # Получаем целевую переменную
    target = df['target']
    
    # Удаляем ID и target из признаков
    df_features = df.drop(columns=['sk_id_curr', 'target'])
    
    # Определяем категориальные признаки
    cat_features = [col for col in df_features.columns if df_features[col].dtype == 'object']
    
    # Кодируем категориальные признаки
    le = LabelEncoder()
    
    # Сохраняем encoder
    encoders = {}
    for col in cat_features:
        df_features[col] = df_features[col].astype(str)
        df_features[col] = le.fit_transform(df_features[col])
        encoders[col] = pickle.dumps(le)
    
    # Сохраняем label encoder
    with open(ENCODER_PATH, 'wb') as f:
        pickle.dump(encoders, f)
    
    # Заполняем пропуски
    df_features = df_features.fillna(-1)
    
    # Получаем индексы категориальных признаков
    all_columns = df_features.columns.tolist()
    cat_feature_indices = [all_columns.index(col) for col in cat_features]
    
    # Сохраняем список колонок
    with open(FEATURES_PATH, 'w') as f:
        json.dump({
            'columns': all_columns,
            'categorical_indices': cat_feature_indices
        }, f)
    
    # Разделяем на train/valid
    X_train, X_valid, y_train, y_valid = train_test_split(
        df_features, target,
        test_size=0.1,
        random_state=17,
        stratify=target
    )
    
    logger.info(f"Train size: {len(X_train)}, Valid size: {len(X_valid)}")
    logger.info(f"Cat features: {cat_features}")
    logger.info(f"Cat feature indices: {cat_feature_indices}")
    
    return X_train, X_valid, y_train, y_valid, all_columns, cat_feature_indices


def train_model(
    X_train: pd.DataFrame,
    y_train: pd.Series,
    X_valid: pd.DataFrame,
    y_valid: pd.Series,
    cat_features_indices: list,
    n_iterations: int = 1000
) -> CatBoostClassifier:
    """
    Обучение CatBoost модели
    """
    logger.info("Training CatBoost model...")
    
    model = CatBoostClassifier(
        iterations=n_iterations,
        learning_rate=0.1,
        depth=7,
        l2_leaf_reg=40,
        bootstrap_type='Bernoulli',
        subsample=0.7,
        scale_pos_weight=5,
        eval_metric='AUC',
        metric_period=50,
        od_type='Iter',
        od_wait=45,
        random_seed=17,
        allow_writing_files=False,
        verbose=True
    )
    
    model.fit(
        X_train, y_train,
        eval_set=(X_valid, y_valid),
        cat_features=cat_features_indices,
        use_best_model=True,
        verbose=True
    )
    
    return model


def evaluate_model(model: CatBoostClassifier, X_valid: pd.DataFrame, y_valid: pd.Series) -> dict:
    """
    Оценка модели
    """
    y_pred_proba = model.predict_proba(X_valid)[:, 1]
    auc = roc_auc_score(y_valid, y_pred_proba)
    
    metrics = {
        'auc': round(auc, 4),
        'evaluated_at': datetime.now().isoformat()
    }
    
    logger.info(f"Model AUC: {auc:.4f}")
    
    return metrics


def save_model(model: CatBoostClassifier, metrics: dict):
    """
    Сохранение модели и метрик
    """
    joblib.dump(model, MODEL_PATH)
    
    # Обновляем статус
    MODEL_STATUS['status'] = 'trained'
    MODEL_STATUS['last_trained'] = datetime.now().isoformat()
    MODEL_STATUS['metrics'] = metrics
    
    status_path = MODEL_DIR / 'model_status.json'
    with open(status_path, 'w') as f:
        json.dump(MODEL_STATUS, f, indent=2)
    
    logger.info(f"Model saved to {MODEL_PATH}")
    logger.info(f"Model status: {MODEL_STATUS}")


def train_pipeline():
    """
    Полный пайплайн обучения модели
    """
    global MODEL_STATUS
    
    try:
        # 1. Загрузка данных
        logger.info("Step 1: Loading training data...")
        df = load_training_data_from_greenplum()
        
        if df is None or df.empty:
            logger.warning("No data from Greenplum, using prototype data")
            # Прототипные данные
            df = pd.DataFrame({
                'sk_id_curr': range(1, 1001),
                'target': np.random.choice([0, 1], 1000, p=[0.8, 0.2]),
                'amt_income_total': np.random.uniform(20000, 500000, 1000),
                'amt_credit': np.random.uniform(50000, 1000000, 1000),
                'amt_annuity': np.random.uniform(1000, 50000, 1000),
                'cnt_children': np.random.randint(0, 6, 1000),
                'code_gender': np.random.choice(['M', 'F'], 1000),
                'flag_own_car': np.random.choice(['Y', 'N'], 1000),
                'flag_own_realty': np.random.choice(['Y', 'N'], 1000),
                'days_birth': np.random.randint(-20000, -5000, 1000),
                'days_employed': np.random.randint(-10000, -100, 1000),
                'ext_source_1': np.random.uniform(0, 1, 1000),
                'ext_source_2': np.random.uniform(0, 1, 1000),
                'ext_source_3': np.random.uniform(0, 1, 1000),
                'region_rating_client': np.random.randint(1, 4, 1000),
                'organization_type': np.random.choice(['Business Entity', 'Industry', 'Trade', 'Service'], 1000),
                'pos_cash_balance_avg': np.random.uniform(0, 50000, 1000),
                'credit_card_balance_avg': np.random.uniform(0, 100000, 1000),
                'bureau_credit_sum_avg': np.random.uniform(0, 200000, 1000),
                'prev_app_annuity_avg': np.random.uniform(0, 30000, 1000),
            })
        
        # 2. Предобработка
        logger.info("Step 2: Preprocessing data...")
        X_train, X_valid, y_train, y_valid, feature_columns, cat_indices = preprocess_data(df)
        
        # 3. Обучение
        logger.info("Step 3: Training model...")
        model = train_model(X_train, y_train, X_valid, y_valid, cat_indices)
        
        # 4. Оценка
        logger.info("Step 4: Evaluating model...")
        metrics = evaluate_model(model, X_valid, y_valid)
        
        # 5. Сохранение
        logger.info("Step 5: Saving model...")
        save_model(model, metrics)
        
        MODEL_STATUS['status'] = 'ready'
        
        return {
            'success': True,
            'model_version': MODEL_STATUS['version'],
            'metrics': metrics,
            'feature_count': len(feature_columns),
            'model_path': str(MODEL_PATH)
        }
        
    except Exception as e:
        logger.error(f"Training failed: {e}")
        MODEL_STATUS['status'] = 'failed'
        return {
            'success': False,
            'error': str(e),
            'model_version': MODEL_STATUS['version']
        }


if __name__ == '__main__':
    result = train_pipeline()
    print(f"\nTraining result: {result}")

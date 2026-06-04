from __future__ import annotations

import hashlib
from pathlib import Path
from datetime import datetime, timedelta

import pandas as pd
import numpy as np
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.utils.dates import days_ago

DATA_DIR = Path('/opt/airflow/dags/data')
DATA_DIR.mkdir(parents=True, exist_ok=True)

HOME_CREDIT_DATA_DIR = Path('/opt/airflow/dags/data/homecredit_data')
HOME_CREDIT_DATA_DIR.mkdir(parents=True, exist_ok=True)

# Пути к файлам HomeCredit
HOME_CREDIT_FILES = {
    'application_train': HOME_CREDIT_DATA_DIR / 'application_train.csv',
    'application_test': HOME_CREDIT_DATA_DIR / 'application_test.csv',
    'bureau': HOME_CREDIT_DATA_DIR / 'bureau.csv',
    'bureau_balance': HOME_CREDIT_DATA_DIR / 'bureau_balance.csv',
    'credit_card': HOME_CREDIT_DATA_DIR / 'credit_card_balance.csv',
    'pos_cash': HOME_CREDIT_DATA_DIR / 'POS_CASH_balance.csv',
    'previous_app': HOME_CREDIT_DATA_DIR / 'previous_application.csv',
    'installments': HOME_CREDIT_DATA_DIR / 'installments_payments.csv',
}


def _artifact(name: str) -> Path:
    return DATA_DIR / name


def extract_homecredit_data(**context):
    """
    Извлечение данных из файлов HomeCredit.
    Читаем только первые 100000 строк для прототипа.
    """
    print("Extracting HomeCredit data from files...")
    
    # Читаем application_train (с целевой переменной)
    print("Reading application_train.csv...")
    app_train = pd.read_csv(
        HOME_CREDIT_FILES['application_train'],
        nrows=100000  # Прототип: читаем только первые 100к строк
    )
    
    # Читаем application_test
    print("Reading application_test.csv...")
    app_test = pd.read_csv(
        HOME_CREDIT_FILES['application_test'],
        nrows=100000
    )
    
    # Читаем bureau
    print("Reading bureau.csv...")
    bureau = pd.read_csv(HOME_CREDIT_FILES['bureau'], nrows=200000)
    
    # Читаем bureau_balance
    print("Reading bureau_balance.csv...")
    bureau_balance = pd.read_csv(HOME_CREDIT_FILES['bureau_balance'], nrows=500000)
    
    # Читаем credit_card
    print("Reading credit_card_balance.csv...")
    credit_card = pd.read_csv(HOME_CREDIT_FILES['credit_card'], nrows=200000)
    
    # Читаем POS_CASH
    print("Reading POS_CASH_balance.csv...")
    pos_cash = pd.read_csv(HOME_CREDIT_FILES['pos_cash'], nrows=200000)
    
    # Читаем previous_application
    print("Reading previous_application.csv...")
    prev_app = pd.read_csv(HOME_CREDIT_FILES['previous_app'], nrows=200000)
    
    # Читаем installments_payments
    print("Reading installments_payments.csv...")
    installments = pd.read_csv(HOME_CREDIT_FILES['installments'], nrows=300000)
    
    # Сохраняем в CSV для дальнейшей обработки
    app_train.to_csv(_artifact('homecredit_application_train.csv'), index=False)
    app_test.to_csv(_artifact('homecredit_application_test.csv'), index=False)
    bureau.to_csv(_artifact('homecredit_bureau.csv'), index=False)
    bureau_balance.to_csv(_artifact('homecredit_bureau_balance.csv'), index=False)
    credit_card.to_csv(_artifact('homecredit_credit_card.csv'), index=False)
    pos_cash.to_csv(_artifact('homecredit_pos_cash.csv'), index=False)
    prev_app.to_csv(_artifact('homecredit_previous_app.csv'), index=False)
    installments.to_csv(_artifact('homecredit_installments.csv'), index=False)
    
    print(f"Extracted {len(app_train)} training records, {len(app_test)} test records")
    
    # XCom push
    context['ti'].xcom_push(key='train_rows', value=len(app_train))
    context['ti'].xcom_push(key='test_rows', value=len(app_test))
    context['ti'].xcom_push(key='bureau_rows', value=len(bureau))
    context['ti'].xcom_push(key='extract_artifacts', value=str(DATA_DIR))


def validate_homecredit_data(**context):
    """
    Валидация извлеченных данных.
    """
    artifacts_dir = Path(context['ti'].xcom_pull(key='extract_artifacts', task_ids='extract_homecredit_data'))
    
    required_files = [
        'homecredit_application_train.csv',
        'homecredit_application_test.csv',
        'homecredit_bureau.csv',
        'homecredit_credit_card.csv',
        'homecredit_pos_cash.csv',
        'homecredit_previous_app.csv',
    ]
    
    missing = []
    for file in required_files:
        if not (artifacts_dir / file).exists():
            missing.append(file)
    
    if missing:
        raise ValueError(f"Missing files: {missing}")
    
    print("All required files validated successfully")
    context['ti'].xcom_push(key='validation_status', value='passed')


def transform_homecredit_data(**context):
    """
    Трансформация данных как в original notebook.
    Агрегация признаков и создание финального датасета.
    """
    print("Transforming HomeCredit data...")
    
    # Загружаем данные
    app_train = pd.read_csv(_artifact('homecredit_application_train.csv'))
    app_test = pd.read_csv(_artifact('homecredit_application_test.csv'))
    bureau = pd.read_csv(_artifact('homecredit_bureau.csv'))
    credit_card = pd.read_csv(_artifact('homecredit_credit_card.csv'))
    pos_cash = pd.read_csv(_artifact('homecredit_pos_cash.csv'))
    prev_app = pd.read_csv(_artifact('homecredit_previous_app.csv'))
    
    # Кодируем категориальные признаки
    le = LabelEncoder()
    
    # POS_CASH aggregation
    print("Processing POS_CASH...")
    pos_cash['NAME_CONTRACT_STATUS'] = le.fit_transform(pos_cash['NAME_CONTRACT_STATUS'].astype(str))
    nunique_status = pos_cash[['SK_ID_CURR', 'NAME_CONTRACT_STATUS']].groupby('SK_ID_CURR').nunique()[['NAME_CONTRACT_STATUS']].rename(columns={'NAME_CONTRACT_STATUS': 'NUNIQUE_STATUS_POS_CASH'})
    nunique_status.reset_index(inplace=True)
    pos_cash = pos_cash.merge(nunique_status, how='left', on='SK_ID_CURR')
    pos_cash.drop(['SK_ID_PREV', 'NAME_CONTRACT_STATUS'], axis=1, inplace=True)
    pos_agg = pos_cash.groupby('SK_ID_CURR').mean().reset_index()
    pos_agg.columns = ['pos_' + col if col != 'SK_ID_CURR' else 'SK_ID_CURR' for col in pos_agg.columns]
    
    # Credit card aggregation
    print("Processing Credit Card...")
    credit_card['NAME_CONTRACT_STATUS'] = le.fit_transform(credit_card['NAME_CONTRACT_STATUS'].astype(str))
    nunique_status = credit_card[['SK_ID_CURR', 'NAME_CONTRACT_STATUS']].groupby('SK_ID_CURR').nunique()[['NAME_CONTRACT_STATUS']].rename(columns={'NAME_CONTRACT_STATUS': 'NUNIQUE_STATUS_CREDIT_CARD'})
    nunique_status.reset_index(inplace=True)
    credit_card = credit_card.merge(nunique_status, how='left', on='SK_ID_CURR')
    credit_card.drop(['SK_ID_PREV', 'NAME_CONTRACT_STATUS'], axis=1, inplace=True)
    cc_agg = credit_card.groupby('SK_ID_CURR').mean().reset_index()
    cc_agg.columns = ['cc_' + col if col != 'SK_ID_CURR' else 'SK_ID_CURR' for col in cc_agg.columns]
    
    # Bureau aggregation
    print("Processing Bureau...")
    bureau_cat_features = [f for f in bureau.columns if bureau[f].dtype == 'object']
    for f in bureau_cat_features:
        bureau[f] = le.fit_transform(bureau[f].astype(str))
        nunique = bureau[['SK_ID_CURR', f]].groupby('SK_ID_CURR').nunique()[[f]].rename(columns={f: 'NUNIQUE_' + f + '_bureau'})
        nunique.reset_index(inplace=True)
        bureau = bureau.merge(nunique, how='left', on='SK_ID_CURR')
        bureau.drop([f], axis=1, inplace=True)
    bureau.drop(['SK_ID_BUREAU'], axis=1, inplace=True)
    bureau_agg = bureau.groupby('SK_ID_CURR').mean().reset_index()
    bureau_agg.columns = ['bureau_' + col if col != 'SK_ID_CURR' else 'SK_ID_CURR' for col in bureau_agg.columns]
    
    # Previous application aggregation
    print("Processing Previous Application...")
    prev_app_cat_features = [f for f in prev_app.columns if prev_app[f].dtype == 'object']
    for f in prev_app_cat_features:
        prev_app[f] = le.fit_transform(prev_app[f].astype(str))
        nunique = prev_app[['SK_ID_CURR', f]].groupby('SK_ID_CURR').nunique()[[f]].rename(columns={f: 'NUNIQUE_' + f + '_prev_app'})
        nunique.reset_index(inplace=True)
        prev_app = prev_app.merge(nunique, how='left', on='SK_ID_CURR')
        prev_app.drop([f], axis=1, inplace=True)
    prev_app.drop(['SK_ID_PREV'], axis=1, inplace=True)
    prev_agg = prev_app.groupby('SK_ID_CURR').mean().reset_index()
    prev_agg.columns = ['prev_' + col if col != 'SK_ID_CURR' else 'SK_ID_CURR' for col in prev_agg.columns]
    
    # Merge all features
    print("Merging features...")
    data_train = app_train.merge(pos_agg, how='left', on='SK_ID_CURR')
    data_train = data_train.merge(cc_agg, how='left', on='SK_ID_CURR')
    data_train = data_train.merge(bureau_agg, how='left', on='SK_ID_CURR')
    data_train = data_train.merge(prev_agg, how='left', on='SK_ID_CURR')
    
    data_test = app_test.merge(pos_agg, how='left', on='SK_ID_CURR')
    data_test = data_test.merge(cc_agg, how='left', on='SK_ID_CURR')
    data_test = data_test.merge(bureau_agg, how='left', on='SK_ID_CURR')
    data_test = data_test.merge(prev_agg, how='left', on='SK_ID_CURR')
    
    # Подготовка данных для обучения
    target_train = data_train['TARGET']
    data_train.drop(['SK_ID_CURR', 'TARGET'], axis=1, inplace=True)
    data_test_ids = data_test['SK_ID_CURR']
    data_test.drop(['SK_ID_CURR'], axis=1, inplace=True)
    
    # Кодируем оставшиеся категориальные признаки
    cat_features = [f for f in data_train.columns if data_train[f].dtype == 'object']
    for col in cat_features:
        data_train[col] = le.fit_transform(data_train[col].astype(str))
        data_test[col] = le.fit_transform(data_test[col].astype(str))
    
    # Заполняем пропуски
    data_train.fillna(-1, inplace=True)
    data_test.fillna(-1, inplace=True)
    
    # Сохраняем финальные датасеты
    data_train.to_csv(_artifact('homecredit_train_features.csv'), index=False)
    data_test.to_csv(_artifact('homecredit_test_features.csv'), index=False)
    target_train.to_csv(_artifact('homecredit_train_target.csv'), index=False)
    data_test_ids.to_csv(_artifact('homecredit_test_ids.csv'), index=False)
    
    print(f"Training features shape: {data_train.shape}")
    print(f"Test features shape: {data_test.shape}")
    print(f"Target shape: {target_train.shape}")
    
    # XCom push
    context['ti'].xcom_push(key='train_features_shape', value=str(data_train.shape))
    context['ti'].xcom_push(key='test_features_shape', value=str(data_test.shape))
    context['ti'].xcom_push(key='cat_features', value=str(cat_features))


def create_training_summary(**context):
    """
    Создание краткого отчета о training dataset.
    """
    train_shape = eval(context['ti'].xcom_pull(key='train_features_shape', task_ids='transform_homecredit_data'))
    summary = pd.DataFrame({
        'dataset': ['homecredit_training_raw_files'],
        'created_at': [datetime.now().isoformat()],
        'status': ['ready'],
        'train_rows': [train_shape[0]],
        'train_features': [train_shape[1]],
        'source_files': ['application_train.csv, bureau.csv, credit_card_balance.csv, POS_CASH_balance.csv, previous_application.csv']
    })
    
    out = _artifact('homecredit_training_summary.csv')
    summary.to_csv(out, index=False)
    context['ti'].xcom_push(key='summary_path', value=str(out))


def notify_homecredit_etl_complete(**context):
    """Уведомление о завершении ETL из файлов HomeCredit"""
    summary_path = context['ti'].xcom_pull(key='summary_path', task_ids='create_training_summary')
    print(f"HomeCredit ETL completed!")
    print(f"Training dataset ready: {summary_path}")
    print("Next step: Train model using /ml/train endpoint")


# DAG для ETL процесса из файлов HomeCredit
with DAG(
    dag_id='etl_homecredit_from_files',
    start_date=days_ago(1),
    schedule_interval=None,
    catchup=False,
    tags=['homecredit', 'files', 'etl'],
    default_args={
        'retries': 1,
        'retry_delay': timedelta(minutes=5),
    },
) as dag:
    
    from sklearn.preprocessing import LabelEncoder
    
    t1 = PythonOperator(
        task_id='extract_homecredit_data',
        python_callable=extract_homecredit_data,
    )
    
    t2 = PythonOperator(
        task_id='validate_homecredit_data',
        python_callable=validate_homecredit_data,
    )
    
    t3 = PythonOperator(
        task_id='transform_homecredit_data',
        python_callable=transform_homecredit_data,
    )
    
    t4 = PythonOperator(
        task_id='create_training_summary',
        python_callable=create_training_summary,
    )
    
    t5 = PythonOperator(
        task_id='notify_complete',
        python_callable=notify_homecredit_etl_complete,
    )
    
    # Порядок выполнения
    t1 >> t2 >> t3 >> t4 >> t5

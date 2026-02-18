from __future__ import annotations

import hashlib
from pathlib import Path

import pandas as pd
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.utils.dates import days_ago

DATA_DIR = Path('/opt/airflow/dags/data')
DATA_DIR.mkdir(parents=True, exist_ok=True)


EXPECTED_COLUMNS = ['client_id', 'age', 'income', 'debt_to_income', 'bki_request_cnt', 'app_date']


def _artifact(name: str) -> Path:
    return DATA_DIR / name


def extract_raw(**context):
    raw = pd.DataFrame([
        {'client_id': 1, 'age': 30, 'income': 100000, 'debt_to_income': 0.31, 'bki_request_cnt': 2, 'app_date': '2026-02-18'},
        {'client_id': 2, 'age': 45, 'income': 55000, 'debt_to_income': 0.55, 'bki_request_cnt': 4, 'app_date': '2026-02-18'},
    ])
    out = _artifact('raw.csv')
    raw.to_csv(out, index=False)
    context['ti'].xcom_push(key='extract_artifact', value=str(out))


def validate_schema(**context):
    raw_path = Path(context['ti'].xcom_pull(key='extract_artifact', task_ids='extract_raw'))
    data = pd.read_csv(raw_path)
    missing = [c for c in EXPECTED_COLUMNS if c not in data.columns]
    if missing:
        raise ValueError(f'Missing required columns: {missing}')
    context['ti'].xcom_push(key='row_count', value=len(data))


def clean_data(**context):
    raw_path = Path(context['ti'].xcom_pull(key='extract_artifact', task_ids='extract_raw'))
    data = pd.read_csv(raw_path).drop_duplicates().fillna({'debt_to_income': 0.4})
    out = _artifact('clean.csv')
    data.to_csv(out, index=False)
    context['ti'].xcom_push(key='clean_artifact', value=str(out))


def transform_features(**context):
    clean_path = Path(context['ti'].xcom_pull(key='clean_artifact', task_ids='clean_data'))
    data = pd.read_csv(clean_path)
    data['risk_bucket'] = pd.cut(data['debt_to_income'], bins=[0, 0.3, 0.5, 1.0], labels=['low', 'medium', 'high'])
    out = _artifact('features.csv')
    data.to_csv(out, index=False)
    checksum = hashlib.md5(out.read_bytes()).hexdigest()
    context['ti'].xcom_push(key='features_artifact', value=str(out))
    context['ti'].xcom_push(key='features_checksum', value=checksum)


def load_dwh(**context):
    # Prototype placeholder: in production connect to PostgreSQL and upsert into DWH tables.
    features_path = context['ti'].xcom_pull(key='features_artifact', task_ids='transform_features')
    context['ti'].xcom_push(key='load_summary', value={'features_path': features_path, 'status': 'loaded_prototype'})


def post_load_checks(**context):
    row_count = context['ti'].xcom_pull(key='row_count', task_ids='validate_schema')
    checksum = context['ti'].xcom_pull(key='features_checksum', task_ids='transform_features')
    if row_count < 1:
        raise ValueError('No rows processed')
    context['ti'].xcom_push(key='checks', value={'row_count': row_count, 'checksum': checksum})


with DAG(
    dag_id='etl_santander',
    start_date=days_ago(1),
    schedule_interval=None,
    catchup=False,
    tags=['credit', 'prototype'],
) as dag:
    t1 = PythonOperator(task_id='extract_raw', python_callable=extract_raw)
    t2 = PythonOperator(task_id='validate_schema', python_callable=validate_schema)
    t3 = PythonOperator(task_id='clean_data', python_callable=clean_data)
    t4 = PythonOperator(task_id='transform_features', python_callable=transform_features)
    t5 = PythonOperator(task_id='load_dwh', python_callable=load_dwh)
    t6 = PythonOperator(task_id='post_load_checks', python_callable=post_load_checks)

    t1 >> t2 >> t3 >> t4 >> t5 >> t6

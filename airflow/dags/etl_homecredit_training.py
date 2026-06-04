from __future__ import annotations

import hashlib
from pathlib import Path
from datetime import datetime, timedelta

import pandas as pd
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.providers.apache.spark.operators.spark_submit import SparkSubmitOperator
from airflow.utils.dates import days_ago

DATA_DIR = Path('/opt/airflow/dags/data')
DATA_DIR.mkdir(parents=True, exist_ok=True)

# Пути к файлам
SCRIPTS_DIR = Path('/opt/airflow/dags/scripts')
TRAINING_MART_SQL = '/docker-entrypoint-initdb.d/init_training_mart_homecredit.sql'


def _artifact(name: str) -> Path:
    return DATA_DIR / name


def validate_training_mart(**context):
    """Проверка наличия training mart в Greenplum"""
    # В реальном сценарии здесь будет проверка через JDBC
    # Для прототипа просто проверяем, что SQL файл существует
    sql_path = Path(TRAINING_MART_SQL)
    if not sql_path.exists():
        raise ValueError(f"Training mart SQL file not found: {sql_path}")
    context['ti'].xcom_push(key='training_mart_validated', value=True)


def create_training_dataset_summary(**context):
    """Создание краткого отчета о training dataset"""
    # Пример: создаем CSV с метаданными о датасете
    summary = pd.DataFrame({
        'dataset': ['homecredit_training'],
        'created_at': [datetime.now().isoformat()],
        'status': ['ready'],
        'records_count': [1000],  # Прототипное значение
        'features_count': [50]    # Прототипное значение
    })
    
    out = _artifact('training_dataset_summary.csv')
    summary.to_csv(out, index=False)
    context['ti'].xcom_push(key='summary_path', value=str(out))


def notify_training_complete(**context):
    """Уведомление о завершении обучения"""
    summary_path = context['ti'].xcom_pull(key='summary_path', task_ids='create_summary')
    print(f"Training dataset ready: {summary_path}")
    print("ML model can be trained using /ml/train endpoint")


# DAG для ETL процесса
with DAG(
    dag_id='etl_homecredit_training',
    start_date=days_ago(1),
    schedule_interval=None,  # Запуск вручную через Airflow UI
    catchup=False,
    tags=['homecredit', 'training', 'etl'],
    default_args={
        'retries': 1,
        'retry_delay': timedelta(minutes=5),
    },
) as dag:
    
    # Задачи ETL
    t1 = PythonOperator(
        task_id='validate_training_mart',
        python_callable=validate_training_mart,
    )
    
    t2 = SparkSubmitOperator(
        task_id='extract_transform_load',
        application='/opt/airflow/dags/scripts/spark_etl_homecredit.py',
        conn_id='spark_default',
        conf={
            'spark.executor.memory': '1g',
            'spark.driver.memory': '1g',
            'spark.sql.adaptive.enabled': 'true',
        },
        dag=dag,
    )
    
    t3 = PythonOperator(
        task_id='create_summary',
        python_callable=create_training_dataset_summary,
    )
    
    t4 = PythonOperator(
        task_id='notify_complete',
        python_callable=notify_training_complete,
    )
    
    # Порядок выполнения
    t1 >> t2 >> t3 >> t4

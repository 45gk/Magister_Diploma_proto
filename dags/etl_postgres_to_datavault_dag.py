"""
DAG: PostgreSQL (staging src_*) → Greenplum (Data Vault 2.0).

Предварительно:
  1. scripts/init_staging_home_credit.sql на сервисе db
  2. scripts/init_data_vault_home_credit.sql на сервисе gpdb
  3. Данные в src_application_train (импорт CSV через webapp / COPY)

Переменные окружения (опционально):
  ETL_PG_HOST, ETL_GP_HOST, ETL_ROW_LIMIT, ETL_BATCH_SIZE
"""

from __future__ import annotations

import sys
from datetime import timedelta
from pathlib import Path

from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.utils.dates import days_ago

_DAGS_ROOT = Path(__file__).resolve().parent
_SCRIPTS = _DAGS_ROOT / 'scripts'
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

from etl_postgres_to_datavault.pipeline import (  # noqa: E402
    load_application_train_to_dv,
    load_bureau_balance_to_dv,
    load_bureau_to_dv,
    run_post_load_checks,
    test_connections,
)

default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=3),
}

with DAG(
    dag_id='etl_postgres_to_datavault',
    default_args=default_args,
    description='ETL: Postgres staging → Greenplum Data Vault (Home Credit)',
    schedule_interval=None,
    start_date=days_ago(1),
    catchup=False,
    tags=['etl', 'datavault', 'home_credit'],
) as dag:
    t_check = PythonOperator(
        task_id='test_connections',
        python_callable=test_connections,
    )
    t_app = PythonOperator(
        task_id='load_application_train',
        python_callable=load_application_train_to_dv,
    )
    t_bureau = PythonOperator(
        task_id='load_bureau',
        python_callable=load_bureau_to_dv,
    )
    t_bureau_bal = PythonOperator(
        task_id='load_bureau_balance',
        python_callable=load_bureau_balance_to_dv,
    )
    t_checks = PythonOperator(
        task_id='post_load_checks',
        python_callable=run_post_load_checks,
    )

    t_check >> t_app >> t_bureau >> t_bureau_bal >> t_checks

from datetime import timedelta

from airflow import DAG
from airflow.providers.apache.spark.operators.spark_submit import SparkSubmitOperator
from airflow.utils.dates import days_ago

default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'start_date': days_ago(1),
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

SPARK_CONF = {
    'spark.executor.memory': '512m',
    'spark.driver.memory': '512m',
    'spark.sql.adaptive.enabled': 'true',
}

dag = DAG(
    'spark_data_processing',
    default_args=default_args,
    description='DAG for processing data with Spark',
    schedule_interval=timedelta(days=1),
    catchup=False,
    tags=['spark', 'data_processing'],
)

read_postgres_task = SparkSubmitOperator(
    task_id='read_from_postgres',
    application='/opt/airflow/dags/scripts/spark_read_postgres.py',
    conn_id='spark_default',
    conf=SPARK_CONF,
    dag=dag,
)

read_greenplum_task = SparkSubmitOperator(
    task_id='read_from_greenplum',
    application='/opt/airflow/dags/scripts/spark_read_greenplum.py',
    conn_id='spark_default',
    conf=SPARK_CONF,
    dag=dag,
)

process_data_task = SparkSubmitOperator(
    task_id='process_data',
    application='/opt/airflow/dags/scripts/spark_process_data.py',
    conn_id='spark_default',
    conf=SPARK_CONF,
    dag=dag,
)

read_postgres_task >> process_data_task
read_greenplum_task >> process_data_task

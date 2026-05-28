from airflow import DAG
from airflow.operators.python import PythonOperator
from pyspark.sql import SparkSession
from datetime import datetime


#!/usr/bin/env python3

from pyspark.sql import SparkSession

def gp_test():
    # Создаем Spark сессию
    spark = SparkSession.builder \
        .appName("Read from Greenplum") \
        .config("spark.jars.packages", "org.postgresql:postgresql:42.6.0") \
        .getOrCreate()

    # Параметры подключения к Greenplum (используем PostgreSQL драйвер)
    greenplum_url = "jdbc:postgresql://gpdb:5434/bank_dwh"
    greenplum_properties = {
        "user": "bank_user",
        "password": "bank_pass",
        "driver": "org.postgresql.Driver"
    }

    try:
        # Читаем данные из Data Vault таблицы (замените на реальную таблицу)
        df = spark.read.jdbc(url=greenplum_url, table="test_table", properties=greenplum_properties)

        # Показываем схему и первые строки
        df.printSchema()
        df.show(5)

        print(f"Successfully read {df.count()} rows from Greenplum")

        # Здесь можно добавить обработку данных

    except Exception as e:
        print(f"Error reading from Greenplum: {e}")
        raise

    finally:
        spark.stop()


def run_spark_job():
    spark = SparkSession.builder \
        .appName("Airflow_PySpark_Example") \
        .master("local") \
        .getOrCreate()

    data = [("Alice", 1), ("Bob", 2), ("Charlie", 3)]

    df = spark.createDataFrame(data, ["name", "id"])

    df.show()
    spark.stop()


with DAG(
        dag_id="main",
        start_date=datetime(2023, 10, 1),
        schedule_interval="@daily",
        catchup=False,
) as dag:
    run_pyspark_task = PythonOperator(
        task_id="run_pyspark_task",
        python_callable=run_spark_job,
    )
    run_gp_test_task = PythonOperator(
        task_id="gp_test",
        python_callable=gp_test
    )

run_pyspark_task >> run_gp_test_task

from airflow import DAG
from airflow.operators.python import PythonOperator
from pyspark.sql import SparkSession
from datetime import datetime
from pyspark.sql.functions import col, count, avg



#!/usr/bin/env python3

from pyspark.sql import SparkSession


def pg_test():
    spark = SparkSession.builder \
        .appName("Read from PostgreSQL") \
        .config("spark.jars.packages", "org.postgresql:postgresql:42.6.0") \
        .getOrCreate()

    # Параметры подключения к PostgreSQL
    postgres_url = "jdbc:postgresql://host.docker.internal:5433/bank_dwh"
    postgres_properties = {
        "user": "bank_user",
        "password": "bank_pass",
        "driver": "org.postgresql.Driver"
    }

    try:
        # Читаем данные из таблицы (замените на реальную таблицу)
        # df = spark.read.jdbc(url=postgres_url, table="postgres.public.test_db", properties=postgres_properties)

        df = spark.read \
        .format("jdbc") \
        .option("url", postgres_url) \
        .option("user", "bank_user") \
        .option("password", "bank_pass") \
        .option("dbtable", "public.test_db") \
        .option("driver", "org.postgresql.Driver") \
        .load()

        # Показываем схему и первые строки
        df.printSchema()
        df.show(5)

        print(f"Successfully read {df.count()} rows from PostgreSQL")

        # Здесь можно добавить обработку данных

    except Exception as e:
        print(f"Error reading from PostgreSQL: {e}")
        raise

    finally:
        spark.stop()



def process_data_test():
    # Создаем Spark сессию
    spark = SparkSession.builder \
        .appName("Process Credit Data") \
        .config("spark.jars.packages", "org.postgresql:postgresql:42.6.0") \
        .getOrCreate()

    # Параметры подключения к базам данных
    postgres_url = "jdbc:postgresql://host.docker.internal:5433/bank_dwh"
    greenplum_url = "jdbc:postgresql://host.docker.internal:5434/bank_dwh"
    db_properties = {
        "user": "bank_user",
        "password": "bank_pass",
        "driver": "org.postgresql.Driver"
    }

    try:
        # Пример агрегации данных из разных источников
        # В реальном сценарии здесь будет более сложная логика

        print("Processing credit data with Spark...")

        # Создаем пример DataFrame для демонстрации
        sample_data = [
            (1, 30, 50000, 0.3, "approved"),
            (2, 45, 75000, 0.6, "rejected"),
            (3, 25, 40000, 0.2, "approved"),
            (4, 50, 90000, 0.8, "rejected"),
        ]

        df = spark.createDataFrame(sample_data, ["client_id", "age", "income", "debt_ratio", "status"])

        # Выполняем агрегации
        result = df.groupBy("status").agg(
            count("*").alias("count"),
            avg("age").alias("avg_age"),
            avg("income").alias("avg_income"),
            avg("debt_ratio").alias("avg_debt_ratio")
        )

        result.show()

        print("Data processing completed successfully")

        # В реальном сценарии здесь можно сохранить результаты обратно в базу данных

    except Exception as e:
        print(f"Error processing data: {e}")
        raise

    finally:
        spark.stop()



def gp_test():
    # Создаем Spark сессию
    spark = SparkSession.builder \
        .appName("Read from Greenplum") \
        .config("spark.jars.packages", "org.postgresql:postgresql:42.6.0") \
        .getOrCreate()

    # Параметры подключения к Greenplum (используем PostgreSQL драйвер)
    # postgresql://postgres:123@host.docker.internal/postgres
    # url = "jdbc:postgresql://host.docker.internal:5434/your_database"

    greenplum_url = "jdbc:postgresql://host.docker.internal:5434/bank_dwh"
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
    run_pg_test_task = PythonOperator(
        task_id="pg_test",
        python_callable=pg_test
    )
    run_process_data_task = PythonOperator(
        task_id='process_data_test',
        python_callable=process_data_test
    )

run_pyspark_task >> run_gp_test_task >> run_pg_test_task >> run_process_data_task

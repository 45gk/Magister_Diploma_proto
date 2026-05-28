#!/usr/bin/env python3

from pyspark.sql import SparkSession
from pyspark.sql.functions import col, count, avg

def main():
    # Создаем Spark сессию
    spark = SparkSession.builder \
        .appName("Process Credit Data") \
        .getOrCreate()

    # Параметры подключения к базам данных
    postgres_url = "jdbc:postgresql://db:5432/bank_dwh"
    greenplum_url = "jdbc:postgresql://gpdb:5432/bank_dwh"
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

if __name__ == "__main__":
    main()
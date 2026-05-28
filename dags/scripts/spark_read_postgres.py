#!/usr/bin/env python3

from pyspark.sql import SparkSession

def main():
    # Создаем Spark сессию
    spark = SparkSession.builder \
        .appName("Read from PostgreSQL") \
        .getOrCreate()

    # Параметры подключения к PostgreSQL
    postgres_url = "jdbc:postgresql://db:5433/bank_dwh"
    postgres_properties = {
        "user": "bank_user",
        "password": "bank_pass",
        "driver": "org.postgresql.Driver"
    }

    try:
        # Читаем данные из таблицы (замените на реальную таблицу)
        df = spark.read.jdbc(url=postgres_url, table="public.test_db", properties=postgres_properties)

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

if __name__ == "__main__":
    main()
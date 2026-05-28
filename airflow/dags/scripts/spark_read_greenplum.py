#!/usr/bin/env python3

from pyspark.sql import SparkSession

def main():
    # Создаем Spark сессию
    spark = SparkSession.builder \
        .appName("Read from Greenplum") \
        .getOrCreate()

    # Параметры подключения к Greenplum (используем PostgreSQL драйвер)
    greenplum_url = "jdbc:postgresql://gpdb:5432/bank_dwh"
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

if __name__ == "__main__":
    main()
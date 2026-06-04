#!/usr/bin/env python3
"""
ETL-скрипт для подготовки данных Home Credit к обучению модели.
Использует Spark для обработки больших объемов данных.
"""

from pyspark.sql import SparkSession
from pyspark.sql.functions import (
    col, avg, countDistinct, count, when, mean, sum as spark_sum, 
    max as spark_max, min as spark_min, first
)
from pyspark.sql.window import Window
import sys

def main():
    # Создаем Spark сессию
    spark = SparkSession.builder \
        .appName("ETL HomeCredit Training Data") \
        .config("spark.sql.adaptive.enabled", "true") \
        .config("spark.sql.adaptive.coalescePartitions.enabled", "true") \
        .getOrCreate()

    # Параметры подключения к Greenplum
    greenplum_url = "jdbc:postgresql://gpdb:5432/bank_dwh"
    db_properties = {
        "user": "bank_user",
        "password": "bank_pass",
        "driver": "org.postgresql.Driver"
    }

    try:
        print("Starting ETL process for HomeCredit training data...")

        # ==================== EXTRACT ====================
        print("Step 1: Extracting data from Greenplum...")

        # Загружаем hub_application
        df_hub_application = spark.read.jdbc(
            url=greenplum_url,
            table="dv_hub_application",
            properties=db_properties
        ).alias("hub_app")

        # Загружаем target (только для train)
        df_sat_app_target = spark.read.jdbc(
            url=greenplum_url,
            table="dv_sat_app_target",
            properties=db_properties
        ).alias("sat_target")

        # Загружаем все сателлиты
        df_sat_app_contract = spark.read.jdbc(
            url=greenplum_url,
            table="dv_sat_app_contract",
            properties=db_properties
        ).alias("sat_contract")

        df_sat_app_client = spark.read.jdbc(
            url=greenplum_url,
            table="dv_sat_app_client_profile",
            properties=db_properties
        ).alias("sat_client")

        df_sat_app_process = spark.read.jdbc(
            url=greenplum_url,
            table="dv_sat_app_process",
            properties=db_properties
        ).alias("sat_process")

        df_sat_app_contact = spark.read.jdbc(
            url=greenplum_url,
            table="dv_sat_app_contact_flags",
            properties=db_properties
        ).alias("sat_contact")

        df_sat_app_scores = spark.read.jdbc(
            url=greenplum_url,
            table="dv_sat_app_external_scores",
            properties=db_properties
        ).alias("sat_scores")

        df_sat_app_enquiries = spark.read.jdbc(
            url=greenplum_url,
            table="dv_sat_app_credit_bureau_enquiries",
            properties=db_properties
        ).alias("sat_enquiries")

        df_sat_app_documents = spark.read.jdbc(
            url=greenplum_url,
            table="dv_sat_app_documents",
            properties=db_properties
        ).alias("sat_documents")

        df_sat_app_building = spark.read.jdbc(
            url=greenplum_url,
            table="dv_sat_app_building_social",
            properties=db_properties
        ).alias("sat_building")

        print(f"Loaded {df_hub_application.count()} application records")

        # ==================== TRANSFORM ====================
        print("Step 2: Transforming and aggregating data...")

        # Собираем базовые признаки из hub и сателлитов
        base_features = df_hub_application.select(
            col("hub_app.sk_id_curr"),
            col("hub_app.hk_application")
        ).join(
            df_sat_app_target.select(
                col("sat_target.hk_application"),
                col("sat_target.target").alias("target")
            ),
            on="hk_application",
            how="left"
        ).join(
            df_sat_app_contract.select(
                col("sat_contract.hk_application"),
                col("sat_contract.name_contract_type"),
                col("sat_contract.amt_credit"),
                col("sat_contract.amt_annuity"),
                col("sat_contract.amt_goods_price")
            ),
            on="hk_application",
            how="left"
        ).join(
            df_sat_app_client.select(
                col("sat_client.hk_application"),
                col("sat_client.code_gender"),
                col("sat_client.cnt_children"),
                col("sat_client.cnt_fam_members"),
                col("sat_client.name_type_suite"),
                col("sat_client.name_income_type"),
                col("sat_client.name_education_type"),
                col("sat_client.name_family_status"),
                col("sat_client.name_housing_type"),
                col("sat_client.days_birth"),
                col("sat_client.days_employed"),
                col("sat_client.days_registration"),
                col("sat_client.days_id_publish"),
                col("sat_client.occupation_type"),
                col("sat_client.organization_type"),
                col("sat_client.own_car_age"),
                col("sat_client.flag_own_car"),
                col("sat_client.flag_own_realty")
            ),
            on="hk_application",
            how="left"
        ).join(
            df_sat_app_process.select(
                col("sat_process.hk_application"),
                col("sat_process.weekday_appr_process_start"),
                col("sat_process.hour_appr_process_start"),
                col("sat_process.region_population_relative"),
                col("sat_process.region_rating_client"),
                col("sat_process.region_rating_client_w_city"),
                col("sat_process.reg_region_not_live_region"),
                col("sat_process.reg_region_not_work_region"),
                col("sat_process.live_region_not_work_region"),
                col("sat_process.reg_city_not_live_city"),
                col("sat_process.reg_city_not_work_city"),
                col("sat_process.live_city_not_work_city")
            ),
            on="hk_application",
            how="left"
        ).join(
            df_sat_app_contact.select(
                col("sat_contact.hk_application"),
                col("sat_contact.flag_mobil"),
                col("sat_contact.flag_emp_phone"),
                col("sat_contact.flag_work_phone"),
                col("sat_contact.flag_cont_mobile"),
                col("sat_contact.flag_phone"),
                col("sat_contact.flag_email"),
                col("sat_contact.days_last_phone_change")
            ),
            on="hk_application",
            how="left"
        ).join(
            df_sat_app_scores.select(
                col("sat_scores.hk_application"),
                col("sat_scores.ext_source_1"),
                col("sat_scores.ext_source_2"),
                col("sat_scores.ext_source_3")
            ),
            on="hk_application",
            how="left"
        ).join(
            df_sat_app_enquiries.select(
                col("sat_enquiries.hk_application"),
                col("sat_enquiries.amt_req_credit_bureau_hour"),
                col("sat_enquiries.amt_req_credit_bureau_day"),
                col("sat_enquiries.amt_req_credit_bureau_week"),
                col("sat_enquiries.amt_req_credit_bureau_mon"),
                col("sat_enquiries.amt_req_credit_bureau_qrt"),
                col("sat_enquiries.amt_req_credit_bureau_year")
            ),
            on="hk_application",
            how="left"
        ).join(
            df_sat_app_documents.select(
                col("sat_documents.hk_application"),
                col("sat_documents.document_flags")
            ),
            on="hk_application",
            how="left"
        ).join(
            df_sat_app_building.select(
                col("sat_building.hk_application"),
                col("sat_building.building_social_attrs")
            ),
            on="hk_application",
            how="left"
        )

        # ==================== AGGREGATE POS_CASH ====================
        print("Step 3: Aggregating POS_CASH features...")

        df_pos_cash = spark.read.jdbc(
            url=greenplum_url,
            table="dv_sat_pos_cash_balance",
            properties=db_properties
        ).alias("pos")

        pos_aggregates = df_pos_cash.groupBy("sk_id_curr").agg(
            avg("balance").alias("pos_cash_balance_avg"),
            avg("cnt_instalment").alias("pos_cash_cnt_instalment_avg"),
            avg("cnt_instalment_future").alias("pos_cash_cnt_instalment_future_avg"),
            avg("sk_dpd_def").alias("pos_cash_sk_dpd_def_avg"),
            avg("sk_dpd").alias("pos_cash_sk_dpd_avg"),
            countDistinct("months_balance").alias("pos_cash_nunique_status")
        )

        # ==================== AGGREGATE CREDIT CARD ====================
        print("Step 4: Aggregating credit card features...")

        df_credit_card = spark.read.jdbc(
            url=greenplum_url,
            table="dv_sat_credit_card_balance",
            properties=db_properties
        ).alias("cc")

        cc_aggregates = df_credit_card.groupBy("sk_id_curr").agg(
            avg("balance").alias("credit_card_balance_avg"),
            avg("balance_limit").alias("credit_card_limit_avg"),
            avg("sk_dpd_def").alias("credit_card_sk_dpd_def_avg"),
            avg("sk_dpd").alias("credit_card_sk_dpd_avg"),
            countDistinct("months_balance").alias("credit_card_nunique_status")
        )

        # ==================== AGGREGATE BUREAU ====================
        print("Step 5: Aggregating bureau features...")

        df_bureau = spark.read.jdbc(
            url=greenplum_url,
            table="dv_link_application_bureau",
            properties=db_properties
        ).alias("link")

        df_bureau_sat = spark.read.jdbc(
            url=greenplum_url,
            table="dv_sat_bureau_credit",
            properties=db_properties
        ).alias("bureau_sat")

        # Сначала соединяем link с bureau_sat
        bureau_joined = df_bureau.join(
            df_bureau_sat,
            df_bureau.hk_bureau_credit == df_bureau_sat.hk_bureau_credit,
            how="left"
        )

        bureau_aggregates = bureau_joined.groupBy("link.sk_id_curr").agg(
            avg("bureau_sat.amt_credit_sum").alias("bureau_credit_sum_avg"),
            avg("bureau_sat.amt_credit_sum_debt").alias("bureau_credit_debt_avg"),
            avg("bureau_sat.amt_credit_sum_overdue").alias("bureau_credit_overdue_avg"),
            avg("bureau_sat.days_credit").alias("bureau_days_credit_avg"),
            avg("bureau_sat.days_credit_enddate").alias("bureau_days_credit_enddate_avg"),
            countDistinct("bureau_sat.credit_type").alias("bureau_credit_type_nunique"),
            countDistinct("bureau_sat.status").alias("bureau_status_nunique")
        )

        # ==================== AGGREGATE PREVIOUS APPLICATION ====================
        print("Step 6: Aggregating previous application features...")

        df_prev_link = spark.read.jdbc(
            url=greenplum_url,
            table="dv_link_application_prev_application",
            properties=db_properties
        ).alias("prev_link")

        df_prev_sat = spark.read.jdbc(
            url=greenplum_url,
            table="dv_sat_prev_application",
            properties=db_properties
        ).alias("prev_sat")

        prev_joined = df_prev_link.join(
            df_prev_sat,
            df_prev_link.hk_prev_application == df_prev_sat.hk_prev_application,
            how="left"
        )

        prev_aggregates = prev_joined.groupBy("prev_link.sk_id_curr").agg(
            avg("prev_sat.amt_annuity").alias("prev_app_annuity_avg"),
            avg("prev_sat.amt_application").alias("prev_app_amount_avg"),
            avg("prev_sat.amt_credit").alias("prev_app_credit_avg"),
            avg("prev_sat.amt_down_payment").alias("prev_app_down_payment_avg"),
            avg("prev_sat.amt_goods_price").alias("prev_app_goods_price_avg"),
            countDistinct("prev_sat.name_contract_status").alias("prev_app_decision_nunique"),
            countDistinct("prev_sat.name_payment_type").alias("prev_app_payment_type_nunique"),
            countDistinct("prev_sat.name_product_type").alias("prev_app_product_type_nunique")
        )

        # ==================== MERGE ALL FEATURES ====================
        print("Step 7: Merging all features into final training dataset...")

        # Объединяем все агрегированные признаки
        final_features = base_features

        # Добавляем агрегаты POS_CASH
        final_features = final_features.join(
            pos_aggregates,
            final_features.sk_id_curr == pos_aggregates.sk_id_curr,
            how="left"
        ).select(
            *[final_features[col] for col in final_features.columns],
            *[pos_aggregates[col].alias(f"pos_{col}") if col != "sk_id_curr" else pos_aggregates[col] for col in pos_aggregates.columns if col != "sk_id_curr"]
        )

        # Добавляем агрегаты credit card
        final_features = final_features.join(
            cc_aggregates,
            final_features.sk_id_curr == cc_aggregates.sk_id_curr,
            how="left"
        ).select(
            *[final_features[col] for col in final_features.columns],
            *[cc_aggregates[col].alias(f"cc_{col}") if col != "sk_id_curr" else cc_aggregates[col] for col in cc_aggregates.columns if col != "sk_id_curr"]
        )

        # Добавляем агрегаты bureau
        final_features = final_features.join(
            bureau_aggregates,
            final_features.sk_id_curr == bureau_aggregates.sk_id_curr,
            how="left"
        ).select(
            *[final_features[col] for col in final_features.columns],
            *[bureau_aggregates[col].alias(f"bureau_{col}") if col != "sk_id_curr" else bureau_aggregates[col] for col in bureau_aggregates.columns if col != "sk_id_curr"]
        )

        # Добавляем агрегаты previous application
        final_features = final_features.join(
            prev_aggregates,
            final_features.sk_id_curr == prev_aggregates.sk_id_curr,
            how="left"
        ).select(
            *[final_features[col] for col in final_features.columns],
            *[prev_aggregates[col].alias(f"prev_{col}") if col != "sk_id_curr" else prev_aggregates[col] for col in prev_aggregates.columns if col != "sk_id_curr"]
        )

        print(f"Final dataset has {final_features.count()} records")
        print(f"Final dataset columns: {final_features.columns}")

        # ==================== LOAD ====================
        print("Step 8: Loading data to Greenplum training mart...")

        # Сохраняем в Greenplum
        final_features.write.jdbc(
            url=greenplum_url,
            table="training_mart.homecredit_features",
            mode="overwrite",
            properties=db_properties
        )

        print("ETL process completed successfully!")
        print(f"Training dataset loaded: {final_features.count()} records")

    except Exception as e:
        print(f"Error during ETL process: {e}")
        raise

    finally:
        spark.stop()


if __name__ == "__main__":
    main()

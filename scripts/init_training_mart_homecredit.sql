-- =========================================================
-- TRAINING MART — Home Credit Default Risk
-- Витрина для обучения ML-моделей
-- Источник: Data Vault (dv_*) + агрегированные признаки
-- =========================================================

-- Создание схемы для витрин обучения
CREATE SCHEMA IF NOT EXISTS training_mart;

-- =========================================================
-- ФИНАЛЬНАЯ ВИТРИНА ДЛЯ ОБУЧЕНИЯ
-- =========================================================

CREATE TABLE IF NOT EXISTS training_mart.homecredit_features (
    -- Базовые идентификаторы
    sk_id_curr              BIGINT PRIMARY KEY,
    
    -- Целевая переменная (TARGET)
    target                  SMALLINT,
    
    -- Признаки из application_train (агрегированные)
    name_contract_type      VARCHAR(64),
    code_gender             VARCHAR(8),
    flag_own_car            VARCHAR(8),
    flag_own_realty         VARCHAR(8),
    cnt_children            INTEGER,
    amt_income_total        DOUBLE PRECISION,
    amt_credit              DOUBLE PRECISION,
    amt_annuity             DOUBLE PRECISION,
    amt_goods_price         DOUBLE PRECISION,
    name_type_suite         VARCHAR(128),
    name_income_type        VARCHAR(64),
    name_education_type     VARCHAR(64),
    name_family_status      VARCHAR(64),
    name_housing_type       VARCHAR(64),
    region_population_relative DOUBLE PRECISION,
    days_birth              INTEGER,
    days_employed           DOUBLE PRECISION,
    days_registration       DOUBLE PRECISION,
    days_id_publish         INTEGER,
    own_car_age             DOUBLE PRECISION,
    flag_mobil              INTEGER,
    flag_emp_phone          INTEGER,
    flag_work_phone         INTEGER,
    flag_cont_mobile        INTEGER,
    flag_phone              INTEGER,
    flag_email              INTEGER,
    occupation_type         VARCHAR(128),
    cnt_fam_members         DOUBLE PRECISION,
    region_rating_client    INTEGER,
    region_rating_client_w_city INTEGER,
    weekday_appr_process_start VARCHAR(16),
    hour_appr_process_start DOUBLE PRECISION,
    reg_region_not_live_region INTEGER,
    reg_region_not_work_region INTEGER,
    live_region_not_work_region INTEGER,
    reg_city_not_live_city  INTEGER,
    reg_city_not_work_city  INTEGER,
    live_city_not_work_city INTEGER,
    organization_type       VARCHAR(128),
    ext_source_1            DOUBLE PRECISION,
    ext_source_2            DOUBLE PRECISION,
    ext_source_3            DOUBLE PRECISION,
    days_last_phone_change  DOUBLE PRECISION,
    
    -- Агрегированные признаки из POS_CASH_balance
    pos_cash_balance_avg    DOUBLE PRECISION,
    pos_cash_cnt_instalment_avg DOUBLE PRECISION,
    pos_cash_cnt_instalment_future_avg DOUBLE PRECISION,
    pos_cash_sk_dpd_def_avg DOUBLE PRECISION,
    pos_cash_sk_dpd_avg     DOUBLE PRECISION,
    pos_cash_nunique_status INTEGER,
    
    -- Агрегированные признаки из credit_card_balance
    credit_card_balance_avg DOUBLE PRECISION,
    credit_card_limit_avg   DOUBLE PRECISION,
    credit_card_sk_dpd_def_avg DOUBLE PRECISION,
    credit_card_sk_dpd_avg  DOUBLE PRECISION,
    credit_card_nunique_status INTEGER,
    
    -- Агрегированные признаки из bureau
    bureau_credit_sum_avg   DOUBLE PRECISION,
    bureau_credit_debt_avg  DOUBLE PRECISION,
    bureau_credit_overdue_avg DOUBLE PRECISION,
    bureau_days_credit_avg  INTEGER,
    bureau_days_credit_enddate_avg DOUBLE PRECISION,
    bureau_credit_type_nunique INTEGER,
    bureau_status_nunique   INTEGER,
    
    -- Агрегированные признаки из previous_application
    prev_app_annuity_avg    DOUBLE PRECISION,
    prev_app_amount_avg     DOUBLE PRECISION,
    prev_app_credit_avg     DOUBLE PRECISION,
    prev_app_down_payment_avg DOUBLE PRECISION,
    prev_app_goods_price_avg DOUBLE PRECISION,
    prev_app_decision_nunique INTEGER,
    prev_app_payment_type_nunique INTEGER,
    prev_app_product_type_nunique INTEGER,
    
    -- Агрегированные признаки из документов и соц. окружения
    flag_document_2         INTEGER,
    flag_document_3         INTEGER,
    flag_document_4         INTEGER,
    flag_document_5         INTEGER,
    apartments_avg          DOUBLE PRECISION,
    basementarea_avg        DOUBLE PRECISION,
    livingarea_avg          DOUBLE PRECISION,
    obs_30_cnt_social_circle DOUBLE PRECISION,
    def_30_cnt_social_circle DOUBLE PRECISION,
    obs_60_cnt_social_circle DOUBLE PRECISION,
    def_60_cnt_social_circle DOUBLE PRECISION,
    amt_req_credit_bureau_hour DOUBLE PRECISION,
    amt_req_credit_bureau_day DOUBLE PRECISION,
    amt_req_credit_bureau_week DOUBLE PRECISION,
    amt_req_credit_bureau_mon DOUBLE PRECISION,
    amt_req_credit_bureau_qrt DOUBLE PRECISION,
    amt_req_credit_bureau_year DOUBLE PRECISION,
    
    -- Метаданные
    record_source           TEXT NOT NULL DEFAULT 'training_mart:homecredit',
    load_dts                TIMESTAMP NOT NULL DEFAULT now(),
    update_dts              TIMESTAMP NOT NULL DEFAULT now()
);

-- Индексы для ускорения обучения
CREATE INDEX IF NOT EXISTS idx_training_mart_target 
    ON training_mart.homecredit_features(target);

CREATE INDEX IF NOT EXISTS idx_training_mart_sk_id_curr 
    ON training_mart.homecredit_features(sk_id_curr);

CREATE INDEX IF NOT EXISTS idx_training_mart_load_dts 
    ON training_mart.homecredit_features(load_dts);

-- Комментарии для документации
COMMENT ON TABLE training_mart.homecredit_features IS 'Финальная витрина для обучения ML-моделей предсказания дефолта';
COMMENT ON COLUMN training_mart.homecredit_features.sk_id_curr IS 'Идентификатор заявки/клиента';
COMMENT ON COLUMN training_mart.homecredit_features.target IS 'Целевая переменная: 0 - погашен, 1 - дефолт';
COMMENT ON COLUMN training_mart.homecredit_features.pos_cash_nunique_status IS 'Количество уникальных статусов контракта в POS_CASH';
COMMENT ON COLUMN training_mart.homecredit_features.credit_card_nunique_status IS 'Количество уникальных статусов контракта в credit_card_balance';
COMMENT ON COLUMN training_mart.homecredit_features.bureau_credit_type_nunique IS 'Количество уникальных типов кредитов в bureau';
COMMENT ON COLUMN training_mart.homecredit_features.prev_app_decision_nunique IS 'Количество уникальных решений по заявке';

-- =========================================================
-- DATA VAULT 2.0 — Home Credit Default Risk (Kaggle)
-- Источник: https://www.kaggle.com/competitions/home-credit-default-risk/data
--
-- Файлы датасета:
--   application_train.csv / application_test.csv  → Hub Application (SK_ID_CURR)
--   bureau.csv                                      → Hub Bureau + Link → Application
--   bureau_balance.csv                              → Sat (месячные остатки по SK_ID_BUREAU)
--   previous_application.csv                        → Hub Prev Application + Link → Application
--   installments_payments.csv                     → Sat (платежи по SK_ID_PREV)
--   credit_card_balance.csv                         → Sat (месячные снимки по SK_ID_PREV)
--   POS_CASH_balance.csv                            → Sat (месячные снимки по SK_ID_PREV)
--   HomeCredit_columns_description.csv              → справочник (вне DV)
--
-- Hash-ключи (hk_*) заполняются на ETL; здесь — только DDL.
-- =========================================================

-- ---------- HUBS ----------

-- Текущая заявка / кредит (одна строка = один кредит в выборке)
CREATE TABLE IF NOT EXISTS dv_hub_application (
    hk_application   TEXT PRIMARY KEY,
    sk_id_curr       INTEGER NOT NULL,
    record_source    TEXT NOT NULL DEFAULT 'kaggle:application',
    load_dts         TIMESTAMP NOT NULL DEFAULT now()
);

-- Кредит в БКИ (внешняя история клиента)
CREATE TABLE IF NOT EXISTS dv_hub_bureau_credit (
    hk_bureau_credit TEXT PRIMARY KEY,
    sk_id_bureau     INTEGER NOT NULL,
    record_source    TEXT NOT NULL DEFAULT 'kaggle:bureau',
    load_dts         TIMESTAMP NOT NULL DEFAULT now()
);

-- Предыдущая заявка в Home Credit
CREATE TABLE IF NOT EXISTS dv_hub_prev_application (
    hk_prev_application TEXT PRIMARY KEY,
    sk_id_prev          INTEGER NOT NULL,
    record_source       TEXT NOT NULL DEFAULT 'kaggle:previous_application',
    load_dts            TIMESTAMP NOT NULL DEFAULT now()
);

-- ---------- LINKS ----------

CREATE TABLE IF NOT EXISTS dv_link_application_bureau (
    hk_link_application_bureau TEXT PRIMARY KEY,
    hk_application             TEXT NOT NULL REFERENCES dv_hub_application(hk_application),
    hk_bureau_credit           TEXT NOT NULL REFERENCES dv_hub_bureau_credit(hk_bureau_credit),
    record_source              TEXT NOT NULL DEFAULT 'kaggle:bureau',
    load_dts                   TIMESTAMP NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS dv_link_application_prev_application (
    hk_link_application_prev_application TEXT PRIMARY KEY,
    hk_application                       TEXT NOT NULL REFERENCES dv_hub_application(hk_application),
    hk_prev_application                  TEXT NOT NULL REFERENCES dv_hub_prev_application(hk_prev_application),
    record_source                        TEXT NOT NULL DEFAULT 'kaggle:previous_application',
    load_dts                             TIMESTAMP NOT NULL DEFAULT now()
);

-- ---------- SATELLITES: application_train / application_test ----------

CREATE TABLE IF NOT EXISTS dv_sat_app_contract (
    hk_application      TEXT NOT NULL REFERENCES dv_hub_application(hk_application),
    hashdiff            TEXT NOT NULL,
    name_contract_type  VARCHAR(50),
    amt_credit          NUMERIC(18,2),
    amt_annuity         NUMERIC(18,2),
    amt_goods_price     NUMERIC(18,2),
    amt_income_total    NUMERIC(18,2),
    record_source       TEXT NOT NULL DEFAULT 'kaggle:application',
    load_dts            TIMESTAMP NOT NULL DEFAULT now(),
    effective_from      TIMESTAMP NOT NULL DEFAULT now(),
    PRIMARY KEY (hk_application, load_dts)
);

CREATE TABLE IF NOT EXISTS dv_sat_app_client_profile (
    hk_application       TEXT NOT NULL REFERENCES dv_hub_application(hk_application),
    hashdiff             TEXT NOT NULL,
    code_gender          VARCHAR(10),
    cnt_children         INTEGER,
    cnt_fam_members      NUMERIC(8,2),
    name_type_suite      VARCHAR(100),
    name_income_type     VARCHAR(100),
    name_education_type  VARCHAR(100),
    name_family_status   VARCHAR(100),
    name_housing_type    VARCHAR(100),
    days_birth           INTEGER,
    days_employed        NUMERIC(12,2),
    days_registration    NUMERIC(12,2),
    days_id_publish      INTEGER,
    occupation_type      VARCHAR(100),
    organization_type    VARCHAR(100),
    own_car_age          NUMERIC(8,2),
    flag_own_car         VARCHAR(5),
    flag_own_realty      VARCHAR(5),
    record_source        TEXT NOT NULL DEFAULT 'kaggle:application',
    load_dts             TIMESTAMP NOT NULL DEFAULT now(),
    effective_from       TIMESTAMP NOT NULL DEFAULT now(),
    PRIMARY KEY (hk_application, load_dts)
);

CREATE TABLE IF NOT EXISTS dv_sat_app_process (
    hk_application              TEXT NOT NULL REFERENCES dv_hub_application(hk_application),
    hashdiff                    TEXT NOT NULL,
    weekday_appr_process_start  VARCHAR(20),
    hour_appr_process_start     NUMERIC(8,2),
    region_population_relative  NUMERIC(12,6),
    region_rating_client        INTEGER,
    region_rating_client_w_city INTEGER,
    reg_region_not_live_region  INTEGER,
    reg_region_not_work_region  INTEGER,
    live_region_not_work_region INTEGER,
    reg_city_not_live_city      INTEGER,
    reg_city_not_work_city      INTEGER,
    live_city_not_work_city     INTEGER,
    record_source               TEXT NOT NULL DEFAULT 'kaggle:application',
    load_dts                    TIMESTAMP NOT NULL DEFAULT now(),
    effective_from              TIMESTAMP NOT NULL DEFAULT now(),
    PRIMARY KEY (hk_application, load_dts)
);

CREATE TABLE IF NOT EXISTS dv_sat_app_contact_flags (
    hk_application        TEXT NOT NULL REFERENCES dv_hub_application(hk_application),
    hashdiff              TEXT NOT NULL,
    flag_mobil            INTEGER,
    flag_emp_phone        INTEGER,
    flag_work_phone       INTEGER,
    flag_cont_mobile      INTEGER,
    flag_phone            INTEGER,
    flag_email            INTEGER,
    days_last_phone_change INTEGER,
    record_source         TEXT NOT NULL DEFAULT 'kaggle:application',
    load_dts              TIMESTAMP NOT NULL DEFAULT now(),
    effective_from        TIMESTAMP NOT NULL DEFAULT now(),
    PRIMARY KEY (hk_application, load_dts)
);

CREATE TABLE IF NOT EXISTS dv_sat_app_external_scores (
    hk_application  TEXT NOT NULL REFERENCES dv_hub_application(hk_application),
    hashdiff        TEXT NOT NULL,
    ext_source_1    NUMERIC(12,6),
    ext_source_2    NUMERIC(12,6),
    ext_source_3    NUMERIC(12,6),
    record_source   TEXT NOT NULL DEFAULT 'kaggle:application',
    load_dts        TIMESTAMP NOT NULL DEFAULT now(),
    effective_from  TIMESTAMP NOT NULL DEFAULT now(),
    PRIMARY KEY (hk_application, load_dts)
);

CREATE TABLE IF NOT EXISTS dv_sat_app_credit_bureau_enquiries (
    hk_application              TEXT NOT NULL REFERENCES dv_hub_application(hk_application),
    hashdiff                    TEXT NOT NULL,
    amt_req_credit_bureau_hour  NUMERIC(8,2),
    amt_req_credit_bureau_day   NUMERIC(8,2),
    amt_req_credit_bureau_week  NUMERIC(8,2),
    amt_req_credit_bureau_mon   NUMERIC(8,2),
    amt_req_credit_bureau_qrt   NUMERIC(8,2),
    amt_req_credit_bureau_year  NUMERIC(8,2),
    record_source               TEXT NOT NULL DEFAULT 'kaggle:application',
    load_dts                    TIMESTAMP NOT NULL DEFAULT now(),
    effective_from              TIMESTAMP NOT NULL DEFAULT now(),
    PRIMARY KEY (hk_application, load_dts)
);

-- Документы (FLAG_DOCUMENT_2 … FLAG_DOCUMENT_21) и прочие редко меняющиеся признаки
CREATE TABLE IF NOT EXISTS dv_sat_app_documents (
    hk_application   TEXT NOT NULL REFERENCES dv_hub_application(hk_application),
    hashdiff         TEXT NOT NULL,
    document_flags   JSONB NOT NULL DEFAULT '{}',
    record_source    TEXT NOT NULL DEFAULT 'kaggle:application',
    load_dts         TIMESTAMP NOT NULL DEFAULT now(),
    effective_from   TIMESTAMP NOT NULL DEFAULT now(),
    PRIMARY KEY (hk_application, load_dts)
);

-- Нормализованные признаки жилья / соц. окружения (APARTMENTS_AVG, YEARS_* и т.д.)
CREATE TABLE IF NOT EXISTS dv_sat_app_building_social (
    hk_application       TEXT NOT NULL REFERENCES dv_hub_application(hk_application),
    hashdiff             TEXT NOT NULL,
    building_social_attrs JSONB NOT NULL DEFAULT '{}',
    record_source        TEXT NOT NULL DEFAULT 'kaggle:application',
    load_dts             TIMESTAMP NOT NULL DEFAULT now(),
    effective_from       TIMESTAMP NOT NULL DEFAULT now(),
    PRIMARY KEY (hk_application, load_dts)
);

-- TARGET: только application_train (0 — погашен, 1 — дефолт)
CREATE TABLE IF NOT EXISTS dv_sat_app_target (
    hk_application  TEXT NOT NULL REFERENCES dv_hub_application(hk_application),
    hashdiff        TEXT NOT NULL,
    target          SMALLINT,
    record_source   TEXT NOT NULL DEFAULT 'kaggle:application_train',
    load_dts        TIMESTAMP NOT NULL DEFAULT now(),
    effective_from  TIMESTAMP NOT NULL DEFAULT now(),
    PRIMARY KEY (hk_application, load_dts)
);

-- ---------- SATELLITES: bureau.csv ----------

CREATE TABLE IF NOT EXISTS dv_sat_bureau_credit (
    hk_bureau_credit         TEXT NOT NULL REFERENCES dv_hub_bureau_credit(hk_bureau_credit),
    hashdiff                 TEXT NOT NULL,
    credit_active            VARCHAR(20),
    credit_currency          VARCHAR(20),
    days_credit              INTEGER,
    credit_day_overdue       INTEGER,
    days_credit_enddate      NUMERIC(12,2),
    days_enddate_fact        NUMERIC(12,2),
    amt_credit_max_overdue   NUMERIC(18,2),
    cnt_credit_prolong       INTEGER,
    amt_credit_sum           NUMERIC(18,2),
    amt_credit_sum_debt      NUMERIC(18,2),
    amt_credit_sum_limit     NUMERIC(18,2),
    amt_credit_sum_overdue   NUMERIC(18,2),
    credit_type              VARCHAR(50),
    days_credit_update       INTEGER,
    amt_annuity              NUMERIC(18,2),
    record_source            TEXT NOT NULL DEFAULT 'kaggle:bureau',
    load_dts                 TIMESTAMP NOT NULL DEFAULT now(),
    effective_from           TIMESTAMP NOT NULL DEFAULT now(),
    PRIMARY KEY (hk_bureau_credit, load_dts)
);

-- ---------- SATELLITES: bureau_balance.csv (multi-active по месяцу) ----------

CREATE TABLE IF NOT EXISTS dv_sat_bureau_balance (
    hk_bureau_credit  TEXT NOT NULL REFERENCES dv_hub_bureau_credit(hk_bureau_credit),
    months_balance    INTEGER NOT NULL,
    hashdiff          TEXT NOT NULL,
    status            VARCHAR(10),
    record_source     TEXT NOT NULL DEFAULT 'kaggle:bureau_balance',
    load_dts          TIMESTAMP NOT NULL DEFAULT now(),
    effective_from    TIMESTAMP NOT NULL DEFAULT now(),
    PRIMARY KEY (hk_bureau_credit, months_balance, load_dts)
);

-- ---------- SATELLITES: previous_application.csv ----------

CREATE TABLE IF NOT EXISTS dv_sat_prev_application (
    hk_prev_application        TEXT NOT NULL REFERENCES dv_hub_prev_application(hk_prev_application),
    hashdiff                   TEXT NOT NULL,
    name_contract_type         VARCHAR(50),
    amt_annuity                NUMERIC(18,2),
    amt_application            NUMERIC(18,2),
    amt_credit                 NUMERIC(18,2),
    amt_down_payment           NUMERIC(18,2),
    amt_goods_price            NUMERIC(18,2),
    name_contract_status       VARCHAR(50),
    days_decision              INTEGER,
    name_payment_type          VARCHAR(50),
    code_reject_reason         VARCHAR(50),
    name_client_type           VARCHAR(50),
    name_portfolio             VARCHAR(50),
    name_product_type          VARCHAR(50),
    channel_type               VARCHAR(50),
    cnt_payment                NUMERIC(12,2),
    name_yield_group           VARCHAR(50),
    prev_application_attrs     JSONB NOT NULL DEFAULT '{}',
    record_source              TEXT NOT NULL DEFAULT 'kaggle:previous_application',
    load_dts                   TIMESTAMP NOT NULL DEFAULT now(),
    effective_from             TIMESTAMP NOT NULL DEFAULT now(),
    PRIMARY KEY (hk_prev_application, load_dts)
);

-- ---------- SATELLITES: installments_payments.csv ----------

CREATE TABLE IF NOT EXISTS dv_sat_installment_payment (
    hk_prev_application     TEXT NOT NULL REFERENCES dv_hub_prev_application(hk_prev_application),
    num_instalment_version  INTEGER NOT NULL,
    num_instalment_number   INTEGER NOT NULL,
    hashdiff                TEXT NOT NULL,
    days_instalment         INTEGER,
    days_entry_payment      NUMERIC(12,2),
    amt_instalment          NUMERIC(18,2),
    amt_payment             NUMERIC(18,2),
    record_source           TEXT NOT NULL DEFAULT 'kaggle:installments_payments',
    load_dts                TIMESTAMP NOT NULL DEFAULT now(),
    effective_from          TIMESTAMP NOT NULL DEFAULT now(),
    PRIMARY KEY (hk_prev_application, num_instalment_version, num_instalment_number, load_dts)
);

-- ---------- SATELLITES: credit_card_balance.csv (multi-active по месяцу) ----------

CREATE TABLE IF NOT EXISTS dv_sat_credit_card_balance (
    hk_prev_application  TEXT NOT NULL REFERENCES dv_hub_prev_application(hk_prev_application),
    months_balance       INTEGER NOT NULL,
    hashdiff             TEXT NOT NULL,
    balance              NUMERIC(18,2),
    balance_limit        NUMERIC(18,2),
    sk_dpd_def           INTEGER,
    sk_dpd               INTEGER,
    card_balance_attrs   JSONB NOT NULL DEFAULT '{}',
    record_source        TEXT NOT NULL DEFAULT 'kaggle:credit_card_balance',
    load_dts             TIMESTAMP NOT NULL DEFAULT now(),
    effective_from       TIMESTAMP NOT NULL DEFAULT now(),
    PRIMARY KEY (hk_prev_application, months_balance, load_dts)
);

-- ---------- SATELLITES: POS_CASH_balance.csv (multi-active по месяцу) ----------

CREATE TABLE IF NOT EXISTS dv_sat_pos_cash_balance (
    hk_prev_application   TEXT NOT NULL REFERENCES dv_hub_prev_application(hk_prev_application),
    months_balance        INTEGER NOT NULL,
    hashdiff              TEXT NOT NULL,
    cnt_instalment        NUMERIC(12,2),
    cnt_instalment_future NUMERIC(12,2),
    name_contract_status  VARCHAR(50),
    sk_dpd_def            INTEGER,
    sk_dpd                INTEGER,
    pos_cash_attrs        JSONB NOT NULL DEFAULT '{}',
    record_source         TEXT NOT NULL DEFAULT 'kaggle:POS_CASH_balance',
    load_dts              TIMESTAMP NOT NULL DEFAULT now(),
    effective_from        TIMESTAMP NOT NULL DEFAULT now(),
    PRIMARY KEY (hk_prev_application, months_balance, load_dts)
);

-- ---------- SATELLITES: прототип (скоринг / объяснения ML-агента) ----------

CREATE TABLE IF NOT EXISTS dv_sat_scoring_result (
    hk_application       TEXT NOT NULL REFERENCES dv_hub_application(hk_application),
    hashdiff             TEXT NOT NULL,
    default_probability  NUMERIC(8,6),
    model_version        VARCHAR(64),
    confidence           NUMERIC(8,6),
    scoring_payload      JSONB,
    record_source        TEXT NOT NULL DEFAULT 'mlservice',
    load_dts             TIMESTAMP NOT NULL DEFAULT now(),
    effective_from       TIMESTAMP NOT NULL DEFAULT now(),
    PRIMARY KEY (hk_application, load_dts)
);

CREATE TABLE IF NOT EXISTS dv_sat_agent_explanation (
    hk_application       TEXT NOT NULL REFERENCES dv_hub_application(hk_application),
    hashdiff             TEXT NOT NULL,
    mode                 VARCHAR(20) NOT NULL,
    explanation_payload  JSONB NOT NULL,
    record_source        TEXT NOT NULL DEFAULT 'agentservice',
    load_dts             TIMESTAMP NOT NULL DEFAULT now(),
    effective_from       TIMESTAMP NOT NULL DEFAULT now(),
    PRIMARY KEY (hk_application, load_dts)
);

-- ---------- INDEXES (бизнес-ключи для поиска при загрузке) ----------

CREATE INDEX IF NOT EXISTS idx_dv_hub_application_sk_id_curr
    ON dv_hub_application(sk_id_curr);

CREATE INDEX IF NOT EXISTS idx_dv_hub_bureau_credit_sk_id_bureau
    ON dv_hub_bureau_credit(sk_id_bureau);

CREATE INDEX IF NOT EXISTS idx_dv_hub_prev_application_sk_id_prev
    ON dv_hub_prev_application(sk_id_prev);

CREATE INDEX IF NOT EXISTS idx_dv_link_application_bureau_hk_application
    ON dv_link_application_bureau(hk_application);

CREATE INDEX IF NOT EXISTS idx_dv_link_application_prev_hk_application
    ON dv_link_application_prev_application(hk_application);

CREATE INDEX IF NOT EXISTS idx_dv_sat_app_target_load_dts
    ON dv_sat_app_target(load_dts);

CREATE INDEX IF NOT EXISTS idx_dv_sat_bureau_balance_months
    ON dv_sat_bureau_balance(hk_bureau_credit, months_balance);

CREATE INDEX IF NOT EXISTS idx_dv_sat_credit_card_balance_months
    ON dv_sat_credit_card_balance(hk_prev_application, months_balance);

CREATE INDEX IF NOT EXISTS idx_dv_sat_pos_cash_balance_months
    ON dv_sat_pos_cash_balance(hk_prev_application, months_balance);

CREATE TABLE IF NOT EXISTS clients (
    client_id SERIAL PRIMARY KEY,
    education VARCHAR(100),
    sex VARCHAR(10),
    age INTEGER,
    car BOOLEAN,
    car_type BOOLEAN,
    income NUMERIC(12,2),
    foreign_passport BOOLEAN
);

CREATE TABLE IF NOT EXISTS applications (
    application_id SERIAL PRIMARY KEY,
    client_id INTEGER NOT NULL REFERENCES clients(client_id),
    app_date DATE NOT NULL
);

CREATE TABLE IF NOT EXISTS financial_profiles (
    fp_id SERIAL PRIMARY KEY,
    client_id INTEGER NOT NULL REFERENCES clients(client_id),
    decline_app_cnt INTEGER,
    good_work BOOLEAN,
    bki_request_cnt INTEGER,
    region_rating NUMERIC(5,2)
);

CREATE TABLE IF NOT EXISTS behavioral_contexts (
    bc_id SERIAL PRIMARY KEY,
    client_id INTEGER NOT NULL REFERENCES clients(client_id),
    home_address VARCHAR(100),
    work_address VARCHAR(100),
    sna VARCHAR(100),
    first_time BOOLEAN
);

CREATE TABLE IF NOT EXISTS scoring_info (
    scoring_id SERIAL PRIMARY KEY,
    application_id INTEGER NOT NULL REFERENCES applications(application_id),
    score_bki NUMERIC(8,2),
    default_probability NUMERIC(5,4),
    model_version VARCHAR(20),
    generated_at TIMESTAMP DEFAULT now()
);

CREATE TABLE IF NOT EXISTS default_status (
    default_id SERIAL PRIMARY KEY,
    application_id INTEGER NOT NULL REFERENCES applications(application_id),
    default_flag BOOLEAN
);

CREATE TABLE IF NOT EXISTS agent_explanations (
    explanation_id SERIAL PRIMARY KEY,
    application_id INTEGER NOT NULL REFERENCES applications(application_id),
    mode VARCHAR(20) NOT NULL DEFAULT 'brief',
    explanation_payload JSONB NOT NULL,
    generated_at TIMESTAMP DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_clients_income ON clients(income);
CREATE INDEX IF NOT EXISTS idx_applications_date ON applications(app_date);
CREATE INDEX IF NOT EXISTS idx_scoring_generated_at ON scoring_info(generated_at);
CREATE INDEX IF NOT EXISTS idx_scoring_app_id ON scoring_info(application_id);

-- =========================================================
-- DATA VAULT 2.0 (НОВАЯ КОНЦЕПЦИЯ DWH ДЛЯ ПРОТОТИПА)
-- ВАЖНО: старые таблицы выше оставлены без изменений для обратной совместимости.
-- Ниже добавлены новые Hub / Link / Satellite сущности c префиксом dv_.
-- =========================================================

-- ---------- HUBS ----------
CREATE TABLE IF NOT EXISTS dv_hub_client (
    hk_client TEXT PRIMARY KEY,
    client_id INTEGER NOT NULL,
    record_source TEXT NOT NULL DEFAULT 'webapp',
    load_dts TIMESTAMP NOT NULL DEFAULT now(),
    CONSTRAINT uq_dv_hub_client_bk UNIQUE (client_id)
);

CREATE TABLE IF NOT EXISTS dv_hub_application (
    hk_application TEXT PRIMARY KEY,
    application_id INTEGER NOT NULL,
    record_source TEXT NOT NULL DEFAULT 'webapp',
    load_dts TIMESTAMP NOT NULL DEFAULT now(),
    CONSTRAINT uq_dv_hub_application_bk UNIQUE (application_id)
);

-- ---------- LINKS ----------
CREATE TABLE IF NOT EXISTS dv_link_client_application (
    hk_link_client_application TEXT PRIMARY KEY,
    hk_client TEXT NOT NULL REFERENCES dv_hub_client(hk_client),
    hk_application TEXT NOT NULL REFERENCES dv_hub_application(hk_application),
    record_source TEXT NOT NULL DEFAULT 'webapp',
    load_dts TIMESTAMP NOT NULL DEFAULT now(),
    CONSTRAINT uq_dv_link_client_application UNIQUE (hk_client, hk_application)
);

-- ---------- SATELLITES ----------
CREATE TABLE IF NOT EXISTS dv_sat_client_profile (
    hk_client TEXT NOT NULL REFERENCES dv_hub_client(hk_client),
    hashdiff TEXT NOT NULL,
    education VARCHAR(100),
    sex VARCHAR(10),
    age INTEGER,
    car BOOLEAN,
    car_type BOOLEAN,
    income NUMERIC(12,2),
    foreign_passport BOOLEAN,
    record_source TEXT NOT NULL DEFAULT 'webapp',
    load_dts TIMESTAMP NOT NULL DEFAULT now(),
    effective_from TIMESTAMP NOT NULL DEFAULT now(),
    PRIMARY KEY (hk_client, load_dts)
);

CREATE TABLE IF NOT EXISTS dv_sat_financial_profile (
    hk_client TEXT NOT NULL REFERENCES dv_hub_client(hk_client),
    hashdiff TEXT NOT NULL,
    decline_app_cnt INTEGER,
    good_work BOOLEAN,
    bki_request_cnt INTEGER,
    region_rating NUMERIC(5,2),
    record_source TEXT NOT NULL DEFAULT 'webapp',
    load_dts TIMESTAMP NOT NULL DEFAULT now(),
    effective_from TIMESTAMP NOT NULL DEFAULT now(),
    PRIMARY KEY (hk_client, load_dts)
);

CREATE TABLE IF NOT EXISTS dv_sat_behavioral_context (
    hk_client TEXT NOT NULL REFERENCES dv_hub_client(hk_client),
    hashdiff TEXT NOT NULL,
    home_address VARCHAR(100),
    work_address VARCHAR(100),
    sna VARCHAR(100),
    first_time BOOLEAN,
    record_source TEXT NOT NULL DEFAULT 'webapp',
    load_dts TIMESTAMP NOT NULL DEFAULT now(),
    effective_from TIMESTAMP NOT NULL DEFAULT now(),
    PRIMARY KEY (hk_client, load_dts)
);

CREATE TABLE IF NOT EXISTS dv_sat_application_details (
    hk_application TEXT NOT NULL REFERENCES dv_hub_application(hk_application),
    hashdiff TEXT NOT NULL,
    app_date DATE NOT NULL,
    features JSONB,
    record_source TEXT NOT NULL DEFAULT 'webapp',
    load_dts TIMESTAMP NOT NULL DEFAULT now(),
    effective_from TIMESTAMP NOT NULL DEFAULT now(),
    PRIMARY KEY (hk_application, load_dts)
);

CREATE TABLE IF NOT EXISTS dv_sat_scoring_result (
    hk_application TEXT NOT NULL REFERENCES dv_hub_application(hk_application),
    hashdiff TEXT NOT NULL,
    score_bki NUMERIC(8,2),
    default_probability NUMERIC(5,4),
    model_version VARCHAR(32),
    confidence NUMERIC(5,4),
    record_source TEXT NOT NULL DEFAULT 'mlservice',
    load_dts TIMESTAMP NOT NULL DEFAULT now(),
    effective_from TIMESTAMP NOT NULL DEFAULT now(),
    PRIMARY KEY (hk_application, load_dts)
);

CREATE TABLE IF NOT EXISTS dv_sat_agent_explanation (
    hk_application TEXT NOT NULL REFERENCES dv_hub_application(hk_application),
    hashdiff TEXT NOT NULL,
    mode VARCHAR(20) NOT NULL,
    explanation_payload JSONB NOT NULL,
    record_source TEXT NOT NULL DEFAULT 'agentservice',
    load_dts TIMESTAMP NOT NULL DEFAULT now(),
    effective_from TIMESTAMP NOT NULL DEFAULT now(),
    PRIMARY KEY (hk_application, load_dts)
);

CREATE TABLE IF NOT EXISTS dv_sat_default_status (
    hk_application TEXT NOT NULL REFERENCES dv_hub_application(hk_application),
    hashdiff TEXT NOT NULL,
    default_flag BOOLEAN,
    record_source TEXT NOT NULL DEFAULT 'dwh',
    load_dts TIMESTAMP NOT NULL DEFAULT now(),
    effective_from TIMESTAMP NOT NULL DEFAULT now(),
    PRIMARY KEY (hk_application, load_dts)
);

-- ---------- INDEXES ----------
CREATE INDEX IF NOT EXISTS idx_dv_hub_client_bk ON dv_hub_client(client_id);
CREATE INDEX IF NOT EXISTS idx_dv_hub_application_bk ON dv_hub_application(application_id);
CREATE INDEX IF NOT EXISTS idx_dv_sat_client_profile_load_dts ON dv_sat_client_profile(load_dts);
CREATE INDEX IF NOT EXISTS idx_dv_sat_scoring_result_load_dts ON dv_sat_scoring_result(load_dts);
CREATE INDEX IF NOT EXISTS idx_dv_sat_agent_explanation_load_dts ON dv_sat_agent_explanation(load_dts);

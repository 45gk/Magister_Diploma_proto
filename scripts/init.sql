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

# ETL и ML-сервис для предсказания дефолта

## Что было реализовано

### 1. ETL-процесс для подготовки данных

#### Файлы:
- `scripts/init_training_mart_homecredit.sql` - SQL для создания витрины обучения
- `airflow/dags/etl_homecredit_training.py` - Airflow DAG для ETL из Data Vault
- `airflow/dags/scripts/spark_etl_homecredit.py` - Spark-скрипт для обработки данных
- `airflow/dags/etl_homecredit_from_files.py` - Airflow DAG для ETL из файлов HomeCredit

#### Что делает:
1. Загружает данные из Data Vault (Greenplum) ИЛИ из CSV файлов HomeCredit
2. Агрегирует признаки из POS_CASH, credit_card_balance, bureau, previous_application
3. Создает финальную витрину `training_mart.homecredit_features` для обучения

### 2. ML-сервис

#### Файлы:
- `mlservice/train_model.py` - модуль обучения модели
- `mlservice/model_manager.py` - модуль для управления моделью и предсказаний
- `mlservice/app.py` - FastAPI приложение с REST API
- `mlservice/requirements.txt` - зависимости
- `mlservice/Dockerfile` - Docker образ

#### API endpoints:

**Проверка здоровья:**
```
GET /ml/health
```

**Статус модели:**
```
GET /ml/model/status
```

**Обучение модели:**
```
POST /ml/train
Body: {
  "n_iterations": 1000,
  "dataset_path": "optional_path"
}
```

**Предсказание для одной записи:**
```
POST /ml/predict
Body: {
  "application_id": 123,
  "features": {
    "amt_income_total": 50000,
    "amt_credit": 200000,
    ...
  }
}
```

**Батч предсказания:**
```
POST /ml/predict/batch
Body: {
  "features_list": [
    {"amt_income_total": 50000, ...},
    {"amt_income_total": 60000, ...}
  ]
}
```

## Как использовать

### 1. Инициализация базы данных (опционально)

Если используете Data Vault:
```bash
docker-compose up -d gpdb
# Подождите пока Greenplum запустится
# Затем выполните SQL скрипт для создания витрины
psql -h localhost -p 5434 -U bank_user -d bank_dwh -f scripts/init_training_mart_homecredit.sql
```

### 2. Запуск ETL из файлов HomeCredit (базовый вариант)

Запустите DAG в Airflow UI (`http://localhost:8081`):
- Найдите DAG `etl_homecredit_from_files`
- Нажмите "Trigger DAG"

Этот DAG читает данные напрямую из файлов `homecredit_data/`:
- application_train.csv
- application_test.csv
- bureau.csv
- bureau_balance.csv
- credit_card_balance.csv
- POS_CASH_balance.csv
- previous_application.csv

### 3. Запуск ETL из Data Vault (продвинутый вариант)

Если данные загружены в Greenplum:
- Найдите DAG `etl_homecredit_training`
- Нажмите "Trigger DAG"

### 4. Запуск ML-сервиса

```bash
# Соберите Docker образ
docker-compose build mlservice

# Запустите сервис
docker-compose up -d mlservice
```

### 5. Обучение модели

Отправьте запрос на обучение:
```bash
curl -X POST http://localhost:8001/ml/train \
  -H "Content-Type: application/json" \
  -d '{"n_iterations": 1000}'
```

### 6. Получение предсказаний

```bash
curl -X POST http://localhost:8001/ml/predict \
  -H "Content-Type: application/json" \
  -d '{
    "application_id": 123,
    "features": {
      "amt_income_total": 50000,
      "amt_credit": 200000,
      "amt_annuity": 5000,
      "cnt_children": 1,
      "code_gender": "F",
      "flag_own_car": "N",
      "flag_own_realty": "Y",
      "days_birth": -15000,
      "days_employed": -5000,
      "ext_source_1": 0.5,
      "ext_source_2": 0.6,
      "ext_source_3": 0.4,
      "region_rating_client": 2,
      "organization_type": "Business Entity"
    }
  }'
```

## Архитектура

```
┌─────────────────────────────────────────────────────────────┐
│                    Greenplum DB                             │
│  ┌───────────────────────────────────────────────────────┐  │
│  │  Data Vault (dv_*)                                     │  │
│  │  - dv_hub_application                                  │  │
│  │  - dv_hub_bureau_credit                                │  │
│  │  - dv_hub_prev_application                             │  │
│  │  - dv_sat_* (сателлиты)                                │  │
│  └───────────────────────────────────────────────────────┘  │
│                            │                                │
│                            ▼                                │
│  ┌───────────────────────────────────────────────────────┐  │
│  │  training_mart.homecredit_features (витрина)          │  │
│  └───────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                      Airflow DAGs                           │
│  etl_homecredit_training.py                                 │
│  - Extract data from DV                                     │
│  - Transform & aggregate features                           │
│  - Load to training_mart                                    │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                   HomeCredit Files                          │
│  homecredit_data/                                           │
│  - application_train.csv                                    │
│  - application_test.csv                                     │
│  - bureau.csv                                               │
│  - bureau_balance.csv                                       │
│  - credit_card_balance.csv                                  │
│  - POS_CASH_balance.csv                                     │
│  - previous_application.csv                                 │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                      Airflow DAGs                           │
│  etl_homecredit_from_files.py                               │
│  - Read CSV files                                           │
│  - Transform & aggregate features                           │
│  - Save to /opt/airflow/dags/data/                          │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                     MLService                               │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  train_model.py    (обучение CatBoost)              │   │
│  │  - load_training_data()                             │   │
│  │  - preprocess_data()                                │   │
│  │  - train_model()                                    │   │
│  │  - save_model()                                     │   │
│  └─────────────────────────────────────────────────────┘   │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  model_manager.py  (предсказания)                   │   │
│  │  - load_model()                                     │   │
│  │  - predict_single()                                 │   │
│  │  - predict_batch()                                  │   │
│  └─────────────────────────────────────────────────────┘   │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  app.py            (REST API)                       │   │
│  │  - /ml/train                                        │   │
│  │  - /ml/predict                                      │   │
│  │  - /ml/predict/batch                                │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

## Модель

Используется **CatBoostClassifier** с параметрами из оригинального ноутбука:
- iterations: 1000
- learning_rate: 0.1
- depth: 7
- l2_leaf_reg: 40
- eval_metric: AUC

## Метрики

После обучения модель сохраняется в:
- `/app/models/catboost_default_risk.pkl`
- `/app/models/label_encoder.pkl`
- `/app/models/feature_columns.json`
- `/app/models/model_status.json`

## ETL из файлов HomeCredit

### DAG: `etl_homecredit_from_files`

Этот DAG читает данные напрямую из CSV файлов в папке `homecredit_data/`:

**Таски:**
1. `extract_homecredit_data` - чтение CSV файлов (первые 100к строк для прототипа)
2. `validate_homecredit_data` - проверка наличия файлов
3. `transform_homecredit_data` - агрегация признаков как в original notebook
4. `create_training_summary` - создание отчета
5. `notify_complete` - уведомление

**Выходные файлы:**
- `homecredit_train_features.csv` - признаки для обучения
- `homecredit_test_features.csv` - признаки для тестирования
- `homecredit_train_target.csv` - целевая переменная
- `homecredit_test_ids.csv` - ID тестовых записей

## Примечания

1. ETL можно запускать по расписанию через Airflow UI
2. ML-сервис поддерживает fallback на heuristic scoring если модель не загружена
3. Модель автоматически загружается при старте сервиса
4. Батч предсказания доступны через `/ml/predict/batch`
5. Для работы с полными данными измените параметр `nrows` в коде

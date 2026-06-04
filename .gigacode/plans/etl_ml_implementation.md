# План реализации ETL и ML-сервиса

## Анализ example.ipynb

В ноутбуке реализовано:
1. Загрузка данных из CSV файлов Home Credit (application_train, application_test, POS_CASH, credit_card, bureau, previous_application)
2. Предобработка данных (LabelEncoder для категориальных признаков, группировка по SK_ID_CURR)
3. Обучение модели CatBoostClassifier
4. Предсказания и сохранение submission.csv

---

## Задачи для реализации

### 1. ETL-процесс для подготовки данных (Airflow + Spark)

#### 1.1. Создать ETL DAG для подготовки данных
- **Файл**: `airflow/dags/etl_homecredit_training.py`
- **Задачи**:
  - Extract: Загрузка данных из CSV/Greenplum
  - Transform: Предобработка данных (как в ноутбуке)
  - Load: Сохранение в training dataset в Greenplum (витрина для обучения)

#### 1.2. Создать Spark-скрипты для обработки
- **Файлы**: 
  - `airflow/dags/scripts/spark_etl_homecredit.py` - основной ETL скрипт
  - `airflow/dags/scripts/spark_aggregate_features.py` - агрегация признаков

#### 1.3. Создать SQL-скрипт для витрины обучения
- **Файл**: `scripts/init_training_mart_homecredit.sql`
- **Таблица**: `training_mart.homecredit_features` - финальная витрина для обучения

---

### 2. ML-сервис (mlservice)

#### 2.1. Обновить requirements.txt
- Добавить: `catboost`, `scikit-learn`, `pandas`, `joblib`

#### 2.2. Создать модуль обучения
- **Файл**: `mlservice/train_model.py`
- **Функции**:
  - `load_training_data()` - загрузка из Greenplum/CSV
  - `preprocess_data()` - предобработка (как в ноутбуке)
  - `train_model()` - обучение CatBoost
  - `save_model()` - сохранение модели (joblib)

#### 2.3. Обновить mlservice/app.py
- Добавить endpoints:
  - `GET /ml/train` - запуск обучения
  - `GET /ml/model/status` - статус модели
  - `POST /ml/predict` - предсказания на новых данных
  - `GET /ml/predict/batch` - батч предсказания
- Обновить существующий heuristic_score на использование обученной модели

#### 2.4. Создать модуль для работы с моделью
- **Файл**: `mlservice/model_manager.py`
- **Функции**:
  - `load_model()` - загрузка модели
  - `predict()` - предсказания
  - `validate_features()` - валидация входных данных

---

## Архитектура

```
┌─────────────────────────────────────────────────────────────┐
│                      Airflow DAGs                           │
│  etl_homecredit_training.py                                 │
│  - Extract (CSV/Greenplum)                                  │
│  - Transform (Spark/Python)                                 │
│  - Load (Greenplum training_mart)                           │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                    Greenplum DB                             │
│  training_mart.homecredit_features (витрина для обучения)   │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                     MLService                               │
│  - train_model.py   (обучение)                             │
│  - model_manager.py (загрузка/предсказания)                │
│  - app.py (API endpoints)                                   │
└─────────────────────────────────────────────────────────────┘
```

---

## Порядок реализации

1. **Создать SQL для витрины обучения** (`scripts/init_training_mart_homecredit.sql`)
2. **Создать ETL DAG** (`airflow/dags/etl_homecredit_training.py`)
3. **Создать Spark-скрипты** (`airflow/dags/scripts/spark_etl_homecredit.py`)
4. **Обновить requirements.txt** для mlservice
5. **Создать train_model.py** в mlservice
6. **Создать model_manager.py** в mlservice
7. **Обновить app.py** с новыми endpoints
8. **Протестировать** полный цикл

---

## Примечания

- Используем Greenplum как источник и хранилище для витрины
- CatBoost остается основной моделью (как в ноутбуке)
- MLService предоставляет REST API для предсказаний
- ETL можно запускать по расписанию или вручную через Airflow UI

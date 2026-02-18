# Прототип информационно-советующей системы управления банковскими кредитами

Монорепозиторий реализует прототип из ТЗ главы 4:
- `webapp/` — Django + DRF API для заявок, скоринга и рекомендаций;
- `mlservice/` — FastAPI сервис инференса (`/ml/score`);
- `agentservice/` — FastAPI сервис объяснений (`/agent/explain`);
- `airflow/dags/` — ETL DAG (extract/validate/clean/transform/load/checks);
- `scripts/init.sql` — DWH DDL для PostgreSQL.

## Быстрый старт

```bash
cp .env.example .env
docker-compose up --build
```

Сервисы:
- Web API: http://localhost:8000
- MLService: http://localhost:8001/docs
- AgentService: http://localhost:8002/docs
- Airflow: http://localhost:8080

## API сценарий

### 1) Создание заявки

```bash
curl -X POST http://localhost:8000/applications/ \
  -H 'Content-Type: application/json' \
  -d '{
    "client": {
      "education":"higher",
      "sex":"F",
      "age":34,
      "car":true,
      "car_type":true,
      "income":50000,
      "foreign_passport":true
    },
    "financial_profile": {
      "decline_app_cnt":1,
      "good_work":true,
      "bki_request_cnt":2,
      "region_rating":0.85
    },
    "behavioral_context": {
      "home_address":"X",
      "work_address":"Y",
      "sna":"connected",
      "first_time":false
    },
    "application": {"app_date":"2026-02-18"},
    "features": {"income":50000,"age":34,"debt_to_income":0.45,"bki_request_cnt":2}
  }'
```

### 2) Инициация скоринга

```bash
curl -X POST http://localhost:8000/applications/1/score
```

### 3) Инициация объяснения агента

```bash
curl -X POST http://localhost:8000/applications/1/recommend \
  -H 'Content-Type: application/json' \
  -d '{"mode":"detailed"}'
```

## AgentService режимы

- `brief`: краткое описание (2-4 предложения);
- `detailed`: подробное объяснение по факторам;
- `policy`: объяснение с регуляторным акцентом.

## Проверка качества

Базовые тесты для web API:

```bash
cd webapp
python manage.py test
```

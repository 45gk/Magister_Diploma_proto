# Прототип информационно-советующей системы управления банковскими кредитами

Монорепозиторий реализует прототип из ТЗ главы 4:
- `webapp/` — Django + DRF API + веб-интерфейс для заявок, скоринга и рекомендаций;
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
- **Веб-интерфейс**: http://localhost:8000 (главная страница с навигацией)
- Web API: http://localhost:8000/api/ (DRF endpoints)
- MLService: http://localhost:8001/docs
- AgentService: http://localhost:8002/docs
- Airflow: http://localhost:8081 (admin/admin)
- Greenplum (Data Vault): порт 5434 для подключения к Greenplum Database
- Spark Master: http://localhost:4040 (Spark UI), порт 7077 для подключения
- PostgreSQL: порт 5433

## Работа с Spark через Airflow

Airflow интегрирован с Spark кластером. В DAG'ах можно использовать SparkSubmitOperator для запуска Spark-приложений на кластере.

Пример подключения к базам данных из Spark:
- PostgreSQL: `jdbc:postgresql://db:5432/bank_dwh`
- Greenplum: `jdbc:postgresql://gpdb:5432/bank_dwh`

### Доступные DAG'и:
- `etl_santander` — базовый ETL на Python
- `spark_data_processing` — обработка данных через Spark с подключением к PostgreSQL и Greenplum

**Spark URL для DAG'ов**: `spark://spark-master:7077`

Система предоставляет удобный веб-интерфейс для работы с кредитными заявками:

### Главная страница
- Статистика системы (количество заявок, клиентов, оцененных заявок)
- Быстрые ссылки на основные функции
- Список последних заявок

### Основные разделы
- **Главная** (`/`) — дашборд с обзором системы
- **Мои заявки** (`/applications/`) — список всех кредитных заявок
- **Новая заявка** (`/applications/new/`) — форма создания заявки
- **Статус системы** (`/health/`) — проверка работоспособности всех сервисов

### Работа с заявками
1. **Создание заявки**: Заполните форму с данными клиента, финансового профиля и поведенческого контекста
2. **Просмотр деталей**: Посмотрите полную информацию о заявке, результаты скоринга и объяснения агента
3. **Скоринг**: Запустите оценку вероятности дефолта с помощью ML-модели
4. **Рекомендации**: Получите объяснение решения от AI-агента

### Особенности интерфейса
- Адаптивный дизайн с современным UI
- Валидация форм на стороне клиента
- Сообщения об успехе/ошибках операций
- Интерактивные элементы (кнопки скоринга, рекомендации)
- Цветовая индикация статуса заявок

## Подключение к Greenplum через DBeaver

1. Запустите `docker compose up -d --build`.
2. Откройте DBeaver и создайте новое подключение.
3. Выберите драйвер PostgreSQL (Greenplum совместим с PostgreSQL-клиентом).
4. В настройках подключения укажите:
   - Host: `localhost`
   - Port: `5434`
   - Database: `bank_dwh`
   - Username: `bank_user`
   - Password: `bank_pass`
5. Нажмите `Test Connection`.
6. Если соединение успешно, сохраните подключение и откройте SQL-редактор.

> Примечание: Greenplum в этом прототипе доступен как отдельный сервис `gpdb`. Данные Data Vault инициализируются из `scripts/init_data_vault.sql`.

## API сценарий

> **Примечание**: Для удобства работы также доступен веб-интерфейс по адресу http://localhost:8000

### 1) Создание заявки

**Через веб-интерфейс:**
- Перейдите на http://localhost:8000/applications/new/
- Заполните форму и нажмите "Создать заявку"

**Через API:**

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

**Через веб-интерфейс:**
- Откройте детали заявки: http://localhost:8000/applications/{id}/
- Нажмите кнопку "🎯 Провести скоринг"

**Через API:**

```bash
curl -X POST http://localhost:8000/applications/1/score
```

### 3) Инициация объяснения агента

**Через веб-интерфейс:**
- После скоринга нажмите кнопку "💡 Получить рекомендацию агента"

**Через API:**

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

### Ручное тестирование

1. **Веб-интерфейс**: Откройте http://localhost:8000 и протестируйте все функции
2. **API endpoints**: Используйте curl или Postman для тестирования REST API
3. **Статус системы**: Проверьте http://localhost:8000/health/ для мониторинга сервисов

### Структура проекта

```
webapp/
├── apps/credit/
│   ├── templates/credit/     # HTML шаблоны веб-интерфейса
│   ├── views.py             # Views для API и веб-интерфейса
│   ├── urls.py              # Маршруты (API + веб)
│   ├── models.py            # Модели данных
│   └── serializers.py       # DRF сериализаторы
├── credit_system/
│   ├── settings.py          # Настройки Django
│   └── urls.py              # Главные маршруты
└── manage.py
```


docker exec magister_diploma_proto-airflow-webserver-1 bash -c "pip install --no-cache-dir 'apache-airflow-providers-apache-spark==4.11.3'"
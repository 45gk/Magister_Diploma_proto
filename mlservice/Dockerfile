FROM python:3.11-slim

WORKDIR /app

# Установка зависимостей
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копирование приложения
COPY app.py .
COPY train_model.py .
COPY model_manager.py .

# Создание директории для модели
RUN mkdir -p /app/models

# Экспорт порта
EXPOSE 8001

# Запуск приложения
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8001"]

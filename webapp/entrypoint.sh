#!/bin/bash
set -e

echo "Waiting for PostgreSQL..."
until python - <<'PY'
import os
import sys
import psycopg2

conn = psycopg2.connect(
    host=os.environ.get("POSTGRES_HOST", "db"),
    port=int(os.environ.get("POSTGRES_PORT", "5432")),
    dbname=os.environ.get("POSTGRES_DB", "bank_dwh"),
    user=os.environ.get("POSTGRES_USER", "bank_user"),
    password=os.environ.get("POSTGRES_PASSWORD", "bank_pass"),
)
conn.close()
PY
do
  echo "PostgreSQL is unavailable - sleeping"
  sleep 2
done
echo "PostgreSQL is up."

python manage.py makemigrations credit --noinput
python manage.py migrate --noinput

exec python manage.py runserver 0.0.0.0:8000

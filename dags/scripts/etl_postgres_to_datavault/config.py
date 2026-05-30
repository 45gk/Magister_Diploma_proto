"""Параметры подключения (Docker-сеть: db / gpdb)."""

from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class DbConfig:
    host: str
    port: int
    dbname: str
    user: str
    password: str


def pg_config() -> DbConfig:
    return DbConfig(
        host=os.getenv('ETL_PG_HOST', 'db'),
        port=int(os.getenv('ETL_PG_PORT', '5432')),
        dbname=os.getenv('ETL_PG_DB', os.getenv('POSTGRES_DB', 'bank_dwh')),
        user=os.getenv('ETL_PG_USER', os.getenv('POSTGRES_USER', 'bank_user')),
        password=os.getenv('ETL_PG_PASSWORD', os.getenv('POSTGRES_PASSWORD', 'bank_pass')),
    )


def gp_config() -> DbConfig:
    return DbConfig(
        host=os.getenv('ETL_GP_HOST', 'gpdb'),
        port=int(os.getenv('ETL_GP_PORT', '5432')),
        dbname=os.getenv('ETL_GP_DB', os.getenv('POSTGRES_DB', 'bank_dwh')),
        user=os.getenv('ETL_GP_USER', os.getenv('POSTGRES_USER', 'bank_user')),
        password=os.getenv('ETL_GP_PASSWORD', os.getenv('POSTGRES_PASSWORD', 'bank_pass')),
    )


RECORD_SOURCE_APP = 'etl:postgres:application_train'
RECORD_SOURCE_BUREAU = 'etl:postgres:bureau'
RECORD_SOURCE_BUREAU_BAL = 'etl:postgres:bureau_balance'

# Мусорные поля (как в apps.credit.models.ETL_JUNK_FIELDS)
JUNK_FIELDS = {
    'src_application_train': ('legacy_amt_income_text', 'internal_sync_token'),
    'src_bureau': ('old_sys_bureau_ref',),
    'src_bureau_balance': ('raw_status_dump',),
}

BATCH_SIZE = int(os.getenv('ETL_BATCH_SIZE', '2000'))
ROW_LIMIT = os.getenv('ETL_ROW_LIMIT')  # None = все строки

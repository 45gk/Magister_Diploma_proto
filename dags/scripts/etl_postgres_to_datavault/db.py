"""Подключения к PostgreSQL и Greenplum."""

from __future__ import annotations

from contextlib import contextmanager
from typing import Any, Generator, Iterable, Sequence

import psycopg2
from psycopg2.extras import RealDictCursor, execute_batch

from .config import DbConfig, BATCH_SIZE


def connect(cfg: DbConfig):
    return psycopg2.connect(
        host=cfg.host,
        port=cfg.port,
        dbname=cfg.dbname,
        user=cfg.user,
        password=cfg.password,
    )


@contextmanager
def pg_cursor(cfg: DbConfig) -> Generator:
    conn = connect(cfg)
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            yield conn, cur
            conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


@contextmanager
def gp_cursor(cfg: DbConfig) -> Generator:
    conn = connect(cfg)
    try:
        with conn.cursor() as cur:
            yield conn, cur
            conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def normalize_row(row: dict[str, Any]) -> dict[str, Any]:
    """Привести ключи к snake_case (SK_ID_CURR → sk_id_curr)."""
    return {str(k).lower(): v for k, v in row.items()}


def fetch_table(
    cfg: DbConfig,
    table: str,
    *,
    limit: int | None = None,
    order_by: str | None = None,
) -> list[dict[str, Any]]:
    sql = f'SELECT * FROM {table}'
    if order_by:
        sql += f' ORDER BY {order_by}'
    if limit is not None:
        sql += f' LIMIT {int(limit)}'
    with pg_cursor(cfg) as (_, cur):
        cur.execute(sql)
        return [normalize_row(dict(r)) for r in cur.fetchall()]


def insert_batch(
    cfg: DbConfig,
    table: str,
    columns: Sequence[str],
    rows: Iterable[Sequence[Any]],
    *,
    on_conflict: str | None = None,
    page_size: int = BATCH_SIZE,
) -> int:
    data = list(rows)
    if not data:
        return 0
    cols = ', '.join(columns)
    placeholders = ', '.join(['%s'] * len(columns))
    sql = f'INSERT INTO {table} ({cols}) VALUES ({placeholders})'
    if on_conflict:
        sql += f' ON CONFLICT {on_conflict} DO NOTHING'
    with gp_cursor(cfg) as (_, cur):
        execute_batch(cur, sql, data, page_size=page_size)
    return len(data)


def count_table(cfg: DbConfig, table: str) -> int:
    with gp_cursor(cfg) as (_, cur):
        cur.execute(f'SELECT COUNT(*) FROM {table}')
        return int(cur.fetchone()[0])

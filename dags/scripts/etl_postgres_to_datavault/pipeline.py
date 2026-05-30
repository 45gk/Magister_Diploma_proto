"""Оркестрация ETL: extract → transform → load."""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

_SCRIPTS_DIR = Path(__file__).resolve().parents[1]
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

from etl_postgres_to_datavault.config import (
    BATCH_SIZE,
    RECORD_SOURCE_APP,
    RECORD_SOURCE_BUREAU,
    RECORD_SOURCE_BUREAU_BAL,
    ROW_LIMIT,
    gp_config,
    pg_config,
)
from etl_postgres_to_datavault.db import count_table, fetch_table, gp_cursor, insert_batch, pg_cursor
from etl_postgres_to_datavault.transform import (
    application_train_to_dv,
    bureau_balance_to_dv,
    bureau_to_dv,
)

_HUB_APP_COLS = ('hk_application', 'sk_id_curr', 'record_source', 'load_dts')
_SAT_CONTRACT_COLS = (
    'hk_application', 'hashdiff', 'name_contract_type', 'amt_credit', 'amt_annuity',
    'amt_goods_price', 'amt_income_total', 'record_source', 'load_dts', 'effective_from',
)
_SAT_PROFILE_COLS = (
    'hk_application', 'hashdiff', 'code_gender', 'cnt_children', 'cnt_fam_members',
    'name_type_suite', 'name_income_type', 'name_education_type', 'name_family_status',
    'name_housing_type', 'days_birth', 'days_employed', 'days_registration', 'days_id_publish',
    'occupation_type', 'organization_type', 'own_car_age', 'flag_own_car', 'flag_own_realty',
    'record_source', 'load_dts', 'effective_from',
)
_SAT_PROCESS_COLS = (
    'hk_application', 'hashdiff', 'weekday_appr_process_start', 'hour_appr_process_start',
    'region_population_relative', 'region_rating_client', 'region_rating_client_w_city',
    'reg_region_not_live_region', 'reg_region_not_work_region', 'live_region_not_work_region',
    'reg_city_not_live_city', 'reg_city_not_work_city', 'live_city_not_work_city',
    'record_source', 'load_dts', 'effective_from',
)
_SAT_CONTACT_COLS = (
    'hk_application', 'hashdiff', 'flag_mobil', 'flag_emp_phone', 'flag_work_phone',
    'flag_cont_mobile', 'flag_phone', 'flag_email', 'days_last_phone_change',
    'record_source', 'load_dts', 'effective_from',
)
_SAT_EXT_COLS = (
    'hk_application', 'hashdiff', 'ext_source_1', 'ext_source_2', 'ext_source_3',
    'record_source', 'load_dts', 'effective_from',
)
_SAT_ENQ_COLS = (
    'hk_application', 'hashdiff',
    'amt_req_credit_bureau_hour', 'amt_req_credit_bureau_day', 'amt_req_credit_bureau_week',
    'amt_req_credit_bureau_mon', 'amt_req_credit_bureau_qrt', 'amt_req_credit_bureau_year',
    'record_source', 'load_dts', 'effective_from',
)
_SAT_DOCS_COLS = (
    'hk_application', 'hashdiff', 'document_flags', 'record_source', 'load_dts', 'effective_from',
)
_SAT_BUILD_COLS = (
    'hk_application', 'hashdiff', 'building_social_attrs', 'record_source', 'load_dts', 'effective_from',
)
_SAT_TARGET_COLS = (
    'hk_application', 'hashdiff', 'target', 'record_source', 'load_dts', 'effective_from',
)
_HUB_BUREAU_COLS = ('hk_bureau_credit', 'sk_id_bureau', 'record_source', 'load_dts')
_LINK_APP_BUREAU_COLS = (
    'hk_link_application_bureau', 'hk_application', 'hk_bureau_credit', 'record_source', 'load_dts',
)
_SAT_BUREAU_COLS = (
    'hk_bureau_credit', 'hashdiff', 'credit_active', 'credit_currency', 'days_credit',
    'credit_day_overdue', 'days_credit_enddate', 'days_enddate_fact', 'amt_credit_max_overdue',
    'cnt_credit_prolong', 'amt_credit_sum', 'amt_credit_sum_debt', 'amt_credit_sum_limit',
    'amt_credit_sum_overdue', 'credit_type', 'days_credit_update', 'amt_annuity',
    'record_source', 'load_dts', 'effective_from',
)
_SAT_BUREAU_BAL_COLS = (
    'hk_bureau_credit', 'months_balance', 'hashdiff', 'status',
    'record_source', 'load_dts', 'effective_from',
)

_TABLE_LOAD_MAP = {
    'dv_hub_application': (_HUB_APP_COLS, '(hk_application)'),
    'dv_sat_app_contract': (_SAT_CONTRACT_COLS, None),
    'dv_sat_app_client_profile': (_SAT_PROFILE_COLS, None),
    'dv_sat_app_process': (_SAT_PROCESS_COLS, None),
    'dv_sat_app_contact_flags': (_SAT_CONTACT_COLS, None),
    'dv_sat_app_external_scores': (_SAT_EXT_COLS, None),
    'dv_sat_app_credit_bureau_enquiries': (_SAT_ENQ_COLS, None),
    'dv_sat_app_documents': (_SAT_DOCS_COLS, None),
    'dv_sat_app_building_social': (_SAT_BUILD_COLS, None),
    'dv_sat_app_target': (_SAT_TARGET_COLS, None),
    'dv_hub_bureau_credit': (_HUB_BUREAU_COLS, '(hk_bureau_credit)'),
    'dv_link_application_bureau': (_LINK_APP_BUREAU_COLS, '(hk_link_application_bureau)'),
    'dv_sat_bureau_credit': (_SAT_BUREAU_COLS, None),
    'dv_sat_bureau_balance': (_SAT_BUREAU_BAL_COLS, None),
}


def _row_limit() -> int | None:
    if not ROW_LIMIT:
        return None
    return int(ROW_LIMIT)


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _as_jsonb(val: Any) -> str:
    if isinstance(val, str):
        return val
    return json.dumps(val, default=str)


def _load_dv_tables(payload: dict[str, list[tuple]]) -> dict[str, int]:
    gp = gp_config()
    stats: dict[str, int] = {}
    for table, rows in payload.items():
        if not rows:
            stats[table] = 0
            continue
        cols, on_conflict = _TABLE_LOAD_MAP[table]
        adapted = []
        for row in rows:
            r = list(row)
            if table in ('dv_sat_app_documents', 'dv_sat_app_building_social') and len(r) > 2:
                r[2] = _as_jsonb(r[2])
            adapted.append(tuple(r))
        stats[table] = insert_batch(
            gp, table, cols, adapted, on_conflict=on_conflict, page_size=BATCH_SIZE,
        )
    return stats


def test_connections(**context) -> dict[str, Any]:
    """Проверка доступности PostgreSQL (staging) и Greenplum (DV)."""
    pg = pg_config()
    gp = gp_config()
    with pg_cursor(pg) as (_, cur):
        cur.execute('SELECT 1')
    with gp_cursor(gp) as (_, cur):
        cur.execute('SELECT 1')
    summary = {'postgres': 'ok', 'greenplum': 'ok'}
    if context.get('ti'):
        context['ti'].xcom_push(key='connection_check', value=summary)
    return summary


def load_application_train_to_dv(**context) -> dict[str, Any]:
    rows = fetch_table(
        pg_config(),
        'src_application_train',
        limit=_row_limit(),
        order_by='sk_id_curr',
    )
    if not rows:
        raise ValueError('src_application_train пуста — загрузите CSV в PostgreSQL')

    load_dts = _now()
    payload = application_train_to_dv(
        rows, load_dts=load_dts, record_source=RECORD_SOURCE_APP,
    )
    stats = _load_dv_tables(payload)
    summary = {'source_rows': len(rows), 'loaded': stats}
    if context.get('ti'):
        context['ti'].xcom_push(key='load_application_train', value=summary)
    return summary


def load_bureau_to_dv(**context) -> dict[str, Any]:
    rows = fetch_table(pg_config(), 'src_bureau', limit=_row_limit(), order_by='sk_id_bureau')
    if not rows:
        summary = {'source_rows': 0, 'loaded': {}, 'skipped': True}
        if context.get('ti'):
            context['ti'].xcom_push(key='load_bureau', value=summary)
        return summary

    payload = bureau_to_dv(rows, load_dts=_now(), record_source=RECORD_SOURCE_BUREAU)
    stats = _load_dv_tables(payload)
    summary = {'source_rows': len(rows), 'loaded': stats}
    if context.get('ti'):
        context['ti'].xcom_push(key='load_bureau', value=summary)
    return summary


def load_bureau_balance_to_dv(**context) -> dict[str, Any]:
    rows = fetch_table(
        pg_config(), 'src_bureau_balance', limit=_row_limit(), order_by='sk_id_bureau',
    )
    if not rows:
        summary = {'source_rows': 0, 'loaded': {}, 'skipped': True}
        if context.get('ti'):
            context['ti'].xcom_push(key='load_bureau_balance', value=summary)
        return summary

    payload = bureau_balance_to_dv(
        rows, load_dts=_now(), record_source=RECORD_SOURCE_BUREAU_BAL,
    )
    stats = _load_dv_tables(payload)
    summary = {'source_rows': len(rows), 'loaded': stats}
    if context.get('ti'):
        context['ti'].xcom_push(key='load_bureau_balance', value=summary)
    return summary


def run_post_load_checks(**context) -> dict[str, Any]:
    gp = gp_config()
    checks = {
        'dv_hub_application': count_table(gp, 'dv_hub_application'),
        'dv_hub_bureau_credit': count_table(gp, 'dv_hub_bureau_credit'),
        'dv_sat_app_target': count_table(gp, 'dv_sat_app_target'),
    }
    if checks['dv_hub_application'] < 1:
        raise ValueError('В Data Vault нет заявок (dv_hub_application пуст)')
    if context.get('ti'):
        context['ti'].xcom_push(key='post_load_checks', value=checks)
    return checks

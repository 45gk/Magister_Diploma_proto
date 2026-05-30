"""Очистка staging-строк и маппинг в структуры Data Vault."""

from __future__ import annotations

import json
from datetime import datetime
from typing import Any

from .config import JUNK_FIELDS
from .hashing import (
    hashdiff,
    hashdiff_json,
    hk_application,
    hk_bureau_credit,
    hk_link_application_bureau,
)


def strip_junk(row: dict[str, Any], table: str) -> dict[str, Any]:
    junk = set(JUNK_FIELDS.get(table, ()))
    return {k: v for k, v in row.items() if k not in junk}


def _doc_flags(row: dict[str, Any]) -> dict[str, Any]:
    return {k: row[k] for k in row if k.startswith('flag_document_') and row.get(k) is not None}


def _building_social(row: dict[str, Any]) -> dict[str, Any]:
    keys = (
        'apartments_avg', 'basementarea_avg', 'years_beginexpluatation_avg', 'years_build_avg',
        'commonarea_avg', 'elevators_avg', 'entrances_avg', 'floorsmax_avg', 'floorsmin_avg',
        'landarea_avg', 'livingapartments_avg', 'livingarea_avg', 'nonlivingapartments_avg',
        'nonlivingarea_avg', 'apartments_mode', 'basementarea_mode', 'years_beginexpluatation_mode',
        'years_build_mode', 'commonarea_mode', 'elevators_mode', 'entrances_mode', 'floorsmax_mode',
        'floorsmin_mode', 'landarea_mode', 'livingapartments_mode', 'livingarea_mode',
        'nonlivingapartments_mode', 'nonlivingarea_mode', 'apartments_medi', 'basementarea_medi',
        'years_beginexpluatation_medi', 'years_build_medi', 'commonarea_medi', 'elevators_medi',
        'entrances_medi', 'floorsmax_medi', 'floorsmin_medi', 'landarea_medi', 'livingapartments_medi',
        'livingarea_medi', 'nonlivingapartments_medi', 'nonlivingarea_medi', 'fondkapremont_mode',
        'housetype_mode', 'totalarea_mode', 'wallsmaterial_mode', 'emergencystate_mode',
        'obs_30_cnt_social_circle', 'def_30_cnt_social_circle', 'obs_60_cnt_social_circle',
        'def_60_cnt_social_circle',
    )
    return {k: row[k] for k in keys if k in row and row[k] is not None}


def application_train_to_dv(
    rows: list[dict[str, Any]],
    *,
    load_dts: datetime,
    record_source: str,
) -> dict[str, list[tuple]]:
    hubs: list[tuple] = []
    sat_contract: list[tuple] = []
    sat_profile: list[tuple] = []
    sat_process: list[tuple] = []
    sat_contact: list[tuple] = []
    sat_ext: list[tuple] = []
    sat_enquiries: list[tuple] = []
    sat_documents: list[tuple] = []
    sat_building: list[tuple] = []
    sat_target: list[tuple] = []

    for raw in rows:
        row = strip_junk(raw, 'src_application_train')
        sk = row.get('sk_id_curr')
        if sk is None:
            continue
        hk = hk_application(sk)

        hubs.append((hk, sk, record_source, load_dts))

        sat_contract.append((
            hk,
            hashdiff(row.get('name_contract_type'), row.get('amt_credit'), row.get('amt_annuity'),
                     row.get('amt_goods_price'), row.get('amt_income_total')),
            row.get('name_contract_type'), row.get('amt_credit'), row.get('amt_annuity'),
            row.get('amt_goods_price'), row.get('amt_income_total'),
            record_source, load_dts, load_dts,
        ))

        sat_profile.append((
            hk,
            hashdiff(row.get('code_gender'), row.get('cnt_children'), row.get('days_birth')),
            row.get('code_gender'), row.get('cnt_children'), row.get('cnt_fam_members'),
            row.get('name_type_suite'), row.get('name_income_type'), row.get('name_education_type'),
            row.get('name_family_status'), row.get('name_housing_type'),
            row.get('days_birth'), row.get('days_employed'), row.get('days_registration'),
            row.get('days_id_publish'), row.get('occupation_type'), row.get('organization_type'),
            row.get('own_car_age'), row.get('flag_own_car'), row.get('flag_own_realty'),
            record_source, load_dts, load_dts,
        ))

        sat_process.append((
            hk,
            hashdiff(row.get('region_rating_client'), row.get('hour_appr_process_start')),
            row.get('weekday_appr_process_start'), row.get('hour_appr_process_start'),
            row.get('region_population_relative'), row.get('region_rating_client'),
            row.get('region_rating_client_w_city'),
            row.get('reg_region_not_live_region'), row.get('reg_region_not_work_region'),
            row.get('live_region_not_work_region'), row.get('reg_city_not_live_city'),
            row.get('reg_city_not_work_city'), row.get('live_city_not_work_city'),
            record_source, load_dts, load_dts,
        ))

        sat_contact.append((
            hk,
            hashdiff(row.get('flag_mobil'), row.get('flag_email')),
            row.get('flag_mobil'), row.get('flag_emp_phone'), row.get('flag_work_phone'),
            row.get('flag_cont_mobile'), row.get('flag_phone'), row.get('flag_email'),
            row.get('days_last_phone_change'),
            record_source, load_dts, load_dts,
        ))

        sat_ext.append((
            hk,
            hashdiff(row.get('ext_source_1'), row.get('ext_source_2'), row.get('ext_source_3')),
            row.get('ext_source_1'), row.get('ext_source_2'), row.get('ext_source_3'),
            record_source, load_dts, load_dts,
        ))

        sat_enquiries.append((
            hk,
            hashdiff(row.get('amt_req_credit_bureau_hour'), row.get('amt_req_credit_bureau_year')),
            row.get('amt_req_credit_bureau_hour'), row.get('amt_req_credit_bureau_day'),
            row.get('amt_req_credit_bureau_week'), row.get('amt_req_credit_bureau_mon'),
            row.get('amt_req_credit_bureau_qrt'), row.get('amt_req_credit_bureau_year'),
            record_source, load_dts, load_dts,
        ))

        docs = _doc_flags(row)
        sat_documents.append((
            hk, hashdiff_json(docs), json_dumps(docs), record_source, load_dts, load_dts,
        ))

        building = _building_social(row)
        sat_building.append((
            hk, hashdiff_json(building), json_dumps(building), record_source, load_dts, load_dts,
        ))

        if row.get('target') is not None:
            sat_target.append((
                hk, hashdiff(row.get('target')), row.get('target'),
                record_source, load_dts, load_dts,
            ))

    return {
        'dv_hub_application': hubs,
        'dv_sat_app_contract': sat_contract,
        'dv_sat_app_client_profile': sat_profile,
        'dv_sat_app_process': sat_process,
        'dv_sat_app_contact_flags': sat_contact,
        'dv_sat_app_external_scores': sat_ext,
        'dv_sat_app_credit_bureau_enquiries': sat_enquiries,
        'dv_sat_app_documents': sat_documents,
        'dv_sat_app_building_social': sat_building,
        'dv_sat_app_target': sat_target,
    }


def json_dumps(data: dict) -> str:
    return json.dumps(data, default=str)


def bureau_to_dv(
    rows: list[dict[str, Any]],
    *,
    load_dts: datetime,
    record_source: str,
) -> dict[str, list[tuple]]:
    hubs: list[tuple] = []
    links: list[tuple] = []
    sats: list[tuple] = []

    for raw in rows:
        row = strip_junk(raw, 'src_bureau')
        sk_bureau = row.get('sk_id_bureau')
        sk_curr = row.get('sk_id_curr')
        if sk_bureau is None or sk_curr is None:
            continue
        hk_b = hk_bureau_credit(sk_bureau)
        hk_a = hk_application(sk_curr)

        hubs.append((hk_b, sk_bureau, record_source, load_dts))
        links.append((
            hk_link_application_bureau(sk_curr, sk_bureau),
            hk_a, hk_b, record_source, load_dts,
        ))
        sats.append((
            hk_b,
            hashdiff(row.get('credit_active'), row.get('amt_credit_sum')),
            row.get('credit_active'), row.get('credit_currency'), row.get('days_credit'),
            row.get('credit_day_overdue'), row.get('days_credit_enddate'), row.get('days_enddate_fact'),
            row.get('amt_credit_max_overdue'), row.get('cnt_credit_prolong'), row.get('amt_credit_sum'),
            row.get('amt_credit_sum_debt'), row.get('amt_credit_sum_limit'), row.get('amt_credit_sum_overdue'),
            row.get('credit_type'), row.get('days_credit_update'), row.get('amt_annuity'),
            record_source, load_dts, load_dts,
        ))

    return {
        'dv_hub_bureau_credit': hubs,
        'dv_link_application_bureau': links,
        'dv_sat_bureau_credit': sats,
    }


def bureau_balance_to_dv(
    rows: list[dict[str, Any]],
    *,
    load_dts: datetime,
    record_source: str,
) -> dict[str, list[tuple]]:
    sats: list[tuple] = []
    for raw in rows:
        row = strip_junk(raw, 'src_bureau_balance')
        sk_bureau = row.get('sk_id_bureau')
        months = row.get('months_balance')
        if sk_bureau is None or months is None:
            continue
        hk_b = hk_bureau_credit(sk_bureau)
        sats.append((
            hk_b, months,
            hashdiff(months, row.get('status')),
            row.get('status'),
            record_source, load_dts, load_dts,
        ))
    return {'dv_sat_bureau_balance': sats}

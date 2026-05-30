"""Hash-ключи и hashdiff для Data Vault 2.0."""

from __future__ import annotations

import hashlib
import json
from typing import Any


def _md5(text: str) -> str:
    return hashlib.md5(text.encode('utf-8')).hexdigest()


def hk_application(sk_id_curr: int | str) -> str:
    return _md5(f'application|{sk_id_curr}')


def hk_bureau_credit(sk_id_bureau: int | str) -> str:
    return _md5(f'bureau|{sk_id_bureau}')


def hk_prev_application(sk_id_prev: int | str) -> str:
    return _md5(f'prev_application|{sk_id_prev}')


def hk_link_application_bureau(sk_id_curr: int | str, sk_id_bureau: int | str) -> str:
    return _md5(f'link_app_bureau|{sk_id_curr}|{sk_id_bureau}')


def hk_link_application_prev(sk_id_curr: int | str, sk_id_prev: int | str) -> str:
    return _md5(f'link_app_prev|{sk_id_curr}|{sk_id_prev}')


def hashdiff(*parts: Any) -> str:
    payload = '|'.join('' if p is None else str(p) for p in parts)
    return _md5(payload)


def hashdiff_json(data: dict[str, Any]) -> str:
    return _md5(json.dumps(data, sort_keys=True, default=str))

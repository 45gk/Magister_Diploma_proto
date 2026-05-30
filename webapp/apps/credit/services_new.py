"""
Сервисы (_new): ML/Agent + загрузка CSV из банковских выгрузок.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import requests
from django.conf import settings

from .csv_loader_interface import CsvBatchLoadResult, CsvLoadResult, CsvSourceLoader
from .csv_loader_new import HomeCreditCsvLoader, get_default_csv_loader


def call_ml_score_new(application_id: int, features: dict[str, Any]) -> dict[str, Any]:
    response = requests.post(
        f'{settings.ML_SERVICE_URL}/ml/score',
        json={'application_id': application_id, 'features': features},
        timeout=10,
    )
    response.raise_for_status()
    return response.json()


def call_agent_explain_new(
    application_id: int,
    features: dict[str, Any],
    scoring_data: dict[str, Any],
    mode: str,
) -> dict[str, Any]:
    payload = {
        'application_id': application_id,
        'features': features,
        'scoring_result': {
            'default_probability': scoring_data['default_probability'],
            'model_version': scoring_data['model_version'],
        },
        'explain_data': {'feature_importances': scoring_data.get('feature_importances', {})},
        'mode': mode,
    }
    response = requests.post(f'{settings.AGENT_SERVICE_URL}/agent/explain', json=payload, timeout=10)
    response.raise_for_status()
    return response.json()


def load_csv_file_new(
    dataset_key: str,
    file_path: Path | str,
    loader: CsvSourceLoader | None = None,
    *,
    strip_junk: bool = True,
    enrich_junk: bool = False,
    limit: int | None = None,
) -> CsvLoadResult:
    """Загрузить один CSV с диска."""
    loader = loader or get_default_csv_loader()
    return loader.load_file(
        dataset_key,
        file_path,
        strip_junk=strip_junk,
        enrich_junk=enrich_junk,
        limit=limit,
    )


def load_csv_upload_new(
    dataset_key: str,
    uploaded_file,
    loader: CsvSourceLoader | None = None,
    *,
    strip_junk: bool = True,
    enrich_junk: bool = False,
    limit: int | None = None,
) -> CsvLoadResult:
    """Загрузить CSV из Django UploadedFile."""
    loader = loader or get_default_csv_loader()
    uploaded_file.seek(0)
    return loader.load_stream(
        dataset_key,
        uploaded_file,
        source_name=getattr(uploaded_file, 'name', ''),
        strip_junk=strip_junk,
        enrich_junk=enrich_junk,
        limit=limit,
    )


def load_csv_directory_new(
    directory: Path | str,
    loader: CsvSourceLoader | None = None,
    **kwargs: Any,
) -> CsvBatchLoadResult:
    """Загрузить все известные CSV из папки (например, распакованный Kaggle)."""
    loader = loader or get_default_csv_loader()
    return loader.load_directory(directory, **kwargs)


def preview_csv_rows_new(
    result: CsvLoadResult,
    max_rows: int = 5,
) -> list[dict[str, Any]]:
    """Первые строки для отображения в UI."""
    return result.rows[:max_rows]

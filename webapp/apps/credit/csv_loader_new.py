"""
Реализация загрузки CSV Home Credit Default Risk.
"""

from __future__ import annotations

import csv
import io
from pathlib import Path
from typing import Any, BinaryIO, Iterator, Sequence

from django.db import models

from .csv_loader_interface import CsvDatasetSpec, CsvLoadResult, CsvSourceLoader
from .models import (
    ETL_JUNK_FIELDS,
    ApplicationTest,
    ApplicationTrain,
    Bureau,
    BureauBalance,
    CreditCardBalance,
    InstallmentsPayments,
    PosCashBalance,
    PreviousApplication,
)

# Колонки Kaggle (без мусорных полей models_1)
_DATASET_MODELS: dict[str, type[models.Model]] = {
    'application_train': ApplicationTrain,
    'application_test': ApplicationTest,
    'bureau': Bureau,
    'bureau_balance': BureauBalance,
    'previous_application': PreviousApplication,
    'installments_payments': InstallmentsPayments,
    'credit_card_balance': CreditCardBalance,
    'pos_cash_balance': PosCashBalance,
}

_DATASET_FILENAMES: dict[str, str] = {
    'application_train': 'application_train.csv',
    'application_test': 'application_test.csv',
    'bureau': 'bureau.csv',
    'bureau_balance': 'bureau_balance.csv',
    'previous_application': 'previous_application.csv',
    'installments_payments': 'installments_payments.csv',
    'credit_card_balance': 'credit_card_balance.csv',
    'pos_cash_balance': 'POS_CASH_balance.csv',
}

# Симуляция мусорных полей АБС при enrich_junk=True
_JUNK_ENRICHERS: dict[str, dict[str, Any]] = {
    'ApplicationTrain': {
        'legacy_amt_income_text': lambda row: str(row.get('amt_income_total') or ''),
        'internal_sync_token': 'PENDING_MIGRATION',
    },
    'ApplicationTest': {
        'export_batch_label': 'BATCH_UNKNOWN',
    },
    'Bureau': {
        'old_sys_bureau_ref': lambda row: f"LEG-{row.get('sk_id_bureau', '')}",
    },
    'BureauBalance': {
        'raw_status_dump': lambda row: f"status={row.get('status', '')}|raw",
    },
    'InstallmentsPayments': {
        'source_file_row_no': 0.0,
    },
    'PosCashBalance': {
        'abs_operator_note': '',
    },
}


def _model_kaggle_columns(model_cls: type[models.Model]) -> tuple[str, ...]:
    """Имена колонок CSV (UPPER) по полям модели, без мусора и без surrogate id."""
    junk = set(ETL_JUNK_FIELDS.get(model_cls.__name__, ()))
    columns: list[str] = []
    for f in model_cls._meta.get_fields():
        if not getattr(f, 'concrete', False):
            continue
        if f.name in junk or f.name == 'id':
            continue
        if isinstance(f, models.AutoField):
            continue
        db_col = getattr(f, 'db_column', None) or f.name.upper()
        columns.append(db_col)
    return tuple(columns)


def _model_field_names(model_cls: type[models.Model], *, include_junk: bool) -> set[str]:
    junk = set() if include_junk else set(ETL_JUNK_FIELDS.get(model_cls.__name__, ()))
    names: set[str] = set()
    for f in model_cls._meta.get_fields():
        if not getattr(f, 'concrete', False):
            continue
        if f.name in junk or f.name == 'id':
            continue
        if isinstance(f, models.AutoField):
            continue
        names.add(f.name)
    return names


def _coerce_value(field: models.Field, raw: str) -> Any:
    if raw == '' or raw is None:
        return None
    if isinstance(field, (models.IntegerField, models.BigIntegerField, models.SmallIntegerField)):
        try:
            return int(float(raw))
        except (TypeError, ValueError):
            return None
    if isinstance(field, (models.FloatField, models.DecimalField)):
        try:
            return float(raw)
        except (TypeError, ValueError):
            return None
    return raw


class HomeCreditCsvLoader(CsvSourceLoader):
    """Загрузчик CSV под models_1 / Kaggle Home Credit."""

    def supported_datasets(self) -> Sequence[CsvDatasetSpec]:
        specs = []
        for key, model_cls in _DATASET_MODELS.items():
            specs.append(
                CsvDatasetSpec(
                    key=key,
                    filename=_DATASET_FILENAMES[key],
                    model_label=model_cls.__name__,
                    kaggle_columns=_model_kaggle_columns(model_cls),
                )
            )
        return specs

    def validate_headers(self, dataset_key: str, headers: Sequence[str]) -> list[str]:
        spec = self.get_dataset_spec(dataset_key)
        normalized = {self.normalize_header(h) for h in headers}
        missing = []
        for col in spec.kaggle_columns:
            if self.normalize_header(col) not in normalized:
                missing.append(col)
        return missing

    def load_file(
        self,
        dataset_key: str,
        file_path: Path | str,
        *,
        strip_junk: bool = True,
        enrich_junk: bool = False,
        limit: int | None = None,
        encoding: str = 'utf-8',
    ) -> CsvLoadResult:
        path = Path(file_path)
        with path.open('rb') as fh:
            return self.load_stream(
                dataset_key,
                fh,
                source_name=str(path),
                strip_junk=strip_junk,
                enrich_junk=enrich_junk,
                limit=limit,
                encoding=encoding,
            )

    def load_stream(
        self,
        dataset_key: str,
        stream: BinaryIO,
        *,
        source_name: str = '',
        strip_junk: bool = True,
        enrich_junk: bool = False,
        limit: int | None = None,
        encoding: str = 'utf-8',
    ) -> CsvLoadResult:
        result = CsvLoadResult(
            dataset=dataset_key,
            row_count=0,
            junk_fields_stripped=strip_junk,
            source_name=source_name,
        )
        try:
            rows = list(
                self.iter_rows(
                    dataset_key,
                    stream,
                    strip_junk=strip_junk,
                    enrich_junk=enrich_junk,
                    encoding=encoding,
                )
            )
            if limit is not None:
                rows = rows[:limit]
            result.rows = rows
            result.row_count = len(rows)
        except Exception as exc:
            result.errors.append(str(exc))
        return result

    def iter_rows(
        self,
        dataset_key: str,
        stream: BinaryIO,
        *,
        strip_junk: bool = True,
        enrich_junk: bool = False,
        encoding: str = 'utf-8',
    ) -> Iterator[dict[str, Any]]:
        model_cls = _DATASET_MODELS[dataset_key]
        model_label = model_cls.__name__
        allowed = _model_field_names(model_cls, include_junk=not strip_junk)
        junk_names = set(ETL_JUNK_FIELDS.get(model_label, ()))
        field_by_name = {
            f.name: f
            for f in model_cls._meta.get_fields()
            if getattr(f, 'concrete', False) and not isinstance(f, models.AutoField)
        }

        text = io.TextIOWrapper(stream, encoding=encoding, newline='')
        reader = csv.DictReader(text)
        if not reader.fieldnames:
            raise ValueError('CSV без заголовка')

        missing = self.validate_headers(dataset_key, reader.fieldnames)
        if missing:
            raise ValueError(f'Отсутствуют колонки: {", ".join(missing[:10])}{"..." if len(missing) > 10 else ""}')

        header_map = {self.normalize_header(h): h for h in reader.fieldnames}

        for raw_row in reader:
            row: dict[str, Any] = {}
            for norm_key, orig_header in header_map.items():
                if norm_key not in allowed and norm_key not in junk_names:
                    continue
                raw_val = raw_row.get(orig_header, '')
                field = field_by_name.get(norm_key)
                if field is not None and not isinstance(field, models.ForeignKey):
                    row[norm_key] = _coerce_value(field, raw_val)
                else:
                    # FK и неизвестные — целые ключи из CSV
                    if raw_val == '':
                        row[norm_key] = None
                    else:
                        try:
                            row[norm_key] = int(float(raw_val))
                        except (TypeError, ValueError):
                            row[norm_key] = raw_val

            if enrich_junk:
                self._apply_junk_enrichment(model_label, row)

            if strip_junk:
                for key in junk_names:
                    row.pop(key, None)

            yield row

    @staticmethod
    def _apply_junk_enrichment(model_label: str, row: dict[str, Any]) -> None:
        enrichers = _JUNK_ENRICHERS.get(model_label, {})
        for key, value in enrichers.items():
            if callable(value):
                row[key] = value(row)
            else:
                row[key] = value

    def strip_junk_from_rows(self, model_label: str, rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Явная очистка мусорных полей (для ETL-пайплайна)."""
        junk = set(ETL_JUNK_FIELDS.get(model_label, ()))
        cleaned = []
        for row in rows:
            cleaned.append({k: v for k, v in row.items() if k not in junk})
        return cleaned


def get_default_csv_loader() -> HomeCreditCsvLoader:
    """Фабрика для DI во views_new / services_new."""
    return HomeCreditCsvLoader()

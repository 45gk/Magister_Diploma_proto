"""
Интерфейс загрузки исходных данных из CSV (слой банковской системы → staging).
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, BinaryIO, Iterator, Mapping, Sequence


@dataclass(frozen=True)
class CsvDatasetSpec:
    """Описание одного CSV-источника."""

    key: str
    filename: str
    model_label: str
    kaggle_columns: tuple[str, ...]


@dataclass
class CsvLoadResult:
    """Результат чтения одного CSV."""

    dataset: str
    row_count: int
    rows: list[dict[str, Any]] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    junk_fields_stripped: bool = False
    source_name: str = ''

    @property
    def ok(self) -> bool:
        return not self.errors and self.row_count >= 0


@dataclass
class CsvBatchLoadResult:
    """Результат загрузки нескольких файлов за один вызов."""

    results: dict[str, CsvLoadResult] = field(default_factory=dict)

    @property
    def ok(self) -> bool:
        return all(r.ok for r in self.results.values())


class CsvSourceLoader(ABC):
    """
    Контракт загрузчика CSV из банковских систем.

    Реализации читают файлы Kaggle Home Credit (и аналоги), нормализуют
    заголовки, приводят типы и опционально отбрасывают мусорные поля ETL.
    """

    @abstractmethod
    def supported_datasets(self) -> Sequence[CsvDatasetSpec]:
        """Список поддерживаемых типов выгрузок."""

    @abstractmethod
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
        """Загрузить CSV с диска."""

    @abstractmethod
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
        """Загрузить CSV из потока (upload, S3, SFTP)."""

    @abstractmethod
    def validate_headers(
        self,
        dataset_key: str,
        headers: Sequence[str],
    ) -> list[str]:
        """
        Проверить заголовки файла.
        Возвращает список отсутствующих обязательных колонок Kaggle.
        """

    @abstractmethod
    def iter_rows(
        self,
        dataset_key: str,
        stream: BinaryIO,
        *,
        strip_junk: bool = True,
        enrich_junk: bool = False,
        encoding: str = 'utf-8',
    ) -> Iterator[dict[str, Any]]:
        """Потоковая выдача строк без накопления всего файла в памяти."""

    def load_directory(
        self,
        directory: Path | str,
        *,
        datasets: Sequence[str] | None = None,
        strip_junk: bool = True,
        enrich_junk: bool = False,
        limit_per_file: int | None = None,
    ) -> CsvBatchLoadResult:
        """Загрузить все известные CSV из каталога (удобно для локального Kaggle)."""
        directory = Path(directory)
        batch = CsvBatchLoadResult()
        keys = list(datasets) if datasets else [s.key for s in self.supported_datasets()]
        for key in keys:
            spec = self.get_dataset_spec(key)
            path = directory / spec.filename
            if not path.is_file():
                batch.results[key] = CsvLoadResult(
                    dataset=key,
                    row_count=0,
                    errors=[f'Файл не найден: {path}'],
                    source_name=str(path),
                )
                continue
            batch.results[key] = self.load_file(
                key,
                path,
                strip_junk=strip_junk,
                enrich_junk=enrich_junk,
                limit=limit_per_file,
            )
        return batch

    def get_dataset_spec(self, dataset_key: str) -> CsvDatasetSpec:
        for spec in self.supported_datasets():
            if spec.key == dataset_key:
                return spec
        raise KeyError(f'Неизвестный dataset: {dataset_key}')

    @staticmethod
    def normalize_header(header: str) -> str:
        """SK_ID_CURR → sk_id_curr (как в models_1)."""
        return header.strip().lower()

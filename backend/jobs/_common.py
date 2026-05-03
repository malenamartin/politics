from __future__ import annotations

import json
from pathlib import Path
import uuid
from typing import Iterable, Mapping

from app.config import get_settings
from app.db.supabase_client import get_supabase


def upsert_rows(table: str, rows: Iterable[Mapping]) -> None:
    data = list(rows)
    if not data:
        return
    settings = get_settings()
    if settings.local_storage:
        _upsert_local(table, data)
        return
    get_supabase().table(table).upsert(data).execute()


def read_rows(table: str) -> list[dict]:
    settings = get_settings()
    if settings.local_storage:
        return _read_jsonl(table)
    response = get_supabase().table(table).select("*").execute()
    return response.data or []


def generate_id() -> str:
    return str(uuid.uuid4())


def _append_jsonl(table: str, rows: list[Mapping]) -> None:
    path = _table_path(table)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(dict(row), ensure_ascii=False) + "\n")


def _upsert_local(table: str, rows: list[Mapping]) -> None:
    existing = _read_jsonl(table)
    if rows and all("id" in row for row in rows):
        by_id: dict[str, dict] = {}
        for row in existing:
            if "id" in row:
                by_id[str(row["id"])] = row
        for row in rows:
            by_id[str(row["id"])] = dict(row)
        _write_jsonl(table, list(by_id.values()))
        return
    _append_jsonl(table, rows)


def _read_jsonl(table: str) -> list[dict]:
    path = _table_path(table)
    if not path.exists():
        return []
    output: list[dict] = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            text = line.strip()
            if not text:
                continue
            output.append(json.loads(text))
    return output


def _write_jsonl(table: str, rows: list[Mapping]) -> None:
    path = _table_path(table)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(dict(row), ensure_ascii=False) + "\n")


def _table_path(table: str) -> Path:
    settings = get_settings()
    return Path(settings.local_data_dir) / f"{table}.jsonl"

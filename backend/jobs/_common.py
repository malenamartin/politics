from __future__ import annotations

from typing import Iterable, Mapping

from app.db.supabase_client import get_supabase


def upsert_rows(table: str, rows: Iterable[Mapping]) -> None:
    data = list(rows)
    if not data:
        return
    get_supabase().table(table).upsert(data).execute()

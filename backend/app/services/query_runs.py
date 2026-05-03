from __future__ import annotations

import datetime as dt
from typing import Any

from jobs._common import generate_id, read_rows, upsert_rows


def create_query_run(query_text: str, horizon: int = 30) -> dict[str, Any]:
    now = dt.datetime.now(dt.timezone.utc).isoformat()
    run = {
        "id": generate_id(),
        "query_text": query_text.strip(),
        "aliases": _derive_aliases(query_text),
        "status": "queued",
        "horizon_days": _normalize_horizon(horizon),
        "coverage": {},
        "quality": {},
        "created_at": now,
        "started_at": None,
        "completed_at": None,
        "error": None,
    }
    upsert_rows("query_runs", [run])
    return run


def get_query_run(run_id: str) -> dict[str, Any] | None:
    for row in read_rows("query_runs"):
        if str(row.get("id")) == run_id:
            return row
    return None


def update_query_run(run_id: str, **fields: Any) -> dict[str, Any]:
    current = get_query_run(run_id)
    if not current:
        raise ValueError(f"query_run {run_id} not found")
    updated = {**current, **fields}
    upsert_rows("query_runs", [updated])
    return updated


def put_query_results(run_id: str, payload: dict[str, Any]) -> dict[str, Any]:
    row = {"id": run_id, "query_run_id": run_id, **payload}
    upsert_rows("query_results", [row])
    return row


def get_query_results(run_id: str) -> dict[str, Any] | None:
    for row in read_rows("query_results"):
        if str(row.get("query_run_id") or row.get("id")) == run_id:
            return row
    return None


def _derive_aliases(query_text: str) -> list[str]:
    base = query_text.strip()
    aliases = {base}
    if " " in base:
        aliases.add(base.replace(" ", ""))
    return [item for item in aliases if item]


def _normalize_horizon(horizon: int) -> int:
    if horizon <= 7:
        return 7
    if horizon <= 14:
        return 14
    return 30

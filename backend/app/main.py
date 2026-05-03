from __future__ import annotations

from collections import defaultdict
import datetime as dt
import logging
from pathlib import Path
import subprocess
import sys
from typing import Optional

from fastapi import Depends, FastAPI, Header, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from app.config import get_settings
from app.middleware.rate_limit import PublicRateLimitMiddleware
from app.services.forecast import build_forecast
from app.services.forecast import build_query_forecast
from app.services.query_runs import (
    create_query_run,
    get_query_results,
    get_query_run,
    update_query_run,
)
from app.services.recommendations import generate_recommendations
from app.services.recommendations import generate_query_recommendations
from app.services.sample_quality import quality_metadata
from app.services.sentiment_map import build_sentiment_map
from jobs._common import read_rows

app = FastAPI(title="Monitoreo Politico API", version="0.1.0")
app.add_middleware(PublicRateLimitMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=get_settings().cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
logger = logging.getLogger("monitoreo-politico")


def _require_pro_access(
    x_pro_key: str | None = Header(default=None),
    x_user_tier: str | None = Header(default=None),
) -> bool:
    settings = get_settings()
    if (x_user_tier or "").lower() == "pro":
        return True
    if settings.pro_api_key and x_pro_key == settings.pro_api_key:
        return True
    raise HTTPException(
        status_code=403,
        detail="Pro access required. Provide x-pro-key or x-user-tier=pro.",
    )


@app.middleware("http")
async def request_logger(request: Request, call_next):  # type: ignore[no-untyped-def]
    started_at = dt.datetime.now(dt.timezone.utc)
    try:
        response = await call_next(request)
    except Exception as exc:  # noqa: BLE001
        logger.exception("Unhandled error: %s", exc)
        return JSONResponse(status_code=500, content={"detail": "Internal server error"})

    elapsed = (dt.datetime.now(dt.timezone.utc) - started_at).total_seconds() * 1000
    logger.info(
        "request path=%s method=%s status=%s elapsed_ms=%.2f",
        request.url.path,
        request.method,
        response.status_code,
        elapsed,
    )
    return response


@app.get("/health")
def health() -> dict:
    settings = get_settings()
    storage_mode = "local" if settings.local_storage else "supabase"
    return {
        "status": "ok",
        "env": settings.app_env,
        "storage_mode": storage_mode,
        "minimum_significant_sample": settings.minimum_significant_sample,
    }


@app.get("/")
def root() -> dict:
    return {"service": "monitoreo-politico", "docs": "/docs"}


@app.get("/api/mentions/recent")
def recent_mentions(entity: Optional[str] = None, limit: int = 10) -> dict:
    rows = read_rows("mentions")
    if entity:
        rows = [row for row in rows if row.get("entity_name") == entity]
    rows.sort(key=lambda row: row.get("published_at", ""), reverse=True)
    sliced = rows[: max(1, min(limit, 100))]
    quality = quality_metadata(
        sample_size=len(rows),
        minimum_significant_sample=get_settings().minimum_significant_sample,
    )
    return {"items": sliced, "quality": quality}


@app.get("/api/stats/ai-mentions")
def ai_mentions(
    entity: Optional[str] = None,
    entities: Optional[str] = None,
    days: int = 7,
) -> dict:
    selected = _selected_entities(entity=entity, entities=entities)
    rows = _recent_ai_rows(days=days, selected_entities=selected)
    grouped: dict[tuple[str, str], int] = defaultdict(int)
    for row in rows:
        date = (row.get("observed_at") or "")[:10]
        grouped[(date, row.get("entity_name", ""))] += 1
    data = [
        {"date": date, "entity_name": entity_name, "mentions": count}
        for (date, entity_name), count in sorted(grouped.items())
    ]
    quality = quality_metadata(
        sample_size=len(rows),
        minimum_significant_sample=get_settings().minimum_significant_sample,
    )
    return {"items": data, "quality": quality}


@app.get("/api/stats/ai-sentiment")
def ai_sentiment(
    entity: Optional[str] = None,
    entities: Optional[str] = None,
    days: int = 7,
) -> dict:
    selected = _selected_entities(entity=entity, entities=entities)
    rows = _recent_ai_rows(days=days, selected_entities=selected)
    grouped: dict[tuple[str, str], dict] = defaultdict(lambda: {"sum": 0.0, "count": 0})
    for row in rows:
        date = (row.get("observed_at") or "")[:10]
        key = (date, row.get("entity_name", ""))
        grouped[key]["sum"] += float(row.get("sentiment_score", 0) or 0)
        grouped[key]["count"] += 1
    data = []
    for (date, entity_name), agg in sorted(grouped.items()):
        avg = agg["sum"] / agg["count"] if agg["count"] else 0
        data.append({"date": date, "entity_name": entity_name, "avg_sentiment": round(avg, 4)})
    quality = quality_metadata(
        sample_size=len(rows),
        minimum_significant_sample=get_settings().minimum_significant_sample,
    )
    return {"items": data, "quality": quality}


@app.get("/api/stats/share-of-voice")
def share_of_voice(days: int = 7, entities: Optional[str] = None) -> dict:
    selected = _selected_entities(entity=None, entities=entities)
    rows = _recent_ai_rows(days=days, selected_entities=selected)
    totals: dict[str, int] = defaultdict(int)
    for row in rows:
        totals[row.get("entity_name", "")] += 1
    grand_total = sum(totals.values()) or 1
    data = [
        {"entity_name": name, "mentions": count, "share_of_voice": round(count / grand_total, 4)}
        for name, count in sorted(totals.items(), key=lambda x: x[1], reverse=True)
    ]
    quality = quality_metadata(
        sample_size=len(rows),
        minimum_significant_sample=get_settings().minimum_significant_sample,
    )
    return {"items": data, "quality": quality}


@app.get("/api/public/access")
def public_access_info() -> dict:
    settings = get_settings()
    return {
        "mode": "freemium",
        "public_features": [
            "recent_mentions",
            "ai_mentions",
            "ai_sentiment",
            "share_of_voice",
        ],
        "pro_features": ["forecast", "recommendations"],
        "rate_limit_per_minute": settings.public_rate_limit_per_minute,
    }


@app.get("/api/pro/forecast")
def forecast(
    entity: str,
    horizon: int = 7,
    _: bool = Depends(_require_pro_access),
) -> dict:
    payload = build_forecast(entity=entity, horizon=horizon)
    quality = quality_metadata(
        sample_size=len(payload.get("baseline", [])),
        minimum_significant_sample=get_settings().minimum_significant_sample,
    )
    return {
        "entity_name": payload["entity_name"],
        "horizon_days": payload["horizon_days"],
        "baseline": payload["baseline"],
        "forecast": payload["forecast"],
        "model_version": payload["model_version"],
        "metrics": payload["metrics"],
        "quality": quality,
    }


@app.get("/api/pro/recommendations")
def recommendations(
    entity: str,
    horizon: int = 7,
    _: bool = Depends(_require_pro_access),
) -> dict:
    payload = generate_recommendations(entity=entity, horizon=horizon)
    quality = quality_metadata(
        sample_size=payload["signals"]["sample_size"],
        minimum_significant_sample=get_settings().minimum_significant_sample,
    )
    return {
        "entity_name": payload["entity_name"],
        "horizon_days": payload["horizon_days"],
        "recommendations": payload["recommendations"],
        "signals": payload["signals"],
        "quality": quality,
    }


class CreateQueryRunPayload(BaseModel):
    query_text: str = Field(min_length=2, max_length=200)
    horizon: int = Field(default=30, ge=7, le=30)


@app.post("/api/query-runs")
def create_query_run_endpoint(payload: CreateQueryRunPayload) -> dict:
    run = create_query_run(query_text=payload.query_text, horizon=payload.horizon)
    _spawn_adhoc_job(run["id"])
    return {"query_run": run}


@app.get("/api/query-runs/{run_id}")
def query_run_status(run_id: str) -> dict:
    run = get_query_run(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="query_run not found")
    return {"query_run": run}


@app.get("/api/query-runs/{run_id}/results")
def query_run_results(run_id: str) -> dict:
    run = get_query_run(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="query_run not found")
    result = get_query_results(run_id)
    if not result:
        raise HTTPException(status_code=404, detail="query_run results not found")
    horizon = int(run.get("horizon_days", 30))
    forecast = build_query_forecast(query_run_id=run_id, horizon=horizon)
    recommendations = generate_query_recommendations(query_run_id=run_id, horizon=horizon)
    sentiment_map = build_sentiment_map(query_run_id=run_id)
    return {
        "query_run": run,
        "result": result,
        "sentiment_map": sentiment_map,
        "forecast": forecast,
        "recommendations": recommendations,
    }


def _selected_entities(entity: Optional[str], entities: Optional[str]) -> set[str]:
    if entity:
        return {entity}
    if not entities:
        return set()
    return {item.strip() for item in entities.split(",") if item.strip()}


def _recent_ai_rows(days: int, selected_entities: set[str]) -> list[dict]:
    rows = read_rows("ai_observations")
    cutoff = dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=max(1, days))
    items: list[dict] = []
    for row in rows:
        observed = row.get("observed_at")
        if not observed:
            continue
        try:
            observed_dt = dt.datetime.fromisoformat(observed.replace("Z", "+00:00"))
        except ValueError:
            continue
        if observed_dt >= cutoff:
            items.append(row)
    if selected_entities:
        items = [row for row in items if row.get("entity_name") in selected_entities]
    items.sort(key=lambda row: row.get("observed_at", ""), reverse=True)
    return items


def _spawn_adhoc_job(query_run_id: str) -> None:
    backend_root = Path(__file__).resolve().parents[1]
    command = [
        sys.executable,
        "-c",
        f"from jobs.adhoc_analysis_job import run; run('{query_run_id}')",
    ]
    subprocess.Popen(command, cwd=backend_root, start_new_session=True)  # noqa: S603



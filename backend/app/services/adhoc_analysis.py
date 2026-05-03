from __future__ import annotations

import datetime as dt
import hashlib
import logging
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeoutError
from collections import Counter
from dataclasses import dataclass
from statistics import pstdev
from typing import Any

from app.config import get_settings
from app.services.ai_observation import AIObservationService
from app.services.ingestion_news import NewsIngestionService
from app.services.ingestion_reddit import RedditIngestionService
from app.services.ingestion_web import WebIngestionService
from app.services.ingestion_x import XIngestionService
from app.services.ingestion_youtube import YouTubeIngestionService
from app.services.narrative_taxonomy import infer_narrative_from_text
from app.services.recommendations import generate_query_recommendations
from app.services.sample_quality import adaptive_quality_metadata
from app.services.scoring import ScoringService
from jobs._common import upsert_rows

logger = logging.getLogger("monitoreo-politico.adhoc")


@dataclass
class MentionCandidate:
    source: str
    content: str
    published_at: str
    url: str


def run_adhoc_analysis(query_run: dict[str, Any]) -> dict[str, Any]:
    settings = get_settings()
    topic = str(query_run["query_text"])
    query_run_id = str(query_run["id"])

    ai_service = AIObservationService()
    score_service = ScoringService()
    coverage = Counter()
    candidates: list[MentionCandidate] = []
    started_at = dt.datetime.now(dt.timezone.utc)
    budget_seconds = settings.query_budget_seconds
    logger.info("adhoc.start query_run_id=%s query=%s", query_run_id, topic)

    # 1) Priority source: AI engines
    ai_observations = ai_service.collect_for_topic(topic=topic, engines=settings.ai_engines)
    for obs in ai_observations:
        candidates.append(
            MentionCandidate(
                source="ai",
                content=obs.response_excerpt,
                published_at=obs.observed_at,
                url=f"ai://{obs.engine}/{hashlib.md5(obs.prompt_template.encode()).hexdigest()}",
            )
        )
    coverage["ai"] += len(ai_observations)
    logger.info("adhoc.source query_run_id=%s source=ai count=%s", query_run_id, len(ai_observations))

    # 2) Complementary sources
    source_timeout = max(3, settings.source_timeout_seconds)
    if _within_budget(started_at, budget_seconds):
        candidates.extend(
            _collect_with_timeout(
                "news",
                lambda: _collect_news(topic, coverage),
                timeout_seconds=source_timeout,
            )
        )
    if _within_budget(started_at, budget_seconds):
        candidates.extend(
            _collect_with_timeout(
                "x",
                lambda: _collect_x(topic, coverage),
                timeout_seconds=source_timeout,
            )
        )
    if _within_budget(started_at, budget_seconds):
        candidates.extend(
            _collect_with_timeout(
                "reddit",
                lambda: _collect_reddit(topic, coverage),
                timeout_seconds=source_timeout,
            )
        )
    if _within_budget(started_at, budget_seconds):
        candidates.extend(
            _collect_with_timeout(
                "youtube",
                lambda: _collect_youtube(topic, coverage),
                timeout_seconds=source_timeout,
            )
        )
    if _within_budget(started_at, budget_seconds):
        candidates.extend(
            _collect_with_timeout(
                "web",
                lambda: _collect_web(topic, coverage),
                timeout_seconds=source_timeout,
            )
        )

    # 3) Dedup and score
    unique = _deduplicate(candidates)
    logger.info(
        "adhoc.dedup query_run_id=%s raw=%s unique=%s",
        query_run_id,
        len(candidates),
        len(unique),
    )
    max_llm = max(1, settings.max_llm_scoring_items)
    rows = []
    for idx, item in enumerate(unique):
        if idx < max_llm:
            scored = score_service.score_text(entity_name=topic, text=item.content)
        else:
            scored = _fast_score_fallback(topic=topic, text=item.content)
        rows.append(
            {
                "id": _row_id(query_run_id, item),
                "query_run_id": query_run_id,
                "query_text": topic,
                "source": item.source,
                "content": item.content[:3000],
                "sentiment_label": scored["sentiment_label"],
                "sentiment_score": scored["sentiment_score"],
                "narrative_tag": scored["narrative_tag"],
                "published_at": item.published_at,
                "url": item.url,
                "created_at": dt.datetime.now(dt.timezone.utc).isoformat(),
            }
        )
    upsert_rows("query_mentions", rows)

    sentiment_scores = [float(r["sentiment_score"]) for r in rows]
    adaptive_quality = adaptive_quality_metadata(
        sample_size=len(rows),
        distinct_sources=len({r["source"] for r in rows}) if rows else 0,
        sentiment_std_proxy=pstdev(sentiment_scores) if len(sentiment_scores) > 1 else 0.0,
    )
    recommendations = generate_query_recommendations(
        query_run_id=query_run_id,
        horizon=int(query_run.get("horizon_days", 30)),
    )
    result = {
        "query_run_id": query_run_id,
        "query_text": topic,
        "status": "completed",
        "coverage": dict(coverage),
        "quality": adaptive_quality,
        "summary": {
            "total_mentions": len(rows),
            "sources_used": sorted({r["source"] for r in rows}),
            "top_narratives": recommendations["signals"]["top_narratives"],
        },
        "recommendations": recommendations,
    }
    logger.info(
        "adhoc.complete query_run_id=%s sample=%s significant=%s",
        query_run_id,
        adaptive_quality["sample_size"],
        adaptive_quality["is_significant"],
    )
    return result


def _collect_news(topic: str, coverage: Counter) -> list[MentionCandidate]:
    settings = get_settings()
    if not settings.newsapi_key:
        return []
    service = NewsIngestionService()
    items = []
    for row in service.collect([topic])[: settings.max_items_per_source]:
        items.append(
            MentionCandidate(
                source="news",
                content=row.content,
                published_at=row.published_at,
                url=row.url,
            )
        )
    coverage["news"] += len(items)
    logger.info("adhoc.source source=news count=%s", len(items))
    return items


def _collect_x(topic: str, coverage: Counter) -> list[MentionCandidate]:
    settings = get_settings()
    if not settings.x_enabled:
        return []
    service = XIngestionService()
    per_entity_limit = min(settings.max_items_per_source, 80)
    rows = service.collect([topic], per_entity_limit=per_entity_limit)
    items = [
        MentionCandidate(
            source="x",
            content=row.content,
            published_at=row.published_at,
            url=row.url,
        )
        for row in rows
    ]
    coverage["x"] += len(items)
    logger.info("adhoc.source source=x count=%s", len(items))
    return items


def _collect_reddit(topic: str, coverage: Counter) -> list[MentionCandidate]:
    settings = get_settings()
    try:
        rows = RedditIngestionService().collect(topic=topic, limit=settings.max_items_per_source)
    except Exception:
        rows = []
    items = [
        MentionCandidate(
            source=row.source,
            content=row.content,
            published_at=row.published_at,
            url=row.url,
        )
        for row in rows
    ]
    coverage["reddit"] += len(items)
    logger.info("adhoc.source source=reddit count=%s", len(items))
    return items


def _collect_youtube(topic: str, coverage: Counter) -> list[MentionCandidate]:
    settings = get_settings()
    try:
        rows = YouTubeIngestionService().collect(topic=topic, limit=settings.max_items_per_source)
    except Exception:
        rows = []
    items = [
        MentionCandidate(
            source=row.source,
            content=row.content,
            published_at=row.published_at,
            url=row.url,
        )
        for row in rows
    ]
    coverage["youtube"] += len(items)
    logger.info("adhoc.source source=youtube count=%s", len(items))
    return items


def _collect_web(topic: str, coverage: Counter) -> list[MentionCandidate]:
    settings = get_settings()
    try:
        rows = WebIngestionService().collect(topic=topic, limit=settings.max_items_per_source)
    except Exception:
        rows = []
    items = [
        MentionCandidate(
            source=row.source,
            content=row.content,
            published_at=row.published_at,
            url=row.url,
        )
        for row in rows
    ]
    coverage["web"] += len(items)
    logger.info("adhoc.source source=web count=%s", len(items))
    return items


def _deduplicate(items: list[MentionCandidate]) -> list[MentionCandidate]:
    seen: set[str] = set()
    output: list[MentionCandidate] = []
    for item in items:
        signature = f"{item.source}|{_normalize_text(item.content)}|{(item.url or '').strip().lower()}"
        digest = hashlib.md5(signature.encode("utf-8")).hexdigest()
        if digest in seen:
            continue
        seen.add(digest)
        output.append(item)
    return output


def _normalize_text(text: str) -> str:
    return " ".join(text.lower().split())[:1200]


def _row_id(query_run_id: str, item: MentionCandidate) -> str:
    value = f"{query_run_id}|{item.source}|{item.url}|{_normalize_text(item.content)}"
    return hashlib.md5(value.encode("utf-8")).hexdigest()


def _within_budget(started_at: dt.datetime, budget_seconds: int) -> bool:
    return (dt.datetime.now(dt.timezone.utc) - started_at).total_seconds() < max(5, budget_seconds)


def _fast_score_fallback(topic: str, text: str) -> dict[str, Any]:
    lowered = text.lower()
    topic_tokens = [token for token in topic.lower().split() if len(token) > 2]
    is_mentioned = any(token in lowered for token in topic_tokens) if topic_tokens else False
    return {
        "is_mentioned": is_mentioned,
        "sentiment_label": "neutral",
        "sentiment_score": 0.0,
        "narrative_tag": infer_narrative_from_text(text),
    }


def _collect_with_timeout(
    source_name: str,
    collector: Any,
    *,
    timeout_seconds: int,
) -> list[MentionCandidate]:
    executor = ThreadPoolExecutor(max_workers=1)
    future = executor.submit(collector)
    try:
        return future.result(timeout=timeout_seconds)
    except FutureTimeoutError:
        logger.warning("adhoc.source_timeout source=%s timeout_s=%s", source_name, timeout_seconds)
        future.cancel()
        return []
    except Exception:
        logger.exception("adhoc.source_error source=%s", source_name)
        future.cancel()
        return []
    finally:
        executor.shutdown(wait=False, cancel_futures=True)

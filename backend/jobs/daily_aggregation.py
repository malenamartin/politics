from __future__ import annotations

import datetime as dt
from collections import defaultdict
from typing import Dict, Tuple

from app.db.supabase_client import get_supabase
from jobs._common import upsert_rows


def run(stat_date: dt.date | None = None) -> int:
    target_date = stat_date or dt.datetime.now(dt.timezone.utc).date()
    start = dt.datetime.combine(target_date, dt.time.min, tzinfo=dt.timezone.utc).isoformat()
    end = dt.datetime.combine(target_date, dt.time.max, tzinfo=dt.timezone.utc).isoformat()

    supabase = get_supabase()
    ai_rows = (
        supabase.table("ai_observations")
        .select("engine,entity_name,sentiment_label,sentiment_score,narrative_tag")
        .gte("observed_at", start)
        .lte("observed_at", end)
        .execute()
        .data
    )
    mention_rows = (
        supabase.table("mentions")
        .select("source,entity_name,sentiment_label,sentiment_score")
        .gte("published_at", start)
        .lte("published_at", end)
        .execute()
        .data
    )

    grouped: Dict[Tuple[str, str, str], dict] = defaultdict(
        lambda: {
            "total_mentions": 0,
            "score_sum": 0.0,
            "positive_count": 0,
            "neutral_count": 0,
            "negative_count": 0,
            "narratives": defaultdict(int),
        }
    )

    for row in ai_rows:
        key = ("ai", row["entity_name"], row.get("engine") or "")
        _accumulate(grouped[key], row["sentiment_label"], float(row["sentiment_score"] or 0))
        grouped[key]["narratives"][row.get("narrative_tag") or "unknown"] += 1

    for row in mention_rows:
        key = (row["source"], row["entity_name"], "")
        _accumulate(grouped[key], row["sentiment_label"], float(row["sentiment_score"] or 0))

    totals_by_channel: Dict[Tuple[str, str], int] = defaultdict(int)
    for (channel, _, _), data in grouped.items():
        totals_by_channel[(channel, target_date.isoformat())] += data["total_mentions"]

    rows = []
    for (channel, entity_name, engine), data in grouped.items():
        total = data["total_mentions"]
        channel_total = totals_by_channel[(channel, target_date.isoformat())] or 1
        top_narratives = sorted(
            data["narratives"].items(),
            key=lambda x: x[1],
            reverse=True,
        )[:5]
        rows.append(
            {
                "stat_date": target_date.isoformat(),
                "entity_name": entity_name,
                "channel": channel,
                "engine": engine or None,
                "total_mentions": total,
                "share_of_voice": round(total / channel_total, 4),
                "avg_sentiment": round(data["score_sum"] / total, 4) if total else 0,
                "positive_count": data["positive_count"],
                "neutral_count": data["neutral_count"],
                "negative_count": data["negative_count"],
                "top_narratives": [
                    {"tag": tag, "count": count} for tag, count in top_narratives
                ],
            }
        )

    upsert_rows("daily_stats", rows)
    print(f"daily_aggregation: date={target_date.isoformat()} rows={len(rows)}")
    return len(rows)


def _accumulate(bucket: dict, label: str, score: float) -> None:
    bucket["total_mentions"] += 1
    bucket["score_sum"] += score
    normalized = (label or "neutral").lower()
    if normalized not in {"positive", "neutral", "negative"}:
        normalized = "neutral"
    bucket[f"{normalized}_count"] += 1


if __name__ == "__main__":
    run()

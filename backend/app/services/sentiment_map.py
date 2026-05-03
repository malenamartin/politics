from __future__ import annotations

from collections import Counter, defaultdict
from typing import Any

from app.services.narrative_taxonomy import normalize_narrative_tag
from jobs._common import read_rows


def build_sentiment_map(query_run_id: str) -> dict[str, Any]:
    rows = [
        row
        for row in read_rows("query_mentions")
        if str(row.get("query_run_id")) == query_run_id
    ]
    total = len(rows)
    if total == 0:
        return {
            "totals": {"positive": 0, "neutral": 0, "negative": 0},
            "distribution": {"positive": 0.0, "neutral": 0.0, "negative": 0.0},
            "by_source": {},
            "narrative_intensity": [],
        }

    sentiment_totals = Counter(str(row.get("sentiment_label") or "neutral") for row in rows)
    by_source: dict[str, Counter] = defaultdict(Counter)
    narrative_agg: dict[str, dict[str, float]] = defaultdict(
        lambda: {"volume": 0, "sentiment_sum": 0.0, "positive": 0, "negative": 0}
    )
    for row in rows:
        source = str(row.get("source") or "other")
        label = str(row.get("sentiment_label") or "neutral")
        score = float(row.get("sentiment_score", 0) or 0)
        narrative = normalize_narrative_tag(
            str(row.get("narrative_tag") or ""),
            text=str(row.get("content", "")),
        )
        by_source[source][label] += 1
        narrative_agg[narrative]["volume"] += 1
        narrative_agg[narrative]["sentiment_sum"] += score
        if label == "positive":
            narrative_agg[narrative]["positive"] += 1
        elif label == "negative":
            narrative_agg[narrative]["negative"] += 1

    narrative_intensity = []
    for tag, agg in narrative_agg.items():
        volume = int(agg["volume"])
        avg_sentiment = agg["sentiment_sum"] / max(1, volume)
        momentum = (agg["positive"] - agg["negative"]) / max(1, volume)
        narrative_intensity.append(
            {
                "tag": tag,
                "volume": volume,
                "avg_sentiment": round(avg_sentiment, 4),
                "momentum": round(momentum, 4),
            }
        )
    narrative_intensity.sort(key=lambda item: item["volume"], reverse=True)

    return {
        "totals": {
            "positive": sentiment_totals.get("positive", 0),
            "neutral": sentiment_totals.get("neutral", 0),
            "negative": sentiment_totals.get("negative", 0),
        },
        "distribution": {
            "positive": round(sentiment_totals.get("positive", 0) / total, 4),
            "neutral": round(sentiment_totals.get("neutral", 0) / total, 4),
            "negative": round(sentiment_totals.get("negative", 0) / total, 4),
        },
        "by_source": {
            source: {
                "positive": counts.get("positive", 0),
                "neutral": counts.get("neutral", 0),
                "negative": counts.get("negative", 0),
                "total": sum(counts.values()),
            }
            for source, counts in by_source.items()
        },
        "narrative_intensity": narrative_intensity[:10],
    }

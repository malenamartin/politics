from __future__ import annotations

import datetime as dt
from collections import Counter
from collections import defaultdict
from statistics import mean

from jobs._common import read_rows


def build_forecast(entity: str, horizon: int) -> dict:
    horizon_days = _normalize_horizon(horizon)
    daily = _daily_entity_series(entity)
    if len(daily) < 2:
        return {
            "entity_name": entity,
            "horizon_days": horizon_days,
            "baseline": [],
            "forecast": [],
            "model_version": "baseline_v1",
            "metrics": {"mae": None, "mape": None, "confidence": 0.2},
        }

    slope = _linear_trend_slope([row["mentions"] for row in daily])
    moving_avg_mentions = mean(row["mentions"] for row in daily[-7:])
    moving_avg_sentiment = mean(row["avg_sentiment"] for row in daily[-7:])
    moving_avg_sov = mean(row["share_of_voice"] for row in daily[-7:])

    last = daily[-1]
    predictions = []
    for step in range(1, horizon_days + 1):
        forecast_date = (
            dt.datetime.fromisoformat(last["date"]) + dt.timedelta(days=step)
        ).date().isoformat()
        projected_mentions = max(0, round(moving_avg_mentions + slope * step))
        predictions.append(
            {
                "date": forecast_date,
                "entity_name": entity,
                "predicted_mentions": projected_mentions,
                "predicted_avg_sentiment": round(moving_avg_sentiment, 4),
                "predicted_share_of_voice": round(max(0, min(1, moving_avg_sov)), 4),
            }
        )

    mae, mape = _backtest(daily)
    confidence = max(0.2, min(0.95, 1 - (mape / 100))) if mape is not None else 0.35
    return {
        "entity_name": entity,
        "horizon_days": horizon_days,
        "baseline": daily[-30:],
        "forecast": predictions,
        "model_version": "baseline_v1",
        "metrics": {
            "mae": None if mae is None else round(mae, 4),
            "mape": None if mape is None else round(mape, 4),
            "confidence": round(confidence, 4),
        },
    }


def build_query_forecast(query_run_id: str, horizon: int) -> dict:
    horizon_days = _normalize_horizon(horizon)
    daily = _daily_query_series(query_run_id)
    if len(daily) < 2:
        return {
            "query_run_id": query_run_id,
            "horizon_days": horizon_days,
            "baseline": daily,
            "forecast": [],
            "model_version": "baseline_v1",
            "metrics": {"mae": None, "mape": None, "confidence": 0.2},
        }
    slope = _linear_trend_slope([row["mentions"] for row in daily])
    moving_avg_mentions = mean(row["mentions"] for row in daily[-7:])
    moving_avg_sentiment = mean(row["avg_sentiment"] for row in daily[-7:])
    moving_avg_sov = mean(row["share_of_voice"] for row in daily[-7:])
    last = daily[-1]
    predictions = []
    for step in range(1, horizon_days + 1):
        forecast_date = (
            dt.datetime.fromisoformat(last["date"]) + dt.timedelta(days=step)
        ).date().isoformat()
        predictions.append(
            {
                "date": forecast_date,
                "predicted_mentions": max(0, round(moving_avg_mentions + slope * step)),
                "predicted_avg_sentiment": round(moving_avg_sentiment, 4),
                "predicted_share_of_voice": round(max(0, min(1, moving_avg_sov)), 4),
            }
        )
    scenario_forecast = _build_scenario_forecast(predictions)
    mae, mape = _backtest(daily)
    confidence = max(0.2, min(0.95, 1 - (mape / 100))) if mape is not None else 0.35
    return {
        "query_run_id": query_run_id,
        "horizon_days": horizon_days,
        "baseline": daily[-30:],
        "forecast": predictions,
        "model_version": "baseline_v1",
        "metrics": {
            "mae": None if mae is None else round(mae, 4),
            "mape": None if mape is None else round(mape, 4),
            "confidence": round(confidence, 4),
        },
        "scenario_forecast": scenario_forecast,
        "narrative_shift_risk": _narrative_shift_risk(query_run_id),
    }


def _daily_entity_series(entity: str) -> list[dict]:
    rows = read_rows("ai_observations")
    grouped: dict[str, dict] = defaultdict(
        lambda: {"mentions": 0, "sentiment_sum": 0.0, "sov_denominator": 0}
    )
    mentions_per_date: dict[str, int] = defaultdict(int)

    for row in rows:
        date = (row.get("observed_at") or "")[:10]
        if not date:
            continue
        mentions_per_date[date] += 1
        if row.get("entity_name") != entity:
            continue
        grouped[date]["mentions"] += 1
        grouped[date]["sentiment_sum"] += float(row.get("sentiment_score", 0) or 0)

    result: list[dict] = []
    for date in sorted(grouped.keys()):
        mentions = grouped[date]["mentions"]
        denom = mentions_per_date.get(date, mentions) or 1
        avg_sentiment = grouped[date]["sentiment_sum"] / mentions if mentions else 0
        result.append(
            {
                "date": date,
                "entity_name": entity,
                "mentions": mentions,
                "avg_sentiment": round(avg_sentiment, 4),
                "share_of_voice": round(mentions / denom, 4),
            }
        )
    return result


def _daily_query_series(query_run_id: str) -> list[dict]:
    rows = [
        row
        for row in read_rows("query_mentions")
        if str(row.get("query_run_id")) == query_run_id
    ]
    grouped: dict[str, dict] = defaultdict(lambda: {"mentions": 0, "sentiment_sum": 0.0})
    for row in rows:
        date = (row.get("published_at") or row.get("observed_at") or "")[:10]
        if not date:
            continue
        grouped[date]["mentions"] += 1
        grouped[date]["sentiment_sum"] += float(row.get("sentiment_score", 0) or 0)
    result: list[dict] = []
    for date in sorted(grouped.keys()):
        mentions = grouped[date]["mentions"]
        avg_sentiment = grouped[date]["sentiment_sum"] / mentions if mentions else 0
        result.append(
            {
                "date": date,
                "mentions": mentions,
                "avg_sentiment": round(avg_sentiment, 4),
                "share_of_voice": 1.0,
            }
        )
    return result


def _linear_trend_slope(values: list[int]) -> float:
    n = len(values)
    if n < 2:
        return 0
    x_mean = (n - 1) / 2
    y_mean = mean(values)
    num = sum((i - x_mean) * (y - y_mean) for i, y in enumerate(values))
    den = sum((i - x_mean) ** 2 for i in range(n))
    return num / den if den else 0


def _backtest(series: list[dict]) -> tuple[float | None, float | None]:
    if len(series) < 6:
        return (None, None)
    values = [row["mentions"] for row in series]
    errors = []
    pct_errors = []
    for i in range(3, len(values)):
        pred = mean(values[max(0, i - 3) : i])
        actual = values[i]
        err = abs(actual - pred)
        errors.append(err)
        if actual > 0:
            pct_errors.append(err / actual)
    if not errors:
        return (None, None)
    mae = mean(errors)
    mape = mean(pct_errors) * 100 if pct_errors else None
    return (mae, mape)


def _normalize_horizon(horizon: int) -> int:
    if horizon <= 7:
        return 7
    if horizon <= 14:
        return 14
    return 30


def _build_scenario_forecast(base: list[dict]) -> dict:
    def _scaled(multiplier: float) -> list[dict]:
        output = []
        for item in base:
            output.append(
                {
                    **item,
                    "predicted_mentions": max(
                        0,
                        round(item["predicted_mentions"] * multiplier),
                    ),
                }
            )
        return output

    return {
        "base": base,
        "bull": _scaled(1.18),
        "bear": _scaled(0.82),
    }


def _narrative_shift_risk(query_run_id: str) -> str:
    rows = [
        row
        for row in read_rows("query_mentions")
        if str(row.get("query_run_id")) == query_run_id
    ]
    if not rows:
        return "low"
    top_two = Counter(str(row.get("narrative_tag") or "other_relevant") for row in rows).most_common(2)
    if len(top_two) < 2:
        return "low"
    first = top_two[0][1]
    second = top_two[1][1]
    ratio = second / max(1, first)
    if ratio >= 0.85:
        return "high"
    if ratio >= 0.6:
        return "medium"
    return "low"

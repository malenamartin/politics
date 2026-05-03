from __future__ import annotations

from collections import Counter

from app.services.forecast import build_forecast, build_query_forecast
from app.services.narrative_taxonomy import normalize_narrative_tag
from jobs._common import read_rows


def generate_recommendations(entity: str, horizon: int) -> dict:
    rows = [r for r in read_rows("ai_observations") if r.get("entity_name") == entity]
    forecast = build_forecast(entity=entity, horizon=horizon)
    top_narratives = Counter(
        normalize_narrative_tag(str(row.get("narrative_tag") or ""), text=str(row.get("content", "")))
        for row in rows
    ).most_common(5)
    sentiment_avg = _avg([float(r.get("sentiment_score", 0) or 0) for r in rows])
    mentions_count = len(rows)

    predicted_mentions = (
        forecast["forecast"][-1]["predicted_mentions"] if forecast["forecast"] else 0
    )
    current_mentions = forecast["baseline"][-1]["mentions"] if forecast["baseline"] else 0

    recommendations = []
    if predicted_mentions < current_mentions:
        recommendations.append(
            _rec(
                "optimization",
                "high",
                "Riesgo de caída de visibilidad",
                "La proyección indica menor volumen de menciones. Incrementar cadencia de mensajes y presencia en canales de alto alcance.",
                "Diseñar sprint de contenidos de respuesta rápida",
                "high",
                "3-5 días",
                0.78,
            )
        )
    else:
        recommendations.append(
            _rec(
                "insight",
                "medium",
                "Momentum favorable en menciones",
                "La tendencia proyectada sostiene o mejora el volumen. Conviene amplificar narrativas de mejor desempeño.",
                "Escalar distribución de mensajes con mejor tracción",
                "medium",
                "2-3 días",
                0.74,
            )
        )

    if sentiment_avg < -0.1:
        recommendations.append(
            _rec(
                "content",
                "high",
                "Sentimiento negativo persistente",
                "El sentimiento promedio es negativo. Priorizar piezas de contraste narrativo y voceros de mayor credibilidad.",
                "Activar plan de corrección narrativa",
                "high",
                "5-7 días",
                0.82,
            )
        )
    elif sentiment_avg > 0.2:
        recommendations.append(
            _rec(
                "feature",
                "medium",
                "Ventana de reputación positiva",
                "Hay clima favorable. Aprovechar para consolidar temas con alta aceptación y reforzar presencia en motores IA.",
                "Publicar contenidos de consolidación",
                "medium",
                "2-4 días",
                0.7,
            )
        )

    if top_narratives:
        dominant_tag, dominant_count = top_narratives[0]
        recommendations.append(
            _rec(
                "ai-action",
                "medium",
                f"Narrativa dominante: {dominant_tag}",
                f"La narrativa {dominant_tag} concentra {dominant_count} menciones. Conviene decidir si se amplifica o se corrige según objetivo político.",
                "Definir estrategia por narrativa dominante",
                "medium",
                "1-2 días",
                0.69,
            )
        )

    if mentions_count < 500:
        recommendations.append(
            _rec(
                "insight",
                "critical",
                "Muestra insuficiente para decisiones críticas",
                "No se alcanza el umbral mínimo de 500 observaciones. Las recomendaciones deben tomarse como exploratorias.",
                "Aumentar frecuencia y cobertura de ingesta",
                "high",
                "24-48 horas",
                0.95,
            )
        )

    recommendations = sorted(recommendations, key=lambda x: _priority_order(x["priority"]))
    return {
        "entity_name": entity,
        "horizon_days": forecast["horizon_days"],
        "recommendations": recommendations,
        "signals": {
            "sample_size": mentions_count,
            "avg_sentiment": round(sentiment_avg, 4),
            "top_narratives": [{"tag": tag, "count": count} for tag, count in top_narratives],
            "forecast_confidence": forecast["metrics"]["confidence"],
        },
    }


def generate_query_recommendations(query_run_id: str, horizon: int) -> dict:
    rows = [
        r
        for r in read_rows("query_mentions")
        if str(r.get("query_run_id")) == query_run_id
    ]
    forecast = build_query_forecast(query_run_id=query_run_id, horizon=horizon)
    top_narratives = Counter(
        normalize_narrative_tag(str(row.get("narrative_tag") or ""), text=str(row.get("content", "")))
        for row in rows
    ).most_common(5)
    sentiment_avg = _avg([float(r.get("sentiment_score", 0) or 0) for r in rows])
    mentions_count = len(rows)
    coverage = Counter(str(row.get("source") or "other_relevant") for row in rows)

    recommendations = []
    signal_trend = _signal_trend(forecast)
    evidence_base = {
        "source_count": len(coverage),
        "narrative_count": len(top_narratives),
        "signal_trend": signal_trend,
    }

    if sentiment_avg < -0.1:
        recommendations.append(
            _rec(
                "optimization",
                "high",
                "Riesgo reputacional en conversación pública",
                "El sentimiento agregado del tema está en zona negativa. Conviene activar piezas de mitigación y contraste narrativo.",
                "Lanzar plan de mitigación narrativa",
                "high",
                "3-5 días",
                0.79,
                evidence=evidence_base,
            )
        )
    if coverage.get("ai", 0) < max(20, int(mentions_count * 0.4)):
        recommendations.append(
            _rec(
                "insight",
                "medium",
                "Cobertura IA menor a la esperada",
                "La muestra tiene baja densidad en motores IA para este tema. Aumentar consultas en fuentes AI para robustez del diagnóstico.",
                "Incrementar barrido en motores IA",
                "medium",
                "24-48 horas",
                0.74,
                evidence=evidence_base,
            )
        )
    if top_narratives:
        tag, count = top_narratives[0]
        recommendations.append(
            _rec(
                "ai-action",
                "medium",
                f"Narrativa principal detectada: {tag}",
                f"La narrativa {tag} domina con {count} menciones. Definir estrategia de amplificación o respuesta según objetivo.",
                "Diseñar acción táctica por narrativa",
                "medium",
                "1-2 días",
                0.68,
                evidence=evidence_base,
            )
        )

    if forecast.get("narrative_shift_risk") in {"high", "medium"}:
        recommendations.append(
            _rec(
                "optimization",
                "high" if forecast.get("narrative_shift_risk") == "high" else "medium",
                "Riesgo de cambio de narrativa dominante",
                "La concentración entre narrativas es inestable y puede cambiar rápido el marco de conversación.",
                "Preparar mensajes de contención para escenarios alternativos",
                "high",
                "24-72 horas",
                0.72,
                evidence=evidence_base,
            )
        )

    if not recommendations:
        recommendations.append(
            _rec(
                "insight",
                "low",
                "Tema estable sin alertas críticas",
                "No se detectan desvíos relevantes en las señales principales. Continuar monitoreo y revisión periódica.",
                "Mantener monitoreo continuo",
                "low",
                "semanal",
                0.62,
                evidence=evidence_base,
            )
        )

    return {
        "query_run_id": query_run_id,
        "horizon_days": forecast["horizon_days"],
        "recommendations": sorted(recommendations, key=lambda x: _priority_order(x["priority"])),
        "signals": {
            "sample_size": mentions_count,
            "avg_sentiment": round(sentiment_avg, 4),
            "coverage_by_source": dict(coverage),
            "top_narratives": [{"tag": tag, "count": count} for tag, count in top_narratives],
            "forecast_confidence": forecast["metrics"]["confidence"],
        },
    }


def _rec(
    rec_type: str,
    priority: str,
    title: str,
    description: str,
    action_text: str,
    expected_impact: str,
    time_to_implement: str,
    confidence: float,
    evidence: dict | None = None,
) -> dict:
    payload = {
        "type": rec_type,
        "priority": priority,
        "title": title,
        "description": description,
        "actionText": action_text,
        "expectedImpact": expected_impact,
        "timeToImplement": time_to_implement,
        "confidence": confidence,
    }
    if evidence:
        payload["evidence"] = evidence
    return payload


def _priority_order(priority: str) -> int:
    ordered = {"critical": 0, "high": 1, "medium": 2, "low": 3}
    return ordered.get(priority, 4)


def _avg(values: list[float]) -> float:
    if not values:
        return 0.0
    return sum(values) / len(values)


def _signal_trend(forecast: dict) -> str:
    points = forecast.get("forecast", [])
    if len(points) < 2:
        return "flat"
    first = points[0].get("predicted_mentions", 0)
    last = points[-1].get("predicted_mentions", 0)
    if last > first:
        return "up"
    if last < first:
        return "down"
    return "flat"

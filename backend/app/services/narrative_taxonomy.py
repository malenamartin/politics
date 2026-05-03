from __future__ import annotations

import re
from typing import Iterable

VALID_NARRATIVE_TAGS = {
    "governance",
    "economy",
    "reputation",
    "conflict",
    "policy",
    "risk",
    "opportunity",
    "media",
    "security",
    "social_impact",
    "electoral",
    "other_relevant",
}

_SYNONYMS = {
    "political_figure": "electoral",
    "political_analysis": "governance",
    "economic_policy": "economy",
    "economic_growth": "economy",
    "economic_challenges": "risk",
    "public_perception": "reputation",
    "media_mention": "media",
    "media_war": "conflict",
    "corruption": "risk",
    "market_analysis": "economy",
    "feature": "opportunity",
    "unknown": "other_relevant",
    "no_entity": "other_relevant",
}

_KEYWORD_MAP: list[tuple[str, str]] = [
    ("inflacion", "economy"),
    ("econom", "economy"),
    ("mercado", "economy"),
    ("deuda", "economy"),
    ("riesgo", "risk"),
    ("crisis", "risk"),
    ("corrup", "risk"),
    ("escandal", "risk"),
    ("conflic", "conflict"),
    ("ataque", "conflict"),
    ("debate", "conflict"),
    ("voto", "electoral"),
    ("encuesta", "electoral"),
    ("eleccion", "electoral"),
    ("gestion", "governance"),
    ("gobierno", "governance"),
    ("politic", "governance"),
    ("seguridad", "security"),
    ("delito", "security"),
    ("social", "social_impact"),
    ("educacion", "social_impact"),
    ("salud", "social_impact"),
    ("medio", "media"),
    ("prensa", "media"),
    ("reput", "reputation"),
    ("imagen", "reputation"),
    ("oportunidad", "opportunity"),
    ("crecimiento", "opportunity"),
]


def normalize_narrative_tag(raw_tag: str | None, *, text: str = "") -> str:
    candidate = _slugify(raw_tag or "")
    if candidate in _SYNONYMS:
        candidate = _SYNONYMS[candidate]
    if candidate in VALID_NARRATIVE_TAGS:
        return candidate
    inferred = infer_narrative_from_text(text)
    return inferred


def infer_narrative_from_text(text: str) -> str:
    lowered = _slugify(text)
    for key, tag in _KEYWORD_MAP:
        if key in lowered:
            return tag
    return "other_relevant"


def normalize_narrative_list(values: Iterable[str]) -> list[str]:
    return [normalize_narrative_tag(value) for value in values]


def _slugify(value: str) -> str:
    cleaned = re.sub(r"[^a-zA-Z0-9_\\s]", " ", value.strip().lower())
    return re.sub(r"\\s+", "_", cleaned).strip("_")

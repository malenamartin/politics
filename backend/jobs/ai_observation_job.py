from __future__ import annotations

import datetime as dt

from app.config import get_settings
from app.services.ai_observation import AIObservationService
from app.services.scoring import ScoringService
from jobs._common import upsert_rows


def run() -> int:
    settings = get_settings()
    observer = AIObservationService()
    scorer = ScoringService()

    observations = observer.collect(entities=settings.ai_entities[:5], engines=settings.ai_engines)
    rows = []
    for obs in observations:
        scored = scorer.score_text(entity_name=obs.entity_name, text=obs.response_excerpt)
        rows.append(
            {
                "engine": obs.engine,
                "entity_name": obs.entity_name,
                "prompt_template": obs.prompt_template,
                "response_excerpt": obs.response_excerpt,
                "observed_at": obs.observed_at,
                "is_mentioned": scored["is_mentioned"],
                "sentiment_label": scored["sentiment_label"],
                "sentiment_score": scored["sentiment_score"],
                "narrative_tag": scored["narrative_tag"],
                "created_at": dt.datetime.now(dt.timezone.utc).isoformat(),
            }
        )

    upsert_rows("ai_observations", rows)
    print(
        f"ai_observation_job: stored={len(rows)} target_min={settings.min_observations_per_run}"
    )
    return len(rows)


if __name__ == "__main__":
    run()

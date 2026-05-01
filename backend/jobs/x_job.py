from __future__ import annotations

from app.config import get_settings
from app.services.ingestion_x import XIngestionService
from app.services.scoring import ScoringService
from jobs._common import upsert_rows


def run() -> int:
    settings = get_settings()
    if not settings.x_enabled:
        print("x_job: skipped because X_ENABLED=false")
        return 0

    ingestor = XIngestionService()
    scorer = ScoringService()

    mentions = ingestor.collect(settings.ai_entities[:5], per_entity_limit=30)
    rows = []
    for mention in mentions:
        scored = scorer.score_text(entity_name=mention.entity_name, text=mention.content)
        rows.append(
            {
                "entity_name": mention.entity_name,
                "source": mention.source,
                "content": mention.content,
                "sentiment_label": scored["sentiment_label"],
                "sentiment_score": scored["sentiment_score"],
                "published_at": mention.published_at,
                "url": mention.url,
            }
        )

    upsert_rows("mentions", rows)
    print(f"x_job: stored={len(rows)}")
    return len(rows)


if __name__ == "__main__":
    run()

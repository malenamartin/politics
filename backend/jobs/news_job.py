from __future__ import annotations

from app.config import get_settings
from app.services.ingestion_news import NewsIngestionService
from app.services.scoring import ScoringService
from jobs._common import upsert_rows


def run() -> int:
    settings = get_settings()
    ingestor = NewsIngestionService()
    scorer = ScoringService()

    mentions = ingestor.collect(settings.ai_entities[:5])
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
    print(f"news_job: stored={len(rows)}")
    return len(rows)


if __name__ == "__main__":
    run()

from __future__ import annotations

import datetime as dt
from dataclasses import dataclass
from typing import Iterable, List

from newsapi import NewsApiClient

from app.config import get_settings


@dataclass
class NewsMention:
    entity_name: str
    source: str
    content: str
    published_at: str
    url: str


class NewsIngestionService:
    def __init__(self) -> None:
        settings = get_settings()
        if not settings.newsapi_key:
            raise RuntimeError("Missing NEWSAPI_KEY.")
        self._client = NewsApiClient(api_key=settings.newsapi_key)

    def collect(self, entities: Iterable[str]) -> List[NewsMention]:
        mentions: List[NewsMention] = []
        for entity in entities:
            data = self._client.get_everything(
                q=f'"{entity}"',
                language="es",
                sort_by="publishedAt",
                page_size=25,
            )
            for article in data.get("articles", []):
                text = " ".join(
                    filter(
                        None,
                        [
                            article.get("title", ""),
                            article.get("description", ""),
                            article.get("content", ""),
                        ],
                    )
                ).strip()
                if not text:
                    continue
                mentions.append(
                    NewsMention(
                        entity_name=entity,
                        source="news",
                        content=text[:3000],
                        published_at=article.get("publishedAt")
                        or dt.datetime.now(dt.timezone.utc).isoformat(),
                        url=article.get("url", ""),
                    )
                )
        return mentions

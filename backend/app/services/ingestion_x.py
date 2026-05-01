from __future__ import annotations

import datetime as dt
from dataclasses import dataclass
from typing import Iterable, List

import snscrape.modules.twitter as sntwitter


@dataclass
class XMention:
    entity_name: str
    source: str
    content: str
    published_at: str
    url: str


class XIngestionService:
    def collect(self, entities: Iterable[str], *, per_entity_limit: int = 30) -> List[XMention]:
        mentions: List[XMention] = []
        for entity in entities:
            query = f'"{entity}" lang:es'
            scraper = sntwitter.TwitterSearchScraper(query)
            for i, tweet in enumerate(scraper.get_items()):
                if i >= per_entity_limit:
                    break
                mentions.append(
                    XMention(
                        entity_name=entity,
                        source="x",
                        content=tweet.rawContent[:3000],
                        published_at=tweet.date.isoformat()
                        if tweet.date
                        else dt.datetime.now(dt.timezone.utc).isoformat(),
                        url=tweet.url,
                    )
                )
        return mentions

from __future__ import annotations

import datetime as dt
import re
from dataclasses import dataclass
from typing import List

import httpx


@dataclass
class WebMention:
    source: str
    content: str
    published_at: str
    url: str


class WebIngestionService:
    def collect(self, topic: str, limit: int = 30) -> List[WebMention]:
        query = topic.replace(" ", "+")
        search_url = f"https://duckduckgo.com/html/?q={query}"
        with httpx.Client(timeout=20.0, follow_redirects=True) as client:
            response = client.get(search_url, headers={"User-Agent": "Mozilla/5.0"})
            response.raise_for_status()
            html = response.text

        links = []
        for match in re.finditer(r'href="(https?://[^"]+)"', html):
            link = match.group(1)
            if "duckduckgo.com" in link:
                continue
            if link not in links:
                links.append(link)
            if len(links) >= max(1, min(limit, 80)):
                break

        now = dt.datetime.now(dt.timezone.utc).isoformat()
        mentions: List[WebMention] = []
        for link in links:
            mentions.append(
                WebMention(
                    source="web",
                    content=f"Resultado web relacionado con: {topic}",
                    published_at=now,
                    url=link,
                )
            )
        return mentions

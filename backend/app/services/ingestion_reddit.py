from __future__ import annotations

import datetime as dt
from dataclasses import dataclass
from typing import List

import httpx


@dataclass
class RedditMention:
    source: str
    content: str
    published_at: str
    url: str


class RedditIngestionService:
    def collect(self, topic: str, limit: int = 50) -> List[RedditMention]:
        endpoint = "https://www.reddit.com/search.json"
        headers = {"User-Agent": "monitoreo-politico/1.0"}
        params = {"q": topic, "sort": "new", "limit": max(1, min(limit, 100))}
        with httpx.Client(timeout=20.0, follow_redirects=True) as client:
            response = client.get(endpoint, params=params, headers=headers)
            response.raise_for_status()
            payload = response.json()

        mentions: List[RedditMention] = []
        for item in payload.get("data", {}).get("children", []):
            data = item.get("data", {})
            title = data.get("title", "")
            text = data.get("selftext", "")
            content = f"{title}. {text}".strip()[:3000]
            if not content:
                continue
            created_ts = data.get("created_utc")
            published_at = (
                dt.datetime.fromtimestamp(created_ts, tz=dt.timezone.utc).isoformat()
                if created_ts
                else dt.datetime.now(dt.timezone.utc).isoformat()
            )
            permalink = data.get("permalink", "")
            mentions.append(
                RedditMention(
                    source="reddit",
                    content=content,
                    published_at=published_at,
                    url=f"https://www.reddit.com{permalink}" if permalink else "",
                )
            )
        return mentions

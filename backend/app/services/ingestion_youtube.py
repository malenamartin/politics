from __future__ import annotations

import datetime as dt
import re
from dataclasses import dataclass
from typing import List

import httpx


@dataclass
class YouTubeMention:
    source: str
    content: str
    published_at: str
    url: str


class YouTubeIngestionService:
    def collect(self, topic: str, limit: int = 20) -> List[YouTubeMention]:
        query = topic.replace(" ", "+")
        url = f"https://www.youtube.com/results?search_query={query}"
        with httpx.Client(timeout=20.0, follow_redirects=True) as client:
            response = client.get(url, headers={"User-Agent": "Mozilla/5.0"})
            response.raise_for_status()
            html = response.text

        video_ids = []
        for match in re.finditer(r"watch\?v=([A-Za-z0-9_-]{11})", html):
            video_id = match.group(1)
            if video_id not in video_ids:
                video_ids.append(video_id)
            if len(video_ids) >= max(1, min(limit, 50)):
                break

        now = dt.datetime.now(dt.timezone.utc).isoformat()
        mentions: List[YouTubeMention] = []
        for video_id in video_ids:
            mentions.append(
                YouTubeMention(
                    source="youtube",
                    content=f"Resultado de YouTube relacionado con: {topic}",
                    published_at=now,
                    url=f"https://www.youtube.com/watch?v={video_id}",
                )
            )
        return mentions

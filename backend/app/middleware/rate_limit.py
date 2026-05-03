from __future__ import annotations

import time
from collections import defaultdict, deque
from typing import Deque, Dict

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from app.config import get_settings


class PublicRateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app) -> None:  # type: ignore[no-untyped-def]
        super().__init__(app)
        self._requests: Dict[str, Deque[float]] = defaultdict(deque)

    async def dispatch(self, request: Request, call_next):  # type: ignore[no-untyped-def]
        settings = get_settings()
        user_tier = (request.headers.get("x-user-tier") or "").lower()
        is_pro = user_tier == "pro" or (
            settings.pro_api_key and request.headers.get("x-pro-key") == settings.pro_api_key
        )
        if is_pro:
            return await call_next(request)

        limit = max(1, settings.public_rate_limit_per_minute)
        now = time.time()
        ip = request.client.host if request.client else "unknown"
        bucket = self._requests[ip]
        while bucket and now - bucket[0] > 60:
            bucket.popleft()
        if len(bucket) >= limit:
            return JSONResponse(
                status_code=429,
                content={
                    "detail": "Rate limit exceeded for public access.",
                    "limit_per_minute": limit,
                },
            )

        bucket.append(now)
        return await call_next(request)

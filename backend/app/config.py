from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache
from typing import List


def _split_csv(value: str) -> List[str]:
    return [item.strip() for item in value.split(",") if item.strip()]


@dataclass(frozen=True)
class Settings:
    app_env: str
    supabase_url: str
    supabase_service_role_key: str
    ai_entities: List[str]
    ai_engines: List[str]
    ai_capture_mode: str
    openai_api_key: str
    anthropic_api_key: str
    newsapi_key: str
    x_enabled: bool


@lru_cache
def get_settings() -> Settings:
    return Settings(
        app_env=os.getenv("APP_ENV", "development"),
        supabase_url=os.getenv("SUPABASE_URL", ""),
        supabase_service_role_key=os.getenv("SUPABASE_SERVICE_ROLE_KEY", ""),
        ai_entities=_split_csv(os.getenv("AI_ENTITIES", "Javier Milei,Axel Kicillof")),
        ai_engines=_split_csv(
            os.getenv("AI_ENGINES", "chatgpt,gemini,perplexity,claude,copilot")
        ),
        ai_capture_mode=os.getenv("AI_CAPTURE_MODE", "hybrid"),
        openai_api_key=os.getenv("OPENAI_API_KEY", ""),
        anthropic_api_key=os.getenv("ANTHROPIC_API_KEY", ""),
        newsapi_key=os.getenv("NEWSAPI_KEY", ""),
        x_enabled=os.getenv("X_ENABLED", "true").lower() == "true",
    )

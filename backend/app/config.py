from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import List

from dotenv import load_dotenv

ROOT_ENV_PATH = Path(__file__).resolve().parents[1] / ".env"
load_dotenv(dotenv_path=ROOT_ENV_PATH, override=True)


def _split_csv(value: str) -> List[str]:
    return [item.strip() for item in value.split(",") if item.strip()]


@dataclass(frozen=True)
class Settings:
    app_env: str
    local_storage: bool
    local_data_dir: str
    pro_api_key: str
    public_rate_limit_per_minute: int
    minimum_significant_sample: int
    supabase_url: str
    supabase_service_role_key: str
    ai_entities: List[str]
    ai_engines: List[str]
    ai_capture_mode: str
    min_observations_per_run: int
    max_observation_cycles: int
    source_timeout_seconds: int
    max_items_per_source: int
    query_budget_seconds: int
    max_llm_scoring_items: int
    openai_api_key: str
    anthropic_api_key: str
    newsapi_key: str
    x_enabled: bool
    cors_origins: List[str]


@lru_cache
def get_settings() -> Settings:
    return Settings(
        app_env=os.getenv("APP_ENV", "development"),
        local_storage=os.getenv("LOCAL_STORAGE", "false").lower() == "true",
        local_data_dir=os.getenv("LOCAL_DATA_DIR", "data"),
        pro_api_key=os.getenv("PRO_API_KEY", ""),
        public_rate_limit_per_minute=int(os.getenv("PUBLIC_RATE_LIMIT_PER_MINUTE", "90")),
        minimum_significant_sample=int(os.getenv("MINIMUM_SIGNIFICANT_SAMPLE", "500")),
        supabase_url=os.getenv("SUPABASE_URL", ""),
        supabase_service_role_key=os.getenv("SUPABASE_SERVICE_ROLE_KEY", ""),
        ai_entities=_split_csv(os.getenv("AI_ENTITIES", "Javier Milei,Axel Kicillof")),
        ai_engines=_split_csv(
            os.getenv("AI_ENGINES", "chatgpt,gemini,perplexity,claude,copilot")
        ),
        ai_capture_mode=os.getenv("AI_CAPTURE_MODE", "hybrid"),
        min_observations_per_run=int(os.getenv("MIN_OBSERVATIONS_PER_RUN", "500")),
        max_observation_cycles=int(os.getenv("MAX_OBSERVATION_CYCLES", "20")),
        source_timeout_seconds=int(os.getenv("SOURCE_TIMEOUT_SECONDS", "20")),
        max_items_per_source=int(os.getenv("MAX_ITEMS_PER_SOURCE", "80")),
        query_budget_seconds=int(os.getenv("QUERY_BUDGET_SECONDS", "1200")),
        max_llm_scoring_items=int(os.getenv("MAX_LLM_SCORING_ITEMS", "80")),
        openai_api_key=os.getenv("OPENAI_API_KEY", ""),
        anthropic_api_key=os.getenv("ANTHROPIC_API_KEY", ""),
        newsapi_key=os.getenv("NEWSAPI_KEY", ""),
        x_enabled=os.getenv("X_ENABLED", "true").lower() == "true",
        cors_origins=_split_csv(
            os.getenv(
                "CORS_ORIGINS",
                "http://localhost:3000,http://127.0.0.1:3000",
            )
        ),
    )

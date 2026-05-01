from __future__ import annotations

import datetime as dt
import os
import subprocess
from dataclasses import dataclass
from typing import Iterable, List

from anthropic import Anthropic
from openai import OpenAI

from app.config import get_settings


@dataclass
class Observation:
    engine: str
    entity_name: str
    prompt_template: str
    response_excerpt: str
    observed_at: str


BASE_PROMPTS = [
    "Resume la situación actual de {entity} en la política argentina.",
    "¿Cuáles son los principales apoyos y críticas hacia {entity} hoy?",
    "Describe el desempeño económico asociado a {entity}.",
    "¿Qué narrativa domina sobre {entity} en la conversación pública?",
    "Compara fortalezas y debilidades de {entity} frente a sus rivales.",
    "¿Cómo percibe la opinión pública a {entity} esta semana?",
]


class AIObservationService:
    def __init__(self) -> None:
        settings = get_settings()
        self._capture_mode = settings.ai_capture_mode
        self._openai = OpenAI(api_key=settings.openai_api_key) if settings.openai_api_key else None
        self._anthropic = (
            Anthropic(api_key=settings.anthropic_api_key) if settings.anthropic_api_key else None
        )

    def collect(self, entities: Iterable[str], engines: Iterable[str]) -> List[Observation]:
        observations: List[Observation] = []
        for engine in engines:
            for entity in entities:
                for template in BASE_PROMPTS:
                    prompt = template.format(entity=entity)
                    response = self._capture(engine=engine, prompt=prompt)
                    if response:
                        observations.append(
                            Observation(
                                engine=engine,
                                entity_name=entity,
                                prompt_template=template,
                                response_excerpt=response[:2000],
                                observed_at=dt.datetime.now(dt.timezone.utc).isoformat(),
                            )
                        )
        return observations

    def _capture(self, *, engine: str, prompt: str) -> str:
        # Hybrid mode: prefer API path when available, fallback to browser automation command.
        if self._capture_mode in {"api", "hybrid"}:
            response = self._capture_via_api(engine=engine, prompt=prompt)
            if response:
                return response
        if self._capture_mode in {"browser", "hybrid"}:
            return self._capture_via_browser(engine=engine, prompt=prompt)
        return ""

    def _capture_via_api(self, *, engine: str, prompt: str) -> str:
        if engine == "chatgpt" and self._openai:
            res = self._openai.chat.completions.create(
                model="gpt-4o-mini",
                temperature=0,
                messages=[{"role": "user", "content": prompt}],
            )
            return res.choices[0].message.content or ""

        if engine == "claude" and self._anthropic:
            msg = self._anthropic.messages.create(
                model="claude-3-5-haiku-latest",
                max_tokens=512,
                temperature=0,
                messages=[{"role": "user", "content": prompt}],
            )
            return "".join(
                block.text for block in msg.content if getattr(block, "type", "") == "text"
            )

        # Remaining engines can run through browser automation in hybrid mode.
        return ""

    def _capture_via_browser(self, *, engine: str, prompt: str) -> str:
        # Expected env var format:
        # AI_BROWSER_CAPTURE_CMD='python scripts/capture_engine.py --engine {engine} --prompt "{prompt}"'
        command_template = os.getenv("AI_BROWSER_CAPTURE_CMD", "").strip()
        if not command_template:
            return ""
        command = command_template.format(engine=engine, prompt=prompt.replace('"', '\\"'))
        result = subprocess.run(command, shell=True, capture_output=True, text=True, check=False)
        if result.returncode != 0:
            return ""
        return result.stdout.strip()

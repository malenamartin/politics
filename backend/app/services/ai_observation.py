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
        self._settings = settings
        self._capture_mode = settings.ai_capture_mode
        self._openai = (
            OpenAI(api_key=settings.openai_api_key, timeout=settings.source_timeout_seconds)
            if settings.openai_api_key
            else None
        )
        self._anthropic = (
            Anthropic(api_key=settings.anthropic_api_key, timeout=settings.source_timeout_seconds)
            if settings.anthropic_api_key
            else None
        )

    def collect(self, entities: Iterable[str], engines: Iterable[str]) -> List[Observation]:
        observations: List[Observation] = []
        entities_list = list(entities)
        engines_list = list(engines)
        target = max(1, self._settings.min_observations_per_run)
        max_cycles = max(1, self._settings.max_observation_cycles)
        for cycle in range(max_cycles):
            for engine in engines_list:
                for entity in entities_list:
                    for template in BASE_PROMPTS:
                        if len(observations) >= target:
                            return observations
                        prompt = _variant_prompt(template=template, entity=entity, cycle=cycle)
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

    def collect_for_topic(self, topic: str, engines: Iterable[str]) -> List[Observation]:
        return self.collect(entities=[topic], engines=engines)

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
            try:
                res = self._openai.chat.completions.create(
                    model="gpt-4o-mini",
                    temperature=0,
                    messages=[{"role": "user", "content": prompt}],
                )
                return res.choices[0].message.content or ""
            except Exception:
                return ""

        if engine == "claude" and self._anthropic:
            try:
                msg = self._anthropic.messages.create(
                    model="claude-3-5-haiku-latest",
                    max_tokens=512,
                    temperature=0,
                    messages=[{"role": "user", "content": prompt}],
                )
                return "".join(
                    block.text for block in msg.content if getattr(block, "type", "") == "text"
                )
            except Exception:
                return ""

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


def _variant_prompt(template: str, entity: str, cycle: int) -> str:
    prompt = template.format(entity=entity)
    if cycle == 0:
        return prompt
    variant_suffixes = [
        "Responde de forma breve y concreta.",
        "Incluye factores de contexto económico y social.",
        "Enfoca el análisis en los últimos 30 días.",
        "Diferencia señales fuertes de señales débiles.",
        "Entrega una respuesta orientada a diagnóstico estratégico.",
    ]
    suffix = variant_suffixes[cycle % len(variant_suffixes)]
    return f"{prompt} {suffix}"

from __future__ import annotations

import json
from typing import Dict

from anthropic import Anthropic
from openai import OpenAI

from app.config import get_settings


SYSTEM_PROMPT = """
You classify political text. Return compact JSON only:
{
  "is_mentioned": boolean,
  "sentiment_label": "positive" | "neutral" | "negative",
  "sentiment_score": number,
  "narrative_tag": string
}
Rules:
- sentiment_score must be between -1 and 1.
- narrative_tag must be short snake_case.
- If entity is missing, set is_mentioned=false and sentiment_label=neutral, sentiment_score=0.
""".strip()


class ScoringService:
    def __init__(self) -> None:
        settings = get_settings()
        self._openai = OpenAI(api_key=settings.openai_api_key) if settings.openai_api_key else None
        self._anthropic = (
            Anthropic(api_key=settings.anthropic_api_key) if settings.anthropic_api_key else None
        )

    def score_text(self, *, entity_name: str, text: str) -> Dict[str, object]:
        user_prompt = f"Entity: {entity_name}\nText:\n{text}\nReturn JSON."
        if self._openai:
            try:
                completion = self._openai.chat.completions.create(
                    model="gpt-4o-mini",
                    temperature=0,
                    response_format={"type": "json_object"},
                    messages=[
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": user_prompt},
                    ],
                )
                payload = completion.choices[0].message.content or "{}"
                return self._normalize(json.loads(payload))
            except Exception:
                pass

        if self._anthropic:
            msg = self._anthropic.messages.create(
                model="claude-3-5-haiku-latest",
                max_tokens=256,
                temperature=0,
                system=SYSTEM_PROMPT,
                messages=[{"role": "user", "content": user_prompt}],
            )
            text_output = "".join(
                block.text for block in msg.content if getattr(block, "type", "") == "text"
            )
            return self._normalize(json.loads(text_output))

        raise RuntimeError("No scoring provider available (OPENAI_API_KEY or ANTHROPIC_API_KEY).")

    @staticmethod
    def _normalize(payload: Dict[str, object]) -> Dict[str, object]:
        score = float(payload.get("sentiment_score", 0) or 0)
        score = max(-1.0, min(1.0, score))
        label = str(payload.get("sentiment_label", "neutral")).lower()
        if label not in {"positive", "neutral", "negative"}:
            label = "neutral"

        return {
            "is_mentioned": bool(payload.get("is_mentioned", False)),
            "sentiment_label": label,
            "sentiment_score": score,
            "narrative_tag": str(payload.get("narrative_tag", "unknown")).strip().lower(),
        }

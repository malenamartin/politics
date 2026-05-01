# Backend MVP Monitoreo Politico

Semana 1 implementa:
- Esqueleto FastAPI con healthcheck.
- Jobs de observación AI-first (`ai_observation_job.py`).
- Jobs complementarios (`news_job.py`, `x_job.py`).
- Agregación diaria (`daily_aggregation.py`).

## Setup

1. Crear entorno virtual e instalar dependencias:
   - `python -m venv .venv`
   - `source .venv/bin/activate`
   - `pip install -r requirements.txt`
2. Copiar variables:
   - `cp .env.example .env`
3. Cargar SQL en Supabase:
   - `infra/supabase/schema.sql`
   - `infra/supabase/rls.sql`

## Ejecutar API local

```bash
uvicorn app.main:app --reload
```

## Ejecutar jobs manualmente

```bash
python -m jobs.ai_observation_job
python -m jobs.news_job
python -m jobs.x_job
python -m jobs.daily_aggregation
```

## Nota sobre modo híbrido

- `AI_CAPTURE_MODE=hybrid` intenta API para `chatgpt` y `claude`.
- Para `gemini`, `perplexity` y `copilot`, el job usa `AI_BROWSER_CAPTURE_CMD` si está configurado.

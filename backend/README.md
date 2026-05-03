# Backend MVP Monitoreo Politico

Semana 1 implementa:
- Esqueleto FastAPI con healthcheck.
- Jobs de observación AI-first (`ai_observation_job.py`).
- Jobs complementarios (`news_job.py`, `x_job.py`).
- Agregación diaria (`daily_aggregation.py`).
- Acceso freemium (público + endpoints pro).
- Gate de calidad de muestra (mínimo configurable).
- Predicción 7/14/30 días y recomendaciones accionables.

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
- `MIN_OBSERVATIONS_PER_RUN` define objetivo mínimo por corrida (default 500).
- `MAX_ITEMS_PER_SOURCE` limita costo por fuente en análisis ad-hoc.

## Freemium access

- Endpoints públicos:
  - `GET /api/mentions/recent`
  - `GET /api/stats/ai-mentions`
  - `GET /api/stats/ai-sentiment`
  - `GET /api/stats/share-of-voice`
  - `POST /api/query-runs`
  - `GET /api/query-runs/{id}`
  - `GET /api/query-runs/{id}/results`
- Endpoints pro:
  - `GET /api/pro/forecast?entity=&horizon=7|14|30`
  - `GET /api/pro/recommendations?entity=&horizon=7|14|30`

Autorización pro:
- Header `x-pro-key: <PRO_API_KEY>` o `x-user-tier: pro`.

Rate limit público:
- Configurable por `PUBLIC_RATE_LIMIT_PER_MINUTE`.

## Buscador universal ad-hoc

Consulta profunda por tema/persona:

1. Crear consulta:
   - `POST /api/query-runs`
2. Estado:
   - `GET /api/query-runs/{id}`
3. Resultado consolidado:
   - `GET /api/query-runs/{id}/results`

El pipeline combina fuentes AI, news, X, reddit, youtube y web, luego aplica deduplicación, scoring, umbral adaptativo, forecast y recomendaciones.

## Trabajar sin Supabase (modo local)

Si todavía no configuraste Supabase, podés usar:

- `LOCAL_STORAGE=true`
- `LOCAL_DATA_DIR=data`

Con eso, los jobs guardan en:
- `data/ai_observations.jsonl`
- `data/mentions.jsonl`
- `data/daily_stats.jsonl`

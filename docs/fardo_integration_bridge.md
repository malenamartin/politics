# Fardo Integration Bridge

This document maps reusable pieces from cloned Fardo repositories into this MVP.

## Source repositories

- `heyfardo-backoffice-backend`
- `heyfardo-platform-frontend`

## Auth and access mapping

### Backoffice backend (`NestJS`)

- Auth controller: `src/modules/auth/auth.controller.ts`
  - `POST /auth/login`
  - `POST /auth/reset-password`
  - `GET /auth/me` (guarded by `DualAuthGuard`)
- Analysis controller: `src/modules/analysis/analysis.controller.ts`
  - `GET /analyses/stats`
  - `GET /analyses/top-brands`
  - `GET /analyses/industries`
  - CRUD and lookup endpoints under `/analyses/*`

### Platform frontend (`Next.js`)

- Uses Clerk for auth and user state.
- Routes and flow documented in:
  - `README.md`
  - `docs/Plataforma-FARDO.md`

## Recommendations and analytics mapping

### Reusable recommendation model

From `heyfardo-platform-frontend/lib/analytics/recommendation-engine.ts`:

- `Recommendation` shape
  - `type`: `feature | content | optimization | insight | ai-action`
  - `priority`: `low | medium | high | critical`
  - `expectedImpact`: `low | medium | high`
  - confidence and time-to-implement metadata

This MVP adopts compatible fields for future cross-product interoperability.

### Reusable analytics concepts

From `docs/Plataforma-FARDO.md` and `README.md`:

- Freemium public plus advanced features by user tier.
- Predictive analytics using time series.
- Actionable recommendations tied to measurable signals.
- Multi-LLM metrics and visibility trends.

## Integration contract for this MVP

### What is reused now

- Recommendation taxonomy (`type`, `priority`, impact/confidence semantics).
- Freemium access approach (public basic dashboard + pro advanced endpoints).
- Predictive analytics concept with multi-horizon forecasts.

### What stays local in this repository for now

- Data ingestion jobs and local/Supabase storage.
- Public dashboard endpoints and sample-quality gating.
- Forecast and recommendation runtime implementation.

### Future sync path

When product integration is prioritized, expose this MVP as:

- Shared metrics provider to Fardo API Gateway.
- Shared recommendation payload contract for Fardo dashboards.
- Optional auth alignment (Clerk/JWT) for unified user tier detection.

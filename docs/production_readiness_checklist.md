# Production Readiness Checklist

## Core configuration

- [ ] `SUPABASE_URL` and `SUPABASE_SERVICE_ROLE_KEY` configured in production.
- [ ] `LOCAL_STORAGE=false` in production runtime.
- [ ] `PRO_API_KEY` configured and rotated.
- [ ] `PUBLIC_RATE_LIMIT_PER_MINUTE` tuned by traffic profile.
- [ ] `MINIMUM_SIGNIFICANT_SAMPLE=500` or business-approved threshold.
- [ ] `QUERY_BUDGET_SECONDS` aligned with expected deep-analysis SLA (10-20 min).
- [ ] `MAX_ITEMS_PER_SOURCE` and `SOURCE_TIMEOUT_SECONDS` tuned to cap cost per query.

## Data quality and ingestion

- [ ] `MIN_OBSERVATIONS_PER_RUN` validated for cost and throughput.
- [ ] AI ingestion success rate monitored per engine.
- [ ] Daily aggregation jobs scheduled and verified.
- [ ] Forecast baseline has enough history (recommended >= 21 daily points).
- [ ] Ad-hoc pipeline validates fallback behavior per source (AI, news, x, reddit, youtube, web).
- [ ] Narrative taxonomy is versioned and `unknown` is not emitted in production outputs.

## API and access

- [ ] Public endpoints validated under anonymous traffic.
- [ ] Pro endpoints validated with `x-pro-key`.
- [ ] Rate limiting tested (429 behavior and headers/logs).
- [ ] Error responses return non-sensitive messages.
- [ ] Query run endpoints validated: create, status polling, consolidated results.
- [ ] Query results include `sentiment_map` and scenario forecast metadata.

## Frontend

- [ ] Public dashboard works without pro key.
- [ ] Pro modules unlock and fail gracefully when key is invalid.
- [ ] Sample significance banner correctly reflects API quality metadata.
- [ ] Search UX handles deep-processing states (queued/running/completed/failed).
- [ ] Sentiment map and narrative clusters are understandable without technical context.
- [ ] Scenario forecast card communicates base/bull/bear with narrative risk.

## Observability

- [ ] Request logs enabled and centralized.
- [ ] Job logs include stored count and target minimum.
- [ ] Alerting for ingestion failures and zero-data days.
- [ ] `query_run_id` included in ad-hoc analysis logs for traceability.

## Security and operations

- [ ] Secrets stored in deployment secret manager.
- [ ] CORS restricted to expected domains.
- [ ] Backup/restore process validated for production data store.

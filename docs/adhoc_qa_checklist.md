# AdHoc Search QA Checklist

## API flow

- [ ] `POST /api/query-runs` creates a run with `status=completed` after processing.
- [ ] `GET /api/query-runs/{id}` returns coverage and quality.
- [ ] `GET /api/query-runs/{id}/results` returns summary, forecast and recommendations.

## Data quality

- [ ] Deduplication removes repeated cross-source mentions.
- [ ] Adaptive threshold is present in quality metadata.
- [ ] Confidence band is present and coherent with sample size.
- [ ] `narrative_tag` is normalized and never returns `unknown`.
- [ ] Fallback classification uses `other_relevant` when a narrative is ambiguous.

## Source coverage

- [ ] AI source is present and prioritized.
- [ ] At least one complementary source contributes (news/x/reddit/youtube/web).
- [ ] Pipeline degrades gracefully when a source fails.

## Forecasting and recommendations

- [ ] Forecast returns 7/14/30 horizons.
- [ ] Query forecast includes `scenario_forecast` (`base`, `bull`, `bear`).
- [ ] Query forecast includes `narrative_shift_risk`.
- [ ] Recommendation payload includes priority/type/action.
- [ ] Recommendations are linked to current signals and evidence (`source_count`, `narrative_count`, `signal_trend`).

## Sentiment map

- [ ] `/api/query-runs/{id}/results` includes `sentiment_map`.
- [ ] Sentiment map includes totals, distribution and breakdown by source.
- [ ] Narrative intensity exposes `avg_sentiment`, `volume` and `momentum`.

## Frontend

- [ ] Search input creates runs successfully.
- [ ] Loading and error states are visible.
- [ ] Result sections render: quality, sentiment map, narrative clusters, scenario forecast, recommendations.

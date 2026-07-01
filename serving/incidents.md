# Serving Layer — Production Incident Runbook (Task 14)

Realistic serving-layer incidents with symptoms, root cause, detection,
resolution, and prevention. Detection references the metrics in
[monitoring.md](monitoring.md).

---

## I-01 Slow Dashboard

- **Symptoms**: Operations dashboard takes >10 s to render; users report timeouts.
- **Root cause**: A chart ran a live join across two Gold marts instead of reading a wide serving product.
- **Detection**: `serving_dashboard_render_seconds` p95 breach; slow-query log.
- **Resolution**: Repoint chart to the `serving_wildfire_daily` product; warm Superset cache.
- **Prevention**: Enforce "physical dataset only" rule; ban ad-hoc SQL datasets in review.

---

## I-02 API Timeout

- **Symptoms**: `/api/v1/vessels` returns `504`; latency spikes.
- **Root cause**: Unbounded query (missing `limit`) scanned the full product under load.
- **Detection**: `serving_api_request_duration_seconds` p99 breach; `429`/`5xx` spike.
- **Resolution**: Enforce default `limit=50`, add cursor pagination; scale API workers.
- **Prevention**: Server-side max `limit=500`; load test list endpoints.

---

## I-03 Corrupted Gold Table

- **Symptoms**: Wildfire product rebuild fails; `NULL` `aoi_key` rows appear.
- **Root cause**: A partial Gold Parquet write left half-written files after a Spark job crash.
- **Detection**: dbt test `not_null(aoi_key)` fails; `serving_refresh_status == 0`.
- **Resolution**: Re-run the Gold job (idempotent overwrite); rebuild serving products from clean Gold.
- **Prevention**: Atomic (write-then-swap) Gold publishing; freshness gate before serving refresh.

---

## I-04 Missing KPI

- **Symptoms**: "EMS Corroboration Rate" shows blank on the executive dashboard.
- **Root cause**: A dashboard referenced a mistyped metric name inline instead of the semantic registry.
- **Detection**: `KeyError` from `compute_kpis`; empty-value alert.
- **Resolution**: Reference the registered metric `ems_corroboration_rate`; add the chart back.
- **Prevention**: Semantic layer fails fast on unknown metrics; no inline KPI SQL in BI.

---

## I-05 High API Latency

- **Symptoms**: p95 latency doubles during business hours.
- **Root cause**: Redis response cache disabled after a config change → every request hit the store.
- **Detection**: `serving_cache_hits_total` drops; latency p95 breach.
- **Resolution**: Re-enable response cache; verify TTL and invalidation hook.
- **Prevention**: Alert on cache hit ratio < 70 %; cache config in version control.

---

## I-06 Cache Inconsistency

- **Symptoms**: Dashboard shows yesterday's flood numbers after a refresh.
- **Root cause**: Serving refresh completed but caches were not invalidated.
- **Detection**: Freshness gauge current, but user-reported stale values; cache age high.
- **Resolution**: Flush Superset + API caches; emit invalidation event on refresh.
- **Prevention**: Refresh job publishes a cache-invalidation event consumers subscribe to.

---

## I-07 Unauthorized Access Attempt

- **Symptoms**: `ops_eo` user tries to open the maritime (sensitive) dataset.
- **Root cause**: Direct dashboard URL access without dataset permission.
- **Detection**: Audit log `result=deny`; denied-access alert.
- **Resolution**: Access correctly blocked by RBAC; confirm row-level security; review the request.
- **Prevention**: Deny-by-default RBAC, row-level security, periodic access review.

---

## I-08 Broken Materialized View

- **Symptoms**: Executive rollup empty; `mv_kpi_platform_daily` build errors.
- **Root cause**: An upstream product renamed a column, breaking the aggregate SQL.
- **Detection**: dbt build failure on the `marts_agg` model; `serving_refresh_status == 0`.
- **Resolution**: Fix the aggregate SQL/contract; rebuild; add a schema contract test.
- **Prevention**: dbt column contracts on serving products; CI runs `dbt build` on change.

---

## I-09 Expired API Token

- **Symptoms**: Partner integration suddenly gets `401` on all calls.
- **Root cause**: Short-lived token expired and the client did not refresh.
- **Detection**: `serving_api_requests_total{status="401"}` spike from one client.
- **Resolution**: Client refreshes the token via the IdP; verify clock skew.
- **Prevention**: Document token lifetime; client-side auto-refresh; `Deprecation`/expiry headers.

---

## I-10 Stale Analytics (Freshness Breach)

- **Symptoms**: `/readyz` returns `503`; dashboards flagged stale.
- **Root cause**: Upstream ingestion delayed → Gold not rebuilt → serving freshness > 24 h.
- **Detection**: `serving_dataset_freshness_seconds > 86400`; stale-dataset alert.
- **Resolution**: Trigger the ingestion→Gold→serving chain; backfill the missing day.
- **Prevention**: End-to-end freshness SLO alerting; upstream lag alerts; readiness gate.

---

## I-11 Semantic Drift Between BI and API

- **Symptoms**: Executive dashboard and API report different "flood day rate".
- **Root cause**: The API reimplemented the rate instead of calling `compute_kpis`.
- **Detection**: Reconciliation check comparing BI vs API KPI values diverges.
- **Resolution**: Route the API through the semantic reducer; remove the duplicate logic.
- **Prevention**: Single-source metrics in `semantic.METRICS`; contract test asserting parity.

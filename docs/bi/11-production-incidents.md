# 11 — Production Incident Scenarios

> Phase 12 · Task 11 — Production Incidents (≥10)

Each incident follows the platform incident format (symptoms, root cause,
resolution, prevention), consistent with
[../../quality/incidents/production-incidents.md](../../quality/incidents/production-incidents.md).

## BI-01 — Dashboard loading slowly
- **Symptoms:** Executive dashboard takes >30 s; users report timeouts.
- **Root cause:** Charts querying wide serving products directly instead of the
  `platform_daily` materialized aggregate; cache cold after redeploy.
- **Resolution:** Repoint exec charts to `platform_daily`; warm cache post-refresh.
- **Prevention:** Standard: exec charts MUST use materialized aggregates; cache
  warm task in the refresh DAG.

## BI-02 — Missing KPIs
- **Symptoms:** A KPI tile shows blank / "No data".
- **Root cause:** Upstream serving product produced 0 rows (e.g. no NDWI ingested →
  `flood_daily` empty), so the metric is `None`.
- **Resolution:** Confirm ingestion; the semantic layer correctly returns `None`
  (not a misleading 0). Add an empty-state message to the tile.
- **Prevention:** Freshness alert on the source product; empty-state UX standard.

## BI-03 — Incorrect metrics
- **Symptoms:** BI number disagrees with the API for the same KPI.
- **Root cause:** Someone added a Superset calculated column re-deriving the KPI.
- **Resolution:** Remove the calculated column; use the certified serving metric.
- **Prevention:** Governance rule "no KPI math in BI"; API-parity test in CI.

## BI-04 — Stale dashboards
- **Symptoms:** Dashboard shows yesterday's data after a refresh ran.
- **Root cause:** Cache warmed **before** the serving refresh completed; TTL long.
- **Resolution:** Invalidate cache; move warm task to fire on refresh success.
- **Prevention:** Order refresh → warm; monitor freshness metric.

## BI-05 — Broken filters
- **Symptoms:** AOI filter returns nothing / errors.
- **Root cause:** Filter bound to a column renamed in the serving product.
- **Resolution:** Update the certified dataset SQL + native filter target.
- **Prevention:** Dataset contract test; filters bind only to certified columns.

## BI-06 — Failed scheduled report
- **Symptoms:** Daily Executive Brief not delivered.
- **Root cause:** Celery worker down / headless renderer OOM on the 16 GB host.
- **Resolution:** Restart worker; cap concurrent report renders; retry.
- **Prevention:** Health-check Celery; stagger report schedules; alert on failure.

## BI-07 — Dataset unavailable
- **Symptoms:** Chart errors "table not found".
- **Root cause:** Serving DuckDB not rebuilt (serving `dbt run` failed) or file
  not mounted.
- **Resolution:** Re-run serving build; verify read-only mount into Superset.
- **Prevention:** Gate BI cache warm on serving build success; mount health-check.

## BI-08 — Unauthorized access
- **Symptoms:** `ops_maritime` user sees EO wildfire data.
- **Root cause:** Dataset granted to the wrong role / missing RLS.
- **Resolution:** Revoke grant; apply maritime RLS; audit access log.
- **Prevention:** Default-deny RBAC; periodic grant review; RLS tests.

## BI-09 — Cache corruption
- **Symptoms:** Charts show impossible values / mixed time ranges.
- **Root cause:** Results cache holds a partial payload after a mid-query restart.
- **Resolution:** Flush Superset results cache; reload.
- **Prevention:** Shorter TTL for volatile datasets; cache key includes dataset
  version.

## BI-10 — Visualization rendering errors
- **Symptoms:** deck.gl map / chart fails to render.
- **Root cause:** Null `geo_key` rows or unsupported geometry from empty EO Silver.
- **Resolution:** Filter null geometry; validate geo columns in the product.
- **Prevention:** Serving test asserts geo completeness; chart handles empty set.

## BI-11 — Sim dashboard mistaken for real data
- **Symptoms:** Stakeholder cites "satellite availability" as a real KPI.
- **Root cause:** Sim label not prominent enough.
- **Resolution:** Enforce ` sim ` title tag + grey ribbon + dashboard note (ADR-09).
- **Prevention:** Design-standards checklist item; review gate before publish.

## BI-12 — Gold Parquet read failure (sim datasets)
- **Symptoms:** `sat_health` / `weather_impact` error on load.
- **Root cause:** MinIO creds/endpoint not injected into the Superset DuckDB
  connection, so `httpfs` `read_parquet('s3://gold/...')` fails.
- **Resolution:** Set `s3_endpoint`/keys on the connection `engine_params`.
- **Prevention:** Import-time env substitution; connection smoke test.

## Incident Governance

All BI incidents are logged in the platform incident register format, tagged
`bi`, with an owner and a prevention action tracked to closure.

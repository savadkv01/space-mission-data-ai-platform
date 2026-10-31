# 05 — Online Serving

The readiness-aware service wraps Feast's online lookup with explicit use,
freshness, and fallback metadata. The only host-published endpoint is bound to
`127.0.0.1`; internal Airflow materialization is disabled until a job token is
configured.

| Endpoint | Purpose |
|---|---|
| `GET /health` | Confirms PostgreSQL availability |
| `GET /readiness` | Lists registered views, statuses, work packages, and permitted uses |
| `POST /features/online` | Readiness-checked Feast online lookup |
| `POST /internal/materialize` | Token-protected sync + incremental/backfill materialization |

Example request:

```json
{
  "feature_refs": ["satellite_health_daily:health_score", "satellite_health_daily:feature_date"],
  "entity_rows": [{"sat_key": "SIM-SAT-001"}]
}
```

The response carries the requested Feast values, readiness scope, per-view
observation age, publication age where available, SLA results, cache status,
and a degraded flag. Climate publication age is based on the serving DuckDB
file's modification time; it is a database-build proxy, not a per-product
watermark. Freshness metadata fields are fetched internally and omitted from
`features` unless explicitly requested. A blocked view is rejected before
querying Postgres. A stale response is never reported as fresh.

## Resilience and freshness

| Control | Default behavior |
|---|---|
| Low-latency path | Postgres online tables, bounded 2-second process-local response cache |
| Database outage | Return a cached response only within its 60-second stale window and mark `stale_fallback` / `degraded`; otherwise HTTP 503 |
| Feature age | Compare `feature_date` with the view's observation-age SLA; climate views also report serving-database publication age |
| View TTL | Feast historical retention contract; not a deletion guarantee in PostgreSQL online store |
| Online concurrency | Single service worker and Postgres; scale only after contention/load tests |
| Security | Localhost host binding; materialization requires constant-time token comparison; no credential values are returned |

The cache is process-local and is not shared across replicas. PostgreSQL remains
the source of truth. No Redis service is added. Operational consumers must
inspect readiness and freshness metadata rather than treating HTTP 200 as
scientific or decision-grade validity.

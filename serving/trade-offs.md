# Serving Layer — Trade-off Analysis (Task 15)

## Live Queries vs Materialized Views

| | Live queries | Materialized views |
| --- | --- | --- |
| Freshness | always current | as of last refresh |
| Latency | variable, join-heavy | fast, pre-computed |
| Cost | recomputed per request | computed once/day |
| Complexity | simple to build | refresh + invalidation logic |

**Decision**: Materialized views/aggregates for dashboards and cross-product KPIs;
data freshness is daily (batch EO), so staleness is acceptable and the latency SLA
is met cheaply on a laptop. Live queries reserved for single-entity API lookups.
(ADR-SV-02)

---

## API-First vs Direct SQL

| | API-first | Direct SQL |
| --- | --- | --- |
| Governance | central auth, audit, rate limit | hard to govern |
| Coupling | consumers isolated from schema | consumers bind to tables |
| Flexibility | fixed endpoints | arbitrary queries |
| External access | safe | unsafe |

**Decision**: API-first for external and application consumers (governed, versioned);
internal analysts get governed **read-only** SQL/BI access to serving datasets only
(never Silver/Gold). Best of both without exposing raw layers.

---

## Wide Tables vs Normalized Serving Models

| | Wide (denormalized) | Normalized |
| --- | --- | --- |
| Read speed | fast, no joins | join cost per query |
| Storage | some duplication | compact |
| Write/refresh | rebuild wide table | update dimensions once |
| Consumer simplicity | high (self-describing rows) | low (must join) |

**Decision**: Wide data products for the serving read path — read performance and
analyst simplicity outweigh modest storage duplication at MVP scale. Normalized
dims are kept upstream in Gold; serving denormalizes them in. (ADR-SV-05)

---

## Cached vs Real-Time Responses

| | Cached | Real-time |
| --- | --- | --- |
| Latency | lowest | store round-trip |
| Freshness | TTL-bounded | current |
| Load | shields the store | full load per request |
| Consistency risk | stale until invalidated | none |

**Decision**: Cache with **event-driven invalidation** — the serving refresh emits
an invalidation event so caches are fresh-after-refresh, capturing cache latency
benefits without the stale-data risk that plagues pure TTL caching (see incident
I-06).

---

## Cross-Cutting: Engine Choice (DuckDB vs distributed)

DuckDB is chosen for the serving engine because the 16 GB laptop target and MVP
data volumes (AOI/day grain) fit comfortably in an in-process columnar engine.
The model SQL is portable to Trino/Spark-SQL for the scale tier without rewrites
(same dbt models), so the trade-off is reversible. (Aligns with data-modeling
ADR-10 tiered storage.)

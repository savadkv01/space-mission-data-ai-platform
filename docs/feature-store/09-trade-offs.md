# 09 — Trade-offs

| Decision | Chosen approach | Alternative | Why / trade-off |
|---|---|---|---|
| Feast vs custom store | Feast | Hand-built metadata, PIT joins, and online protocol | Feast supplies reusable registry, feature definitions, materialization, and PIT semantics; adds runtime/dependency complexity that tests must constrain. |
| Offline + online backend | Existing PostgreSQL for both plus SQL registry | DuckDB/Parquet offline and Redis online | One existing service minimizes RAM and operational burden. PostgreSQL is not a large-scale lakehouse; bounded sync/backfill and capacity checks are required. |
| Source path | Phase 13 curated Gold metadata and Phase 13b 11b serving products copied to source tables in PostgreSQL | Duplicate source ingestion or read raw Bronze in feature jobs | The copy is a selected Feast-readable snapshot, not an ingestion pipeline. Climate features preserve 11b ownership and require its read-only serving DB. |
| Online backend | PostgreSQL | Redis | Avoid a new container. Postgres online semantics are latest-value lookup and do not provide online TTL deletion. |
| Materialization | Batch + hourly schedule through the existing trigger | Streaming feature computation | Existing products are batch-oriented; hourly refresh meets the post-publication air-quality target without streaming state or new infrastructure. |
| Readiness | Blocked views remain registered but gated | Hide all unready definitions | Keeps candidate contracts and blockers visible without enabling unsafe use. Registration is not eligibility. |
| Cache | Small process-local TTL + explicit stale fallback | No cache or Redis cache | Reduces repeated local reads without adding infrastructure; cache is not shared and must return degraded status during fallback. |
| Feature coverage | Implement candidate contracts for all planned domains; populate only supported demo/catalog slices | Create populated-looking fixtures for every domain | Honest status and source provenance are preferred over synthetic evidence. |

# 06 — Pipelines and Operations

## Data flow

1. `feature_store.entrypoint` initializes idempotent source tables in the
   existing PostgreSQL `feast` schema.
2. The optional sync reads `gold/fact_scene_catalog/*.parquet` from MinIO and
   the four Phase 11b climate products from the read-only serving DuckDB file.
   It checks product grain and quality contracts before writing source rows.
3. Optional demo seeding inserts synthetic satellite-health rows with explicit
   provenance and `demo_only` status.
4. Feast applies entities, feature views, and feature services to the SQL
   registry.
5. Only `demo_only` and explicitly allowed `restricted` views with rows are
   materialized. Blocked feature views remain unavailable.
6. Airflow's hourly DAG calls the token-protected incremental materialization
   endpoint. The same endpoint supports explicit backfill windows.

## Jobs and idempotence

| Job | Source / effect | Retry behavior |
|---|---|---|
| `sync_scene_catalog` | Upsert selected Gold catalog metadata into its Feast source table | Idempotent on `(scene_key, event_timestamp)` |
| `sync_climate_serving_products` | Upsert quality-approved 11b product rows and temporal fields | Idempotent on `(aoi_key, event_timestamp)`; blocked/quality-failed products are reported |
| `seed_satellite_health_demo` | Upsert isolated synthetic test records | Idempotent on `(sat_key, event_timestamp)` |
| `FeatureStore.apply` | Register definitions and online table schemas | Re-runnable; registry is SQL-backed |
| `materialize_eligible` | Read approved source windows and update online values | Feast timestamp semantics prevent older values replacing newer ones |
| Airflow DAG | Trigger incremental materialization hourly | One active run, retry once after two minutes |

Backfill uses `start_date` and `end_date` in UTC. A request with invalid or
reversed bounds fails explicitly. Scheduled jobs do not materialize blocked
views. Source errors and Feast failures are surfaced in container/Airflow logs;
they are not converted into successful empty runs.

## Runtime resource profile

The service is limited to 1 GB RAM and 1 CPU. It reuses existing PostgreSQL and
MinIO containers. Keep Spark and Ollama workloads from peaking concurrently on
the 16-GB laptop. PostgreSQL capacity, online table growth, and backfill
duration remain operational monitoring responsibilities.

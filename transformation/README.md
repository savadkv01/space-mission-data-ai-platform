# Transformation Layer (Phase 9)

Bronze → Silver → Gold lakehouse processing for the Space Mission Data & AI Platform.

The **pure-Python transformation rules** (cleaning, Silver conformance, Gold aggregation, features, geospatial, time-series) are infra-free and fully unit-tested — they run on any laptop with **no Java/Spark/Kafka/MinIO**. Thin **PySpark**, **dbt**, and **Airflow** entrypoints apply the same rules at scale once infrastructure is provisioned.

> Status: design + reference implementation complete. Infrastructure not yet provisioned — `make test` and `make demo` work today; Spark/dbt/Airflow jobs activate when infra lands.

> **Scope boundary.** The **MVP** covers the six Earth-observation / maritime use
> cases on real open data (`obs_fire`, `obs_vessel`, `obs_scene`, `obs_index`,
> `ref_aoi` and their Gold marts). The telemetry / orbit / space-weather
> transforms are a **post-MVP Simulation Track** on synthetic data — a streaming
> and anomaly-ML demonstrator, excluded from MVP (see ADR-09).

## Quick Start (offline, no infra)

```bash
# from transformation/
make install     # installs python-dotenv + pytest only
make test        # 32 offline unit tests

# the demo runs from the repo root so packages resolve without an install:
cd .. && python -m transformation.scripts.run_local_demo --records 60
#   -> Bronze -> Silver -> Gold -> Features, writes transformation/output/
# (or `make demo`, which cds to the repo root for you)
```

## Layout

```text
transformation/
├── config/            settings (env-driven, no secrets)
├── common/            spark session, io, lineage, metrics, logging
├── cleaning/          cleaning_rules.py, validation_framework.py   (Task 7, 12)
├── batch/             bronze_to_silver.py, silver_to_gold.py, aggregation_jobs.py  (Task 3, 4, 9)
├── streaming/         spark_streaming.py  (Task 5)
├── features/          feature_engineering.py  (Task 8)
├── geospatial/        spatial_transform.py  (Task 10)
├── timeseries/        time_series.py  (Task 11)
├── orchestration/     dags/transformation_pipeline_dag.py  (Task 6)
├── dbt/               Gold marts + tests (DuckDB)  (Task 2, 4)
├── scripts/           run_local_demo.py
└── tests/             offline unit tests
```

## Engine Boundaries

| Engine | Owns | Code |
| --- | --- | --- |
| Spark | Bronze→Silver, streaming, features | `batch/`, `streaming/`, `features/` |
| dbt (DuckDB) | Silver→Gold marts + tests | `dbt/` |
| Pure-Python rules | canonical logic reused by both | `cleaning/`, `batch/`, `geospatial/`, `timeseries/` |

## Running With Infrastructure (later)

```bash
make install-spark              # PySpark + dbt-duckdb + Airflow (needs Java)
make silver                     # Spark Bronze->Silver
make dbt-deps && make dbt-run   # Gold marts + tests
make stream                     # structured streaming (needs Kafka)
```

## Documentation

Full design spec: [docs/transformation/](../docs/transformation/README.md) (documents 01–19).

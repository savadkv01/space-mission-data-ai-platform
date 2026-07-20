# Airflow Configuration (Reference)

> Orchestration layer config for the Space Mission Data & AI Platform.
> Phase 7 — Infrastructure Implementation.

Airflow runs as a single `apache/airflow:2.9.2` container in **`standalone`** mode
(webserver + scheduler in one process, `LocalExecutor`) to conserve memory on a
16 GB laptop. Configuration is supplied via environment variables in
[`docker-compose.processing.yml`](../../docker/docker-compose.processing.yml) —
there is intentionally **no mounted `airflow.cfg`**, so the files here are a
**reference** for operators and the basis for later phases.

## Configuration model

| Concern | Mechanism | Value |
| --- | --- | --- |
| Executor | `AIRFLOW__CORE__EXECUTOR` | `LocalExecutor` |
| Metadata DB | `AIRFLOW__DATABASE__SQL_ALCHEMY_CONN` | PostgreSQL, `airflow` schema |
| Example DAGs | `AIRFLOW__CORE__LOAD_EXAMPLES` | `false` |
| Config exposure | `AIRFLOW__WEBSERVER__EXPOSE_CONFIG` | `false` |
| StatsD metrics | `AIRFLOW__METRICS__STATSD_ON` | `false` (Prometheus via exporter later) |

The `airflow` PostgreSQL schema is created by
[`bootstrap.sh`](../../scripts/bootstrap.sh); the container runs
`airflow db migrate` on first start.

## Files

| File | Purpose |
| --- | --- |
| `requirements.txt` | Provider packages DAGs will need in later phases (reference; not auto-installed). |
| `airflow.env.reference` | Canonical list of `AIRFLOW__*` overrides used by the Compose service. |

## DAGs & logs

Logs are persisted on the named volume `airflow-logs`. DAG code is **not** on a
named volume — it is bind-mounted read-only straight from the repo (live edits, no
rebuild needed):

| Repo path | Mounted at | DAGs |
| --- | --- | --- |
| `ingestion/batch/dags/` | `/opt/airflow/dags/ingestion` | Per-source scheduled ingestion DAGs (`ingest_nasa_power`, `ingest_openaq`, …) |
| `transformation/orchestration/dags/` | `/opt/airflow/dags/transformation` | `transformation_medallion_batch` (daily Bronze→Silver→Gold) |
| `pipelines/dags/` | `/opt/airflow/dags/pipelines` | `platform_batch_pipeline` / `platform_streaming_pipeline` / `platform_master_pipeline` (manual-trigger-only orchestration, logs to the `metadata` schema — see OPERATIONS.md §14) |

The whole repo is additionally mounted read-only at `/opt/airflow/repo`
(`PYTHONPATH=/opt/airflow/repo`), so all of `ingestion`, `transformation`, and
`pipelines` import as regular Python packages inside the Airflow container.

## Scaling note

`LocalExecutor` is single-host. To scale beyond the laptop, switch to
`CeleryExecutor` (add Redis broker + worker containers) or `KubernetesExecutor`.
See [13-scalability](../../../docs/infrastructure/17-scalability.md).

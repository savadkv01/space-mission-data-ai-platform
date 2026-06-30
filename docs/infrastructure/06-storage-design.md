# 06 Storage Design

> **Phase 4 - Infrastructure Design (Docker Local Platform)**
> Document 06 of 14

## Purpose

This document defines the storage infrastructure: MinIO bucket layout, PostgreSQL schema design, Iceberg table storage, metadata strategy, volume management, and backup approach.

## Storage Topology

```mermaid
flowchart TB
    subgraph MinIO["MinIO (S3 object storage)"]
        Bronze["bronze/"]
        Silver["silver/"]
        Gold["gold/"]
        Warehouse["warehouse/ (Iceberg data)"]
        MLArt["mlflow-artifacts/"]
        Stage["staging/"]
    end
    subgraph PG["PostgreSQL"]
        MetaS["metadata schema"]
        GoldS["gold schema"]
        IcebergS["iceberg_catalog schema"]
        AppS["airflow / mlflow / superset schemas"]
    end
    Bronze --> Silver --> Gold
    Gold --> GoldS
    Warehouse --> IcebergS
```

## MinIO Bucket Structure

| Bucket | Purpose | Layer |
| --- | --- | --- |
| `bronze` | Raw, immutable ingested objects with source metadata | Bronze |
| `silver` | Validated, standardized, deduplicated data | Silver |
| `gold` | Business-ready aggregates and marts | Gold |
| `warehouse` | Iceberg-managed table data and metadata files | Lakehouse |
| `mlflow-artifacts` | Model artifacts, plots, serialized pipelines | ML |
| `staging` | Transient landing area before promotion to Bronze | Transient |

### Bronze Object Key Convention
```text
bronze/{domain}/{dataset}/ingest_date=YYYY-MM-DD/{source}_{batch_id}.{ext}

examples:
bronze/telemetry/satellite_health/ingest_date=2026-06-28/spacetrack_000123.json
bronze/earth-obs/sentinel2/ingest_date=2026-06-28/copernicus_000456.tif
bronze/space-weather/solar_flux/ingest_date=2026-06-28/noaa_000789.csv
```

### Silver / Gold Convention
```text
silver/{domain}/{table}/             # Iceberg-managed, partitioned by event_date
gold/{domain}/{mart}/                # Iceberg or Parquet, partitioned by reporting period
```

Domains align with Phase 2 datasets: `telemetry`, `earth-obs`, `space-weather`, `launch`.

## PostgreSQL Schema Design

A single PostgreSQL instance hosts multiple logical schemas, isolating concerns while conserving memory (one engine instead of many).

| Schema | Owner service | Contents |
| --- | --- | --- |
| `metadata` | Platform | dataset inventory, provenance, quality scores, freshness, lineage references |
| `gold` | Analytics | curated serving tables for BI/API |
| `iceberg_catalog` | Iceberg REST | Iceberg namespace + table pointers |
| `airflow` | Airflow | DAG run + task metadata |
| `mlflow` | MLflow | experiments, runs, registered models |
| `superset` | Superset | dashboards, charts, datasets metadata |
| `feast` | Feast | feature registry + online store (optional) |

### `metadata` Schema (illustrative tables)

| Table | Key columns | Purpose |
| --- | --- | --- |
| `dataset_inventory` | dataset_id, domain, owner, cadence | Discoverability |
| `source_provenance` | dataset_id, source_url, license | Trust/audit |
| `quality_scores` | dataset_id, layer, score, checked_at | Promotion gating |
| `freshness` | dataset_id, last_ingest_at, sla_minutes | SLA monitoring |
| `lineage_edge` | from_asset, to_asset, transform | Impact analysis |

> Exact DDL is implemented in a later phase; this is the storage layout, not the schema implementation.

## Iceberg Table Storage Layout

- **Catalog**: Iceberg REST catalog (`iceberg-rest`) backed by the `iceberg_catalog` PostgreSQL schema.
- **Data + metadata files**: stored in the `warehouse` MinIO bucket via the S3 API.
- **Namespaces** mirror domains: `telemetry`, `earth_obs`, `space_weather`, `launch`.
- **Partitioning**: Silver tables partition by `event_date`; Gold marts partition by reporting period.
- **Snapshots**: Iceberg retains snapshots for time-travel; expiration policy keeps the last N snapshots to cap storage.

```text
s3://warehouse/telemetry/satellite_health/
├── metadata/            # Iceberg metadata.json, manifests
└── data/event_date=.../ # Parquet data files
```

## Metadata Storage Strategy

| Metadata type | Store | Accessed via |
| --- | --- | --- |
| Table schema/snapshots | Iceberg (PostgreSQL + MinIO) | Iceberg REST catalog |
| Dataset/lineage/quality | PostgreSQL `metadata` schema | FastAPI + Superset |
| Experiment/model | PostgreSQL `mlflow` + MinIO artifacts | MLflow API/UI |
| Orchestration state | PostgreSQL `airflow` | Airflow UI |

## Volume Management

| Named volume | Backing service | Contents | Backup priority |
| --- | --- | --- | --- |
| `postgres-data` | postgres | All relational schemas | **Critical** |
| `minio-data` | minio | All object layers + artifacts | **Critical** |
| `kafka-data` | kafka | Topic logs (transient) | Low |
| `qdrant-data` | qdrant | Vector embeddings | Medium |
| `ollama-models` | ollama | Downloaded model weights | Low (re-pullable) |
| `mlflow` (in MinIO) | mlflow | Artifacts | High |
| `airflow-dags` / `airflow-logs` | airflow | DAGs + logs | Medium |
| `grafana-data` | grafana | Dashboards/config | Medium |
| `prometheus-data` | prometheus | Metrics TSDB | Low |
| `superset-home` | superset | Dashboards/metadata | Medium |
| `jupyter-work` | jupyter | Notebooks | Medium |

## Backup Strategy

| Asset | Method | Cadence |
| --- | --- | --- |
| PostgreSQL | `pg_dump` to `./backups/postgres/` | On-demand + before resets |
| MinIO objects | `mc mirror` to `./backups/minio/` | On-demand |
| Grafana/Superset config | volume tar snapshot | On-demand |
| Vector data (Qdrant) | snapshot API → `./backups/qdrant/` | Before major reindex |

```bash
# Illustrative — implemented in scripts later (run from infrastructure/docker)
docker compose exec -T postgres pg_dump -U $POSTGRES_USER platform > ./backups/postgres/platform.sql
# Buckets via a one-off mc client on the data network (minio server image has no mc):
docker run --rm --network space-data-net \
  -e MC_HOST_local="http://$MINIO_ROOT_USER:$MINIO_ROOT_PASSWORD@minio:9000" \
  -v "$PWD/backups/minio:/backup" minio/mc mirror local/gold /backup/gold
```

- Backups are stored on the host under `infrastructure/backups/` (git-ignored).
- `reset-platform.sh` performs an optional backup before destroying volumes (see [10-deployment-runbook.md](./10-deployment-runbook.md)).
- Transient stores (Kafka logs, Prometheus TSDB, Ollama weights) are excluded from backup as they are reproducible.

## Cross References

- Phase 3 data architecture: [../../architecture/06-data-architecture.md](../../architecture/06-data-architecture.md)
- Failure handling / persistence: [11-failure-handling.md](./11-failure-handling.md)
- Deployment runbook: [10-deployment-runbook.md](./10-deployment-runbook.md)

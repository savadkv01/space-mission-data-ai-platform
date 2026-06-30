# 05 - File-Based Ingestion (MinIO)

> **Phase 8 - Data Ingestion** · Document 05 of 17

## Purpose

Design ingestion of file datasets (CSV telemetry, JSON mission logs, Parquet, Earth-observation products) into MinIO. Implemented in [`ingestion/file/file_loader.py`](../../ingestion/file/file_loader.py).

## Supported Formats

| Format | Example source | Content type |
| --- | --- | --- |
| CSV | FIRMS exports, telemetry dumps | `text/csv` |
| JSON / JSONL | mission logs, API snapshots | `application/json` |
| Parquet | curated datasets | `application/vnd.apache.parquet` |
| Binary | EMS rasters, COGs | `application/octet-stream` |

## MinIO Folder Structure

```
s3://bronze/
  <source>/
    ingest_date=YYYY-MM-DD/
      <batch_id>/
        <original_filename>
```

Example: `s3://bronze/EMS/ingest_date=2026-06-30/EMS-20260630T101500Z-ab12cd34/EMSR700_delineation.json`

## Naming Conventions

| Element | Rule |
| --- | --- |
| `source` | uppercase dataset code (EMS, MISSION_LOGS, …) |
| `ingest_date` | UTC date partition (Hive-style) |
| `batch_id` | `<source>-<UTC timestamp>-<rand8>` |
| filename | original name preserved for traceability |

## Partitioning Strategy

- Primary partition: `ingest_date` (date) — aligns with [docs/data-modeling/12-partitioning.md](../data-modeling/12-partitioning.md).
- Secondary (large EO): `mission` / `region` sub-folders to bound file counts.
- Raw bytes preserved verbatim (schema-on-read).

## Ingestion Triggers

| Trigger | Mechanism |
| --- | --- |
| Manual / CLI | `python -m ingestion.file.file_loader <path> --source EMS` |
| Scheduled sweep | Airflow DAG calls `ingest_path` over a watch directory |
| Event (future) | MinIO bucket notification → webhook |

## Cross References

- [07-landing-zone.md](07-landing-zone.md) · [08-schema-strategy.md](08-schema-strategy.md)

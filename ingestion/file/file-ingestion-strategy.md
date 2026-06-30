# File Ingestion Strategy

Code: [file_loader.py](file_loader.py). Narrative: [docs/ingestion/05-file-ingestion.md](../../docs/ingestion/05-file-ingestion.md).

| Aspect | Strategy |
| --- | --- |
| Formats | CSV, JSON/JSONL, Parquet, binary (content-type set per extension) |
| Preservation | raw bytes landed verbatim (schema-on-read) |
| Naming | `<source>/ingest_date=.../<batch_id>/<original_name>` |
| Triggers | CLI, scheduled Airflow sweep, (future) MinIO bucket notification |
| Partitioning | `ingest_date` primary; `mission`/`region` sub-folders for large EO |

Usage: `python -m ingestion.file.file_loader <path> --source EMS`.

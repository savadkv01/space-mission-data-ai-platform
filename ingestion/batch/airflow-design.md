# Airflow Design (Batch)

Full narrative: [docs/ingestion/03-batch-design.md](../../docs/ingestion/03-batch-design.md).

## Runtime
- Airflow 2.9.2 standalone, LocalExecutor (Phase 7 processing stack).
- DAGs mounted into the `airflow-dags` volume; metadata in Postgres `airflow` schema.

## Pattern
Thin DAGs → shared [ingest_task.py](ingest_task.py) → connector → Bronze. Defaults (retries, backoff) in [dags/_defaults.py](dags/_defaults.py).

See [dag-structure.md](dag-structure.md) and [scheduling-strategy.md](scheduling-strategy.md).

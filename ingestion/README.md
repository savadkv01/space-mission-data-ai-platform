# Ingestion Layer

Phase 8 implementation of the Space Mission Data & AI Platform ingestion layer:
streaming (Kafka), batch (Airflow), API + file connectors, a synthetic data
generation system, ingestion-time data quality, and the Bronze landing zone.

> Open-source only · fits a 16 GB laptop · no secrets in code.

## Layout

```
ingestion/
├── config/        # environment-driven settings
├── common/        # Bronze envelope, HTTP/Kafka/MinIO IO, schema registry
├── simulation/    # synthetic telemetry / orbit / space-weather generators
├── api/           # NASA/NOAA/CelesTrak pull connectors
├── streaming/     # Kafka producers + consumers
├── batch/         # Airflow DAGs + shared ingest task
├── file/          # MinIO file loader
├── quality/       # validation + quarantine
├── scripts/       # create_topics, run_local_demo
└── tests/         # offline unit tests (no infra)
```

Design docs: [docs/ingestion/](../docs/ingestion/) (01–17) and the `*.md` files in each subfolder.

## Setup

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Credentials are inherited from [infrastructure/env/.env](../infrastructure/env/.env).
Copy [.env.example](.env.example) → `.env` only to override host endpoints
(e.g. `KAFKA_BOOTSTRAP=localhost:9092`).

## Run

### Offline (no infrastructure)

```powershell
python -m pytest                              # 14 unit tests
python -m ingestion.scripts.run_local_demo    # end-to-end pipeline in-memory
```

The demo generates telemetry → Bronze envelopes → validation → cleaned/quarantine
and writes samples to `ingestion/output/`.

### With infrastructure (Phase 7 stacks up)

```powershell
# 1. storage + ingestion + processing stacks (see infrastructure/)
# 2. create topics
python -m ingestion.scripts.create_topics
# 3. produce synthetic telemetry
python -m ingestion.streaming.producers.telemetry_producer --max 1000 --rate 50
# 4. land raw telemetry in Bronze (MinIO)
python -m ingestion.streaming.consumers.raw_ingest_consumer
# 5. validate -> cleaned / DLQ
python -m ingestion.streaming.consumers.validation_consumer
```

Batch DAGs in [batch/dags/](batch/dags/) mount into the Airflow `dags` volume.

A `Makefile` wraps these (`make test`, `make demo`, `make topics`, `make produce`, …).

## Status

- ✅ Code implemented and offline-validated (pytest + demo).
- ⏳ Running against live Kafka/MinIO/Airflow is deferred (infra not started).

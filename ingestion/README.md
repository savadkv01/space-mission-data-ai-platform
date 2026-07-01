# Ingestion Layer

Phase 8 implementation of the Space Mission Data & AI Platform ingestion layer:
streaming (Kafka), batch (Airflow), API + file connectors, a synthetic data
generation system, ingestion-time data quality, and the Bronze landing zone.

> Open-source only · fits a 16 GB laptop · no secrets in code.

> **Scope boundary.** Real-data MVP connectors (`api/nasa_firms`, `api/gfw`,
> `api/sentinelhub`, `api/sentinelhub_stats`, `api/earthdata`, `api/landsat`,
> `file/` EMS) power the Earth-observation / maritime use cases. The
> `simulation/` telemetry/orbit/space-weather generators feed the **post-MVP
> Simulation Track** (synthetic data), excluded from MVP — see ADR-09 in
> [docs/data-modeling/17-adr.md](../docs/data-modeling/17-adr.md).

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

### With infrastructure (platform stacks up)

Kafka is **not published to the host** (it advertises only `kafka:9092`), so run these
modules from a container attached to the platform's `space-ops-net` — which reaches both
`kafka:9092` and `minio:9000` by DNS. The step-by-step operator runbook (start a reusable
runner, stream, run API connectors, verify offsets/Bronze, clean up) is in
[OPERATIONS.md §10](../OPERATIONS.md#10-running-the-ingestion-layer).

```powershell
# Start a throwaway runner (repo bind-mounted; reads infrastructure/env/.env)
$REPO = (Resolve-Path ..).Path
docker run -d --name space-ingest-runner --network space-ops-net `
  -v "${REPO}:/work" -w /work `
  -e KAFKA_BOOTSTRAP=kafka:9092 -e MINIO_ENDPOINT=http://minio:9000 `
  python:3.11-slim sleep infinity
docker exec space-ingest-runner pip install -q -r ingestion/requirements.txt

# Then run each stage inside the runner:
docker exec space-ingest-runner python -m ingestion.scripts.create_topics
docker exec space-ingest-runner python -m ingestion.streaming.producers.telemetry_producer --max 300 --rate 200
docker exec space-ingest-runner python -m ingestion.streaming.consumers.raw_ingest_consumer --batch-size 100 --max-batches 3
docker exec space-ingest-runner python -m ingestion.streaming.consumers.validation_consumer --max 300
```

> Consumers have no idle timeout — bound them with `--max-batches`/`--max` so they exit
> once the produced records are drained.

Batch DAGs in [batch/dags/](batch/dags/) are bind-mounted into the Airflow container
(`/opt/airflow/dags/ingestion`) by the **processing** stack and appear in the UI at
`http://localhost:8082`. The custom Airflow image installs the ingestion deps and puts
the repo on `PYTHONPATH`, so each DAG runs its connector in-process and lands Bronze in
MinIO. Unpause/trigger them from the UI — see [OPERATIONS.md §5](../OPERATIONS.md).

A `Makefile` wraps the offline targets (`make test`, `make demo`, `make topics`, `make produce`, …).

## Status

- ✅ Code implemented and offline-validated (pytest + demo).
- ✅ Live-verified against the running platform: synthetic streaming pipeline
  (telemetry → Bronze → cleaned/DLQ) and API connectors → Bronze for NASA POWER,
  NOAA SWPC, CelesTrak, NASA FIRMS, and Global Fishing Watch.
- ⚠️ Sentinel Hub connector is implemented and unit-tested but its OAuth host was
  unreachable (read-timeout) from the test environment — retry from a network with
  egress to `services.sentinel-hub.com`.

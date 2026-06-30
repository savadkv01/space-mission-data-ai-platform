# Infrastructure

> **Phase 4 — Infrastructure Design (Docker Local Platform)**
> Deployable local blueprint for the Space Mission Data & AI Platform.

This directory contains the infrastructure-as-code blueprint produced in Phase 4.
The full design rationale lives in [../docs/infrastructure/](../docs/infrastructure/README.md).

## Layout

```text
infrastructure/
├── docker/                          # Docker Compose (base + 6 stack overrides)
│   ├── docker-compose.yml           # networks, volumes, shared anchors
│   ├── docker-compose.storage.yml   # postgres, minio, iceberg-rest
│   ├── docker-compose.ingestion.yml # kafka (KRaft), kafka-ui
│   ├── docker-compose.processing.yml# spark, airflow, dbt
│   ├── docker-compose.ai.yml        # mlflow, jupyter, qdrant, ollama, open-webui
│   ├── docker-compose.observability.yml # prometheus, grafana, otel
│   └── docker-compose.bi.yml        # superset
├── env/
│   └── .env.example                 # documented environment template (copy to .env)
├── scripts/
│   ├── bootstrap.sh                 # buckets, schemas, migrations (one-time)
│   ├── start-platform.sh            # staged startup by profile
│   ├── stop-platform.sh             # stop, preserve volumes
│   └── reset-platform.sh            # DESTRUCTIVE reset (backs up first)
└── configs/
    ├── kafka/server.properties      # KRaft settings (reference)
    ├── spark/spark-defaults.conf    # S3A + Iceberg wiring
    ├── postgres/init/01-schemas.sql # schema + role bootstrap
    ├── minio/README.md              # bucket + policy strategy
    ├── prometheus/prometheus.yml    # scrape targets
    ├── otel/otel-collector-config.yaml    ├── airflow/                      # executor/db config reference + providers    └── grafana/provisioning/        # datasource + dashboards
```

## Quick Start

```bash
cd infrastructure
cp env/.env.example env/.env      # edit credentials/ports
bash scripts/bootstrap.sh         # create buckets, schemas
bash scripts/start-platform.sh --profile core
```

Profiles: `storage` | `core` | `ai` | `obs` | `all`.
See the [Deployment Runbook](../docs/infrastructure/10-deployment-runbook.md).

## Constraints

- Docker Compose only (no Kubernetes)
- Open-source tools only
- Optimized for a 16 GB RAM laptop (explicit limits + staged heavy workloads)

> These files are an **infrastructure blueprint**. Application code (pipelines,
> DAGs, services) is implemented in later phases; placeholders are marked in the
> Compose files where application containers will be added.

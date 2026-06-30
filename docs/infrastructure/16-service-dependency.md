# 16 — Service Dependency & Startup Strategy

> **Phase 7 — Infrastructure Implementation**
> Startup order, health-gated dependencies, readiness retries, and the
> one-time initialization sequence for the local platform.

This document specifies **Task 8** of Phase 7. It formalizes how the platform
comes up deterministically despite asynchronous container startup, building on
the dependency inventory in [03-service-mapping](./03-service-mapping.md).

---

## 1. Dependency principles

| Principle | Mechanism |
| --- | --- |
| Foundation first | Storage (PostgreSQL, MinIO) is a hard prerequisite for almost everything. |
| Health-gated startup | `depends_on: { condition: service_healthy }` blocks dependents until a healthcheck passes. |
| Idempotent init | `bootstrap.sh` creates schemas/buckets safely on re-run (`IF NOT EXISTS`, `--ignore-existing`). |
| Self-healing | `restart: unless-stopped` (services) / `on-failure:3` (workers) recovers from transient failures. |
| Staged scripting | `start-platform.sh` brings stacks up in waves and waits for health between waves. |

---

## 2. Dependency graph

```mermaid
graph TD
  PG[postgres]:::core
  MINIO[minio]:::core
  ICE[iceberg-rest]
  KAFKA[kafka]
  KUI[kafka-ui]
  SM[spark-master]
  SW[spark-worker]
  AF[airflow]
  ML[mlflow]
  JUP[jupyter]
  QD[qdrant]
  OLL[ollama]
  OWUI[open-webui]
  PROM[prometheus]
  GRAF[grafana]
  OTEL[otel-collector]
  SUP[superset]

  PG --> ICE
  MINIO --> ICE
  PG --> AF
  PG --> ML
  MINIO --> ML
  SM --> SW
  KAFKA --> KUI
  OLL --> OWUI
  PROM --> GRAF
  PG --> SUP

  classDef core fill:#1f6feb,color:#fff,stroke:#0b3d91;
```

Services with **no** hard `depends_on` (kafka, spark-master, qdrant, ollama,
prometheus, otel-collector) can start in parallel within their wave; the scripts
still sequence waves to respect resource pressure on a 16 GB laptop.

---

## 3. Health checks

Every long-running service defines a Docker healthcheck so dependents wait for
*readiness*, not merely *process start*.

| Service | Probe | Interval / Retries |
| --- | --- | --- |
| postgres | `pg_isready -U $USER -d $DB` | 10s / 5 |
| minio | `curl /minio/health/live` | 15s / 5 |
| iceberg-rest | `curl /v1/config` | 20s / 5 |
| kafka | `kafka-broker-api-versions.sh --bootstrap-server localhost:9092` | 20s / 5 |
| spark-master | `curl :8080` | 20s / 5 |
| airflow | `curl /health` | 30s / 5 |
| mlflow | `curl /health` | 30s / 5 |
| qdrant | TCP open on 6333 | 20s / 5 |
| ollama | `curl /api/tags` | 30s / 5 |
| prometheus | `wget /-/healthy` | 20s / 5 |
| grafana | `curl /api/health` | 30s / 5 |
| superset | `curl /health` | 30s / 5 |

`condition: service_healthy` consumers (iceberg-rest, kafka-ui, airflow, mlflow,
spark-worker, open-webui, superset) will not be scheduled until the upstream
healthcheck reports `healthy`.

---

## 4. Startup sequence (per `start-platform.sh`)

```mermaid
sequenceDiagram
  participant Op as Operator
  participant S as start-platform.sh
  participant D as Docker Compose
  Op->>S: --profile core
  S->>D: up storage (postgres, minio, iceberg-rest)
  D-->>S: postgres healthy
  D-->>S: minio healthy
  S->>D: up ingestion (kafka, kafka-ui)
  D-->>S: kafka healthy
  S->>D: up processing (spark, airflow, dbt)
  S-->>Op: docker compose ps (status)
```

Wave ordering by profile:

| Wave | Profile(s) | Services | Gate before next wave |
| --- | --- | --- | --- |
| 1 | storage | postgres, minio, iceberg-rest | postgres + minio healthy |
| 2 | core | kafka, kafka-ui | kafka healthy |
| 3 | core | spark-master, spark-worker, airflow | — |
| (alt) | ai | mlflow, jupyter, qdrant, ollama, open-webui | depends on storage healthy |
| (alt) | obs | prometheus, grafana, otel, superset | depends on storage healthy |

The script's `wait_healthy()` helper polls `docker inspect` until
`State.Health.Status == healthy`, providing an application-level readiness
retry on top of Docker's own probe retries.

---

## 5. One-time initialization sequence (`bootstrap.sh`)

```mermaid
flowchart TD
  A["check .env exists"] --> B["pull + start storage"]
  B --> C["wait postgres & minio healthy"]
  C --> D["create PostgreSQL schemas<br/>metadata, gold, iceberg_catalog,<br/>airflow, mlflow, superset, feast"]
  D --> E["create MinIO buckets<br/>bronze, silver, gold, warehouse,<br/>mlflow-artifacts, staging"]
  E --> F["(optional) ollama pull default model"]
  F --> G["ready: start-platform.sh --profile core"]
```

Idempotency guarantees:

| Step | Idempotent mechanism |
| --- | --- |
| Schemas | `CREATE SCHEMA IF NOT EXISTS` |
| Buckets | `mc mb --ignore-existing` |
| Airflow metadata | `airflow db migrate` (safe to re-run) |
| Superset metadata | `superset db upgrade && superset init` |

---

## 6. Readiness & retry mechanisms (summary)

| Layer | Retry behavior |
| --- | --- |
| Docker healthcheck | per-service `interval` × `retries` before marking unhealthy |
| `depends_on: service_healthy` | dependent stays pending until upstream healthy |
| `start-platform.sh wait_healthy()` | polls every 3s until healthy before next wave |
| Restart policy | `unless-stopped` (services), `on-failure:3` (spark-worker, ollama) |
| Connection-level | clients (airflow→postgres, mlflow→minio) reconnect on transient errors |

---

## Cross references

- [03-service-mapping](./03-service-mapping.md) — full container/port/volume inventory
- [11-failure-handling](./11-failure-handling.md) — restart & recovery policies
- [10-deployment-runbook](./10-deployment-runbook.md) — operator run procedure
- `infrastructure/scripts/start-platform.sh`, `infrastructure/scripts/bootstrap.sh`

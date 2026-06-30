# Phase 4 — Infrastructure Design (Docker Local Platform)

> Enterprise Space Mission Data & AI Platform
> Complete infrastructure blueprint for local Docker deployment on a 16 GB laptop.

## Scope

This phase delivers a **fully deployable local infrastructure blueprint** using Docker Compose only (no Kubernetes), with open-source tooling, optimized for a 16 GB RAM laptop. It is detailed enough that a DevOps engineer can implement the entire platform without architectural clarification.

It does **not** implement application code, pipelines, DAGs, or services — only the infrastructure that hosts them.

## Document Index

| # | Document | Purpose |
| --- | --- | --- |
| 01 | [Overview](./01-overview.md) | Philosophy, Docker-first rationale, resource strategy, service grouping |
| 02 | [Docker System Design](./02-docker-design.md) | Network architecture, container groups, multi-Compose structure |
| 03 | [Service Mapping](./03-service-mapping.md) | Component-to-container inventory, ports, dependencies, volumes |
| 04 | [Resource Management](./04-resource-management.md) | Per-container limits, profile envelopes, staged workloads |
| 05 | [Networking](./05-networking.md) | Networks, exposed ports, gateway, discovery, comms rules |
| 06 | [Storage Design](./06-storage-design.md) | MinIO buckets, PostgreSQL schemas, Iceberg layout, backups |
| 07 | [Observability](./07-observability.md) | Metrics, logging, tracing pipelines and dashboards |
| 08 | [AI Infrastructure](./08-ai-infrastructure.md) | Training, registry, features, vectors, LLM, RAG |
| 09 | [Security](./09-security.md) | Env strategy, secrets, API keys, lightweight RBAC |
| 10 | [Deployment Runbook](./10-deployment-runbook.md) | Startup order, scripts, profiles, access URLs |
| 11 | [Failure Handling](./11-failure-handling.md) | Restart policies, persistence, backup, partial failure |
| 12 | [Trade-offs](./12-trade-offs.md) | Kafka/RabbitMQ, Spark/DuckDB, MinIO, Superset, Ollama, Compose/K8s |
| 13 | [ADR](./13-adr.md) | Seven binding infrastructure decision records |
| 14 | [Glossary](./14-glossary.md) | Infrastructure terminology |
| 15 | [Environment Configuration](./15-environment-configuration.md) | `.env` contract, secrets, dev/full-stack separation, parameterization *(Phase 7)* |
| 16 | [Service Dependency](./16-service-dependency.md) | Startup waves, health gating, retries, init sequence *(Phase 7)* |
| 17 | [Scalability](./17-scalability.md) | Per-service and platform-wide scale-out paths *(Phase 7)* |

## Deliverable Artifacts

| Location | Contents |
| --- | --- |
| `infrastructure/docker/` | Base + 6 stack Compose files (storage, ingestion, processing, ai, observability, bi) |
| `infrastructure/env/.env.example` | Documented environment template |
| `infrastructure/scripts/` | `bootstrap.sh`, `start-platform.sh`, `stop-platform.sh`, `reset-platform.sh` |
| `infrastructure/configs/` | kafka, spark, postgres, minio, prometheus, grafana, otel, airflow configs |

## Stack Summary

| Stack | Services | Compose file |
| --- | --- | --- |
| Storage | PostgreSQL, MinIO, Iceberg REST | `docker-compose.storage.yml` |
| Ingestion | Kafka (KRaft), Kafka UI | `docker-compose.ingestion.yml` |
| Processing | Spark, Airflow, dbt | `docker-compose.processing.yml` |
| AI/ML | MLflow, Jupyter, Feast, Qdrant, Ollama, Open WebUI | `docker-compose.ai.yml` |
| Observability | Prometheus, Grafana, OTel | `docker-compose.observability.yml` |
| BI | Apache Superset | `docker-compose.bi.yml` |

## Acceptance Criteria (met)

- [x] Entire infrastructure is Docker-based
- [x] System is feasible on 16 GB RAM (profile envelopes documented)
- [x] All services mapped to containers
- [x] Full startup strategy defined
- [x] Observability stack included
- [x] AI/ML stack included
- [x] Failure handling defined

## Quick Start

```bash
cd infrastructure
cp env/.env.example env/.env      # then edit credentials/ports
bash scripts/bootstrap.sh
bash scripts/start-platform.sh --profile core
```

See the [Deployment Runbook](./10-deployment-runbook.md) for the full procedure.

## Cross References

- Phase 3 architecture: [../../architecture/README.md](../../architecture/README.md)
- Phase 2 domain research: [../domain-research/README.md](../domain-research/README.md)
- Phase 1 business analysis: [../business/README.md](../business/README.md)

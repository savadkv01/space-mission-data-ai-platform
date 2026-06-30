# 14 Glossary

> **Phase 4 - Infrastructure Design (Docker Local Platform)**
> Document 14 of 14

## Purpose

Definitions of infrastructure terms used across the Phase 4 documents.

## Terms

| Term | Definition |
| --- | --- |
| **Bridge network** | A Docker software network that lets containers on the same host communicate by name. |
| **Bootstrap** | One-time initialization: creating networks, volumes, buckets, schemas, and running migrations. |
| **Compose override** | A supplementary `docker-compose.*.yml` file that extends the base file with stack-specific services. |
| **Container** | An isolated, runnable instance of an image with its own filesystem, network, and resource limits. |
| **dbt** | Data Build Tool; SQL-based transformation framework run as an ephemeral container. |
| **DuckDB** | In-process analytical database used for lightweight, memory-efficient queries. |
| **Edge network (`edge-net`)** | The only network carrying host-published, user-facing traffic. |
| **Ephemeral container** | A short-lived container that runs a one-shot job (e.g., dbt, Great Expectations) and exits. |
| **Feast** | Open-source feature store managing offline/online features for ML. |
| **Great Expectations** | Data validation framework used to gate medallion-layer promotion. |
| **Health check** | A Docker-defined probe that reports whether a container is ready/healthy; gates startup order. |
| **Iceberg** | Open table format providing schema evolution, partitioning, and snapshots over object storage. |
| **Iceberg REST catalog** | A service exposing Iceberg table metadata via REST, backed by PostgreSQL + MinIO. |
| **Kafka** | Distributed, replayable event-streaming platform; the streaming backbone. |
| **KRaft** | Kafka Raft mode; runs Kafka without ZooKeeper using a built-in consensus controller. |
| **Medallion (Bronze/Silver/Gold)** | Layered data refinement: raw → validated → business-ready. |
| **MinIO** | S3-compatible open-source object storage. |
| **MLflow** | Experiment tracking and model registry. |
| **Named volume** | Docker-managed persistent storage that outlives container lifecycles. |
| **Observability stack** | Prometheus + Grafana + OpenTelemetry for metrics, dashboards, and traces. |
| **Ollama** | Local runtime for serving quantized LLMs. |
| **OTLP** | OpenTelemetry Protocol; transport for traces/metrics to the collector. |
| **Profile** | A Compose mechanism to start a named subset of services. |
| **Prometheus** | Pull-based time-series metrics database. |
| **Qdrant** | Vector database for embedding storage and semantic search. |
| **Quantized model** | An LLM with reduced-precision weights (e.g., Q4) to lower memory use. |
| **RBAC** | Role-Based Access Control; permissions assigned by role. |
| **Resource class** | A reusable set of `mem_limit`/`cpus` values (small/medium/large) applied via YAML anchors. |
| **Restart policy** | Docker rule (`no`, `on-failure`, `unless-stopped`) governing automatic container restarts. |
| **Spark** | Distributed batch processing engine for heavy transformations. |
| **Stack** | A functional group of services sharing a Compose override (storage, ingestion, etc.). |
| **Staged workload** | Operating policy ensuring only one heavy engine peaks at a time. |
| **Superset** | Enterprise-grade open-source BI/dashboard tool. |
| **Volume backup** | Host-side snapshot (`pg_dump`, `mc mirror`, snapshot API) of durable state. |
| **YAML anchor** | A reusable YAML fragment (`&name`/`*name`) used to keep Compose files DRY. |

## Cross References

- Overview: [01-overview.md](./01-overview.md)
- Phase 3 glossary: [../../architecture/15-glossary.md](../../architecture/15-glossary.md)
- Phase 2 glossary: [../domain-research/10-glossary.md](../domain-research/10-glossary.md)

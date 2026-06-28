# 05 Technology Mapping

> **Phase 3 - Solution Architecture & System Design**
> Document 05 of 15

## Purpose

This document maps every architecture layer to a concrete open-source tool and justifies each choice against three constraints: the 16 GB RAM local environment, open-source availability, and production realism.

## Layer-to-Tool Mapping

| Architecture Layer | Tool | Role |
| --- | --- | --- |
| Streaming ingestion | Apache Kafka | Event backbone for incremental data |
| Batch processing | Apache Spark | Large transformations and reprocessing |
| Lightweight analytics | DuckDB | Local analytical queries and prototyping |
| Object storage | MinIO | S3-compatible raw and curated storage |
| Table format | Apache Iceberg | Lakehouse tables with schema evolution |
| Orchestration | Apache Airflow | Scheduled batch workflows |
| Metadata + warehouse | PostgreSQL | Catalog, metadata, and Gold serving |
| Feature store | Feast (or internal feature tables) | Reusable feature management |
| Model tracking | MLflow | Experiment tracking and model registry |
| Vector database | Qdrant | Embedding storage and semantic search |
| Local LLM | Ollama | On-device generation for RAG |
| BI / dashboards | Apache Superset | Operational dashboards and alerts |
| Metrics | Prometheus | Time-series metrics collection |
| Visualization | Grafana | Metrics and health dashboards |
| Tracing | OpenTelemetry | Distributed tracing and instrumentation |
| API services | FastAPI | REST and RAG service endpoints |

## Justification by Tool

### Kafka
- **16 GB fit:** runs as a single broker with conservative heap and partition counts.
- **Open-source:** Apache-licensed.
- **Realism:** the de-facto streaming backbone in production data platforms.

### Spark
- **16 GB fit:** used selectively in local mode with bounded executor memory; heavy jobs run one at a time.
- **Open-source:** Apache-licensed.
- **Realism:** standard distributed processing engine; demonstrates real ETL skills.

### DuckDB
- **16 GB fit:** in-process, extremely memory-efficient for analytical queries.
- **Open-source:** MIT-licensed.
- **Realism:** increasingly used for local and embedded analytics.

### MinIO
- **16 GB fit:** lightweight single-node container.
- **Open-source:** AGPL/Apache components.
- **Realism:** S3-compatible API mirrors cloud object storage patterns.

### Iceberg
- **16 GB fit:** metadata-light table format usable with Spark and DuckDB.
- **Open-source:** Apache-licensed.
- **Realism:** leading open lakehouse table format.

### Airflow
- **16 GB fit:** runs with a local executor and a small scheduler footprint.
- **Open-source:** Apache-licensed.
- **Realism:** widely adopted orchestration standard.

### PostgreSQL
- **16 GB fit:** efficient and reliable at small scale.
- **Open-source:** PostgreSQL license.
- **Realism:** serves both metadata catalog and Gold serving layer.

### Feast
- **16 GB fit:** lightweight; can fall back to plain feature tables if needed.
- **Open-source:** Apache-licensed.
- **Realism:** recognized feature store framework.

### MLflow
- **16 GB fit:** modest local tracking server.
- **Open-source:** Apache-licensed.
- **Realism:** standard model lifecycle tool.

### Qdrant
- **16 GB fit:** efficient vector search with small memory footprint.
- **Open-source:** Apache-licensed.
- **Realism:** production-grade vector database.

### Ollama
- **16 GB fit:** runs quantized small models locally.
- **Open-source:** permissively licensed runtime.
- **Realism:** practical local LLM serving for RAG.

### Superset
- **16 GB fit:** single-container deployment.
- **Open-source:** Apache-licensed.
- **Realism:** enterprise-grade BI tool.

### Prometheus + Grafana + OpenTelemetry
- **16 GB fit:** lightweight collectors and dashboards.
- **Open-source:** CNCF projects.
- **Realism:** the standard cloud-native observability stack.

### FastAPI
- **16 GB fit:** minimal overhead async framework.
- **Open-source:** MIT-licensed.
- **Realism:** common choice for ML and data APIs.

## Resource-Aware Notes

- Heavy engines (Spark, Kafka, Ollama) are not all run at maximum load simultaneously.
- DuckDB is preferred over Spark for smaller analytical tasks to conserve memory.
- Quantized LLM models are used to keep inference within local limits.

## Cross References

- Container architecture: [04-container-architecture.md](./04-container-architecture.md)
- Trade-offs: [13-trade-offs.md](./13-trade-offs.md)
- ADRs: [14-adr.md](./14-adr.md)

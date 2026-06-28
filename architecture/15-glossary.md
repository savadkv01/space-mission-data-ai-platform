# 15 Glossary

> **Phase 3 - Solution Architecture & System Design**
> Document 15 of 15

## Purpose

This glossary defines the architecture and technology terms used across the Phase 3 documents.

## Architecture Terms

| Term | Definition |
| --- | --- |
| Lakehouse | Architecture combining open data lake storage with warehouse-style table semantics. |
| Medallion architecture | Layered data refinement using Bronze, Silver, and Gold stages. |
| Bronze layer | Raw, immutable ingested data with source metadata. |
| Silver layer | Validated, standardized, quality-checked data. |
| Gold layer | Business-ready, curated data for analytics and AI. |
| Event-driven architecture | Design where components react to events rather than direct calls. |
| Lambda architecture | Hybrid pattern combining batch and streaming paths. |
| Microservices | Decomposition into independently deployable services. |
| Schema evolution | Safely changing table schemas over time. |
| Data lineage | Traceability of data from source to consumption. |
| Dead-letter queue | Destination for events that repeatedly fail processing. |
| Feature store | System managing reusable, versioned ML features. |
| RAG | Retrieval-augmented generation; grounding an LLM with retrieved context. |
| Embedding | Vector representation of text or metadata for semantic search. |
| Drift | Change in data or prediction distributions over time. |

## Technology Terms

| Term | Definition |
| --- | --- |
| Kafka | Distributed streaming platform used as the event backbone. |
| Spark | Distributed processing engine for batch ETL. |
| DuckDB | In-process analytical database for local queries. |
| MinIO | S3-compatible open-source object storage. |
| Iceberg | Open lakehouse table format. |
| Airflow | Workflow orchestration system. |
| PostgreSQL | Relational database for metadata and Gold serving. |
| Feast | Open-source feature store framework. |
| MLflow | Experiment tracking and model registry. |
| Qdrant | Vector database for embeddings and semantic search. |
| Ollama | Local LLM runtime for on-device inference. |
| Superset | Open-source BI and dashboard tool. |
| Prometheus | Metrics collection and time-series monitoring. |
| Grafana | Observability dashboard and visualization tool. |
| OpenTelemetry | Standard for distributed tracing and instrumentation. |
| FastAPI | Python framework for REST and ML APIs. |

## Operational Terms

| Term | Definition |
| --- | --- |
| Bronze/Silver/Gold promotion | Moving data between medallion layers after quality checks. |
| Backpressure | Mechanism to handle producers faster than consumers. |
| RBAC | Role-based access control. |
| Recovery point | The data state to which the system can be restored. |
| Recovery time | Duration required to restore service after failure. |

## Cross References

- System overview: [01-system-overview.md](./01-system-overview.md)
- Phase 2 glossary: [../docs/domain-research/10-glossary.md](../docs/domain-research/10-glossary.md)

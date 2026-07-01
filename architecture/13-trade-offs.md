# 13 Trade-off Analysis

> **Phase 3 - Solution Architecture & System Design**
> Document 13 of 15

## Purpose

This document analyzes the major technology trade-offs that shaped the architecture. Each decision lists the chosen option, the benefit, the cost, and when the alternative would be preferable.

## Kafka vs Simpler Queue Systems

| Aspect | Kafka (chosen) | Simpler queue (e.g., RabbitMQ) |
| --- | --- | --- |
| Throughput | high, partitioned | moderate |
| Replay | native log replay | limited |
| Realism | production streaming standard | lighter messaging |
| Cost | more memory and ops | simpler footprint |

**Decision:** Kafka, for replay, durability, and realism.
**When to prefer alternative:** a pure task-queue workload with no replay need and tight memory limits.

## Spark vs DuckDB

| Aspect | Spark | DuckDB |
| --- | --- | --- |
| Scale | large, distributed-capable | single-node analytical |
| Memory | heavier | very light |
| Use case | big ETL and reprocessing | local analytics and prototyping |

**Decision:** use both — Spark for heavy ETL, DuckDB for light analytics.
**When to prefer one:** small data → DuckDB; large transformations → Spark.

## Iceberg vs Delta Lake

| Aspect | Iceberg (chosen) | Delta Lake |
| --- | --- | --- |
| Openness | engine-neutral | strong in Spark ecosystem |
| Schema evolution | robust | robust |
| Portability | high across engines | best within Spark |

**Decision:** Iceberg, for engine neutrality and portability.
**When to prefer alternative:** a Spark/Databricks-centric stack favors Delta.
**MVP tiering:** the MVP / local tier uses plain **Parquet on MinIO + DuckDB** (matches the code, no extra catalog service on a 16 GB laptop); Iceberg is the **scale-tier** target (see data-modeling ADR-10).

## PostgreSQL vs Distributed Warehouse

| Aspect | PostgreSQL (chosen) | Distributed warehouse |
| --- | --- | --- |
| Setup | simple, local | complex, resource-heavy |
| Scale | sufficient for MVP | very large scale |
| Cost | low | high |

**Decision:** PostgreSQL, for MVP-scale serving and metadata.
**When to prefer alternative:** enterprise-scale concurrent analytics beyond a laptop.

## Local LLM vs Cloud LLM

| Aspect | Local LLM (chosen) | Cloud LLM |
| --- | --- | --- |
| Privacy | data stays local | data leaves environment |
| Cost | no per-token cost | recurring cost |
| Quality | smaller quantized models | larger, higher quality |
| Offline | works offline | requires connectivity |

**Decision:** local LLM (Ollama), for privacy, cost control, and offline feasibility.
**When to prefer alternative:** tasks needing top-tier reasoning quality and no privacy/cost constraints.

## Summary Table

| Decision | Chosen | Primary reason |
| --- | --- | --- |
| Streaming | Kafka | replay + realism |
| Processing | Spark + DuckDB | right tool per workload |
| Table format | Iceberg | portability |
| Serving DB | PostgreSQL | simplicity at MVP scale |
| LLM | Ollama (local) | privacy + cost + offline |

## Cross References

- Technology mapping: [05-technology-mapping.md](./05-technology-mapping.md)
- Architecture decision records: [14-adr.md](./14-adr.md)

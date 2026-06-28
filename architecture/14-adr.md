# 14 Architecture Decision Records

> **Phase 3 - Solution Architecture & System Design**
> Document 14 of 15

## Purpose

This document records the formal Architecture Decision Records (ADRs) for the platform. Each ADR captures context, the decision, alternatives considered, and trade-offs.

## ADR Index

| ID | Decision | Status |
| --- | --- | --- |
| ADR-001 | Use Kafka as the streaming backbone | Accepted |
| ADR-002 | Use Iceberg as the lakehouse table format | Accepted |
| ADR-003 | Use MinIO for object storage | Accepted |
| ADR-004 | Adopt a local-first architecture | Accepted |
| ADR-005 | Adopt medallion (Bronze/Silver/Gold) architecture | Accepted |
| ADR-006 | Use a local LLM with RAG over curated data | Accepted |

---

## ADR-001: Use Kafka as the Streaming Backbone

- **Status:** Accepted
- **Date:** 2026-06-28

**Context:** the platform needs durable, replayable event flow for telemetry, ingestion triggers, and anomaly notifications.

**Decision:** use Kafka as the central streaming backbone.

**Alternatives considered:** RabbitMQ, database-based eventing, no streaming layer.

**Trade-offs:** higher memory and operational cost than a simple queue, accepted for replay, durability, and production realism.

---

## ADR-002: Use Iceberg as the Lakehouse Table Format

- **Status:** Accepted
- **Date:** 2026-06-28

**Context:** the platform needs schema evolution, partitioning, and governance over large semi-structured data.

**Decision:** use Apache Iceberg for lakehouse tables.

**Alternatives considered:** Delta Lake, Hive tables, plain parquet.

**Trade-offs:** slightly more setup complexity, accepted for engine neutrality and portability.

---

## ADR-003: Use MinIO for Object Storage

- **Status:** Accepted
- **Date:** 2026-06-28

**Context:** the platform needs S3-compatible object storage that runs locally.

**Decision:** use MinIO as the object storage layer.

**Alternatives considered:** local filesystem only, Ceph, cloud object storage.

**Trade-offs:** less enterprise depth than Ceph, accepted for practicality on a 16 GB laptop.

---

## ADR-004: Adopt a Local-First Architecture

- **Status:** Accepted
- **Date:** 2026-06-28

**Context:** the platform must be demonstrable on a 16 GB RAM laptop using open-source tools and free datasets, without managed cloud services.

**Decision:** design a local-first, Docker-based, single-node deployment whose logical architecture mirrors a scalable production system.

**Alternatives considered:** cloud-native managed services, hybrid cloud deployment.

**Trade-offs:** limited raw scale and concurrency, accepted because the same logical patterns scale out later without redesign, and local-first maximizes portability and cost control.

---

## ADR-005: Adopt Medallion Architecture

- **Status:** Accepted
- **Date:** 2026-06-28

**Context:** the platform needs progressive data quality and clear separation between raw landing and business-ready outputs.

**Decision:** use Bronze, Silver, and Gold layers.

**Alternatives considered:** single-stage transformation, ad-hoc curation.

**Trade-offs:** more storage and pipeline stages, accepted for traceability, reuse, and governance.

---

## ADR-006: Use a Local LLM with RAG over Curated Data

- **Status:** Accepted
- **Date:** 2026-06-28

**Context:** the platform needs an analyst assistant grounded in curated mission data while respecting privacy, cost, and offline constraints.

**Decision:** use a local LLM (Ollama) with a Qdrant-backed RAG pipeline over Gold data.

**Alternatives considered:** cloud LLM APIs, no LLM assistant.

**Trade-offs:** lower raw model quality and slower responses than large cloud models, accepted for privacy, zero per-token cost, and offline feasibility.

## Cross References

- Trade-offs: [13-trade-offs.md](./13-trade-offs.md)
- Technology mapping: [05-technology-mapping.md](./05-technology-mapping.md)

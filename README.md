# Space Mission Data & AI Platform

An enterprise-grade, production-simulated **Space Mission Data & AI Platform** covering Earth Observation Operations Intelligence. Inspired by real-world aerospace organizations (NASA, ESA, MBRSC, Space42, Bayanat, Yahsat) and designed to run on a 16 GB RAM laptop with Docker Desktop and open-source tooling.

---

## Phase Progress

| Phase | Title | Status |
| --- | --- | --- |
| 01 | Business Analysis & Use-Case Discovery | ✅ Complete |
| 02 | Domain Research & Dataset Ecosystem Mapping | ✅ Complete |
| 03 | Solution Architecture & System Design | ✅ Complete |
| 04 | Infrastructure Design & Container Architecture | ✅ Complete |
| 05 | Source Data Analysis | ✅ Complete |
| 06 | Data Modeling & Lakehouse Design | ✅ Complete |
| 07 | Data Ingestion Engineering | ✅ Complete |
| 08 | Data Processing & Transformation | 🔜 Upcoming |
| 09 | AI/ML Pipelines | 🔜 Upcoming |
| 10 | LLM + RAG Systems | 🔜 Upcoming |
| 11 | APIs & Serving | 🔜 Upcoming |
| 12 | Observability & DevOps | 🔜 Upcoming |

---

## Operations

Day-to-day operator commands — start/stop, status & health, service URLs and login,
querying PostgreSQL, browsing MinIO, and viewing Bronze/Silver/Gold — live in the
[Operations Runbook](OPERATIONS.md). It is a living document, extended each phase.

---

## Repository Structure

| Folder | Purpose |
| --- | --- |
| `architecture/` | System overview, patterns, HLA, container design, technology mapping, data/AI/ML/observability/security/deployment architecture |
| `docs/business/` | MVP definition, use-case ranking, roadmap, stakeholders, KPIs, risks |
| `docs/domain-research/` | Ecosystem overview, 30-source dataset catalog, data flows, quality, prioritization |
| `docs/source-data-analysis/` | 45-dataset inventory, profiling, structure, quality, use-case mapping, prioritization |
| `docs/data-modeling/` | Medallion design, Bronze/Silver/Gold models, star schemas, time-series, geospatial, feature store, vector model, governance, ADRs |
| `docs/ingestion/` | Ingestion design (streaming, batch, API/file, simulation, landing zone, quality, observability, ADRs) |
| `infrastructure/` | Docker Compose stacks, configs (Kafka, MinIO, Spark, Postgres, Prometheus, Grafana, OpenTelemetry) |
| `ingestion/` | Ingestion layer implementation — Kafka producers/consumers, Airflow DAGs, API/file connectors, synthetic data generators, quality/quarantine |
| `tools/` | Developer utilities (e.g. `datasource-preflight` data-source connectivity checks) |

---

## Key Documentation

### Phase 1 — Business Analysis
`docs/business/` — industry overview, business problems, use-case analysis and ranking, MVP definition, 6-phase roadmap, stakeholder map, KPIs, risks, and glossary.

### Phase 2 — Domain Research
`docs/domain-research/` — space data ecosystem overview, 30-source dataset catalog, data flow analysis, classification, quality assessment, prioritization, MVP dataset selection, and expansion roadmap.

### Phase 3–4 — Architecture
`architecture/` — 15 documents covering system overview, architecture patterns, high-level and container architecture, technology mapping, data/AI/ML/observability/security/deployment design, scalability, failure handling, trade-offs, ADRs, and glossary.

### Phase 5 — Source Data Analysis
`docs/source-data-analysis/` — 45-dataset inventory across 8 categories, dataset profiling, structure analysis, quality assessment, use-case mapping, transformation complexity, relationships, freshness strategy, risks, prioritization, and MVP dataset selection.

### Phase 6 — Data Modeling
`docs/data-modeling/` — complete lakehouse data model across 18 documents:
- Modeling strategy (medallion, star schema, OLTP/OLAP, batch/stream alignment)
- Bronze (immutable raw landing zone with provenance)
- Silver (conformed entities: satellite, mission, sensor, orbit, ground station, EO observations)
- Gold (star schemas for satellite health, launch, space weather, earth observation)
- Time-series model (telemetry, orbit, sensor readings — minute/hour/day tiers)
- Geospatial model (WGS84, H3 indexing, spatial joins)
- Feature store design (satellite health, orbit stability, weather impact, EO risk features)
- Vector data model (RAG knowledge base, telemetry semantic embeddings)
- Data relationships, granularity, partitioning, lifecycle, performance, governance
- 6 ADRs, trade-off analysis, and glossary

### Phase 7 — Data Ingestion
`docs/ingestion/` (17 design docs) + `ingestion/` (implementation):
- Streaming ingestion (Kafka producers/consumers, topic architecture, at-least-once delivery, DLQ)
- Batch ingestion (Airflow DAGs, scheduling, retry/backoff, idempotent re-runs)
- API connectors (NASA FIRMS/POWER, NOAA SWPC, CelesTrak) with retry, rate-limiting and backoff
- File ingestion + MinIO landing-zone layout (Hive-style `ingest_date` partitions)
- Synthetic data generators (satellite telemetry, orbit via SGP4, space weather)
- Bronze envelope (provenance + checksum), ingestion-time validation and quarantine
- Observability, latency, scalability, security, trade-offs, ADRs and glossary
- Offline-validated: 14 unit tests pass and an end-to-end in-memory demo runs without infrastructure. See [ingestion/README.md](ingestion/README.md).

---

## Technology Stack

| Concern | Tool |
| --- | --- |
| Containerization | Docker Desktop |
| Streaming | Apache Kafka |
| Processing | Apache Spark, DuckDB |
| Storage | MinIO (object), Apache Iceberg (table format), PostgreSQL |
| Orchestration | Apache Airflow |
| Observability | Prometheus, Grafana, OpenTelemetry |
| AI / ML | Python, scikit-learn, PyTorch |
| LLM / RAG | Qdrant, LangChain |

---

## Project Intent

Simulates a real enterprise aerospace data platform end-to-end: from raw open datasets through lakehouse modeling, AI/ML, LLM+RAG, APIs, and observability — while remaining fully feasible on a developer laptop with free, open-source tools.

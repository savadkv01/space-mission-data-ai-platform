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
| 07 | Data Ingestion Engineering | 🔜 Upcoming |
| 08 | Data Processing & Transformation | 🔜 Upcoming |
| 09 | AI/ML Pipelines | 🔜 Upcoming |
| 10 | LLM + RAG Systems | 🔜 Upcoming |
| 11 | APIs & Serving | 🔜 Upcoming |
| 12 | Observability & DevOps | 🔜 Upcoming |

---

## Repository Structure

| Folder | Purpose |
| --- | --- |
| `architecture/` | System overview, patterns, HLA, container design, technology mapping, data/AI/ML/observability/security/deployment architecture |
| `docs/business/` | MVP definition, use-case ranking, roadmap, stakeholders, KPIs, risks |
| `docs/domain-research/` | Ecosystem overview, 30-source dataset catalog, data flows, quality, prioritization |
| `docs/source-data-analysis/` | 45-dataset inventory, profiling, structure, quality, use-case mapping, prioritization |
| `docs/data-modeling/` | Medallion design, Bronze/Silver/Gold models, star schemas, time-series, geospatial, feature store, vector model, governance, ADRs |
| `infrastructure/` | Docker Compose stacks, configs (Kafka, MinIO, Spark, Postgres, Prometheus, Grafana, OpenTelemetry) |

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

# Space Mission Data & AI Platform

An enterprise-grade, production-simulated **Space Mission Data & AI Platform** covering Earth Observation Operations Intelligence. Inspired by real-world aerospace organizations (NASA, ESA, MBRSC, Space42, Bayanat, Yahsat) and designed to run on a 16 GB RAM laptop with Docker Desktop and open-source tooling.

---

## Phase Progress

Phase numbering aligns with the authored phase prompts in [.github/prompts/](.github/prompts/).

| Phase | Title | Status |
| --- | --- | --- |
| 01 | Business Analysis | ✅ Complete |
| 02 | Domain Research | ✅ Complete |
| 03 | Solution Architecture | ✅ Complete |
| 04 | Infrastructure Design | ✅ Complete |
| 05 | Source Data Analysis | ✅ Complete |
| 06 | Data Modeling | ✅ Complete |
| 07 | Infrastructure Implementation | ✅ Complete |
| 08 | Data Ingestion | ✅ Complete |
| 09 | Data Transformation | ✅ Complete |
| 10 | Data Quality | ✅ Complete |
| 11 | Serving Layer | ✅ Complete |
| 12 | Business Intelligence (BI) | ✅ Complete |
| 13 | Feature Store | 🔜 Upcoming |
| 14 | Machine Learning | 🔜 Upcoming |
| 15 | RAG (LLM Retrieval) | 🔜 Upcoming |
| 16 | Platform API | 🔜 Upcoming |
| 17 | Observability | 🔜 Upcoming |
| 18 | Security | 🔜 Upcoming |
| 19 | CI/CD | 🔜 Upcoming |
| 20 | Production Incidents | 🔜 Upcoming |
| 21 | Testing | 🔜 Upcoming |
| 22 | Performance | 🔜 Upcoming |
| 23 | Documentation | 🔜 Upcoming |
| 24 | Interview Preparation | 🔜 Upcoming |
| 25 | Project Review | 🔜 Upcoming |

> **Parallel track:** a Climate, Dust & Air-Quality expansion (extension prompts `05b`–`16b`) — see [Planned Expansion](#planned-expansion--climate-dust--air-quality-monitoring) below. The source-analysis → BI layers (`05b`–`12b`) are **implemented**; `13b`–`16b` (feature store, ML, RAG, API) are upcoming with the AI/ML track.

---

## Operations

Day-to-day operator commands — start/stop, status & health, service URLs and login,
querying PostgreSQL, browsing MinIO, and viewing Bronze/Silver/Gold — live in the
[Operations Runbook](OPERATIONS.md). It is a living document, extended each phase.

Two operator references complement the runbook:

- [Data Inventory](DATA-INVENTORY.md) — consolidated table of every Bronze source, Silver entity, Gold fact/dim, serving product, BI dataset, feature group, ML artifact, and RAG collection, with a short description of what each contains.
- [Functional Test Cases](FUNCTIONAL-TEST-CASES.md) — business-level acceptance tests (Given/When/Then) that validate use-case outcomes against certified data products and KPI thresholds.

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
| `docs/transformation/` | Transformation design (processing engines, Bronze→Silver→Gold, streaming/batch, cleaning, feature engineering, geospatial, time-series, lineage, ADRs) |
| `docs/data-quality/` | Data-quality design (dimensions, validation rules, medallion validation, profiling, reconciliation, monitoring, governance, SLAs/KPIs, ADRs) |
| `docs/bi/` | BI design (strategy, dashboard catalog, KPIs, dashboard standards, personas, datasets, reporting, alerting, security, ADRs) |
| `infrastructure/` | Docker Compose stacks, configs (Kafka, MinIO, Spark, Postgres, Prometheus, Grafana, OpenTelemetry) |
| `ingestion/` | Ingestion layer implementation — Kafka producers/consumers, Airflow DAGs, API/file connectors, synthetic data generators, quality/quarantine |
| `transformation/` | Transformation layer implementation — Bronze→Silver→Gold (PySpark + dbt/DuckDB), geospatial/time-series/feature engineering, Spark streaming, Airflow orchestration |
| `quality/` | Data-quality framework — validation rules, profiling, monitoring, governance, and incident records |
| `serving/` | Serving layer — Gold data products, semantic layer, dbt marts, REST API design, and LLM/RAG serving models |
| `bi/` | Business intelligence — Apache Superset dashboards, certified datasets, KPI catalog, alerts, and reporting strategy |
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

### Phase 7 — Infrastructure Implementation
`infrastructure/` — Docker Compose stacks (storage, processing, ingestion, AI, BI, observability) plus service configs for Kafka, MinIO, Spark, PostgreSQL, Prometheus, Grafana, and OpenTelemetry. See [infrastructure/README.md](infrastructure/README.md).

### Phase 8 — Data Ingestion
`docs/ingestion/` (17 design docs) + `ingestion/` (implementation):
- Streaming ingestion (Kafka producers/consumers, topic architecture, at-least-once delivery, DLQ)
- Batch ingestion (Airflow DAGs, scheduling, retry/backoff, idempotent re-runs)
- API connectors (NASA FIRMS/POWER, NOAA SWPC, CelesTrak, Sentinel Hub) with retry, rate-limiting and backoff
- File ingestion + MinIO landing-zone layout (Hive-style `ingest_date` partitions)
- Synthetic data generators (satellite telemetry, orbit via SGP4, space weather)
- Bronze envelope (provenance + checksum), ingestion-time validation and quarantine
- Observability, latency, scalability, security, trade-offs, ADRs and glossary
- Offline-validated: unit tests pass and an end-to-end in-memory demo runs without infrastructure. See [ingestion/README.md](ingestion/README.md).

### Phase 9 — Data Transformation
`docs/transformation/` (19 design docs) + `transformation/` (implementation):
- Processing engines (PySpark + dbt/DuckDB) and Bronze→Silver→Gold pipelines
- Cleaning framework, feature engineering, aggregation, geospatial (Apache Sedona), and time-series transforms
- Spark structured streaming, Airflow orchestration, lineage, performance, error handling, ADRs
- Pure-Python rules offline unit-tested; Spark/dbt entrypoints ready for infra. See [transformation/README.md](transformation/README.md).

### Phase 10 — Data Quality
`docs/data-quality/` (16 design docs) + `quality/` (implementation):
- Quality dimensions, validation rules, medallion validation, and data profiling
- Business rules, reconciliation, monitoring, exception handling, metadata/lineage
- Governance, SLAs/KPIs, production incidents, trade-offs, ADRs. See [quality/README.md](quality/README.md).

### Phase 11 — Serving Layer
`serving/` — Gold data products (wildfire, flood, vessel, scene-catalog, AOI-validation daily), a semantic layer (business dimensions + metric registry), dbt marts and raw DDL, a materialized KPI aggregate, REST API design, and LLM/RAG serving models. Contract-tested with dbt schema tests and offline Python unit tests. See [serving/README.md](serving/README.md).

### Phase 12 — Business Intelligence
`docs/bi/` (14 design docs) + `bi/` (implementation):
- Apache Superset dashboards (executive, earth-observation, satellite, weather, launch, platform)
- Certified datasets, KPI catalog, alert strategy, reporting strategy, dataset governance
- Dashboard standards, personas, security, ADRs. See [bi/README.md](bi/README.md).

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

---

## Planned Expansion — Climate, Dust & Air-Quality Monitoring

A post-MVP initiative extends the platform into **climate change, dust storm, and air-quality monitoring** (high value for UAE contexts). It is delivered as a set of authored phase prompts and requires **no architectural change** — it reuses the existing `ApiConnector` → JSONL Bronze → Silver/Gold → serving → BI pattern, plus the existing Feast, MLflow, and Qdrant/Ollama stacks.

**Scope decision (Strategy A — tabular / statistical-API sources only):**

| Included | Deferred |
| --- | --- |
| OpenAQ (ground air quality); Sentinel-5P/TROPOMI + MODIS/VIIRS AOD via **Google Earth Engine** (free — NO₂, SO₂, CO, O₃, CH₄, aerosol index, AOD); climate indicators derived from already-ingested LST/NDVI/SST/forest data | CAMS & ERA5 raw NetCDF (need a binary blob-landing capability); geostationary SEVIRI/Himawari (exceeds the 16 GB budget) |

**Authored prompt phases:** `05b → 06b → 08b → 09b → 10b → 11b → 12b` (extend the completed source-analysis → BI layers), then `13b → 14b → 15b → 16b` (climate-scoped feature store, ML, RAG, API). Phases 17–25 run once and cover the new components automatically. See [.github/prompts/](.github/prompts/).

**Implementation status:**

| Phase | Deliverable | Status |
| --- | --- | --- |
| 05b | Climate source-data analysis (inventory, AOI strategy, derived indicators, quality, freshness/risk, MVP) — [docs](docs/source-data-analysis/climate/README.md) | ✅ Complete |
| 06b | Climate data model (Bronze/Silver/Gold contracts, dimensions, KPI thresholds, lineage) — [docs](docs/data-modeling/climate/README.md) | ✅ Complete |
| 08b | Ingestion — OpenAQ + Google Earth Engine (S-5P/AOD) connectors, DAGs, preflight — [docs](docs/ingestion/climate-connectors.md) | ✅ Complete |
| 09b | Transformation — atmospheric Bronze→Silver→Gold marts + climate indicators — [docs](docs/transformation/climate-marts.md) | ✅ Complete |
| 10b | Data quality — climate profiling, rules, and validation suites | ✅ Complete |
| 11b | Serving — climate serving products + semantic dimensions | ✅ Complete |
| 12b | BI — air-quality/dust + climate-indicators dashboards; weather promoted to real data | ✅ Complete |
| 13b–16b | Climate-scoped feature store, ML, RAG, API | 🔜 With AI/ML track |

> **Atmospheric access-layer note.** Sentinel-5P (trace gases) and MODIS/VIIRS AOD are ingested via **Google Earth Engine** (free, non-commercial) rather than the Sentinel Hub Statistical API, whose `sentinel-5p-l2` / MODIS collections are not entitled on the free plan. The emitted Bronze bucket shape is unchanged, so every downstream Silver/Gold/serving/BI layer is backend-agnostic. See [docs/ingestion/climate-connectors.md](docs/ingestion/climate-connectors.md).

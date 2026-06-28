# Prompt 06 - Data Modeling (Lakehouse Architecture)

# Enterprise Space Mission Data & AI Platform

> **Phase 6 - Data Modeling & Lakehouse Design**

---

# Objective

You are acting as:

* Principal Data Architect
* Data Modeling Expert
* Lakehouse Architect
* Analytics Engineer
* AI Data Architect

Your task is to design the **complete enterprise data model** for the Space Mission Data & AI Platform.

This includes:

* Lakehouse modeling
* Warehouse modeling
* Feature store design
* Vector data design
* AI-ready data structures

This is NOT implementation.

This is **conceptual + logical + physical data modeling design**.

---

# Critical Rules

* Do NOT write code
* Do NOT implement Spark/dbt pipelines
* Do NOT configure databases
* Do NOT design ingestion flows
* Focus ONLY on data modeling
* Must align with datasets from Phase 5
* Must be feasible on 16GB laptop

---

# Context

We are building a Space Data Platform that processes:

* Satellite telemetry
* Earth observation data
* Space weather data
* Launch data
* Orbit tracking data
* Mission events
* AI/ML training datasets

The platform will support:

* Real-time analytics
* Historical analytics
* Machine learning models
* LLM + RAG systems

---

# Task 1 - Data Modeling Strategy

Define overall modeling strategy:

Include:

* Medallion architecture (Bronze / Silver / Gold)
* Star schema vs Snowflake schema usage
* Data vault (if applicable)
* OLTP vs OLAP separation
* Batch vs streaming model alignment

---

# Task 2 - Bronze Layer (Raw Data Model)

Design Bronze layer:

Include:

* Raw ingestion structure
* Append-only design
* Schema-on-read strategy
* Storage format (Parquet/Iceberg conceptually)
* Partitioning strategy (time-based, mission-based)

Explain:

* Why raw layer must remain immutable
* How traceability is maintained

---

# Task 3 - Silver Layer (Cleaned Data Model)

Design Silver layer:

Include:

* Data cleaning rules
* Standardized schemas
* Deduplication logic (conceptual)
* Time alignment strategy
* Geospatial normalization
* Telemetry standardization

Define core entities:

* Satellite
* Sensor
* Mission
* Launch event
* Orbit trajectory
* Ground station

---

# Task 4 - Gold Layer (Business Data Model)

Design Gold layer:

Create analytical models for:

* Satellite health analytics
* Launch performance analytics
* Space weather impact analytics
* Earth observation analytics
* Mission success metrics

Define:

* Fact tables
* Dimension tables
* Aggregation strategy
* KPI tables

---

# Task 5 - Star Schema Design

Design star schemas for:

## 1. Satellite Operations Analytics

## 2. Launch Analytics

## 3. Space Weather Impact

## 4. Earth Observation Insights

For each:

* Fact tables
* Dimension tables
* Grain definition
* Keys
* Relationships

Include Mermaid ER diagrams.

---

# Task 6 - Time-Series Data Model

Design time-series model for:

* telemetry data
* orbit data
* sensor readings

Include:

* partitioning strategy
* windowing strategy
* aggregation levels (minute/hour/day)

---

# Task 7 - Geospatial Data Model

Design geospatial structure for:

* satellite position
* earth observation coordinates
* orbit paths

Include:

* coordinate system handling
* spatial indexing concept
* geospatial joins (conceptual)

---

# Task 8 - Feature Store Design

Define AI feature store:

Include:

* Feature definitions
* Feature groups:

  * Satellite health features
  * Orbit stability features
  * Weather impact features
* Online vs offline store concept
* Feature reuse strategy

---

# Task 9 - Vector Data Model (LLM / RAG)

Design vector database structure:

Include:

* Embedding types
* Document structure
* Space mission knowledge base
* Telemetry semantic embeddings
* RAG indexing structure

---

# Task 10 - Data Relationships

Define relationships between:

* Satellite ↔ Mission
* Satellite ↔ Telemetry
* Launch ↔ Satellite
* Space weather ↔ Telemetry anomalies
* Earth observation ↔ climate events

Include ER diagram (Mermaid).

---

# Task 11 - Data Granularity Strategy

Define:

* Event-level data
* Time-series data
* Aggregated KPI data
* Snapshot tables

Explain when each is used.

---

# Task 12 - Data Partitioning Strategy

Define:

* Time-based partitioning
* Mission-based partitioning
* Satellite-based partitioning
* Hybrid partitioning strategy

---

# Task 13 - Data Lifecycle Management

Define:

* Retention policies
* Archival strategy
* Data versioning
* Historical reprocessing strategy

---

# Task 14 - Performance Considerations

Define:

* Query optimization strategy
* Pre-aggregation strategy
* Indexing strategy (conceptual)
* Storage optimization

---

# Task 15 - Data Governance Model

Define:

* Data ownership model
* Data lineage tracking
* Metadata strategy
* Data catalog design (conceptual)

---

# Task 16 - Trade-off Analysis

Explain:

* Star schema vs Data Vault
* Wide tables vs normalized models
* Batch aggregates vs real-time views
* Feature store vs direct computation

---

# Task 17 - Architecture Decision Records (ADR)

Create at least 5 ADRs:

Examples:

* Why Medallion architecture is used
* Why Star schema is preferred for analytics
* Why time-series modeling is required
* Why feature store is introduced
* Why vector database is needed

---

# Deliverables

Generate:

```text id="fix6c"
docs/data-modeling/

01-modeling-strategy.md
02-bronze-layer.md
03-silver-layer.md
04-gold-layer.md
05-star-schemas.md
06-time-series-model.md
07-geospatial-model.md
08-feature-store.md
09-vector-model.md
10-data-relationships.md
11-granularity.md
12-partitioning.md
13-data-lifecycle.md
14-performance.md
15-governance.md
16-trade-offs.md
17-adr.md
18-glossary.md
```

---

# Documentation Standards

* Enterprise-grade Markdown
* Include multiple Mermaid ER diagrams
* Include schema tables
* Clearly define grain for every fact table
* Explicit assumptions required
* Interview-ready explanation style

---

# Acceptance Criteria

This phase is complete only if:

* Full Lakehouse model is defined
* Star schemas are created
* Time-series model is defined
* Geospatial model is included
* Feature store design exists
* Vector DB design exists
* Data governance is defined

---

# Definition of Done

This phase is complete when:

> A data engineering team can directly implement physical tables from this design without asking clarification questions.

Stop after completing this phase. Do NOT proceed to ingestion or implementation.

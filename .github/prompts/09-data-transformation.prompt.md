# Prompt 09 - Data Transformation Layer Design

# Enterprise Space Mission Data & AI Platform

> **Phase 9 - Data Transformation (Lakehouse Processing Layer)**

---

# Objective

You are acting as:

* Principal Data Engineer
* Lakehouse Architect
* Analytics Engineer
* Spark Architect
* Data Modeling Engineer

Your task is to design the **complete data transformation layer** for the Space Mission Data & AI Platform.

This layer converts:

> Raw ingestion data → clean structured data → analytics + AI-ready datasets

---

# Critical Rules

* Do NOT write code
* Do NOT implement Spark/dbt jobs
* Do NOT configure infrastructure
* Focus ONLY on transformation design
* Must align with ingestion (Phase 8) and modeling (Phase 6)
* Must be feasible on **16 GB Docker-based local system**
* Must use open-source tools only

---

# Context

We are transforming data from:

* Satellite telemetry streams
* Earth observation data
* Space weather feeds
* Launch events
* Orbital trajectory updates
* Mission logs
* Synthetic simulation data

Into:

* Analytics-ready datasets
* AI/ML feature sets
* Business intelligence tables
* LLM + RAG knowledge structures

---

# Task 1 - Transformation Layer Overview

Define:

* Purpose of transformation layer in lakehouse architecture
* Position between ingestion and serving layers
* Batch vs streaming transformation strategy
* Medallion architecture role (Bronze → Silver → Gold)

Include Mermaid architecture flow.

---

# Task 2 - Processing Engine Design

Define transformation engines:

## 1. Apache Spark (core engine)

* batch processing
* structured streaming (conceptual)

## 2. dbt (analytics transformations)

* SQL-based modeling
* data marts

## 3. Optional lightweight processing fallback (DuckDB concept)

Explain:

* why Spark is used
* when dbt is used
* when lightweight processing is sufficient

---

# Task 3 - Bronze → Silver Transformation Design

Define Silver layer processing:

Include:

* schema standardization
* data cleaning rules
* deduplication logic
* timestamp normalization
* geospatial normalization
* telemetry structuring

Define transformation rules for:

* satellite telemetry
* orbit data
* space weather data

---

# Task 4 - Silver → Gold Transformation Design

Define Gold layer:

Include:

* aggregation logic
* KPI computation
* business metrics creation
* analytical dataset design

Define Gold datasets for:

## 1. Satellite Health Analytics

## 2. Launch Performance Analytics

## 3. Space Weather Impact Analytics

## 4. Earth Observation Analytics

---

# Task 5 - Streaming Transformation Design

Define near real-time processing:

Include:

* Kafka → Spark streaming pipeline
* windowing strategy
* micro-batch processing
* late data handling
* watermark strategy (conceptual)

---

# Task 6 - Batch Transformation Design

Define batch processing workflows:

Include:

* daily/hourly batch jobs
* incremental processing
* full reprocessing strategy
* dependency chaining

---

# Task 7 - Data Cleaning Framework

Define cleaning rules:

* null handling
* duplicate removal
* outlier detection
* corrupted record handling
* schema mismatch handling

Include:

* where cleaning happens (Bronze/Silver boundary)
* rule standardization strategy

---

# Task 8 - Feature Engineering Design

Define AI feature engineering layer:

Include features for:

## Satellite Health

* signal stability
* anomaly indicators
* sensor drift metrics

## Orbit Analytics

* orbit deviation
* velocity variance
* trajectory stability

## Space Weather

* solar storm intensity
* radiation exposure index

Explain:

* feature derivation strategy
* feature reuse strategy

---

# Task 9 - Data Aggregation Strategy

Define:

* time-based aggregation (minute/hour/day)
* satellite-level aggregation
* mission-level aggregation
* geospatial aggregation

Explain trade-offs between:

* raw vs aggregated data storage

---

# Task 10 - Geospatial Transformation Design

Define:

* coordinate transformation strategy
* spatial normalization
* orbit path reconstruction
* geospatial joins (conceptual)

---

# Task 11 - Time-Series Processing Design

Define:

* time-window alignment
* missing timestamp interpolation
* resampling strategy
* anomaly detection preprocessing

---

# Task 12 - Data Quality Enforcement in Transformation

Define:

* validation checkpoints between layers
* data reconciliation strategy
* correction vs rejection rules
* audit logging strategy

---

# Task 13 - Data Lineage Design

Define:

* lineage tracking strategy
* transformation traceability
* dataset versioning
* reproducibility mechanism

---

# Task 14 - Performance Optimization Strategy

Define:

* partition optimization
* caching strategy
* compute optimization (Spark tuning conceptually)
* file format optimization (Parquet/Iceberg concept)

---

# Task 15 - Error Handling Strategy

Define:

* failed transformation recovery
* partial job retry strategy
* checkpointing strategy
* dead letter dataset handling

---

# Task 16 - Observability of Transformation Layer

Define monitoring for:

* job execution status
* processing latency
* data freshness
* failure rates
* throughput metrics

Include:

* Prometheus metrics mapping
* Grafana dashboard concepts

---

# Task 17 - Trade-off Analysis

Explain trade-offs:

* batch vs streaming transformation
* Spark vs dbt responsibilities
* pre-aggregation vs on-demand computation
* lakehouse vs warehouse separation

---

# Task 18 - Architecture Decision Records (ADR)

Create at least 5 ADRs:

Examples:

* Why Spark is used for transformation
* Why dbt is used for Gold layer
* Why Medallion architecture is enforced
* Why streaming + batch hybrid is required
* Why feature engineering is part of transformation layer

---

# Deliverables

Generate:

```text id="fix9b"
transformation/

batch/
├── bronze-to-silver.md
├── silver-to-gold.md
├── aggregation-jobs.md

streaming/
├── spark-streaming-design.md
├── windowing-strategy.md

features/
├── feature-engineering.md
├── feature-definitions.md

cleaning/
├── data-quality-rules.md
├── validation-framework.md

geospatial/
├── spatial-transformation.md

timeseries/
├── time-series-processing.md

docs/transformation/

01-overview.md
02-processing-engines.md
03-bronze-silver.md
04-silver-gold.md
05-streaming-processing.md
06-batch-processing.md
07-cleaning-framework.md
08-feature-engineering.md
09-aggregation.md
10-geospatial.md
11-time-series.md
12-data-quality.md
13-lineage.md
14-performance.md
15-error-handling.md
16-observability.md
17-trade-offs.md
18-adr.md
19-glossary.md
```

---

# Documentation Standards

* Enterprise-grade Markdown
* Include Mermaid diagrams for:

  * transformation flow (Bronze → Silver → Gold)
  * streaming pipeline
  * batch DAG flow
* Include tables for feature definitions
* Clearly define transformation rules
* Explicit assumptions required

---

# Acceptance Criteria

This phase is complete only if:

* Full Medallion transformation system is defined
* Streaming + batch transformation is included
* Feature engineering is defined
* Data quality framework exists
* Geospatial + time-series processing is included
* Observability is included
* System is feasible on 16GB local environment

---

# Definition of Done

This phase is complete when:

> A data engineering team can implement Spark/dbt pipelines directly from this design without clarification.

Stop after completing this phase. Do NOT proceed to AI/ML or serving layer.

# Prompt 08 - Data Ingestion Implementation Design

# Enterprise Space Mission Data & AI Platform

> **Phase 8 - Data Ingestion Layer (Engineering Design)**

---

# Objective

You are acting as:

* Senior Data Engineer
* Streaming Architect
* Data Integration Engineer
* Platform Engineer
* SRE for Data Systems

Your task is to design the **full ingestion layer implementation blueprint** for the Space Mission Data & AI Platform.

This includes:

* Streaming ingestion (Kafka)
* Batch ingestion (Airflow)
* API ingestion (NASA/NOAA/etc.)
* File-based ingestion (MinIO)
* Synthetic telemetry ingestion system

This phase defines **how data actually flows into the platform**.

---

# Critical Rules

* Do NOT write code
* Do NOT implement pipelines
* Do NOT configure actual Kafka/Airflow jobs
* Do NOT design transformations (that is Phase 9+)
* Focus ONLY on ingestion design
* Must be feasible on **16 GB RAM Docker environment**
* Must align with infrastructure from Phase 7

---

# Context

We are building a Space Data Platform that ingests:

* Satellite telemetry streams
* Earth observation metadata
* Space weather feeds
* Launch event data
* Orbital position updates
* Mission logs
* Simulated satellite data

These will power downstream:

* Analytics
* ML models
* BI dashboards
* LLM + RAG system

---

# Task 1 - End-to-End Ingestion Architecture

Define:

* Full ingestion lifecycle
* Data flow from external source → platform landing zone
* Separation of streaming vs batch ingestion
* Role of Kafka, Airflow, APIs, and MinIO

Include Mermaid diagram.

---

# Task 2 - Streaming Ingestion Design (Kafka)

Design Kafka ingestion layer:

Include:

## 1. Topic Strategy

* telemetry.satellite.raw
* telemetry.satellite.cleaned
* space.weather.events
* launch.events
* orbit.position.stream

## 2. Partition Strategy

* satellite_id-based partitioning
* time-based partitioning

## 3. Message Structure (conceptual)

* timestamp
* satellite_id
* sensor_type
* payload
* metadata

## 4. Producer Design

* simulated telemetry producers
* API-to-Kafka bridge producers

## 5. Consumer Design

* raw ingestion consumer
* validation consumer
* storage writer consumer

## 6. Offset Management Strategy

---

# Task 3 - Batch Ingestion Design (Airflow)

Design Airflow ingestion system:

Include:

## DAG Categories

* NASA API ingestion DAG
* NOAA space weather ingestion DAG
* Earth observation batch ingestion DAG
* Launch data ingestion DAG

## DAG Design Rules

* retry strategy
* backoff strategy
* scheduling frequency
* incremental loads

## Data Flow

External API → staging → MinIO → Bronze layer

---

# Task 4 - API Ingestion Design

Design ingestion from external APIs:

Include:

* NASA APIs
* NOAA APIs
* ESA datasets
* CelesTrak orbital data

Define:

* Pagination handling
* Rate limiting strategy
* Retry + backoff strategy
* Caching strategy
* API failure fallback behavior

---

# Task 5 - File-Based Ingestion (MinIO)

Design ingestion from files:

Include:

* CSV telemetry files
* JSON mission logs
* Parquet datasets
* Earth observation datasets

Define:

* folder structure in MinIO
* naming conventions
* partitioning strategy
* ingestion triggers

---

# Task 6 - Synthetic Data Generation System

Design simulation system:

Include:

* satellite telemetry generator
* orbit simulation generator
* space weather synthetic generator

Define:

* frequency of generation
* realism strategy
* noise injection
* failure simulation (for ML training)

Explain why synthetic data is needed.

---

# Task 7 - Data Landing Zone Architecture

Define ingestion landing zones:

## Zones

* Raw Zone (Bronze)
* Staging Zone
* Processed Zone (handoff to transformation layer)

Define:

* MinIO bucket structure
* folder hierarchy
* retention rules

---

# Task 8 - Schema Strategy

Define:

* schema-on-read vs schema-on-write
* schema registry concept (lightweight)
* schema evolution handling
* backward compatibility strategy
* schema validation at ingestion

---

# Task 9 - Data Quality at Ingestion

Define validation rules:

* null checks
* range validation
* duplicate detection
* timestamp validation
* geospatial validation

Define:

* where validation happens
* failure handling strategy
* quarantine (bad data handling)

---

# Task 10 - Error Handling Strategy

Define:

* retry mechanisms
* dead letter queues (Kafka DLQ)
* Airflow task failure strategy
* API ingestion fallback strategy
* partial ingestion recovery strategy

---

# Task 11 - Observability for Ingestion Layer

Define monitoring for:

* Kafka lag
* consumer throughput
* API ingestion failures
* Airflow DAG success/failure
* ingestion latency

Include:

* Prometheus metrics mapping
* Grafana dashboard concepts

---

# Task 12 - Latency Strategy

Define:

* real-time ingestion latency target (<5 sec for telemetry)
* batch ingestion latency (hourly/daily)
* trade-offs between latency and cost

---

# Task 13 - Scalability Design

Explain:

* scaling Kafka consumers
* scaling Airflow workers
* handling increasing satellite streams
* handling burst ingestion events (launch events)

---

# Task 14 - Security in Ingestion

Define:

* API authentication handling
* secure ingestion credentials
* internal network isolation
* ingestion boundary protection

---

# Task 15 - Trade-off Analysis

Explain trade-offs:

* streaming vs batch ingestion
* Kafka vs simpler queue
* push vs pull ingestion
* real vs simulated telemetry
* Airflow vs alternative orchestrators

---

# Task 16 - Architecture Decision Records (ADR)

Create at least 5 ADRs:

Examples:

* Why Kafka is used for streaming ingestion
* Why Airflow is used for batch ingestion
* Why synthetic telemetry is required
* Why MinIO is used as landing zone
* Why hybrid ingestion model is used

---

# Deliverables

Generate:

```text id="fix8b"
ingestion/

streaming/
├── kafka-design.md
├── topic-architecture.md
├── producer-consumer-design.md

batch/
├── airflow-design.md
├── dag-structure.md
├── scheduling-strategy.md

api/
├── nasa-ingestion.md
├── noaa-ingestion.md
├── retry-rate-limit.md

file/
├── minio-layout.md
├── file-ingestion-strategy.md

simulation/
├── telemetry-generator.md
├── orbit-simulator.md

landing-zone/
├── bronze-zone.md
├── staging-zone.md

quality/
├── validation-rules.md
├── quarantine-strategy.md

docs/ingestion/

01-overview.md
02-streaming-design.md
03-batch-design.md
04-api-ingestion.md
05-file-ingestion.md
06-simulation.md
07-landing-zone.md
08-schema-strategy.md
09-data-quality.md
10-error-handling.md
11-observability.md
12-latency.md
13-scalability.md
14-security.md
15-trade-offs.md
16-adr.md
17-glossary.md
```

---

# Documentation Standards

* Enterprise-grade Markdown
* Include Mermaid diagrams for:

  * Kafka flow
  * Airflow DAG flow
  * End-to-end ingestion pipeline
* Include tables for topic design
* Include failure scenarios matrix
* Explicit assumptions required

---

# Acceptance Criteria

This phase is complete only if:

* Streaming ingestion is fully designed
* Batch ingestion is fully designed
* API ingestion is defined
* File ingestion is defined
* Synthetic data generation is included
* Landing zones are defined
* Error handling is production-grade
* Observability is included
* System is feasible for 16GB local environment

---

# Definition of Done

This phase is complete when:

> A data engineering team can implement ingestion pipelines directly from this design without asking any clarification questions.

Stop after completing this phase. Do NOT proceed to transformation or modeling.

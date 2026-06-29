# Prompt 11 - Serving Layer Design

# Enterprise Space Mission Data & AI Platform

> **Phase 11 - Serving Layer (Analytics, APIs & Data Products)**

---

# Objective

You are acting as:

* Principal Data Architect
* Analytics Platform Architect
* Data Product Architect
* API Architect
* Enterprise Solution Architect

Your task is to design the complete **Serving Layer** of the Space Mission Data & AI Platform.

The Serving Layer is responsible for exposing trusted, curated, and governed data to:

* BI dashboards
* APIs
* Data scientists
* AI/ML pipelines
* LLM/RAG systems
* External applications
* Internal engineering teams

This is an IMPLEMENTATION phase: build runnable serving artifacts plus supporting docs.

---

# Critical Rules

* This is an IMPLEMENTATION phase: build serving tables, materialized views, and data products
* Implement semantic layer + serving SQL/dbt models; APIs may be stubbed for Phase 16
* Align with previous phases; open-source only; Docker Desktop (16GB RAM); provide tests

---

# Context

The platform currently contains:

* Bronze Layer
* Silver Layer
* Gold Layer
* Data Quality Framework

Trusted Gold datasets are now ready to be consumed.

---

# Task 1 - Serving Layer Overview

Explain:

* Purpose of the Serving Layer
* Data Product philosophy
* Self-service analytics
* Data consumers
* Enterprise serving principles

Include Mermaid architecture.

---

# Task 2 - Data Products

Define the platform Data Products.

Create products such as:

## Satellite Operations

* Satellite Health Summary
* Satellite Availability
* Telemetry KPI

---

## Mission Operations

* Mission Timeline
* Mission Status
* Mission Success Metrics

---

## Launch Analytics

* Launch Performance
* Launch Delays
* Launch Success Rate

---

## Space Weather

* Solar Activity
* Radiation Index
* Weather Impact

---

## Earth Observation

* Image Metadata
* Coverage Metrics
* Observation Catalog

For every product define:

* Purpose
* Owner
* Consumers
* Refresh frequency
* SLA
* Source datasets
* KPIs

---

# Task 3 - Semantic Layer

Design a semantic layer.

Define:

* Business-friendly naming
* Metric definitions
* Standard dimensions
* Standard measures
* KPI catalogue

Explain:

* Why semantic consistency matters

---

# Task 4 - Serving Models

Design serving models for:

* BI
* APIs
* ML
* RAG

Define:

* Wide tables
* Aggregated tables
* Time-series views
* Snapshot tables
* Materialized views

---

# Task 5 - API Serving Design

Design API architecture.

Define:

* REST APIs
* Versioning strategy
* Pagination
* Filtering
* Search
* Authentication (conceptual)

Create example endpoints:

* /satellites
* /missions
* /launches
* /telemetry
* /weather
* /analytics

---

# Task 6 - BI Consumption Layer

Design BI architecture.

Include:

* Apache Superset
* Dataset strategy
* Dashboard organization
* KPI management
* User groups

Explain:

* Executive dashboards
* Operations dashboards
* Engineering dashboards
* AI dashboards

---

# Task 7 - AI Data Serving

Design datasets exposed for:

* ML training
* Batch inference
* Online inference
* Feature Store consumption

Explain:

* Offline datasets
* Online datasets
* Feature serving strategy

---

# Task 8 - LLM / RAG Serving

Define knowledge serving layer.

Include:

* Documents
* Telemetry summaries
* Mission documentation
* Incident reports
* Operational runbooks

Explain:

* What should be indexed
* Chunking strategy
* Metadata strategy
* Retrieval boundaries

---

# Task 9 - Data Access Strategy

Define:

* Internal consumers
* External consumers
* RBAC model
* Read-only datasets
* Sensitive datasets
* Public datasets

---

# Task 10 - Performance Strategy

Define:

* Materialized views
* Pre-computed aggregates
* Query caching
* API caching
* Dataset optimization

---

# Task 11 - Serving SLAs

Define SLAs for:

* Dashboard refresh
* API latency
* Data freshness
* Availability
* Query performance

Provide measurable targets.

---

# Task 12 - Monitoring the Serving Layer

Design monitoring for:

* API latency
* Query duration
* Dashboard performance
* Cache hit ratio
* Consumer activity
* Dataset freshness

Map conceptual metrics to:

* Prometheus
* Grafana

---

# Task 13 - Security

Define:

* Authentication
* Authorization
* Dataset permissions
* API security
* Audit logging
* Consumer isolation

---

# Task 14 - Production Incident Scenarios

Create at least 10 realistic incidents.

Examples:

* Slow dashboard
* API timeout
* Corrupted Gold table
* Missing KPI
* High API latency
* Cache inconsistency
* Unauthorized access
* Broken materialized view
* Expired API token
* Stale analytics

For each provide:

* Symptoms
* Root cause
* Detection
* Resolution
* Preventive actions

---

# Task 15 - Trade-off Analysis

Explain trade-offs:

* Live queries vs materialized views
* API-first vs direct SQL
* Wide tables vs normalized serving models
* Cached vs real-time responses

---

# Task 16 - Architecture Decision Records (ADR)

Create at least five ADRs.

Examples:

* Why Gold Layer is the serving source
* Why semantic layer is required
* Why APIs are versioned
* Why materialized views are used
* Why data products are defined

---

# Deliverables

Generate:

```text
serving/
sql/                serving tables, aggregates, materialized views
dbt/                semantic + serving models
tests/              data product + view tests

products/
├── satellite-products.md
├── mission-products.md
├── launch-products.md
├── weather-products.md
├── observation-products.md

semantic/
├── semantic-model.md
├── kpi-catalog.md

api/
├── api-design.md
├── endpoint-catalog.md

bi/
├── dashboard-design.md
├── dataset-catalog.md

llm/
├── rag-serving.md
├── knowledge-index.md

monitoring/
├── serving-monitoring.md
├── serving-slas.md

incidents/
├── production-incidents.md

docs/serving/

01-overview.md
02-data-products.md
03-semantic-layer.md
04-serving-models.md
05-api-design.md
06-bi-layer.md
07-ai-serving.md
08-rag-serving.md
09-data-access.md
10-performance.md
11-slas.md
12-monitoring.md
13-security.md
14-production-incidents.md
15-trade-offs.md
16-adr.md
17-glossary.md
```

---

# Documentation Standards

* Enterprise-grade Markdown
* Include Mermaid diagrams
* Include API sequence diagrams
* Include serving architecture diagrams
* Include KPI catalog tables
* Include SLA matrices
* Clearly document assumptions

---

# Acceptance Criteria

This phase is complete only if:

* Data Products are fully defined
* Semantic Layer is documented
* API architecture is complete
* BI serving strategy is complete
* AI/RAG serving strategy is defined
* Monitoring and SLAs are documented
* Security and governance are addressed

---

# Definition of Done

This phase is complete when:

> Serving tables, materialized views, semantic models, and data products are built, tested, and queryable; BI, AI, and API consumers can read them directly.

Stop after completing this phase. Do NOT proceed to AI/ML implementation or application development.

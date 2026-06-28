# Prompt 03 - Solution Architecture

# Enterprise Space Mission Data & AI Platform

> **Phase 3 - Solution Architecture & System Design**

---

# Objective

You are acting as:

* Principal Cloud Architect
* Enterprise Data Architect
* Staff Data Platform Engineer
* MLOps Architect
* Security Architect

Your task is to design the **complete end-to-end architecture** of the Space Mission Data & AI Platform.

This is a **production-grade system design exercise**, not a tutorial.

---

# Critical Rules

* Do NOT write implementation code
* Do NOT configure Docker or services
* Do NOT create pipelines yet
* Do NOT focus on optimization details
* Focus ONLY on architecture and system design
* Use ONLY open-source tools
* Assume a 16 GB RAM local environment
* Build for portfolio-grade enterprise simulation

---

# Context

We are building a Space Mission Data & AI Platform inspired by:

* NASA mission systems
* ESA Earth observation systems
* MBRSC space analytics systems
* Space42 geospatial AI platforms
* Bayanat geospatial intelligence systems
* Yahsat satellite communication systems

The platform must support:

* Satellite telemetry analytics
* Earth observation analytics
* Space weather forecasting
* Launch analytics
* Orbit tracking
* AI/ML prediction systems
* LLM + RAG assistant for space data

---

# Task 1 - System Overview

Provide a high-level architecture overview:

Explain:

* System purpose
* Key capabilities
* Major subsystems
* Data flow principles
* Real-time vs batch processing strategy

---

# Task 2 - Architecture Styles

Define which architecture patterns are used:

* Data Lakehouse architecture
* Event-driven architecture
* Lambda architecture (if applicable)
* Microservices architecture
* Medallion architecture (Bronze/Silver/Gold)
* Streaming architecture

Explain why each is used.

---

# Task 3 - High-Level Architecture Diagram

Create a full system diagram using **Mermaid** including:

* Data sources
* Ingestion layer
* Streaming layer
* Storage layer
* Processing layer
* Serving layer
* AI/ML layer
* API layer
* Observability layer
* User interface layer

---

# Task 4 - Container-Level Architecture

Break down system into logical containers:

## Data Ingestion Services

## Streaming Infrastructure

## Batch Processing Engine

## Data Lakehouse Storage

## Data Warehouse Layer

## Feature Store

## Vector Database

## ML Platform

## API Layer

## BI Layer

## Monitoring Layer

Explain responsibilities of each container.

---

# Task 5 - Technology Mapping

Map each architecture layer to tools:

Example:

* Kafka → streaming ingestion
* Spark → processing engine
* MinIO → object storage
* Iceberg → table format
* Airflow → orchestration
* MLflow → model tracking
* Superset → BI layer
* Prometheus → monitoring
* Grafana → visualization
* Qdrant → vector database
* Ollama → local LLM

Explain why each tool is chosen for:

* 16 GB RAM constraint
* open-source availability
* production realism

---

# Task 6 - Data Architecture Design

Define:

* Bronze / Silver / Gold layers
* Data flow between layers
* Batch vs streaming ingestion strategy
* Schema evolution strategy
* Metadata management strategy
* Data lineage approach

Include Mermaid data flow diagrams.

---

# Task 7 - AI/ML Architecture

Design the AI system:

Include:

* Feature Store architecture
* Model training pipeline
* Model serving architecture
* LLM + RAG architecture
* Vector database usage
* Embedding pipeline
* Model registry (MLflow)

Explain:

* How telemetry becomes features
* How predictions are served
* How LLM interacts with space data

---

# Task 8 - Observability Architecture

Design full monitoring system:

Include:

* Logging architecture
* Metrics collection
* Distributed tracing
* Pipeline monitoring
* ML model monitoring
* Alerting system

Tools:

* Prometheus
* Grafana
* OpenTelemetry

---

# Task 9 - Security Architecture

Define:

* Authentication strategy
* Authorization (RBAC)
* Data encryption (at rest and in transit)
* API security
* Secret management
* Container security

---

# Task 10 - Deployment Architecture

Design local deployment using Docker:

Include:

* Docker network design
* Service communication model
* Port allocation strategy
* Resource allocation strategy (CPU/RAM limits)
* Volume management

---

# Task 11 - Scalability Design

Explain how system scales to:

* Large satellite fleets
* High-frequency telemetry streams
* Large image datasets
* Multi-mission operations

---

# Task 12 - Failure Handling Design

Define:

* Fault tolerance strategy
* Retry mechanisms
* Dead letter queues
* Data recovery strategies
* Backup approach

---

# Task 13 - Trade-off Analysis

Explain trade-offs for:

* Kafka vs simpler queue systems
* Spark vs DuckDB
* Iceberg vs Delta Lake
* PostgreSQL vs distributed warehouses
* Local LLM vs cloud LLM

---

# Task 14 - Architecture Decision Records (ADR)

Create at least 5 ADRs:

Examples:

* Why Kafka is used
* Why Iceberg is used
* Why MinIO is used
* Why local-first architecture is chosen
* Why medallion architecture is used

---

# Deliverables

Generate:

```text id="m9x2qz"
architecture/

01-system-overview.md
02-architecture-patterns.md
03-high-level-architecture.md
04-container-architecture.md
05-technology-mapping.md
06-data-architecture.md
07-ai-ml-architecture.md
08-observability-architecture.md
09-security-architecture.md
10-deployment-architecture.md
11-scalability-design.md
12-failure-handling.md
13-trade-offs.md
14-adr.md
15-glossary.md
```

---

# Documentation Standards

* Use enterprise-grade Markdown
* Include multiple Mermaid diagrams
* Include tables for system mapping
* Include clear separation of concerns
* Include assumptions explicitly
* Include reasoning for every design decision

---

# Acceptance Criteria

This phase is complete only if:

* Full end-to-end architecture is defined
* At least 5 Mermaid diagrams are included
* All system layers are mapped to tools
* AI/ML architecture is clearly defined
* Observability is fully designed
* Security architecture is included
* Deployment strategy is feasible for 16GB laptop

---

# Definition of Done

This phase is complete when:

> A senior engineering team can start infrastructure implementation without asking any architectural questions.

Stop after completing this phase. Do NOT proceed to implementation.

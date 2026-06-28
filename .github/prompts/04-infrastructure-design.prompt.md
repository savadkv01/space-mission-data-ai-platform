# Prompt 04 - Infrastructure Design (Docker Local Platform)

# Enterprise Space Mission Data & AI Platform

> **Phase 4 - Infrastructure Design for Local Deployment**

---

# Objective

You are acting as:

* Senior DevOps Architect
* Platform Engineer
* Site Reliability Engineer (SRE)
* Cloud Infrastructure Engineer
* Data Platform Engineer

Your task is to design a **fully deployable local infrastructure platform** using Docker Desktop that supports the architecture defined in Phase 3.

This is NOT implementation.

This is a **complete infrastructure blueprint for engineering execution**.

---

# Critical Rules

* Do NOT write application code
* Do NOT build pipelines
* Do NOT configure DAGs or jobs
* Do NOT implement services
* Focus ONLY on infrastructure design
* Must be optimized for **16 GB RAM laptop**
* Must use **Docker Compose only (no Kubernetes)**
* Must use **open-source tools only**

---

# Context

We are building a Space Mission Data & AI Platform supporting:

* Satellite telemetry ingestion
* Earth observation analytics
* Space weather monitoring
* Launch analytics
* AI/ML pipelines
* LLM + RAG system
* Observability + monitoring
* BI dashboards

This platform must simulate real enterprise systems using local infrastructure.

---

# Task 1 - Infrastructure Overview

Define:

* Local platform architecture philosophy
* Why Docker-first approach is used
* Resource constraints strategy (CPU/RAM optimization)
* Service grouping strategy

---

# Task 2 - Docker System Design

Design the complete Docker-based system:

Include:

## 1. Docker Network Architecture

* internal networks
* isolated service groups
* communication patterns

## 2. Container Groups

Group services into:

* ingestion stack
* processing stack
* storage stack
* AI/ML stack
* observability stack
* BI stack

---

# Task 3 - Service Mapping

Map architecture components to containers:

Example:

### Data Ingestion Layer

* Kafka
* Kafka UI
* REST ingestion service

### Processing Layer

* Spark Master
* Spark Worker
* dbt container

### Storage Layer

* MinIO
* PostgreSQL
* Iceberg metadata store

### AI/ML Layer

* MLflow
* Jupyter
* Feature store service
* Qdrant

### Observability Layer

* Prometheus
* Grafana
* OpenTelemetry collector

### BI Layer

* Apache Superset

### LLM Layer

* Ollama
* Open WebUI

---

# Task 4 - Docker Compose Design

Define:

* multi-compose structure strategy
* service dependencies
* startup order
* health checks
* restart policies

Include:

* base compose file
* environment-specific overrides (dev/local)

---

# Task 5 - Resource Optimization Strategy

Define how system fits into:

* 16 GB RAM
* limited CPU
* local SSD constraints

Include:

* memory limits per container
* CPU limits
* scaling strategy (local scale-down design)
* disabling heavy components when needed

---

# Task 6 - Storage Infrastructure Design

Define:

* MinIO bucket structure
* PostgreSQL schemas
* Iceberg table storage layout
* metadata storage strategy
* backup strategy

---

# Task 7 - Networking Design

Define:

* internal Docker networks
* exposed ports strategy
* API gateway strategy (if any)
* service discovery approach
* inter-service communication rules

---

# Task 8 - Security Design (Local Environment)

Define:

* environment variable strategy
* secrets management (local-safe)
* API key handling
* access control design (lightweight RBAC simulation)

---

# Task 9 - Observability Infrastructure

Define:

* logging pipeline (centralized logs)
* metrics pipeline (Prometheus)
* visualization (Grafana dashboards)
* tracing (OpenTelemetry)

Include:

* what each service emits
* how logs are collected
* how metrics flow

---

# Task 10 - Data Infrastructure Readiness

Define infrastructure required for:

* streaming ingestion (Kafka)
* batch ingestion (Airflow)
* transformations (Spark + dbt)
* data validation (Great Expectations)
* ML tracking (MLflow)

---

# Task 11 - AI/ML Infrastructure

Define infrastructure for:

* model training (Jupyter / Spark ML)
* model registry (MLflow)
* feature store (Feast)
* vector database (Qdrant)
* LLM runtime (Ollama)
* RAG pipeline support

---

# Task 12 - Deployment Strategy

Define:

* how system is started locally
* bootstrap order
* dependency resolution
* initialization scripts
* environment setup process

---

# Task 13 - Failure Handling Strategy

Define:

* container crash recovery
* restart policies
* data persistence strategy
* volume backup strategy
* partial system failure handling

---

# Task 14 - Trade-off Analysis

Explain trade-offs:

* Kafka vs RabbitMQ
* Spark vs DuckDB
* MinIO vs local filesystem
* Superset vs lightweight BI tools
* Ollama vs cloud LLM APIs

---

# Task 15 - Architecture Decision Records (ADR)

Create at least 5 ADRs:

Examples:

* Why Docker Compose instead of Kubernetes
* Why MinIO for object storage
* Why local-first LLM approach
* Why service grouping strategy
* Why resource-limited architecture is chosen

---

# Deliverables

Generate:

```text id="p4deliver1"
infrastructure/

docker/
├── docker-compose.yml
├── docker-compose.ingestion.yml
├── docker-compose.processing.yml
├── docker-compose.storage.yml
├── docker-compose.ai.yml
├── docker-compose.observability.yml

env/
├── .env.example

scripts/
├── bootstrap.sh
├── start-platform.sh
├── stop-platform.sh
├── reset-platform.sh

configs/
├── kafka/
├── spark/
├── postgres/
├── minio/
├── prometheus/
├── grafana/

docs/infrastructure/

01-overview.md
02-docker-design.md
03-service-mapping.md
04-resource-management.md
05-networking.md
06-storage-design.md
07-observability.md
08-ai-infrastructure.md
09-security.md
10-deployment-runbook.md
11-failure-handling.md
12-trade-offs.md
13-adr.md
14-glossary.md
```

---

# Documentation Standards

* Enterprise-grade Markdown
* Include tables for container mapping
* Include Mermaid diagrams for network design
* Include startup order diagrams
* Include resource allocation tables
* Explicit assumptions

---

# Acceptance Criteria

This phase is complete only if:

* Entire infrastructure is Docker-based
* System is feasible on 16GB RAM
* All services are mapped to containers
* Full startup strategy is defined
* Observability stack is included
* AI/ML stack is included
* Failure handling is defined

---

# Definition of Done

This phase is complete when:

> A DevOps engineer can implement the entire platform using this document without needing architectural clarification.

Stop after completing this phase. Do NOT proceed to implementation.

# Prompt 07 - Infrastructure Implementation (Docker Platform Build)

# Enterprise Space Mission Data & AI Platform

> **Phase 7 - Infrastructure Implementation**

---

# Objective

You are acting as:

* Principal DevOps Engineer
* Platform Engineer
* Site Reliability Engineer (SRE)
* Data Platform Engineer

Your task is to design and implement the **complete local infrastructure foundation** of the Space Mission Data & AI Platform using **Docker Compose**.

This phase turns architectural design into a **fully runnable local platform blueprint**.

---

# Critical Rules

* You MAY define Docker Compose files
* You MAY define infrastructure configuration
* You MUST NOT implement application logic (no pipelines, no Spark jobs, no DAG code)
* You MUST NOT implement business logic
* You MUST use ONLY open-source tools
* You MUST optimize for **16 GB RAM laptop**
* Everything must run locally using Docker Desktop

---

# Context

We are building an enterprise-grade Space Data Platform that includes:

* Data ingestion (Kafka, APIs, simulation)
* Data processing (Spark, dbt)
* Storage (MinIO, PostgreSQL, Iceberg)
* Orchestration (Airflow)
* AI/ML (MLflow, Feature Store, Qdrant, Ollama)
* Observability (Prometheus, Grafana, OpenTelemetry)
* BI (Superset)
* APIs (FastAPI)

This phase focuses ONLY on infrastructure setup.

---

# Task 1 - Infrastructure Overview

Define:

* What "platform infrastructure" means in this project
* Why Docker Compose is used instead of Kubernetes
* Service grouping strategy
* Resource constraints strategy (16GB RAM optimization)

---

# Task 2 - Docker Compose Architecture

Design modular Docker Compose structure:

Define:

* docker-compose.base.yml
* docker-compose.ingestion.yml
* docker-compose.processing.yml
* docker-compose.storage.yml
* docker-compose.ai.yml
* docker-compose.observability.yml
* docker-compose.bi.yml

Explain:

* Why modular structure is used
* Dependency handling between services
* Startup sequencing strategy

---

# Task 3 - Service Definitions

Define container-level architecture:

## Ingestion Layer

* Kafka
* Kafka UI
* Schema registry (conceptual or lightweight)

## Processing Layer

* Spark master
* Spark worker
* dbt container

## Storage Layer

* MinIO
* PostgreSQL
* Iceberg metadata store (conceptual mapping)

## Orchestration Layer

* Airflow (scheduler + webserver)

## AI/ML Layer

* MLflow
* Jupyter
* Qdrant
* Ollama
* Open WebUI

## Observability Layer

* Prometheus
* Grafana
* OpenTelemetry collector

## BI Layer

* Apache Superset

---

# Task 4 - Docker Networking Design

Define:

* Internal Docker networks
* Service isolation strategy
* Communication rules between layers
* Exposed ports strategy

Include Mermaid network diagram.

---

# Task 5 - Resource Optimization Strategy

Design system to fit within:

* 16 GB RAM
* Limited CPU
* Local SSD constraints

Define:

* Memory limits per service
* CPU allocation strategy
* Services that can be disabled in "light mode"
* Startup profiles (full vs minimal)

---

# Task 6 - Storage Infrastructure Setup

Define:

* MinIO bucket structure
* PostgreSQL schema separation
* Iceberg table storage mapping
* Persistent volume strategy
* Backup strategy (local)

---

# Task 7 - Environment Configuration Strategy

Define:

* .env structure
* secrets handling (local-safe)
* configuration separation (dev vs full stack)
* parameterization strategy

---

# Task 8 - Service Dependency Strategy

Define:

* startup order
* dependency checks (health checks)
* retry mechanisms for service readiness
* initialization sequence

---

# Task 9 - Observability Infrastructure

Define:

* Logging strategy (centralized logs)
* Metrics collection (Prometheus)
* Visualization (Grafana dashboards)
* Distributed tracing (OpenTelemetry)

Explain:

* what each service emits
* how telemetry flows

---

# Task 10 - AI/ML Infrastructure Setup

Define infrastructure for:

* MLflow tracking server
* model registry
* Jupyter notebook environment
* feature store (Feast concept)
* vector database (Qdrant)
* LLM runtime (Ollama)

---

# Task 11 - Security (Local Simulation)

Define:

* environment variable protection
* API key handling
* service isolation
* network segmentation (soft security model)

---

# Task 12 - Failure Handling Strategy

Define:

* container restart policies
* data persistence guarantees
* partial system failure recovery
* volume recovery strategy

---

# Task 13 - Scalability Strategy

Explain:

* how system would scale beyond local
* how Kafka would scale
* how Spark workers scale
* how storage scaling would evolve

---

# Task 14 - Trade-off Analysis

Explain trade-offs:

* Docker Compose vs Kubernetes
* Local MinIO vs cloud object storage
* Spark local mode vs cluster mode
* Ollama local LLM vs API-based LLMs

---

# Task 15 - Architecture Decision Records (ADR)

Create at least 5 ADRs:

Examples:

* Why Docker Compose is used for local platform
* Why modular compose files are used
* Why MinIO is chosen for object storage
* Why services are grouped by domain
* Why resource-limited architecture is required

---

# Deliverables

Generate:

```text id="fix7b"
infrastructure/

docker/
├── docker-compose.base.yml
├── docker-compose.ingestion.yml
├── docker-compose.processing.yml
├── docker-compose.storage.yml
├── docker-compose.ai.yml
├── docker-compose.observability.yml
├── docker-compose.bi.yml

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
├── airflow/
├── prometheus/
├── grafana/

docs/infrastructure/

01-overview.md
02-docker-compose-architecture.md
03-service-definitions.md
04-networking.md
05-resource-management.md
06-storage-setup.md
07-env-config.md
08-service-dependency.md
09-observability.md
10-ai-infrastructure.md
11-security.md
12-failure-handling.md
13-scalability.md
14-trade-offs.md
15-adr.md
16-glossary.md
```

---

# Documentation Standards

* Enterprise-grade Markdown
* Include Mermaid diagrams for:

  * Docker network topology
  * Service dependency graph
  * Layered architecture view
* Include resource allocation tables
* Include startup sequence diagrams

---

# Acceptance Criteria

This phase is complete only if:

* Entire platform is Docker Compose based
* System runs within 16GB RAM constraints
* All services are defined with clear roles
* Networking design is defined
* Observability stack is included
* AI/ML infrastructure is included
* Startup strategy is fully defined

---

# Definition of Done

This phase is complete when:

> A DevOps engineer can execute a single bootstrap script and understand the entire system structure without asking clarifying questions.

Stop after completing this phase. Do NOT proceed to ingestion or pipeline development.

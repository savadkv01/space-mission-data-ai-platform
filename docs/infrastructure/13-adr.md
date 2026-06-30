# 13 Architecture Decision Records (ADR)

> **Phase 4 - Infrastructure Design (Docker Local Platform)**
> Document 13 of 14

## Purpose

This document records the binding infrastructure decisions for Phase 4. Each ADR follows a Context → Decision → Consequences format.

---

## ADR-001: Docker Compose instead of Kubernetes

**Status:** Accepted

**Context:** The platform must run on a single 16 GB laptop using open-source tooling. Kubernetes introduces a persistent control-plane memory cost (etcd, API server, scheduler, kubelet) of roughly 1–2 GB and significant operational complexity.

**Decision:** Use Docker Compose with a base file plus six stack-specific override files. Orchestrate startup order via `depends_on` + health checks and helper scripts.

**Consequences:**
- (+) Near-zero orchestration overhead; all RAM goes to workloads.
- (+) Declarative, reproducible, simple to operate for one engineer.
- (−) Less production-identical than K8s; no autoscaling/self-healing scheduler.
- Mitigation: container and network topology is kept K8s-portable for a future migration.

---

## ADR-002: MinIO for object storage

**Status:** Accepted

**Context:** The lakehouse needs S3-compatible object storage for Bronze/Silver/Gold and MLflow artifacts. The alternative is the local filesystem.

**Decision:** Use MinIO as a single-node S3-compatible store with dedicated buckets per medallion layer.

**Consequences:**
- (+) Cloud parity: identical S3 code paths for Iceberg, Spark, MLflow.
- (+) Clean lift-and-shift to AWS S3 / GCS later.
- (−) One additional lightweight container vs raw files.
- Mitigation: MinIO runs in the `small` resource class (~512 MB).

---

## ADR-003: Local-first LLM via Ollama

**Status:** Accepted

**Context:** The platform requires LLM inference for RAG under free, open-source, and offline constraints.

**Decision:** Run a quantized small model in Ollama locally, fronted by Open WebUI and consumed by the FastAPI RAG endpoint.

**Consequences:**
- (+) Zero cost, full privacy, offline-capable.
- (+) Complete RAG demonstration with no external dependencies.
- (−) Lower model quality than cloud APIs; ~4 GB local footprint.
- Mitigation: RAG design is provider-agnostic; a cloud LLM can be swapped in without architectural change. Ollama never peaks alongside Spark.

---

## ADR-004: Stack-based service grouping with segmented networks

**Status:** Accepted

**Context:** Running all services on one flat network and as one monolith Compose file would be hard to operate and resource-manage on constrained hardware.

**Decision:** Group services into six stacks (storage, ingestion, processing, AI/ML, observability, BI), each in its own Compose override, communicating over six segmented bridge networks with profile-based activation.

**Consequences:**
- (+) Start only the subset a task needs; control RAM precisely.
- (+) Least-privilege network zoning; smaller blast radius.
- (+) Clear mapping to Phase 3 architecture planes.
- (−) More files and networks to manage.
- Mitigation: shared base file + YAML anchors keep configuration DRY; helper scripts wrap multi-file commands.

---

## ADR-005: Resource-limited architecture with staged heavy workloads

**Status:** Accepted

**Context:** A 16 GB laptop cannot run Spark and Ollama (and everything else) at peak simultaneously.

**Decision:** Declare explicit `mem_limit`/`cpus` per container via resource-class anchors, and enforce that only one heavy engine (Spark batch **or** Ollama inference) peaks at a time, serialized through Airflow and profiles.

**Consequences:**
- (+) Predictable, stable operation within ~12 GB working budget.
- (+) No single service can starve the host.
- (−) Cannot demonstrate Spark and LLM workloads at full load concurrently.
- Mitigation: workloads are staged; profiles make subset operation trivial.

---

## ADR-006: Kafka in KRaft mode (no ZooKeeper)

**Status:** Accepted

**Context:** Kafka traditionally requires a ZooKeeper ensemble, adding ~300 MB and another failure domain.

**Decision:** Run Kafka in KRaft (combined broker+controller) mode as a single broker with bounded heap and few partitions.

**Consequences:**
- (+) ~300 MB saved; one fewer container and failure domain.
- (+) Modern, production-aligned Kafka deployment.
- (−) Single broker = no replication/HA (acceptable locally).
- Mitigation: topic logs are transient and re-ingestible.

---

## ADR-007: Single PostgreSQL with multiple schemas

**Status:** Accepted

**Context:** Airflow, MLflow, Superset, Feast, and the platform metadata/Gold layers each need a relational store. Running separate database containers for each wastes memory.

**Decision:** Run one PostgreSQL instance hosting isolated schemas (`metadata`, `gold`, `iceberg_catalog`, `airflow`, `mlflow`, `superset`, `feast`) with per-schema roles.

**Consequences:**
- (+) One database engine instead of five; major RAM savings.
- (+) Centralized backup via a single `pg_dump`.
- (−) Single point of failure for multiple services; noisy-neighbor risk.
- Mitigation: `unless-stopped` restart policy, health checks, and the `medium` resource class; PostgreSQL is a backup-critical store.

## ADR Index

| ADR | Decision |
| --- | --- |
| ADR-001 | Docker Compose over Kubernetes |
| ADR-002 | MinIO for object storage |
| ADR-003 | Local-first LLM via Ollama |
| ADR-004 | Stack grouping + segmented networks |
| ADR-005 | Resource limits + staged workloads |
| ADR-006 | Kafka KRaft (no ZooKeeper) |
| ADR-007 | Single PostgreSQL, multiple schemas |

## Cross References

- Trade-off analysis: [12-trade-offs.md](./12-trade-offs.md)
- Phase 3 ADRs: [../../architecture/14-adr.md](../../architecture/14-adr.md)

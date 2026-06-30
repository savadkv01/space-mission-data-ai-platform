# 12 Trade-off Analysis

> **Phase 4 - Infrastructure Design (Docker Local Platform)**
> Document 12 of 14

## Purpose

This document records the major infrastructure trade-offs, the alternatives considered, and the rationale for each decision under the 16 GB local constraint. Each decision is reflected in an ADR in [13-adr.md](./13-adr.md).

## Decision Summary

| Decision | Chosen | Alternative | Driver |
| --- | --- | --- | --- |
| Messaging | Kafka (KRaft) | RabbitMQ | Production realism, lakehouse fit |
| Batch engine | Spark + DuckDB | DuckDB only / Spark only | Realism + memory efficiency |
| Object storage | MinIO | Local filesystem | S3-compatibility, cloud parity |
| BI | Superset | Metabase / lightweight tools | Enterprise feature depth |
| LLM | Ollama (local) | Cloud LLM APIs | Cost, privacy, offline capability |
| Orchestration | Docker Compose | Kubernetes | Memory footprint, simplicity |

---

## Kafka vs RabbitMQ

| Dimension | Kafka (chosen) | RabbitMQ |
| --- | --- | --- |
| Model | Distributed log, replayable | Queue/broker, consume-once |
| Realism | Industry standard for data platforms | Common for task queues |
| Lakehouse fit | Native streaming → Bronze | Less natural for analytics |
| Memory | Higher (mitigated by KRaft) | Lower |
| Replay/backfill | Strong (offset-based) | Limited |

**Decision:** Kafka in **KRaft mode** (no ZooKeeper) gives a realistic, replayable streaming backbone while removing ~300 MB of ZooKeeper overhead. RabbitMQ's lower footprint does not justify losing log replay and ecosystem fit.

**Trade-off accepted:** higher baseline memory than RabbitMQ, controlled via single-broker + few partitions + bounded heap.

---

## Spark vs DuckDB

| Dimension | Spark (chosen for heavy) | DuckDB (chosen for light) |
| --- | --- | --- |
| Scale | Large/distributed | Single-node, in-process |
| Memory | High | Very low |
| Realism | Enterprise ETL standard | Modern embedded analytics |
| Setup | Heavier | Trivial |

**Decision:** Use **both**. Spark demonstrates real distributed ETL and reprocessing; DuckDB handles small analytical tasks in Jupyter to conserve memory. Heavy Spark jobs run one at a time.

**Trade-off accepted:** two engines to maintain, justified by realism + efficiency. Not Spark-only (too heavy for routine small jobs) and not DuckDB-only (misses distributed-processing demonstration).

---

## MinIO vs Local Filesystem

| Dimension | MinIO (chosen) | Local filesystem |
| --- | --- | --- |
| API | S3-compatible | POSIX |
| Cloud parity | High (lift-and-shift to S3) | Low |
| Iceberg fit | Native S3 | Requires adaptation |
| Overhead | One lightweight container | None |

**Decision:** MinIO. The S3 API mirrors cloud object storage, lets Iceberg/Spark/MLflow use the same code paths they would in production, and adds minimal overhead.

**Trade-off accepted:** a small container vs raw filesystem simplicity — worth it for cloud-realistic patterns and a clean migration path.

---

## Superset vs Lightweight BI Tools

| Dimension | Superset (chosen) | Metabase / lightweight |
| --- | --- | --- |
| Features | Rich SQL Lab, RBAC, many charts | Simpler, faster setup |
| Memory | ~1 GB | Lower |
| Enterprise realism | High | Moderate |

**Decision:** Superset for enterprise-grade dashboards, native RBAC, and SQL Lab. It best represents a real BI layer for a portfolio platform.

**Trade-off accepted:** higher memory than Metabase; acceptable since BI is started on-demand and runs without a concurrent Spark/Ollama peak.

---

## Ollama vs Cloud LLM APIs

| Dimension | Ollama (chosen) | Cloud LLM APIs |
| --- | --- | --- |
| Cost | Free, local | Per-token billing |
| Privacy | Fully local | Data leaves machine |
| Offline | Yes | No |
| Quality | Smaller quantized models | State-of-the-art models |
| Memory | ~4 GB | ~0 (remote) |

**Decision:** Ollama with a quantized small model. It satisfies the open-source + free + local constraints and demonstrates a complete RAG stack without external dependencies or cost.

**Trade-off accepted:** lower model quality and a 4 GB local footprint vs cloud APIs. The platform's RAG design is API-agnostic, so a cloud provider can be swapped in later without architectural change.

---

## Docker Compose vs Kubernetes

| Dimension | Compose (chosen) | Kubernetes |
| --- | --- | --- |
| Control-plane RAM | ~0 | ~1–2 GB (etcd, API, kubelet) |
| Complexity | Low | High |
| Local fit | Excellent | Poor on 16 GB |
| Production realism | Moderate | High |

**Decision:** Docker Compose. On a 16 GB laptop, Kubernetes' control-plane tax is unjustifiable and irrelevant to demonstrating data/AI engineering. Compose provides reproducible, declarative orchestration with near-zero overhead.

**Trade-off accepted:** less production-identical orchestration. The container/network design is intentionally K8s-portable for a future migration.

## Cross References

- ADRs: [13-adr.md](./13-adr.md)
- Phase 3 trade-offs: [../../architecture/13-trade-offs.md](../../architecture/13-trade-offs.md)
- Resource management: [04-resource-management.md](./04-resource-management.md)

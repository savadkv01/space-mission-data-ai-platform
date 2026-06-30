# 18 - Architecture Decision Records (ADR)

> **Phase 9 - Data Transformation** · Document 18 of 19

Format: Context · Decision · Alternatives · Consequences.

---

## ADR-1 — Apache Spark as the core transformation engine

- **Context:** Need batch + streaming, scale from laptop to cluster, rich connectors (Kafka, MinIO, Parquet).
- **Decision:** Use Spark for Bronze→Silver cleaning/conformance, large joins, and structured streaming.
- **Alternatives:** Flink (streaming-first, second framework for batch); pandas (no scale); Beam (heavier).
- **Consequences:** One engine/API for both paths; requires a JDK; `local[*]` fits 16 GB. Pure-Python rule core keeps logic testable without Spark.

## ADR-2 — dbt for the Gold layer

- **Context:** Gold is SQL aggregation + KPIs that analysts should own and test.
- **Decision:** Build all Silver→Gold marts in dbt; tests as quality gates; DuckDB locally, Trino/Spark-SQL in prod.
- **Alternatives:** Spark SQL only (no testing/lineage ergonomics); hand-written SQL scripts (no DAG/tests).
- **Consequences:** Free lineage + tests + docs; SQL accessible to analysts; one extra tool. KPI definitions duplicated in Python for the offline path — kept in sync by shared tests.

## ADR-3 — Enforce Medallion (Bronze → Silver → Gold)

- **Context:** Need reproducibility, clear contracts, and a single source of clean data.
- **Decision:** Strict layering; Gold never reads Bronze; Silver is the clean source of truth.
- **Alternatives:** Direct Bronze→Gold (fast but unauditable); two-layer model.
- **Consequences:** Clear contracts + replayability; minor extra storage/compute for Silver.

## ADR-4 — Hybrid streaming + batch

- **Context:** Live dashboards need seconds; analytics need correctness despite late data.
- **Decision:** Streaming produces low-latency approximate rollups; nightly batch is authoritative and overwrites them.
- **Alternatives:** Streaming-only (late-data correctness hard); batch-only (no live view).
- **Consequences:** Best of both; reconciliation logic + provenance flag required.

## ADR-5 — Feature engineering inside the transformation layer

- **Context:** Features are transformations of Silver; train/serve skew must be avoided.
- **Decision:** Compute features from Silver with deterministic, windowed, versioned rules; one feature dataset reused across models.
- **Alternatives:** Feature logic inside model training (skew, duplication); separate feature platform (overkill on a laptop).
- **Consequences:** One lineage graph, no skew, reuse across models; feature store remains lightweight.

## ADR-6 — Pure-Python rule core, infra-free + tested

- **Context:** Infrastructure (Spark/Kafka/MinIO) is not always available; logic must be testable.
- **Decision:** Canonical cleaning/transform/feature rules in pure Python; Spark/dbt wrap the same rules.
- **Alternatives:** Spark-only (needs Java for every test; slow CI).
- **Consequences:** Fast unit tests, runs anywhere, zero batch/stream drift; thin wrappers needed for Spark.

## Cross References

- [17-trade-offs.md](17-trade-offs.md) · [architecture/14-adr.md](../../architecture/14-adr.md) · [data-modeling/17-adr.md](../data-modeling/17-adr.md)

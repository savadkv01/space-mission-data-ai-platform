# 15 — Architecture Decision Records (ADR)

> Decisions specific to the data quality framework. Format follows the platform
> ADR convention (Status / Date / Context / Decision / Alternatives / Trade-offs)
> used in [architecture/14-adr.md](../../architecture/14-adr.md) and
> [docs/data-modeling/17-adr.md](../../docs/data-modeling/17-adr.md).

---

## ADR-DQ-01: Medallion quality gates

- **Status:** Accepted
- **Date:** 2026-07-01
- **Context:** Data flows Bronze → Silver → Gold before reaching BI/ML/RAG. A
  single end-of-pipeline check would detect problems too late and could not tell
  *where* corruption entered.
- **Decision:** Enforce a quality gate at every layer — Bronze (integrity +
  schema), Silver (clean/dedup/range/geo), Gold (business rules + KPI +
  reconciliation).
- **Alternatives:** single end-of-pipeline validation; validation only at
  ingestion.
- **Trade-offs:** more checkpoints to maintain, but early, localized detection
  and clear layer accountability. Accepted.

---

## ADR-DQ-02: Data profiling is mandatory

- **Status:** Accepted
- **Date:** 2026-07-01
- **Context:** Validation thresholds risk being arbitrary if not grounded in
  observed data; upstream feeds drift.
- **Decision:** Profile every dataset at ingestion and each promotion; derive
  thresholds and drift baselines from profiles.
- **Alternatives:** hand-set thresholds; ad-hoc profiling on incident only.
- **Trade-offs:** compute cost (mitigated by sampling on large partitions), in
  exchange for data-driven thresholds and early drift detection. Accepted.

---

## ADR-DQ-03: Quarantine zone preferred over rejection

- **Status:** Accepted
- **Date:** 2026-07-01
- **Context:** In aerospace/EO, an out-of-range record may be the most important
  signal (an anomaly), and upstream feeds are outside our control.
- **Decision:** Invalid records are quarantined with reasons (and DLQ for
  streaming), never dropped; they are replayable after a fix.
- **Alternatives:** drop invalid records; fail the whole batch on any bad record.
- **Trade-offs:** storage + triage overhead, in exchange for zero data loss,
  upstream visibility and recoverability. Accepted.

---

## ADR-DQ-04: Business-rule validation occurs in Silver and Gold

- **Status:** Accepted
- **Date:** 2026-07-01
- **Context:** Field-level validity is insufficient — domain invariants
  (identity obfuscation, AOI referential integrity, temporal ordering) span
  fields and entities.
- **Decision:** Enforce row/entity business rules at Silver and cross-entity /
  aggregate rules at Gold, using tiered severity.
- **Alternatives:** all rules at ingestion; business rules only in BI layer.
- **Trade-offs:** requires context available only after cleaning/joining, so
  business rules cannot live at Bronze; accepted for correctness.

---

## ADR-DQ-05: Continuous monitoring is required

- **Status:** Accepted
- **Date:** 2026-07-01
- **Context:** Point-in-time validation cannot catch slow drift, freshness decay
  or duplicate creep between runs.
- **Decision:** Every gate emits Prometheus metrics; profiling sets baselines;
  Alertmanager routes deviations by severity; Grafana visualizes. MTTD/MTTR are
  measured.
- **Alternatives:** manual periodic audits; logs-only, no metrics.
- **Trade-offs:** observability wiring effort, in exchange for continuous,
  measurable quality assurance. Accepted.

---

## ADR-DQ-06: Tiered (critical/warn) severity model

- **Status:** Accepted
- **Date:** 2026-07-01
- **Context:** Strict validation over-rejects; relaxed validation lets corruption
  through.
- **Decision:** Expectations carry `critical` (block/hold) or `warn`
  (log + promote) severity, mirroring the existing validation framework.
- **Alternatives:** all-or-nothing strict validation.
- **Trade-offs:** requires disciplined severity assignment per rule; accepted for
  the throughput/trust balance.

---

## ADR-DQ-07: Batch-first validation for the MVP

- **Status:** Accepted
- **Date:** 2026-07-01
- **Context:** Target environment is a 16 GB laptop, open-source only; EO feeds
  are near-real-time-to-daily, not sub-second.
- **Decision:** Validate in batch for the MVP; retain a real-time validation path
  only in the Simulation streaming track.
- **Alternatives:** real-time validation everywhere; hybrid for all datasets.
- **Trade-offs:** higher detection latency than streaming, accepted as a fit to
  the constraints and feed cadence. Aligns with data-modeling ADR-10 (plain
  Parquet, batch-first).

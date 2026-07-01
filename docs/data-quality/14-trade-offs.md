# 14 — Trade-off Analysis

> The consequential design choices in the data quality framework, with the
> alternatives considered and what each choice sacrifices. Decisions are recorded
> as ADRs in [15-adr.md](15-adr.md).

---

## 1. Reject vs quarantine bad records

| Option | Pros | Cons |
|--------|------|------|
| **Reject (drop)** | simple, no storage | data loss, unrecoverable, hides upstream issues |
| **Quarantine (chosen)** | nothing lost, replayable, upstream visibility | storage + triage cost |

**Decision:** quarantine. In an aerospace/EO context a "bad" record may be the
*most* important one (an anomaly). Loss is unacceptable; storage is cheap.
→ ADR-03.

---

## 2. Strict vs relaxed validation

| Option | Pros | Cons |
|--------|------|------|
| **Strict** | high trust, clean Gold | more quarantine, risk of over-rejection |
| **Relaxed** | high throughput | corrupt data reaches BI/ML |
| **Tiered (chosen)** | critical rules hard-fail, soft rules warn | needs severity discipline |

**Decision:** tiered severity — `critical` blocks, `warn` passes with a signal.
Balances trust and throughput. → ADR-04.

---

## 3. Real-time vs batch validation

| Option | Pros | Cons |
|--------|------|------|
| **Real-time** | earliest detection | complex, resource-heavy on 16 GB |
| **Batch (chosen for MVP)** | simple, cheap, reproducible | higher detection latency |
| **Hybrid** | best of both | most complexity |

**Decision:** batch-first for the MVP (matches the laptop constraint and the
EO feeds' cadence); the streaming track keeps a real-time path for the
demonstrator. → ADR-05.

---

## 4. Automated vs manual correction

| Option | Pros | Cons |
|--------|------|------|
| **Fully automated** | fast, scalable | risky auto-fixes can mask errors |
| **Fully manual** | careful | slow, unscalable |
| **Automated detect + gated manual fix (chosen)** | fast detection, safe correction | steward in the loop |

**Decision:** automate detection and quarantine; require steward-gated replay for
correction. Preserves safety without sacrificing detection speed.

---

## 5. Cross-cutting trade-offs

| Trade-off | Chosen stance | Sacrifice |
|-----------|---------------|-----------|
| Prevention vs correction | prevention-biased, correction retained | some upfront rule effort |
| Profiling cost vs insight | sampled profiling on large partitions | exactness on tails |
| Open-source vs managed | open-source only (GE-style, dbt, Prometheus) | manual wiring |
| Iceberg vs plain Parquet | plain Parquet for MVP (ADR-10 data-modeling) | no time-travel yet |

Each stance is a deliberate fit to the platform constraints: 16 GB RAM,
open-source only, batch-first, EO-focused MVP.

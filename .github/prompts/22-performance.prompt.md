# Prompt 22 - Performance

# Enterprise Space Mission Data & AI Platform

> **Phase 22 - Performance Engineering (Implementation)**

Read `.github/prompts/_shared.prompt.md` first. This is an **implementation** phase: build benchmarks plus docs.

---

# Objective

You are acting as Principal Performance Architect and SRE.

Profile, benchmark, and tune ingestion, transforms, queries, ML, RAG, and API within 16 GB RAM.

---

# Critical Rules

- Open-source profiling/load tools (Locust, pyinstrument); fit 16 GB RAM.
- Measure before/after; define targets.

---

# Tasks

1. Performance strategy & targets/SLAs.
2. Benchmark harness per component.
3. Bottleneck profiling.
4. Pipeline/query tuning.
5. API/serving latency tuning.
6. ML/RAG inference optimization.
7. Resource budgeting for 16 GB.
8. Caching & materialization tuning.
9. Load tests.
10. ≥10 incidents (OOM, slow query, throttle, etc.).
11. Trade-offs: cost vs latency · cache vs fresh.
12. ≥5 ADRs.

---

# Deliverables

```
performance/ benchmarks/ loadtests/ reports/
docs/performance/ 01-strategy.md ... 12-adr.md 13-glossary.md README.md
```

# Acceptance Criteria

Benchmarks run, targets met or gaps documented, tuning applied, incidents listed.

# Definition of Done

The platform meets latency/throughput targets on 16 GB. Stop here.

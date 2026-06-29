# Prompt 13 - Feature Store

# Enterprise Space Mission Data & AI Platform

> **Phase 13 - Feature Store (Implementation)**

Read `.github/prompts/_shared.prompt.md` first. This is an **implementation** phase: build working, tested, containerized code plus docs.

---

# Objective

You are acting as Principal ML Platform Architect, Staff ML Engineer, and MLOps Engineer.

Build the Feature Store that turns Gold datasets into reusable, versioned, point-in-time-correct features for training and serving across satellite, mission, launch, weather, and Earth-observation use cases.

---

# Critical Rules

- Use Feast (open-source) with Postgres for offline, online, and registry; no extra containers, no managed services.
- Reuse existing Gold tables and the serving layer; do not duplicate ingestion.
- Point-in-time correctness is mandatory; no training/serving skew.
- Provide tests, seed data, and a one-command bring-up; fit 16 GB RAM.

---

# Tasks

1. Feature store strategy: vision, online vs offline, freshness, ownership, reuse.
2. Feature definitions: entities, feature views, value types, TTL for satellite/mission/launch/weather/EO.
3. Geospatial/raster features for EO use cases (wildfire/flood/vessel): spatial aggregations, NDVI/thermal indices, scene metadata.
4. Feast project: `feature_store.yaml`, registry, Postgres offline + online, materialization jobs.
5. Training data API: point-in-time joins, dataset versioning, reproducible splits.
6. Online serving: low-latency retrieval, caching, fallback, freshness SLAs.
7. Feature pipelines: batch materialization, scheduling, backfill, monitoring.
8. Data quality & drift: validation, null/skew checks, feature drift detection.
9. Governance: feature catalog, lineage, versioning, deprecation.
10. Tests: unit + integration (offline retrieval, online lookup, PIT correctness).
11. ≥10 production incidents (stale features, skew, materialization fail, registry corruption, etc.).
12. Trade-offs: Feast vs custom · Postgres vs Redis online · batch vs streaming features.
13. ≥5 ADRs.

---

# Deliverables

```
feature_store/  feature_store.yaml, feature_repo/, materialize/, tests/
docs/feature-store/ 01-strategy.md ... 12-adr.md 13-glossary.md README.md
```

# Acceptance Criteria

Feast runs in Docker, features materialize, online + PIT offline retrieval tested, drift checks and incidents documented.

# Definition of Done

An ML engineer can register, materialize, and serve features for any use case from the repo without redesign. Stop here.

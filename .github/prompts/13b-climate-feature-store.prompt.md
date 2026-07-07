# Prompt 13b - Feature Store (Climate / Dust / Air-Quality Extension)

# Enterprise Space Mission Data & AI Platform

> **Phase 13b - Feature Store (Climate Expansion, Implementation)**

Read `.github/prompts/_shared.prompt.md` first. Extends Phase 13 (`feature_store/`). This is an **implementation** phase: build working, tested code plus docs.

---

# Objective

You are acting as Principal ML Platform Architect, Staff ML Engineer, and MLOps Engineer.

Extend the existing Feast feature store with **climate, dust, and air-quality features** sourced from the Phase 11b certified data products, keeping point-in-time correctness.

---

# Scope Guardrails

- Reuse the existing Feast project, Postgres offline/online, registry, and materialization jobs. Do NOT stand up new infrastructure.
- Source only from certified 11b products (`serving_air_quality_daily`, `serving_dust_event_daily`, `serving_climate_indicator_daily`, `serving_vegetation_health_daily`).
- Entities align to `dim_aoi` + date (same grain as existing EO features).
- No CAMS/ERA5 NetCDF or geostationary features (deferred).

---

# Tasks

1. Feature definitions: new feature views for air quality (PM2.5/PM10, NO₂, SO₂, CO, O₃, CH₄, AQI band), aerosol/dust (AOD, dust-index, dust-flag), climate indicators (LST + anomaly, NDVI/EVI, SST + anomaly, NDWI), with value types and TTL.
2. Derived/temporal features: rolling means, recency, velocity-of-change, wind-transport context (NASA POWER) for dust prediction.
3. Entities: reuse AOI entity; add pollutant/indicator join keys as needed.
4. Materialization: extend existing batch jobs + scheduling + backfill for the new views.
5. Training data API: point-in-time joins spanning EO + climate features (e.g., fire + AOD + wind).
6. Online serving: freshness SLAs for near-real-time air-quality features.
7. Data quality & drift: null/skew/drift checks on new features.
8. Governance: catalog, lineage, versioning entries for new features.
9. Tests: PIT correctness, offline retrieval, online lookup for new views.
10. Trade-offs + ≥3 ADRs (feature grain, freshness tier, batch vs streaming for AQ).

---

# Deliverables

```
feature_store/feature_repo/climate/    (new feature views/entities)
feature_store/materialize/              (extend: climate materialization)
feature_store/tests/test_climate_features.py
docs/feature-store/climate.md
```

# Acceptance Criteria

New climate/dust/air-quality feature views materialize, online + PIT offline retrieval tested, drift checks documented.

# Definition of Done

An ML engineer can retrieve climate/dust/air-quality features (with EO context) for training and serving without redesign. Stop here.

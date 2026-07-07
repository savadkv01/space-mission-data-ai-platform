# Prompt 11b - Climate & Air-Quality Serving Layer (Extension, Implementation)

# Enterprise Space Mission Data & AI Platform

> **Phase 11b - Serving Layer (Climate / Dust / Air-Quality Expansion)**
>
> Read `_shared.prompt.md` first. Extends Phase 11 (`serving/`).

---

# Objective

You are acting as:

* Staff Data Engineer
* Analytics Engineer
* Semantic-Layer / Data-Product Owner

Your task is to **expose the new Gold climate/dust/air-quality marts as governed data products**, mirroring the existing serving pattern.

This is an **IMPLEMENTATION phase**: working models + contracts + tests.

---

# Scope Guardrails

* Serve only the IN-scope marts from Phase 9b.
* Mirror the existing serving pattern exactly: pure-Python builders are canonical (`serving/marts/`), dbt models duplicate for scale (`serving/dbt/`), raw DDL in `serving/sql/`, contracts tested via dbt schema tests.
* Reuse the existing semantic layer (`dim_aoi`) and metric registry; do not fork it.

---

# Context

Existing products (`serving_wildfire_daily`, `serving_flood_daily`, etc.) are pre-denormalized, AOI-date grained, and consumed by BI/API/ML. New products must match this so consumers need no joins.

---

# Task 1 - Data Products

Build serving data products (pure-Python builders + dbt models):

* `serving_air_quality_daily` — pollutant means/max, AQI band, exceedance flag (per AOI-date)
* `serving_dust_event_daily` — AOD, dust-index, dust-flag, wind context
* `serving_climate_indicator_daily` — LST/anomaly, NDVI/EVI, SST/anomaly, NDWI, deforestation, desertification proxy
* `serving_vegetation_health_daily` — NDVI/EVI trend, crop-stress proxy

---

# Task 2 - Semantic Layer Extensions

* Add dimensions `dim_pollutant`, `dim_climate_indicator` (from Phase 6b) with business-friendly names, units, thresholds.
* Register KPIs/metrics: AQI breakpoints, AOD severity bands, LST anomaly bands, NDVI health bands.

---

# Task 3 - Materialized Aggregate

Extend or add a materialized KPI rollup (mirror `mv_kpi_platform_daily`) to include air-quality/dust/climate KPIs for the executive and weather dashboards.

---

# Task 4 - Serving Contracts

* dbt schema tests: grain uniqueness, KPI ranges, enum validation, not-null keys.
* Row-level-security considerations if any AOI is restricted (reuse existing RLS approach; likely none needed here).

---

# Task 5 - Tests

* Offline unit tests for pure-Python builders (`serving/tests/`), asserting grain, KPI math, and denormalization.
* Ensure `make test` passes.

---

# Deliverables

```text
serving/marts/climate/                 (pure-Python builders)
serving/dbt/models/climate/            (dbt serving models)
serving/sql/climate/                   (raw DDL)
serving/semantic/                      (extend: dim_pollutant, dim_climate_indicator, KPIs)
serving/products/                      (extend: product registry)
serving/tests/test_climate_products.py
docs/serving/climate-products.md
```

---

# Critical Rules

* Implementation phase: products build, contracts + tests pass.
* Mirror existing serving pattern; reuse semantic layer.
* Do NOT build BI dashboards (Phase 12b) or REST API (Phase 16).

---

# Acceptance Criteria

Complete only if:

* All 4 products build at AOI-date grain, pre-denormalized
* Semantic dims + KPIs registered
* dbt contracts + unit tests pass

---

# Definition of Done

> Certified climate/dust/air-quality data products are queryable and contract-tested, ready for BI (12b), API (16), and ML (14).

Stop after this phase. Do NOT build dashboards.

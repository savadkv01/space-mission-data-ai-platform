# Prompt 09b - Climate & Air-Quality Transformation (Extension, Implementation)

# Enterprise Space Mission Data & AI Platform

> **Phase 9b - Data Transformation (Climate / Dust / Air-Quality Expansion)**
>
> Read `_shared.prompt.md` first. Extends Phase 9 (`transformation/`).

---

# Objective

You are acting as:

* Staff Data Engineer
* Lakehouse / Spark Engineer
* Geospatial & Time-Series Specialist

Your task is to **implement Bronze → Silver → Gold transformations** for the new climate/dust/air-quality entities defined in Phase 6b.

This is an **IMPLEMENTATION phase**: working, tested code.

---

# Scope Guardrails

* Transform only the IN-scope entities: air quality, aerosol/dust, atmospheric columns, and derived climate indicators.
* **Reuse existing engines** — do NOT create new frameworks:
  * `transformation/geospatial/` for AOI/raster→vector aggregation
  * `transformation/timeseries/` for rolling windows, anomaly, trend
  * `transformation/features/` patterns where relevant
* Pure-Python transformation rules are canonical + unit-tested (offline); Spark/dbt entrypoints mirror them for scale (existing convention).
* Do NOT handle NetCDF/gridded CAMS/ERA5 or geostationary (deferred).

---

# Context

Existing marts (`wildfire`, `flood`) are built by pure-Python rule modules plus dbt models. New marts must land at the same **AOI-date grain** and reuse `dim_aoi` so cross-domain joins (fire + smoke + air quality) work directly.

---

# Task 1 - Bronze → Silver Cleaning

Implement cleaning/conforming for:

* `obs_air_quality` — unit standardization (µg/m³), quality-flag filtering, station→AOI tagging, dedup
* `obs_aerosol` — AOD validity filtering, AOI/day aggregation
* `obs_atmos_column` — trace-gas column harmonization per AOI/day

Reuse geospatial point-in-polygon for AOI tagging.

---

# Task 2 - Derived Climate Indicators (from Existing Silver)

Implement index derivations using already-ingested data (no new ingestion):

* NDVI / EVI, NDWI (from Sentinel-2/MODIS index stats)
* LST + LST anomaly (from MODIS/Landsat thermal)
* SST + anomaly (from NOAA OISST)
* Desertification proxy (NDVI trend + LST) and deforestation (Global Forest Watch)

Use `timeseries` module for anomalies and trends.

---

# Task 3 - Silver → Gold Marts

Build the Gold facts from Phase 6b at AOI-date grain:

* `fact_air_quality_daily`
* `fact_dust_event_daily` (AOD + dust-index + wind context from NASA POWER)
* `fact_climate_indicator_daily`
* `fact_vegetation_health_daily`

Compute KPI columns and exceedance/severity flags per the Phase 6b registry.

---

# Task 4 - Feature-Ready Outputs

Emit feature-friendly columns (recency, rolling means, velocity of change) so Phase 13 feature store can consume without recomputation.

---

# Task 5 - Orchestration

* Add DAG tasks to the existing transformation pipeline (`transformation/orchestration/dags/`) for the new marts, with SLA + dependency on 8b ingestion.

---

# Task 6 - Tests

* Offline unit tests for each pure-Python rule module (unit conversions, anomaly logic, dust-flag thresholds, AOI tagging), following `transformation/tests/` conventions.
* Ensure `make test` passes.

---

# Deliverables

```text
transformation/cleaning/climate/            (air quality, aerosol, atmos cleaning)
transformation/batch/climate_bronze_to_silver.py
transformation/batch/climate_silver_to_gold.py
transformation/timeseries/climate_indicators.py
transformation/dbt/models/climate/          (dbt marts mirroring Python rules)
transformation/orchestration/dags/          (extend: climate tasks)
transformation/tests/test_climate_*.py
docs/transformation/climate-marts.md
```

---

# Critical Rules

* Implementation phase: code runs, tests pass.
* Reuse geospatial/timeseries engines; no new frameworks.
* Do NOT design serving products (Phase 11b).

---

# Acceptance Criteria

Complete only if:

* All new Silver entities and Gold marts build at AOI-date grain
* Derived indicators produced from existing sources (no new ingestion)
* Offline unit tests pass; DAG tasks wired

---

# Definition of Done

> New Gold climate/dust/air-quality marts exist and rebuild reproducibly from Bronze, ready for serving (11b), feature store (13), and BI (12b).

Stop after this phase. Do NOT build serving products.

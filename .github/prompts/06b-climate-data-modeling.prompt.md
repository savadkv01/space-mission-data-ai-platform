# Prompt 06b - Climate & Air-Quality Data Modeling (Extension)

# Enterprise Space Mission Data & AI Platform

> **Phase 6b - Data Modeling (Climate / Dust / Air-Quality Expansion)**
>
> Read `_shared.prompt.md` first. Extends Phase 6 (`docs/data-modeling/`).

---

# Objective

You are acting as:

* Principal Data Architect
* Data Modeler
* Lakehouse / Dimensional Modeling Specialist

Your task is to define the **Bronze → Silver → Gold data model** for the new climate, dust, and air-quality domain, consistent with the existing Phase 6 modeling contracts.

This is a **design phase**: produce schemas and contracts only, no code.

---

# Scope Guardrails

* Model only the IN-scope sources from Phase 5b: OpenAQ, TROPOMI (stats), MODIS/VIIRS AOD, and derived climate indicators.
* All Bronze records MUST fit the existing **record-oriented JSONL envelope** (`ingestion/common/envelope.py` — `BronzeEnvelope`). No binary/NetCDF entities.
* Reuse existing modeling patterns: mirror `obs_index` / `obs_scene` (Silver) and the `*_daily` fact marts (Gold) used by wildfire/flood.
* Do NOT model CAMS/ERA5 gridded data or geostationary (deferred).

---

# Context

Existing marts follow an AOI-date grain (`serving_wildfire_daily`, `serving_flood_daily`). New marts must align to the same `dim_aoi` and date dimensions so cross-domain joins are trivial (e.g., fire + smoke + air quality per AOI-day).

---

# Task 1 - Bronze Layer Contracts

Define Bronze record shapes (payload schema inside the standard envelope) for:

* `obs_air_quality_raw` (OpenAQ station readings)
* `obs_atmos_raw` (TROPOMI per-AOI statistical buckets: NO₂, SO₂, CO, O₃, CH₄, aerosol index)
* `obs_aerosol_raw` (MODIS/VIIRS AOD per-AOI/point)

For each: field list, types, source event timestamp, provenance columns inherited from the envelope, partitioning (`ingest_date`).

---

# Task 2 - Silver Layer Entities

Define cleaned/conformed Silver entities:

* `obs_air_quality` — harmonized pollutant readings (unit-standardized, quality-flag filtered, AOI-tagged)
* `obs_aerosol` — AOD + UV aerosol index per AOI per day
* `obs_atmos_column` — trace-gas column densities per AOI per day

Specify: keys, deduplication logic, unit standardization rules, quality-flag handling, spatial tagging to `dim_aoi`, schema-evolution notes.

---

# Task 3 - Gold Marts (Business-Ready)

Define new Gold fact marts at **AOI-date grain**, consistent with existing facts:

* `fact_air_quality_daily` — pollutant means/maxes, AQI bands, exceedance flags
* `fact_dust_event_daily` — AOD, dust-index, wind-transport context, dust-flag
* `fact_climate_indicator_daily` — LST/LST-anomaly, NDVI/EVI, SST/anomaly, NDWI, deforestation, desertification proxy (from existing sources)
* `fact_vegetation_health_daily` — NDVI/EVI trend, crop-stress proxy

For each: grain statement, dimensions, measures, derived KPIs, source lineage.

---

# Task 4 - Dimensions & Conformance

Define / extend shared dimensions:

* `dim_aoi` (reuse existing — confirm the new AOIs from Phase 5b are added)
* `dim_pollutant` (NO₂, SO₂, CO, O₃, CH₄, PM2.5, PM10, AOD — with units, AQI breakpoints, thresholds)
* `dim_climate_indicator` (indicator code, unit, normal range, anomaly bands)

Document conformance to the existing semantic layer.

---

# Task 5 - KPI & Threshold Definitions

Define the metric registry entries (for later serving/BI):

* PM2.5 / PM10 AQI breakpoints
* AOD dust-severity bands
* LST anomaly bands (°C above baseline)
* NDVI health bands
* Data-quality thresholds (valid-pixel fraction, station coverage)

---

# Task 6 - Lineage & Schema Evolution

* Bronze → Silver → Gold lineage diagram (Mermaid)
* Schema-evolution strategy for added pollutants/indicators
* Reproducibility notes (how marts rebuild from Bronze)

---

# Deliverables

```text
docs/data-modeling/climate/

01-bronze-contracts.md
02-silver-entities.md
03-gold-marts.md
04-dimensions-conformance.md
05-kpi-thresholds.md
06-lineage-schema-evolution.md
07-glossary.md
```

---

# Documentation Standards

* Schema tables, grain statements, Mermaid lineage
* Explicit alignment to existing `dim_aoi` and `*_daily` fact patterns

---

# Acceptance Criteria

Complete only if:

* Bronze/Silver/Gold contracts defined for all IN-scope sources
* New marts align to AOI-date grain and existing dimensions
* `dim_pollutant` and `dim_climate_indicator` fully specified with thresholds
* Lineage and schema-evolution documented

---

# Definition of Done

> Ingestion (8b), transformation (9b), and serving (11b) teams can implement without further modeling questions.

Stop after this phase. Do NOT write ingestion or transformation code.

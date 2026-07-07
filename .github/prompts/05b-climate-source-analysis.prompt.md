# Prompt 05b - Climate & Air-Quality Source Data Analysis (Extension)

# Enterprise Space Mission Data & AI Platform

> **Phase 5b - Source Data Analysis (Climate / Dust / Air-Quality Expansion)**
>
> Read `_shared.prompt.md` first. Extends Phase 5 (`docs/source-data-analysis/`).

---

# Objective

You are acting as:

* Data Architect
* Data Analyst
* Atmospheric / Earth-Observation Domain Expert
* Data Governance Specialist

Your task is to perform a **deep technical analysis of the new atmospheric and climate data sources** required to add Climate Change, Dust Storm, and Air-Quality monitoring to the platform.

This phase is about **data understanding only** — structure, behavior, limitations, usability — not ingestion design or code.

---

# Scope Guardrails (NON-NEGOTIABLE)

This is a **light expansion**. Include only sources that fit the existing tabular/statistical-API ingestion pattern.

* **IN scope (Strategy A — tabular / stats API):**
  * OpenAQ (ground-station air quality)
  * Sentinel-5P / TROPOMI atmospheric products via **Sentinel Hub Statistical API** (NO₂, SO₂, CO, O₃, CH₄, UV Aerosol Index)
  * MODIS / VIIRS Aerosol Optical Depth (AOD) via point/stats access
  * Climate indicators **derivable from already-ingested sources** (MODIS/Landsat LST, Sentinel-2/MODIS NDVI, NOAA OISST SST, Global Forest Watch) — no new ingestion
* **OUT of scope (heavy / deferred — do NOT analyze for adoption):**
  * CAMS and ERA5 **raw NetCDF** (require a new binary blob-landing capability)
  * Geostationary SEVIRI / Himawari (violates the 16 GB / Docker budget)
  * Note these explicitly in the future-expansion section as deferred, with rationale.

Do NOT design ingestion pipelines, architecture, or code in this phase.

---

# Context

The platform already ingests (Phase 5/8) FIRMS, Sentinel-1/2, Landsat, MODIS, NASA POWER, Global Forest Watch, NOAA OISST, and maritime AIS/GFW. This extension adds the **atmospheric column** that is currently missing, unlocking the highest-value UAE use cases: dust storms and air quality.

New use cases to support:

* Climate change monitoring (LST, vegetation health, urban heat, SST, deforestation, desertification, water availability)
* Dust storm monitoring (aerosol concentration, plume proxy, PM estimation, wind-driven transport)
* Air-quality monitoring (NO₂, SO₂, CO, O₃, CH₄, AOD)

---

# Task 1 - New Dataset Inventory

Add rows to the Phase 5 inventory for each IN-scope source. For each provide:

* Dataset Name and Source Organization
* Data Format and access method (API / Statistical API / point query)
* High-level schema (fields / bands / pollutants)
* Granularity and Update Frequency
* Historical Coverage
* Geospatial Coverage
* Data Volume Estimate (per AOI, per day)
* API Limitations (rate limits, auth, quotas)
* Reliability Score (High / Medium / Low)

---

# Task 2 - Area-of-Interest (AOI) Strategy

Define the AOI-bounded ingestion strategy required to respect the 16 GB budget:

* Primary AOIs: UAE (national) + key sub-regions (Abu Dhabi, Dubai, coastal zone, desert interior)
* Secondary AOIs: regional dust-source corridors (Arabian Peninsula, Iran/Iraq basins)
* Bounding-box definitions (lat/lon) as a reusable table
* Rationale: why AOI clipping is mandatory (no full-disk / global rasters)

---

# Task 3 - Derived Climate Indicators (No New Ingestion)

For indicators derivable from **already-ingested** sources, document the source → indicator mapping and formula (conceptual only):

* NDVI / EVI (Sentinel-2, MODIS)
* Land Surface Temperature + LST anomaly (MODIS, Landsat thermal)
* Sea Surface Temperature + anomaly (NOAA OISST)
* NDWI / water availability (Sentinel-2)
* Deforestation / tree-cover loss (Global Forest Watch)
* Desertification proxy (NDVI trend + LST)
* Snow cover proxy (MODIS/Sentinel-2)

State clearly that these require **zero new connectors**.

---

# Task 4 - Data Quality Assessment

For each new source identify:

* Missing-data / cloud-contamination patterns
* Timestamp / latency behavior (near-real-time vs daily)
* Sensor noise and retrieval-quality flags
* Geospatial accuracy / resolution limits
* Unit and calibration considerations (µg/m³, mol/m², unitless AOD)

---

# Task 5 - Use-Case Mapping

Map each source to the new use cases (table). Example:

* OpenAQ → PM ground-truth, model calibration
* TROPOMI → air-quality (NO₂/SO₂/CO/O₃/CH₄), smoke, carbon proxy
* MODIS/VIIRS AOD → dust plume, aerosol concentration
* Derived LST/NDVI/SST → climate change indicators

---

# Task 6 - Transformation Complexity

Classify each source Low / Medium / High complexity based on cleaning, unit harmonization, spatial aggregation, and time alignment needs.

---

# Task 7 - Data Relationships

Extend the Phase 5 relationship graph (Mermaid) to show how the new atmospheric sources join to existing AOIs, weather (NASA POWER wind), and fire (FIRMS) data for cross-domain analysis (e.g., smoke = fire + AOD + wind).

---

# Task 8 - Freshness & Risk

* Classify each source: real-time / near-real-time / daily batch
* Document risks: rate limits, auth/quota, licensing, retrieval gaps, duplication

---

# Task 9 - Prioritization & MVP Definition

Rank the IN-scope sources and define the climate-expansion MVP set:

* Tier 1: OpenAQ, TROPOMI, MODIS/VIIRS AOD
* Tier 1 (free): derived climate indicators from existing data
* Explicitly list what is **excluded** (CAMS/ERA5 NetCDF, geostationary) and why

---

# Deliverables

Generate (append/extend, do not overwrite Phase 5 files):

```text
docs/source-data-analysis/climate/

01-climate-dataset-inventory.md
02-aoi-strategy.md
03-derived-indicators.md
04-climate-data-quality.md
05-climate-use-case-mapping.md
06-climate-transformation-complexity.md
07-climate-data-relationships.md
08-climate-freshness-risks.md
09-climate-mvp-and-deferred.md
10-glossary.md
```

---

# Documentation Standards

* Enterprise-grade Markdown, comparison tables, Mermaid relationship diagram
* Be explicit about assumptions and about deferred (out-of-scope) sources

---

# Acceptance Criteria

Complete only if:

* Each IN-scope source is fully profiled
* AOI strategy with bounding boxes is defined
* Derived-indicator mappings are documented
* Climate-expansion MVP set and deferred set are explicit
* Relationships and risks are captured

---

# Definition of Done

> A data engineering team can design the climate/dust/air-quality ingestion pipelines (Phase 8b) without asking any further questions about the new sources.

Stop after this phase. Do NOT proceed to data modeling or ingestion design.

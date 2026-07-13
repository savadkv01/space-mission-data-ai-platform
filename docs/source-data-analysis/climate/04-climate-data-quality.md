# 04 Climate / Air-Quality Data Quality Assessment

> Per-source data-quality profile for the IN-scope atmospheric sources. Identifies contamination, latency, noise, accuracy, and unit/calibration issues that downstream cleaning (Phase 8b/9) must handle. Documentation only.

## Executive Summary

Atmospheric sources carry quality risks that differ from the platform's existing telemetry/imagery: **retrieval quality varies with cloud, solar angle, and surface brightness**; ground stations are **spatially sparse** over the Gulf; and units are heterogeneous (µg/m³ vs mol/m² vs unitless AOD). Quality handling is therefore dominated by **QA-flag filtering, cloud masking, and unit harmonization** rather than schema repair. None of these blocks adoption, but each must be encoded as an explicit cleaning rule.

## Quality Dimensions by Source

| Source | Missing / Contamination | Latency Behavior | Sensor Noise / QA | Geospatial Accuracy | Units / Calibration |
| --- | --- | --- | --- | --- | --- |
| OpenAQ | Station outages, embargoed/aggregated feeds, duplicate reports | Near-real-time (hourly, station-dependent) | Instrument drift; provider-mixed methods | Point stations, sparse in Gulf → poor spatial representativeness | µg/m³, ppm, ppb mixed by pollutant — must normalize |
| TROPOMI (SH Stats) | Cloud, high solar zenith, snow/ice, low-signal scenes → `noDataCount` | Daily (one overpass/day) | Retrieval noise; `qa_value` threshold needed (drop < 0.5–0.75) | ~3.5 × 5.5 km native → aggregated to AOI (coarse) | Column density mol/m²; CH₄ ppb — not surface concentration |
| MODIS/VIIRS AOD | Cloud-contaminated retrievals, bright-surface (desert) bias, gaps | Daily | QA flags mandatory; desert bright-surface inflates AOD | 1–10 km; retrieval confidence varies | Unitless (0–5); sensor cross-calibration (MODIS vs VIIRS) |
| Derived indicators | Inherits source cloud gaps; optical needs cloud mask | Inherits source cadence | Inherits source QA | Inherits source resolution | Consistent per indicator; anomalies need stable baseline |

## Key Quality Concerns

### 1. Cloud & Retrieval Contamination (dominant risk)
Satellite atmospheric retrievals (TROPOMI, AOD) and optical indicators are only valid under favorable conditions. Rule: **filter on the provider QA field before AOI aggregation** — TROPOMI `qa_value` threshold, MODIS/VIIRS AOD QA confidence, and cloud masks for NDVI/NDWI. The per-AOI valid-vs-no-data pixel counts (`sampleCount`/`noDataCount`, emitted by the Google Earth Engine `reduceRegion` count reducers) are the primary completeness signal.

### 2. Desert Bright-Surface Bias (region-specific)
Over the bright desert surfaces that dominate UAE AOIs, AOD retrievals are **prone to positive bias**. MAIAC (MODIS MCD19A2) is preferred over legacy Dark Target because it performs better over bright land. Flag high-brightness retrievals; corroborate dust with TROPOMI UV Aerosol Index (`AER_AI`), which is more robust over bright surfaces.

### 3. Ground-Station Sparsity (representativeness)
OpenAQ coverage over the Gulf is sparse. A single station is **not representative** of an AOI mean. Treat OpenAQ as **point ground-truth / calibration**, not as an area estimate — pair it with satellite columns rather than substituting for them (see [`05-climate-use-case-mapping.md`](./05-climate-use-case-mapping.md)).

### 4. Column vs Surface Concentration (semantic trap)
TROPOMI reports **vertical column density (mol/m²)**, not breathable surface concentration (µg/m³). These are **not directly comparable** to OpenAQ. Any air-quality index blending the two must document the transformation/assumption explicitly and must not silently equate them.

### 5. Latency & Timestamp Alignment
Sources span near-real-time (OpenAQ hourly) to daily (TROPOMI/AOD). Cross-source joins must align on a **common daily grain per AOI** with explicit UTC handling. OpenAQ carries both `datetime_utc` and `datetime_local` — standardize on UTC in Bronze/Silver.

## Quality Scoring Summary

| Source | Completeness | Accuracy | Timeliness | Consistency | Overall |
| --- | --- | --- | --- | --- | --- |
| OpenAQ | Medium (sparse) | Medium-High | High | Medium (mixed methods) | **Medium** |
| TROPOMI (SH Stats) | Medium (cloud) | High | Medium (daily) | High | **High** |
| MODIS/VIIRS AOD | Medium (cloud/bright) | Medium-High | Medium (daily) | Medium (MODIS≠VIIRS) | **Medium-High** |
| Derived indicators | Inherited | Inherited | Inherited | High | **High** |

## Cleaning Rules to Carry Into Phase 8b

- Drop retrievals below QA thresholds (TROPOMI `qa_value`, AOD QA) **before** AOI aggregation.
- Harmonize units to a canonical set per pollutant; keep raw + normalized columns.
- Standardize all timestamps to UTC; align cross-source joins on a daily AOI grain.
- Never equate column density with surface concentration without a documented conversion.
- Flag desert bright-surface AOD; prefer MAIAC + corroborate dust with `AER_AI`.

## Cross References

- Inventory: [`01-climate-dataset-inventory.md`](./01-climate-dataset-inventory.md)
- Transformation complexity: [`06-climate-transformation-complexity.md`](./06-climate-transformation-complexity.md)
- Freshness & risk: [`08-climate-freshness-risks.md`](./08-climate-freshness-risks.md)
- Phase 5 quality baseline: [`../04-data-quality-assessment.md`](../04-data-quality-assessment.md)

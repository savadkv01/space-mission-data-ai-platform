# Phase 6b — Climate / Dust / Air-Quality Data Modeling (Extension)

Bronze → Silver → Gold data model for the climate, dust, and air-quality domain. Extends Phase 6 ([`../18-glossary.md`](../18-glossary.md) and the 18 core modeling docs) — design only, no code.

## Documents

| # | Document | Purpose |
| --- | --- | --- |
| 01 | [Bronze Contracts](./01-bronze-contracts.md) | Raw payload schemas inside the standard envelope |
| 02 | [Silver Entities](./02-silver-entities.md) | Cleaned/conformed `obs_air_quality`, `obs_aerosol`, `obs_atmos_column` |
| 03 | [Gold Marts](./03-gold-marts.md) | AOI-date fact marts (air quality, dust, climate, vegetation) |
| 04 | [Dimensions & Conformance](./04-dimensions-conformance.md) | `dim_aoi` extension, `dim_pollutant`, `dim_climate_indicator` |
| 05 | [KPI & Thresholds](./05-kpi-thresholds.md) | AQI breakpoints, AOD/LST/NDVI bands, DQ thresholds |
| 06 | [Lineage & Schema Evolution](./06-lineage-schema-evolution.md) | Lineage diagram, evolution strategy, reproducibility |
| 07 | [Glossary](./07-glossary.md) | Modeling terms |

## Scope

- Models only Phase 5b IN-scope sources: OpenAQ, TROPOMI (stats), MODIS/VIIRS AOD, and derived climate indicators.
- All Bronze records fit the record-oriented JSONL envelope (`BronzeEnvelope`); **no** binary/NetCDF entities.
- Marts align to the shared `dim_aoi` + `dim_date` and the existing `*_daily` fact pattern.
- CAMS/ERA5 gridded data and geostationary are **not** modeled (deferred).

Design phase — schemas and contracts only. Do NOT write ingestion or transformation code.

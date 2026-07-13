# 04 - Dimensions & Conformance (Climate / Dust / Air-Quality)

> **Phase 6b - Data Modeling (Climate Extension)** · Document 04 of 07
>
> Extends Phase 6 [`../05-star-schemas.md`](../05-star-schemas.md) and [`../07-geospatial-model.md`](../07-geospatial-model.md). Defines the new conformed dimensions and confirms the Phase 5b AOIs are added to the shared `dim_aoi`.

## Purpose

Guarantee that the climate marts conform to the existing dimensional bus. `dim_aoi` and `dim_date` are **reused** (not forked); two new conformed dimensions — `dim_pollutant` and `dim_climate_indicator` — carry the units, thresholds, and bands that the marts and semantic layer reference.

## Conformance Bus Matrix

| Fact | dim_date | dim_aoi | dim_pollutant | dim_climate_indicator |
| --- | --- | --- | --- | --- |
| `fact_air_quality_daily` | ✓ | ✓ | ✓ | — |
| `fact_dust_event_daily` | ✓ | ✓ | ✓ (AOD) | — |
| `fact_climate_indicator_daily` | ✓ | ✓ | — | ✓ |
| `fact_vegetation_health_daily` | ✓ | ✓ | — | ✓ (NDVI/EVI) |

All conform to the **same** `dim_date` (`date_key`) and `dim_aoi` (`aoi_key`) used by the MVP EO/maritime facts — enabling drill-across.

---

## `dim_aoi` (reuse + extend)

Existing `dim_aoi` (Copernicus EMS footprints, key `aoi_key`) is **extended** with the Phase 5b climate AOIs. No structural change — new rows only.

**Confirmed new AOI rows (from Phase 5b [`02-aoi-strategy.md`](../../source-data-analysis/climate/02-aoi-strategy.md)):**

| aoi_key | aoi_name | tier | bbox `[min_lon, min_lat, max_lon, max_lat]` |
| --- | --- | --- | --- |
| AOI-UAE-NAT | UAE (national) | primary | `[51.0, 22.5, 56.5, 26.2]` |
| AOI-AUH | Abu Dhabi | primary | `[53.3, 23.5, 55.3, 24.7]` |
| AOI-DXB | Dubai | primary | `[54.9, 24.8, 55.6, 25.4]` |
| AOI-COAST | UAE coastal zone | primary | `[51.5, 24.0, 56.4, 26.1]` |
| AOI-DESERT | Desert interior | primary | `[52.0, 22.5, 55.5, 23.8]` |
| AOI-ARABIA | Arabian Peninsula interior | secondary | `[42.0, 18.0, 55.0, 30.0]` |
| AOI-IRAQ | Iraq / Mesopotamia basin | secondary | `[42.0, 29.0, 48.5, 36.0]` |
| AOI-IRAN | Iran SW basins | secondary | `[47.0, 28.0, 55.0, 34.0]` |
| AOI-GULF | Arabian Gulf water body | secondary | `[48.0, 24.0, 57.0, 30.5]` |

**New/confirmed columns on `dim_aoi`:** `tier` (`primary`/`secondary`), `aoi_role` (`monitored`/`dust_corridor`) — additive, nullable for existing EMS rows. Stored as a single versioned seed (extends `transformation/seeds/aoi_reference.geojson`).

---

## `dim_pollutant` (new)

Conformed pollutant/aerosol dimension with units, AQI breakpoints, and thresholds.

| Column | Type | Notes |
| --- | --- | --- |
| `pollutant_code` | string (PK) | `PM25`, `PM10`, `NO2`, `SO2`, `CO`, `O3`, `CH4`, `AOD` |
| `pollutant_name` | string | Human-readable |
| `measure_type` | string | `surface_concentration` / `column_density` / `optical` |
| `canonical_unit` | string | `µg/m³`, `mg/m³`, `mol/m²`, `ppb`, `unitless` |
| `aqi_scheme` | string | `US_EPA` / `WHO` / `n/a` |
| `aqi_breakpoints` | array | Ordered band boundaries (see [`05-kpi-thresholds.md`](./05-kpi-thresholds.md)) |
| `who_guideline` | double | WHO guideline value; nullable |
| `exceedance_threshold` | double | Value above which `exceedance_flag`=1; nullable |

Seed values and breakpoints are specified in [`05-kpi-thresholds.md`](./05-kpi-thresholds.md).

---

## `dim_climate_indicator` (new)

Conformed indicator dimension for the derived climate/vegetation marts.

| Column | Type | Notes |
| --- | --- | --- |
| `indicator_code` | string (PK) | `LST`, `LST_ANOM`, `SST`, `SST_ANOM`, `NDVI`, `EVI`, `NDWI`, `TREE_LOSS`, `DESERT_PROXY` |
| `indicator_name` | string | Human-readable |
| `unit` | string | `°C`, `unitless`, `ha`, `index` |
| `source_family` | string | `MODIS/Landsat`, `OISST`, `Sentinel-2`, `GFW`, `derived` |
| `normal_range` | array | `[low, high]` expected range |
| `anomaly_bands` | array | Ordered band boundaries (warming/health bands) |
| `native_cadence` | string | `daily`, `8-day`, `16-day`, `annual` |
| `requires_new_ingest` | bool | **`false` for all** (derived from existing sources) |

---

## Semantic-Layer Conformance

- All climate KPIs are single-sourced in the serving semantic metric registry (ADR-BI-02), extending `serving/marts/semantic.py METRICS` — no ad-hoc chart SQL (ADR-BI-03). This phase defines the registry entries ([`05-kpi-thresholds.md`](./05-kpi-thresholds.md)); implementation is deferred to serving (11b).
- `dim_aoi` and `dim_date` remain the shared conformed dimensions across MVP EO, maritime, and climate — a single bus, no dimension forking.
- Climate marts read as Parquet from `s3://gold/<mart>/` (existing serving pattern), so BI wiring reuses the current DuckDB/httpfs path.

## Cross References

- Gold marts: [`03-gold-marts.md`](./03-gold-marts.md)
- KPI thresholds: [`05-kpi-thresholds.md`](./05-kpi-thresholds.md)
- Phase 5b AOI strategy: [`../../source-data-analysis/climate/02-aoi-strategy.md`](../../source-data-analysis/climate/02-aoi-strategy.md)
- Phase 6 star schemas: [`../05-star-schemas.md`](../05-star-schemas.md)

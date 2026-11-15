# 05 - KPI & Threshold Definitions (Climate / Dust / Air-Quality)

> **Phase 6b - Data Modeling (Climate Extension)** · Document 05 of 07
>
> Metric-registry entries for later serving/BI (11b). Single-sourced in the semantic layer (ADR-BI-02); no ad-hoc chart SQL (ADR-BI-03). Design only — thresholds specified, not implemented.

## Purpose

Define the canonical breakpoints, bands, and data-quality thresholds that `dim_pollutant` / `dim_climate_indicator` carry and that the climate Gold marts reference for their derived KPI columns.

## 1. PM2.5 / PM10 AQI Breakpoints (US EPA scheme)

**PM2.5 (µg/m³, 24-h)** → `aqi_pm25` / `aqi_band`:

| AQI band | Category | PM2.5 low | PM2.5 high |
| --- | --- | --- | --- |
| 0–50 | Good | 0.0 | 12.0 |
| 51–100 | Moderate | 12.1 | 35.4 |
| 101–150 | Unhealthy (sensitive) | 35.5 | 55.4 |
| 151–200 | Unhealthy | 55.5 | 150.4 |
| 201–300 | Very Unhealthy | 150.5 | 250.4 |
| 301–500 | Hazardous | 250.5 | 500.4 |

**PM10 (µg/m³, 24-h)** → `aqi_pm10`:

| AQI band | Category | PM10 low | PM10 high |
| --- | --- | --- | --- |
| 0–50 | Good | 0 | 54 |
| 51–100 | Moderate | 55 | 154 |
| 101–150 | Unhealthy (sensitive) | 155 | 254 |
| 151–200 | Unhealthy | 255 | 354 |
| 201–300 | Very Unhealthy | 355 | 424 |
| 301–500 | Hazardous | 425 | 604 |

**WHO 2021 guideline (exceedance_flag reference):** PM2.5 24-h = 15 µg/m³; PM10 24-h = 45 µg/m³. `exceedance_flag`=1 when the daily mean exceeds the WHO guideline.

## 2. AOD Load Bands (unitless, 550 nm)

→ `dust_severity_band` (AOD load of **any** aerosol type), `aerosol_load_label`, `dust_flag`:

| Band | `aerosol_load_label` | AOD low | AOD high | `dust_severity_label` when `dust_status = positive` |
| --- | --- | --- | --- | --- |
| 0 | Clear | 0.0 | 0.2 | — (dust requires AOD ≥ 0.5) |
| 1 | Hazy | 0.2 | 0.5 | — |
| 2 | Elevated | 0.5 | 1.0 | Dusty |
| 3 | High | 1.0 | 2.0 | Heavy dust |
| 4 | Very high | 2.0 | 5.0 | Severe |

`dust_flag` = 1 when `aod_mean` ≥ 0.5 **and** dust is evidenced: the MAIAC dust-model share (`dust_fraction`, `AOD_QA` bits 13–14) is ≥ 0.5, or, when no aerosol-model information exists, `uv_aerosol_index_mean` ≥ 1.0. Smoke also raises the UV aerosol index, so with MAIAC information the dust share decides (L5 / D-07). `aerosol_type` is the dominant MAIAC model (`dust` / `smoke` / `mixed` / `background`). Dust wording (`dust_severity_label`) is used only for positive dust rows; negative rows are `No dust event` (changed 2026-11-15; earlier releases labelled AOD bands 2–4 as dust regardless of type).

`transport_flag` = 1 when the strongest AOD over **upwind** same-region AOIs (bearing within ±45° of the NASA POWER wind direction) is ≥ 0.5 and wind speed > 0 (D-06).

## 3. LST Anomaly Bands (°C above same-DOY baseline)

→ `lst_anomaly_band`, `warming_flag`:

| Band | Label | Anomaly low (°C) | Anomaly high (°C) |
| --- | --- | --- | --- |
| −1 | Cooler | −∞ | −1.0 |
| 0 | Normal | −1.0 | +1.0 |
| 1 | Warm | +1.0 | +3.0 |
| 2 | Hot | +3.0 | +5.0 |
| 3 | Extreme | +5.0 | +∞ |

`warming_flag`=1 when `lst_anomaly_c` ≥ +3.0 (or `sst_anomaly_c` ≥ +1.5 for coastal AOIs).

## 4. NDVI Health Bands (unitless)

→ `ndvi_health_band`, `crop_stress_flag`:

| Band | Label | NDVI low | NDVI high |
| --- | --- | --- | --- |
| 0 | Bare / water | −1.0 | 0.1 |
| 1 | Sparse | 0.1 | 0.3 |
| 2 | Moderate | 0.3 | 0.5 |
| 3 | Healthy | 0.5 | 0.7 |
| 4 | Dense | 0.7 | 1.0 |

`crop_stress_flag`=1 when `ndvi_mean` < 0.3 **and** `ndvi_trend_30d` < 0, evaluated only for AOIs marked `cropland` in the AOI seed (`crop_stress_applicable`); elsewhere it is `not_evaluated` (D-08, 2026-11-15). Low, declining NDVI over sea, desert or a city is not crop stress.

The desertification proxy needs **both** a declining NDVI trend and a positive LST anomaly; with one driver it is `None` → `not_evaluated` (D-05). An NDVI decline alone is also what a crop harvest looks like.

## 4a. Flood (NDWI, permanent-water masked)

→ `flood_flag`, `water_fraction` (`kpi_flood_aoi_daily`):

| Rule | Value | Notes |
| --- | --- | --- |
| Permanent water mask | JRC GSW v1.4 `seasonality` ≥ 10 months **or** ESA WorldCover v200 class 80 | UN-SPIDER practice; WorldCover adds the open sea that GSW does not classify |
| New water | NDWI (McFeeters) > 0 on a non-permanent pixel | — |
| `flood_flag` = 1 | `water_fraction` ≥ 0.02 | Dry-season baselines (2026-11-15): Dubai 0.1–0.3 %, Assam 0.4–0.9 % |
| Not evaluated | legacy unmasked statistics, or `valid_pixel_fraction` < 0.1 | Flag null; never a negative |

## 5. Data-Quality Thresholds

| Threshold | Applies to | Rule |
| --- | --- | --- |
| `valid_pixel_fraction` ≥ 0.5 | TROPOMI `obs_atmos_column` | Below → row flagged `low_coverage`, excluded from KPI mean |
| AOD QA confidence = high | `obs_aerosol` | Low/medium confidence retrievals dropped before aggregation |
| `station_count` ≥ 1 | `fact_air_quality_daily` | AQI computed only with ≥1 valid station in AOI |
| Bright-surface AOD | `obs_aerosol` | Flagged; excluded from dust_flag unless UV AI corroborates |
| Cloud-free fraction ≥ 0.3 | NDVI/EVI marts | Below → NDVI KPI marked estimated |
| Sensor plausibility (D-09) | `obs_air_quality` | PM2.5 > 1000 / PM10 > 2000 µg/m³, ≥ 8 identical consecutive readings (flat line), or an isolated reading > 3× and > 250 µg/m³ above both neighbours → `suspect` with `qa_reason`; excluded from Gold |

## Metric Registry Entries (for serving 11b)

Each KPI below becomes a `serving/marts/semantic.py METRICS` entry (implementation deferred):

| Metric key | Mart | Aggregation |
| --- | --- | --- |
| `aqi_pm25_daily` | `fact_air_quality_daily` | band from breakpoints |
| `aqi_exceedance_days` | `fact_air_quality_daily` | count where `exceedance_flag`=1 |
| `dust_event_days` | `fact_dust_event_daily` | count where `dust_flag`=1 |
| `aod_max` | `fact_dust_event_daily` | max(`aod_mean`) per AOI/period |
| `lst_anomaly_mean` | `fact_climate_indicator_daily` | mean(`lst_anomaly_c`) |
| `warming_days` | `fact_climate_indicator_daily` | count where `warming_flag`=1 |
| `ndvi_health_mean` | `fact_vegetation_health_daily` | mean(`ndvi_mean`) |
| `desertification_flag_days` | `fact_climate_indicator_daily` | count where `desertification_flag`=1 |

## Cross References

- Dimensions: [`04-dimensions-conformance.md`](./04-dimensions-conformance.md)
- Gold marts: [`03-gold-marts.md`](./03-gold-marts.md)
- Phase 5b quality: [`../../source-data-analysis/climate/04-climate-data-quality.md`](../../source-data-analysis/climate/04-climate-data-quality.md)

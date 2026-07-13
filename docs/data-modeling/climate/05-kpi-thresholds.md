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

## 2. AOD Dust-Severity Bands (unitless, 550 nm)

→ `dust_severity_band`, `dust_flag`:

| Band | Label | AOD low | AOD high | Notes |
| --- | --- | --- | --- | --- |
| 0 | Clear | 0.0 | 0.2 | Background aerosol |
| 1 | Hazy | 0.2 | 0.5 | Elevated aerosol |
| 2 | Dusty | 0.5 | 1.0 | Likely dust |
| 3 | Heavy dust | 1.0 | 2.0 | Dust storm |
| 4 | Severe | 2.0 | 5.0 | Extreme event |

`dust_flag`=1 when `aod_mean` ≥ 0.5 **and** `uv_aerosol_index_mean` ≥ 1.0 (UV AI confirms absorbing aerosol / dust over bright desert).

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

`crop_stress_flag`=1 when `ndvi_mean` < 0.3 **and** `ndvi_trend_30d` < 0.

## 5. Data-Quality Thresholds

| Threshold | Applies to | Rule |
| --- | --- | --- |
| `valid_pixel_fraction` ≥ 0.5 | TROPOMI `obs_atmos_column` | Below → row flagged `low_coverage`, excluded from KPI mean |
| AOD QA confidence = high | `obs_aerosol` | Low/medium confidence retrievals dropped before aggregation |
| `station_count` ≥ 1 | `fact_air_quality_daily` | AQI computed only with ≥1 valid station in AOI |
| Bright-surface AOD | `obs_aerosol` | Flagged; excluded from dust_flag unless UV AI corroborates |
| Cloud-free fraction ≥ 0.3 | NDVI/EVI marts | Below → NDVI KPI marked estimated |

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

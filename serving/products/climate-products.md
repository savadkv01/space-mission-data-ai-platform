# Climate / Dust / Air-Quality Data Products (Phase 11b)

> Extends the [Earth Observation products](./observation-products.md). Designed
> for free public data sources (OpenAQ, MODIS/VIIRS AOD, Sentinel-2, TROPOMI).
> AOI-date grained and
> pre-denormalized so consumers need no joins.

Every product below is built by a pure-Python builder in
[../marts/climate/climate_products.py](../marts/climate/climate_products.py) and a
mirrored dbt model in [../dbt/models/climate/](../dbt/models/climate/). KPIs are
single-sourced in [../marts/semantic.py](../marts/semantic.py).

---

## Air Quality

| Attribute | Value |
| --- | --- |
| Product | `serving_air_quality_daily` |
| Purpose | Per-AOI daily pollutant means/max, AQI and WHO exceedance for public-health alerting |
| Owner | Climate Analytics team |
| Consumers | Weather/air-quality dashboard, executive dashboard, REST API, RAG |
| Refresh | Daily (batch, after Gold rebuild) |
| SLA | Freshness ≤ 24 h; dashboard read p95 ≤ 3 s |
| Source | `fact_air_quality_daily`, `ref_aoi` |
| Grain | 1 row / AOI / day |
| KPIs | pm25/pm10 mean+max, gas column means, aqi_pm25/pm10, aqi_band, exceedance_flag |

---

## Dust Event

| Attribute | Value |
| --- | --- |
| Product | `serving_dust_event_daily` |
| Purpose | Per-AOI daily AOD, dust-severity, corroborated dust flag + wind/corridor transport context |
| Owner | Climate Analytics team |
| Consumers | Weather dashboard, aviation/ops, REST API |
| Refresh | Daily |
| SLA | Freshness ≤ 24 h; dashboard read p95 ≤ 3 s |
| Source | `fact_dust_event_daily`, `ref_aoi` |
| Grain | 1 row / AOI / day |
| KPIs | aod_mean/max, uv_aerosol_index_mean, dust_severity_band+label, dust_flag, transport_flag |

---

## Climate Indicator

| Attribute | Value |
| --- | --- |
| Product | `serving_climate_indicator_daily` |
| Purpose | Per-AOI daily LST/SST + anomalies, NDWI, desertification proxy for climate monitoring |
| Owner | Climate Analytics team |
| Consumers | Executive dashboard, weather dashboard, ML (14) |
| Refresh | Daily |
| SLA | Freshness ≤ 24 h |
| Source | `fact_climate_indicator_daily`, `fact_vegetation_health_daily`, `ref_aoi` |
| Grain | 1 row / AOI / day |
| KPIs | lst_c/anomaly, sst/anomaly, ndvi_mean, evi_mean, ndwi_mean, desertification_proxy, warming_flag, desertification_flag |

---

## Vegetation Health

| Attribute | Value |
| --- | --- |
| Product | `serving_vegetation_health_daily` |
| Purpose | Per-AOI daily NDVI/EVI + 30-day trend and crop-stress proxy for agriculture/land |
| Owner | Climate Analytics team |
| Consumers | Agriculture/land dashboards, ML (14) |
| Refresh | Daily |
| SLA | Freshness ≤ 24 h |
| Source | `fact_vegetation_health_daily`, `ref_aoi` |
| Grain | 1 row / AOI / day |
| KPIs | ndvi_mean/max, evi_mean, ndvi_trend_30d + direction, ndvi_health_band+label, crop_stress_flag |

---

## Conformed Dimensions

| Dimension | Key | Notes |
| --- | --- | --- |
| `dim_aoi` | `aoi_key` | Reused (not forked) — shared bus with MVP EO/maritime |
| `dim_pollutant` | `pollutant_code` | Units, AQI scheme, WHO thresholds |
| `dim_climate_indicator` | `indicator_code` | Unit, source family, cadence |

## Materialized Aggregate

`mv_kpi_climate_daily` — one row per calendar day rolling up air-quality / dust /
climate / vegetation KPIs for the executive and weather dashboards (mirrors
`mv_kpi_platform_daily`).

## Certification and source limitations

These are governed serving contracts, not an unconditional certification of
every source batch. The Phase 10b quality gates determine whether a Gold batch
is `DRAFT`, `VALIDATED`, or `CERTIFIED`; serving-model tests verify schema,
grain, ranges, and enums only. Do not label a dataset or batch certified unless
the corresponding quality-gate evidence and owner approval are available.

The current Gold air-quality fact does not expose a CH4 measure, although
`dim_pollutant` includes CH4 as a reference species. The serving product does
not synthesize a CH4 value. Source access, pollutant completeness, and unit
reconciliation remain upstream requirements before those fields can be
promoted for feature-store consumption.

The 2026-10-31 local Gold snapshot contains 72 air-quality AOI-days and 35
dust AOI-days, both with latest observations in 2024; climate-indicator and
vegetation-health Gold marts contain no rows. These tables build and pass
serving contracts, but are not certified or suitable as fresh training data.

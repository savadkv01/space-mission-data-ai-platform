# Air-Quality — Data Quality Rules

> Entities: Silver `obs_air_quality` (OpenAQ surface pollutants) → Gold
> `fact_air_quality_daily` (AQI KPIs per AOI/day). Suites:
> `silver_air_quality_suite()`, `gold_air_quality_daily_suite()`.

---

## Silver `obs_air_quality`

Natural key: `air_quality_key` = hash(`location_id`, `sensor_id`, `pollutant_code`, `event_ts`).
Grain: 1 row / station / pollutant / reading.

### Mandatory fields

| Field | Type | Rule | Severity |
|-------|------|------|----------|
| `air_quality_key` | string | Non-null, unique | critical |
| `event_ts` | ISO-8601 UTC | Non-null | critical |
| `pollutant_code` | enum | Non-null; `∈ {PM25, PM10, NO2, SO2, CO, O3, BC}` | critical |
| `geo_key` | string | Non-null | critical |
| `quality_flag` | enum | `∈ {valid, suspect, low_coverage}` | critical |

### Range & unit checks

| Signal | Rule | Severity |
|--------|------|----------|
| `value_std` | `≥ 0` (canonical unit per pollutant: µg/m³, CO → mg/m³) | critical |
| `value_raw` | `≥ 0` | critical |
| `latitude` | `[-90, 90]` | critical |
| `longitude` | `[-180, 180]` | critical |
| PM2.5 `value_std` | `≤ 1000 µg/m³` (plausibility cap) | warn |
| PM10 `value_std` | `≤ 2000 µg/m³` (plausibility cap) | warn |

> **Unit invariant:** the Silver cleaner standardizes every reading to the
> pollutant's canonical unit and retains `value_raw`/`unit_raw` for audit
> (`transformation/cleaning/climate/units.py`). Non-convertible units are kept
> and flagged `suspect`, not silently coerced.

---

## Gold `fact_air_quality_daily`

Grain: **1 row / AOI / day** (`aoi_key`, `date_key` unique).

| Category | Rule | Severity |
|----------|------|----------|
| Keys | `aoi_key`, `date_key` non-null; `(aoi_key, date_key)` unique | critical |
| Range | `pm25_mean/max`, `pm10_mean/max` `≥ 0` | critical |
| Range | `aqi_pm25`, `aqi_pm10` `∈ [0, 500]` (US EPA scale) | critical |
| Range | `station_count ≥ 0`; `column_valid_fraction ∈ [0, 1]` | critical / warn |
| Range | `no2/so2/co/o3_column_mean ≥ 0` | warn |
| Enum | `aqi_band ∈ {Good, Moderate, Unhealthy (sensitive), Unhealthy, Very Unhealthy, Hazardous}` | critical |
| Consistency | `aqi_pm25` populated **only** when `station_count ≥ 1` | critical |
| Completeness | every AOI-day has `station_count ≥ 1` | warn |

**Business impact of failure:** mis-scaled pollutant values or missing station
coverage break the AQI KPI and the WHO exceedance flag that drive the
Air-Quality dashboard and the environmental-report RAG corpus.

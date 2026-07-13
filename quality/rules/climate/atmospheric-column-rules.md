# Atmospheric Column — Data Quality Rules

> Entity: Silver `obs_atmos_column` (TROPOMI / Sentinel-5P trace-gas & aerosol-index
> column densities per AOI/day). Suite: `silver_atmos_column_suite()`. The column
> means also feed `fact_air_quality_daily` (NO₂/SO₂/CO/O₃) and
> `fact_dust_event_daily` (AER_AI).

---

## Silver `obs_atmos_column`

Natural key: `atmos_key` = hash(`aoi_id`, `gas_code`, `stat_date`).
Grain: 1 row / AOI / gas / day.

### Mandatory fields

| Field | Type | Rule | Severity |
|-------|------|------|----------|
| `atmos_key` | string | Non-null, unique | critical |
| `event_ts` | ISO-8601 UTC | Non-null | critical |
| `aoi_id` | string | Non-null | critical |
| `gas_code` | enum | Non-null; `∈ {NO2, SO2, CO, O3, CH4, AER_AI}` | critical |
| `mean` | float | Non-null (column density) | critical |
| `unit_std` | enum | `∈ {mol/m2, ppb, unitless}` | critical |
| `quality_flag` | enum | `∈ {valid, suspect, low_coverage}` | critical |

### Range & unit checks

| Signal | Rule | Severity |
|--------|------|----------|
| `mean` (trace gas) | `≥ 0` for `NO2/SO2/CO/O3/CH4` — **`AER_AI` exempt** (may be negative) | critical |
| `valid_pixel_fraction` | `∈ [0, 1]` | critical |
| `valid_pixel_fraction` | `≥ 0.5` coverage floor (below → `low_coverage`) | warn |
| Grain | `(aoi_id, gas_code, stat_date)` unique | critical |

> **Unit mapping** (`transformation/cleaning/climate/atmos_column.py`): `NO2/SO2/CO/O3`
> → `mol/m2`, `CH4` → `ppb`, `AER_AI` → `unitless`. A column density is **never**
> conformed to a surface concentration (`obs_air_quality.value_std`).

**Business impact of failure:** a bad column density or wrong unit propagates into
the daily air-quality gas means and the UV-aerosol-index dust corroboration,
skewing both the Air-Quality and Dust dashboards.

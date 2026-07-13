# Aerosol / Dust — Data Quality Rules

> Entities: Silver `obs_aerosol` (MODIS/VIIRS AOD) → Gold `fact_dust_event_daily`
> (dust KPIs per AOI/day). Suites: `silver_aerosol_suite()`,
> `gold_dust_event_daily_suite()`.

---

## Silver `obs_aerosol`

Natural key: `aerosol_key` = hash(`aoi_id`, `sensor`, `stat_date`).
Grain: 1 row / AOI / sensor / day.

### Mandatory fields

| Field | Type | Rule | Severity |
|-------|------|------|----------|
| `aerosol_key` | string | Non-null, unique | critical |
| `event_ts` | ISO-8601 UTC | Non-null | critical |
| `aoi_id` | string | Non-null | critical |
| `stat_date` | date | Non-null | critical |
| `quality_flag` | enum | `∈ {valid, suspect, low_coverage}` | critical |

### Range & completeness checks

| Signal | Rule | Severity |
|--------|------|----------|
| `aod_550nm` | `∈ [0, 5]` — non-physical retrievals rejected | critical |
| `valid_fraction` | `∈ [0, 1]` | critical |
| `valid_fraction` | `≥ 0.5` retrieval-completeness floor | warn |
| Grain | `(aoi_id, sensor, stat_date)` unique | critical |

> Bright-surface (desert) or low-coverage AOD is *flagged* `suspect`, not dropped,
> so downstream dust logic can corroborate it against the UV aerosol index.

---

## Gold `fact_dust_event_daily`

Grain: **1 row / AOI / day** (`aoi_key`, `date_key` unique).

| Category | Rule | Severity |
|----------|------|----------|
| Keys | `aoi_key`, `date_key` non-null; `(aoi_key, date_key)` unique | critical |
| Range | `aod_mean`, `aod_max`, `corridor_aod_max` `∈ [0, 5]` | critical |
| Range | `valid_fraction ∈ [0, 1]`; floor `≥ 0.5` | critical / warn |
| Range | `wind_speed_mean ≥ 0` (nullable — NASA POWER context) | warn |
| Enum | `dust_severity_band ∈ {0, 1, 2, 3, 4}` (AOD severity scheme) | critical |

**Dust-severity bands** (AOD 550 nm, single-sourced from
[05-kpi-thresholds.md](../../../docs/data-modeling/climate/05-kpi-thresholds.md)):
`0` Clear (0–0.2) · `1` Hazy (0.2–0.5) · `2` Dusty (0.5–1.0) · `3` Heavy (1.0–2.0) · `4` Severe (2.0–5.0).

**Business impact of failure:** an out-of-range or mis-banded AOD misfires the
`dust_flag` / `transport_flag`, corrupting the dust-event count KPI and the
dust-forecast feature inputs (14b).

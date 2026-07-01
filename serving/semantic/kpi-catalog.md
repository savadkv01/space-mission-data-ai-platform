# KPI Catalog (Task 3)

Canonical KPI definitions, single-sourced in
[../marts/semantic.py](../marts/semantic.py) (`METRICS`). Each KPI names its unit,
grain, definition, and the serving product it is computed over. Consumers call
`semantic.compute_kpis(rows, [...])` — they never re-implement the formula.

## MVP Earth-Observation KPIs

| KPI | Unit | Grain | Definition | Product |
| --- | --- | --- | --- | --- |
| Total Fire Detections | count | aoi/day | Σ FIRMS/VIIRS detections attributed to AOIs | `serving_wildfire_daily` |
| Mean Fire Radiative Power | MW | aoi/day | avg(`mean_frp`) over wildfire rows | `serving_wildfire_daily` |
| Flood Day Rate | ratio | aoi/day | share of AOI-days with `flood_flag` | `serving_flood_daily` |
| Suspicious Vessel Rate | ratio | vessel/day | share of vessel-days with `suspicious_flag` | `serving_vessel_activity` |
| Searchable Scene Rate | ratio | scene | share of scenes with `is_searchable` | `serving_scene_catalog` |
| EMS Corroboration Rate | ratio | aoi | share of EMS AOIs `corroborated` | `serving_aoi_validation` |

## Simulation-Track KPIs (`sim`)

| KPI | Unit | Grain | Definition | Product |
| --- | --- | --- | --- | --- |
| Mean Satellite Health | score | sat/day | avg(`health_score`) | `serving_sat_health` |
| Launch Success Rate | ratio | provider/month | avg(`success_rate`) | `serving_launch_monthly` |

## Derived / Banded Attributes

These are deterministic classifications produced inside the data products (not
metrics to aggregate), documented here so BI and API agree on thresholds:

| Attribute | Product | Rule |
| --- | --- | --- |
| `severity` | wildfire | ≥100 extreme · ≥30 high · ≥10 moderate · else low |
| `quality_band` | scene catalog | ≥0.9 gold · ≥0.7 silver · else bronze · not searchable ⇒ unlisted |
| `review_priority` | vessel | suspicious ⇒ high, else normal |
| `trust` | validation | corroborated ⇒ corroborated, else unconfirmed |
| `status` | sat health (sim) | ≥0.8 nominal · ≥0.5 degraded · else critical |
| `storm_day` | weather (sim) | `max_kp_index` ≥ 5 |

## Consistency Guarantees

- Requesting an unregistered KPI raises `KeyError` (fail fast, no silent empties).
- Empty input returns `None` per KPI (never a crash or a misleading `0`).
- The same reducer runs in BI (via product tables), API responses, and RAG
  summaries — no divergent implementations.

# BI Dataset Catalog (Task 6)

Superset physical datasets. Each maps 1:1 to a serving product or materialized
aggregate. No ad-hoc SQL datasets are permitted in BI.

## MVP Datasets

| Superset dataset | Source table | Grain | Primary charts | Role |
| --- | --- | --- | --- | --- |
| `wildfire_daily` | `serving.serving_wildfire_daily` | AOI/day | AOI map, severity pie, detections trend | `ops_eo`, `exec` |
| `flood_daily` | `serving.serving_flood_daily` | AOI/day | NDWI trend, flood-day calendar | `ops_eo`, `exec` |
| `vessel_activity` | `serving.serving_vessel_activity` | vessel/day | suspicious queue, priority table | `ops_maritime` |
| `scene_catalog` | `serving.serving_scene_catalog` | scene | quality band bar, searchable gauge | `steward` |
| `aoi_validation` | `serving.serving_aoi_validation` | AOI | corroboration rate, trust table | `exec`, `ops_eo` |
| `platform_daily` | `serving_agg.mv_kpi_platform_daily` | day | executive KPI tiles + trends | `exec` |
| `catalog_quality` | `serving_agg.mv_catalog_quality` | collection | searchable rate, completeness | `steward` |

## Simulation-Track Datasets (`demo`)

| Superset dataset | Source table | Grain | Role |
| --- | --- | --- | --- |
| `sat_health` | `serving_sat_health` | sat/day | `demo` |
| `launch_monthly` | `serving_launch_monthly` | provider/month | `demo` |
| `weather_impact` | `serving_weather_impact` | day | `demo` |

## Dataset Conventions

- **Physical datasets only** — charts select columns; no per-chart SQL.
- **Refresh**: Superset cache warms after the serving-refresh DAG completes.
- **Cache TTL**: 1 h for daily products, 15 min for materialized aggregates.
- **Ownership**: dataset owner = product owner (see [../products/](../products/)).
- **Classification**: each dataset inherits the sensitivity tag from
  [../access-strategy.md](../access-strategy.md).

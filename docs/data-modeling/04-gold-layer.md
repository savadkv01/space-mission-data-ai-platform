# 04 - Gold Layer (Business Data Model)

> **Phase 6 - Data Modeling** · Document 04 of 18

## Purpose

Define curated, business-ready analytical models: fact tables, dimensions, aggregates, and KPI tables serving dashboards, APIs, and ML.

## Analytical Domains

| Domain | Output |
| --- | --- |
| Satellite health analytics | health score, anomaly counts |
| Launch performance analytics | success rate, delay, cadence |
| Space weather impact | storm-to-anomaly correlation |
| Earth observation analytics | fire/flood/change KPIs |
| Maritime domain awareness | vessel activity, suspicious-fishing KPIs |
| Catalog quality analytics | metadata completeness, searchability |
| Mission success metrics | objective completion |

## Fact / Dimension Inventory

> **Track.** `fact_launch`, `fact_sat_health`, and `fact_weather_impact` belong to
> the post-MVP **Simulation Track** (synthetic spacecraft data, excluded from MVP
> per ADR-09). All other facts/marts are MVP Earth-observation / maritime.

| Fact | Grain |
| --- | --- |
| `fact_fire_detection` | 1 row/fire detection/day |
| `fact_flood_extent` | 1 row/AOI/scene |
| `fact_vessel_activity` | 1 row/vessel/day |
| `fact_scene_catalog` | 1 row/scene |
| `fact_launch` | 1 row/launch |
| `fact_sat_health` | 1 row/sat/day |
| `fact_weather_impact` | 1 row/sat/storm window |

| Dimension | Key |
| --- | --- |
| `dim_date` | `date_key` |
| `dim_satellite` | `sat_key` |
| `dim_mission` | `mission_key` |
| `dim_geo` (AOI/tile) | `geo_key` |
| `dim_provider` | `provider_key` |
| `dim_vessel` | `vessel_key` |
| `dim_aoi` (EMS footprint) | `aoi_key` |

## Aggregation Strategy

- Pre-aggregate to daily/AOI marts; incremental refresh from Silver.
- KPI tables wide and dashboard-shaped to avoid runtime joins.

## KPI Tables

| Table | KPIs |
| --- | --- |
| `kpi_eo_daily` | fires, burned area, flood km², revisit gap |
| `kpi_fishing_daily` | vessels observed, suspicious events, fishing hours |
| `kpi_catalog_quality` | metadata completeness %, searchable scenes, mean cloud cover |
| `kpi_wildfire_aoi_daily` | detections, mean/max FRP per AOI (point-in-polygon) |
| `kpi_flood_aoi_daily` | NDWI mean/max, valid-pixel %, flood flag per AOI |
| `kpi_aoi_validation` | EMS ground-truth corroboration, evidence days |
| `kpi_launch_monthly` | success %, mean delay, cadence |
| `kpi_mission` | objective %, uptime |

## Cross References

- [05-star-schemas.md](05-star-schemas.md) · [08-feature-store.md](08-feature-store.md) · [14-performance.md](14-performance.md)

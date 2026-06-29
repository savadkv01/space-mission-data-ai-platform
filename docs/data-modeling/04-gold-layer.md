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
| Mission success metrics | objective completion |

## Fact / Dimension Inventory

| Fact | Grain |
| --- | --- |
| `fact_fire_detection` | 1 row/fire detection/day |
| `fact_flood_extent` | 1 row/AOI/scene |
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

## Aggregation Strategy

- Pre-aggregate to daily/AOI marts; incremental refresh from Silver.
- KPI tables wide and dashboard-shaped to avoid runtime joins.

## KPI Tables

| Table | KPIs |
| --- | --- |
| `kpi_eo_daily` | fires, burned area, flood km², revisit gap |
| `kpi_launch_monthly` | success %, mean delay, cadence |
| `kpi_mission` | objective %, uptime |

## Cross References

- [05-star-schemas.md](05-star-schemas.md) · [08-feature-store.md](08-feature-store.md) · [14-performance.md](14-performance.md)

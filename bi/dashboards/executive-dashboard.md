# Executive Dashboard

> Phase 12 · Task 2 — Dashboard Catalog · Audience: **Executives / Program Leadership**
> Superset slug: `executive` · Role: `exec` · Primary dataset: `platform_daily`

## Purpose

A single decision-support view of platform-wide mission value: how much
high-impact activity the platform detected, how trustworthy those detections are
(EMS corroboration), and whether the platform met its service commitments. It
reads the pre-computed `platform_daily` materialized aggregate so it loads fast
and stays within the caching SLA.

## KPI Tiles

| Tile | KPI | Dataset · column | Definition | Green / Amber / Red |
| --- | --- | --- | --- | --- |
| Active Missions | Active AOIs + vessels + sats | `platform_daily` (fire_aois + flood_aois), `vessel_activity`, `sat_health`(sim) | Distinct monitored entities in window | informational |
| Mission Success Rate | EMS Corroboration Rate | `aoi_validation.corroborated` | share of EMS AOIs corroborated | ≥0.8 / 0.6–0.8 / <0.6 |
| Detections (window) | Total Fire Detections | `platform_daily.fire_detections` | Σ detections | informational + trend |
| Suspicious Vessels | Suspicious Vessel count | `platform_daily.suspicious_vessels` | Σ suspicious vessel-days | trend, spike = red |
| Satellite Availability `sim` | Mean Satellite Health | `sat_health.health_score` | avg health score | ≥0.8 / 0.5–0.8 / <0.5 |
| SLA Compliance | Serving latency SLA met | monitoring metric (see below) | % requests within SLA | ≥0.99 / 0.95–0.99 / <0.95 |
| Platform Health | Pipeline success rate | Platform dashboard cross-link | % DAG runs successful | ≥0.98 / 0.9–0.98 / <0.9 |

> MVP-primary executive KPIs are **EMS Corroboration Rate**, **Detections**,
> **Suspicious Vessels**, and **SLA Compliance** — all real-data. *Satellite
> Availability* is drawn from the **simulation track** (ADR-09) and is tagged
> `sim` on the tile.

## Climate KPI Tiles  *(added Phase 12b)*

Sourced from the extended materialized aggregate
[`climate_daily`](../datasets/sql/climate_daily.sql) (`serving_agg.mv_kpi_climate_daily`)
so the executive view stays within the 15-min caching SLA.

| Tile | KPI | Dataset · column | Definition | Green / Amber / Red |
| --- | --- | --- | --- | --- |
| Air-Quality Exceedances | AQI Exceedance Days | `climate_daily.aqi_exceedance_days` | Σ AOI-days over WHO guideline | 0 / 1–5 / >5 |
| Active Dust Days | Dust event days | `climate_daily.dust_event_days` | Σ dust-flag days in window | 0 / 1–4 / ≥5 |
| Climate Signal | Mean LST anomaly (°C) | `climate_daily.mean_lst_anomaly` | window mean LST anomaly | <+1 / +1–+2 / ≥+2 |

> These climate KPIs are **real-data** (Phase 11b certified products) and drill
> down into the Air-Quality/Dust and Climate-Indicators dashboards.

## Layout (wireframe)

```
+---------------------------------------------------------------+
|  SPACE MISSION PLATFORM — EXECUTIVE            [ time range ▾] |
+------------+------------+------------+------------+------------+
| Active     | Mission    | Detections | Suspicious | SLA        |
| Missions   | Success %  | (window)   | Vessels    | Compliance |
|   42       |   0.83     |   1,204    |    7       |   99.4%    |
+------------+------------+------------+------------+------------+
|  Detections & Flood AOI-days (trend, platform_daily)          |
|  ▁▂▄▆█▅▃  fire_detections   ▁▁▂▁▃  flood_aoi_days             |
+-------------------------------+-------------------------------+
| EMS Corroboration by event    | Suspicious vessels (trend)    |
| (aoi_validation, fire/flood)  | (platform_daily)              |
+-------------------------------+-------------------------------+
| Satellite Availability `sim`  | SLA / Pipeline health (links) |
+-------------------------------+-------------------------------+
| AQI Exceed. | Active Dust | Mean LST Anomaly (climate_daily)  |
|    12       |     4       |    +1.8 °C                        |
+-------------+-------------+-----------------------------------+
| Climate Exceedance & Dust Trend (line, climate_daily)         |
+---------------------------------------------------------------+
```

## Filters

- Global time range (default: last 30 days), applied to every `*_date` column.
- Event type (fire / flood) cross-filter on the corroboration chart.

## Drill-down

- Detections trend → **Earth Observation Dashboard** (wildfire tab).
- Suspicious vessels → **Earth Observation Dashboard** (maritime tab).
- SLA / Pipeline health tiles → **Platform Operations Dashboard**.
- Climate KPI tiles → **Air Quality & Dust** and **Climate Indicators** dashboards.

## Data Lineage

`s3://gold/*` → serving products → `serving_agg.mv_kpi_platform_daily` →
`platform_daily` dataset → this dashboard. See
[../kpis/kpi-catalog.md](../kpis/kpi-catalog.md).

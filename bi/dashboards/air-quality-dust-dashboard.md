# Air Quality & Dust Dashboard

> Phase 12b · Task 1 — Dashboard Catalog · Audience: **Air-Quality, Smart-City,
> Aviation & Ports teams** · Superset slug: `air-quality-dust`
> Roles: `ops_airquality` (+ `exec` read) · **Real-data (11b climate products)**

## Purpose

Operational surface for atmospheric hazard monitoring. Fuses the certified
air-quality and dust serving products into one investigative view: detect
pollutant exceedances, track dust plumes and their wind transport, and prioritise
notifications for smart-city, aviation, and port operations. Reuses the Earth
Observation dashboard's tab/chart/certification pattern exactly — no new tooling.

## Data Sources (certified 11b products)

| Dataset | Certified SQL | Source product | Grain |
| --- | --- | --- | --- |
| `air_quality_daily` | [air_quality_daily.sql](../datasets/sql/air_quality_daily.sql) | `serving.serving_air_quality_daily` | AOI/day |
| `dust_event_daily` | [dust_event_daily.sql](../datasets/sql/dust_event_daily.sql) | `serving.serving_dust_event_daily` | AOI/day |

## Tabs & Charts

### Tab 1 — Air Quality (dataset `air_quality_daily`)

| Chart | Type | Columns / Metric |
| --- | --- | --- |
| AOI pollutant map (AQI heat layer) | deck.gl / geo | `aoi_key`, `aqi_pm25`, `aqi_band` |
| AQI Exceedance Days | big number | `exceedance_days` |
| AQI Band Distribution | pie | `aqi_band` |
| PM2.5 / PM10 Trend | line | `event_date`, `mean_pm25`, `mean_pm10` |

### Tab 2 — Dust (dataset `dust_event_daily`)

| Chart | Type | Columns / Metric |
| --- | --- | --- |
| Dust plume / AOD map | deck.gl / geo | `aoi_key`, `aod_max`, `dust_severity_label` |
| Active Dust Days | big number | `dust_days` |
| Dust Severity Distribution | pie | `dust_severity_label` |
| AOD (Dust) Trend | time bar | `event_date`, `peak_aod` |
| Dust-flag Calendar | calendar heatmap | `event_date`, `dust_days` |
| Wind-transport context | table (panel) | `wind_speed_mean`, `wind_dir_dominant`, `transport_flag` |

### Tab 3 — Details (drill-down)

| Chart | Type | Columns |
| --- | --- | --- |
| Air Quality Details | table | `aoi_name`, `event_date`, `pm25_mean`, `aqi_pm25`, `aqi_band`, `exceedance_flag`, `station_count` |
| Dust & Wind-transport Details | table | `aoi_name`, `event_date`, `aod_mean`, `uv_aerosol_index_mean`, `wind_speed_mean`, `wind_dir_dominant`, `transport_flag` |

> **Wind-transport context (NASA POWER):** `wind_speed_mean` / `wind_dir_dominant`
> carried by `serving_dust_event_daily` originate from the NASA POWER wind context
> joined upstream in 11b; `transport_flag` marks corridor-driven dust import.

## Layout (wireframe — Air Quality tab)

```
+---------------------------------------------------------------+
| AIR QUALITY & DUST  [Air Quality][Dust][Details]        [ ▾ ] |
+------------------------+--------------------------------------+
| AQI Exceedance Days    | AQI Band Distribution (pie)          |
|        12              |  Good / Moderate / Unhealthy / …     |
+------------------------+--------------------------------------+
| PM2.5 / PM10 Trend (line)                                     |
+---------------------------------------------------------------+
```

```
+---------------------------------------------------------------+
| … [Dust]                                                      |
+------------------------+--------------------------------------+
| Active Dust Days       | Dust Severity Distribution (pie)     |
|        4               |  Clear / Hazy / Dusty / Heavy / …    |
+------------------------+--------------------------------------+
| AOD (Dust) Trend (bar)         | Dust-flag Calendar           |
+-------------------------------+-------------------------------+
```

## Filters & Cross-filtering

- Global time range + AOI selector (`aoi_name`) shared across Air Quality / Dust.
- Clicking an AQI band slice cross-filters the PM trend and the detail table.
- Selecting a dust severity slice cross-filters the AOD trend + calendar.

## Alerts (see [../alerts/alert-strategy.md](../alerts/alert-strategy.md))

- **AQI exceedance** — new `air_quality_daily.exceedance_flag = true`.
- **High-AOD dust event** — `dust_event_daily.aod_max` above the heavy-dust band.

## Alignment

- Certified 11b products only (no Silver/Gold, no ad-hoc SQL) — ADR-BI-03.
- Same deck.gl AOI-map + certified-dataset pattern as
  [earth-observation-dashboard.md](./earth-observation-dashboard.md).
- KPIs single-sourced in [../kpis/kpi-catalog.md](../kpis/kpi-catalog.md).

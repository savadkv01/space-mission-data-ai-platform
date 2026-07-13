# Weather & Climate Dashboard  `real`

> Phase 12 · Task 2 (spec) → **Phase 12b · Task 3 (promoted sim → real)**
> Audience: **Climate / Air-Quality / Operations** · Superset slug: `weather`
> Roles: `ops_climate`, `ops_airquality` (+ `exec` read)

## Promotion Note (12b)

This dashboard was originally a **Simulation-Track demonstrator** that fused real
NOAA SWPC Kp with synthetic telemetry anomaly rate (dataset `weather_impact`,
tagged `sim`, ADR-09). In Phase 12b it is **repointed to real certified climate /
air-quality products** from Phase 11b. The layout is preserved; only the datasets
and KPIs change, and the `sim` tag is removed.

| Aspect | Before (sim) | After (real, 12b) |
| --- | --- | --- |
| Primary dataset | `weather_impact` (Gold httpfs) | `climate_daily` (`serving_agg.mv_kpi_climate_daily`) |
| Supporting | — | `dust_event_daily`, `climate_indicator_daily` |
| Track tag | `sim` | `real` |
| Role | `demo` | `ops_climate` / `ops_airquality` / `exec` |

> The original space-weather (Kp) demonstrator is retained on the
> **Simulation-Track dashboard** so no capability is lost.

## KPI Tiles

| Tile | KPI | Dataset · column | Definition | Band |
| --- | --- | --- | --- | --- |
| Air Quality | Mean AQI (PM2.5) | `climate_daily.mean_aqi_pm25` | window mean AQI | ≤50 good / 51–100 moderate / >100 unhealthy |
| Exceedances | AQI Exceedance Days | `climate_daily.aqi_exceedance_days` | Σ AOI-days over WHO guideline | trend |
| Dust | Active Dust Days | `climate_daily.dust_event_days` | Σ dust-flag days | ≥5 alert |
| Temperature | Mean LST Anomaly | `climate_daily.mean_lst_anomaly` | window mean LST anomaly (°C) | ≥+2 °C red |

## Charts

| Chart | Type | Columns |
| --- | --- | --- |
| Mean AQI (PM2.5) | big number | `climate_daily.mean_aqi_pm25` |
| AQI & Exceedance Trend | line | `kpi_date`, `mean_aqi_pm25`, `aqi_exceedance_days` |
| Dust-day Calendar | calendar heatmap | `event_date`, `dust_days` (`dust_event_daily`) |
| LST Anomaly Trend | line | `kpi_date`, `mean_lst_anomaly` |

## Layout (wireframe — preserved)

```
+---------------------------------------------------------------+
| WEATHER & CLIMATE  `real`                              [ ▾ ]   |
+---------------------------------------------------------------+
| Mean AQI (PM2.5)                                              |
|        63                                                    |
+---------------------------------------------------------------+
| AQI & Exceedance Trend (line)                                |
+-------------------------------+-------------------------------+
| Dust-day Calendar             | LST Anomaly Trend (line)      |
+-------------------------------+-------------------------------+
```

## Filters

- Global time range (default 30 days).

## Alignment

- Promoted to real certified 11b products (`mv_kpi_climate_daily`,
  `serving_dust_event_daily`, `serving_climate_indicator_daily`).
- KPIs single-sourced in [../kpis/kpi-catalog.md](../kpis/kpi-catalog.md).
- Superset export: [../superset/dashboards/weather-dashboard.yaml](../superset/dashboards/weather-dashboard.yaml).

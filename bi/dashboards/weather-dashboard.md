# Space Weather Dashboard  `sim`

> Phase 12 · Task 2 — Dashboard Catalog · Audience: **Platform Engineers / Demo**
> Superset slug: `weather` · Role: `demo` · **Simulation-Track (post-MVP, ADR-09)**

## Scope Note

Space-weather forecasting support is a **post-MVP expansion candidate** — retained
here as a demonstrator that fuses **real NOAA SWPC Kp** data with the synthetic
telemetry anomaly rate. Because it depends on the sim telemetry for the impact
join, the dashboard is tagged `sim`.

## KPI Tiles (dataset `weather_impact`)

| Tile | KPI | Column | Definition | Band |
| --- | --- | --- | --- | --- |
| Solar / Geomagnetic Activity | Max Kp index | `max_kp_index` | daily peak Kp | ≥5 storm |
| Radiation Index (proxy) | Mean Kp index | `mean_kp_index` | daily mean Kp | — |
| Geomagnetic Storms | Storm events | `storm_events` | count of storm periods | trend |
| Weather Alerts | Storm days | `storm_day` | days with Kp≥5 | red when true |
| Telemetry Impact | Anomaly rate | `anomaly_rate` | anomalies / samples on storm days | correlate |

> "Radiation Index" is proxied by the Kp mean (the sim mart does not carry a
> distinct radiation measure). The value of this dashboard is the **correlation**
> between geomagnetic storms and telemetry anomaly rate.

## Charts

| Chart | Type | Columns |
| --- | --- | --- |
| Kp index trend (max/mean) | line | `weather_date`, `max_kp_index`, `mean_kp_index` |
| Storm-day calendar | calendar heatmap | `weather_date`, `storm_day` |
| Storm events by day | bar | `weather_date`, `storm_events` |
| Anomaly rate vs Kp | scatter | `max_kp_index`, `anomaly_rate` |

## Layout (wireframe)

```
+---------------------------------------------------------------+
| SPACE WEATHER  `sim`                                   [ ▾ ]   |
+------------+------------+------------+------------+
| Max Kp     | Mean Kp    | Storm      | Storm      |
| (window)   |            | Events     | Days       |
|   6        |   3.1      |   4        |   2        |
+------------+------------+------------+------------+
| Kp index trend (max/mean, line)                              |
+---------------------------------------------------------------+
| Storm-day calendar            | Anomaly rate vs Kp (scatter)  |
+-------------------------------+-------------------------------+
```

## Filters

- Time range; storm-day toggle (`storm_day = true`).

## Alignment

- Post-MVP expansion; ADR-09. Data product `gold.fact_weather_impact` →
  [weather_impact dataset](../datasets/sql/weather_impact.sql).
- Kp source is real (NOAA SWPC); impact join uses sim telemetry.

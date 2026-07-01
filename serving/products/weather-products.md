# Space Weather Data Products (Simulation Track)

> **Post-MVP demonstrator on synthetic data (ADR-09).** Space-weather forecasting
> support was a deferred expansion candidate; the impact mart runs on synthetic
> telemetry. Marked `track = sim`.

Built by `serve_weather_impact` in [../marts/serving_marts.py](../marts/serving_marts.py).

> **Note.** Real NOAA SWPC Kp-index and NASA POWER connectors exist in ingestion,
> so `mean_kp_index` / `max_kp_index` can be sourced from real data; the *impact
> correlation* to telemetry anomalies is synthetic (no real spacecraft anomalies),
> which is why the product stays in the Simulation Track.

---

## Solar Activity

| Attribute | Value |
| --- | --- |
| Product | `serving_weather_impact` (Kp fields) |
| Purpose | Daily geomagnetic activity index |
| Owner | Simulation Track |
| Consumers | AI/ops dashboard (demo) |
| Refresh | Daily (sim) |
| SLA | Demo-only |
| Source | `fact_weather_impact` |
| Grain | 1 row / day |
| KPIs | max_kp_index, mean_kp_index, storm_events, storm_day flag |

---

## Radiation / Storm Index

| Attribute | Value |
| --- | --- |
| Product | derived from `serving_weather_impact` (`storm_day`) |
| Purpose | Geomagnetic-storm day classification |
| Owner | Simulation Track |
| Consumers | AI/ops dashboard (demo) |
| Refresh | Daily (sim) |
| SLA | Demo-only |
| Source | `fact_weather_impact` |
| Grain | 1 row / day |
| KPIs | storm_day = max_kp_index ≥ 5 |

---

## Weather Impact

| Attribute | Value |
| --- | --- |
| Product | `serving_weather_impact` (`anomaly_rate`) |
| Purpose | Correlate geomagnetic activity with telemetry anomaly rate (sim) |
| Owner | Simulation Track |
| Consumers | Anomaly-ML demonstrator |
| Refresh | Daily (sim) |
| SLA | Demo-only |
| Source | `fact_weather_impact` (synthetic telemetry join) |
| Grain | 1 row / day |
| KPIs | anomaly_rate vs Kp correlation |

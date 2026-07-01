# Satellite Operations Data Products (Simulation Track)

> **Post-MVP demonstrator on synthetic data (ADR-09).** These products are
> retained to exercise streaming + time-series anomaly ML that the batch EO path
> does not. They are marked `track = sim` and MUST NOT be presented as validated
> operational analytics.

Built by `serve_satellite_health` in [../marts/serving_marts.py](../marts/serving_marts.py).

---

## Satellite Health Summary

| Attribute | Value |
| --- | --- |
| Product | `serving_sat_health` |
| Purpose | Daily per-satellite health score + status band (sim) |
| Owner | Simulation Track (platform demo) |
| Consumers | Operations dashboard (demo), anomaly-ML demonstrator |
| Refresh | Streaming rollup → daily snapshot (sim) |
| SLA | Demo-only (no production SLA) |
| Source | `fact_sat_health` (synthetic telemetry) |
| Grain | 1 row / satellite / day |
| KPIs | health_score, anomaly_density, status (nominal/degraded/critical) |

---

## Satellite Availability

| Attribute | Value |
| --- | --- |
| Product | derived from `serving_sat_health` (status = nominal share) |
| Purpose | Uptime / availability demonstrator |
| Owner | Simulation Track |
| Consumers | Operations dashboard (demo) |
| Refresh | Daily (sim) |
| SLA | Demo-only |
| Source | `fact_sat_health` |
| Grain | 1 row / satellite / day |
| KPIs | availability = share of nominal samples |

---

## Telemetry KPI

| Attribute | Value |
| --- | --- |
| Product | streaming 1-minute window mart (`stream_sat_health_1m`) |
| Purpose | Near-real-time telemetry aggregates for the streaming demo |
| Owner | Simulation Track |
| Consumers | Streaming demo, anomaly detection |
| Refresh | 1-minute tumbling window (Structured Streaming) |
| SLA | Demo-only |
| Source | synthetic telemetry stream |
| Grain | 1 row / satellite / minute |
| KPIs | sample count, anomaly rate, mean battery voltage |

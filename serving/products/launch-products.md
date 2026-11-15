# Launch Analytics Data Products (Simulation Track)

> **Post-MVP demonstrator on synthetic data (ADR-09).** Launch operations were
> excluded from the MVP (rare events, sparse open data). Marked `track = sim`.

Built by `serve_launch_monthly` in [../marts/serving_marts.py](../marts/serving_marts.py).

---

## Launch Performance

| Attribute | Value |
| --- | --- |
| Product | `serving_launch_monthly` |
| Purpose | Monthly launch performance per provider (sim) |
| Owner | Simulation Track |
| Consumers | Analytics dashboard (demo) |
| Refresh | Monthly (sim) |
| SLA | Demo-only |
| Source | `kpi_launch_monthly` (synthetic) |
| Grain | 1 row / provider / month |
| KPIs | launches, successes, success_rate, mean_delay_days |

**Availability:** the canonical Gold reader has no launch input, so
`kpi_launch_monthly` is currently schema-only. Zero rows means **unavailable
data, not zero launches**. `launch_monthly_availability()` reports
`data_availability = 'unavailable'`; the Superset `launch_monthly` dataset
returns one `unavailable` row with NULL measures (so `SUM(launches)` is NULL,
not 0); and the batch DAG logs empty Gold marts with
`data_availability = unavailable`.

---

## Launch Delays

| Attribute | Value |
| --- | --- |
| Product | derived from `serving_launch_monthly` (`mean_delay_days`) |
| Purpose | Delay trend per provider |
| Owner | Simulation Track |
| Consumers | Analytics dashboard (demo) |
| Refresh | Monthly (sim) |
| SLA | Demo-only |
| Source | `kpi_launch_monthly` |
| Grain | 1 row / provider / month |
| KPIs | mean_delay_days trend |

---

## Launch Success Rate

| Attribute | Value |
| --- | --- |
| Product | derived from `serving_launch_monthly` (`success_rate`) |
| Purpose | Provider reliability metric |
| Owner | Simulation Track |
| Consumers | Analytics dashboard (demo) |
| Refresh | Monthly (sim) |
| SLA | Demo-only |
| Source | `kpi_launch_monthly` |
| Grain | 1 row / provider / month |
| KPIs | success_rate = successes / launches |

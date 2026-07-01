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

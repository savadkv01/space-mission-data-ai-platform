# Launch Operations Dashboard  `sim`

> Phase 12 · Task 2 — Dashboard Catalog · Audience: **Platform Engineers / Demo**
> Superset slug: `launch` · Role: `demo` · **Simulation-Track (post-MVP, ADR-09)**

## Scope Note

Launch operations analytics is **excluded from the MVP** (rare events, sparse open
data, difficult demonstration quality — see
[../../docs/business/05-mvp-definition.md](../../docs/business/05-mvp-definition.md)).
It is retained as a synthetic demonstrator. All charts are labelled `sim`.

## KPI Tiles (dataset `launch_monthly`)

| Tile | KPI | Column | Definition | Band |
| --- | --- | --- | --- | --- |
| Launch Success Rate | Launch Success Rate | `success_rate` | successes / launches | ≥0.9 good |
| Launch Timeline | launches per month | `launches` | count per provider/month | trend |
| Delays | Mean delay | `mean_delay_days` | avg schedule slip | lower better |
| Vehicle Statistics | cadence | `cadence_per_month` | launch cadence | informational |
| Failure Causes | failures | `launches - successes` | derived count | trend |

> The sim launch mart does not model detailed failure-cause taxonomy; "Failure
> Causes" is shown as a failed-count trend (`launches − successes`). A richer
> cause breakdown is a post-MVP expansion.

## Charts

| Chart | Type | Columns |
| --- | --- | --- |
| Success rate trend | line | `month_key`, `success_rate` |
| Launches by provider | bar | `provider_key`, `launches` |
| Delay distribution | box/bar | `mean_delay_days` |
| Failures by month | bar | `month_key`, `launches - successes` |
| Provider detail | table | all columns |

## Layout (wireframe)

```
+---------------------------------------------------------------+
| LAUNCH OPERATIONS  `sim`                               [ ▾ ]   |
+------------+------------+------------+------------+
| Success    | Launches   | Mean Delay | Cadence    |
| Rate       | (window)   | (days)     | /month     |
|  0.92      |   14       |   2.1      |   1.8      |
+------------+------------+------------+------------+
| Success rate trend (line)     | Launches by provider (bar)    |
+-------------------------------+-------------------------------+
| Failures by month (bar)       | Provider detail (table)       |
+-------------------------------+-------------------------------+
```

## Filters

- Time range (month grain), provider (`provider_key`).

## Alignment

- Sim track / ADR-09; data product `gold.kpi_launch_monthly` →
  [launch_monthly dataset](../datasets/sql/launch_monthly.sql).
- Note: launch data is currently 0-row until a launch source is ingested; the
  path is fully wired (see repo OPERATIONS notes).

# Satellite Operations Dashboard  `sim`

> Phase 12 · Task 2 — Dashboard Catalog · Audience: **Platform Engineers / Demo**
> Superset slug: `satellite` · Role: `demo` · **Simulation-Track (post-MVP, ADR-09)**

## Scope Note

Spacecraft telemetry health is **excluded from the MVP** (public telemetry realism
scored 1/5, see [../../docs/business/05-mvp-definition.md](../../docs/business/05-mvp-definition.md)).
This dashboard runs on **synthetic** data from the ingestion simulation generators
and is retained as a streaming/time-series demonstrator. Every chart title carries
a `sim` tag so it is never mistaken for a real-data KPI.

## KPI Tiles (dataset `sat_health`)

| Tile | KPI | Column | Definition | Band |
| --- | --- | --- | --- | --- |
| Satellite Health | Mean Satellite Health | `health_score` | avg health score | ≥0.8 nominal |
| Telemetry Status | status distribution | `status` | nominal/degraded/critical | — |
| Sensor Performance | anomaly density | `anomaly_density` | anomalies / samples | lower better |
| Communication Availability | uptime proxy | `samples` | telemetry samples received | informational |
| Orbit Stability | battery drift proxy | `battery_voltage_drift` | drift over window | near 0 |

> `sat_health` exposes health, anomaly and battery-drift measures. Orbit stability
> and communication availability are **proxied** from these synthetic fields — the
> sim track does not model true orbit/comms telemetry.

## Charts

| Chart | Type | Columns |
| --- | --- | --- |
| Health status distribution | pie | `status` |
| Mean health by day | line | `health_date`, `health_score` |
| Anomaly density by satellite | bar | `sat_key`, `anomaly_density` |
| Battery voltage drift | line | `health_date`, `battery_voltage_drift` |
| Satellite detail | table | all columns |

## Layout (wireframe)

```
+---------------------------------------------------------------+
| SATELLITE OPERATIONS  `sim`                            [ ▾ ]   |
+------------+------------+------------+------------+
| Mean       | Nominal    | Anomaly    | Battery    |
| Health     | Share      | Density    | Drift      |
|  0.86      |  78%       |  0.03      |  -0.01     |
+------------+------------+------------+------------+
| Health status (pie)          | Mean health by day (line)      |
+-------------------------------+-------------------------------+
| Anomaly density by satellite | Satellite detail (table)       |
+-------------------------------+-------------------------------+
```

## Filters

- Time range, satellite (`sat_key`), status.

## Alignment

- Sim track defined in
  [../../docs/business/05-mvp-definition.md](../../docs/business/05-mvp-definition.md)
  (Simulation Track section) and ADR-09.
- Data product: `gold.fact_sat_health` →
  [sat_health dataset](../datasets/sql/sat_health.sql).

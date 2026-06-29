# 11 - Data Granularity Strategy

> **Phase 6 - Data Modeling** · Document 11 of 18

| Granularity | Example | When used |
| --- | --- | --- |
| Event-level | fire detection, launch | source-of-truth, audit |
| Time-series | telemetry per minute | anomaly/trend ML |
| Aggregated KPI | daily fires by AOI | dashboards, reporting |
| Snapshot | sat health end-of-day | point-in-time state |

## Guidance

- Keep finest grain in Silver; aggregate in Gold.
- Snapshots for slowly-changing state; events for activity; KPIs for serving.

## Cross References

- [06-time-series-model.md](06-time-series-model.md) · [04-gold-layer.md](04-gold-layer.md)

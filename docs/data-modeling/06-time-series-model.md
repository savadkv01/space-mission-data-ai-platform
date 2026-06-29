# 06 - Time-Series Data Model

> **Phase 6 - Data Modeling** · Document 06 of 18

## Scope

Telemetry, orbit positions, and sensor readings modeled as append-only time series.

## Grain & Schema

| Series | Grain | Key columns |
| --- | --- | --- |
| `ts_telemetry` | sat+sensor+timestamp | sat_key, sensor_key, ts, value |
| `ts_orbit` | sat+timestamp | sat_key, ts, lat, lon, alt, vel |
| `ts_sensor` | sensor+timestamp | sensor_key, ts, metric, value |

## Partitioning

- Time-based: hour for live, day for historical; mission_id sub-partition.

## Windowing

| Window | Use |
| --- | --- |
| Tumbling 1m | anomaly detection |
| Sliding 5m | smoothing |
| Session | pass/contact windows |

## Aggregation Levels

| Level | Retention | Table |
| --- | --- | --- |
| Minute | 30 days | raw `ts_*` |
| Hour | 1 year | `ts_*_hourly` |
| Day | 5 years | `ts_*_daily` |

## Cross References

- [11-granularity.md](11-granularity.md) · [13-data-lifecycle.md](13-data-lifecycle.md)

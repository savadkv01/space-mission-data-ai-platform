# 12 - Data Partitioning Strategy

> **Phase 6 - Data Modeling** · Document 12 of 18

| Strategy | Key | Datasets |
| --- | --- | --- |
| Time-based | date/hour | telemetry, weather, alerts |
| Mission-based | mission_id | mission-scoped facts |
| Satellite-based | sat_key | orbit, health |
| Hybrid | date + region | EO imagery, fire/flood |

## Guidance

- Default: date partition + low-cardinality region/mission sub-partition.
- Avoid over-partitioning on 16 GB laptop; target file sizes 128–512 MB.

## Cross References

- [02-bronze-layer.md](02-bronze-layer.md) · [14-performance.md](14-performance.md)

# 04 Data Quality Assessment

## Executive Summary

Quality risks are assessed per category against seven dimensions: missing data, timestamp consistency, availability latency, sensor noise, geospatial accuracy, API reliability, and schema stability. This drives the cleaning effort estimates in the transformation-complexity document.

## Quality Matrix by Category

| Category | Missing Data | Timestamps | Latency | Noise | Geo Accuracy | API | Schema |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Satellite Telemetry | Medium | Medium | Low | High | Low | Medium | Medium |
| Earth Observation | High (cloud) | Low | Medium | Medium | Low | Medium | Low |
| Space Weather | Low | Low | Low | Medium | N/A | Low | Low |
| Orbital Mechanics | Low | Medium (epoch) | Low | Low | N/A | Low | Low |
| Launch | Medium | Medium (slip) | Low | Low | N/A | Medium | Low |
| Astronomical | Low | Low | Low | Low | N/A | Low | Low |
| Environmental | Medium | Low | High | Medium | Medium | Medium | Low |
| Simulation | Low | Low | Low | Controlled | N/A | Low | Low |

## Key Risks

- **Cloud occlusion (EO):** optical scenes unusable under cloud; mitigated by SAR and Sentinel Hub indices.
- **Inconsistent timestamps:** epoch formats (TLE day-of-year, Unix, ISO) and time zones require UTC normalization.
- **Delayed availability:** ERA5 ~5-day lag; EMS event-driven; FIRMS ~3 hr.
- **Sensor noise:** telemetry spikes and AIS spoofing demand outlier filtering.
- **Geo accuracy:** point detections (FIRMS) coarse; needs tolerance buffers in joins.
- **Schema drift:** community APIs (SpaceX, Heavens-Above) may change without notice.

## Cleaning Priorities

1. UTC timestamp normalization across all sources.
2. Cloud masking and quality-flag filtering for EO.
3. Outlier removal for telemetry and AIS.
4. Spatial buffering for cross-source joins.

## Cross References

- Phase 2 quality: [../domain-research/05-data-quality-assessment.md](../domain-research/05-data-quality-assessment.md)
- Transformation: [06-transformation-complexity.md](./06-transformation-complexity.md)

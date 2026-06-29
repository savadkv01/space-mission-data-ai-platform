# 09 Data Risks & Constraints

## Executive Summary

Source-data risks span rate limits, gaps, geospatial inconsistencies, time zones, calibration, licensing, and duplication. Each is documented with mitigation.

## Risk Register

| Risk | Affected | Severity | Mitigation |
| --- | --- | --- | --- |
| API rate limits | LL2, NeoWs, N2YO | Medium | Cache, backoff, free keys |
| Missing historical data | telemetry, AIS | Medium | Synthetic + anomaly datasets |
| Geospatial inconsistency | FIRMS, AIS | Medium | Buffered joins, reprojection |
| Time zone issues | all | High | UTC normalization |
| Sensor calibration | telemetry, EO | Medium | Quality flags, calibration meta |
| Licensing | mostly open | Low | Verify attribution terms |
| Duplication | FIRMS+VIIRS, MODIS | Medium | Dedup by id+time+geo |
| Schema drift | SpaceX, scrapers | Medium | Schema checks, contracts |
| Download queues | ERA5, CAMS, Sentinel | High | Pre-stage, subset AOIs |

## Cross References

- Phase 2 risks: [../domain-research/08-data-risks.md](../domain-research/08-data-risks.md)
- Quality: [04-data-quality-assessment.md](./04-data-quality-assessment.md)

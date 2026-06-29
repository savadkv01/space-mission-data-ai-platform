# 06 Transformation Complexity

## Executive Summary

Each dataset is classified Low/Medium/High transformation complexity based on cleaning needs, schema complexity, joins, geospatial processing, and time-series alignment. This guides ingestion effort estimation.

## Complexity by Dataset

| Dataset | Cleaning | Schema | Joins | Geo | Time | Overall |
| --- | --- | --- | --- | --- | --- | --- |
| FIRMS/VIIRS | Low | Low | Med | Low | Low | Low |
| NASA POWER | Low | Low | Low | Low | Low | Low |
| SWPC/GOES | Low | Low | Low | N/A | Med | Low |
| Launch Library 2 | Low | Med | Low | Low | Low | Low |
| CelesTrak TLE | Med | Med | Med | N/A | High | Medium |
| Sentinel-2 | High | Med | Med | High | Med | High |
| Sentinel-1 SAR | High | High | Med | High | Med | High |
| Landsat | High | Med | Med | High | Med | High |
| ERA5/CAMS | Med | High | Med | High | High | High |
| GFW/AIS | Med | Med | High | Med | High | High |
| EMS | Med | Med | Low | High | Low | Medium |
| Sentinel Hub | Low | Low | Low | Med | Low | Low |

## Drivers

- **High:** raster processing, reprojection, large volume, time alignment (Sentinel, ERA5, AIS).
- **Medium:** epoch parsing, moderate joins (TLE, EMS).
- **Low:** flat APIs with clean schemas (FIRMS, POWER, SWPC).

## Cross References

- Quality: [04-data-quality-assessment.md](./04-data-quality-assessment.md)
- Prioritization: [10-data-prioritization.md](./10-data-prioritization.md)

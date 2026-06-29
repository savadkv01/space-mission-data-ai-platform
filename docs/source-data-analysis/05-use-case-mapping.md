# 05 Use-Case Mapping

## Executive Summary

This maps datasets to Phase 1 business problems, confirming each MVP use case is covered and showing where each dataset adds value. Mapping connects raw sources to the AI/ML and analytics targets.

## Dataset-to-Use-Case Map

| Use Case | Primary Datasets | Supporting | AI/ML Pattern |
| --- | --- | --- | --- |
| UC-15 Wildfire | FIRMS, VIIRS, Sentinel-2 | NASA POWER, GFW, MODIS | Classification + change detection |
| UC-16 Flood | Sentinel-1 SAR, Copernicus EMS | Sentinel-2, NASA POWER | Segmentation |
| UC-18 Illegal fishing | Global Fishing Watch | AIS streams | Anomaly detection |
| UC-27 Damage assessment | Sentinel-2, Sentinel-1 | EMS | Classification/ranking |
| UC-14 Change detection | Sentinel-2, Landsat | Sentinel Hub | Differencing/ML |
| UC-25 Metadata quality | Earthdata, all metadata | — | Cataloging/validation |
| UC-21 Space weather (future) | SWPC, DONKI, GOES | OMNIWeb, Kp | Forecasting |
| UC-01/03 Telemetry anomaly (future) | NASA anomaly dataset, synthetic | N2YO, SatNOGS | Anomaly detection |

## Category Mapping

- Satellite telemetry → anomaly detection
- Space weather → prediction models
- Launch data → delay prediction
- Earth observation → classification/segmentation
- Orbital → revisit/geometry context
- Environmental → risk drivers

## Cross References

- Business problems: [../business/02-business-problems.md](../business/02-business-problems.md)
- MVP datasets: [11-mvp-datasets.md](./11-mvp-datasets.md)

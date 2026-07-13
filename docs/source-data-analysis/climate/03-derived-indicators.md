# 03 Derived Climate Indicators (No New Ingestion)

> Indicators computable from sources the platform **already ingests** (Phase 5/8). These require **zero new connectors** — they are transformation logic over existing Bronze/Silver, not new data sources.

## Executive Summary

The platform already ingests the optical, thermal, and ocean inputs needed to derive a robust climate-change indicator suite. This document maps each indicator to its existing source(s) and gives the **conceptual formula only** (no code, no ingestion design). All indicators land as derived Silver/Gold products keyed by `aoi_id` + date, joining directly to the new atmospheric sources for cross-domain analysis.

> Explicit statement: **every indicator below requires zero new ingestion connectors.** They reuse MODIS/Landsat, Sentinel-2, NOAA OISST, and Global Forest Watch data already flowing through the platform.

## Source → Indicator Mapping

| Indicator | Already-Ingested Source(s) | Conceptual Formula | Cadence | New Connector? |
| --- | --- | --- | --- | --- |
| NDVI | Sentinel-2 (B8, B4), MODIS surface reflectance | `(NIR − Red) / (NIR + Red)` | S2 ~5-day / MODIS 16-day | No |
| EVI | Sentinel-2 (B8, B4, B2) | `2.5 · (NIR − Red) / (NIR + 6·Red − 7.5·Blue + 1)` | ~5–16 day | No |
| Land Surface Temperature (LST) | MODIS LST product, Landsat thermal (B10/B11) | Retrieved LST (K) → °C; split-window for Landsat | MODIS daily / Landsat 16-day | No |
| LST anomaly | Derived LST + rolling climatology | `LST(t) − mean(LST over baseline period, same DOY window)` | Matches LST | No |
| Sea Surface Temperature (SST) | NOAA OISST | Retrieved SST (°C) per AOI | Daily | No |
| SST anomaly | Derived SST + OISST climatology | `SST(t) − climatological_mean(SST, same DOY)` | Daily | No |
| NDWI / water availability | Sentinel-2 (B3, B8) | `(Green − NIR) / (Green + NIR)` | ~5–16 day | No |
| Deforestation / tree-cover loss | Global Forest Watch | Annual tree-cover-loss area within AOI | Annual | No |
| Desertification proxy | Derived NDVI trend + LST | Negative NDVI slope over years **and** rising LST → desertification flag | Seasonal/annual | No |
| Snow-cover proxy | MODIS NDSI / Sentinel-2 (B3, B11) | `NDSI = (Green − SWIR)/(Green + SWIR)`; threshold → snow mask | ~daily/16-day | No |

## Indicator Notes

- **Anomalies over absolutes.** Climate signal lives in the *anomaly* (departure from a same-day-of-year baseline), not the raw value. LST/SST anomalies use a rolling climatological baseline built from the historical archive the platform already ingests.
- **Desertification is a composite.** No single band gives it — it is inferred from a **multi-year NDVI decline co-located with LST increase** inside desert-margin AOIs (`AOI-DESERT`). Treat as a proxy/flag, not a measurement.
- **Cloud masking is a prerequisite.** Optical indicators (NDVI/EVI/NDWI/NDSI) must drop cloud-contaminated pixels before AOI aggregation (see [`04-climate-data-quality.md`](./04-climate-data-quality.md)).
- **AOI aggregation.** Each indicator is aggregated to `aoi_id` (mean/percentiles) so it shares the join grain of TROPOMI/AOD atmospheric stats.

## Climate-Change Indicator Coverage

| Climate Dimension | Indicator(s) | Source Family |
| --- | --- | --- |
| Vegetation health | NDVI, EVI | Sentinel-2, MODIS |
| Urban heat / warming | LST, LST anomaly | MODIS, Landsat thermal |
| Ocean warming | SST, SST anomaly | NOAA OISST |
| Water availability | NDWI | Sentinel-2 |
| Land degradation | Desertification proxy | Derived (NDVI trend + LST) |
| Forest / carbon | Tree-cover loss | Global Forest Watch |
| Cryosphere (marginal for UAE) | Snow-cover proxy | MODIS/Sentinel-2 |

## Cross References

- Inventory (derived class S-104): [`01-climate-dataset-inventory.md`](./01-climate-dataset-inventory.md)
- Quality (cloud masking, QA flags): [`04-climate-data-quality.md`](./04-climate-data-quality.md)
- Use cases (climate monitoring): [`05-climate-use-case-mapping.md`](./05-climate-use-case-mapping.md)
- Phase 5 derived-source precedent: [`../06-transformation-complexity.md`](../06-transformation-complexity.md)

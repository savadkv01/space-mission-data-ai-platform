# 06 Climate / Air-Quality Transformation Complexity

> Classifies each IN-scope source Low / Medium / High transformation complexity based on cleaning, unit harmonization, spatial aggregation, and time alignment. Documentation only — no pipeline design.

## Executive Summary

Because all IN-scope sources use the tabular / statistical-API pattern (Strategy A), none require raster or NetCDF decoding — the hard complexity (blob landing, xarray) was deliberately deferred. Remaining complexity is concentrated in **unit harmonization** (µg/m³ vs mol/m² vs unitless), **QA-flag filtering**, and **time alignment to a daily AOI grain**. Derived indicators are the lightest (no ingest) except for the desertification proxy, which needs multi-year trend fitting.

## Complexity Dimensions

| Dimension | What it covers |
| --- | --- |
| Cleaning | QA/cloud filtering, dedup, null handling |
| Unit harmonization | Normalizing heterogeneous units to a canonical set |
| Spatial aggregation | Reducing points/pixels to an `aoi_id` statistic |
| Time alignment | UTC normalization + join to common daily grain |

## Per-Source Classification

| Source | Cleaning | Unit Harmon. | Spatial Agg. | Time Align. | Overall |
| --- | --- | --- | --- | --- | --- |
| OpenAQ | Medium (dedup, outages, mixed methods) | Medium (µg/m³, ppm, ppb per pollutant) | Low (point → AOI membership) | Medium (hourly → daily, tz) | **Medium** |
| TROPOMI (SH Stats) | Low-Med (QA already applied in evalscript) | Medium (mol/m², ppb; column semantics) | Low (API returns AOI aggregate) | Low (daily native) | **Medium** |
| MODIS/VIIRS AOD | Medium (QA flags, desert bias, MODIS↔VIIRS) | Low (unitless) | Low-Med (point/stats → AOI) | Low (daily) | **Medium** |
| Derived: NDVI/EVI/NDWI/SST/LST anomalies | Low (reuses cleaned sources) | Low (consistent) | Low (inherits AOI grain) | Low | **Low** |
| Derived: desertification proxy | Medium (multi-year NDVI trend + LST fusion) | Low | Medium (trend per AOI) | Medium (multi-year baseline) | **Medium** |

## Complexity Drivers & Notes

- **Unit harmonization is the top driver.** Air-quality blending must keep raw + canonical columns and must never equate TROPOMI column density with OpenAQ surface concentration without an explicit documented step.
- **Server-side AOI aggregation lowers spatial complexity.** TROPOMI/AOD aggregation happens server-side in Google Earth Engine (`reduceRegion` mean/min/max/stdDev per AOI), so no local raster reduction is needed — a key reason it stays Strategy A / Medium rather than High.
- **AOD cross-sensor consistency.** MODIS and VIIRS AOD are not identical; harmonize or keep sensor as a dimension; apply desert bright-surface handling.
- **Desertification needs history.** The only derived indicator above Low — it requires a multi-year NDVI slope co-fitted with LST, so it depends on the historical archive already ingested.
- **No High-complexity IN-scope sources.** All High-complexity atmospheric work (NetCDF reanalysis, geostationary rasters) is deferred by scope — see [`09-climate-mvp-and-deferred.md`](./09-climate-mvp-and-deferred.md).

## Effort Summary

| Complexity | Sources |
| --- | --- |
| Low | Derived NDVI/EVI/NDWI/LST/SST anomalies |
| Medium | OpenAQ, TROPOMI (SH Stats), MODIS/VIIRS AOD, desertification proxy |
| High | *(none IN scope — deferred: CAMS/ERA5 NetCDF, geostationary)* |

## Cross References

- Quality (cleaning rules): [`04-climate-data-quality.md`](./04-climate-data-quality.md)
- Derived indicators: [`03-derived-indicators.md`](./03-derived-indicators.md)
- Deferred heavy sources: [`09-climate-mvp-and-deferred.md`](./09-climate-mvp-and-deferred.md)
- Phase 5 baseline: [`../06-transformation-complexity.md`](../06-transformation-complexity.md)

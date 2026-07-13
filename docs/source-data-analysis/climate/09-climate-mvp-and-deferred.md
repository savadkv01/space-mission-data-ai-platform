# 09 Climate-Expansion MVP & Deferred Sources

> Ranks the IN-scope sources and defines the climate-expansion MVP set. Explicitly lists what is excluded (CAMS/ERA5 NetCDF, geostationary) and why. Extends Phase 5 [`10-data-prioritization.md`](../10-data-prioritization.md) and [`11-mvp-datasets.md`](../11-mvp-datasets.md).

## Executive Summary

The climate-expansion MVP is **three atmospheric connectors plus a derived-indicator layer**, all fitting the existing Strategy-A pattern and 16 GB budget. This adds dust, air-quality, and climate-change monitoring with **no new ingestion subsystem**. Two heavy source families are deferred because they would require a NetCDF/binary blob-landing capability and compute that breaks the laptop constraint.

## Prioritization Ranking

| Rank | Source | Value | Effort | Fit (Strategy A / 16 GB) | Decision |
| --- | --- | --- | --- | --- | --- |
| 1 | TROPOMI (Google Earth Engine) | High (air quality + dust proxy + carbon) | Medium | Strong (GEE `reduceRegion` → same bucket shape) | **MVP Tier 1** |
| 2 | MODIS/VIIRS AOD | High (dust concentration, PM proxy) | Medium | Strong (point/stats) | **MVP Tier 1** |
| 3 | OpenAQ | High (ground truth / calibration) | Medium | Strong (tabular REST) | **MVP Tier 1** |
| 4 | Derived climate indicators | High (climate baseline) | Low (no ingest) | Strong (compute-only) | **MVP Tier 1 (free)** |
| — | CAMS / ERA5 NetCDF | High | High (new blob subsystem) | Breaks Strategy A | **Deferred** |
| — | Geostationary SEVIRI/Himawari | Medium-High | Very High | Breaks 16 GB budget | **Deferred** |

## Climate-Expansion MVP Set

| # | MVP Component | Unlocks | New Connector? |
| --- | --- | --- | --- |
| 1 | OpenAQ | Air-quality ground truth (UC-C3) | Yes (tabular REST) |
| 2 | TROPOMI via Google Earth Engine | NO₂/SO₂/CO/O₃/CH₄ + AER_AI (UC-C2, UC-C3) | GEE `reduceRegion` (free) |
| 3 | MODIS/VIIRS AOD | Dust/aerosol concentration (UC-C2) | Yes (point/stats) |
| 4 | Derived climate indicators | LST/SST/NDVI/NDWI anomalies, desertification (UC-C1) | **No — compute only** |

**MVP outcome:** dust-storm monitoring, air-quality monitoring, and climate-change monitoring — all AOI-bounded, all within budget.

## Explicitly Excluded (Deferred) — with Rationale

| Source | Why excluded now | What it would require | Revisit condition |
| --- | --- | --- | --- |
| **CAMS** (atmosphere reanalysis/forecast, raw NetCDF) | Native NetCDF/GRIB grids; breaks the tabular Strategy-A pattern | New binary **blob-landing** capability + xarray/eccodes decode stack + object-store layout for rasters | When a raster-landing subsystem is prioritized (post-MVP) |
| **ERA5** (Copernicus CDS, raw NetCDF) | Multi-GB global reanalysis grids; same NetCDF gap | Same blob-landing stack + CDS API async retrieval + large storage | Same as CAMS |
| **Geostationary SEVIRI / Himawari** (full-disk) | High-cadence full-disk rasters violate 16 GB / Docker budget | Dedicated compute + streaming raster store beyond laptop scope | Only with non-laptop infra |

> Design choice: **statistical/point access over AOIs (Strategy A)** was chosen over raster ingestion. Alternatives considered — (a) local AOI-clipped raster download + aggregate, (b) full CAMS/ERA5 NetCDF pipeline — both rejected for this phase because they reintroduce a binary blob-landing subsystem and exceed the memory/storage budget. The deferred items are documented so a future phase can adopt them deliberately, not by accident.

## What This Phase Does NOT Do

- No ingestion pipeline, connector code, or DAG design (that is Phase 8b).
- No schema/data-model design.
- No adoption of any deferred (OUT-of-scope) source.

## Cross References

- Inventory: [`01-climate-dataset-inventory.md`](./01-climate-dataset-inventory.md)
- Use cases: [`05-climate-use-case-mapping.md`](./05-climate-use-case-mapping.md)
- Freshness & risk: [`08-climate-freshness-risks.md`](./08-climate-freshness-risks.md)
- Phase 5 MVP: [`../11-mvp-datasets.md`](../11-mvp-datasets.md)
- Phase 5 future expansion: [`../12-future-expansion.md`](../12-future-expansion.md)

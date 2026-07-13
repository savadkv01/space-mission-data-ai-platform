# 02 Area-of-Interest (AOI) Strategy

> Defines the AOI-bounded ingestion strategy required to keep the climate/dust/air-quality expansion within the 16 GB RAM / Docker budget. Applies to all IN-scope sources in [`01-climate-dataset-inventory.md`](./01-climate-dataset-inventory.md).

## Executive Summary

AOI clipping is **mandatory, not optional**, for the atmospheric expansion. TROPOMI, MODIS/VIIRS AOD, and any raster-derived product are global/full-disk at source; ingesting them unclipped would blow the memory and storage budget and exceed Google Earth Engine per-request compute limits. Every statistical/point request is therefore bounded by a **named AOI bounding box** drawn from a single reusable reference table. AOIs are versioned as a seed (consistent with the existing `transformation/seeds/aoi_reference.geojson` pattern) so all downstream joins share one geometry source of truth.

## Why AOI Clipping Is Mandatory

| Driver | Consequence without AOI clipping |
| --- | --- |
| 16 GB RAM / Docker budget | Global rasters (TROPOMI, MODIS) cannot be held or processed in memory |
| Google Earth Engine compute limits | `reduceRegion` over a global geometry exceeds per-request pixel/compute limits and burns Earth Engine quota |
| AOI-statistics access (`reduceRegion`) | Returns aggregates per AOI polygon — an AOI geometry is a **required input**, not a filter |
| Storage on laptop | Full-disk/global daily grids are GBs/day; AOI stats are KBs/day |
| Analytical relevance | UAE use cases (dust, air quality) are regional; global pixels add no value |

> Design choice: **statistical/point access over an AOI**, not raster download. Alternative considered — download AOI-clipped rasters and aggregate locally — rejected because it reintroduces a NetCDF/GeoTIFF blob-landing capability that this phase explicitly keeps OUT of scope (see deferred sources).

## AOI Tiers

- **Primary AOIs** — UAE national + operational sub-regions (where air-quality and urban-heat questions are asked).
- **Secondary AOIs** — regional dust-source corridors upwind of the UAE (where dust plumes originate and transport from).

## Bounding-Box Reference Table

> Coordinates are approximate WGS84 (EPSG:4326) envelopes for AOI-clipping. `[min_lon, min_lat, max_lon, max_lat]`. Treat as a reusable seed; refine polygons for production.

### Primary AOIs (UAE)

| AOI ID | Name | min_lon | min_lat | max_lon | max_lat | Purpose |
| --- | --- | --- | --- | --- | --- | --- |
| AOI-UAE-NAT | UAE (national) | 51.0 | 22.5 | 56.5 | 26.2 | National air-quality & climate rollup |
| AOI-AUH | Abu Dhabi (emirate/urban) | 53.3 | 23.5 | 55.3 | 24.7 | Urban air quality, urban heat |
| AOI-DXB | Dubai (urban) | 54.9 | 24.8 | 55.6 | 25.4 | Urban air quality, NO₂ traffic proxy |
| AOI-COAST | UAE coastal zone (Arabian Gulf) | 51.5 | 24.0 | 56.4 | 26.1 | SST, coastal aerosol, humidity haze |
| AOI-DESERT | Desert interior (Empty Quarter margin) | 52.0 | 22.5 | 55.5 | 23.8 | Dust source/deposition, desertification |

### Secondary AOIs (Regional Dust Corridors)

| AOI ID | Name | min_lon | min_lat | max_lon | max_lat | Purpose |
| --- | --- | --- | --- | --- | --- | --- |
| AOI-ARABIA | Arabian Peninsula interior | 42.0 | 18.0 | 55.0 | 30.0 | Upwind dust source region |
| AOI-IRAQ | Iraq / Mesopotamia basin | 42.0 | 29.0 | 48.5 | 36.0 | Shamal dust source (Tigris–Euphrates) |
| AOI-IRAN | Iran SW basins | 47.0 | 28.0 | 55.0 | 34.0 | Cross-Gulf dust transport source |
| AOI-GULF | Arabian (Persian) Gulf water body | 48.0 | 24.0 | 57.0 | 30.5 | Marine aerosol, transport pathway |

## AOI-to-Source Applicability

| Source | Primary AOIs | Secondary AOIs | Notes |
| --- | --- | --- | --- |
| OpenAQ | UAE-NAT, AUH, DXB | — | Station-based; bbox filters stations; sparse in secondary AOIs |
| TROPOMI (SH Stats) | all primary | ARABIA, IRAQ, IRAN | One stats request per AOI per band per day |
| MODIS/VIIRS AOD | all primary | all secondary | Dust plume tracking needs upwind corridors |
| Derived indicators | all primary | as needed | Reuses source AOIs already ingested |

## Reuse & Governance

- Store AOIs as a **single versioned seed** (extend the existing `aoi_reference.geojson` convention) so ingestion, transformation, and BI share identical geometries — no per-request ad-hoc bboxes.
- Each stats/point request references an `aoi_id`; the `aoi_id` becomes a **join key** across atmospheric, weather, and fire data (see [`07-climate-data-relationships.md`](./07-climate-data-relationships.md)).
- Resolution is auto-coarsened per AOI so raster side ≤ SH max dimension (reuses the `_safe_resolution` guard already implemented for the Statistical API).

## Cross References

- Inventory: [`01-climate-dataset-inventory.md`](./01-climate-dataset-inventory.md)
- Relationships (AOI as join key): [`07-climate-data-relationships.md`](./07-climate-data-relationships.md)
- Risks (PU quota, area caps): [`08-climate-freshness-risks.md`](./08-climate-freshness-risks.md)

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
- **Regional tier (INDIA)** — focused Indian AOIs in their own analysis region; see [Analysis Regions](#analysis-regions).

## Bounding-Box Reference Table

> Coordinates are approximate WGS84 (EPSG:4326) envelopes for AOI-clipping. `[min_lon, min_lat, max_lon, max_lat]`. Treat as a reusable seed; refine polygons for production.
>
> **Reporting partition (ADR-12, 2026-11-15).** Within a region the AOIs below never overlap (shared edges only), so per-AOI counts add up to region totals without double counting. They are rectangles because every connector requests a bounding box. The former national box `AOI-UAE-NAT` (51.0–56.5°E, 22.5–26.2°N) is retired; the national view is the `sub_region = UAE` group. Event footprints such as `EMSR-AE-FLOOD-2024` are overlays (`rollup_eligible: false`) and are never summed.

### Primary AOIs (UAE, `sub_region = UAE`)

| AOI ID | Name | min_lon | min_lat | max_lon | max_lat | Purpose |
| --- | --- | --- | --- | --- | --- | --- |
| AOI-AUH | Abu Dhabi (emirate/urban) | 53.3 | 23.5 | 55.3 | 24.7 | Urban air quality, urban heat |
| AOI-DXB | Dubai (urban) | 54.9 | 24.8 | 55.6 | 25.4 | Urban air quality, NO₂ traffic proxy, NDVI/NDWI |
| AOI-COAST | UAE western coast & Abu Dhabi offshore (Al Dhafra) | 51.5 | 24.7 | 54.9 | 26.2 | Coastal aerosol, offshore maritime activity |
| AOI-NEM | Northern Emirates (RAK–Fujairah) | 55.6 | 24.8 | 56.5 | 26.2 | Northern Emirates air quality, coverage of the former national box |
| AOI-DESERT | Desert interior (Empty Quarter margin) | 52.0 | 22.5 | 55.5 | 23.5 | Dust source/deposition, desertification |

### Secondary AOIs (Regional Dust Corridors)

| AOI ID | Name | min_lon | min_lat | max_lon | max_lat | Purpose |
| --- | --- | --- | --- | --- | --- | --- |
| AOI-ARABIA | Arabian Peninsula interior (Najd–Dahna) | 42.0 | 18.0 | 48.0 | 29.0 | Upwind dust source region |
| AOI-ARABIA-E | Eastern Arabia (Al-Ahsa, Qatar, NE Rub al Khali) | 48.0 | 18.0 | 51.5 | 26.2 | Westerly dust source upwind of the UAE |
| AOI-IRAQ | Iraq / Mesopotamia basin | 42.0 | 29.0 | 48.0 | 36.0 | Shamal dust source (Tigris–Euphrates) |
| AOI-IRAN | Iran SW basins (Khuzestan–Zagros) | 48.0 | 30.5 | 55.0 | 34.0 | Cross-Gulf dust transport source |
| AOI-GULF | Arabian Gulf basin (north of the UAE coast) | 48.0 | 26.2 | 57.0 | 30.5 | Marine aerosol, maritime activity, transport pathway |

## Analysis Regions

Every AOI belongs to exactly one **analysis region** (`region` on the seed,
`ref_aoi`, `dim_aoi`, every AOI-grained serving product, and both rollups).
Regions are never combined: rollups are `(date_key, region)`, dust corridors
only consider AOIs of the same region, AQI uses the region's standard, and FIRMS
freshness is judged per region.

| Region | AOIs | AQI standard | FIRMS request | Status |
| --- | --- | --- | --- | --- |
| `UAE-GULF` | 10 UAE/corridor reporting AOIs + overlay `EMSR-AE-FLOOD-2024` | `US_EPA_PRE2024` (legacy EPA bands, V03) | One box `30,10,60,40` | Primary programme region |
| `INDIA` | 6 AOIs below | `IN_CPCB_NAQI_2014` | One request per fire-relevant AOI box, 10,000-detection cap per request | Regional tier added 2026-11-14 |
| `US-LEGACY` | `EMSR-CA-FIRE-2025` | n/a | Not requested | Legacy reference; freshness reports `stale` / `no_observations` |

### INDIA Regional Tier

Focused AOIs instead of a national rectangle: a national box would include
neighbouring countries and sea, break Earth Engine compute limits, and dilute
every aggregate.

| AOI ID | Name | min_lon | min_lat | max_lon | max_lat | Purpose |
| --- | --- | --- | --- | --- | --- | --- |
| IN-DEL-NCR | Delhi NCR | 76.8 | 28.3 | 77.6 | 28.9 | Urban air quality (PM2.5/PM10), NO₂ |
| IN-MUM | Mumbai metropolitan | 72.75 | 18.85 | 73.2 | 19.35 | Coastal urban air quality |
| IN-PB-HR | Punjab–Haryana crop-fire belt | 73.8 | 29.0 | 77.4 | 32.5 | Crop-residue fires, crop stress (NDVI) |
| IN-THAR | Thar Desert | 69.5 | 24.5 | 74.5 | 29.0 | Regional dust source |
| IN-GUJ-COAST | Gujarat coast (Arabian Sea) | 68.5 | 20.0 | 73.0 | 24.0 | Arabian/Gulf dust arrival, coastal aerosol |
| IN-ASSAM | Brahmaputra flood basin | 89.7 | 25.8 | 96.0 | 27.9 | Monsoon flood extent (NDWI) |

INDIA AOIs are deliberately non-overlapping with each other and with the
UAE-GULF envelope (INDIA starts at 68.5°E; UAE-GULF ends at 57°E).

| Source | INDIA AOIs | Budget control |
| --- | --- | --- |
| FIRMS VIIRS (`FIRMS_SOURCE`, default NOAA-20 NRT; S-NPP NRT ended 2026-11-02) | PB-HR, DEL-NCR, THAR, GUJ-COAST, ASSAM | Per-AOI box; ≤ 10,000 detections per request (most recent kept); truncation recorded as `coverage = capped` |
| OpenAQ | DEL-NCR, MUM | PM2.5/PM10 only; ≤ 25 stations, 3 × 200-row pages per sensor; caps recorded as `coverage = capped` |
| TROPOMI (GEE) | DEL-NCR, PB-HR | Same products as UAE |
| MODIS AOD (GEE) | THAR, GUJ-COAST, DEL-NCR, PB-HR | Dust source + arrival |
| Sentinel-2 NDVI / NDWI (GEE) | NDVI: PB-HR · NDWI: ASSAM | `bestEffort` reduceRegion coarsens large boxes |
| NASA POWER wind | all AOIs | Point at AOI centroid |

Backfill: `python -m ingestion.scripts.regional_ingest --region INDIA --days 30`
(FIRMS walked in 5-day `DATE` windows, the API maximum). The daily batch driver
then ingests the same plan over the rolling 14-day window, with the latest FIRMS day.

**Known limitations:** daily grain is the UTC day (IST is UTC+5:30, so local
evening crop burning can split across dates); AOIs are hand-drawn rectangles;
June–September monsoon cloud reduces Sentinel-2 coverage (surfaced as
`not_evaluated`); the NAQI "Severe" band is interpolated to 500 at PM2.5 500 /
PM10 600 µg/m³ pending domain approval.

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

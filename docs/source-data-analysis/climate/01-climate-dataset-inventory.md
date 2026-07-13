# 01 Climate / Air-Quality Dataset Inventory (Phase 5b Extension)

> Extends Phase 5 [`01-dataset-inventory.md`](../01-dataset-inventory.md). Adds the **atmospheric column** (dust, air quality) that the platform is currently missing. Documentation only — no ingestion design.

## Executive Summary

This extension adds **three new IN-scope atmospheric sources** plus a class of **derived climate indicators** that require **zero new connectors** (computed from data the platform already ingests). All IN-scope sources fit the existing tabular / statistical-API ingestion pattern (Strategy A) and respect the 16 GB RAM / Docker budget through mandatory AOI clipping. Two heavy source families (CAMS/ERA5 raw NetCDF, geostationary SEVIRI/Himawari) are **explicitly deferred** — see [`09-climate-mvp-and-deferred.md`](./09-climate-mvp-and-deferred.md).

## Inventory Summary

| Category | Source | Access Pattern | Scope | Tier |
| --- | --- | --- | --- | --- |
| Air quality (ground) | OpenAQ v3 | REST API (tabular) | IN | Tier 1 |
| Air quality / atmosphere (satellite) | Sentinel-5P / TROPOMI via Google Earth Engine | AOI `reduceRegion` stats | IN | Tier 1 |
| Aerosol (satellite) | MODIS / VIIRS Aerosol Optical Depth (AOD) | Point / stats access | IN | Tier 1 |
| Climate indicators | Derived from already-ingested sources | Compute-only (no ingest) | IN | Tier 1 (free) |
| Reanalysis (raw grids) | CAMS / ERA5 NetCDF | Binary blob landing | **OUT — deferred** | — |
| Geostationary | SEVIRI / Himawari full-disk | Heavy raster stream | **OUT — deferred** | — |

---

## New Source Profiles (IN scope)

### S-101 · OpenAQ (Ground-Station Air Quality)

| Attribute | Detail |
| --- | --- |
| Source Organization | OpenAQ (non-profit) |
| Data Format | JSON over REST (`api.openaq.org` v3) |
| Access Method | REST API — paginated tabular queries by location / bbox / parameter |
| High-level Schema | `location_id`, `sensor_id`, `parameter` (pm25, pm10, no2, so2, co, o3, bc), `value`, `unit` (µg/m³, ppm), `datetime_utc`, `datetime_local`, `coordinates{lat,lon}`, `country`, `provider` |
| Granularity | Per station, per pollutant; hourly (some sub-hourly) |
| Update Frequency | Near-real-time (station-dependent, typ. hourly) |
| Historical Coverage | ~2016 → present (varies by station) |
| Geospatial Coverage | Global where ground stations exist; **sparse over UAE/Gulf** (few public stations) |
| Data Volume (per AOI/day) | Small — KBs to low MBs (rows, not rasters) |
| API Limitations | API key required (free); rate-limited (per-key throttle); pagination `limit`/`page`; some providers embargo/aggregate |
| Reliability Score | **Medium** (High for value, Medium for spatial coverage in the Gulf) |

### S-102 · Sentinel-5P / TROPOMI via Google Earth Engine

| Attribute | Detail |
| --- | --- |
| Source Organization | ESA Copernicus (data) / Google Earth Engine (access layer) |
| Data Format | JSON statistics response (mean/min/max/stDev per AOI per date) |
| Access Method | Google Earth Engine `reduceRegion` over the AOI geometry — one request per AOI per day; returns aggregates, **not pixels** |
| High-level Schema (products) | `NO2`, `SO2`, `CO`, `O3`, `CH4`, `AER_AI` (UV Aerosol Index); per band: `mean`, `min`, `max`, `stDev`, `sampleCount`, `noDataCount`; `interval{from,to}` |
| Units | Column densities in **mol/m²** (NO₂, SO₂, CO, O₃), CH₄ in ppb (column-averaged mixing ratio), AER_AI unitless |
| Granularity | Per AOI polygon per acquisition day; native pixel ~3.5 × 5.5 km (aggregated to AOI) |
| Update Frequency | Daily (near-daily global coverage; one overpass/day mid-latitudes) |
| Historical Coverage | 2018 (S-5P launch Oct 2017, ops 2018) → present |
| Geospatial Coverage | Global; AOI-clipped to UAE + regional dust corridors |
| Data Volume (per AOI/day) | Tiny — one JSON stats record per band per AOI per day (KBs) |
| API Limitations | Google service-account auth (free, non-commercial); Earth Engine per-request compute + rate quotas (drive AOI clipping + coarse sampling scale) |
| Reliability Score | **High** (retrieval quality varies with cloud / solar angle) |

> **Access-layer decision (implemented in Phase 8b).** Sentinel-5P and MODIS AOD
> are sourced from **Google Earth Engine (GEE)** rather than the Sentinel Hub
> Statistical API. *Why:* the `sentinel-5p-l2` and MODIS collections are **not
> entitled** on the free / CDSE Sentinel Hub plan (the commercial Sentinel Hub
> carries them but is paid after a 30-day trial), whereas GEE indexes both
> `COPERNICUS/S5P/*` and `MODIS/*` and is free for non-commercial use.
> *Alternatives considered:* (a) paid Sentinel Hub subscription — rejected
> (breaks the free/open-source constraint); (b) NASA AppEEARS + GES DISC — viable
> free fallback (async task model, no Sentinel-5P for AppEEARS). *Trade-off:* GEE
> adds a Google service-account dependency and an SDK, but `reduceRegion` maps
> 1:1 onto the AOI-statistics design so the Bronze bucket shape — and every
> downstream Silver/Gold/serving/BI contract — is unchanged. The 16 GB budget is
> respected because only **AOI aggregates** are returned — no raster download.

### S-103 · MODIS / VIIRS Aerosol Optical Depth (AOD)

| Attribute | Detail |
| --- | --- |
| Source Organization | NASA LP DAAC / LAADS (MODIS MCD19A2 MAIAC, VIIRS Deep Blue); accessed via Google Earth Engine |
| Data Format | Point / statistical extract (value per lat/lon/day); tabular after extraction |
| Access Method | Google Earth Engine `reduceRegion` over the AOI on `MODIS/061/MCD19A2_GRANULES` (band `Optical_Depth_055`, scaled ×0.001) — **no full-granule download** |
| High-level Schema | `aod_550nm` (unitless), `qa_flag`, `datetime`, `lat`, `lon`, `sensor` (MODIS/VIIRS), optional `angstrom_exponent` |
| Units | Aerosol Optical Depth — **unitless** (typically 0–5) |
| Granularity | ~1 km (MAIAC) / 3–10 km; daily |
| Update Frequency | Daily (Terra AM, Aqua PM, VIIRS) |
| Historical Coverage | MODIS 2000 → present; VIIRS 2012 → present |
| Geospatial Coverage | Global; AOI point/stats extraction only |
| Data Volume (per AOI/day) | Small — point/stats rows (KBs) |
| API Limitations | Google service-account auth (free, non-commercial); Earth Engine per-request compute + rate quotas; retrieval gaps under cloud |
| Reliability Score | **Medium-High** (High signal for dust; QA flags needed to drop cloud-contaminated retrievals) |

### S-104 · Derived Climate Indicators (No New Ingestion)

| Attribute | Detail |
| --- | --- |
| Source Organization | Internal — computed from already-ingested Phase 5/8 sources |
| Data Format | Derived tabular indicators (Silver/Gold) |
| Access Method | **None** — compute-only over existing Bronze/Silver |
| Inputs | MODIS/Landsat LST, Sentinel-2/MODIS NDVI, NOAA OISST SST, Global Forest Watch, Sentinel-2 NDWI |
| Indicators | NDVI/EVI, LST + anomaly, SST + anomaly, NDWI/water availability, deforestation, desertification proxy, snow-cover proxy |
| Granularity | Inherits source (per AOI, daily/8-day/monthly) |
| Update Frequency | Inherits source cadence |
| Historical Coverage | Inherits source (MODIS 2000→, Landsat 1984→, OISST 1981→) |
| Data Volume | Zero new ingest; derived tables only |
| API Limitations | None (no new connector) |
| Reliability Score | **High** (bounded by the reliability of already-vetted sources) |

Full mapping and formulas: [`03-derived-indicators.md`](./03-derived-indicators.md).

---

## Deferred (OUT of scope — do not adopt this phase)

| Source | Why deferred | Revisit condition |
| --- | --- | --- |
| CAMS reanalysis / forecast (raw NetCDF) | Requires a **new binary blob-landing capability** (NetCDF/GRIB), xarray/eccodes stack — breaks the tabular Strategy-A pattern | When a raster-landing subsystem is funded |
| ERA5 (Copernicus CDS, raw NetCDF) | Same NetCDF blob-landing gap; large multi-GB grids | Same as above |
| Geostationary SEVIRI / Himawari (full-disk) | Full-disk high-cadence rasters violate the 16 GB / Docker budget | Dedicated compute / object store beyond laptop scope |

Rationale detail: [`09-climate-mvp-and-deferred.md`](./09-climate-mvp-and-deferred.md).

---

## Coverage Confirmation

- New IN-scope sources: **3** (OpenAQ, TROPOMI-via-SH-Stats, MODIS/VIIRS AOD) + **1** derived-indicator class.
- All fit the existing tabular / statistical-API ingestion pattern (Strategy A).
- Heavy NetCDF and geostationary families explicitly deferred with rationale.

## Cross References

- Phase 5 inventory: [`../01-dataset-inventory.md`](../01-dataset-inventory.md)
- AOI strategy: [`02-aoi-strategy.md`](./02-aoi-strategy.md)
- Data quality: [`04-climate-data-quality.md`](./04-climate-data-quality.md)
- Freshness & risk: [`08-climate-freshness-risks.md`](./08-climate-freshness-risks.md)

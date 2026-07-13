# 10 Climate / Air-Quality Glossary

> Terms specific to the climate/dust/air-quality expansion. Extends Phase 5 [`13-glossary.md`](../13-glossary.md).

| Term | Definition |
| --- | --- |
| AOD (Aerosol Optical Depth) | Unitless (0–5) measure of aerosol loading in the atmospheric column; proxy for dust/haze/PM. |
| AER_AI (UV Aerosol Index) | TROPOMI unitless index sensitive to UV-absorbing aerosols (dust, smoke); robust over bright surfaces. |
| AOI (Area of Interest) | Named bounding-box/polygon that bounds every stats/point request; the universal join key (`aoi_id`). |
| Column density | Vertically integrated amount of a gas over a unit ground area, in **mol/m²** (TROPOMI). Not surface concentration. |
| Surface concentration | Breathable near-ground concentration in **µg/m³** or ppm/ppb (OpenAQ ground stations). |
| CAMS | Copernicus Atmosphere Monitoring Service; reanalysis/forecast in raw NetCDF — **deferred** (blob-landing gap). |
| ERA5 | ECMWF reanalysis via Copernicus CDS; raw NetCDF grids — **deferred**. |
| Climatology / baseline | Long-term same-day-of-year mean used to compute anomalies (LST/SST). |
| Deep Blue / MAIAC | AOD retrieval algorithms; MAIAC (MODIS MCD19A2) preferred over bright desert surfaces. |
| Desertification proxy | Composite flag: multi-year NDVI decline co-located with rising LST inside desert-margin AOIs. |
| EVI | Enhanced Vegetation Index; NDVI variant reducing atmospheric/soil effects. |
| Geostationary (SEVIRI/Himawari) | High-cadence full-disk imagers — **deferred** (violates 16 GB budget). |
| LST | Land Surface Temperature (MODIS/Landsat thermal); with anomaly, a warming/urban-heat indicator. |
| NDSI | Normalized Difference Snow Index; snow-cover proxy. |
| NDVI | Normalized Difference Vegetation Index `(NIR−Red)/(NIR+Red)`; vegetation health. |
| NDWI | Normalized Difference Water Index `(Green−NIR)/(Green+NIR)`; water availability. |
| noDataCount / sampleCount | Statistical-API completeness fields per AOI; primary cloud/coverage signal. |
| OpenAQ | Open ground-station air-quality API (PM, NO₂, SO₂, CO, O₃, BC); near-real-time, spatially sparse. |
| PU (Processing Units) | Sentinel Hub quota metering request area × resolution; the main driver of AOI clipping. |
| qa_value | TROPOMI per-pixel retrieval-quality flag; threshold filter before AOI aggregation. |
| Sentinel Hub Statistical API | Endpoint returning per-AOI aggregates (mean/min/max/stDev/percentiles), not pixels — Strategy A. |
| Shamal | Northwesterly wind driving Mesopotamian/Gulf dust storms toward the UAE. |
| Strategy A | The platform's tabular / statistical-API ingestion pattern (no raster/NetCDF blob landing). |
| SST | Sea Surface Temperature (NOAA OISST); with anomaly, an ocean-warming indicator. |
| TROPOMI | Instrument on Sentinel-5P measuring NO₂/SO₂/CO/O₃/CH₄ + aerosol index; accessed via SH Statistical API. |

## Cross References

- Phase 5 glossary: [`../13-glossary.md`](../13-glossary.md)
- Inventory: [`01-climate-dataset-inventory.md`](./01-climate-dataset-inventory.md)

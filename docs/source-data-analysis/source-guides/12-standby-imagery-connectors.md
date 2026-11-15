# 12 — Standby Imagery Connectors (Implemented, Not Scheduled)

These connectors are implemented and unit-tested but **not called** by any scheduled DAG or by
[`run_full_batch_ingest.py`](../../../ingestion/scripts/run_full_batch_ingest.py). They exist as
**fallbacks** and as **catalog breadth** for UC-25. Their Bronze output, when run, unions into the
same Silver entities as the active sources.

## 1. Summary

| Connector | Bronze `_source` | Provider | Auth | What it returns | Why it is on standby |
| --- | --- | --- | --- | --- | --- |
| [`LandsatConnector`](../../../ingestion/api/landsat.py) | `LANDSAT` | **USGS** LandsatLook STAC server | Anonymous | Landsat 8/9 Collection-2 L2 scene metadata (STAC Features) | Optional long-baseline catalog breadth |
| [`EarthdataConnector`](../../../ingestion/api/earthdata.py) | `EARTHDATA` | **NASA CMR** (Common Metadata Repository) | Anonymous (search) | Granule metadata for any NASA collection (`short_name`, default `MOD14` = MODIS fire) | Optional catalog breadth |
| [`SentinelHubConnector`](../../../ingestion/api/sentinelhub.py) | `SENTINELHUB` | **Sinergise / Planet** Sentinel Hub Catalog API | OAuth client credentials | Sentinel-2 STAC scene metadata | Replaced by GEE (account availability) |
| [`SentinelHubStatsConnector`](../../../ingestion/api/sentinelhub_stats.py) | `SENTINELHUB_STATS` | Sentinel Hub **Statistical API** | OAuth | NDVI/NDWI/NBR AOI statistics (**correct sign**) | Replaced by GEE |
| [`TropomiConnector`](../../../ingestion/api/tropomi.py) | `TROPOMI` | Sentinel Hub Statistical API (`sentinel-5p-l2`) | OAuth | Trace-gas AOI statistics | `sentinel-5p-l2` not entitled on the free plan |
| [`ModisAodConnector`](../../../ingestion/api/modis_aod.py) | `MODIS_AOD` | Sentinel Hub Statistical API | OAuth | AOD AOI statistics | MODIS AOD not entitled on the free plan |

## 2. Landsat 8/9 (USGS LandsatLook STAC)

| Aspect | Detail |
| --- | --- |
| Who | **USGS** and **NASA** jointly operate Landsat; USGS EROS archives and distributes |
| How collected | Landsat 8 (2013) and Landsat 9 (2021): OLI (11 bands incl. 30 m multispectral, 15 m pan) + TIRS thermal (100 m); 185 km swath; 16-day revisit each (8-day combined); ≈ 10:00 local |
| Why | **50-year archive** (Landsat 1, 1972): the longest civil Earth-observation record, ideal for long-term change (UC-14, desertification) |
| Access | `POST https://landsatlook.usgs.gov/stac-server/search` with `{"collections": ["landsat-c2l2-sr"], "bbox": [...], "datetime": "...", "limit": 20}` |
| Format | STAC `FeatureCollection`; each Feature is landed unchanged |
| Key fields | `id` (e.g., `LC09_L2SP_160043_20240115_…`: sensor, level, WRS-2 path/row, date), `bbox`, `geometry` (true footprint), `properties.datetime`, `eo:cloud_cover`, `landsat:wrs_path/row`, `assets` (COG links per band) |
| Gotcha | Landsat L2 surface reflectance uses a **scale factor (0.0000275) and offset (−0.2)**: apply both if pixels are ever read |

## 3. NASA Earthdata CMR

| Aspect | Detail |
| --- | --- |
| Who | NASA ESDIS: catalogue of all NASA Earth-science data across the DAACs |
| Access | `GET https://cmr.earthdata.nasa.gov/search/granules.json?short_name=MOD14&bounding_box=W,S,E,N&page_size=20[&temporal=…]` |
| Format | JSON feed: `{"feed": {"entry": [ … ]}}`; each entry landed unchanged |
| Key fields | `producer_granule_id` / `title` (scene key), `time_start`/`time_end`, `boxes` (**`"S W N E"`, lat first!**), `polygons`, `dataset_id`, `collection_concept_id`, `links` (download URLs, Earthdata Login required for files) |
| Why | One API to discover MODIS, VIIRS, Landsat and thousands more NASA collections |
| Gotcha | `boxes` axis order differs from STAC `bbox`; Silver's `_scene_geo` handles the swap |

## 4. Sentinel Hub (Catalog + Statistical)

| Aspect | Detail |
| --- | --- |
| Who | Sentinel Hub (Sinergise, now Planet Labs): commercial processing API over Copernicus data |
| Auth | OAuth2 client credentials → bearer token (`SENTINELHUB_CLIENT_ID`/`SECRET`) |
| Catalog | `POST /api/v1/catalog/1.0.0/search`: STAC search, returns true footprints |
| Statistical | `POST /api/v1/statistics` with an **evalscript** (JavaScript band math) and `aggregationInterval P1D`; returns `{"data": [buckets]}`, the shape all GEE connectors now imitate |
| Resolution cap | Output raster ≤ 2,500 px per side; the connector auto-coarsens `resx`/`resy` |
| Why standby | Free-tier processing-unit quotas and collection entitlements |
| Value | Its evalscripts define the **reference formulas** for SG-01: `(B08 − B04)/(B08 + B04)` etc. |

## 5. Decision Record

| | |
| --- | --- |
| **Chosen** | Keep fallbacks implemented and tested, but unscheduled |
| **Why** | Backend resilience: switching back is a configuration change, because Bronze `_source` codes and payload shapes are identical |
| **Alternatives** | Delete unused connectors (simpler) · Run all in parallel (duplicate data, quota cost) |
| **Trade-off** | Maintenance of untested-in-production code paths; risk of silent drift from provider APIs |

## 6. References

- LandsatLook STAC: https://landsatlook.usgs.gov/stac-server/
- Landsat Collection 2 scale factors: https://www.usgs.gov/landsat-missions/landsat-collection-2-level-2-science-products
- CMR Search API: https://cmr.earthdata.nasa.gov/search/site/docs/search/api.html
- Sentinel Hub Statistical API: https://docs.sentinel-hub.com/api/latest/api/statistical/

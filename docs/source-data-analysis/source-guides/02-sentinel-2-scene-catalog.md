# 02 — Sentinel-2 Scene Catalog (via Google Earth Engine)

## 1. Identity Card

| Attribute | Value |
| --- | --- |
| Bronze `_source` | `SENTINELHUB` *(historical name, kept so downstream layers are unchanged; real backend is GEE)* |
| Data owner | **ESA / European Commission Copernicus Programme** |
| Access backend | **Google Earth Engine (GEE)** asset `COPERNICUS/S2_SR_HARMONIZED` |
| Satellites / instrument | Sentinel-2A, 2B, 2C · **MSI** (MultiSpectral Instrument) |
| Connector | [`GeeSentinel2SceneConnector`](../../../ingestion/api/gee_sentinel2.py) |
| Schedule | `@daily`, 14-day look-back window ([`gee_sentinel2_ingest_dag.py`](../../../ingestion/batch/dags/gee_sentinel2_ingest_dag.py)) |
| Auth | Google Cloud service account JSON key (`GEE_SERVICE_ACCOUNT`, `GEE_KEY_FILE`, `GEE_PROJECT`) |
| Licence | Copernicus data: free, full and open (attribution required); GEE: free for non-commercial and research use |
| Use cases | UC-25 imagery catalog and metadata quality; UC-14 change-detection scene selection |

## 2. What It Is (Plain Language)

A **library card for satellite photos**: each record says "a Sentinel-2 image of this tile was taken
at this time with X % cloud". It contains **no pixels**. It helps answer: *Do we have a recent,
cloud-free image of Dubai?*

## 3. How the Data Is Collected

| Aspect | Detail |
| --- | --- |
| Orbit | Sun-synchronous, 786 km, crosses the equator ≈ 10:30 local time (descending) |
| Revisit | 5 days at the equator with two satellites (2–3 days at mid-latitudes) |
| Instrument | Push-broom imager, **13 spectral bands**: visible/NIR at 10 m, red-edge/SWIR at 20 m, atmospheric at 60 m; 290 km swath |
| Product | **Level-2A**: bottom-of-atmosphere (surface) reflectance after Sen2Cor atmospheric correction, plus a **Scene Classification Layer (SCL)** (cloud, shadow, water, vegetation…) |
| Tiling | Delivered in 100 × 100 km **MGRS** tiles (e.g., `T39RZH`); one overpass can create several tiles |
| "Harmonized" | Since Jan 2022 (processing baseline 04.00), ESA added a +1000 offset to digital numbers. GEE's `_HARMONIZED` collection removes it, so long time series are consistent |

## 4. Why We Access It

| Reason | Detail |
| --- | --- |
| Discovery before analysis | Know which dates have usable imagery before computing indices (doc 03) |
| Metadata-quality KPI (UC-25) | Completeness and searchability of a scene catalog is a real ground-segment concern |
| Low cost | Metadata only: ~200 bytes per scene |

## 5. How We Access It

| Item | Value |
| --- | --- |
| Method | GEE Python SDK: `ImageCollection("COPERNICUS/S2_SR_HARMONIZED").filterDate(...).filterBounds(Rectangle(bbox)).sort("system:time_start", False).limit(N)` |
| Properties read | `system:time_start` (ms epoch), `CLOUDY_PIXEL_PERCENTAGE`, `system:index` |
| AOI | `AOI-DXB` = `[54.9, 24.8, 55.6, 25.4]` |
| Window / limit | Last 14 UTC days (ending yesterday), newest 20 scenes |
| Quota | GEE per-user concurrent-request and compute quotas; tiny for metadata |

## 6. Format at Source

GEE returns an `ee.FeatureCollection` as JSON (`getInfo()`):

```json
{"type": "Feature", "geometry": null,
 "properties": {"system:time_start": 1794553365347, "CLOUDY_PIXEL_PERCENTAGE": 2.374943,
                "scene_id": "20261113T065121_20261113T070235_T39RZH"}}
```

## 7. What We Store in Bronze (and Why)

The connector **reshapes** the GEE response into a **STAC-like Feature**, the same shape the
original Sentinel Hub Catalog API returned. This keeps the Silver `clean_scene_metadata` cleaner
unchanged.

Real record (`s3://bronze/SENTINELHUB/ingest_date=2026-11-14/…/part-0000.jsonl`):

```json
{"_source": "SENTINELHUB", "_format": "json", "_event_ts": "2026-11-13T07:02:45.347000Z",
 "payload": {"type": "Feature", "id": "20261113T065121_20261113T070235_T39RZH",
   "collection": "sentinel-2-l2a", "bbox": [54.9, 24.8, 55.6, 25.4],
   "properties": {"datetime": "2026-11-13T07:02:45.347000Z", "eo:cloud_cover": 2.374943,
                  "platform": "sentinel-2", "provider": "Google Earth Engine"}}}
```

| Decision | Why | Alternative | Trade-off |
| --- | --- | --- | --- |
| Reshape to STAC instead of storing the raw GEE dict | Backend-independent contract; Sentinel Hub/Landsat/GEE union into one Silver entity | Store the raw GEE dict | Bronze is no longer byte-identical to the provider response (transformation documented here) |
| GEE instead of the Sentinel Hub Catalog | Sentinel Hub account availability and free-tier limits; GEE is already used for S5P/AOD | Copernicus Data Space STAC (free) | Adds a Google dependency |

## 8. Field Dictionary

| Field | Type | Meaning | Notes |
| --- | --- | --- | --- |
| `id` | string | GEE `system:index`: `<datatake sensing start>_<product discriminator time>_<MGRS tile>` | `T39RZH` = UTM zone 39, latitude band R, 100 km square ZH |
| `collection` | string | Logical collection, fixed `sentinel-2-l2a` | — |
| `bbox` | `[min_lon, min_lat, max_lon, max_lat]` | ⚠️ **Requested AOI**, not the tile footprint (README SG-02) | Silver derives `geo_key` from its centroid |
| `properties.datetime` | ISO UTC | Image acquisition time (`system:time_start`) | ≈ 07:00Z over the UAE ≈ 11:00 local |
| `properties.eo:cloud_cover` | double, % | `CLOUDY_PIXEL_PERCENTAGE` for the **whole tile** | Not the cloud fraction over the AOI |
| `properties.platform` | string | `sentinel-2` (A/B/C not distinguished) | — |
| `properties.provider` | string | Access backend | `Google Earth Engine` |

## 9. How to Read & Interpret

- **One overpass, many records:** the Dubai AOI spans several MGRS tiles, so one pass yields 2–4
  scene ids with the same `datetime` but different tile suffixes.
- **Cloud screening:** `eo:cloud_cover < 20` is a reasonable first filter, then confirm with the
  index valid-pixel fraction (doc 03), which is AOI-specific.
- **Completeness score (Silver):** share of {collection, platform, bbox, geo_key, cloud_cover}
  that is populated; GEE records score 1.0.

## 10. Quality, Limitations & Gotchas

| Gotcha | Mitigation |
| --- | --- |
| Tile-level cloud cover can mislead for a small AOI | Use `silver_index.valid_pixel_fraction` for the AOI |
| Bbox is not the footprint | Do not compute scene coverage area from `bbox` |
| Re-pull of a 14-day window daily duplicates scenes | Silver dedupes on `scene_key` |
| `_source` says SENTINELHUB | Use `properties.provider` to see the real backend |

## 11. Downstream Lineage

`Bronze SENTINELHUB` → `silver_scene` (`obs_scene`, unioned with `LANDSAT`, `EARTHDATA`) →
Gold `fact_scene_catalog`, `kpi_catalog_quality` → `serving_scene_catalog`, `mv_catalog_quality` →
Superset Imagery-Quality dashboard.

## 12. References

- GEE catalog: https://developers.google.com/earth-engine/datasets/catalog/COPERNICUS_S2_SR_HARMONIZED
- Sentinel-2 mission (ESA SentiWiki): https://sentiwiki.copernicus.eu/web/s2-mission
- STAC specification: https://stacspec.org

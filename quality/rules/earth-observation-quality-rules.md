# Earth Observation — Data Quality Rules

> **Scope:** MVP-critical datasets. These rules govern the six Earth-observation
> use cases that define the platform MVP (UC-14 change detection, UC-15 wildfire,
> UC-16 flood, UC-18 illegal fishing, UC-25 catalog quality, UC-27 damage
> prioritization). Rules are enforced at the Bronze, Silver and Gold gates.

---

## 1. Coverage

| Silver entity | Source connector(s) | MVP use case | Gold mart(s) |
|---------------|---------------------|--------------|--------------|
| `silver_fire` | NASA FIRMS (VIIRS/MODIS) | UC-15 wildfire | `kpi_eo_daily`, `kpi_wildfire_aoi_daily`, `kpi_aoi_validation` |
| `silver_index` | Sentinel Hub Statistical API | UC-16 flood, UC-14 change | `kpi_flood_aoi_daily`, `kpi_aoi_validation` |
| `silver_vessel` | Global Fishing Watch | UC-18 fishing | `fact_vessel_activity` |
| `silver_scene` | Sentinel Hub / Landsat / Earthdata CMR | UC-25 catalog, UC-27 damage | `fact_scene_catalog` |
| `ref_aoi` | Copernicus EMS (manual GeoJSON) | validation ground truth | `kpi_aoi_validation` |

Business KPIs these rules protect: **Mean Time to Detect (MTTD)**, **false
negative rate**, **monitored coverage**, **metadata completeness**, **search
success rate**, **analyst throughput** (see [docs/business/08-kpis.md](../../docs/business/08-kpis.md)).

---

## 2. `silver_fire` (Active Fire Detections — UC-15)

### Mandatory fields

| Field | Type | Rule |
|-------|------|------|
| `fire_key` | string | Non-null, unique (natural key: SHA1 of lat/lon/ts/satellite) |
| `event_ts` | ISO-8601 UTC | Non-null, parseable, not > 48h in the future |
| `latitude` | float | Non-null, `-90 ≤ lat ≤ 90` |
| `longitude` | float | Non-null, `-180 ≤ lon ≤ 180` (normalized) |
| `geo_key` | string | Non-null (derived spatial grid cell) |

### Optional fields

| Field | Type | Rule |
|-------|------|------|
| `frp` | float | If present, `frp ≥ 0` (Fire Radiative Power, MW) |
| `confidence` | int | If present, `0 ≤ confidence ≤ 100` |
| `brightness` | float | If present, `> 0` (Kelvin brightness temperature) |
| `daynight` | char | If present, `∈ {D, N}` |
| `satellite` | string | `∈ {N, M, <instrument>}` |

### Referential integrity, duplicates, timestamp, geospatial

- **Duplicate rule:** `fire_key` unique after Silver dedup; identical detections
  (same lat/lon/ts/satellite) collapse to one row.
- **Timestamp rule:** `event_ts` reconstructed from `acq_date` + `acq_time`;
  must be monotonic within a single acquisition granule.
- **Geospatial rule:** lat/lon inside valid earth bounds; `geo_key` must
  correspond to the (lat, lon) grid cell (no drift).
- **Referential integrity:** every `geo_key` used by `kpi_eo_daily` must exist in
  the fire detections; every AOI attribution in `kpi_wildfire_aoi_daily` must map
  to a `ref_aoi.aoi_key`.

**Business impact of failure:** dropped or mislocated detections directly raise
the **false negative rate** and degrade **MTTD** for wildfire response.

---

## 3. `silver_index` (Spectral Index Statistics — UC-16 / UC-14)

### Mandatory fields

| Field | Type | Rule |
|-------|------|------|
| `event_ts` | ISO-8601 UTC | Non-null, parseable |
| `index_name` | string | Non-null (upper-cased), `∈ {NDVI, NDWI, NBR, ...}` |
| `stat_date` | date (YYYY-MM-DD) | Non-null (derived from `event_ts`) |
| `mean` | float | Non-null; index-specific range (see below) |
| `bbox` | string | 4 comma-separated floats `minx,miny,maxx,maxy` |
| `geo_key` | string | Non-null |
| `index_key` | string | Unique natural key = hash(`geo_key`, `index_name`, `stat_date`) |

### Accepted ranges (index-specific)

| Index | Range | Interpretation |
|-------|-------|----------------|
| NDVI | `-1.0 … 1.0` | Vegetation vigor |
| NDWI | `-1.0 … 1.0` | Open-water presence (> threshold ⇒ flood) |
| NBR | `-1.0 … 1.0` | Burn severity |

### Optional fields & rules

| Field | Type | Rule |
|-------|------|------|
| `valid_pixel_fraction` | float | `0 ≤ x ≤ 1`; **< 0.2 ⇒ warn** (mostly cloud/no-data) |
| `stddev` | float | If present, `≥ 0` |
| `min` / `max` | float | If present, `min ≤ mean ≤ max` and each in `[-1, 1]` |

- **Duplicate rule:** one row per `index_key` (`geo_key` + `index_name` +
  `stat_date`); later reruns supersede earlier ones by `event_ts`.
- **Business rule:** flood classification only trusts rows with
  `valid_pixel_fraction ≥ 0.5`; lower coverage feeds the *uncertain* bucket.

**Business impact of failure:** low valid-pixel coverage inflates false
positives/negatives in **inundation extent**, corrupting UC-16 damage estimates.

---

## 4. `silver_vessel` (Vessel Identity & Activity — UC-18)

### Mandatory fields

| Field | Type | Rule |
|-------|------|------|
| `vessel_key` | string | Non-null (MMSI), unique |
| `mmsi` | string | Non-null; 9 digits when numeric-normalizable |
| `last_transmission_ts` | ISO-8601 UTC | Non-null, parseable |
| `event_ts` | ISO-8601 UTC | Non-null (= `last_transmission_ts`) |

### Optional fields

| Field | Type | Rule |
|-------|------|------|
| `imo` | string | If present, 7 digits; **absence raises `suspicious_flag`** |
| `flag` | string | Upper-case ISO country; **absence raises `suspicious_flag`** |
| `shipname` | string | Upper-case, trimmed |
| `vessel_type` | string | Controlled vocabulary (`fishing`, `cargo`, …) |
| `first_transmission_ts` | ISO-8601 | If present, `≤ last_transmission_ts` |

- **Referential integrity:** `fact_vessel_activity.vessel_key` must exist in
  `silver_vessel`.
- **Timestamp rule:** `first_transmission_ts ≤ last_transmission_ts`; span used
  for `active_span_days` must be `≥ 0`.
- **Business rule (UC-18):** missing `flag` **or** missing `imo` obscures vessel
  identity → `suspicious_flag = true`.

**Business impact of failure:** identity gaps directly change the **suspicious
vessel detection rate** and analyst triage prioritization.

---

## 5. `silver_scene` (Imagery Catalog — UC-25 / UC-27)

### Mandatory fields

| Field | Type | Rule |
|-------|------|------|
| `scene_key` | string | Non-null, unique (STAC id or CMR granule id) |
| `event_ts` | ISO-8601 UTC | Non-null, parseable |
| `source` | string | `∈ {SENTINELHUB, LANDSAT, EARTHDATA}` |

### Optional fields

| Field | Type | Rule |
|-------|------|------|
| `collection` | string | Controlled (`sentinel-2-l2a`, `landsat-c2-l2`, …) |
| `platform` | string | Controlled (`sentinel-2a`, `landsat-9`, …) |
| `bbox` | string | 4 floats; parseable to `minx,miny,maxx,maxy` |
| `geo_key` | string | Derived from bbox centroid |
| `cloud_cover` | float | `0 ≤ x ≤ 100` (clamped) |
| `completeness_score` | float | `0 ≤ x ≤ 1` (presence of key metadata) |

- **Duplicate rule:** one row per `scene_key`; latest `event_ts` wins.
- **Business rule (UC-25):** a scene is `is_searchable` only if it has
  `geo_key` **and** `event_ts` **and** `collection`.
- **Completeness target:** `completeness_score ≥ 0.8` for catalog certification.

**Business impact of failure:** low completeness lowers the **search success
rate** and increases analyst retrieval time (UC-25).

---

## 6. `ref_aoi` (Reference AOI Footprints — validation ground truth)

### Mandatory fields

| Field | Type | Rule |
|-------|------|------|
| `aoi_key` | string | Non-null, unique |
| `polygons` | GeoJSON rings | Valid polygon / multipolygon (closed ring, ≥ 4 points) |
| `geo_key` | string | Non-null (centroid grid cell) |
| `event_ts` / `event_date` | ISO-8601 | Non-null (activation/publication date) |
| `source` | string | `EMS` (Copernicus Emergency Management Service) |

### Optional fields

| Field | Type | Rule |
|-------|------|------|
| `aoi_name` | string | Human-readable AOI name |
| `bbox` | list[float] | `minx,miny,maxx,maxy` bounds |
| `area_km2` | float | If present, `> 0` and consistent with polygon area (±10%) |
| `event_type` | string | `∈ {fire, flood, other}` (drives validation branch) |

- **Geospatial rule:** all polygon vertices within valid earth bounds; rings
  must close; area must be positive.
- **Referential integrity:** every AOI referenced by `kpi_aoi_validation`,
  `kpi_wildfire_aoi_daily`, `kpi_flood_aoi_daily` must exist here.

**Business impact of failure:** a broken ground-truth layer invalidates the
**detection match rate** used to measure recall across all EO use cases.

---

## 7. Enforcement matrix

| Rule family | Bronze | Silver | Gold |
|-------------|:------:|:------:|:----:|
| File / envelope integrity | ✅ | — | — |
| Schema (required fields, types) | ✅ | ✅ | ✅ |
| Range / validity | — | ✅ | ✅ |
| Deduplication (natural key) | — | ✅ | — |
| Timestamp normalization (UTC) | — | ✅ | — |
| Geospatial bounds / `geo_key` | — | ✅ | ✅ |
| Referential integrity | — | — | ✅ |
| Business rules | — | ✅ | ✅ |
| KPI / aggregate verification | — | — | ✅ |

Executable form of these rules lives in
[transformation/quality/eo_suites.py](../../transformation/quality/eo_suites.py)
and is exercised by
[transformation/tests/test_eo_quality_suites.py](../../transformation/tests/test_eo_quality_suites.py).

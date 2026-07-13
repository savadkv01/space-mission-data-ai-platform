# 01 - Bronze Layer Contracts (Climate / Dust / Air-Quality)

> **Phase 6b - Data Modeling (Climate Extension)** · Document 01 of 07
>
> Extends Phase 6 [`../02-bronze-layer.md`](../02-bronze-layer.md). Design only — no code. All records fit the existing **record-oriented JSONL envelope** (`ingestion/common/envelope.py` — `BronzeEnvelope`). No binary/NetCDF entities.

## Purpose

Define the raw landing contracts for the three IN-scope atmospheric sources from Phase 5b: OpenAQ (ground air quality), TROPOMI per-AOI statistics, and MODIS/VIIRS AOD. Each raw source record is wrapped as-is in the standard envelope `payload`; the tables below specify the **payload schema** only.

## Standard Envelope (inherited — not redefined here)

Every Bronze record carries these provenance columns from `BronzeEnvelope`:

| Column | Type | Notes |
| --- | --- | --- |
| `_ingest_id` | UUID | Unique per record |
| `_source` | string | Source code (see per-entity below) |
| `_ingest_ts` | timestamp | Arrival time (UTC ISO-8601) |
| `_event_ts` | string/null | Source event time if parseable |
| `_batch_id` | string | Ingestion run id (`new_batch_id`) |
| `_format` | string | `json` for all three sources |
| `_checksum` | string | SHA-256 of payload |
| `_source_uri` | string/null | Request URL / object key |
| `payload` | object | Raw source record (schemas below) |

**Partitioning (all three):** `_source` / `ingest_date=YYYY-MM-DD` (derived from `_ingest_ts`), consistent with existing `s3://bronze/<SOURCE>/ingest_date=.../`.

---

## 1. `obs_air_quality_raw` — OpenAQ station readings

- **`_source`:** `OPENAQ`
- **Source event timestamp:** `payload.datetime_utc` → mapped to envelope `_event_ts`
- **Grain:** one record per station-sensor-parameter-timestamp

| payload field | Type | Notes |
| --- | --- | --- |
| `location_id` | int | OpenAQ location id |
| `location_name` | string | Station name; nullable |
| `sensor_id` | int | Sensor id (parameter-specific) |
| `parameter` | string | `pm25`, `pm10`, `no2`, `so2`, `co`, `o3`, `bc` |
| `value` | double | Measured value (raw unit) |
| `unit` | string | `µg/m³`, `ppm`, `ppb` (source-native) |
| `datetime_utc` | string | UTC ISO-8601 reading time |
| `datetime_local` | string | Local time; nullable |
| `latitude` | double | Station lat |
| `longitude` | double | Station lon |
| `country` | string | ISO country; nullable |
| `provider` | string | Data provider; nullable |
| `is_mobile` | bool | Mobile sensor flag; nullable |

## 2. `obs_atmos_raw` — TROPOMI per-AOI statistical buckets

- **`_source`:** `TROPOMI` (Sentinel-5P/S5P; accessed via **Google Earth Engine** `reduceRegion` AOI statistics — see the [access-layer note](../../source-data-analysis/climate/01-climate-dataset-inventory.md) — landed under a distinct source code to avoid collision with the existing `SENTINELHUB_STATS` spectral-index source. The emitted bucket shape is identical to the Sentinel Hub Statistical-API shape, so the Silver contract is backend-agnostic.)
- **Source event timestamp:** `payload.interval_from` → envelope `_event_ts`
- **Grain:** one record per AOI per product (band) per time interval (daily bucket)

| payload field | Type | Notes |
| --- | --- | --- |
| `aoi_id` | string | AOI reference (from Phase 5b AOI seed) |
| `product` | string | `NO2`, `SO2`, `CO`, `O3`, `CH4`, `AER_AI` |
| `interval_from` | string | Bucket start (UTC ISO-8601) |
| `interval_to` | string | Bucket end (UTC ISO-8601) |
| `bbox` | array | `[min_lon, min_lat, max_lon, max_lat]` |
| `mean` | double | AOI mean over valid pixels |
| `min` | double | Min; nullable |
| `max` | double | Max; nullable |
| `stddev` | double | Std deviation; nullable |
| `sample_count` | int | Valid-pixel count |
| `no_data_count` | int | No-data pixel count |
| `unit` | string | `mol/m2` (gases), `ppb` (CH4), `unitless` (AER_AI) |
| `resolution_m` | double | Effective resolution used (auto-coarsened) |

## 3. `obs_aerosol_raw` — MODIS/VIIRS AOD per-AOI / point

- **`_source`:** `MODIS_AOD` (VIIRS variant carries `sensor=VIIRS`)
- **Source event timestamp:** `payload.observation_date` → envelope `_event_ts`
- **Grain:** one record per AOI (or point) per sensor per day

| payload field | Type | Notes |
| --- | --- | --- |
| `aoi_id` | string | AOI reference; nullable if pure point |
| `latitude` | double | Point/centroid lat |
| `longitude` | double | Point/centroid lon |
| `observation_date` | string | UTC date/datetime |
| `sensor` | string | `MODIS` or `VIIRS` |
| `algorithm` | string | `MAIAC`, `DeepBlue`, `DarkTarget`; nullable |
| `aod_550nm` | double | Aerosol Optical Depth (unitless, ~0–5) |
| `angstrom_exponent` | double | Size proxy; nullable |
| `qa_flag` | int/string | Retrieval quality flag |
| `bright_surface_flag` | bool | Desert bright-surface indicator; nullable |
| `unit` | string | `unitless` |

---

## Design Notes & Trade-offs

- **Why record-oriented, not raster:** TROPOMI and AOD are accessed via the Statistical/point pattern (Strategy A from Phase 5b), so each raw record is a small JSON object that fits the envelope. This deliberately avoids the deferred NetCDF/binary blob-landing path (CAMS/ERA5/geostationary — out of scope).
- **Raw units preserved:** Bronze keeps source-native units (`µg/m³`, `mol/m²`, `unitless`); harmonization happens in Silver ([`02-silver-entities.md`](./02-silver-entities.md)).
- **Provenance-complete:** `_checksum` + `_batch_id` make every downstream KPI traceable to a raw record; marts fully replay from Bronze.
- **AOI carried early:** `aoi_id` is present in Bronze for TROPOMI/AOD because the AOI is a *request input* (not a post-hoc filter), enabling deterministic replay.

## Cross References

- Envelope contract: [`../02-bronze-layer.md`](../02-bronze-layer.md)
- Silver entities: [`02-silver-entities.md`](./02-silver-entities.md)
- Phase 5b inventory: [`../../source-data-analysis/climate/01-climate-dataset-inventory.md`](../../source-data-analysis/climate/01-climate-dataset-inventory.md)

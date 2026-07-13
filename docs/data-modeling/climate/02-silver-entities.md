# 02 - Silver Layer Entities (Climate / Dust / Air-Quality)

> **Phase 6b - Data Modeling (Climate Extension)** · Document 02 of 07
>
> Extends Phase 6 [`../03-silver-layer.md`](../03-silver-layer.md). Mirrors the existing `obs_index` / `obs_scene` Silver pattern. All timestamps UTC ISO-8601; all coordinates EPSG:4326; every row carries Bronze provenance columns (`_ingest_id`, `_batch_id`, `_source`, `_event_ts`).

## Purpose

Define cleaned, conformed, unit-standardized Silver entities for the atmospheric domain. These are the single source of truth for the climate Gold marts and align to the shared `dim_aoi` / `geo_key` conventions so cross-domain joins (fire + smoke + air quality per AOI-day) are trivial.

## Entity Inventory

| Entity | Grain | Key | Track |
| --- | --- | --- | --- |
| `obs_air_quality` | 1 row/station/pollutant/reading | `air_quality_key` | Climate |
| `obs_aerosol` | 1 row/AOI/sensor/day | `aerosol_key` | Climate |
| `obs_atmos_column` | 1 row/AOI/gas/day | `atmos_key` | Climate |

## Shared Cleaning Rules (inherited + extended)

| Rule | Action |
| --- | --- |
| Type coercion | Cast to canonical types (mixed int/float coerced, per existing `coerce_rows_to_schema`) |
| Range checks | Drop/flag out-of-bound lat/lon, negative concentrations, AOD outside [0, 5] |
| Null policy | Reject records missing keys/timestamps |
| Dedup | Window by natural key, order by `_event_ts` desc, keep rank 1 |
| Time alignment | Normalize to UTC ISO-8601; derive `stat_date` (UTC day) |
| Geo normalize | EPSG:4326; grid-snap `geo_key`; tag `aoi_id` via point-in-polygon |
| Unit standardize | Convert to canonical unit per pollutant/gas (see below) |
| QA filter | Drop retrievals below quality thresholds before use |

---

## `obs_air_quality` (source: OpenAQ)

Harmonized surface pollutant readings — unit-standardized, quality-filtered, AOI-tagged.

| Field | Type | Rule |
| --- | --- | --- |
| `air_quality_key` | string | Natural key = hash(location_id, sensor_id, parameter, event_ts) |
| `event_ts` | timestamp | From `datetime_utc`, normalized to UTC |
| `stat_date` | date | UTC day of `event_ts` |
| `location_id` | int | OpenAQ location id |
| `pollutant_code` | string | Canonical: `PM25`, `PM10`, `NO2`, `SO2`, `CO`, `O3`, `BC` (maps `dim_pollutant`) |
| `value_std` | double | Value in **canonical unit** (`µg/m³` for PM/NO2/SO2/O3; `mg/m³` for CO) |
| `value_raw` | double | Original value (audit) |
| `unit_raw` | string | Original unit (audit) |
| `latitude` | double | Range [-90, 90] |
| `longitude` | double | Range [-180, 180] |
| `geo_key` | string | Grid-snapped cell |
| `aoi_id` | string | AOI membership (point-in-polygon); nullable if outside all AOIs |
| `quality_flag` | string | `valid` / `suspect` (drift, dup, out-of-range) |
| `source` | string | `OPENAQ` |

**Unit standardization:** convert ppm/ppb → µg/m³ using molar-mass + reference T/P where the source reports volumetric units; keep `value_raw`/`unit_raw` for audit. Gases with no defensible conversion are flagged `suspect` rather than silently converted.

**Dedup:** natural key on (location_id, sensor_id, parameter, event_ts); duplicates/re-reports logged to quality table.

---

## `obs_aerosol` (source: MODIS/VIIRS AOD)

AOD + UV aerosol index conformed per AOI per day (UV aerosol index sourced from `obs_atmos_column` `AER_AI` and denormalized here for dust analytics).

| Field | Type | Rule |
| --- | --- | --- |
| `aerosol_key` | string | Natural key = hash(aoi_id, sensor, stat_date) |
| `stat_date` | date | UTC day |
| `event_ts` | timestamp | Observation datetime, UTC |
| `aoi_id` | string | AOI reference (from `dim_aoi`) |
| `geo_key` | string | AOI centroid grid cell |
| `sensor` | string | `MODIS` or `VIIRS` |
| `aod_550nm` | double | AOD (unitless), range [0, 5]; QA-filtered |
| `angstrom_exponent` | double | Size proxy; nullable |
| `uv_aerosol_index` | double | From TROPOMI `AER_AI`; nullable (join by aoi_id+day) |
| `bright_surface_flag` | bool | Desert bright-surface bias indicator |
| `valid_fraction` | double | Fraction of valid retrievals contributing |
| `quality_flag` | string | `valid` / `suspect` (cloud, bright-surface) |
| `source` | string | `MODIS_AOD` |

**QA handling:** drop cloud-contaminated / low-confidence retrievals before aggregation; flag (not drop) desert bright-surface where MAIAC unavailable. Prefer MAIAC; corroborate dust via `uv_aerosol_index`.

**Cross-sensor:** `sensor` retained as a dimension; MODIS and VIIRS not blended into one value without a harmonization note.

---

## `obs_atmos_column` (source: TROPOMI via SH Statistical API)

Trace-gas column densities per AOI per day.

| Field | Type | Rule |
| --- | --- | --- |
| `atmos_key` | string | Natural key = hash(aoi_id, gas_code, stat_date) |
| `stat_date` | date | Bucket date (from interval start) |
| `event_ts` | timestamp | Interval start, UTC |
| `aoi_id` | string | AOI reference (from `dim_aoi`) |
| `geo_key` | string | AOI centroid grid cell |
| `bbox` | string | `minx,miny,maxx,maxy` |
| `gas_code` | string | `NO2`, `SO2`, `CO`, `O3`, `CH4`, `AER_AI` |
| `mean` | double | AOI mean over valid pixels (canonical unit) |
| `min` | double | Min; nullable |
| `max` | double | Max; nullable |
| `stddev` | double | Std deviation; nullable |
| `unit_std` | string | `mol/m2` (gases), `ppb` (CH4), `unitless` (AER_AI) |
| `valid_pixel_fraction` | double | sample_count / (sample_count + no_data_count) |
| `quality_flag` | string | `valid` / `low_coverage` (below valid-fraction threshold) |
| `source` | string | `TROPOMI` |

**Semantic guard:** `mean` is a **column density** (mol/m²), not a surface concentration — never conformed to `obs_air_quality.value_std` without an explicit documented conversion. Kept in separate entities by design.

**Coverage flag:** rows with `valid_pixel_fraction` below the data-quality threshold ([`05-kpi-thresholds.md`](./05-kpi-thresholds.md)) are marked `low_coverage`, not dropped, so gaps are visible downstream.

---

## Spatial Tagging to `dim_aoi`

All three entities resolve `aoi_id` against the shared `dim_aoi` (extended with the Phase 5b climate AOIs — see [`04-dimensions-conformance.md`](./04-dimensions-conformance.md)) using the existing point-in-polygon / bbox path (`spatial_transform`, cluster: Spark+Sedona/H3). TROPOMI/AOD already carry `aoi_id` from Bronze (AOI = request input); OpenAQ points are assigned at Silver.

## Schema-Evolution Notes

- New pollutants/gases are **additive**: a new `pollutant_code` / `gas_code` value plus a `dim_pollutant` row — no schema change to the entity.
- Additive nullable columns only (e.g. a future `angstrom_exponent` refinement) — never rename/retype existing fields.
- Unit conventions are versioned in `dim_pollutant`; a conversion change bumps a `conversion_version` rather than mutating history.

## Cross References

- Bronze contracts: [`01-bronze-contracts.md`](./01-bronze-contracts.md)
- Gold marts: [`03-gold-marts.md`](./03-gold-marts.md)
- Dimensions: [`04-dimensions-conformance.md`](./04-dimensions-conformance.md)
- Phase 6 Silver baseline: [`../03-silver-layer.md`](../03-silver-layer.md)

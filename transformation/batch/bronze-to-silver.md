# Design — Bronze → Silver (batch)

> Code: [bronze_to_silver.py](bronze_to_silver.py) · Spec: [docs/transformation/03-bronze-silver.md](../../docs/transformation/03-bronze-silver.md)

## Contract

Input: unwrapped Bronze records (source payload + provenance columns). Output: `SilverResult(rows, quarantine)` per entity.

| Entity | Function | Dedup key | Required keys |
| --- | --- | --- | --- |
| Telemetry | `silver_telemetry` | `(satellite_id, event_ts)` | timestamp, satellite_id |
| Orbit | `silver_orbit` | `(satellite_id, event_ts)` | timestamp, satellite_id, lat, lon |
| Space weather | `silver_space_weather` | `(event_ts, event_type)` | timestamp, kp_index |

## Pipeline (per record)

1. `require_fields` → reject `null:*`
2. `normalize_timestamp` → UTC ISO-8601 (reject unparseable)
3. range checks (lat/lon/alt, kp) → reject out-of-range
4. geo normalize (orbit) → `geo_key`, `grid_lat/lon`
5. structure/flatten (telemetry sensor map → typed columns)
6. `deduplicate` → keep latest by `event_ts`

Rejected rows → quarantine with `_entity`, `_reasons`, original `payload`.

## Spark entrypoint

`run_spark(entity)` reuses the same cleaner functions as `mapInPandas` logic so batch and offline behaviour are identical. Reads `s3a://bronze/...`, writes `s3a://silver/...` Parquet. Requires infra.

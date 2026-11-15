# 02 — Feature Catalog

Entity and FeatureView definitions are in
[`feature_repo/`](../../feature_store/feature_repo/). PostgreSQL source tables
are created from [`01-feature-sources.sql`](../../feature_store/sql/01-feature-sources.sql).
`readiness.yaml` is the release gate and carries detailed blockers.

All event times are UTC. Gold daily/monthly date keys are normalized to UTC
midnight for Feast event timestamps. `feature_date`, `data_nature`, and
`readiness_status` travel with each feature record so consumers can distinguish
data facts from governance state.

| Feature view | Entity / grain | Feature fields | TTL | Status / permitted use |
|---|---|---|---:|---|
| `satellite_health_daily` | `sat_key` / satellite-day | samples, anomaly samples/density, health score, battery drift | 14d | `demo_only`; pipeline validation only |
| `mission_operations` | `mission_key` / mission-time | uptime fraction, anomaly count, state | 14d | Blocked: no reviewed source product |
| `orbit_stability` | `sat_key` / orbit-time | altitude drift, velocity variance, decay rate | 7d | Blocked: source coverage/grain not inventoried |
| `launch_performance_monthly` | `provider_key` / provider-month | launches, success rate, cadence, mean delay | 400d | Blocked: source state/freshness not inventoried |
| `space_weather_daily` | `weather_scope_key` / scope-day | max/mean Kp, storm count | 7d | Blocked: verify lineage and separate synthetic telemetry measures |
| `wildfire_aoi_daily` | `aoi_key` / AOI-day | detections, mean/max FRP, EMS corroboration, area | 30d | Blocked: WP1 45/98 AOI reconciliation |
| `spectral_index_daily` | `aoi_key` / AOI-day | NDVI/NDWI/NBR, valid-pixel fraction | 30d | Blocked: no validated `silver_index` rows |
| `scene_catalog_metadata` | `scene_key` / scene | cloud cover, completeness, searchable | 90d | `restricted`; catalog discovery only |
| `vessel_activity_daily` | `vessel_key` / vessel-day | transmissions, active span, screening flag | 14d | Blocked: event grain and heuristic semantics |
| `air_quality_aoi_daily` | `aoi_key` / AOI-day | PM2.5/PM10/O3, station count | 14d | Blocked: mixed units and measure missingness |
| `dust_aoi_daily` | `aoi_key` / AOI-day | AOD, valid fraction, wind speed/direction | 14d | Blocked pending the 13b gate review; wind completeness met 2026-11-15; freshness objective 96 h |

Only the synthetic satellite-health fixture and populated scene catalog source
are populated by the default demonstration startup. The former is deliberately
synthetic. The latter is descriptive metadata; it is not imagery or an
image-derived signal. Current scene records have event dates in 2024 and the
online endpoint reports them outside the 744-hour freshness objective.

### Keys and type rules

| Rule | Enforcement |
|---|---|
| Entity keys | Non-null UTF-8 strings; names match the platform Gold key (`sat_key`, `aoi_key`, `scene_key`, etc.). |
| Event time | Required, timezone-aware UTC `TIMESTAMPTZ`; no ingestion time substituted for missing event time. |
| Creation time | Captured separately for late-arriving-record and PIT tie-breaking behavior. |
| Numeric values | PostgreSQL `DOUBLE PRECISION` / `BIGINT`, mapped to Feast `Float32` / `Int64` where defined. |
| Provenance | `source_reference`, nature and readiness status are persisted beside feature rows. |
| Evolution | Additive, reviewed fields only; breaking changes create a new feature-view version/name and migration plan. |

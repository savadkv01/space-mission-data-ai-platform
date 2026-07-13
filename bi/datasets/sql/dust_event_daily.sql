-- Certified dataset: dust_event_daily  (Superset virtual dataset)  [CLIMATE-EXT 12b]
-- Owner: Air-Quality Lead  |  Layer: serving  |  Grain: 1 row / AOI / day
-- Source of truth: serving.serving_dust_event_daily (Phase 11b data product).
-- Carries AOD (aerosol optical depth), UV-aerosol index, wind-transport context,
-- and the pre-computed dust-severity band + dust/transport flags.
--
-- Superset database connection: `serving_duckdb`
-- Refresh: rebuilt by the `serving_refresh` DAG; cache TTL 1h.
select
    aoi_key,
    aoi_name,
    cast(date_key as date)          as event_date,
    aod_mean,
    aod_max,
    uv_aerosol_index_mean,
    wind_speed_mean,
    wind_dir_dominant,
    corridor_aod_max,
    valid_fraction,
    dust_severity_band,
    dust_severity_label,
    dust_flag,
    transport_flag,
    area_km2
from serving.serving_dust_event_daily

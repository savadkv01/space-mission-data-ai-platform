-- Certified dataset: weather_impact  (Superset virtual dataset)  [SIMULATION-TRACK]
-- Owner: Platform Lead  |  Grain: 1 row / day  |  Track: sim (post-MVP, ADR-09)
-- Source: Gold mart fact_weather_impact (NOAA SWPC Kp fused with synthetic
-- telemetry anomaly rate). Read directly from Gold Parquet via httpfs.
-- storm_day band matches the semantic rule (max_kp_index >= 5).
--
-- Superset database connection: `serving_duckdb`
-- NOTE: labelled `sim` — space-weather forecasting is a post-MVP expansion.
select
    cast(date_key as date)          as weather_date,
    max_kp_index,
    mean_kp_index,
    storm_events,
    telemetry_samples,
    anomaly_samples,
    anomaly_rate,
    (max_kp_index >= 5)             as storm_day
from read_parquet('s3://gold/fact_weather_impact/*.parquet')

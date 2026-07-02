-- Certified dataset: launch_monthly  (Superset virtual dataset)  [SIMULATION-TRACK]
-- Owner: Platform Lead  |  Grain: provider / month  |  Track: sim (post-MVP, ADR-09)
-- Source: Gold mart kpi_launch_monthly (synthetic). Read directly from Gold
-- Parquet via httpfs — no sim serving dbt product exists.
--
-- Superset database connection: `serving_duckdb`
-- NOTE: labelled `sim`. Launch analytics is excluded from the MVP (sparse open
-- data, rare events) and retained only as a demonstrator.
select
    provider_key,
    month_key,
    launches,
    successes,
    success_rate,
    cadence_per_month,
    mean_delay_days
from read_parquet('s3://gold/kpi_launch_monthly/*.parquet')

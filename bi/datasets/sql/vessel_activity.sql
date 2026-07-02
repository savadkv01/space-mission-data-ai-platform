-- Certified dataset: vessel_activity  (Superset virtual dataset)
-- Owner: Maritime Intelligence Lead  |  Layer: serving  |  Grain: vessel / day
-- Source of truth: serving.serving_vessel_activity (dbt data product, UC-18).
-- suspicious_flag / review_priority are the serving heuristic — BI displays only.
--
-- Superset database connection: `serving_duckdb`
-- RLS: restricted to `ops_maritime` and `exec` roles (see bi security doc).
select
    vessel_key,
    cast(date_key as date)          as activity_date,
    transmissions,
    flag,
    vessel_type,
    active_span_days,
    suspicious_flag,
    review_priority                 -- high | normal
from serving.serving_vessel_activity

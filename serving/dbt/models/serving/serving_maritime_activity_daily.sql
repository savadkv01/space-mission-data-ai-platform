-- Serving data product: Maritime Activity (UC-18, area-based). Mirrors
-- serving.marts.serving_marts.serve_maritime_activity_daily. GFW 4Wings
-- apparent fishing effort, AIS vessel presence, and Sentinel-1 SAR detections
-- per AOI and day, pre-joined to dim_aoi (name + analysis region). Null measures
-- with *_status = 'not_published' mean GFW has not released that day yet; they
-- are not zero. Unmatched SAR detections are review candidates, not confirmed
-- illegal activity. Overlapping AOIs (e.g. AOI-COAST inside AOI-GULF) are non-additive.
with activity as (
    select * from {{ source('gold', 'fact_maritime_activity_daily') }}
),
aoi as (
    select * from {{ ref('dim_aoi') }}
)
select
    m.aoi_key,
    a.aoi_name,
    a.region,
    m.date_key,
    m.fishing_hours,
    m.fishing_vessels,
    m.fishing_status,
    m.presence_hours,
    m.presence_vessels,
    m.presence_status,
    m.sar_detections,
    m.sar_unmatched_detections,
    m.sar_dark_fraction,
    m.sar_status
from activity m
left join aoi a on m.aoi_key = a.aoi_key

-- Pre-computed materialized aggregate: platform-wide daily KPIs (Task 10).
-- One row per calendar day summarizing every MVP EO data product — the executive
-- dashboard reads this single small table instead of scanning the wide products.
with fire as (
    select date_key,
           sum(detections)                         as fire_detections,
           max(max_frp)                            as peak_frp,
           count(distinct aoi_key)                 as fire_aois
    from {{ ref('serving_wildfire_daily') }}
    group by date_key
),
flood as (
    select date_key,
           sum(case when flood_flag then 1 else 0 end) as flood_aoi_days,
           count(distinct aoi_key)                      as flood_aois
    from {{ ref('serving_flood_daily') }}
    group by date_key
),
vessel as (
    select date_key,
           count(*)                                     as vessel_days,
           sum(case when suspicious_flag then 1 else 0 end) as suspicious_vessels
    from {{ ref('serving_vessel_activity') }}
    group by date_key
)
select
    coalesce(fire.date_key, flood.date_key, vessel.date_key) as date_key,
    coalesce(fire.fire_detections, 0)      as fire_detections,
    fire.peak_frp,
    coalesce(fire.fire_aois, 0)            as fire_aois,
    coalesce(flood.flood_aoi_days, 0)      as flood_aoi_days,
    coalesce(flood.flood_aois, 0)          as flood_aois,
    coalesce(vessel.vessel_days, 0)        as vessel_days,
    coalesce(vessel.suspicious_vessels, 0) as suspicious_vessels
from fire
full outer join flood  on fire.date_key = flood.date_key
full outer join vessel on coalesce(fire.date_key, flood.date_key) = vessel.date_key

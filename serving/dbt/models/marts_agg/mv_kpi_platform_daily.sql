-- Pre-computed materialized aggregate: daily platform KPIs per analysis region
-- (Task 10). One row per (date_key, region) summarizing the MVP EO data products;
-- the executive dashboard reads this single small table instead of scanning the
-- wide products. Vessel identity records carry no position, so maritime KPIs are
-- reported under region 'GLOBAL' and never added to a geographic region.
with fire as (
    select date_key, region,
           sum(detections)                         as fire_detections,
           max(max_frp)                            as peak_frp,
           count(distinct aoi_key)                 as fire_aois
    from {{ ref('serving_wildfire_daily') }}
    group by date_key, region
),
flood as (
    select date_key, region,
           sum(case when flood_flag then 1 else 0 end) as flood_aoi_days,
           count(distinct aoi_key)                      as flood_aois
    from {{ ref('serving_flood_daily') }}
    group by date_key, region
),
vessel as (
    select date_key, 'GLOBAL' as region,
           count(*)                                     as vessel_days,
           sum(case when suspicious_flag then 1 else 0 end) as suspicious_vessels
    from {{ ref('serving_vessel_activity') }}
    group by date_key
),
spine as (
    select date_key, region from fire
    union select date_key, region from flood
    union select date_key, region from vessel
)
select
    s.date_key,
    coalesce(s.region, 'UNASSIGNED')       as region,
    coalesce(fire.fire_detections, 0)      as fire_detections,
    fire.peak_frp,
    coalesce(fire.fire_aois, 0)            as fire_aois,
    coalesce(flood.flood_aoi_days, 0)      as flood_aoi_days,
    coalesce(flood.flood_aois, 0)          as flood_aois,
    coalesce(vessel.vessel_days, 0)        as vessel_days,
    coalesce(vessel.suspicious_vessels, 0) as suspicious_vessels
from spine s
left join fire   on fire.date_key   = s.date_key and fire.region   is not distinct from s.region
left join flood  on flood.date_key  = s.date_key and flood.region  is not distinct from s.region
left join vessel on vessel.date_key = s.date_key and vessel.region = s.region
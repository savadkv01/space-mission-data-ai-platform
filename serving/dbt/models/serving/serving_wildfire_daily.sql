-- Serving data product: Wildfire Activity (UC-15). Mirrors
-- serving.marts.serving_marts.serve_wildfire_daily. Wide, business-named, and
-- pre-joined to dim_aoi + EMS corroboration so BI/API read with no runtime joins.
with fire as (
    select * from {{ source('gold', 'kpi_wildfire_aoi_daily') }}
),
aoi as (
    select * from {{ ref('dim_aoi') }}
),
corr as (
    select aoi_key, event_date
    from {{ source('gold', 'kpi_aoi_validation') }}
    where event_type = 'fire' and corroborated
),
freshness as (
    select * from {{ ref('serving_wildfire_freshness') }}
)
select
    f.aoi_key,
    a.aoi_name,
    a.region,
    f.date_key,
    f.detections,
    f.mean_frp,
    f.max_frp,
    a.area_km2,
    case
        when f.max_frp is null then 'unknown'
        when f.max_frp >= 100  then 'extreme'
        when f.max_frp >= 30   then 'high'
        when f.max_frp >= 10   then 'moderate'
        else 'low'
    end                                                   as severity,
    (c.aoi_key is not null)                               as ems_corroborated,
    s.latest_observation_ts,
    s.observation_age_hours,
    coalesce(s.freshness_status, 'no_observations')       as freshness_status,
    coalesce(s.publication_status, 'blocked')             as publication_status
from fire f
left join aoi  a on f.aoi_key = a.aoi_key
left join freshness s on s.region = a.region
left join corr c on f.aoi_key = c.aoi_key and f.date_key = c.event_date

-- Serving data product: Wildfire observation freshness per analysis region
-- (UC-15 publication gate). Mirrors serving.marts.serving_marts.wildfire_freshness.
-- Exactly one row per dim_aoi region, so a region with an empty or zero-record
-- FIRMS feed is visible as 'no_observations' instead of silently reading as
-- "no fires". Freshness is event-time (latest acquired detection inside the
-- region envelope), not last landing. Regions are judged independently: a fresh
-- INDIA feed never makes UAE-GULF look current. Evaluated at build time; BI
-- re-evaluates age against now() at query time.
with regions as (
    select distinct region from {{ ref('dim_aoi') }} where region is not null
),
obs as (
    select
        region,
        max(try_cast(event_ts as timestamptz)) as latest_observation_ts,
        count(*)                               as detections_total
    from {{ source('gold', 'fire_aoi_attribution') }}
    where region is not null
    group by region
),
evaluated as (
    select
        r.region,
        o.latest_observation_ts,
        coalesce(o.detections_total, 0)                             as detections_total,
        now()                                                       as freshness_evaluated_at,
        {{ var('wildfire_max_observation_age_hours', 24) }}         as max_observation_age_hours,
        round(date_diff('second', o.latest_observation_ts, now()) / 3600.0, 3)
                                                                    as observation_age_hours
    from regions r
    left join obs o on o.region = r.region
)
select
    region,
    latest_observation_ts,
    freshness_evaluated_at,
    observation_age_hours,
    max_observation_age_hours,
    detections_total,
    case
        when latest_observation_ts is null then 'no_observations'
        when observation_age_hours between 0 and max_observation_age_hours then 'current'
        else 'stale'
    end                                                             as freshness_status,
    case
        when latest_observation_ts is not null
             and observation_age_hours between 0 and max_observation_age_hours
            then 'exploratory'
        else 'blocked'
    end                                                             as publication_status
from evaluated
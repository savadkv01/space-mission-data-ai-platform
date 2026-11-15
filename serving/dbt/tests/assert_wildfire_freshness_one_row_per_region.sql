-- The wildfire freshness gate must publish exactly one status row per analysis
-- region, so an empty FIRMS feed can never disappear from the serving layer.
with regions as (
    select distinct region from {{ ref('dim_aoi') }} where region is not null
),
gate as (
    select region, count(*) as status_rows
    from {{ ref('serving_wildfire_freshness') }}
    group by region
)
select r.region, coalesce(g.status_rows, 0) as status_rows
from regions r
left join gate g on g.region = r.region
where coalesce(g.status_rows, 0) <> 1
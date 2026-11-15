-- D-01 reconciliation: the executive fire total must equal the number of
-- distinct vegetation-fire detections attributed to a reporting AOI in the
-- per-detection ledger (fire_aoi_attribution), per region and day. A mismatch
-- means a detection was counted twice (overlapping reporting AOIs) or dropped.
with ledger as (
    select a.date_key, d.region, count(*) as detections
    from {{ source('gold', 'fire_aoi_attribution') }} a
    join {{ ref('dim_aoi') }} d on d.aoi_key = a.reporting_aoi_key
    where a.reporting_aoi_key is not null
      and a.heat_source_class = 'vegetation_fire'
    group by a.date_key, d.region
),
rollup as (
    select date_key, region, fire_detections
    from {{ ref('mv_kpi_platform_daily') }}
    where region not in ('GLOBAL', 'UNASSIGNED')
)
select
    coalesce(l.date_key, r.date_key) as date_key,
    coalesce(l.region, r.region)     as region,
    coalesce(l.detections, 0)        as ledger_detections,
    coalesce(r.fire_detections, 0)   as rollup_detections
from ledger l
full outer join rollup r on r.date_key = l.date_key and r.region = l.region
where coalesce(l.detections, 0) <> coalesce(r.fire_detections, 0)

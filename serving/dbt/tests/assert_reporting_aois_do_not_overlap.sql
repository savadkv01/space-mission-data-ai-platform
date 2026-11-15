-- ADR-12: rollup-eligible AOIs form a non-overlapping reporting partition per
-- region (shared edges allowed). Any pair with a positive-area overlap would be
-- double counted by the region rollups.
with boxes as (
    select
        aoi_key,
        region,
        cast(split_part(bbox, ',', 1) as double) as w,
        cast(split_part(bbox, ',', 2) as double) as s,
        cast(split_part(bbox, ',', 3) as double) as e,
        cast(split_part(bbox, ',', 4) as double) as n
    from {{ source('gold', 'ref_aoi') }}
    where rollup_eligible and bbox is not null
)
select a.aoi_key as aoi_a, b.aoi_key as aoi_b, a.region
from boxes a
join boxes b
  on a.region = b.region
 and a.aoi_key < b.aoi_key
where least(a.e, b.e) - greatest(a.w, b.w) > 0
  and least(a.n, b.n) - greatest(a.s, b.s) > 0

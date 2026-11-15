-- Serving data product: Vegetation Health. Mirrors
-- serving.marts.climate.climate_products.serve_vegetation_health_daily. Wide,
-- business-named, and pre-joined to dim_aoi so BI/API read with no runtime joins.
-- A null trend (< 2 NDVI observations) is 'unknown', not 'flat'. crop_stress_flag
-- (NDVI < 0.3 AND declining) is null unless evidence decides it (crop_stress_status),
-- and is evaluated only on cropland AOIs (crop_stress_applicable, D-08): low,
-- declining NDVI over sea, desert or a city is not crop stress.
with veg as (
    select
        *,
        case
            when not coalesce(crop_stress_applicable, true) then 'not_evaluated'
            else {{ evidence_status(
                'crop_stress_flag',
                'ndvi_mean >= 0.3 or ndvi_trend_30d >= 0',
                'ndvi_mean is not null or ndvi_trend_30d is not null'
            ) }}
        end as crop_stress_status
    from {{ source('gold', 'fact_vegetation_health_daily') }}
),
aoi as (
    select * from {{ ref('dim_aoi') }}
)
select
    v.aoi_key,
    a.aoi_name,
    a.region,
    v.date_key,
    v.ndvi_mean,
    v.ndvi_max,
    v.evi_mean,
    v.ndvi_trend_30d,
    case
        when v.ndvi_trend_30d is null then 'unknown'
        when v.ndvi_trend_30d > 0     then 'improving'
        when v.ndvi_trend_30d < 0     then 'declining'
        else 'flat'
    end                                                   as ndvi_trend_dir,
    v.valid_pixel_fraction,
    v.ndvi_health_band,
    case v.ndvi_health_band
        when 0 then 'Bare / water'
        when 1 then 'Sparse'
        when 2 then 'Moderate'
        when 3 then 'Healthy'
        when 4 then 'Dense'
        else 'unknown'
    end                                                   as ndvi_health_label,
    {{ decided_flag('v.crop_stress_status') }}            as crop_stress_flag,
    v.crop_stress_status,
    coalesce(v.crop_stress_applicable, true)              as crop_stress_applicable,
    a.area_km2
from veg v
left join aoi a on v.aoi_key = a.aoi_key

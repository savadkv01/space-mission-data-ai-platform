-- Pre-computed materialized aggregate: platform-wide daily climate KPIs (Phase 11b).
-- One row per calendar day summarizing the air-quality / dust / climate /
-- vegetation products, mirroring mv_kpi_platform_daily. The executive and weather
-- dashboards read this single small table instead of scanning the wide products.
with aq as (
    select date_key,
           avg(aqi_pm25)                                     as mean_aqi_pm25,
           sum(case when exceedance_flag then 1 else 0 end)  as aqi_exceedance_days,
           count(distinct aoi_key)                           as air_quality_aois
    from {{ ref('serving_air_quality_daily') }}
    group by date_key
),
dust as (
    select date_key,
           sum(case when dust_flag then 1 else 0 end)        as dust_event_days,
           max(aod_mean)                                     as peak_aod,
           count(distinct aoi_key)                           as dust_aois
    from {{ ref('serving_dust_event_daily') }}
    group by date_key
),
clim as (
    select date_key,
           avg(lst_anomaly_c)                                   as mean_lst_anomaly,
           sum(case when warming_flag then 1 else 0 end)        as warming_days,
           sum(case when desertification_flag then 1 else 0 end) as desertification_days
    from {{ ref('serving_climate_indicator_daily') }}
    group by date_key
),
veg as (
    select date_key,
           avg(ndvi_mean)                                    as mean_ndvi,
           sum(case when crop_stress_flag then 1 else 0 end) as crop_stress_days
    from {{ ref('serving_vegetation_health_daily') }}
    group by date_key
)
select
    coalesce(aq.date_key, dust.date_key, clim.date_key, veg.date_key) as date_key,
    aq.mean_aqi_pm25,
    coalesce(aq.aqi_exceedance_days, 0)    as aqi_exceedance_days,
    coalesce(aq.air_quality_aois, 0)       as air_quality_aois,
    coalesce(dust.dust_event_days, 0)      as dust_event_days,
    dust.peak_aod,
    coalesce(dust.dust_aois, 0)            as dust_aois,
    clim.mean_lst_anomaly,
    coalesce(clim.warming_days, 0)         as warming_days,
    coalesce(clim.desertification_days, 0) as desertification_days,
    veg.mean_ndvi,
    coalesce(veg.crop_stress_days, 0)      as crop_stress_days
from aq
full outer join dust on aq.date_key = dust.date_key
full outer join clim on coalesce(aq.date_key, dust.date_key) = clim.date_key
full outer join veg  on coalesce(aq.date_key, dust.date_key, clim.date_key) = veg.date_key

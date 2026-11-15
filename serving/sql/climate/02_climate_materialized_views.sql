-- =============================================================================
-- Serving Layer - Climate materialized aggregate (Phase 11b, Task 3)
-- =============================================================================
-- Small, dashboard-shaped daily climate rollup per analysis region, refreshed
-- after the climate data products rebuild. Mirrors
-- ../../dbt/models/marts_agg/mv_kpi_climate_daily.sql. Regions are never summed
-- together (UAE-GULF and INDIA use different AQI standards and coverage).
-- =============================================================================

CREATE SCHEMA IF NOT EXISTS serving_agg;

CREATE OR REPLACE TABLE serving_agg.mv_kpi_climate_daily AS
-- Only rollup-eligible AOIs (non-overlapping reporting partition, ADR-12) are counted.
with eligible as (
    select aoi_key from semantic.dim_aoi where rollup_eligible
),
aq as (
    select date_key, region,
           avg(aqi_pm25)                                     as mean_aqi_pm25,
           sum(case when exceedance_flag then 1 else 0 end)  as aqi_exceedance_days,
           sum(case when exceedance_status in ('positive', 'negative') then 1 else 0 end) as aqi_exceedance_evaluated_aois,
           count(distinct aoi_key)                           as air_quality_aois
    from serving.serving_air_quality_daily
    where aoi_key in (select aoi_key from eligible)
    group by date_key, region
),
dust as (
    select date_key, region,
           sum(case when dust_flag then 1 else 0 end)        as dust_event_days,
           sum(case when dust_status in ('positive', 'negative') then 1 else 0 end) as dust_evaluated_aois,
           max(aod_mean)                                     as peak_aod,
           count(distinct aoi_key)                           as dust_aois
    from serving.serving_dust_event_daily
    where aoi_key in (select aoi_key from eligible)
    group by date_key, region
),
clim as (
    select date_key, region,
           avg(lst_anomaly_c)                                   as mean_lst_anomaly,
           sum(case when warming_flag then 1 else 0 end)        as warming_days,
           sum(case when warming_status in ('positive', 'negative') then 1 else 0 end) as warming_evaluated_aois,
           sum(case when desertification_flag then 1 else 0 end) as desertification_days,
           sum(case when desertification_status in ('positive', 'negative') then 1 else 0 end) as desertification_evaluated_aois
    from serving.serving_climate_indicator_daily
    where aoi_key in (select aoi_key from eligible)
    group by date_key, region
),
veg as (
    select date_key, region,
           avg(ndvi_mean)                                    as mean_ndvi,
           sum(case when crop_stress_flag then 1 else 0 end) as crop_stress_days,
           sum(case when crop_stress_status in ('positive', 'negative') then 1 else 0 end) as crop_stress_evaluated_aois
    from serving.serving_vegetation_health_daily
    where aoi_key in (select aoi_key from eligible)
    group by date_key, region
),
spine as (
    select date_key, region from aq
    union select date_key, region from dust
    union select date_key, region from clim
    union select date_key, region from veg
)
select
    s.date_key,
    coalesce(s.region, 'UNASSIGNED')                      as region,
    aq.mean_aqi_pm25,
    coalesce(aq.aqi_exceedance_days, 0)                   as aqi_exceedance_days,
    coalesce(aq.aqi_exceedance_evaluated_aois, 0)         as aqi_exceedance_evaluated_aois,
    coalesce(aq.air_quality_aois, 0)                      as air_quality_aois,
    coalesce(dust.dust_event_days, 0)                     as dust_event_days,
    coalesce(dust.dust_evaluated_aois, 0)                 as dust_evaluated_aois,
    dust.peak_aod,
    coalesce(dust.dust_aois, 0)                           as dust_aois,
    clim.mean_lst_anomaly,
    coalesce(clim.warming_days, 0)                        as warming_days,
    coalesce(clim.warming_evaluated_aois, 0)              as warming_evaluated_aois,
    coalesce(clim.desertification_days, 0)                as desertification_days,
    coalesce(clim.desertification_evaluated_aois, 0)      as desertification_evaluated_aois,
    veg.mean_ndvi,
    coalesce(veg.crop_stress_days, 0)                     as crop_stress_days,
    coalesce(veg.crop_stress_evaluated_aois, 0)           as crop_stress_evaluated_aois
from spine s
left join aq   on aq.date_key   = s.date_key and aq.region   is not distinct from s.region
left join dust on dust.date_key = s.date_key and dust.region is not distinct from s.region
left join clim on clim.date_key = s.date_key and clim.region is not distinct from s.region
left join veg  on veg.date_key  = s.date_key and veg.region  is not distinct from s.region;

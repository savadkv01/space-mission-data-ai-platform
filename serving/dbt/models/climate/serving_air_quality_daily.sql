-- Serving data product: Air Quality. Mirrors
-- serving.marts.climate.climate_products.serve_air_quality_daily. Wide,
-- business-named, and pre-joined to dim_aoi so BI/API read with no runtime joins.
-- exceedance_flag is null unless PM evidence decides it (see exceedance_status);
-- a null aqi_band means no surface PM measurement, not "Good".
with aq as (
    select
        *,
        {{ evidence_status(
            'exceedance_flag',
            'pm25_mean is not null and pm10_mean is not null',
            'pm25_mean is not null or pm10_mean is not null'
        ) }} as exceedance_status
    from {{ source('gold', 'fact_air_quality_daily') }}
),
aoi as (
    select * from {{ ref('dim_aoi') }}
)
select
    q.aoi_key,
    a.aoi_name,
    a.region,
    q.date_key,
    q.pm25_mean,
    q.pm25_max,
    q.pm10_mean,
    q.pm10_max,
    q.no2_column_mean,
    q.so2_column_mean,
    q.co_column_mean,
    q.o3_column_mean,
    q.station_count,
    q.aqi_pm25,
    q.aqi_pm10,
    q.aqi_band,
    q.aqi_standard,
    {{ decided_flag('q.exceedance_status') }}             as exceedance_flag,
    q.exceedance_status,
    case
        when q.pm25_mean is not null and q.pm10_mean is not null then 'pm25_and_pm10'
        when q.pm25_mean is not null then 'pm25_only'
        when q.pm10_mean is not null then 'pm10_only'
        else 'none'
    end                                                   as pm_coverage,
    a.area_km2
from aq q
left join aoi a on q.aoi_key = a.aoi_key

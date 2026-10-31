-- Gold: Air-Quality Analytics (Phase 9b) -> fact_air_quality_daily (1 row/AOI/day).
-- Mirrors transformation.batch.climate_silver_to_gold.gold_air_quality_daily so
-- the SQL and Spark/pure-Python paths produce the same KPI definition. AOI
-- membership is already resolved in Silver (station->AOI tagging), so this mart
-- is a pure SQL aggregation (no point-in-polygon needed here — ADR-SV-01).
with surface as (
    select
        aoi_id                                                as aoi_key,
        stat_date                                             as date_key,
        pollutant_code,
        value_std,
        location_id
    from {{ source('silver_climate', 'silver_air_quality') }}
    where aoi_id is not null
      and quality_flag = 'valid'
),
agg_surface as (
    select
        aoi_key,
        date_key,
        avg(case when pollutant_code = 'PM25' then value_std end) as pm25_mean,
        max(case when pollutant_code = 'PM25' then value_std end) as pm25_max,
        avg(case when pollutant_code = 'PM10' then value_std end) as pm10_mean,
        max(case when pollutant_code = 'PM10' then value_std end) as pm10_max,
        count(distinct case
            when pollutant_code in ('PM25', 'PM10') then location_id
        end)                                                     as station_count
    from surface
    group by aoi_key, date_key
),
columns as (
    select
        aoi_id                                                as aoi_key,
        stat_date                                             as date_key,
        gas_code,
        mean,
        valid_pixel_fraction,
        quality_flag
    from {{ source('silver_climate', 'silver_atmos_column') }}
    where aoi_id is not null
),
agg_columns as (
    select
        aoi_key,
        date_key,
        avg(case when gas_code = 'NO2' and quality_flag <> 'low_coverage' then mean end) as no2_column_mean,
        avg(case when gas_code = 'SO2' and quality_flag <> 'low_coverage' then mean end) as so2_column_mean,
        avg(case when gas_code = 'CO'  and quality_flag <> 'low_coverage' then mean end) as co_column_mean,
        avg(case when gas_code = 'O3'  and quality_flag <> 'low_coverage' then mean end) as o3_column_mean,
        avg(valid_pixel_fraction)                                                        as column_valid_fraction
    from columns
    group by aoi_key, date_key
),
joined as (
    select
        coalesce(s.aoi_key, c.aoi_key)   as aoi_key,
        coalesce(s.date_key, c.date_key) as date_key,
        s.pm25_mean, s.pm25_max, s.pm10_mean, s.pm10_max,
        coalesce(s.station_count, 0)     as station_count,
        c.no2_column_mean, c.so2_column_mean, c.co_column_mean, c.o3_column_mean,
        c.column_valid_fraction
    from agg_surface s
    full outer join agg_columns c
        on s.aoi_key = c.aoi_key and s.date_key = c.date_key
),
aqi as (
    select
        *,
        case
            when pm25_mean is null or station_count < 1 then null
            when pm25_mean <= 12.0  then cast(round((50-0)  /(12.0-0.0)  *(pm25_mean-0.0)  +0)   as integer)
            when pm25_mean <= 35.4  then cast(round((100-51)/(35.4-12.1) *(pm25_mean-12.1) +51)  as integer)
            when pm25_mean <= 55.4  then cast(round((150-101)/(55.4-35.5)*(pm25_mean-35.5) +101) as integer)
            when pm25_mean <= 150.4 then cast(round((200-151)/(150.4-55.5)*(pm25_mean-55.5)+151) as integer)
            when pm25_mean <= 250.4 then cast(round((300-201)/(250.4-150.5)*(pm25_mean-150.5)+201) as integer)
            when pm25_mean <= 500.4 then cast(round((500-301)/(500.4-250.5)*(pm25_mean-250.5)+301) as integer)
            else 500
        end as aqi_pm25,
        case
            when pm10_mean is null or station_count < 1 then null
            when pm10_mean <= 54.0  then cast(round((50-0)  /(54.0-0.0)  *(pm10_mean-0.0)  +0)   as integer)
            when pm10_mean <= 154.0 then cast(round((100-51)/(154.0-55.0)*(pm10_mean-55.0) +51)  as integer)
            when pm10_mean <= 254.0 then cast(round((150-101)/(254.0-155.0)*(pm10_mean-155.0)+101) as integer)
            when pm10_mean <= 354.0 then cast(round((200-151)/(354.0-255.0)*(pm10_mean-255.0)+151) as integer)
            when pm10_mean <= 424.0 then cast(round((300-201)/(424.0-355.0)*(pm10_mean-355.0)+201) as integer)
            when pm10_mean <= 604.0 then cast(round((500-301)/(604.0-425.0)*(pm10_mean-425.0)+301) as integer)
            else 500
        end as aqi_pm10
    from joined
)
select
    aoi_key,
    date_key,
    pm25_mean, pm25_max, pm10_mean, pm10_max,
    no2_column_mean, so2_column_mean, co_column_mean, o3_column_mean,
    station_count,
    column_valid_fraction,
    aqi_pm25,
    aqi_pm10,
    case
        when aqi_pm25 is null and aqi_pm10 is null then null
        when greatest(coalesce(aqi_pm25, 0), coalesce(aqi_pm10, 0)) <= 50  then 'Good'
        when greatest(coalesce(aqi_pm25, 0), coalesce(aqi_pm10, 0)) <= 100 then 'Moderate'
        when greatest(coalesce(aqi_pm25, 0), coalesce(aqi_pm10, 0)) <= 150 then 'Unhealthy (sensitive)'
        when greatest(coalesce(aqi_pm25, 0), coalesce(aqi_pm10, 0)) <= 200 then 'Unhealthy'
        when greatest(coalesce(aqi_pm25, 0), coalesce(aqi_pm10, 0)) <= 300 then 'Very Unhealthy'
        else 'Hazardous'
    end as aqi_band,
    coalesce(pm25_mean > 15.0, false) or coalesce(pm10_mean > 45.0, false) as exceedance_flag
from aqi

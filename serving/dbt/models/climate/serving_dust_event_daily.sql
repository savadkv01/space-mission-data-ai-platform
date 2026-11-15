-- Serving data product: Dust Event. Mirrors
-- serving.marts.climate.climate_products.serve_dust_event_daily. Wide,
-- business-named, and pre-joined to dim_aoi so BI/API read with no runtime joins.
-- dust_flag / transport_flag are null unless evidence decides them (AND rules:
-- one observed sub-threshold component is a negative). Thresholds mirror
-- transformation.batch.climate_silver_to_gold (AOD 0.5; dust evidence = MAIAC
-- dust-model share 0.5, or UV aerosol index 1.0 when no aerosol model exists).
-- aerosol_load_label describes AOD of any aerosol type; dust_severity_label is
-- a dust label only for positive dust rows (D-07). corridor_aod_max is the
-- strongest AOD over *upwind* same-region AOIs (D-06).
with dust as (
    select
        *,
        {{ evidence_status(
            'dust_flag',
            'aod_mean < 0.5 or (dust_fraction is not null and dust_fraction < 0.5)'
            ~ ' or (dust_fraction is null and uv_aerosol_index_mean < 1.0)',
            'aod_mean is not null or uv_aerosol_index_mean is not null or dust_fraction is not null'
        ) }} as dust_status,
        {{ evidence_status(
            'transport_flag',
            'corridor_aod_max < 0.5 or wind_speed_mean <= 0',
            'corridor_aod_max is not null or wind_speed_mean is not null'
        ) }} as transport_status
    from {{ source('gold', 'fact_dust_event_daily') }}
),
aoi as (
    select * from {{ ref('dim_aoi') }}
)
select
    d.aoi_key,
    a.aoi_name,
    a.region,
    d.date_key,
    d.aod_mean,
    d.aod_max,
    d.uv_aerosol_index_mean,
    d.smoke_fraction,
    d.dust_fraction,
    coalesce(d.aerosol_type, 'unknown')                   as aerosol_type,
    d.wind_speed_mean,
    d.wind_dir_dominant,
    d.corridor_aod_max,
    d.valid_fraction,
    d.dust_severity_band,
    case d.dust_severity_band
        when 0 then 'Clear'
        when 1 then 'Hazy'
        when 2 then 'Elevated'
        when 3 then 'High'
        when 4 then 'Very high'
        else 'unknown'
    end                                                   as aerosol_load_label,
    case
        when d.dust_status = 'positive' then
            case d.dust_severity_band
                when 2 then 'Dusty'
                when 3 then 'Heavy dust'
                when 4 then 'Severe'
                else 'unknown'
            end
        when d.dust_status = 'negative' then 'No dust event'
        else 'unknown'
    end                                                   as dust_severity_label,
    {{ decided_flag('d.dust_status') }}                   as dust_flag,
    d.dust_status,
    {{ decided_flag('d.transport_status') }}              as transport_flag,
    d.transport_status,
    a.area_km2
from dust d
left join aoi a on d.aoi_key = a.aoi_key

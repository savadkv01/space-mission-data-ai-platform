-- Serving data product: Detection Validation (UC-27 / QA). Mirrors
-- serve_aoi_validation. Only Copernicus EMS activation footprints are ground
-- truth, so only they can be 'corroborated' / 'unconfirmed' (D-12). Other AOIs
-- report the platform's own signal as 'signal_only' / 'no_signal', which is not
-- independent corroboration.
select
    aoi_key,
    event_type,
    event_date,
    area_km2,
    evidence_days,
    coalesce(is_ems_activation, true) as is_ems_activation,
    signal_present,
    corroborated,
    case
        when coalesce(is_ems_activation, true) and corroborated then 'corroborated'
        when coalesce(is_ems_activation, true) then 'unconfirmed'
        when signal_present then 'signal_only'
        else 'no_signal'
    end as trust
from {{ source('gold', 'kpi_aoi_validation') }}

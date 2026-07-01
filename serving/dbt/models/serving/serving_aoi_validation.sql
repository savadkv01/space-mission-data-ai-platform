-- Serving data product: Detection Validation (UC-27 / QA). Mirrors
-- serve_aoi_validation. EMS ground-truth corroboration as a trust signal for
-- damage-assessment prioritization.
select
    aoi_key,
    event_type,
    event_date,
    area_km2,
    evidence_days,
    corroborated,
    case when corroborated then 'corroborated' else 'unconfirmed' end as trust
from {{ source('gold', 'kpi_aoi_validation') }}

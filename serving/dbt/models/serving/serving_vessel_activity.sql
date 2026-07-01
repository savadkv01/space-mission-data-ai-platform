-- Serving data product: Maritime Vessel Activity (UC-18). Mirrors
-- serve_vessel_activity. Surfaces the suspicious-identity heuristic and a
-- triage priority for the illegal-fishing review workflow.
select
    vessel_key,
    date_key,
    transmissions,
    flag,
    vessel_type,
    active_span_days,
    suspicious_flag,
    case when suspicious_flag then 'high' else 'normal' end as review_priority
from {{ source('gold', 'fact_vessel_activity') }}

-- Serving data product: Imagery Catalog (UC-25). Mirrors serve_scene_catalog.
-- Exposes searchability + a catalog-quality band for metadata management.
select
    scene_key,
    date_key,
    collection,
    provider,
    platform,
    geo_key,
    cloud_cover,
    completeness_score,
    is_searchable,
    case
        when not is_searchable            then 'unlisted'
        when completeness_score is null   then 'listed'
        when completeness_score >= 0.9    then 'gold'
        when completeness_score >= 0.7    then 'silver'
        else 'bronze'
    end as quality_band
from {{ source('gold', 'fact_scene_catalog') }}

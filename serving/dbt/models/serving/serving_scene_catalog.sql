-- Serving data product: Imagery Catalog (UC-25). Mirrors serve_scene_catalog.
-- Exposes searchability + a catalog-quality band for metadata management. The
-- band is driven by usability (cloud cover) once metadata is complete (D-11):
-- gold <= 10 % cloud, silver <= 30 %, bronze otherwise or incomplete metadata.
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
        when not is_searchable                                  then 'unlisted'
        when completeness_score is null or cloud_cover is null  then 'listed'
        when completeness_score < 0.7                           then 'bronze'
        when cloud_cover <= 10                                  then 'gold'
        when cloud_cover <= 30                                  then 'silver'
        else 'bronze'
    end as quality_band
from {{ source('gold', 'fact_scene_catalog') }}

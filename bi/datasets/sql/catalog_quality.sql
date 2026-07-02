-- Certified dataset: catalog_quality  (Superset virtual dataset)  [ENGINEERING]
-- Owner: Data Steward  |  Layer: serving (BI-certified aggregate)  |  Grain: collection
-- Rolls the per-scene serving product up to a collection-level quality summary.
-- This is a certified BI aggregate (not a per-chart ad-hoc query) so every
-- catalog-quality chart shares one definition of "searchable rate".
--
-- Superset database connection: `serving_duckdb`
select
    collection,
    provider,
    count(*)                                                     as scenes,
    sum(case when is_searchable then 1 else 0 end)               as searchable_scenes,
    round(avg(case when is_searchable then 1.0 else 0.0 end), 4) as searchable_rate,
    round(avg(completeness_score), 4)                           as mean_completeness,
    round(avg(cloud_cover), 4)                                  as mean_cloud_cover,
    sum(case when quality_band = 'gold'   then 1 else 0 end)     as gold_scenes,
    sum(case when quality_band = 'silver' then 1 else 0 end)     as silver_scenes,
    sum(case when quality_band = 'bronze' then 1 else 0 end)     as bronze_scenes
from serving.serving_scene_catalog
group by collection, provider

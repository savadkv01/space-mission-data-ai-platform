# 14 — Glossary

> Phase 12 · Task 14 — Glossary

| Term | Definition |
| --- | --- |
| **Apache Superset** | Open-source enterprise BI tool used for all platform dashboards. |
| **Certified dataset** | A governed, version-controlled Superset dataset mapped 1:1 to a serving product; the only dataset type allowed on dashboards. |
| **Virtual dataset** | A dataset defined by SQL (not a physical table); all BI datasets here are virtual, sourced from `bi/datasets/sql/`. |
| **Materialized aggregate** | A pre-computed rollup table (`mv_kpi_platform_daily`) backing latency-critical executive charts. |
| **Serving product** | A wide, business-named table produced by the serving dbt layer (e.g. `serving_wildfire_daily`) that BI reads. |
| **Semantic layer** | Single source of KPI formulas (`serving/marts/semantic.py`); BI/API/RAG all consume it. |
| **KPI** | Key Performance Indicator; a governed metric registered in the semantic layer and bound to a dataset in the BI KPI catalog. |
| **Severity band** | Pre-computed wildfire classification (extreme/high/moderate/low) from `max_frp`. |
| **Quality band** | Pre-computed scene classification (gold/silver/bronze/listed/unlisted) from completeness + searchability. |
| **Trust / corroboration** | Whether a detection is confirmed by Copernicus-EMS ground truth; the platform's headline quality signal. |
| **RBAC** | Role-Based Access Control; Superset roles (`exec`, `ops_eo`, `ops_maritime`, `steward`, `ai`, `demo`, `analyst`). |
| **RLS** | Row-Level Security; filters rows per role (e.g. maritime-only for `ops_maritime`). |
| **Assets-as-code** | Superset objects exported to YAML under `bi/superset/` and version-controlled; the UI is never the source of truth. |
| **Cache TTL** | Time-to-live for the Superset results cache (15 min aggregates, 1 h daily products). |
| **serving_refresh DAG** | Airflow pipeline that rebuilds serving products and warms the BI cache. |
| **AOI** | Area Of Interest; a Copernicus-EMS footprint used for wildfire/flood attribution and validation. |
| **NDWI** | Normalized Difference Water Index; drives the flood-day classification. |
| **FRP** | Fire Radiative Power; wildfire intensity measure (`mean_frp`/`max_frp`). |
| **Kp index** | Geomagnetic activity index (NOAA SWPC); drives the sim storm-day band. |
| **Simulation-Track (`sim`)** | Post-MVP demonstrator dashboards on synthetic spacecraft data (ADR-09), isolated to the `demo` role and hard-labelled. |
| **MVP** | Earth Observation Operations Intelligence scope: wildfire, flood, maritime, imagery catalog, detection validation. |
| **httpfs** | DuckDB extension letting the sim datasets read Gold Parquet directly from MinIO (`s3://gold/...`). |
| **DuckDB** | In-process analytical engine hosting the serving layer that Superset connects to. |

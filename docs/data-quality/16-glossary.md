# 16 — Glossary

| Term | Definition |
|------|------------|
| **AOI** | Area of Interest — a bounded geographic region (e.g. a Copernicus EMS activation footprint) used for detection roll-ups and validation. |
| **Bronze** | Raw, immutable landing layer storing source payloads plus provenance envelopes. |
| **Certification** | Governance status (`CERTIFIED`) that marks a dataset trusted for BI/ML/RAG consumption. |
| **Checkpoint** | A set of declarative expectations run against a batch after a transform and before publication. |
| **Completeness** | Quality dimension: required fields and expected records are present. |
| **Consistency** | Quality dimension: the same fact agrees across layers and marts. |
| **Corroboration** | Cross-source agreement (e.g. FIRMS fire inside an EMS fire AOI) used as a recall signal in `kpi_aoi_validation`. |
| **Drift** | A shift in a column's distribution vs its baseline, measured by PSI. |
| **DLQ** | Dead-Letter Queue — Kafka topic where invalid streaming records are routed for replay. |
| **Expectation** | A single named quality predicate with a severity (`critical`/`warn`). |
| **Freshness** | Quality dimension: `now − max(event_ts)` measured against a per-entity SLA. |
| **`frp`** | Fire Radiative Power (MW) — fire intensity in FIRMS detections. |
| **`geo_key`** | Spatial grid-cell identifier derived from (lat, lon), used for geospatial roll-ups. |
| **Gold** | Business-ready curated aggregates / KPI marts consumed by BI/ML/RAG. |
| **Great Expectations** | Open-source validation framework; this platform uses a dependency-free, laptop-friendly analogue. |
| **Integrity** | Quality dimension: referential and business relationships hold. |
| **IQR fence** | Interquartile-range outlier bound: `[Q1−1.5·IQR, Q3+1.5·IQR]`. |
| **Medallion** | The Bronze → Silver → Gold layered architecture. |
| **MTTD** | Mean Time To Detect — issue occurrence to alert firing. |
| **MTTR** | Mean Time To Recover — alert to data restored/certified. |
| **Natural key** | Business identifier used for deduplication (e.g. `fire_key`, `vessel_key`, `scene_key`). |
| **NDVI / NDWI / NBR** | Normalized spectral indices (vegetation / water / burn), each bounded `[-1, 1]`. |
| **Profiling** | Measuring the statistical shape of a dataset (stats, nulls, cardinality, distribution, outliers, drift). |
| **PSI** | Population Stability Index — a drift metric comparing actual vs baseline bin shares. |
| **Provenance** | Record-level lineage carried in the Bronze envelope (`_ingest_id`, `_batch_id`, `_checksum`, …). |
| **Quarantine** | Storage area (and DLQ) where invalid records are kept with reasons for triage and replay — never dropped. |
| **Reconciliation** | Cross-layer count/checksum/freshness checks proving no silent loss or duplication. |
| **`ref_aoi`** | Reference AOI footprints (Copernicus EMS) used as validation ground truth. |
| **Severity** | An expectation's blocking level: `critical` (hold) or `warn` (log + promote). |
| **Silver** | Cleaned, deduplicated, UTC-normalized, validated conformed layer. |
| **Simulation track** | Post-MVP synthetic datasets (telemetry, orbit, launch, space weather) retained as the streaming/anomaly-ML demonstrator (ADR-09). |
| **SLA** | Service Level Agreement — a measurable target (e.g. freshness ≤ 6 h). |
| **`suspicious_flag`** | UC-18 heuristic: set when a vessel lacks `flag` or `imo` (identity obfuscation). |
| **Timeliness** | Quality dimension: data arrives within its freshness SLA. |
| **Uniqueness** | Quality dimension: no unintended duplicate records after dedup. |
| **UC-14/15/16/18/25/27** | The six MVP Earth-observation use cases (change, wildfire, flood, fishing, catalog, damage). |
| **Validity** | Quality dimension: values conform to type, range and format rules. |
| **`valid_pixel_fraction`** | Share of usable (non-cloud/no-data) pixels in a spectral-index observation. |

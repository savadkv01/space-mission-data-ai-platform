# Phase 5b — Climate / Dust / Air-Quality Source Analysis (Extension)

Deep technical analysis of the new atmospheric sources that add **Climate Change**, **Dust Storm**, and **Air-Quality** monitoring to the platform. Extends Phase 5 ([`../README.md`](../README.md)) — data understanding only, no ingestion or code.

## Documents

| # | Document | Purpose |
| --- | --- | --- |
| 01 | [Climate Dataset Inventory](./01-climate-dataset-inventory.md) | New IN-scope sources + deferred sources |
| 02 | [AOI Strategy](./02-aoi-strategy.md) | Bounding boxes + why AOI clipping is mandatory |
| 03 | [Derived Indicators](./03-derived-indicators.md) | Climate indicators from existing data (no ingest) |
| 04 | [Climate Data Quality](./04-climate-data-quality.md) | Cloud/QA/unit/latency risks |
| 05 | [Use-Case Mapping](./05-climate-use-case-mapping.md) | Sources → climate/dust/air-quality use cases |
| 06 | [Transformation Complexity](./06-climate-transformation-complexity.md) | Low/Med/High per source |
| 07 | [Data Relationships](./07-climate-data-relationships.md) | Atmospheric ↔ AOI/wind/fire graph |
| 08 | [Freshness & Risks](./08-climate-freshness-risks.md) | Cadence tiers + risk register |
| 09 | [MVP & Deferred](./09-climate-mvp-and-deferred.md) | MVP set + excluded (CAMS/ERA5/geostationary) |
| 10 | [Glossary](./10-glossary.md) | Climate/atmospheric terms |

## Scope Note

Light expansion — **only** sources fitting the existing tabular / statistical-API pattern (Strategy A) and the 16 GB / Docker budget.

- **IN scope:** OpenAQ, Sentinel-5P/TROPOMI via Sentinel Hub Statistical API, MODIS/VIIRS AOD, derived indicators from already-ingested sources.
- **OUT of scope (deferred):** CAMS / ERA5 raw NetCDF (needs a binary blob-landing capability), geostationary SEVIRI/Himawari (violates the 16 GB budget). See [`09-climate-mvp-and-deferred.md`](./09-climate-mvp-and-deferred.md).

Documentation only. Do NOT proceed to data modeling or ingestion design (Phase 8b).

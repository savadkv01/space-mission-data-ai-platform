# Phase 13 — Feature Store

The Phase 13 implementation provides Feast feature definitions, a PostgreSQL
offline/online store and SQL registry, PIT training-data retrieval, a
readiness-aware online endpoint, and an Airflow materialization trigger.

## Documents

| # | Document | Purpose |
|---|---|---|
| 01 | [Strategy](./01-strategy.md) | Architecture, ownership, freshness, reuse |
| 02 | [Feature catalog](./02-feature-catalog.md) | Entities, views, fields, grains, TTLs |
| 03 | [Readiness and blockers](./03-readiness-and-blockers.md) | Eligibility gates tied to the source-analysis plan |
| 04 | [Training data](./04-training-data.md) | PIT joins, versions, deterministic splits |
| 05 | [Online serving](./05-online-serving.md) | Retrieval, cache, fallback, freshness |
| 06 | [Pipelines and operations](./06-pipelines-and-operations.md) | Sync, materialize, schedule, backfill |
| 07 | [Quality and drift](./07-quality-and-drift.md) | Contracts, null checks, drift monitoring |
| 08 | [Governance](./08-governance.md) | Lineage, ownership, versioning, deprecation |
| 09 | [Trade-offs](./09-trade-offs.md) | Feast, storage, and compute choices |
| 10 | [Production incidents](./10-incidents.md) | Ten tabletop incident scenarios |
| 11 | [KPIs and risks](./11-kpis-and-risks.md) | Acceptance evidence and delivery risks |
| 12 | [ADRs](./12-adr.md) | Architecture decisions |
| 13b | [Climate feature store](./climate.md) | Phase 13b climate, dust, and air-quality features |
| 13 | [Glossary](./13-glossary.md) | Shared terminology |

## Quick links

- Runtime package: [`feature_store/`](../../feature_store/)
- Analysis-readiness baseline: [implementation plan](../source-data-analysis/15-data-analysis-readiness-implementation-plan.md)
- Operator steps: [OPERATIONS.md](../../OPERATIONS.md#15-feature-store-phase-13)

**Release constraint:** feature registration is not feature certification. At
the current readiness baseline, only synthetic demo features and restricted
scene-catalog metadata can be materialized. They are explicitly marked with
their permitted uses; all other feature views are blocked.

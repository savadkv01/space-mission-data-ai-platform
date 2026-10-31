# 11 — KPIs, Risks, and Acceptance

## Acceptance evidence

| Measure | Target | Phase 13 evidence / current limit |
|---|---:|---|
| Registered domain contracts | 11 feature views across 7 entity types | Code definitions cover satellite, mission, orbit, launch, weather, EO, vessel, air quality, dust |
| PostgreSQL backends | Offline + online + registry | Single existing Postgres instance and `feast` schema |
| PIT correctness | No future feature leakage | Integration test queries two event times and verifies historical values |
| Online materialization and retrieval | At least one working source | Synthetic demo tested; Gold scene metadata materialized with restricted use |
| Blocked feature rejection | 100% of blocked view requests rejected | Online API returns HTTP 409 before database lookup |
| Source lineage | All materialized rows include nature, status, date, and source reference | Enforced by source table schema and pipeline |
| Drift check | PSI computed and reportable | Advisory only; no domain-approved universal threshold |
| Startup resources | ≤1 GB and 1 CPU | Docker Compose service limits |
| Analysis-ready use cases | No unreviewed features labeled certified | All real operational candidate views remain blocked/restricted |

## Risks

| Risk | Mitigation |
|---|---|
| Feast/Postgres offline store is a contrib implementation | Pin Feast, run integration tests against the actual platform Postgres, and keep a rollback path. |
| Staging Gold into Postgres duplicates storage | Sync only selected Gold outputs and profile table growth; keep Gold authoritative. |
| Simulation features may be mistaken for spacecraft data | Explicit `synthetic_demo` nature, `demo_only` status, endpoint caveats, and documentation. |
| Cached fallback may be mistaken for current data | Include cache state, degraded flag, and freshness result in every response. |
| Existing Gold completeness gaps flow downstream | Readiness manifest blocks affected views; no arbitrary fill or inferred attribution. |
| Domain-owner thresholds are unavailable | Treat numerical PSI/null-rate business thresholds as advisory until approved. |
| Current scene metadata is old | Return stale status and keep scope to catalog discovery; refresh before promoting freshness. |

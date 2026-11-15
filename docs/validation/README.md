# Data Platform Validation

Evidence-based validation of ingestion, Bronze/Silver/Gold transformations,
serving products, and their analytical interpretation before ML or AI expansion.

| Assessment | Evidence | Release decision |
|---|---|---|
| [2026-11-01 end-to-end run](./2026-11-01-end-to-end-readiness.md) | [Machine-readable summary](./2026-11-01-evidence.json) | Hold ML/AI advancement: transport works, but correctness, coverage, and operational gates remain open. |
| [2026-11-14 priority remediation](./2026-11-14-priority-remediation.md) | Live dbt/stream re-run recorded in the document | Fixes V01 and the serving-contract parts of V05, V09, V12, V13; hold decision unchanged (domain acceptance, V02–V04, V06–V08, V10 remain open). |
| [2026-11-14 INDIA regional tier E2E](./2026-11-14-india-regional-e2e.md) | Two orchestrated `platform_batch_pipeline` runs (`…_india_regional_e2e`, `…_v2`) | Regional model live (UAE-GULF / INDIA / US-LEGACY). Fixes the FIRMS S-NPP end-of-feed and GEE index sign inversion (SG-01). Hold decision unchanged; flood permanent-water baseline (L1) and freshness objective (L2) need decisions. |

Assessments are timestamped observations, not continuing freshness guarantees.
A successful build or row-count reconciliation is not domain certification.
Full scan evidence and execution logs accompany the assessment as session artifacts.

See the [operations runbook](../../OPERATIONS.md) for execution commands and the
[existing remediation plan](../source-data-analysis/15-data-analysis-readiness-implementation-plan.md)
for earlier readiness work.

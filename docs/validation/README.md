# Data Platform Validation

Evidence-based validation of ingestion, Bronze/Silver/Gold transformations,
serving products, and their analytical interpretation before ML or AI expansion.

| Assessment | Evidence | Release decision |
|---|---|---|
| [2026-11-01 end-to-end run](./2026-11-01-end-to-end-readiness.md) | [Machine-readable summary](./2026-11-01-evidence.json) | Hold ML/AI advancement: transport works, but correctness, coverage, and operational gates remain open. |
| [2026-11-14 priority remediation](./2026-11-14-priority-remediation.md) | Live dbt/stream re-run recorded in the document | Fixes V01 and the serving-contract parts of V05, V09, V12, V13; hold decision unchanged (domain acceptance, V02–V04, V06–V08, V10 remain open). |
| [2026-11-14 INDIA regional tier E2E](./2026-11-14-india-regional-e2e.md) | Two orchestrated `platform_batch_pipeline` runs (`…_india_regional_e2e`, `…_v2`) | Regional model live (UAE-GULF / INDIA / US-LEGACY). Fixes the FIRMS S-NPP end-of-feed and GEE index sign inversion (SG-01). Hold decision unchanged; flood permanent-water baseline (L1) and freshness objective (L2) need decisions. |
| [2026-11-15 full E2E + domain analysis](./2026-11-15-full-e2e-domain-analysis.md) | Orchestrated `platform_master_pipeline` run `manual__2026-11-15_full_e2e_domain` (148/149 units, 126/126 dbt tests) plus serving/Silver/Bronze domain queries | Hold unchanged. New high-severity domain defects: D-01 overlapping-AOI double counting in rollups (UAE fire 1.82×), D-02 OpenAQ cap drops newest Delhi days, D-03 gas flaring published as UAE wildfire. **Remediated same day (§16):** run `manual__2026-11-15_remediation_e2e`, 128/128 serving tests incl. new overlap and fire-reconciliation tests; Phase 14 may start on INDIA wildfire, INDIA AQ and maritime subject to domain sign-off. |

Assessments are timestamped observations, not continuing freshness guarantees.
A successful build or row-count reconciliation is not domain certification.
Full scan evidence and execution logs accompany the assessment as session artifacts.

See the [operations runbook](../../OPERATIONS.md) for execution commands and the
[existing remediation plan](../source-data-analysis/15-data-analysis-readiness-implementation-plan.md)
for earlier readiness work.

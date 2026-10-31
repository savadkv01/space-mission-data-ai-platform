# Data Analysis Readiness — Implementation Plan

## 1. Purpose

Turn the currently populated lake and serving products into analysis that is
traceable, coverage-aware, and suitable for clearly bounded operational
questions. This plan prioritizes fixing evidence gaps in the data before
expanding dashboards, feature engineering, or machine learning.

This is a plan, not an authorization to start implementation. It does not
replace or advance the active phase prompt. The next implementation phase should
consume data products only after their readiness and limitations are explicit.

## 2. Executive Recommendation

Deliver one trustworthy analysis slice first: **fire detections associated
with defined areas of interest (AOIs)**. It has a real, populated source,
existing Gold summaries, and an operational interpretation, but current fire
coverage is incomplete: all 98 Silver fire rows have null brightness, and
only 45 detections appear in AOI-level daily results.

In parallel, reconcile the documented dataset catalog with the live lake and
publish repeatable quality/coverage evidence. Then restore spectral-index
availability for flood and vegetation analyses. Treat air quality, dust, and
vessel activity as bounded exploratory products until their measurement,
coverage, and event-grain limitations are resolved.

## 3. Observed Baseline

Live-state measurements below were collected on **2026-10-31** from MinIO,
Silver/Gold Parquet, and the serving DuckDB database. Counts are snapshot
measurements, not freshness guarantees.

| Area | Observed baseline | Analysis implication |
|---|---|---|
| Catalog versus live sources | Documentation describes 45 candidate datasets. The live Bronze bucket has 13 top-level prefixes, including 10 prominent source families. | A documented source is not necessarily implemented, accessible, or populated. Track these states separately. |
| Storage footprint | Bronze: 272 objects / 59.64 MiB. Silver: 43 objects / 0.40 MiB. Gold: 38 objects / 0.06 MiB. | Bronze storage is dominated by OpenAQ at 54.02 MiB; object size is not a substitute for record coverage. |
| Fire | 98 Silver rows; brightness null in all 98. Gold EO daily: 98 detections across four dates; AOI wildfire KPI: 45 detections across three dates and one AOI. | Investigate source-field availability and mapping; account for every detection in the AOI join, including unmatched records. |
| Scene catalog | 40 Sentinel-2 L2A metadata records; all marked searchable; average cloud cover 35.4%. | This is catalog metadata, not image pixels or a validated flood/vegetation result. |
| Spectral indices and derived products | `silver_index` has 0 rows; Gold flood, vegetation, and climate-indicator products have 0 rows. | These analytical domains are not currently supported by populated inputs. |
| Vessel activity | 77 vessel identities / activity rows; one transmission per activity row. IMO is missing for 86%; vessel type for 100%; 66 rows carry a suspicious heuristic flag. | Do not interpret flags as confirmed behavior or the current grain as a repeated track. |
| Air quality | 4,000 Silver observations across 6 pollutant codes, 7 locations, and 2 AOIs; serving product has 72 rows. | Daily aggregates have significant missing measures and O₃ arrives in two native units. |
| Dust / aerosol | 35 Silver aerosol rows across 5 AOIs; average valid fraction 0.904. Wind speed and direction are null in all 35 Gold dust rows. | AOD summaries are possible; wind-transport conclusions are not supported. |
| Synthetic mission data | Silver contains 120 telemetry, 30 orbit, and 20 space-weather rows. Streaming output has 6 verified window rows across 3 satellites. | Demonstrator data is useful for pipeline validation, not operational mission conclusions. |
| Deferred platform capabilities | Feature, quarantine, and MLflow-artifact buckets are empty. | Consistent with future-phase design; do not present these as populated analytical assets. |
| Source refresh | The latest preflight reported Sentinel Hub and TROPOMI HTTP 403 responses and a host-side GEE credential-path mismatch. | Cached data and current source availability must be reported separately. |

Use the [dataset inventory](./01-dataset-inventory.md) for the documented
catalog and the [data-quality assessment](./04-data-quality-assessment.md) for
catalog-level risks. Use the
[operations runbook](../../OPERATIONS.md) for live verification procedures.

## 4. Objectives and Scope

### Objectives

1. Make **designed**, **implemented**, **populated**, **refreshable**, and
   **analysis-ready** distinct, verifiable dataset states.
2. Make every published result traceable to source, transformation, time
   coverage, spatial coverage, and applicable quality rules.
3. Improve the fire/AOI slice enough to support an auditable operational
   summary.
4. Restore upstream data before presenting empty flood, vegetation, or climate
   products as analytical results.
5. Preserve known limitations in serving products, BI, and future feature
   inputs.

### Out of scope

- Implementing the Feature Store, ML, RAG, or API phases.
- Adding paid data sources, managed services, or hardware beyond the
  16-GB-laptop/Docker/open-source constraints.
- Claiming scientific validation or decision-grade performance without
  domain-owner review and appropriate reference labels.
- Treating synthetic telemetry as real spacecraft data.

## 5. Work Packages and Sequence

Work packages are ordered by dependency and analytical value. “Exit evidence”
must be retained in tests, profiling output, run metadata, or the relevant
product documentation. Numeric quality thresholds that depend on operational
risk require domain-owner approval before they become blocking gates.

| Package | Priority | Scope and implementation tasks | Dependencies | Exit evidence |
|---|---|---|---|---|
| **WP0 — Live-versus-designed inventory** | P0 | Extend the inventory model to record source, logical dataset, physical path/table, owner, source access status, last successful ingest, date range, row count, schema version, and states: designed / implemented / populated / refreshable / analysis-ready. Add a repeatable snapshot command that does not expose credentials. | None | A generated snapshot reconciles every documented source family with observed Bronze/Silver/Gold objects. Empty paths and unavailable sources are explicit rather than implied to be complete. |
| **WP1 — Fire detection and AOI evidence** | P1 | Trace `brightness` from source payload through Bronze envelope, Silver mapping, and Gold aggregation. Determine whether the source actually supplies brightness for each record; correct mapping only where evidence supports it. Record source-field absence separately from transformation loss. Add explicit spatial matching to AOIs with matched/unmatched counts, match method, and documented coordinate/geometry assumptions. Preserve FRP and confidence as independent measures. | WP0; source payload inspection | Regression tests cover the source-to-Silver mapping and null behavior. Every fire record is accounted for as matched or unmatched. Gold reconciliation explains the difference between 98 EO detections and the AOI-level subset; reports include date range and AOI coverage. |
| **WP2 — Spectral-index access and EO-derived use cases** | P1 | Diagnose Sentinel Hub 403s (entitlement, scope, token, endpoint) and confirm whether a permitted no-cost source or sample is available. If access is restored, ingest a small, reproducible AOI/date sample, populate `silver_index`, and validate index names, date, spatial keys, valid-pixel fraction, and provenance. Rebuild flood/vegetation products only from valid inputs. If access cannot be restored, mark dependent use cases blocked and do not synthesize production-looking output. | WP0; source entitlement or approved alternative | Successful source preflight and non-empty validated index data, or a documented blocked status with reason. Flood/vegetation outputs have tested lineage to real index observations and are non-empty for a known fixture/accepted sample. |
| **WP3 — Air-quality measurement integrity** | P2 | Document native and canonical units per pollutant/source. Verify O₃ conversion from ppm to the serving unit; test conversion boundaries and preserve original value/unit. Profile coverage by pollutant, location, AOI, date, and quality flag. Make missingness and station count visible in daily products; avoid interpreting null-only rows as clean air. | WP0; domain-approved unit conventions | Unit tests demonstrate correct, reversible/auditable conversion behavior. Product profiles expose counts, date bounds, coverage, and null rates by measure. Data contracts reject invalid units and impossible values according to approved rules. |
| **WP4 — Dust and atmospheric context** | P2 | Establish whether wind data exists in Bronze and whether it can be joined to aerosol observations by time and location. Add the join only with defined tolerances and match-rate reporting. Keep AOD-only metrics distinct from wind-supported transport metrics. Profile TROPOMI and MODIS access separately. | WP0; WP2/source access; time/space join rules | Wind-supported metrics are published only when matched evidence exists; otherwise fields remain explicitly unavailable. Join tests cover time tolerance, spatial tolerance, and unmatched records. |
| **WP5 — Vessel event grain and screening semantics** | P2 | Inspect GFW Bronze payloads and transformation logic to determine whether transmission-level observations are retained. If the payload supports it, preserve event-level position/time records separately from vessel identity and aggregate repeated observations into activity windows. Document the suspicious-flag rule, evidence fields, and intended use as screening, not confirmation. | WP0; GFW payload/schema review | Tests verify event-to-vessel aggregation and the flag explanation. Products report observation counts and coverage; no behavioral claim is based solely on a single transmission or a heuristic flag. |
| **WP6 — Analysis-ready contracts and BI evidence** | P1 foundation; complete after WP1–WP5 | Define shared product metadata: source lineage, refresh timestamp, event-time range, record count, geographic coverage, key-field completeness, quality status, synthetic/real classification, and limitations. Add automated checks for empty required datasets, schema drift, duplicates, timestamp/unit validity, and row-count reconciliation. Display product readiness and caveats in BI descriptions or accompanying views. | WP0; incremental with other packages | A product cannot be labeled analysis-ready without a reviewed contract and passing evidence. Failed or blocked gates are visible in run status and product metadata; empty-but-expected optional products are distinguished from failed required products. |

### Recommended sequencing

1. **WP0** establishes a reliable baseline and prevents design-versus-live
   ambiguity.
2. Implement **WP1** as the first end-to-end analytical slice. Start **WP6**
   alongside it so the fire result carries quality and coverage evidence.
3. Resolve **WP2** source availability before rebuilding flood or vegetation
   products.
4. Implement **WP3–WP5** as separate workstreams; do not combine their
   measurements until shared time/space keys and missingness behavior are
   proven.
5. Complete **WP6** product gates and BI exposure before downstream feature or
   model consumers rely on these products.

## 6. Analysis-Readiness Contract

Every serving product intended for analysis should publish the following,
either as columns, a companion metadata table, or an equivalent certified
dataset description:

| Contract field | Requirement |
|---|---|
| Business question and grain | State the decision supported and exactly what one row represents. |
| Source lineage | Identify source family, Bronze path, transformations, and output table. |
| Data nature | Label real/open, synthetic, reference, or derived data. |
| Time coverage | Report event-time minimum/maximum, distinct dates, and freshness separately. |
| Spatial coverage | Report AOI/location/grid counts, matched count, unmatched count, and matching method where applicable. |
| Completeness | Report null rates for decision-critical fields, not just an overall quality score. |
| Measurement semantics | Preserve native units, canonical units, conversions, flags, and aggregation behavior. |
| Quality status | Pass, warn, blocked, or not applicable, with rule results and explanatory details. |
| Limitations | State known source gaps, unsupported claims, and thresholds requiring approval. |

### Readiness gate

A product may be labeled **analysis-ready** only when:

- The declared grain and business question are reviewed.
- Required fields, units, timestamps, identifiers, and provenance have tested
  contracts.
- Date and spatial coverage are measurable and exposed.
- Source-to-product reconciliation explains exclusions and unmatched records.
- Missingness is reported for critical measures and is within
  domain-owner-approved bounds, or the product is explicitly restricted to a
  narrower use.
- At least one representative business query or acceptance scenario produces
  a reviewable result.
- Synthetic data is clearly separated from real observations.

Do not use “non-zero rows” or “DAG succeeded” as the sole readiness criterion.

## 7. Success Measures

These are proposed delivery measures, not claims about current quality. Agree
any business-risk thresholds with the relevant domain owner before making them
blocking.

| Measure | Current baseline | Target / acceptance |
|---|---:|---|
| Documented sources with explicit live-state classification | Not consistently reconciled | 100% of documented sources classified as designed, implemented, populated, refreshable, or blocked/not applicable. |
| Fire observations accounted for in AOI analysis | 45 of 98 in the AOI KPI | Every source fire is accounted for as matched or unmatched; no silent drop. Match coverage is reported and reviewed. |
| Fire brightness completeness | 0 of 98 populated | Source support and mapping are established. If available, mapped values pass tests; if unavailable, limitation is explicit and FRP remains a separately validated measure. |
| Spectral-index availability | 0 Silver rows | Valid, provenance-backed rows exist before derived flood/vegetation outputs are declared populated; otherwise dependent use cases are marked blocked. |
| Air-quality measure transparency | Significant nulls; mixed O₃ native units | Canonical-unit behavior is tested; per-measure coverage and missingness are exposed. |
| Vessel activity evidence | One transmission per activity row | Product distinguishes event observations from identity records; heuristic flag is documented and not represented as a confirmed event. |
| Run-to-product reconciliation | Stage success can coexist with partial/empty outputs | Required products have data-aware gates; optional/blocked products state why no rows are expected. |
| Product limitation visibility | Currently split across run notes and documentation | Every certified analytical product exposes its known data limitations and source freshness. |

## 8. Risks, Trade-offs, and Decisions

| Decision / risk | Preferred approach | Alternative and trade-off |
|---|---|---|
| Prioritize a single use case or improve all domains at once | Complete fire/AOI evidence first; build shared readiness metadata alongside it. | Parallelize every dataset, but this spreads effort across access problems and empty inputs, delaying a defensible result. |
| Source access unavailable | Mark dependent analysis blocked; pursue entitlement or a documented open alternative. | Use synthetic substitutes for workflow testing only; they cannot establish real-world analytical validity. |
| Missing source field versus transformation defect | Trace payload-to-product and retain explicit reason codes. | Fill nulls or infer values; this risks manufacturing evidence and hiding a mapping defect. |
| AOI association | Preserve matched and unmatched records and make spatial tolerance explicit. | Drop unmatched records; simpler aggregation, but it conceals coverage loss and biases summaries. |
| Dataset quality thresholds | Set blocking thresholds with domain owners using observed profiles and the intended decision. | Adopt arbitrary global thresholds; easy to automate, but inappropriate across distinct measures and use cases. |
| Shared quality framework scope | Start with reusable profiling/contracts that fit the current Docker and laptop footprint. | Add a larger metadata platform now; more capability, but unnecessary infrastructure and operational cost. |

## 9. Delivery and Verification

For each package:

1. Record the baseline snapshot and source/version context.
2. Implement the smallest change that preserves raw provenance and makes
   transformation semantics testable.
3. Add focused unit/contract tests and an integration check against a small,
   reproducible dataset.
4. Run the affected transformation, serving, and data-quality tests.
5. Verify the resulting rows and key distributions directly in Silver/Gold or
   serving, not only from run logs.
6. Update the live-versus-designed inventory, product limitations, and
   runbook/query instructions.
7. Obtain domain-owner review before changing a product from exploratory to
   analysis-ready.

Keep the existing open-source, free-data, Docker Desktop, and 16-GB laptop
constraints. Avoid downloading full satellite imagery when a small, licensed
AOI/date subset is sufficient for the acceptance scenario.

## 10. Definition of Done

This readiness improvement is complete when:

- The documented-versus-live source state is repeatable and unambiguous.
- The fire/AOI slice has reconciled coverage, tested field semantics, and
  explicit unmatched-record reporting.
- Empty flood/vegetation outputs are either backed by validated index inputs or
  clearly reported as blocked.
- Air-quality, dust, and vessel products disclose measurement and coverage
  limitations relevant to their intended use.
- Analysis-readiness status is based on tested contracts and domain-approved
  gates, not pipeline completion alone.
- The next downstream phase can identify which data products are safe to use
  and which remain exploratory, synthetic, or blocked.

## 11. Phase 13 Handoff Tracker

**Snapshot date:** 2026-10-31. This handoff records the effect of the
readiness baseline on Feature Store eligibility; it does not claim that the
upstream work packages below have been completed.

| Work package | Phase 13 disposition | Current status | Closure evidence |
|---|---|---|---|
| WP0 — live-versus-designed inventory | Mission, orbit, launch, and weather views remain unavailable until eligible source state and lineage are established. | Snapshot tooling implemented and live-verified for all 45 catalog entries, 40 observed lake families, and 9 serving products. Unimplemented/unprobed source states remain explicit; no certification inferred. | [Generated inventory](./live-readiness-snapshot.json) with paths, counts, UTC ranges, observed schemas, prior access evidence, and refresh state. |
| WP1 — fire/AOI evidence | Fire/AOI features remain blocked pending domain review; unmatched detections remain explicit. | Engineering slice verified: VIIRS brightness restored, all 1,686 unique detections accounted for, 258 matched and 1,428 unmatched, 472 overlapping AOI assignments reconciled through serving. Domain completeness/coverage acceptance is pending. | Source-to-Silver regression tests, persisted per-detection ledger, exact grid/AOI/serving reconciliation, and [fire contract](./16-live-readiness-and-fire-contract.md). |
| WP2 — spectral-index access | Flood, vegetation, NDVI, NDWI, and NBR features are blocked. No synthetic image features are generated. | Partial; the live GEE fallback now populates `silver_scene`, `silver_index`, and dependent Gold products, but index freshness breaches the ≤48-hour objective and quality/coverage still need domain approval. Features remain blocked. | Approved source access or alternative plus fresh, provenance-backed indices, cloud-mask/coverage validation, and derived-product tests. |
| WP3 — air-quality integrity | Pollutant features are blocked. | Open; native/canonical units and per-measure coverage are unresolved. | O3 conversion tests, source/native-unit preservation, null and coverage profiles. |
| WP4 — dust context | Wind-supported features are blocked; AOD and transport are not conflated. | Open; all 35 Gold wind measures remain null at baseline. | Evidence-backed temporal/spatial join and match-rate evidence, or explicit AOD-only use. |
| WP5 — vessel event grain | Activity features are blocked; heuristic flags are not treated as behavior. | Open; activity rows do not establish repeated transmission tracks. | Payload-level event retention, aggregation tests, and documented screening semantics. |
| WP6 — analysis-ready contracts | Phase 13 returns readiness state and limitations; the fire slice additionally publishes live lineage, freshness, completeness, coverage, and reconciliation gates. | Partial; fire technical gates pass, but domain approval is pending and other products are not globally certified. | Reviewed product contracts, approved thresholds, coverage reconciliation, and representative use-case review. |

The implementation and per-view release state are documented in
[docs/feature-store/03-readiness-and-blockers.md](../feature-store/03-readiness-and-blockers.md).
The baseline above remains a historical snapshot; the live refresh below updates
source and materialization status without certifying any product. **Feature
registration, non-zero rows, or successful materialization do not close a
readiness work package or certify an analytical product.**

### 11.1 Live refresh and upstream remediation (2026-10-31)

The event-time freshness snapshot was taken at approximately **2026-10-31
14:13 UTC**. Ages are approximate and measure `snapshot time − max(event_ts)`,
not ingestion time. Objectives are from the
[freshness SLA register](../../quality/monitoring/quality-kpis.md); where no
explicit SLA is registered, cadence observations are not represented as an SLA.

| Source / entity | Latest observed event (UTC) | Approx. age | Objective / result |
|---|---:|---:|---|
| NOAA SWPC | 2026-10-31 09:00 | 5.2 h | No explicit project freshness SLA; live JSON parsing and Silver routing are fixed. |
| CelesTrak TLE | 2026-10-31 04:14 | 9.9 h | Six-hour configured cadence; behind cadence, but no explicit freshness SLA was found. |
| NASA POWER | 2026-10-30 00:00 | 38 h | No explicit project freshness SLA found. |
| FIRMS MENA | 2026-10-31 10:56 | 3.2 h | ≤6 h; within objective. |
| GFW | 2026-10-29 23:59 | 38 h | ≤24 h objective breached; the connector remains a vessel-identity sample, not a live AIS track feed. |
| OpenAQ | 2026-10-31 12:00 | 2.2 h | ≤3 h; within objective after current-date filtering and up to five pages per sensor. |
| Sentinel-2 scenes | 2026-10-29 07:02 | 55 h | ≤12 h objective breached; source revisit is approximately five days. |
| Sentinel-2 indices | 2026-10-29 00:00 | 62 h | ≤48 h objective breached; no newer qualifying scene was available in the query window. |
| TROPOMI | 2026-10-30 00:00 | 38 h | ≤24 h objective breached; source publication latency remains. |
| MODIS AOD | 2026-10-27 00:00 | 110 h | ≤24 h objective breached; source publication latency remains. |

Remediation removed confirmed access and transformation blockers: SWPC object
responses now normalize `time_tag`/`Kp` and route through the space-weather
Silver cleaner; the full-run driver now uses recent windows and the MENA FIRMS
area; OpenAQ includes the current date and paginates beyond page one; and
Sentinel-2 scene/index ingestion uses the live GEE fallback while preserving
the existing Bronze source codes and downstream shapes. Sentinel Hub OAuth is
corrected, but its Catalog API still rejects this account with HTTP 403, so
restoring that account remains an external action. The existing Airflow
records for the eight source DAGs (SWPC, CelesTrak, POWER, FIRMS, OpenAQ,
TROPOMI, MODIS AOD, and GEE Sentinel-2) are now unpaused; both the CLI listing
and persisted `DagModel` states report `is_paused=False`.

The subsequent full Bronze-to-Silver-to-Gold/dbt run completed. It wrote 80
`silver_space_weather`, 60 `silver_scene`, 14 `silver_index`, 5,047
`silver_air_quality`, 50 `silver_aerosol`, and 140 `silver_atmos_column` rows;
the flood and vegetation Gold products contain 35 rows each. The dbt run passed
5/5 models and dbt tests passed 18/18. This verifies the processing path, not
data fitness: WP2 remains partial, and GFW, Sentinel-2, TROPOMI, and MODIS
freshness breaches remain open. Other work packages retain their documented
coverage, measurement, lineage, and domain-approval blockers.

### 11.2 WP0 / WP1 / fire-WP6 implementation verification

**2026-10-31 19:52 UTC snapshot:** the repeatable
[live inventory command](../../transformation/scripts/readiness_snapshot.py)
reconciled the 45-entry catalog with 40 observed Bronze/Silver/Gold families
and 9 serving products. Twelve catalog entries have explicit implementation
mappings and eleven have populated mapped paths; mappings are non-additive
and do not establish complete dataset coverage or current source access.
Supplemental families, unknown access, and partial/unknown profiling are explicit.

FIRMS field inspection proved that the prior brightness nulls were
transformation loss: the VIIRS payload supplies `bright_ti4` and `bright_ti5`,
not generic `brightness`. Silver now preserves I4 temperature, I5 separately,
selected native field, status, unit, and Bronze lineage. Source-absent and
invalid temperatures are distinguished from valid measurements.

The live rebuild retained 6,047 Bronze envelopes, removed 4,361 duplicate
natural keys, and produced 1,686 Silver detections with no quarantine. The
persisted Gold attribution ledger accounts for 258 matched and 1,428 unmatched
detections; 140 detections intersect multiple AOIs, yielding 472 assignments
and exactly 472 summed AOI Gold detections. All 10 serving wildfire rows
reconcile to Gold. Brightness, FRP, confidence, ingestion-ID, and batch-ID
null counts are zero. Grid FRP averaging was made order-invariant after live
reconciliation exposed floating-point rounding sensitivity.

All automated fire technical gates passed; serving dbt rebuilt 14 models
and passed 58 tests. Source event time spans 2026-06-30 to 2026-10-31 14:20 UTC;
freshness at this snapshot is approximately 5.53 hours, within the existing
six-hour objective. See the [fire contract](./16-live-readiness-and-fire-contract.md)
and [generated snapshot](./live-readiness-snapshot.json) for reproducible evidence.

**Remaining closure gates:** domain review of grain, geographic coverage,
completeness limits, severity interpretation, and the representative query.
Curated rectangular AOIs are not independently validated EMS activation
ground truth. WP6 remains partial, all analytical certification remains
blocked, and Phase 13b has not started.

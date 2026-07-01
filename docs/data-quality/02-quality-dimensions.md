# 02 — Data Quality Dimensions

> The eight dimensions the platform measures and enforces. Each has a definition,
> a rationale, example failures grounded in our real feeds, a business impact and
> a success metric that maps to the KPIs in
> [quality/monitoring/quality-kpis.md](../../quality/monitoring/quality-kpis.md).

---

## Dimension summary

| # | Dimension | Question | Primary metric |
|---|-----------|----------|----------------|
| 1 | Completeness | Is everything present? | completeness % |
| 2 | Accuracy | Are values correct? | validation pass rate |
| 3 | Consistency | Do values agree across the system? | reconciliation match |
| 4 | Timeliness | Is data fresh enough? | freshness SLA adherence |
| 5 | Validity | Do values conform to rules? | validity pass rate |
| 6 | Uniqueness | Are there duplicates? | duplicate % |
| 7 | Integrity | Do relationships hold? | referential-integrity pass |
| 8 | Availability | Can consumers reach the data? | availability % |

---

## 1. Completeness

- **Definition:** required fields and expected records are present.
- **Why it matters:** missing detections/metadata silently degrade decisions.
- **Example failures:** `silver_scene` missing `collection`; a FIRMS granule not
  ingested; a missing daily partition.
- **Business impact:** UC-25 search success drops; UC-15 false negatives rise.
- **Success metric:** completeness ≥ 99% on mandatory fields; ≥ 0.8 mean
  `completeness_score` for catalog.

## 2. Accuracy

- **Definition:** values reflect the real-world truth.
- **Why it matters:** wrong `frp` or coordinates mislead responders.
- **Example failures:** swapped lat/lon; mis-scaled `kp_index`; wrong
  `confidence` mapping.
- **Business impact:** wrong fire location / storm severity → bad response.
- **Success metric:** validation pass rate ≥ 99.5%; AOI detection match rate
  (cross-source corroboration via `kpi_aoi_validation`).

## 3. Consistency

- **Definition:** the same fact agrees everywhere (across layers/marts).
- **Why it matters:** BI numbers must match reconciled source counts.
- **Example failures:** Gold detection count ≠ Silver rows; `geomagnetic_storm`
  disagrees with `kp_index ≥ 5`.
- **Business impact:** loss of trust in dashboards.
- **Success metric:** Bronze↔Silver↔Gold reconciliation match ≥ 99.9%.

## 4. Timeliness

- **Definition:** data arrives within its freshness SLA.
- **Why it matters:** wildfire/flood value decays with age.
- **Example failures:** FIRMS feed delayed beyond 6 h; scheduler miss.
- **Business impact:** MTTD and alert latency degrade.
- **Success metric:** freshness SLA adherence ≥ 98% (SLAs per entity).

## 5. Validity

- **Definition:** values conform to type, range and format rules.
- **Why it matters:** invalid values corrupt aggregates and joins.
- **Example failures:** `latitude = 999`; `cloud_cover = 250`; unparseable
  timestamp.
- **Business impact:** corrupted KPIs; failed geospatial joins.
- **Success metric:** validity pass rate ≥ 99.5%; quarantine rate ≤ 1%.

## 6. Uniqueness

- **Definition:** no unintended duplicate records.
- **Why it matters:** duplicates inflate counts and skew intensity stats.
- **Example failures:** overlapping fetch windows duplicate `fire_key`; re-sent
  launch events.
- **Business impact:** overstated detections; wrong prioritization.
- **Success metric:** duplicate % ≤ 0.1% after dedup.

## 7. Integrity

- **Definition:** referential and business relationships hold.
- **Why it matters:** every AOI mart row must map to a real `ref_aoi`.
- **Example failures:** `kpi_wildfire_aoi_daily.aoi_key` with no `ref_aoi`; a
  satellite belonging to two missions.
- **Business impact:** broken validation/ground-truth logic.
- **Success metric:** referential-integrity checkpoint pass = 100%.

## 8. Availability

- **Definition:** certified data is reachable by consumers when needed.
- **Why it matters:** an unreachable mart is as bad as a missing one.
- **Example failures:** MinIO object unreadable; storage corruption.
- **Business impact:** analysts/ML blocked.
- **Success metric:** dataset availability ≥ 99.5%; MTTR ≤ 4 h.

---

## Dimension-to-layer enforcement

| Dimension | Bronze | Silver | Gold |
|-----------|:------:|:------:|:----:|
| Completeness | ✅ | ✅ | ✅ |
| Accuracy | — | ✅ | ✅ |
| Consistency | — | ✅ | ✅ |
| Timeliness | ✅ | ✅ | ✅ |
| Validity | ✅ | ✅ | ✅ |
| Uniqueness | — | ✅ | — |
| Integrity | — | — | ✅ |
| Availability | ✅ | ✅ | ✅ |

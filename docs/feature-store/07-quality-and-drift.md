# 07 — Data Quality and Drift

The package provides source profiling, structural validation, numeric bounds,
and Population Stability Index (PSI) comparison helpers. These checks report
evidence; they do not replace the source-specific quality suites or
domain-owner-approved blocking thresholds.

| Check | Behavior | Status |
|---|---|---|
| Entity key / event time | Missing values are contract failures | Blocking |
| Critical measure missingness | Per-field null rate is reported against an explicit caller-supplied bound | Blocking only when approved bound is supplied |
| Numeric ranges | Non-finite and out-of-contract values are reported | Blocking where a domain contract exists |
| Distribution drift | PSI compares a reference distribution to current values | Advisory; 0.2 default warning is not an approved global gate |
| Freshness | View-specific `max_age_hours` in readiness manifest | Response warning; blocked sources remain blocked regardless |
| Reconciliation | Source-specific exclusions and unmatched counts | WP0/WP1 upstream evidence still open |

## Monitoring record

Retain the source table path, event-time range, count, nature, readiness state,
materialization run time, per-field null rates, and rule outcomes for each
refresh. Empty inputs are reported as `no_data` or blocked with a reason; they
are never passed off as a successful populated product.

## Threshold governance

Do not promote PSI 0.2, a global null percentage, or any business-risk value to
a blocking gate without domain-owner approval. Numeric bounds must reflect the
feature's units and intended decision. Synthetic fixtures validate code paths
only.

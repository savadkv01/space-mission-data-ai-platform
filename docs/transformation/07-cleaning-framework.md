# 07 - Data Cleaning Framework

> **Phase 9 - Data Transformation** · Document 07 of 19

## Where Cleaning Happens

At the **Bronze → Silver boundary**. Bronze is never modified; Silver is the first guaranteed-clean layer. This keeps raw data auditable and cleaning reproducible.

## Rule Families

| Family | Rule | Correct or Reject | Code |
| --- | --- | --- | --- |
| Null handling | required key missing/null | **reject** (`null:<field>`) | `require_fields` |
| Type coercion | cast to canonical type | correct | `to_float` |
| Timestamp | parse → UTC ISO-8601 | correct; unparseable → **reject** | `normalize_timestamp` |
| Range / outlier | value outside physical bounds | **reject** (range) | `in_range` |
| Statistical outlier | |z| > 4 from window mean | flag | `is_outlier_zscore` |
| Duplicates | same natural key | dedup, keep latest | `deduplicate` |
| Geo | clamp lat / wrap lon / snap grid | correct | `normalize_position` |
| Schema mismatch | unknown extra fields | allow (schema-on-read); missing required → reject | `require_fields` |
| Corrupted record | un-decodable payload | **reject** to quarantine | transform driver |

Code: [transformation/cleaning/cleaning_rules.py](../../transformation/cleaning/cleaning_rules.py)

## Correct vs Reject Policy

- **Correctable** (recoverable): units, casing, parseable timestamps, geo wrapping → fix in place.
- **Structural** (unrecoverable): missing keys, unparseable time, out-of-range physical values → reject to quarantine with a machine-readable `reason`.

## Rule Standardization

All Silver transforms call the **same primitives** in `cleaning_rules.py`, so "clean" means the same thing for every entity and the rules are unit-tested once. Spark UDFs wrap these identical functions, eliminating batch/stream logic drift.

## Outlier Detection

Z-score over a trailing window flags anomalous sensor values without dropping them (telemetry anomalies are signal, not noise — they feed the anomaly-detection feature). Hard physical bounds (e.g. lat ∈ [-90, 90]) are rejections, not flags.

## Cross References

- [transformation/cleaning/data-quality-rules.md](../../transformation/cleaning/data-quality-rules.md) · [12-data-quality.md](12-data-quality.md) · [ingestion/09-data-quality.md](../ingestion/09-data-quality.md)

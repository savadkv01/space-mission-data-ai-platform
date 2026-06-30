# Data Quality Rules

> Code: [cleaning_rules.py](cleaning_rules.py) · Spec: [docs/transformation/07-cleaning-framework.md](../../docs/transformation/07-cleaning-framework.md)

Cleaning happens at the **Bronze → Silver boundary**. Bronze stays raw.

| Rule | Primitive | Correct / Reject |
| --- | --- | --- |
| Required key null | `require_fields` | reject `null:<field>` |
| Type coercion | `to_float` | correct |
| Timestamp normalize | `normalize_timestamp` | correct; unparseable → reject |
| Physical range | `in_range` | reject `range:<field>` |
| Statistical outlier | `is_outlier_zscore` (|z|>4) | flag |
| Duplicate | `deduplicate` (latest by event_ts) | dedup |
| Geo normalize | `normalize_position` | correct |
| Clamp | `clamp` | correct |

## Reject reasons (machine-readable)

`null:<field>`, `timestamp:unparseable`, `range:<field>` → written to quarantine with the original payload for reconciliation.

## Standardization

Every Silver transform calls these same primitives, so "clean" is defined once and unit-tested once. Spark UDFs wrap the identical functions → no batch/stream drift.

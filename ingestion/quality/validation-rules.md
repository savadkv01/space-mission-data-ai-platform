# Validation Rules

Code: [validators.py](validators.py), [../common/schemas.py](../common/schemas.py). Narrative: [docs/ingestion/09-data-quality.md](../../docs/ingestion/09-data-quality.md).

| Rule | Description |
| --- | --- |
| Schema | required fields, types, ranges (declared `Schema`/`FieldSpec`) |
| Null checks | required values must be non-null |
| Range | numeric bounds (Kp 0–9, altitude, lat/lon) |
| Timestamp | ISO-8601 parseable; not far-future / implausibly-old |
| Geospatial | lat ∈ [-90,90], lon ∈ [-180,180] |
| Duplicate | checksum seen-in-window (`DuplicateTracker`) |

Runs **after** Bronze landing, **before** promotion to `cleaned`. Returns `ValidationOutcome(valid, errors, rule_hits)`.

# Quarantine Strategy

Code: [quarantine.py](quarantine.py). Narrative: [docs/ingestion/09-data-quality.md](../../docs/ingestion/09-data-quality.md), [docs/ingestion/10-error-handling.md](../../docs/ingestion/10-error-handling.md).

- Invalid records are **never dropped** — routed to the Kafka DLQ (`telemetry.satellite.dlq`) and/or `staging/quarantine/...`.
- Each quarantined message carries `{reasons, record, _quarantined_at}` for triage.
- Records can be inspected, fixed, and **replayed** back into the raw topic.
- Persistent failures stay in the DLQ rather than blocking the live stream.

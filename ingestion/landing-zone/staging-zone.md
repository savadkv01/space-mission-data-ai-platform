# Staging Zone

Narrative: [docs/ingestion/07-landing-zone.md](../../docs/ingestion/07-landing-zone.md).

- Bucket `staging`; transient working area.
- Holds quarantined records (`staging/quarantine/<source>/ingest_date=.../<batch>.jsonl`) and temporary pulls.
- Retention: short (e.g. 7–30 days); quarantine reviewed, fixed, and replayed, then cleared.
- Never a source of truth — Bronze is authoritative.

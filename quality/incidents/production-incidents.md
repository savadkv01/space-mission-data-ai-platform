# Production Incident Scenarios

> Ten realistic data-quality incidents for the Space Mission Data & AI Platform,
> grounded in the actual MVP data sources (FIRMS, Sentinel Hub, GFW, Earthdata,
> Copernicus EMS) and Sim-track feeds. Each entry follows the same structure so
> it doubles as an on-call reference. Operational runbooks:
> [runbooks.md](runbooks.md).

Severity legend: 🔴 Critical · 🟠 High · 🟡 Medium.

---

## INC-01 🔴 Satellite / EO feed delayed (freshness breach)

- **Symptoms:** `dq_freshness_lag_seconds{entity="silver_fire"}` exceeds the 6 h
  SLA; UC-15 dashboard shows no new detections.
- **Root cause:** upstream FIRMS near-real-time processing lag or scheduler miss.
- **Detection:** `FreshnessBreach` alert (Prometheus).
- **Resolution:** verify source availability; re-trigger the ingestion DAG;
  backfill missed window from Bronze; confirm freshness recovers.
- **Preventive action:** freshness SLA alerting + source health check; stagger
  retries with backoff.

---

## INC-02 🔴 NASA / provider API unavailable

- **Symptoms:** connector 5xx/timeout; `http_errors_total` spike; empty batches.
- **Root cause:** provider outage, expired API key, or rate-limit ban.
- **Detection:** ingestion error-rate alert + zero-row volume alert.
- **Resolution:** confirm outage vs auth; rotate key if expired; enable backoff;
  hold pipeline (do **not** publish empty Silver); resume on recovery.
- **Preventive action:** credential expiry monitoring; circuit breaker; cached
  last-good snapshot for non-critical enrichments.

---

## INC-03 🔴 Schema unexpectedly changes

- **Symptoms:** `SchemaChanged` alert; `dq_validation_failures_total{rule="schema"}`
  spike; new/renamed field.
- **Root cause:** provider changed payload (e.g. FIRMS column rename, STAC field).
- **Detection:** schema-registry diff at Bronze.
- **Resolution:** quarantine affected batch; update `Schema` + cleaner mapping;
  re-profile; re-run; certify.
- **Preventive action:** schema-diff gate at Bronze; contract tests against
  sample payloads; version schemas.

---

## INC-04 🟠 Duplicate launch / detection events

- **Symptoms:** `DuplicateSpike`; `dq_duplicate_ratio > 0.05`; inflated counts.
- **Root cause:** overlapping fetch windows or provider re-sends.
- **Detection:** duplicate-ratio alert; unique-key checkpoint at Silver.
- **Resolution:** confirm dedup by natural key (`fire_key`, `launch_id`,
  `vessel_key`); reprocess Silver; verify Gold counts corrected.
- **Preventive action:** idempotent dedup on stable natural keys; watermark
  fetch windows; checksum-based `DuplicateTracker`.

---

## INC-05 🟠 Corrupted Earth-observation files

- **Symptoms:** unparseable JSON/CSV; envelope checksum mismatch; Bronze read fail.
- **Root cause:** truncated download / storage write interrupted.
- **Detection:** file-integrity check at Bronze (checksum vs `_checksum`).
- **Resolution:** quarantine the file; re-fetch from source; validate checksum;
  re-land.
- **Preventive action:** checksum on write + read; atomic writes; retry on
  partial download.

---

## INC-06 🟠 Missing partitions

- **Symptoms:** a date/`geo_key` partition absent; Gold aggregate gap; reconciliation
  count mismatch Bronze→Silver.
- **Root cause:** failed task, skipped schedule, or upstream gap.
- **Detection:** reconciliation job (record counts per partition) + volume alert.
- **Resolution:** identify gap window; backfill from Bronze/source; re-run Silver
  and Gold for the window.
- **Preventive action:** partition-completeness reconciliation; expected-partition
  manifest per day.

---

## INC-07 🟠 Space-weather feed outage (Sim)

- **Symptoms:** `silver_space_weather` stale; `fact_weather_impact` missing days.
- **Root cause:** NOAA SWPC endpoint outage or generator halt.
- **Detection:** freshness alert on `silver_space_weather`.
- **Resolution:** restart generator / retry connector; backfill; recompute
  impact mart.
- **Preventive action:** freshness monitoring; synthetic fallback for the demo
  track.

---

## INC-08 🟠 Time-synchronization issues

- **Symptoms:** non-monotonic `event_ts`; timestamps in the future; late-arrival
  spike.
- **Root cause:** source clock skew, timezone mishandling, or replay out of order.
- **Detection:** timestamp validation rule + `dq_late_arrival_pct` alert.
- **Resolution:** normalize to UTC at Silver; quarantine implausible timestamps;
  reorder by event time.
- **Preventive action:** enforce UTC normalization; future/past bounds in
  validators; watermarking in streaming.

---

## INC-09 🔴 Storage corruption

- **Symptoms:** Parquet read errors; checksum mismatch; MinIO object unreadable.
- **Root cause:** interrupted write, disk issue, or partial multipart upload.
- **Detection:** read failure + integrity check; checkpoint failure downstream.
- **Resolution:** restore from Bronze (immutable raw) by reprocessing; re-write
  affected Silver/Gold objects; verify checksums.
- **Preventive action:** Bronze immutability as source of truth; atomic/verified
  writes; periodic integrity sweep.

---

## INC-10 🟠 Invalid coordinate system / geospatial corruption

- **Symptoms:** lat/lon out of range; `geo_key` mismatch; AOI join returns zero.
- **Root cause:** swapped lat/lon, non-WGS84 input, or bbox parse error.
- **Detection:** geospatial validation rule; AOI-attribution reconciliation.
- **Resolution:** quarantine offending rows; fix normalization/parsing; re-derive
  `geo_key`; re-run AOI marts.
- **Preventive action:** strict lat/lon bounds; `normalize_lon`; bbox 4-part
  parse check; assert WGS84 at source.

---

## Incident summary matrix

| ID | Title | Severity | Primary detector |
|----|-------|:--------:|------------------|
| INC-01 | Feed delayed | 🔴 | FreshnessBreach |
| INC-02 | API unavailable | 🔴 | error-rate / volume |
| INC-03 | Schema change | 🔴 | SchemaChanged |
| INC-04 | Duplicate events | 🟠 | DuplicateSpike |
| INC-05 | Corrupted files | 🟠 | file integrity |
| INC-06 | Missing partitions | 🟠 | reconciliation |
| INC-07 | Weather outage | 🟠 | freshness |
| INC-08 | Time sync | 🟠 | timestamp / late-arrival |
| INC-09 | Storage corruption | 🔴 | integrity / checkpoint |
| INC-10 | Invalid coordinates | 🟠 | geospatial rule |

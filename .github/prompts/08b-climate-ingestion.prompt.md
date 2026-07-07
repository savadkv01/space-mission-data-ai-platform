# Prompt 08b - Climate & Air-Quality Ingestion (Extension, Implementation)

# Enterprise Space Mission Data & AI Platform

> **Phase 8b - Data Ingestion (Climate / Dust / Air-Quality Expansion)**
>
> Read `_shared.prompt.md` first. Extends Phase 8 (`ingestion/`).

---

# Objective

You are acting as:

* Senior Data Engineer
* Data Integration Engineer
* Platform Engineer / SRE for Data Systems

Your task is to **implement the tabular ingestion connectors** for the new atmospheric sources so their data lands in Bronze exactly like the existing sources.

This is an **IMPLEMENTATION phase**: working, tested, runnable code.

---

# Scope Guardrails (NON-NEGOTIABLE)

* Implement ONLY tabular / statistical-API connectors (Strategy A):
  * OpenAQ, TROPOMI (Sentinel Hub Statistical API), MODIS/VIIRS AOD.
* Every connector MUST subclass `ingestion/api/base.py::ApiConnector` and return `(records: list[dict], fmt)` from `fetch_raw(...)`, landing via the existing JSONL Bronze writer (`ingestion/common/minio_io.py`).
* Do NOT add NetCDF/HDF/GeoTIFF binary landing, CAMS/ERA5, or geostationary (deferred — out of scope).
* No new architecture; reuse `HttpClient`, `RateLimiter`, `BronzeEnvelope`, and existing config/settings patterns.
* No secrets in code; use `.env` / `ingestion/config/settings.py`. Fit 16 GB RAM; AOI-bounded requests only.

---

# Context

The existing `SentinelHubStatsConnector` (`ingestion/api/sentinelhub_stats.py`) already proves the pattern: request **server-side aggregated per-AOI statistics** as JSON via evalscripts, land one Bronze record per bucket. TROPOMI reuses this exact OAuth + evalscript mechanism.

---

# Task 1 - OpenAQ Connector

Implement `ingestion/api/openaq.py`:

* Subclass `ApiConnector`, `source_code = "OPENAQ"`.
* `fetch_raw(...)` queries OpenAQ v3 measurements by AOI bbox + pollutant list (PM2.5, PM10, O₃, NO₂, CO, SO₂).
* One record per (station, parameter, timestamp); implement `_event_ts`.
* Handle pagination and rate limits via existing `HttpClient`/`RateLimiter`.
* Mirror the structure of `ingestion/api/nasa_power.py`.

---

# Task 2 - TROPOMI Connector (Sentinel Hub Statistical API)

Implement `ingestion/api/tropomi.py`:

* Subclass `SentinelHubStatsConnector` (inherit OAuth + stats flow).
* Add `EVALSCRIPTS` for TROPOMI collections: NO₂, SO₂, CO, O₃, CH₄, UV Aerosol Index.
* `fetch_raw(...)` returns one Bronze record per (AOI, product, time bucket) with mean/min/max/valid-pixel stats.
* Configurable AOI bbox + datetime range + aggregation interval.

---

# Task 3 - MODIS/VIIRS AOD Connector

Implement `ingestion/api/modis_aod.py`:

* Subclass `ApiConnector`, `source_code = "MODIS_AOD"` (or Sentinel Hub stats collection if cleaner).
* Return AOD (and UV aerosol index if available) per AOI per day as JSON records.
* Include retrieval-quality flags in payload.

---

# Task 4 - Configuration & AOIs

* Add AOI bounding boxes (from Phase 5b) and pollutant/product lists to `ingestion/config/settings.py`.
* Add credentials placeholders to `ingestion/.env.example` (OpenAQ key, reuse Sentinel Hub OAuth).
* Add pre-flight verification entries in `tools/datasource-preflight/` for each new endpoint.

---

# Task 5 - Orchestration Wiring

* Add batch ingestion entrypoints / Airflow DAG tasks for the 3 connectors (daily schedule, retry + backoff), consistent with existing ingestion DAGs.
* Land to Bronze buckets using existing `LandingZoneWriter` and `bronze_key` partitioning.

---

# Task 6 - Tests

* Unit tests with a mocked `HttpClient` (no network) for each connector: correct record shaping, `_event_ts`, format, AOI param handling, pagination.
* Follow existing `ingestion/tests/` conventions and `pytest.ini`.
* Ensure `make test` passes from the ingestion package.

---

# Deliverables

```text
ingestion/api/openaq.py
ingestion/api/tropomi.py
ingestion/api/modis_aod.py
ingestion/config/settings.py          (extend: AOIs, pollutant lists)
ingestion/.env.example                (extend: new creds)
ingestion/tests/test_openaq.py
ingestion/tests/test_tropomi.py
ingestion/tests/test_modis_aod.py
tools/datasource-preflight/           (extend: new endpoint checks)
docs/ingestion/climate-connectors.md  (usage + run instructions)
```

---

# Critical Rules

* Implementation phase: connectors run and tests pass.
* Do NOT design transformations (Phase 9b).
* Open-source only; 16 GB RAM; no secrets in code.

---

# Acceptance Criteria

Complete only if:

* All 3 connectors land valid Bronze records via the existing JSONL path
* Unit tests pass offline (mocked HTTP)
* Config/AOIs/creds externalized; pre-flight checks added
* Orchestration entrypoints wired

---

# Definition of Done

> New atmospheric data lands in Bronze identically to existing sources, ready for Phase 9b transformation, with green tests.

Stop after this phase. Do NOT build transformations.

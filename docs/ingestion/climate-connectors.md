# Climate / Dust / Air-Quality Connectors (Phase 8b)

Tabular / statistical-API connectors that land the atmospheric column (air
quality, trace gases, aerosols) into Bronze **identically to the existing
sources** — one JSONL record per bucket wrapped in the standard
`BronzeEnvelope`. No binary/NetCDF landing; AOI-bounded requests only (16 GB
budget). Design contracts: [docs/data-modeling/climate/](../data-modeling/climate/README.md).

## Connectors

| Source | Connector | Auth | Grain landed | Bronze `_source` |
| --- | --- | --- | --- | --- |
| OpenAQ (ground air quality) | [ingestion/api/openaq.py](../../ingestion/api/openaq.py) | `OPENAQ_API_KEY` | 1 record / (station, parameter, timestamp) | `OPENAQ` |
| Sentinel-5P / TROPOMI (trace gases) | [ingestion/api/gee_s5p.py](../../ingestion/api/gee_s5p.py) | Google Earth Engine service account | 1 record / (AOI, product, day bucket) | `TROPOMI` |
| MODIS / VIIRS AOD | [ingestion/api/gee_aod.py](../../ingestion/api/gee_aod.py) | Google Earth Engine service account | 1 record / (AOI, day bucket) | `MODIS_AOD` |

OpenAQ subclasses the Phase 8 base classes and reuses the resilient
[`HttpClient`](../../ingestion/common/http.py) (retry/backoff + `RateLimiter`).

### Atmospheric backend: Google Earth Engine (free) vs Sentinel Hub

Sentinel-5P (trace gases) and MODIS/VIIRS AOD are sourced from **Google Earth
Engine (GEE)** — free for non-commercial / research use — because their
collections (`sentinel-5p-l2`, MODIS AOD) are **not entitled** on the free /
CDSE Sentinel Hub plan (the commercial Sentinel Hub carries them but is paid
after a 30-day trial). The GEE connectors
([`gee_s5p.py`](../../ingestion/api/gee_s5p.py),
[`gee_aod.py`](../../ingestion/api/gee_aod.py)) extend
[`EarthEngineStatsConnector`](../../ingestion/api/gee.py), which runs one
`reduceRegion` per UTC day over the AOI and emits the **identical
Statistical-API bucket shape** the Silver cleaners already consume — so the
source codes stay `TROPOMI` / `MODIS_AOD` and every Silver / Gold / serving / BI
layer downstream is unchanged.

The original Sentinel-Hub-based connectors
([`tropomi.py`](../../ingestion/api/tropomi.py),
[`modis_aod.py`](../../ingestion/api/modis_aod.py)) are retained for operators
who hold a paid Sentinel Hub subscription; swap the connector class in the DAG /
runner to use them.

## Configuration

AOIs, pollutant lists, and product lists are centralized in
[`ingestion/config/settings.py`](../../ingestion/config/settings.py)
(`settings.climate`):

- **AOIs** — named bounding boxes `[min_lon, min_lat, max_lon, max_lat]` for the
  UAE primary AOIs and the upwind dust-source corridors (from
  [Phase 5b AOI strategy](../source-data-analysis/climate/02-aoi-strategy.md)).
- **`openaq_pollutants`** — `pm25, pm10, o3, no2, co, so2`.
- **`tropomi_products`** — `NO2, SO2, CO, O3, CH4, AER_AI`.

Credentials (no secrets in code — set in `.env` / `infrastructure/env/.env`):

```dotenv
OPENAQ_API_KEY=            # free key: https://docs.openaq.org
# Google Earth Engine (free, non-commercial) — Sentinel-5P + MODIS AOD backend
GEE_PROJECT=              # Google Cloud project with the Earth Engine API enabled
GEE_SERVICE_ACCOUNT=      # service-account email
GEE_KEY_FILE=             # path to the service-account JSON key
# Optional: only needed to fall back to the paid Sentinel Hub backend
SENTINELHUB_CLIENT_ID=
SENTINELHUB_CLIENT_SECRET=
```

> **Enabling GEE (free).** Create a Google Cloud project, enable the *Earth
> Engine API*, register the project for Earth Engine (non-commercial), create a
> service account, grant it the *Earth Engine Resource Viewer* role, and
> download its JSON key. The connectors authenticate with
> `ee.ServiceAccountCredentials` — no interactive login on the runner.

> **AOD collection note.** `GeeAodConnector` defaults to
> `MODIS/061/MCD19A2_GRANULES` band `Optical_Depth_055` (scaled ×0.001 to the
> physical 0–5 range); `COLLECTION` / `BAND` are configurable per account /
> sensor. Sentinel-5P products map to the `COPERNICUS/S5P/OFFL/L3_*`
> collections in `GeeS5pConnector.PRODUCTS`.

## Pre-flight verification

Reachability/credential checks are registered in
[`tools/datasource-preflight/sources.py`](../../tools/datasource-preflight/sources.py):

```bash
cd tools/datasource-preflight
python preflight.py --only openaq tropomi modis gee   # subset
python preflight.py                                    # all sources
```

Missing credentials produce `SKIP` (not `FAIL`), matching the existing tool
behavior.

## Running a connector (batch → Bronze)

Connectors are sink-agnostic; the shared
[`run_connector_to_bronze`](../../ingestion/batch/ingest_task.py) task lands
envelopes via `LandingZoneWriter`:

```python
from ingestion.api.openaq import OpenAqConnector
from ingestion.batch.ingest_task import run_connector_to_bronze

run_connector_to_bronze(OpenAqConnector(), aoi_id="AOI-DXB",
                        date_from="2024-06-01", date_to="2024-06-07")
```

```python
from ingestion.api.gee_s5p import GeeS5pConnector
run_connector_to_bronze(GeeS5pConnector(), aoi_id="AOI-UAE-NAT", product="NO2",
                        datetime_range="2024-06-01T00:00:00Z/2024-06-07T23:59:59Z")
```

```python
from ingestion.api.gee_aod import GeeAodConnector
run_connector_to_bronze(GeeAodConnector(), aoi_id="AOI-DESERT", sensor="MODIS",
                        datetime_range="2024-06-01T00:00:00Z/2024-06-07T23:59:59Z")
```

Objects land under `s3://bronze/<SOURCE>/ingest_date=YYYY-MM-DD/<batch_id>/part-*.jsonl`.

## Orchestration (Airflow, daily)

Daily DAGs (retry + exponential backoff via `_defaults.DEFAULT_ARGS`):

| DAG id | Connector | Tasks |
| --- | --- | --- |
| `ingest_openaq` | OpenAQ | one per urban AOI |
| `ingest_tropomi` | TROPOMI | one per (AOI × product) |
| `ingest_modis_aod` | MODIS/VIIRS AOD | one per AOI (incl. dust corridors) |

Files: [ingestion/batch/dags/](../../ingestion/batch/dags/) —
`openaq_ingest_dag.py`, `tropomi_ingest_dag.py`, `modis_aod_ingest_dag.py`.

## Tests

Offline unit tests (mocked `HttpClient`, no network) cover record shaping,
`_event_ts`, AOI/param handling, unit stamping, and pagination:

```bash
cd ingestion
make test        # or: python -m pytest tests/test_openaq.py tests/test_tropomi.py tests/test_modis_aod.py
```

## Scope

In scope (Strategy A — tabular/statistical): OpenAQ, TROPOMI, MODIS/VIIRS AOD.
Deferred (out of scope, not implemented here): CAMS/ERA5 raw NetCDF, geostationary
SEVIRI/Himawari. Transformations are Phase 9b — this phase only lands raw Bronze.

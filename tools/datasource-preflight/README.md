# Data Source Pre-flight

Verifies that the **MVP data sources** for the Space Mission Data & AI Platform are
reachable and (where credentials apply) that your API keys/accounts work — **before**
building the ingestion layer in Phase 8. It performs a tiny real ingestion for each
source and writes samples to `output/`.

> No platform infrastructure required. Pure Python in a virtual environment.

## What it checks

| Source | MVP role | Prerequisite | Env var(s) |
| --- | --- | --- | --- |
| NASA POWER | Weather context (UC-15/16) | Anonymous | — |
| NASA FIRMS / VIIRS | Active fire (UC-15) | Free API key | `FIRMS_MAP_KEY` |
| Copernicus (Sentinel-1/2) | Optical + SAR imagery | Free account (+token optional) | `CDSE_CLIENT_ID`/`CDSE_CLIENT_SECRET` or `COPERNICUS_USERNAME`/`COPERNICUS_PASSWORD` |
| Sentinel Hub | Index extraction (UC-14/15) | Free account + OAuth client | `SENTINELHUB_CLIENT_ID`/`SENTINELHUB_CLIENT_SECRET` |
| Landsat 8/9 (STAC) | Historical baseline (UC-14) | Anonymous (AWS Open Data) | — |
| NASA Earthdata (CMR) | Catalog/metadata | Free account (token optional) | `EARTHDATA_TOKEN` |
| Copernicus EMS | Flood/damage labels (UC-16/27) | Anonymous (portal) | — |
| Global Fishing Watch | Maritime effort (UC-18) | Free account + token | `GFW_API_TOKEN` |
| NASA api.nasa.gov (APOD) | Key validation (DEMO_KEY ok) | Free API key | `NASA_API_KEY` |
| NOAA SWPC | Space weather (supporting) | Anonymous | — |
| CelesTrak (TLE) | Orbital catalog (supporting) | Anonymous | — |

Anonymous sources work out of the box. Keyed sources are **skipped** (not failed)
until you provide credentials, so you can run this immediately and fill keys in later.

## Where to get the free credentials

| Credential | Sign up |
| --- | --- |
| `FIRMS_MAP_KEY` | https://firms.modaps.eosdis.nasa.gov/api/map_key/ |
| `NASA_API_KEY` | https://api.nasa.gov (or use `DEMO_KEY`) |
| Copernicus (Sentinel) | https://dataspace.copernicus.eu — register, then create an OAuth client in the dashboard |
| Sentinel Hub | https://www.sentinel-hub.com — register, then Dashboard → User settings → OAuth clients |
| `GFW_API_TOKEN` | https://globalfishingwatch.org/our-apis/ — request an API access token |
| `EARTHDATA_TOKEN` | https://urs.earthdata.nasa.gov — Generate Token (optional; CMR search is anonymous) |

## Setup (Windows PowerShell)

```powershell
cd tools\datasource-preflight

# 1. Create and activate a virtual environment
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# 2. Install dependencies
pip install -r requirements.txt

# 3. Add your credentials
Copy-Item .env.example .env
notepad .env      # fill in the keys you have; leave the rest blank
```

> If activation is blocked by execution policy, run once:
> `Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned`

## Run

```powershell
python preflight.py            # run every check
python preflight.py --only firms power copernicus   # run a subset
python preflight.py --list     # list check names
```

Each line reports `PASS` / `FAIL` / `WARN` / `SKIP`:

- **PASS** — reachable and (if creds supplied) authenticated; sample written.
- **FAIL** — reachable but credentials rejected, or a hard error. The run exits non-zero.
- **WARN** — reachable/authenticated but the sample response was unexpected.
- **SKIP** — optional credentials not yet provided; nothing attempted.

Samples land in `output/` (git-ignored) — e.g. `firms_viirs_fires.csv`,
`nasa_power_daily.json`, `copernicus_sentinel2_product.json`.

## Security

- `.env` and `output/` are git-ignored. Never commit real credentials.
- The tool only performs small read-only requests against public/free APIs.

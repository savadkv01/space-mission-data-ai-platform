"""Per-source accessibility checks for the MVP data sources.

Each function performs the lightest possible real request against a source,
optionally writing a tiny ingestion sample to ``output/``. Functions never
raise: any failure is captured in the returned :class:`CheckResult`.

MVP coverage (docs/source-data-analysis/11-mvp-datasets.md):
  NASA FIRMS, VIIRS, Sentinel-2, Sentinel-1, Sentinel Hub, Copernicus EMS,
  Global Fishing Watch, NASA POWER, NASA Earthdata, Landsat 8/9.
Supporting anonymous sources used by the ingestion phase are also probed.
"""

from __future__ import annotations

import requests

from common import (
    FAIL,
    PASS,
    SKIP,
    WARN,
    CheckResult,
    DEFAULT_TIMEOUT,
    env,
    save_json_sample,
    save_sample,
)


def _net_fail(result: CheckResult, exc: Exception) -> CheckResult:
    result.status = FAIL
    result.message = f"network error: {type(exc).__name__}: {exc}"
    return result


# ---------------------------------------------------------------------------
# Anonymous MVP / supporting sources
# ---------------------------------------------------------------------------

def check_nasa_power(session: requests.Session) -> CheckResult:
    """NASA POWER daily point API — anonymous weather context (UC-15/16)."""
    result = CheckResult("NASA POWER", "Environmental", "Anonymous")
    url = "https://power.larc.nasa.gov/api/temporal/daily/point"
    params = {
        "parameters": "T2M",
        "community": "RE",
        "longitude": "55.27",   # Dubai-ish AOI
        "latitude": "25.20",
        "start": "20240101",
        "end": "20240103",
        "format": "JSON",
    }
    try:
        resp = session.get(url, params=params, timeout=DEFAULT_TIMEOUT)
    except requests.RequestException as exc:
        return _net_fail(result, exc)

    if resp.status_code == 200 and "properties" in resp.text:
        data = resp.json()
        result.sample_path = save_json_sample("nasa_power_daily.json", data)
        result.status = PASS
        result.message = "daily T2M point series retrieved"
    else:
        result.status = FAIL
        result.message = f"unexpected response (HTTP {resp.status_code})"
    return result


def check_noaa_swpc(session: requests.Session) -> CheckResult:
    """NOAA SWPC planetary K-index — anonymous space weather feed."""
    result = CheckResult("NOAA SWPC (Kp)", "Space Weather", "Anonymous")
    url = "https://services.swpc.noaa.gov/products/noaa-planetary-k-index.json"
    try:
        resp = session.get(url, timeout=DEFAULT_TIMEOUT)
    except requests.RequestException as exc:
        return _net_fail(result, exc)

    if resp.status_code == 200 and isinstance(resp.json(), list):
        rows = resp.json()
        result.sample_path = save_json_sample("noaa_swpc_kp.json", rows[:5])
        result.status = PASS
        result.message = f"{len(rows)} Kp rows retrieved"
    else:
        result.status = FAIL
        result.message = f"unexpected response (HTTP {resp.status_code})"
    return result


def check_celestrak(session: requests.Session) -> CheckResult:
    """CelesTrak GP/TLE — anonymous orbital catalog (ingestion phase)."""
    result = CheckResult("CelesTrak (TLE)", "Orbital", "Anonymous")
    url = "https://celestrak.org/NORAD/elements/gp.php"
    params = {"GROUP": "stations", "FORMAT": "tle"}
    try:
        resp = session.get(url, params=params, timeout=DEFAULT_TIMEOUT)
    except requests.RequestException as exc:
        return _net_fail(result, exc)

    text = resp.text.strip()
    if resp.status_code == 200 and text and "1 " in text and "2 " in text:
        result.sample_path = save_sample("celestrak_stations.tle", text)
        result.status = PASS
        result.message = f"{len(text.splitlines())} TLE lines retrieved"
    else:
        result.status = FAIL
        result.message = f"no TLE data returned (HTTP {resp.status_code})"
    return result


def check_copernicus_ems(session: requests.Session) -> CheckResult:
    """Copernicus EMS rapid-mapping portal — anonymous reachability (UC-16/27).

    EMS products are downloaded from the mapping portal; there is no simple
    public JSON API, so this confirms the portal is reachable.
    """
    result = CheckResult("Copernicus EMS", "Earth Observation", "Anonymous")
    url = "https://rapidmapping.emergency.copernicus.eu/"
    try:
        resp = session.get(url, timeout=DEFAULT_TIMEOUT)
    except requests.RequestException as exc:
        return _net_fail(result, exc)

    if resp.status_code == 200:
        result.status = PASS
        result.message = "rapid-mapping portal reachable (manual/portal download)"
    else:
        result.status = WARN
        result.message = f"portal returned HTTP {resp.status_code}"
    return result


def check_landsat_stac(session: requests.Session) -> CheckResult:
    """Landsat 8/9 via Earth Search STAC on AWS Open Data — anonymous (UC-14)."""
    result = CheckResult("Landsat 8/9 (STAC)", "Earth Observation", "Anonymous")
    url = "https://earth-search.aws.element84.com/v1/collections/landsat-c2-l2"
    try:
        resp = session.get(url, timeout=DEFAULT_TIMEOUT)
    except requests.RequestException as exc:
        return _net_fail(result, exc)

    if resp.status_code == 200 and "id" in resp.json():
        result.sample_path = save_json_sample("landsat_collection.json", resp.json())
        result.status = PASS
        result.message = "landsat-c2-l2 STAC collection reachable"
    else:
        result.status = FAIL
        result.message = f"collection not reachable (HTTP {resp.status_code})"
    return result


def check_earthdata_cmr(session: requests.Session) -> CheckResult:
    """NASA Earthdata via CMR catalog — anonymous search; token optional."""
    result = CheckResult("NASA Earthdata (CMR)", "Earth Observation", "Free account")
    url = "https://cmr.earthdata.nasa.gov/search/collections.json"
    params = {"keyword": "Sentinel-2", "page_size": "3"}
    headers = {}
    token = env("EARTHDATA_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    try:
        resp = session.get(url, params=params, headers=headers, timeout=DEFAULT_TIMEOUT)
    except requests.RequestException as exc:
        return _net_fail(result, exc)

    if resp.status_code == 200:
        entries = resp.json().get("feed", {}).get("entry", [])
        result.sample_path = save_json_sample("earthdata_cmr_collections.json", entries)
        auth_note = "token validated" if token else "anonymous catalog search"
        result.status = PASS
        result.message = f"{len(entries)} collections found ({auth_note})"
    elif resp.status_code in (401, 403):
        result.status = FAIL
        result.message = "EARTHDATA_TOKEN rejected"
    else:
        result.status = FAIL
        result.message = f"unexpected response (HTTP {resp.status_code})"
    return result


# ---------------------------------------------------------------------------
# API-key MVP / supporting sources
# ---------------------------------------------------------------------------

def check_nasa_apod(session: requests.Session) -> CheckResult:
    """NASA api.nasa.gov (APOD) — validates NASA_API_KEY (DEMO_KEY allowed)."""
    result = CheckResult("NASA api.nasa.gov", "Astronomical", "Free API key")
    key = env("NASA_API_KEY", "DEMO_KEY")
    try:
        resp = session.get(
            "https://api.nasa.gov/planetary/apod",
            params={"api_key": key},
            timeout=DEFAULT_TIMEOUT,
        )
    except requests.RequestException as exc:
        return _net_fail(result, exc)

    if resp.status_code == 200:
        result.sample_path = save_json_sample("nasa_apod.json", resp.json())
        result.status = PASS
        result.message = f"APOD retrieved (key: {'DEMO_KEY' if key == 'DEMO_KEY' else 'custom'})"
    elif resp.status_code in (401, 403, 429):
        result.status = FAIL
        result.message = f"key rejected/limited (HTTP {resp.status_code})"
    else:
        result.status = FAIL
        result.message = f"unexpected response (HTTP {resp.status_code})"
    return result


def check_firms(session: requests.Session) -> CheckResult:
    """NASA FIRMS active fire (also covers VIIRS) — requires FIRMS_MAP_KEY (UC-15)."""
    result = CheckResult("NASA FIRMS / VIIRS", "Earth Observation", "Free API key")
    key = env("FIRMS_MAP_KEY")
    if not key:
        result.status = SKIP
        result.message = "FIRMS_MAP_KEY not set"
        return result

    # 1) Validate the key and quota.
    try:
        status = session.get(
            f"https://firms.modaps.eosdis.nasa.gov/mapserver/mapkey_status/?MAP_KEY={key}",
            timeout=DEFAULT_TIMEOUT,
        )
    except requests.RequestException as exc:
        return _net_fail(result, exc)

    if status.status_code != 200 or "current_transactions" not in status.text:
        result.status = FAIL
        result.message = f"MAP_KEY invalid or status check failed (HTTP {status.status_code})"
        return result

    # 2) Small ingestion: VIIRS S-NPP NRT fires, small bbox, last 1 day.
    area_url = (
        f"https://firms.modaps.eosdis.nasa.gov/api/area/csv/{key}/"
        "VIIRS_SNPP_NRT/-10,-10,10,10/1"
    )
    try:
        area = session.get(area_url, timeout=DEFAULT_TIMEOUT)
    except requests.RequestException as exc:
        return _net_fail(result, exc)

    if area.status_code == 200 and area.text.lower().startswith("latitude"):
        rows = max(len(area.text.strip().splitlines()) - 1, 0)
        result.sample_path = save_sample("firms_viirs_fires.csv", area.text)
        result.status = PASS
        result.message = f"VIIRS fire CSV ingested ({rows} detections)"
    else:
        result.status = WARN
        result.message = "key valid but VIIRS sample empty/unexpected"
    return result


def check_gfw(session: requests.Session) -> CheckResult:
    """Global Fishing Watch API — requires GFW_API_TOKEN (UC-18)."""
    result = CheckResult("Global Fishing Watch", "Maritime", "Free account + token")
    token = env("GFW_API_TOKEN")
    if not token:
        result.status = SKIP
        result.message = "GFW_API_TOKEN not set"
        return result

    url = "https://gateway.api.globalfishingwatch.org/v3/vessels/search"
    params = {
        "query": "Maria",
        "datasets[0]": "public-global-vessel-identity:latest",
        "limit": "1",
    }
    headers = {"Authorization": f"Bearer {token}"}
    try:
        resp = session.get(url, params=params, headers=headers, timeout=DEFAULT_TIMEOUT)
    except requests.RequestException as exc:
        return _net_fail(result, exc)

    if resp.status_code in (401, 403):
        result.status = FAIL
        result.message = "GFW_API_TOKEN rejected"
    elif resp.status_code == 200:
        result.sample_path = save_json_sample("gfw_vessel_search.json", resp.json())
        result.status = PASS
        result.message = "token authenticated; vessel search returned"
    else:
        # Reachable + authenticated (request-shape issues still prove access).
        result.status = WARN
        result.message = f"authenticated but HTTP {resp.status_code} on sample query"
    return result


# ---------------------------------------------------------------------------
# OAuth (account + client) MVP sources
# ---------------------------------------------------------------------------

def check_copernicus_dataspace(session: requests.Session) -> CheckResult:
    """Copernicus Data Space (Sentinel-1/2) — anonymous catalog + optional auth."""
    result = CheckResult("Copernicus (Sentinel-1/2)", "Earth Observation", "Free account + token")

    # 1) Anonymous OData catalog query proves data is reachable.
    odata = (
        "https://catalogue.dataspace.copernicus.eu/odata/v1/Products"
        "?$filter=Collection/Name eq 'SENTINEL-2'&$top=1"
    )
    try:
        cat = session.get(odata, timeout=DEFAULT_TIMEOUT)
    except requests.RequestException as exc:
        return _net_fail(result, exc)

    if cat.status_code != 200 or "value" not in cat.text:
        result.status = FAIL
        result.message = f"catalogue unreachable (HTTP {cat.status_code})"
        return result

    products = cat.json().get("value", [])
    result.sample_path = save_json_sample("copernicus_sentinel2_product.json", products)

    # 2) Optional: confirm credentials by acquiring an access token.
    token_ok, token_msg = _cdse_token(session)
    if token_ok is True:
        result.status = PASS
        result.message = f"catalog reachable; {token_msg}"
    elif token_ok is False:
        result.status = FAIL
        result.message = f"catalog reachable but {token_msg}"
    else:  # None -> no creds supplied
        result.status = PASS
        result.message = "catalog reachable (anonymous); no auth creds supplied"
    return result


def _cdse_token(session: requests.Session):
    """Try to obtain a CDSE access token. Returns (ok|None, message)."""
    token_url = (
        "https://identity.dataspace.copernicus.eu/auth/realms/CDSE/"
        "protocol/openid-connect/token"
    )
    client_id = env("CDSE_CLIENT_ID")
    client_secret = env("CDSE_CLIENT_SECRET")
    username = env("COPERNICUS_USERNAME")
    password = env("COPERNICUS_PASSWORD")

    if client_id and client_secret:
        data = {
            "grant_type": "client_credentials",
            "client_id": client_id,
            "client_secret": client_secret,
        }
    elif username and password:
        data = {
            "grant_type": "password",
            "client_id": "cdse-public",
            "username": username,
            "password": password,
        }
    else:
        return None, "no auth creds supplied"

    try:
        resp = session.post(token_url, data=data, timeout=DEFAULT_TIMEOUT)
    except requests.RequestException as exc:
        return False, f"token request failed: {exc}"

    if resp.status_code == 200 and "access_token" in resp.json():
        return True, "credentials validated (token acquired)"
    return False, f"credentials rejected (HTTP {resp.status_code})"


def check_sentinelhub(session: requests.Session) -> CheckResult:
    """Sentinel Hub — requires OAuth client credentials (UC-14/15)."""
    result = CheckResult("Sentinel Hub", "Earth Observation", "Free account + token")
    client_id = env("SENTINELHUB_CLIENT_ID")
    client_secret = env("SENTINELHUB_CLIENT_SECRET")
    if not (client_id and client_secret):
        result.status = SKIP
        result.message = "SENTINELHUB_CLIENT_ID/SECRET not set"
        return result

    try:
        resp = session.post(
            "https://services.sentinel-hub.com/oauth/token",
            data={
                "grant_type": "client_credentials",
                "client_id": client_id,
                "client_secret": client_secret,
            },
            timeout=DEFAULT_TIMEOUT,
        )
    except requests.RequestException as exc:
        return _net_fail(result, exc)

    if resp.status_code == 200 and "access_token" in resp.json():
        token = resp.json()
        result.sample_path = save_json_sample(
            "sentinelhub_token.json",
            {"token_type": token.get("token_type"), "expires_in": token.get("expires_in")},
        )
        result.status = PASS
        result.message = "OAuth client validated (access token acquired)"
    elif resp.status_code in (400, 401):
        result.status = FAIL
        result.message = "client credentials rejected"
    else:
        result.status = FAIL
        result.message = f"unexpected response (HTTP {resp.status_code})"
    return result


# Ordered registry of all checks the runner executes.
ALL_CHECKS = [
    check_nasa_power,
    check_firms,
    check_copernicus_dataspace,
    check_sentinelhub,
    check_landsat_stac,
    check_earthdata_cmr,
    check_copernicus_ems,
    check_gfw,
    check_nasa_apod,
    check_noaa_swpc,
    check_celestrak,
]

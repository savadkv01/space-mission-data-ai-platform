"""Silver -> Gold transforms (Task 4).

Gold datasets are curated, business-ready aggregates aligned with the Phase 6
Gold model (docs/data-modeling/04-gold-layer.md). Each ``gold_*`` function is a
pure aggregation over Silver rows, returning dashboard-shaped wide tables that
avoid runtime joins.

Gold marts produced here:
1. Satellite Health Analytics  -> ``fact_sat_health`` (1 row / sat / day)
2. Launch Performance Analytics -> ``kpi_launch_monthly`` (1 row / provider / month)
3. Space Weather Impact         -> ``fact_weather_impact`` (1 row / day)
4. Earth Observation Analytics  -> ``kpi_eo_daily`` (1 row / geo_key / day)
5. Maritime Domain Awareness    -> ``fact_vessel_activity`` (1 row / vessel / day)
6. Catalog Quality Analytics    -> ``fact_scene_catalog`` (1 row / scene)
7. Wildfire per-AOI Analytics   -> ``kpi_wildfire_aoi_daily`` (1 row / aoi / day)
8. Flood per-AOI Analytics      -> ``kpi_flood_aoi_daily`` (1 row / aoi / day)
9. AOI Detection Validation     -> ``kpi_aoi_validation`` (1 row / EMS AOI)
"""

from __future__ import annotations

from bisect import bisect_left, bisect_right
from collections import defaultdict
from datetime import date, timedelta
from math import fsum
from typing import Any

from transformation.cleaning.cleaning_rules import median
from transformation.geospatial.spatial_transform import attribute_point, attributed_aoi_keys
from transformation.timeseries.time_series import parse_ts

_HEALTH_WEIGHT = {"NOMINAL": 1.0, "UNKNOWN": 0.5, "ANOMALY": 0.0}


def _day(value: Any) -> str | None:
    ts = parse_ts(value)
    return ts.date().isoformat() if ts else None


def _month(value: Any) -> str | None:
    ts = parse_ts(value)
    return f"{ts.year:04d}-{ts.month:02d}" if ts else None


# --- 1. Satellite Health Analytics -----------------------------------------

def gold_satellite_health(silver_telemetry: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Daily health rollup per satellite.

    health_score = mean(health weight) penalised by anomaly density. Also tracks
    battery voltage drift (max-min) as a coarse degradation signal.
    """
    groups: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for r in silver_telemetry:
        day = _day(r.get("event_ts"))
        sat = r.get("satellite_id")
        if day and sat:
            groups[(sat, day)].append(r)

    out = []
    for (sat, day), rows in sorted(groups.items()):
        n = len(rows)
        health_scores = [_HEALTH_WEIGHT.get(r.get("health", "UNKNOWN"), 0.5) for r in rows]
        anomaly_samples = sum(1 for r in rows if r.get("anomaly_sensor_count", 0) > 0)
        labelled = sum(1 for r in rows if r.get("label_anomaly"))
        voltages = [r["battery_voltage_value"] for r in rows
                    if r.get("battery_voltage_value") is not None]
        v_drift = round(max(voltages) - min(voltages), 4) if voltages else None
        base_score = sum(health_scores) / n if n else 0.0
        anomaly_density = anomaly_samples / n if n else 0.0
        out.append({
            "sat_key": sat,
            "date_key": day,
            "samples": n,
            "health_score": round(base_score * (1 - 0.5 * anomaly_density), 4),
            "anomaly_samples": anomaly_samples,
            "labelled_anomalies": labelled,
            "anomaly_density": round(anomaly_density, 4),
            "battery_voltage_drift": v_drift,
        })
    return out


# --- 2. Launch Performance Analytics ---------------------------------------

def gold_launch_performance(silver_launch: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Monthly launch KPIs per provider.

    Expects Silver launch rows with ``event_ts``, ``provider``, ``success``
    (bool) and optional ``delay_days``. Returns success %, cadence, mean delay.
    """
    groups: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for r in silver_launch:
        month = _month(r.get("event_ts"))
        provider = r.get("provider", "unknown")
        if month:
            groups[(provider, month)].append(r)

    out = []
    for (provider, month), rows in sorted(groups.items()):
        n = len(rows)
        successes = sum(1 for r in rows if r.get("success"))
        delays = [float(r["delay_days"]) for r in rows if r.get("delay_days") is not None]
        out.append({
            "provider_key": provider,
            "month_key": month,
            "launches": n,
            "successes": successes,
            "success_rate": round(successes / n, 4) if n else None,
            "cadence_per_month": n,
            "mean_delay_days": round(sum(delays) / len(delays), 3) if delays else None,
        })
    return out


# --- 3. Space Weather Impact Analytics -------------------------------------

def gold_space_weather_impact(silver_space_weather: list[dict[str, Any]],
                              silver_telemetry: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Daily correlation of geomagnetic activity with satellite anomalies.

    Joins weather and telemetry on calendar day to expose storm-to-anomaly
    relationships (the basis for the space-weather impact KPI).
    """
    weather_by_day: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for w in silver_space_weather:
        day = _day(w.get("event_ts"))
        if day:
            weather_by_day[day].append(w)

    anomalies_by_day: dict[str, int] = defaultdict(int)
    samples_by_day: dict[str, int] = defaultdict(int)
    for t in silver_telemetry:
        day = _day(t.get("event_ts"))
        if not day:
            continue
        samples_by_day[day] += 1
        if t.get("anomaly_sensor_count", 0) > 0 or t.get("label_anomaly"):
            anomalies_by_day[day] += 1

    days = sorted(set(weather_by_day) | set(samples_by_day))
    out = []
    for day in days:
        w = weather_by_day.get(day, [])
        kp_values = [x["kp_index"] for x in w if x.get("kp_index") is not None]
        storm_hours = sum(1 for x in w if x.get("geomagnetic_storm"))
        samples = samples_by_day.get(day, 0)
        anomalies = anomalies_by_day.get(day, 0)
        out.append({
            "date_key": day,
            "max_kp_index": round(max(kp_values), 2) if kp_values else None,
            "mean_kp_index": round(sum(kp_values) / len(kp_values), 2) if kp_values else None,
            "storm_events": storm_hours,
            "telemetry_samples": samples,
            "anomaly_samples": anomalies,
            "anomaly_rate": round(anomalies / samples, 4) if samples else None,
        })
    return out


# --- 4. Earth Observation Analytics ----------------------------------------

def gold_earth_observation(silver_fire: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Daily fire-detection KPIs per grid cell.

    Expects Silver fire rows with ``event_ts``/``acq_date``, ``geo_key`` and
    optional ``frp`` (fire radiative power). Returns counts and intensity stats.
    """
    groups: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for r in silver_fire:
        day = _day(r.get("event_ts") or r.get("acq_date"))
        geo = r.get("geo_key", "unknown")
        if day:
            groups[(geo, day)].append(r)

    out = []
    for (geo, day), rows in sorted(groups.items()):
        frps = [float(r["frp"]) for r in rows if r.get("frp") is not None]
        out.append({
            "geo_key": geo,
            "date_key": day,
            "detections": len(rows),
            "mean_frp": round(fsum(frps) / len(frps), 3) if frps else None,
            "median_frp": median(frps),
            "max_frp": round(max(frps), 3) if frps else None,
        })
    return out


# --- 5. Maritime Domain Awareness ------------------------------------------

def gold_vessel_activity(silver_vessel: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Daily vessel-activity rollup per vessel (``fact_vessel_activity``).

    Expects Silver ``obs_vessel`` rows. Because the GFW identity endpoint ships
    registry metadata rather than per-ping fishing effort, the mart derives what
    is available: transmission count, active span, and a ``suspicious_flag``
    heuristic (missing flag state or missing IMO obscures vessel identity).
    """
    groups: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for r in silver_vessel:
        day = _day(r.get("event_ts"))
        vessel = r.get("vessel_key")
        if day and vessel:
            groups[(vessel, day)].append(r)

    out = []
    for (vessel, day), rows in sorted(groups.items()):
        flags = sorted({r["flag"] for r in rows if r.get("flag")})
        types = sorted({r["vessel_type"] for r in rows if r.get("vessel_type")})
        suspicious = any(not r.get("flag") or not r.get("imo") for r in rows)
        spans = []
        for r in rows:
            first = parse_ts(r.get("first_transmission_ts"))
            last = parse_ts(r.get("last_transmission_ts"))
            if first and last:
                spans.append((last - first).days)
        out.append({
            "vessel_key": vessel,
            "date_key": day,
            "transmissions": len(rows),
            "flag": flags[0] if flags else None,
            "vessel_type": types[0] if types else None,
            "suspicious_flag": suspicious,
            "active_span_days": max(spans) if spans else None,
        })
    return out


# --- 5b. Maritime Activity (GFW 4Wings, AOI-level) ---------------------------

_MARITIME_MEASURE = {"fishing_effort": "hours", "presence": "hours", "sar": "detections"}
#: Trailing days GFW is still classifying / SAR-matching (D-10): rows on or after
#: ``last published day - (N - 1)`` are provisional and excluded from trend KPIs.
MARITIME_PROVISIONAL_DAYS = 5


def gold_maritime_activity(silver_maritime: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Daily maritime activity per AOI (``fact_maritime_activity_daily``).

    GFW 4Wings only returns days with activity, so absence is ambiguous. A
    dataset is ``0`` on a day only if that AOI's pull returned the dataset at all
    and the day is on/before the dataset's latest published date across the
    pull; later days are ``None`` with status ``not_published`` (fishing effort
    lags ~96 h, SAR ~5 days). ``*_vessels`` sums per-flag distinct vessels, so a
    vessel is counted once per day (one flag per vessel). ``is_provisional``
    marks the last ``MARITIME_PROVISIONAL_DAYS`` published days, which GFW
    still revises upward.
    """
    sums: dict[tuple[str, str, str], dict[str, float]] = defaultdict(
        lambda: {"measure": 0.0, "vessels": 0.0, "unmatched": 0.0})
    aoi_datasets: set[tuple[str, str]] = set()
    published: dict[str, str] = {}
    aoi_first: dict[str, str] = {}
    for r in silver_maritime:
        ds, aoi, day = r.get("dataset"), r.get("aoi_id"), r.get("stat_date")
        if ds not in _MARITIME_MEASURE or not aoi or not day:
            continue
        value = r.get(_MARITIME_MEASURE[ds]) or 0.0
        acc = sums[(aoi, day, ds)]
        acc["measure"] += float(value)
        acc["vessels"] += float(r.get("vessel_count") or 0.0)
        if not r.get("ais_matched"):
            acc["unmatched"] += float(value)
        aoi_datasets.add((aoi, ds))
        published[ds] = max(published.get(ds, day), day)
        aoi_first[aoi] = min(aoi_first.get(aoi, day), day)

    last_day = max(published.values(), default=None)
    provisional_from = ((date.fromisoformat(last_day)
                         - timedelta(days=MARITIME_PROVISIONAL_DAYS - 1)).isoformat()
                        if last_day else None)
    out = []
    for aoi, first in sorted(aoi_first.items()):
        day = date.fromisoformat(first)
        while last_day and day.isoformat() <= last_day:
            key = day.isoformat()
            row: dict[str, Any] = {"aoi_key": aoi, "date_key": key,
                                   "is_provisional": key >= provisional_from}
            for ds, prefix in (("fishing_effort", "fishing"), ("presence", "presence"),
                               ("sar", "sar")):
                acc = sums.get((aoi, key, ds))
                measured = (aoi, ds) in aoi_datasets and key <= published.get(ds, "")
                status = "measured" if acc is not None or measured else "not_published"
                total = acc["measure"] if acc else (0.0 if measured else None)
                vessels = acc["vessels"] if acc else (0.0 if measured else None)
                row[f"{prefix}_status"] = status
                if ds == "sar":
                    unmatched = acc["unmatched"] if acc else (0.0 if measured else None)
                    row["sar_detections"] = total
                    row["sar_unmatched_detections"] = unmatched
                    row["sar_dark_fraction"] = (round(unmatched / total, 4)
                                                if total else None)
                else:
                    row[f"{prefix}_hours"] = round(total, 3) if total is not None else None
                    row[f"{prefix}_vessels"] = vessels
            out.append(row)
            day += timedelta(days=1)
    return out


# --- 6. Catalog Quality Analytics ------------------------------------------

def gold_scene_catalog(silver_scene: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Curated per-scene catalog mart (``fact_scene_catalog``).

    Expects Silver ``obs_scene`` rows (1 row / scene). Adds ``is_searchable`` for
    the UC-25 metadata-quality use case: a scene is searchable when it carries a
    grid location, an acquisition time, and a collection.
    """
    latest: dict[str, dict[str, Any]] = {}
    for r in silver_scene:
        key = r.get("scene_key")
        if not key:
            continue
        cur = latest.get(key)
        if cur is None or str(r.get("event_ts", "")) >= str(cur.get("event_ts", "")):
            latest[key] = r

    out = []
    for key, r in sorted(latest.items()):
        is_searchable = bool(r.get("geo_key") and r.get("event_ts") and r.get("collection"))
        out.append({
            "scene_key": key,
            "date_key": _day(r.get("event_ts")),
            "collection": r.get("collection"),
            "provider": r.get("provider"),
            "platform": r.get("platform"),
            "geo_key": r.get("geo_key"),
            "cloud_cover": r.get("cloud_cover"),
            "completeness_score": r.get("completeness_score"),
            "is_searchable": is_searchable,
        })
    return out


# --- 7. Wildfire per-AOI Analytics -----------------------------------------

def region_envelopes(aois: list[dict[str, Any]]) -> dict[str, tuple[float, float, float, float]]:
    """Union ``(min_lon, min_lat, max_lon, max_lat)`` of each region's AOI bboxes."""
    envelopes: dict[str, tuple[float, float, float, float]] = {}
    for aoi in aois:
        region, bbox = aoi.get("region"), aoi.get("bbox")
        if not region or not bbox or len(bbox) != 4:
            continue
        w, s, e, n = (float(v) for v in bbox)
        if region in envelopes:
            pw, ps, pe, pn = envelopes[region]
            w, s, e, n = min(w, pw), min(s, ps), max(e, pe), max(n, pn)
        envelopes[region] = (w, s, e, n)
    return envelopes


def region_for_point(lat: Any, lon: Any,
                     envelopes: dict[str, tuple[float, float, float, float]]) -> str | None:
    """First region (sorted) whose envelope contains the point; ``None`` if outside all."""
    try:
        y, x = float(lat), float(lon)
    except (TypeError, ValueError):
        return None
    for region in sorted(envelopes):
        w, s, e, n = envelopes[region]
        if w <= x <= e and s <= y <= n:
            return region
    return None


#: Persistent heat-source rule (D-03): a 0.01° (~1.1 km) cell with detections on
#: at least ``PERSISTENT_MIN_DAYS`` distinct UTC days within ±``PERSISTENT_WINDOW_DAYS``
#: of a detection marks it a fixed industrial source (gas flare, refinery,
#: platform). Vegetation fires move between cells from day to day; flares do not.
PERSISTENT_CELL_DEG = 0.01
PERSISTENT_MIN_DAYS = 5
PERSISTENT_WINDOW_DAYS = 15
HEAT_SOURCE_VEGETATION = "vegetation_fire"
HEAT_SOURCE_PERSISTENT = "persistent_industrial"


def _heat_cell(lat: Any, lon: Any) -> tuple[int, int] | None:
    try:
        return (round(float(lat) / PERSISTENT_CELL_DEG), round(float(lon) / PERSISTENT_CELL_DEG))
    except (TypeError, ValueError):
        return None


def classify_heat_sources(silver_fire: list[dict[str, Any]]) -> list[str | None]:
    """Heat-source class per Silver fire row (same order); ``None`` without date/position.

    A static-source mask, not a fire-type product: FIRMS NRT carries no ``type``
    field, so persistence is the evidence. ``vegetation_fire`` therefore means
    "not persistent", which includes short-lived industrial events.
    """
    days = [parse_ts(r.get("event_ts")) for r in silver_fire]
    cells = [_heat_cell(r.get("latitude"), r.get("longitude")) for r in silver_fire]
    cell_days: dict[tuple[int, int], set[date]] = defaultdict(set)
    for ts, cell in zip(days, cells):
        if ts is not None and cell is not None:
            cell_days[cell].add(ts.date())
    sorted_days = {cell: sorted(ds) for cell, ds in cell_days.items()}
    window = timedelta(days=PERSISTENT_WINDOW_DAYS)

    out: list[str | None] = []
    for ts, cell in zip(days, cells):
        if ts is None or cell is None:
            out.append(None)
            continue
        ds = sorted_days[cell]
        d = ts.date()
        active = bisect_right(ds, d + window) - bisect_left(ds, d - window)
        out.append(HEAT_SOURCE_PERSISTENT if active >= PERSISTENT_MIN_DAYS
                   else HEAT_SOURCE_VEGETATION)
    return out


def fire_aoi_attribution(silver_fire: list[dict[str, Any]],
                         aois: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Account for every detection once: one reporting AOI plus any overlays.

    ``reporting_aoi_key`` is the single rollup-eligible AOI containing the
    detection (ADR-12); ``aoi_keys`` adds event overlays (EMS footprints) used
    for validation. ``region`` places every detection (matched or not) in an
    analysis region by its regional envelope, so FIRMS freshness can be judged
    per region. ``heat_source_class`` separates persistent industrial heat
    sources from vegetation fires (D-03).
    """
    envelopes = region_envelopes(aois)
    classes = classify_heat_sources(silver_fire)
    out = []
    for r, heat_class in zip(silver_fire, classes):
        day = _day(r.get("event_ts"))
        reporting, overlays = attribute_point(r.get("latitude"), r.get("longitude"), aois)
        keys = ([reporting] if reporting else []) + overlays
        status = "invalid_date" if day is None else "matched" if keys else "unmatched"
        out.append({
            "fire_key": r.get("fire_key"),
            "event_ts": r.get("event_ts"),
            "date_key": day,
            "aoi_keys": keys,
            "reporting_aoi_key": reporting if day else None,
            "match_count": len(keys) if day else 0,
            "match_status": status,
            "match_method": "wgs84_point_in_polygon",
            "region": region_for_point(r.get("latitude"), r.get("longitude"), envelopes),
            "heat_source_class": heat_class,
            "latitude": r.get("latitude"),
            "longitude": r.get("longitude"),
            "frp": r.get("frp"),
            "brightness": r.get("brightness"),
            "brightness_source_field": r.get("brightness_source_field"),
            "brightness_status": r.get("brightness_status"),
            "source": r.get("source"),
            "_ingest_id": r.get("_ingest_id"),
            "_batch_id": r.get("_batch_id"),
        })
    return out


def gold_wildfire_aoi(silver_fire: list[dict[str, Any]],
                      aois: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Daily wildfire KPIs per AOI (``kpi_wildfire_aoi_daily``).

    Point-in-polygon attributes each FIRMS/VIIRS detection to its single
    reporting AOI plus any event overlay containing it, then rolls up
    detections and fire radiative power by AOI and day. Persistent industrial
    heat sources are excluded from ``detections`` / FRP and reported separately
    as ``persistent_detections``; an AOI-day with only persistent sources keeps
    a row with ``detections = 0``.
    """
    fires: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    persistent: dict[tuple[str, str], int] = defaultdict(int)
    for r, attribution in zip(silver_fire, fire_aoi_attribution(silver_fire, aois)):
        day = attribution["date_key"]
        if attribution["match_status"] != "matched":
            continue
        is_persistent = attribution["heat_source_class"] == HEAT_SOURCE_PERSISTENT
        for aoi_key in attribution["aoi_keys"]:
            if is_persistent:
                persistent[(aoi_key, day)] += 1
            else:
                fires[(aoi_key, day)].append(r)

    out = []
    for aoi_key, day in sorted(set(fires) | set(persistent)):
        rows = fires.get((aoi_key, day), [])
        frps = [float(r["frp"]) for r in rows if r.get("frp") is not None]
        out.append({
            "aoi_key": aoi_key,
            "date_key": day,
            "detections": len(rows),
            "persistent_detections": persistent.get((aoi_key, day), 0),
            "mean_frp": round(fsum(frps) / len(frps), 3) if frps else None,
            "max_frp": round(max(frps), 3) if frps else None,
        })
    return out


# --- 8. Flood per-AOI Analytics --------------------------------------------

def _bbox_centroid(bbox: Any) -> tuple[float | None, float | None]:
    """Return ``(lat, lon)`` centroid of a ``minx,miny,maxx,maxy`` bbox string."""
    if not isinstance(bbox, str):
        return None, None
    parts = bbox.split(",")
    if len(parts) != 4:
        return None, None
    try:
        minx, miny, maxx, maxy = (float(p) for p in parts)
    except ValueError:
        return None, None
    return (miny + maxy) / 2.0, (minx + maxx) / 2.0


#: Flood rule on permanent-water-masked NDWI statistics (decision 2026-11-15 /
#: L1): new open water on at least this share of the AOI's valid
#: non-permanent-water pixels. Dry-season baselines measured 2026-11-15 were
#: 0.1-0.3 % (Dubai) and 0.4-0.9 % (Assam), so 2 % is 2-20x the baseline.
FLOOD_NEW_WATER_FRACTION = 0.02
#: Below this valid-pixel share of the AOI box (cloud, partial tile) the new-
#: water fraction rests on too few pixels and the flag is not evaluated.
FLOOD_MIN_VALID_FRACTION = 0.1


def gold_flood_aoi(silver_index: list[dict[str, Any]],
                   aois: list[dict[str, Any]],
                   water_threshold: float = 0.0,
                   new_water_fraction: float = FLOOD_NEW_WATER_FRACTION,
                   ) -> list[dict[str, Any]]:
    """Daily flood KPIs per AOI from NDWI statistics (``kpi_flood_aoi_daily``).

    NDWI index rows are attributed to AOIs via their bbox centroid (one
    reporting AOI plus overlays), then averaged per AOI and day.

    ``flood_flag`` is decided only from statistics with the permanent-water
    mask (``water_mask``: JRC GSW seasonality >= 10 months plus ESA WorldCover
    permanent water): it fires when ``water_fraction`` (share of valid
    non-permanent pixels with NDWI > ``water_threshold``) reaches
    ``new_water_fraction``. Legacy unmasked statistics cannot separate sea or
    lakes from flood water, and days with less than ``FLOOD_MIN_VALID_FRACTION``
    valid pixels rest on too few pixels; both leave the flag ``None``.
    """
    groups: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for r in silver_index:
        if str(r.get("index_name", "")).upper() != "NDWI":
            continue
        day = _day(r.get("event_ts"))
        lat, lon = _bbox_centroid(r.get("bbox"))
        if not day or lat is None:
            continue
        for aoi_key in attributed_aoi_keys(lat, lon, aois):
            groups[(aoi_key, day)].append(r)

    out = []
    for (aoi_key, day), all_rows in sorted(groups.items()):
        masked = [r for r in all_rows if r.get("water_mask")]
        rows = masked or all_rows
        means = [float(r["mean"]) for r in rows if r.get("mean") is not None]
        valid = [float(r["valid_pixel_fraction"]) for r in rows
                 if r.get("valid_pixel_fraction") is not None]
        water = [float(r["water_fraction"]) for r in masked
                 if r.get("water_fraction") is not None]
        permanent = [float(r["permanent_water_fraction"]) for r in masked
                     if r.get("permanent_water_fraction") is not None]
        water_fraction = round(sum(water) / len(water), 4) if water else None
        valid_fraction = round(sum(valid) / len(valid), 4) if valid else None
        decidable = (water_fraction is not None and valid_fraction is not None
                     and valid_fraction >= FLOOD_MIN_VALID_FRACTION)
        out.append({
            "aoi_key": aoi_key,
            "date_key": day,
            "ndwi_mean": round(sum(means) / len(means), 4) if means else None,
            "ndwi_max": round(max(means), 4) if means else None,
            "valid_pixel_fraction": valid_fraction,
            "water_fraction": water_fraction,
            "permanent_water_fraction": (round(sum(permanent) / len(permanent), 4)
                                         if permanent else None),
            "water_mask": masked[0]["water_mask"] if masked else None,
            "flood_flag": water_fraction >= new_water_fraction if decidable else None,
        })
    return out


# --- 9. AOI Detection Validation (Copernicus EMS ground truth) --------------

def gold_aoi_validation(ems_aois: list[dict[str, Any]],
                        wildfire_aoi_rows: list[dict[str, Any]],
                        flood_aoi_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Cross-source corroboration of EMS footprints (``kpi_aoi_validation``).

    Only an EMS activation footprint is ground truth mapped by imagery analysts,
    so only those rows can be ``corroborated`` (D-12): the check asks whether
    *independent* detection sources agree (FIRMS vegetation fires for fire AOIs,
    masked NDWI flood flags for flood AOIs). For other AOIs ``signal_present``
    reports the platform's own signal, which is not corroboration.
    """
    fire_by_aoi: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for r in wildfire_aoi_rows:
        fire_by_aoi[r["aoi_key"]].append(r)
    flood_by_aoi: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for r in flood_aoi_rows:
        flood_by_aoi[r["aoi_key"]].append(r)

    out = []
    for aoi in sorted(ems_aois, key=lambda a: a.get("aoi_key", "")):
        key = aoi.get("aoi_key")
        event_type = aoi.get("event_type", "other")
        if event_type == "fire":
            evidence = fire_by_aoi.get(key, [])
            signal = any((r.get("detections") or 0) > 0 for r in evidence)
        elif event_type == "flood":
            evidence = flood_by_aoi.get(key, [])
            signal = any(r.get("flood_flag") for r in evidence)
        else:
            evidence = []
            signal = False
        is_ems = aoi.get("is_ems_activation", True) is not False
        out.append({
            "aoi_key": key,
            "event_type": event_type,
            "event_date": _day(aoi.get("event_date")),
            "area_km2": aoi.get("area_km2"),
            "evidence_days": len(evidence),
            "is_ems_activation": is_ems,
            "signal_present": signal,
            "corroborated": is_ems and signal,
        })
    return out

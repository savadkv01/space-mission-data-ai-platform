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

from collections import defaultdict
from typing import Any

from transformation.cleaning.cleaning_rules import median
from transformation.geospatial.spatial_transform import assign_aoi
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
            "mean_frp": round(sum(frps) / len(frps), 3) if frps else None,
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

def gold_wildfire_aoi(silver_fire: list[dict[str, Any]],
                      aois: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Daily wildfire KPIs per AOI (``kpi_wildfire_aoi_daily``).

    Point-in-polygon attributes each FIRMS/VIIRS detection to every AOI whose
    footprint contains it, then rolls up detections and fire radiative power by
    AOI and day. A detection may count toward multiple overlapping AOIs.
    """
    groups: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for r in silver_fire:
        day = _day(r.get("event_ts"))
        if not day:
            continue
        for aoi_key in assign_aoi(r.get("latitude"), r.get("longitude"), aois):
            groups[(aoi_key, day)].append(r)

    out = []
    for (aoi_key, day), rows in sorted(groups.items()):
        frps = [float(r["frp"]) for r in rows if r.get("frp") is not None]
        out.append({
            "aoi_key": aoi_key,
            "date_key": day,
            "detections": len(rows),
            "mean_frp": round(sum(frps) / len(frps), 3) if frps else None,
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


def gold_flood_aoi(silver_index: list[dict[str, Any]],
                   aois: list[dict[str, Any]],
                   water_threshold: float = 0.0) -> list[dict[str, Any]]:
    """Daily flood KPIs per AOI from NDWI statistics (``kpi_flood_aoi_daily``).

    NDWI (``> water_threshold`` indicates open water) index rows are attributed
    to AOIs via their bbox centroid, then averaged per AOI and day. ``flood_flag``
    fires when the mean NDWI clears the threshold.
    """
    groups: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for r in silver_index:
        if str(r.get("index_name", "")).upper() != "NDWI":
            continue
        day = _day(r.get("event_ts"))
        lat, lon = _bbox_centroid(r.get("bbox"))
        if not day or lat is None:
            continue
        for aoi_key in assign_aoi(lat, lon, aois):
            groups[(aoi_key, day)].append(r)

    out = []
    for (aoi_key, day), rows in sorted(groups.items()):
        means = [float(r["mean"]) for r in rows if r.get("mean") is not None]
        valid = [float(r["valid_pixel_fraction"]) for r in rows
                 if r.get("valid_pixel_fraction") is not None]
        ndwi_mean = round(sum(means) / len(means), 4) if means else None
        out.append({
            "aoi_key": aoi_key,
            "date_key": day,
            "ndwi_mean": ndwi_mean,
            "ndwi_max": round(max(means), 4) if means else None,
            "valid_pixel_fraction": round(sum(valid) / len(valid), 4) if valid else None,
            "flood_flag": bool(ndwi_mean is not None and ndwi_mean > water_threshold),
        })
    return out


# --- 9. AOI Detection Validation (Copernicus EMS ground truth) --------------

def gold_aoi_validation(ems_aois: list[dict[str, Any]],
                        wildfire_aoi_rows: list[dict[str, Any]],
                        flood_aoi_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Cross-source corroboration of EMS footprints (``kpi_aoi_validation``).

    Each EMS activation AOI is ground truth mapped by imagery analysts. This mart
    checks whether *independent* detection sources agree: FIRMS thermal fires for
    fire AOIs, Sentinel-2 NDWI water for flood AOIs. ``corroborated`` is a recall
    signal for the mapped event.
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
            corroborated = any(r.get("detections", 0) > 0 for r in evidence)
        elif event_type == "flood":
            evidence = flood_by_aoi.get(key, [])
            corroborated = any(r.get("flood_flag") for r in evidence)
        else:
            evidence = []
            corroborated = False
        out.append({
            "aoi_key": key,
            "event_type": event_type,
            "event_date": _day(aoi.get("event_date")),
            "area_km2": aoi.get("area_km2"),
            "evidence_days": len(evidence),
            "corroborated": corroborated,
        })
    return out

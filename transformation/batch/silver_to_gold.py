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
"""

from __future__ import annotations

from collections import defaultdict
from typing import Any

from transformation.cleaning.cleaning_rules import median
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

"""Orbit position simulator.

Propagates real Two-Line Element (TLE) sets with SGP4 to produce realistic
sub-satellite ground tracks (lat/lon/alt). Falls back to a simple analytic
circular-orbit model when ``sgp4`` is not installed, so demos and tests still
run offline. Emits records conforming to ``schemas.ORBIT_POSITION``.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Iterator

# A small built-in TLE seed (ISS + two sats) so the simulator works without a
# live CelesTrak pull. Replace/extend from the CelesTrak connector at runtime.
SEED_TLES: dict[str, tuple[str, str]] = {
    "ISS": (
        "1 25544U 98067A   24001.50000000  .00016717  00000-0  10270-3 0  9000",
        "2 25544  51.6416 247.4627 0006703 130.5360 325.0288 15.49514049000000",
    ),
    "SAT-A": (
        "1 43013U 17073A   24001.50000000  .00000045  00000-0  00000-0 0  9990",
        "2 43013  97.6500 100.0000 0001000  90.0000 270.0000 14.20000000000000",
    ),
}

_EARTH_RADIUS_KM = 6371.0
_MU = 398600.4418  # km^3/s^2


@dataclass
class OrbitSimulator:
    tles: dict[str, tuple[str, str]] = field(default_factory=lambda: dict(SEED_TLES))
    interval_s: float = 10.0

    def __post_init__(self) -> None:
        self._t0 = datetime.now(timezone.utc)
        self._sgp4 = self._try_load_sgp4()

    def _try_load_sgp4(self) -> dict | None:
        try:
            from sgp4.api import Satrec  # type: ignore
        except Exception:  # noqa: BLE001
            return None
        sats = {}
        for sid, (l1, l2) in self.tles.items():
            try:
                sats[sid] = Satrec.twoline2rv(l1, l2)
            except Exception:  # noqa: BLE001 — skip malformed TLE
                continue
        return sats or None

    @staticmethod
    def _eci_to_geodetic(r_km: tuple[float, float, float], when: datetime) -> tuple[float, float, float]:
        x, y, z = r_km
        radius = math.sqrt(x * x + y * y + z * z)
        lat = math.degrees(math.asin(max(-1.0, min(1.0, z / radius))))
        # Approximate GMST to rotate ECI longitude into an Earth-fixed frame.
        gmst = (18.697374558 + 24.06570982441908 * _days_since_j2000(when)) % 24
        lon = (math.degrees(math.atan2(y, x)) - gmst * 15.0 + 180) % 360 - 180
        return lat, lon, radius - _EARTH_RADIUS_KM

    def _position_sgp4(self, sid: str, when: datetime) -> tuple[float, float, float] | None:
        sat = self._sgp4.get(sid) if self._sgp4 else None
        if sat is None:
            return None
        jd, fr = _to_jd(when)
        err, r, _v = sat.sgp4(jd, fr)
        if err != 0:
            return None
        return self._eci_to_geodetic(r, when)

    def _position_analytic(self, sid: str, step: int, when: datetime) -> tuple[float, float, float]:
        # Deterministic circular LEO fallback (~90 min period, 51.6 deg incl).
        alt = 420.0
        period_s = 5560.0
        inc = math.radians(51.6)
        theta = 2 * math.pi * (step * self.interval_s % period_s) / period_s
        offset = (hash(sid) % 360) * math.pi / 180
        lat = math.degrees(math.asin(math.sin(inc) * math.sin(theta + offset)))
        lon = ((math.degrees(theta + offset) + step * 0.25) % 360) - 180
        return lat, lon, alt

    def sample(self, satellite_id: str, step: int) -> dict:
        when = self._t0 + timedelta(seconds=step * self.interval_s)
        pos = self._position_sgp4(satellite_id, when) or self._position_analytic(satellite_id, step, when)
        lat, lon, alt = pos
        return {
            "timestamp": when.isoformat(),
            "satellite_id": satellite_id,
            "latitude": round(lat, 5),
            "longitude": round(lon, 5),
            "altitude_km": round(alt, 3),
            "propagator": "sgp4" if (self._sgp4 and satellite_id in self._sgp4) else "analytic",
        }

    def stream(self, max_records: int | None = None) -> Iterator[dict]:
        step = 0
        produced = 0
        sats = list(self.tles.keys())
        while max_records is None or produced < max_records:
            for sid in sats:
                yield self.sample(sid, step)
                produced += 1
                if max_records is not None and produced >= max_records:
                    return
            step += 1


def _days_since_j2000(when: datetime) -> float:
    j2000 = datetime(2000, 1, 1, 12, tzinfo=timezone.utc)
    return (when - j2000).total_seconds() / 86400.0


def _to_jd(when: datetime) -> tuple[float, float]:
    # Julian date split into integer + fractional day for sgp4.
    days = _days_since_j2000(when) + 2451545.0
    jd = math.floor(days - 0.5) + 0.5
    return jd, days - jd

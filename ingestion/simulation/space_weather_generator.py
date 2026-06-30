"""Synthetic space-weather event generator.

Produces Kp-index and solar-flare events with realistic class distributions so
the ``space.weather.events`` topic and downstream alerting can be exercised
without depending on live NOAA/NASA cadence. Deterministic given ``seed``.
"""

from __future__ import annotations

import random
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Iterator

_FLARE_CLASSES = ["A", "B", "C", "M", "X"]
_FLARE_WEIGHTS = [40, 35, 18, 6, 1]  # X-class is rare


@dataclass
class SpaceWeatherGenerator:
    interval_s: float = 60.0
    seed: int = 7

    def __post_init__(self) -> None:
        self._rng = random.Random(self.seed)
        self._t0 = datetime.now(timezone.utc)

    def sample(self, step: int) -> dict:
        when = self._t0 + timedelta(seconds=step * self.interval_s)
        kp = round(min(9.0, max(0.0, self._rng.gauss(3.0, 1.5))), 1)
        flare = self._rng.choices(_FLARE_CLASSES, weights=_FLARE_WEIGHTS, k=1)[0]
        storm = kp >= 5.0
        return {
            "timestamp": when.isoformat(),
            "event_type": "space_weather",
            "kp_index": kp,
            "flare_class": f"{flare}{self._rng.randint(1, 9)}",
            "geomagnetic_storm": storm,
            "severity": "G1+" if storm else "quiet",
            "source": "synthetic",
        }

    def stream(self, max_records: int | None = None) -> Iterator[dict]:
        step = 0
        produced = 0
        while max_records is None or produced < max_records:
            yield self.sample(step)
            produced += 1
            step += 1
            if max_records is not None and produced >= max_records:
                return

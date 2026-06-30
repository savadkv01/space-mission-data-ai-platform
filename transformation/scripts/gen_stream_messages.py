"""Generate deterministic telemetry NDJSON for the streaming demo.

Two waves are emitted on stdout:
  * Wave 1 - the actual window payload (event-time 12:00:00..12:00:50).
  * Wave 2 - future-dated events (12:05:00) that advance the watermark past the
    first 1-minute window end (12:01:00 + 2 min watermark), forcing append-mode
    output to flush.
"""

import json

LINES = []


def emit(ts: str, sat: str, sensor: str, health: str, anomaly: bool) -> None:
    LINES.append(
        json.dumps(
            {
                "timestamp": ts,
                "satellite_id": sat,
                "sensor_type": sensor,
                "health": health,
                "label_anomaly": anomaly,
            }
        )
    )


# Wave 1: window [2026-06-01T12:00:00, 12:01:00) -- SAT-001 & SAT-002
for sec in range(0, 60, 10):
    ts = f"2026-06-01T12:00:{sec:02d}"
    emit(ts, "SAT-001", "thermal", "NOMINAL", anomaly=(sec == 30))
    emit(ts, "SAT-002", "power", "NOMINAL", anomaly=(sec in (20, 40)))

# Wave 2: future events to advance the watermark beyond the window end.
for sec in range(0, 30, 10):
    ts = f"2026-06-01T12:05:{sec:02d}"
    emit(ts, "SAT-001", "thermal", "NOMINAL", anomaly=False)

print("\n".join(LINES))

from __future__ import annotations

from transformation.cleaning.cleaning_rules import (
    clamp,
    deduplicate,
    in_range,
    is_outlier_zscore,
    normalize_timestamp,
    require_fields,
    to_float,
)


def test_normalize_timestamp_to_utc():
    assert normalize_timestamp("2026-06-01T00:00:00Z").endswith("+00:00")
    assert normalize_timestamp("2026-06-01T02:00:00+02:00").startswith("2026-06-01T00:00:00")
    assert normalize_timestamp("not-a-date") is None
    assert normalize_timestamp(None) is None


def test_to_float_and_range():
    assert to_float("3.5") == 3.5
    assert to_float("x", default=0.0) == 0.0
    assert in_range(50, 0, 90)
    assert not in_range(200, 0, 90)


def test_require_fields_reports_nulls():
    reasons = require_fields({"a": 1, "b": None}, ["a", "b", "c"])
    assert "null:b" in reasons and "null:c" in reasons
    assert "null:a" not in reasons


def test_deduplicate_keeps_latest():
    rows = [
        {"satellite_id": "S1", "event_ts": "2026-06-01T00:00:00+00:00", "v": 1},
        {"satellite_id": "S1", "event_ts": "2026-06-01T00:00:01+00:00", "v": 2},
        {"satellite_id": "S2", "event_ts": "2026-06-01T00:00:00+00:00", "v": 3},
    ]
    out = deduplicate(rows, key_fields=["satellite_id"], order_field="event_ts")
    by_sat = {r["satellite_id"]: r["v"] for r in out}
    assert by_sat == {"S1": 2, "S2": 3}


def test_outlier_and_clamp():
    assert is_outlier_zscore(100, mean=10, std=2, threshold=4)
    assert not is_outlier_zscore(11, mean=10, std=2, threshold=4)
    assert clamp(5, 0, 3) == 3
    assert clamp(-1, 0, 3) == 0

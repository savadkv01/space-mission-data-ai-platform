from __future__ import annotations

from transformation.timeseries.time_series import (
    find_gaps,
    floor_to_window,
    interpolate_linear,
    parse_ts,
    resample_mean,
    rolling_mean,
    window_key,
)


def test_floor_to_window_minute():
    ts = parse_ts("2026-06-01T00:01:37+00:00")
    floored = floor_to_window(ts, 60)
    assert floored.second == 0 and floored.minute == 1


def test_window_key():
    assert window_key("2026-06-01T00:01:37Z", 60).endswith("00:01:00+00:00")
    assert window_key("bad", 60) is None


def test_resample_mean():
    pts = [
        {"timestamp": "2026-06-01T00:00:10Z", "v": 10},
        {"timestamp": "2026-06-01T00:00:50Z", "v": 20},
        {"timestamp": "2026-06-01T00:01:10Z", "v": 30},
    ]
    out = resample_mean(pts, "v", 60)
    assert len(out) == 2
    assert out[0]["mean"] == 15.0


def test_find_gaps():
    pts = [
        {"timestamp": "2026-06-01T00:00:00Z"},
        {"timestamp": "2026-06-01T00:00:01Z"},
        {"timestamp": "2026-06-01T00:00:10Z"},  # gap
    ]
    gaps = find_gaps(pts, expected_interval_s=1.0)
    assert len(gaps) == 1
    assert gaps[0]["missing_estimate"] >= 1


def test_interpolate_and_rolling():
    assert interpolate_linear(0, 0, 10, 100, 5) == 50
    assert rolling_mean([1, 2, 3, 4], 2) == [1.0, 1.5, 2.5, 3.5]

"""Offline unit tests for derived climate indicators (Phase 9b)."""

from __future__ import annotations

from transformation.timeseries.climate_indicators import (
    anomaly,
    day_of_year,
    desertification_proxy,
    linear_trend,
    same_doy_baseline,
    velocity_of_change,
)


def test_day_of_year():
    assert day_of_year("2024-01-01T00:00:00Z") == 1
    assert day_of_year("2024-12-31T00:00:00Z") == 366  # leap year
    assert day_of_year(None) is None


def test_same_doy_baseline_averages_same_day():
    # Non-leap years so 1 June shares the same day-of-year (152) across samples.
    pts = [
        {"event_ts": "2021-06-01T00:00:00Z", "v": 30.0},
        {"event_ts": "2022-06-01T00:00:00Z", "v": 34.0},
        {"event_ts": "2023-06-01T00:00:00Z", "v": 38.0},
    ]
    baseline = same_doy_baseline(pts, "v")
    doy = day_of_year("2023-06-01T00:00:00Z")
    assert baseline[doy] == 34.0


def test_anomaly():
    assert anomaly(38.0, 34.0) == 4.0
    assert anomaly(None, 34.0) is None
    assert anomaly(38.0, None) is None


def test_linear_trend_sign():
    assert linear_trend([1.0, 2.0, 3.0, 4.0]) > 0
    assert linear_trend([4.0, 3.0, 2.0, 1.0]) < 0
    assert linear_trend([2.0, 2.0, 2.0]) == 0.0
    assert linear_trend([1.0]) is None


def test_velocity_of_change():
    assert velocity_of_change([0.5, 0.4, 0.2]) == -0.2
    assert velocity_of_change([0.5]) is None


def test_desertification_proxy_range_and_drivers():
    # Strong degradation: declining NDVI + hot LST anomaly -> high proxy.
    high = desertification_proxy(-0.01, 5.0)
    assert high is not None and 0.0 <= high <= 1.0
    assert high >= 0.9
    # Healthy: rising NDVI, no heat -> low proxy.
    low = desertification_proxy(0.02, 0.0)
    assert low == 0.0
    # One driver is not evidence (D-05): an NDVI decline alone is also a harvest.
    assert desertification_proxy(-0.01, None) is None
    assert desertification_proxy(None, 5.0) is None
    assert desertification_proxy(None, None) is None

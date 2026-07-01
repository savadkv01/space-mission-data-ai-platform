"""Semantic-layer tests (Task 3): metric definitions must be single-sourced."""

from __future__ import annotations

import pytest

from serving.marts import semantic
from serving.marts import serving_marts as sm


def test_metrics_and_dimensions_are_registered():
    assert "total_fire_detections" in semantic.METRICS
    assert semantic.DIMENSIONS["dim_aoi"]["key"] == "aoi_key"


def test_compute_kpis_uses_canonical_reducers():
    wildfire = sm.serve_wildfire_daily([
        {"aoi_key": "A", "date_key": "d", "detections": 10, "mean_frp": 20.0, "max_frp": 50.0},
        {"aoi_key": "B", "date_key": "d", "detections": 6, "mean_frp": 40.0, "max_frp": 15.0},
    ])
    kpis = semantic.compute_kpis(wildfire, ["total_fire_detections", "mean_fire_frp"])
    assert kpis["total_fire_detections"] == 16
    assert kpis["mean_fire_frp"] == 30.0


def test_rate_metric_over_serving_rows():
    scenes = sm.serve_scene_catalog([
        {"scene_key": "S1", "completeness_score": 0.9, "is_searchable": True},
        {"scene_key": "S2", "completeness_score": 0.9, "is_searchable": False},
    ])
    kpis = semantic.compute_kpis(scenes, ["searchable_scene_rate"])
    assert kpis["searchable_scene_rate"] == 0.5


def test_unknown_metric_fails_fast():
    with pytest.raises(KeyError):
        semantic.compute_kpis([], ["does_not_exist"])


def test_empty_rows_return_none_not_crash():
    kpis = semantic.compute_kpis([], ["mean_fire_frp", "flood_day_rate"])
    assert kpis == {"mean_fire_frp": None, "flood_day_rate": None}

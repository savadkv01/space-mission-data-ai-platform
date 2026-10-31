from __future__ import annotations

import math
from collections.abc import Mapping, Sequence
from typing import Any

from feature_store.quality.drift import drift_status, population_stability_index
from feature_store.quality.validation import (
    profile_rows,
    validate_numeric_bounds,
    validate_rows,
)

_NULL_RATE_LIMITS: dict[str, dict[str, float]] = {
    "air_quality_aoi_daily": {
        "pm25_mean": 0.2,
        "pm10_mean": 0.2,
    },
    "dust_aoi_daily": {
        "aod_mean": 0.2,
        "wind_speed_mean": 0.1,
        "wind_dir_dominant": 0.1,
    },
    "climate_indicator_aoi_daily": {
        "lst_c": 0.2,
        "lst_anomaly_c": 0.2,
    },
    "vegetation_health_aoi_daily": {
        "ndvi_mean": 0.2,
    },
}

_NUMERIC_BOUNDS: dict[str, dict[str, tuple[float, float]]] = {
    "air_quality_aoi_daily": {
        "pm25_mean": (0.0, 2000.0),
        "pm25_max": (0.0, 2000.0),
        "pm10_mean": (0.0, 2000.0),
        "pm10_max": (0.0, 2000.0),
        "aqi_pm25": (0.0, 500.0),
        "aqi_pm10": (0.0, 500.0),
        "station_count": (0.0, 100000.0),
    },
    "dust_aoi_daily": {
        "aod_mean": (0.0, 5.0),
        "aod_max": (0.0, 5.0),
        "valid_fraction": (0.0, 1.0),
        "wind_speed_mean": (0.0, 200.0),
        "wind_dir_dominant": (0.0, 360.0),
        "dust_severity_band": (0.0, 4.0),
    },
    "climate_indicator_aoi_daily": {
        "lst_c": (-100.0, 100.0),
        "lst_anomaly_c": (-100.0, 100.0),
        "sst_c": (-5.0, 50.0),
        "sst_anomaly_c": (-100.0, 100.0),
        "ndvi_mean": (-1.0, 1.0),
        "evi_mean": (-1.0, 1.0),
        "ndwi_mean": (-1.0, 1.0),
        "desertification_proxy": (0.0, 1.0),
        "tree_cover_loss_ha": (0.0, 1_000_000.0),
        "lst_anomaly_band": (-1.0, 3.0),
    },
    "vegetation_health_aoi_daily": {
        "ndvi_mean": (-1.0, 1.0),
        "ndvi_max": (-1.0, 1.0),
        "evi_mean": (-1.0, 1.0),
        "valid_pixel_fraction": (0.0, 1.0),
        "ndvi_health_band": (0.0, 4.0),
    },
}
_ENUM_VALUES: dict[str, dict[str, set[str]]] = {
    "air_quality_aoi_daily": {
        "aqi_band": {
            "Good",
            "Moderate",
            "Unhealthy (sensitive)",
            "Unhealthy",
            "Very Unhealthy",
            "Hazardous",
        }
    }
}


def validate_climate_feature_rows(
    view_name: str,
    rows: Sequence[Mapping[str, Any]],
) -> list[str]:
    if view_name not in _NULL_RATE_LIMITS:
        raise ValueError(f"No climate quality contract is defined for {view_name!r}.")
    errors = validate_rows(
        rows,
        entity_field="aoi_key",
        critical_fields=(),
    )
    null_rates = profile_rows(rows, _NULL_RATE_LIMITS[view_name])["null_rates"]
    for field, threshold in _NULL_RATE_LIMITS[view_name].items():
        null_rate = null_rates[field]
        if null_rate is not None and null_rate > threshold:
            errors.append(
                f"{field} null rate {null_rate:.4f} exceeds {threshold:.4f}"
            )
    errors.extend(validate_numeric_bounds(rows, _NUMERIC_BOUNDS[view_name]))
    for field, allowed_values in _ENUM_VALUES.get(view_name, {}).items():
        for index, row in enumerate(rows):
            value = row.get(field)
            if value is not None and value not in allowed_values:
                errors.append(
                    f"{field} at row {index} is not an allowed value: {value!r}"
                )
    return errors


def _skewness(values: Sequence[float]) -> float:
    mean = sum(values) / len(values)
    variance = sum((value - mean) ** 2 for value in values) / len(values)
    if variance == 0:
        return 0.0
    standard_deviation = math.sqrt(variance)
    third_moment = sum((value - mean) ** 3 for value in values) / len(values)
    return third_moment / standard_deviation**3


def climate_distribution_report(
    expected: Mapping[str, Sequence[float]],
    actual: Mapping[str, Sequence[float]],
    *,
    psi_warning_threshold: float = 0.2,
    skew_delta_warning_threshold: float = 1.0,
) -> dict[str, dict[str, float | str]]:
    if expected.keys() != actual.keys():
        raise ValueError("Expected and actual drift samples must have the same features.")
    if skew_delta_warning_threshold <= 0:
        raise ValueError("skew_delta_warning_threshold must be positive.")

    report: dict[str, dict[str, float | str]] = {}
    for feature in sorted(expected):
        baseline = expected[feature]
        current = actual[feature]
        psi = population_stability_index(baseline, current)
        skew_delta = _skewness(current) - _skewness(baseline)
        report[feature] = {
            "psi": psi,
            "psi_status": drift_status(psi, warning_threshold=psi_warning_threshold),
            "skew_delta": skew_delta,
            "skew_status": (
                "warn"
                if abs(skew_delta) >= skew_delta_warning_threshold
                else "pass"
            ),
        }
    return report

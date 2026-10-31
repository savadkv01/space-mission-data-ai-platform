"""Tests for the Phase 10b climate / dust / air-quality quality suites.

Pure-Python, offline. Verifies that each Silver/Gold climate suite passes on
clean sample batches and fails (critically) on injected quality defects that
mirror the documented rules in ``quality/rules/climate/``.

Runnable via ``cd transformation && make test`` (the Phase-10 executable-gates
pattern documented in ``quality/README.md``).
"""

from __future__ import annotations

from transformation.cleaning.validation_framework import run_checkpoint
from transformation.quality.climate_suites import (
    CLIMATE_GOLD_SUITES,
    CLIMATE_SILVER_SUITES,
    gold_air_quality_daily_suite,
    gold_climate_indicator_daily_suite,
    gold_dust_event_daily_suite,
    gold_vegetation_health_daily_suite,
    silver_aerosol_suite,
    silver_air_quality_suite,
    silver_atmos_column_suite,
    silver_wind_suite,
)


# --- fixtures (inline sample rows) ------------------------------------------

def _air_quality_rows():
    return [
        {"air_quality_key": "aq1", "event_ts": "2024-06-01T10:00:00Z",
         "stat_date": "2024-06-01", "location_id": "L1", "pollutant_code": "PM25",
         "value_std": 18.0, "value_raw": 18.0, "unit_raw": "µg/m³",
         "latitude": 25.1, "longitude": 55.2, "geo_key": "g1", "aoi_id": "AOI-DXB",
         "quality_flag": "valid"},
        {"air_quality_key": "aq2", "event_ts": "2024-06-01T11:00:00Z",
         "stat_date": "2024-06-01", "location_id": "L2", "pollutant_code": "PM10",
         "value_std": 42.0, "value_raw": 42.0, "unit_raw": "µg/m³",
         "latitude": 25.2, "longitude": 55.3, "geo_key": "g2", "aoi_id": "AOI-DXB",
         "quality_flag": "valid"},
    ]


def _aerosol_rows():
    return [
        {"aerosol_key": "ae1", "event_ts": "2024-06-01T00:00:00Z",
         "stat_date": "2024-06-01", "aoi_id": "AOI-DXB", "geo_key": "g1",
         "sensor": "MODIS", "aod_550nm": 0.42, "valid_fraction": 0.8,
         "quality_flag": "valid"},
        {"aerosol_key": "ae2", "event_ts": "2024-06-02T00:00:00Z",
         "stat_date": "2024-06-02", "aoi_id": "AOI-DXB", "geo_key": "g1",
         "sensor": "MODIS", "aod_550nm": 1.2, "valid_fraction": 0.6,
         "quality_flag": "valid"},
    ]


def _atmos_column_rows():
    return [
        {"atmos_key": "ac1", "event_ts": "2024-06-01T00:00:00Z",
         "stat_date": "2024-06-01", "aoi_id": "AOI-DXB", "geo_key": "g1",
         "gas_code": "NO2", "mean": 0.00012, "unit_std": "mol/m2",
         "valid_pixel_fraction": 0.7, "quality_flag": "valid"},
        {"atmos_key": "ac2", "event_ts": "2024-06-01T00:00:00Z",
         "stat_date": "2024-06-01", "aoi_id": "AOI-DXB", "geo_key": "g1",
         "gas_code": "AER_AI", "mean": -0.3, "unit_std": "unitless",
         "valid_pixel_fraction": 0.9, "quality_flag": "valid"},
    ]


def _wind_rows():
    return [
        {"wind_key": "w1", "event_ts": "2024-06-01T00:00:00Z",
         "stat_date": "2024-06-01", "aoi_id": "AOI-DXB", "parameter": "WS2M",
         "value_std": 4.5, "unit_std": "m/s", "quality_flag": "valid"},
        {"wind_key": "w2", "event_ts": "2024-06-01T00:00:00Z",
         "stat_date": "2024-06-01", "aoi_id": "AOI-DXB", "parameter": "WD2M",
         "value_std": 275.0, "unit_std": "degree", "quality_flag": "valid"},
    ]


def _air_quality_daily_rows():
    return [
        {"aoi_key": "AOI-DXB", "date_key": "2024-06-01", "pm25_mean": 18.0,
         "pm25_max": 30.0, "pm10_mean": 42.0, "pm10_max": 70.0,
         "no2_column_mean": 0.00012, "so2_column_mean": None,
         "co_column_mean": None, "o3_column_mean": None, "station_count": 2,
         "column_valid_fraction": 0.7, "aqi_pm25": 64, "aqi_pm10": 39,
         "aqi_band": "Moderate", "exceedance_flag": True},
    ]


def _dust_event_daily_rows():
    return [
        {"aoi_key": "AOI-DXB", "date_key": "2024-06-01", "aod_mean": 0.42,
         "aod_max": 0.6, "uv_aerosol_index_mean": 1.1, "wind_speed_mean": 5.0,
         "wind_dir_dominant": "NW", "corridor_aod_max": 0.8, "valid_fraction": 0.8,
         "dust_severity_band": 1, "dust_flag": False, "transport_flag": True},
    ]


def _climate_indicator_daily_rows():
    return [
        {"aoi_key": "AOI-DXB", "date_key": "2024-06-01", "lst_c": 41.0,
         "lst_anomaly_c": 2.5, "sst_c": 30.0, "sst_anomaly_c": 1.0,
         "ndwi_mean": -0.2, "tree_cover_loss_ha": None,
         "desertification_proxy": 0.3, "lst_anomaly_band": 1,
         "warming_flag": False, "desertification_flag": False},
    ]


def _vegetation_health_daily_rows():
    return [
        {"aoi_key": "AOI-DXB", "date_key": "2024-06-01", "ndvi_mean": 0.35,
         "ndvi_max": 0.6, "evi_mean": 0.3, "ndvi_trend_30d": 0.01,
         "valid_pixel_fraction": 0.8, "ndvi_health_band": 2,
         "crop_stress_flag": False},
    ]


# --- Silver: clean batches pass ---------------------------------------------

def test_silver_air_quality_clean_passes():
    result = run_checkpoint(_air_quality_rows(), silver_air_quality_suite(),
                            "obs_air_quality")
    assert result.passed, result.failures


def test_silver_aerosol_clean_passes():
    result = run_checkpoint(_aerosol_rows(), silver_aerosol_suite(), "obs_aerosol")
    assert result.passed, result.failures


def test_silver_atmos_column_clean_passes():
    result = run_checkpoint(_atmos_column_rows(), silver_atmos_column_suite(),
                            "obs_atmos_column")
    assert result.passed, result.failures


def test_silver_wind_clean_passes():
    result = run_checkpoint(_wind_rows(), silver_wind_suite(), "obs_wind")
    assert result.passed, result.failures


# --- Gold: clean batches pass -----------------------------------------------

def test_gold_air_quality_daily_clean_passes():
    result = run_checkpoint(_air_quality_daily_rows(), gold_air_quality_daily_suite(),
                            "fact_air_quality_daily")
    assert result.passed, result.failures


def test_gold_dust_event_daily_clean_passes():
    result = run_checkpoint(_dust_event_daily_rows(), gold_dust_event_daily_suite(),
                            "fact_dust_event_daily")
    assert result.passed, result.failures


def test_gold_climate_indicator_daily_clean_passes():
    result = run_checkpoint(_climate_indicator_daily_rows(),
                            gold_climate_indicator_daily_suite(),
                            "fact_climate_indicator_daily")
    assert result.passed, result.failures


def test_gold_vegetation_health_daily_clean_passes():
    result = run_checkpoint(_vegetation_health_daily_rows(),
                            gold_vegetation_health_daily_suite(),
                            "fact_vegetation_health_daily")
    assert result.passed, result.failures


# --- Registries wired -------------------------------------------------------

def test_registries_expose_all_entities():
    assert set(CLIMATE_SILVER_SUITES) == {
        "obs_air_quality", "obs_aerosol", "obs_atmos_column", "obs_wind"}
    assert set(CLIMATE_GOLD_SUITES) == {
        "fact_air_quality_daily", "fact_dust_event_daily",
        "fact_climate_indicator_daily", "fact_vegetation_health_daily"}


# --- Silver: injected defects fail critically -------------------------------

def test_air_quality_unknown_pollutant_fails():
    rows = _air_quality_rows()
    rows[0]["pollutant_code"] = "XYZ"
    result = run_checkpoint(rows, silver_air_quality_suite(), "obs_air_quality")
    assert not result.passed
    assert any("pollutant_code" in f for f in result.failures)


def test_air_quality_negative_value_fails():
    rows = _air_quality_rows()
    rows[0]["value_std"] = -1.0
    result = run_checkpoint(rows, silver_air_quality_suite(), "obs_air_quality")
    assert not result.passed
    assert any("value_std" in f for f in result.failures)


def test_air_quality_duplicate_key_fails():
    rows = _air_quality_rows()
    rows[1]["air_quality_key"] = rows[0]["air_quality_key"]
    result = run_checkpoint(rows, silver_air_quality_suite(), "obs_air_quality")
    assert not result.passed
    assert any("unique" in f for f in result.failures)


def test_aerosol_aod_out_of_range_fails():
    rows = _aerosol_rows()
    rows[0]["aod_550nm"] = 7.5  # > 5 physical bound
    result = run_checkpoint(rows, silver_aerosol_suite(), "obs_aerosol")
    assert not result.passed
    assert any("aod_550nm" in f for f in result.failures)


def test_aerosol_low_coverage_warns_not_fails():
    rows = _aerosol_rows()
    rows[0]["valid_fraction"] = 0.2  # below 0.5 warn band, above 0 hard band
    result = run_checkpoint(rows, silver_aerosol_suite(), "obs_aerosol")
    assert result.passed  # warn only
    assert any("valid_fraction" in w for w in result.warnings)


def test_atmos_column_unknown_gas_fails():
    rows = _atmos_column_rows()
    rows[0]["gas_code"] = "XX"
    result = run_checkpoint(rows, silver_atmos_column_suite(), "obs_atmos_column")
    assert not result.passed
    assert any("gas_code" in f for f in result.failures)


def test_atmos_column_bad_unit_fails():
    rows = _atmos_column_rows()
    rows[0]["unit_std"] = "kg"
    result = run_checkpoint(rows, silver_atmos_column_suite(), "obs_atmos_column")
    assert not result.passed
    assert any("unit_std" in f for f in result.failures)


def test_atmos_column_negative_gas_mean_fails():
    rows = _atmos_column_rows()
    rows[0]["mean"] = -0.001  # NO2 column density cannot be negative
    result = run_checkpoint(rows, silver_atmos_column_suite(), "obs_atmos_column")
    assert not result.passed
    assert any("column_mean_non_negative" in f for f in result.failures)


def test_wind_invalid_speed_fails():
    rows = _wind_rows()
    rows[0]["value_std"] = 151.0
    result = run_checkpoint(rows, silver_wind_suite(), "obs_wind")
    assert not result.passed
    assert any("wind_measurement" in f for f in result.failures)


# --- Gold: injected defects fail critically ---------------------------------

def test_air_quality_daily_duplicate_grain_fails():
    rows = _air_quality_daily_rows() + _air_quality_daily_rows()
    result = run_checkpoint(rows, gold_air_quality_daily_suite(),
                            "fact_air_quality_daily")
    assert not result.passed
    assert any("unique" in f for f in result.failures)


def test_air_quality_daily_aqi_without_station_fails():
    rows = _air_quality_daily_rows()
    rows[0]["station_count"] = 0  # but aqi_pm25 is populated
    result = run_checkpoint(rows, gold_air_quality_daily_suite(),
                            "fact_air_quality_daily")
    assert not result.passed
    assert any("aqi_requires_station" in f for f in result.failures)


def test_air_quality_daily_bad_band_fails():
    rows = _air_quality_daily_rows()
    rows[0]["aqi_band"] = "Terrible"
    result = run_checkpoint(rows, gold_air_quality_daily_suite(),
                            "fact_air_quality_daily")
    assert not result.passed
    assert any("aqi_band" in f for f in result.failures)


def test_dust_event_daily_aod_out_of_range_fails():
    rows = _dust_event_daily_rows()
    rows[0]["aod_mean"] = 6.0
    result = run_checkpoint(rows, gold_dust_event_daily_suite(),
                            "fact_dust_event_daily")
    assert not result.passed
    assert any("aod_mean" in f for f in result.failures)


def test_dust_event_daily_bad_severity_band_fails():
    rows = _dust_event_daily_rows()
    rows[0]["dust_severity_band"] = 9
    result = run_checkpoint(rows, gold_dust_event_daily_suite(),
                            "fact_dust_event_daily")
    assert not result.passed
    assert any("dust_severity_band" in f for f in result.failures)


def test_climate_indicator_lst_out_of_bounds_fails():
    rows = _climate_indicator_daily_rows()
    rows[0]["lst_c"] = 200.0  # non-physical
    result = run_checkpoint(rows, gold_climate_indicator_daily_suite(),
                            "fact_climate_indicator_daily")
    assert not result.passed
    assert any("lst_c" in f for f in result.failures)


def test_climate_indicator_ndwi_out_of_bounds_fails():
    rows = _climate_indicator_daily_rows()
    rows[0]["ndwi_mean"] = 3.0
    result = run_checkpoint(rows, gold_climate_indicator_daily_suite(),
                            "fact_climate_indicator_daily")
    assert not result.passed
    assert any("ndwi_mean" in f for f in result.failures)


def test_vegetation_health_ndvi_out_of_bounds_fails():
    rows = _vegetation_health_daily_rows()
    rows[0]["ndvi_mean"] = 2.0
    result = run_checkpoint(rows, gold_vegetation_health_daily_suite(),
                            "fact_vegetation_health_daily")
    assert not result.passed
    assert any("ndvi_mean" in f for f in result.failures)


def test_vegetation_health_low_coverage_warns_not_fails():
    rows = _vegetation_health_daily_rows()
    rows[0]["valid_pixel_fraction"] = 0.1  # below 0.3 warn band
    result = run_checkpoint(rows, gold_vegetation_health_daily_suite(),
                            "fact_vegetation_health_daily")
    assert result.passed  # warn only
    assert any("valid_pixel_fraction" in w for w in result.warnings)

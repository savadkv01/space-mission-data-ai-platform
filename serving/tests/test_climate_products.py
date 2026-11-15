"""Climate / dust / air-quality data-product tests (Phase 11b).

These run offline (pure-Python) against the exact Gold field names produced by
``transformation.batch.climate_silver_to_gold`` so the serving contracts stay
pinned to real Gold output. They assert AOI-date grain, KPI/band pass-through,
denormalization (AOI enrichment) and the semantic-registry integration.
"""

from __future__ import annotations

from serving.marts import semantic
from serving.marts.climate import climate_products as cp


AOI_DIM = [{"aoi_key": "EMS-A", "aoi_name": "Attica", "area_km2": 55.0}]


# --- Air Quality ----------------------------------------------------------- #

def test_air_quality_enriches_and_passes_through_aqi():
    aq = [{"aoi_key": "EMS-A", "date_key": "2026-06-01",
           "pm25_mean": 40.0, "pm25_max": 60.0, "pm10_mean": 50.0, "pm10_max": 80.0,
           "no2_column_mean": 1e-4, "station_count": 2,
           "aqi_pm25": 112, "aqi_pm10": 46, "aqi_band": "Unhealthy (sensitive)",
           "exceedance_flag": True}]
    rows = cp.serve_air_quality_daily(aq, AOI_DIM)
    assert len(rows) == 1
    r = rows[0]
    assert r["aoi_name"] == "Attica"
    assert r["area_km2"] == 55.0
    assert r["aqi_band"] == "Unhealthy (sensitive)"
    assert r["exceedance_flag"] is True


def test_air_quality_missing_dim_is_safe():
    rows = cp.serve_air_quality_daily(
        [{"aoi_key": "X", "date_key": "d", "pm25_mean": 5.0}])
    r = rows[0]
    assert r["aoi_name"] is None
    # PM10 unobserved: a low PM2.5 alone cannot rule out a WHO exceedance.
    assert r["exceedance_flag"] is None
    assert r["exceedance_status"] == "inconclusive"
    assert r["pm_coverage"] == "pm25_only"


def test_air_quality_without_surface_pm_is_not_evaluated_not_clean():
    r = cp.serve_air_quality_daily([{"aoi_key": "X", "date_key": "d",
                                     "no2_column_mean": 1e-4, "exceedance_flag": False}])[0]
    assert (r["exceedance_flag"], r["exceedance_status"], r["pm_coverage"]) == (
        None, "not_evaluated", "none")
    assert r["aqi_band"] is None


def test_air_quality_negative_requires_both_pollutants_observed():
    r = cp.serve_air_quality_daily([{"aoi_key": "X", "date_key": "d", "pm25_mean": 5.0,
                                     "pm10_mean": 20.0, "exceedance_flag": False}])[0]
    assert (r["exceedance_flag"], r["exceedance_status"]) == (False, "negative")


# --- Dust Event ------------------------------------------------------------ #

def test_dust_event_labels_and_flags():
    dust = [{"aoi_key": "EMS-A", "date_key": "2026-06-02",
             "aod_mean": 0.8, "aod_max": 1.1, "uv_aerosol_index_mean": 1.4,
             "wind_speed_mean": 5.0, "wind_dir_dominant": "NW",
             "corridor_aod_max": 0.9, "valid_fraction": 0.8,
             "dust_severity_band": 2, "dust_flag": True, "transport_flag": True}]
    r = cp.serve_dust_event_daily(dust, AOI_DIM)[0]
    assert r["dust_severity_label"] == "Dusty"
    assert r["aerosol_load_label"] == "Elevated"
    assert r["aerosol_type"] == "unknown"
    assert r["dust_flag"] is True
    assert r["transport_flag"] is True
    assert r["aoi_name"] == "Attica"


def test_smoke_with_high_aod_is_not_labelled_dust():
    # D-07: crop-burning smoke (MAIAC smoke model) with a high UV index.
    r = cp.serve_dust_event_daily([{
        "aoi_key": "IN-DEL-NCR", "date_key": "d", "aod_mean": 1.6,
        "uv_aerosol_index_mean": 1.9, "smoke_fraction": 0.9, "dust_fraction": 0.0,
        "aerosol_type": "smoke", "dust_severity_band": 3, "dust_flag": False}])[0]
    assert (r["dust_status"], r["dust_flag"]) == ("negative", False)
    assert r["dust_severity_label"] == "No dust event"
    assert (r["aerosol_load_label"], r["aerosol_type"]) == ("High", "smoke")


def test_dust_severity_label_unknown_when_band_missing():
    r = cp.serve_dust_event_daily([{"aoi_key": "A", "date_key": "d"}])[0]
    assert r["dust_severity_label"] == "unknown"
    assert (r["dust_flag"], r["dust_status"]) == (None, "not_evaluated")
    assert (r["transport_flag"], r["transport_status"]) == (None, "not_evaluated")


def test_dust_missing_uv_index_is_inconclusive_unless_aod_rules_it_out():
    high_aod = cp.serve_dust_event_daily([{"aoi_key": "A", "date_key": "d", "aod_mean": 0.8,
                                           "dust_flag": False}])[0]
    low_aod = cp.serve_dust_event_daily([{"aoi_key": "A", "date_key": "d", "aod_mean": 0.2,
                                          "dust_flag": False}])[0]
    assert (high_aod["dust_flag"], high_aod["dust_status"]) == (None, "inconclusive")
    assert (low_aod["dust_flag"], low_aod["dust_status"]) == (False, "negative")


def test_transport_missing_wind_is_inconclusive():
    r = cp.serve_dust_event_daily([{"aoi_key": "A", "date_key": "d", "corridor_aod_max": 0.9,
                                    "transport_flag": False}])[0]
    assert (r["transport_flag"], r["transport_status"]) == (None, "inconclusive")


def test_dust_thresholds_match_gold_rule():
    from transformation.batch import climate_silver_to_gold as gold

    assert cp.DUST_AOD_THRESHOLD == gold.DUST_AOD_THRESHOLD
    assert cp.DUST_UV_AI_THRESHOLD == gold.DUST_UV_AI_THRESHOLD
    assert cp.AEROSOL_TYPE_DOMINANT_SHARE == gold.AEROSOL_TYPE_DOMINANT_SHARE


def test_crop_stress_not_evaluated_outside_cropland():
    r = cp.serve_vegetation_health_daily([{
        "aoi_key": "AOI-DXB", "date_key": "d", "ndvi_mean": -0.07, "ndvi_trend_30d": -0.01,
        "crop_stress_applicable": False, "crop_stress_flag": None}])[0]
    assert (r["crop_stress_status"], r["crop_stress_flag"]) == ("not_evaluated", None)


# --- Climate Indicator ----------------------------------------------------- #

def test_climate_indicator_warming_label_and_flags():
    clim = [{"aoi_key": "EMS-A", "date_key": "2026-06-03",
             "lst_c": 42.0, "lst_anomaly_c": 4.0, "sst_c": None, "sst_anomaly_c": None,
             "ndwi_mean": 0.1, "tree_cover_loss_ha": None,
             "desertification_proxy": 0.6, "lst_anomaly_band": 2,
             "warming_flag": True, "desertification_flag": True}]
    r = cp.serve_climate_indicator_daily(
        clim,
        AOI_DIM,
        [{"aoi_key": "EMS-A", "date_key": "2026-06-03",
          "ndvi_mean": 0.62, "evi_mean": 0.31}],
    )[0]
    assert r["lst_anomaly_label"] == "Hot"
    assert r["ndvi_mean"] == 0.62
    assert r["evi_mean"] == 0.31
    assert r["warming_flag"] is True
    assert r["desertification_flag"] is True


def test_climate_indicator_joins_vegetation_only_on_matching_aoi_date():
    rows = cp.serve_climate_indicator_daily(
        [{"aoi_key": "EMS-A", "date_key": "2026-06-03"}],
        vegetation_rows=[
            {"aoi_key": "EMS-A", "date_key": "2026-06-02",
             "ndvi_mean": 0.9, "evi_mean": 0.8},
            {"aoi_key": "EMS-B", "date_key": "2026-06-03",
             "ndvi_mean": 0.7, "evi_mean": 0.6},
        ],
    )
    assert rows[0]["ndvi_mean"] is None
    assert rows[0]["evi_mean"] is None


def test_climate_indicator_cooler_band():
    r = cp.serve_climate_indicator_daily(
        [{"aoi_key": "A", "date_key": "d", "lst_anomaly_band": -1}])[0]
    assert r["lst_anomaly_label"] == "Cooler"


def test_climate_without_lst_sst_or_proxy_is_not_a_no_warming_finding():
    r = cp.serve_climate_indicator_daily([{"aoi_key": "A", "date_key": "d", "ndwi_mean": 0.1,
                                           "warming_flag": False,
                                           "desertification_flag": False}])[0]
    assert (r["warming_flag"], r["warming_status"]) == (None, "not_evaluated")
    assert (r["desertification_flag"], r["desertification_status"]) == (None, "not_evaluated")


def test_climate_warming_negative_requires_lst_and_sst_anomalies():
    partial, full = cp.serve_climate_indicator_daily([
        {"aoi_key": "A", "date_key": "d1", "lst_anomaly_c": 0.5, "warming_flag": False},
        {"aoi_key": "A", "date_key": "d2", "lst_anomaly_c": 0.5, "sst_anomaly_c": 0.2,
         "warming_flag": False},
    ])
    assert (partial["warming_flag"], partial["warming_status"]) == (None, "inconclusive")
    assert (full["warming_flag"], full["warming_status"]) == (False, "negative")


# --- Vegetation Health ----------------------------------------------------- #

def test_vegetation_health_trend_direction_and_bands():
    veg = [
        {"aoi_key": "EMS-A", "date_key": "d1", "ndvi_mean": 0.6, "ndvi_max": 0.7,
         "evi_mean": 0.5, "ndvi_trend_30d": 0.01, "valid_pixel_fraction": 0.9,
         "ndvi_health_band": 3, "crop_stress_flag": False},
        {"aoi_key": "EMS-A", "date_key": "d2", "ndvi_mean": 0.2, "ndvi_max": 0.3,
         "evi_mean": 0.15, "ndvi_trend_30d": -0.02, "valid_pixel_fraction": 0.8,
         "ndvi_health_band": 1, "crop_stress_flag": True},
    ]
    rows = cp.serve_vegetation_health_daily(veg, AOI_DIM)
    by_day = {r["date_key"]: r for r in rows}
    assert by_day["d1"]["ndvi_trend_dir"] == "improving"
    assert by_day["d1"]["ndvi_health_label"] == "Healthy"
    assert by_day["d2"]["ndvi_trend_dir"] == "declining"
    assert by_day["d2"]["crop_stress_flag"] is True


def test_vegetation_health_unknown_trend_when_missing():
    r = cp.serve_vegetation_health_daily([{"aoi_key": "A", "date_key": "d"}])[0]
    assert r["ndvi_trend_dir"] == "unknown"
    assert (r["crop_stress_flag"], r["crop_stress_status"]) == (None, "not_evaluated")


def test_vegetation_computed_zero_trend_is_flat():
    r = cp.serve_vegetation_health_daily([{"aoi_key": "A", "date_key": "d",
                                           "ndvi_trend_30d": 0.0}])[0]
    assert r["ndvi_trend_dir"] == "flat"


def test_crop_stress_low_ndvi_without_trend_is_inconclusive():
    low, healthy = cp.serve_vegetation_health_daily([
        {"aoi_key": "A", "date_key": "d1", "ndvi_mean": 0.1, "crop_stress_flag": False},
        {"aoi_key": "A", "date_key": "d2", "ndvi_mean": 0.6, "crop_stress_flag": False},
    ])
    assert (low["crop_stress_flag"], low["crop_stress_status"]) == (None, "inconclusive")
    assert (healthy["crop_stress_flag"], healthy["crop_stress_status"]) == (False, "negative")


def test_crop_stress_threshold_matches_gold_rule():
    from transformation.batch.climate_silver_to_gold import crop_stress_flag

    t = cp.CROP_STRESS_NDVI_THRESHOLD
    assert crop_stress_flag(t - 1e-9, -0.01) is True
    assert crop_stress_flag(t, -0.01) is False


# --- Grain + determinism --------------------------------------------------- #

def test_products_are_aoi_date_grained_and_sorted():
    aq = [{"aoi_key": "B", "date_key": "d2"}, {"aoi_key": "A", "date_key": "d1"},
          {"aoi_key": "A", "date_key": "d2"}]
    rows = cp.serve_air_quality_daily(aq)
    keys = [(r["aoi_key"], r["date_key"]) for r in rows]
    assert keys == sorted(keys)
    assert len(keys) == len(set(keys))  # unique AOI-date grain preserved


# --- Semantic-registry integration ----------------------------------------- #

def test_climate_dimensions_and_metrics_registered():
    assert semantic.DIMENSIONS["dim_pollutant"]["key"] == "pollutant_code"
    assert semantic.DIMENSIONS["dim_climate_indicator"]["key"] == "indicator_code"
    for key in ("aqi_exceedance_days", "dust_event_days", "aod_max",
                "lst_anomaly_mean", "warming_days", "desertification_flag_days",
                "ndvi_health_mean", "crop_stress_days"):
        assert key in semantic.METRICS


def test_reference_dimensions_have_expected_species():
    codes = {p["pollutant_code"] for p in semantic.POLLUTANTS}
    assert {"PM25", "PM10", "NO2", "AOD"} <= codes
    indicators = {i["indicator_code"] for i in semantic.CLIMATE_INDICATORS}
    assert {"LST", "NDVI", "DESERT_PROXY"} <= indicators
    pm25 = next(p for p in semantic.POLLUTANTS if p["pollutant_code"] == "PM25")
    assert pm25["aqi_breakpoints"][2]["value_low"] == 35.5
    aod = next(p for p in semantic.POLLUTANTS if p["pollutant_code"] == "AOD")
    assert aod["severity_bands"][2]["label"] == "Elevated"   # aerosol load, not dust (D-07)
    lst_anomaly = next(
        i for i in semantic.CLIMATE_INDICATORS
        if i["indicator_code"] == "LST_ANOM"
    )
    assert lst_anomaly["anomaly_bands"][3]["label"] == "Hot"
    ndvi = next(i for i in semantic.CLIMATE_INDICATORS if i["indicator_code"] == "NDVI")
    assert ndvi["anomaly_bands"][3]["label"] == "Healthy"
    assert all(not indicator["requires_new_ingest"] for indicator in semantic.CLIMATE_INDICATORS)


def test_aqi_semantic_breakpoints_match_gold_calculation():
    from transformation.batch.climate_silver_to_gold import aqi_pm10, aqi_pm25

    calculators = {"PM25": aqi_pm25, "PM10": aqi_pm10}
    for pollutant_code, calculator in calculators.items():
        breakpoints = next(
            pollutant["aqi_breakpoints"]
            for pollutant in semantic.POLLUTANTS
            if pollutant["pollutant_code"] == pollutant_code
        )
        for breakpoint in breakpoints:
            assert calculator(breakpoint["value_low"]) == breakpoint["aqi_low"]
            assert calculator(breakpoint["value_high"]) == breakpoint["aqi_high"]


def test_compute_climate_kpis_over_serving_rows():
    dust = cp.serve_dust_event_daily([
        {"aoi_key": "A", "date_key": "d1", "aod_mean": 0.8, "dust_flag": True},
        {"aoi_key": "A", "date_key": "d2", "aod_mean": 0.3, "dust_flag": False},
    ])
    kpis = semantic.compute_kpis(dust, ["dust_event_days", "aod_max"])
    assert kpis["dust_event_days"] == 1
    assert kpis["aod_max"] == 0.8

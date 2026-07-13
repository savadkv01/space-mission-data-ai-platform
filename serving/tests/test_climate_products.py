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
    assert r["exceedance_flag"] is False


# --- Dust Event ------------------------------------------------------------ #

def test_dust_event_labels_and_flags():
    dust = [{"aoi_key": "EMS-A", "date_key": "2026-06-02",
             "aod_mean": 0.8, "aod_max": 1.1, "uv_aerosol_index_mean": 1.4,
             "wind_speed_mean": 5.0, "wind_dir_dominant": "NW",
             "corridor_aod_max": 0.9, "valid_fraction": 0.8,
             "dust_severity_band": 2, "dust_flag": True, "transport_flag": True}]
    r = cp.serve_dust_event_daily(dust, AOI_DIM)[0]
    assert r["dust_severity_label"] == "Dusty"
    assert r["dust_flag"] is True
    assert r["transport_flag"] is True
    assert r["aoi_name"] == "Attica"


def test_dust_severity_label_unknown_when_band_missing():
    r = cp.serve_dust_event_daily([{"aoi_key": "A", "date_key": "d"}])[0]
    assert r["dust_severity_label"] == "unknown"


# --- Climate Indicator ----------------------------------------------------- #

def test_climate_indicator_warming_label_and_flags():
    clim = [{"aoi_key": "EMS-A", "date_key": "2026-06-03",
             "lst_c": 42.0, "lst_anomaly_c": 4.0, "sst_c": None, "sst_anomaly_c": None,
             "ndwi_mean": 0.1, "tree_cover_loss_ha": None,
             "desertification_proxy": 0.6, "lst_anomaly_band": 2,
             "warming_flag": True, "desertification_flag": True}]
    r = cp.serve_climate_indicator_daily(clim, AOI_DIM)[0]
    assert r["lst_anomaly_label"] == "Hot"
    assert r["warming_flag"] is True
    assert r["desertification_flag"] is True


def test_climate_indicator_cooler_band():
    r = cp.serve_climate_indicator_daily(
        [{"aoi_key": "A", "date_key": "d", "lst_anomaly_band": -1}])[0]
    assert r["lst_anomaly_label"] == "Cooler"


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


def test_vegetation_health_flat_trend_when_missing():
    r = cp.serve_vegetation_health_daily([{"aoi_key": "A", "date_key": "d"}])[0]
    assert r["ndvi_trend_dir"] == "flat"


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


def test_compute_climate_kpis_over_serving_rows():
    dust = cp.serve_dust_event_daily([
        {"aoi_key": "A", "date_key": "d1", "aod_mean": 0.8, "dust_flag": True},
        {"aoi_key": "A", "date_key": "d2", "aod_mean": 0.3, "dust_flag": False},
    ])
    kpis = semantic.compute_kpis(dust, ["dust_event_days", "aod_max"])
    assert kpis["dust_event_days"] == 1
    assert kpis["aod_max"] == 0.8

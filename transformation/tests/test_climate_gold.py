"""Offline unit tests for climate Silver->Gold marts + KPIs (Phase 9b)."""

from __future__ import annotations

from transformation.batch.climate_silver_to_gold import (
    air_quality_exceedance,
    aqi_category,
    aqi_pm25,
    crop_stress_flag,
    dust_flag,
    dust_severity_band,
    gold_air_quality_daily,
    gold_climate_indicator_daily,
    gold_dust_event_daily,
    gold_vegetation_health_daily,
    lst_anomaly_band,
    ndvi_health_band,
    warming_flag,
)
from transformation.batch.gold_lakehouse import build_marts

_DXB_AOI = {
    "aoi_key": "AOI-DXB",
    "bbox": [54.9, 24.8, 55.6, 25.4],
    "polygons": [[[[54.9, 24.8], [55.6, 24.8], [55.6, 25.4],
                   [54.9, 25.4], [54.9, 24.8]]]],
}
_DXB_BBOX = "54.9,24.8,55.6,25.4"  # centroid (25.1, 55.25) inside AOI-DXB


# --- KPI helpers -----------------------------------------------------------

def test_aqi_pm25_bands():
    assert aqi_pm25(6.0) <= 50            # Good
    assert 51 <= aqi_pm25(20.0) <= 100    # Moderate
    assert aqi_category(aqi_pm25(20.0)) == "Moderate"
    assert aqi_pm25(None) is None


def test_dust_severity_band_and_flag():
    assert dust_severity_band(0.1) == 0
    assert dust_severity_band(0.7) == 2
    assert dust_severity_band(1.5) == 3
    assert dust_flag(0.6, 1.2) is True
    assert dust_flag(0.6, 0.5) is False   # UV AI does not corroborate
    assert dust_flag(0.3, 2.0) is False   # AOD too low


def test_lst_and_warming():
    assert lst_anomaly_band(-2.0) == -1
    assert lst_anomaly_band(0.0) == 0
    assert lst_anomaly_band(2.0) == 1
    assert lst_anomaly_band(4.0) == 2
    assert lst_anomaly_band(6.0) == 3
    assert warming_flag(3.5, None) is True
    assert warming_flag(1.0, 2.0) is True   # coastal SST anomaly
    assert warming_flag(1.0, 0.0) is False


def test_ndvi_band_and_crop_stress():
    assert ndvi_health_band(0.05) == 0
    assert ndvi_health_band(0.2) == 1
    assert ndvi_health_band(0.8) == 4
    assert crop_stress_flag(0.2, -0.01) is True
    assert crop_stress_flag(0.2, 0.01) is False   # not declining
    assert crop_stress_flag(0.6, -0.01) is False  # not low


def test_exceedance():
    assert air_quality_exceedance(20.0, None) is True    # PM2.5 > 15
    assert air_quality_exceedance(None, 50.0) is True     # PM10 > 45
    assert air_quality_exceedance(10.0, 40.0) is False


# --- fact_air_quality_daily ------------------------------------------------

def _aq_row(pollutant, value, loc, day="2024-06-01"):
    return {"aoi_id": "AOI-DXB", "stat_date": day, "pollutant_code": pollutant,
            "value_std": value, "location_id": loc, "quality_flag": "valid"}


def test_gold_air_quality_daily_grain_and_aqi():
    surface = [
        _aq_row("PM25", 40.0, "L1"),
        _aq_row("PM25", 20.0, "L2"),
        _aq_row("PM10", 60.0, "L1"),
    ]
    columns = [{"aoi_id": "AOI-DXB", "stat_date": "2024-06-01", "gas_code": "NO2",
                "mean": 0.00012, "valid_pixel_fraction": 0.8, "quality_flag": "valid"}]
    gold = gold_air_quality_daily(surface, columns)
    assert len(gold) == 1
    r = gold[0]
    assert (r["aoi_key"], r["date_key"]) == ("AOI-DXB", "2024-06-01")
    assert r["pm25_mean"] == 30.0
    assert r["station_count"] == 2
    assert r["no2_column_mean"] == 0.00012
    assert r["aqi_pm25"] is not None
    assert r["exceedance_flag"] is True     # pm25 mean 30 > 15


def test_gold_air_quality_no_station_no_aqi():
    # Column-only AOI/day (no OpenAQ stations) -> AQI suppressed.
    columns = [{"aoi_id": "AOI-DXB", "stat_date": "2024-06-02", "gas_code": "O3",
                "mean": 0.1, "valid_pixel_fraction": 0.9, "quality_flag": "valid"}]
    gold = gold_air_quality_daily([], columns)
    assert gold[0]["station_count"] == 0
    assert gold[0]["aqi_pm25"] is None


def test_gold_air_quality_excludes_suspect_units_and_counts_only_valid_pm_stations():
    surface = [
        _aq_row("PM25", 12.0, "valid-station"),
        {**_aq_row("PM25", 900.0, "suspect-station"), "quality_flag": "suspect"},
        {**_aq_row("PM10", 800.0, "suspect-station"), "quality_flag": "suspect"},
    ]

    result = gold_air_quality_daily(surface)[0]

    assert result["pm25_mean"] == 12.0
    assert result["pm10_mean"] is None
    assert result["station_count"] == 1
    assert result["aqi_pm10"] is None


# --- fact_dust_event_daily -------------------------------------------------

def _aer_row(aoi, day, aod, uv=None, vf=0.9):
    return {"aoi_id": aoi, "stat_date": day, "aod_550nm": aod,
            "uv_aerosol_index": uv, "valid_fraction": vf}


def test_gold_dust_event_daily_flag_and_corridor():
    aerosol = [
        _aer_row("AOI-DXB", "2024-06-01", 0.8, uv=1.5),
        _aer_row("AOI-ARABIA", "2024-06-01", 1.2, uv=2.0),  # corridor source
    ]
    gold = gold_dust_event_daily(aerosol)
    dxb = next(r for r in gold if r["aoi_key"] == "AOI-DXB")
    assert dxb["aod_mean"] == 0.8
    assert dxb["dust_severity_band"] == 2
    assert dxb["dust_flag"] is True
    # corridor = strongest AOD over OTHER AOIs same day
    assert dxb["corridor_aod_max"] == 1.2


def test_gold_dust_uv_from_atmos_column():
    aerosol = [_aer_row("AOI-DXB", "2024-06-01", 0.9, uv=None)]
    columns = [{"aoi_id": "AOI-DXB", "stat_date": "2024-06-01", "gas_code": "AER_AI",
                "mean": 1.4}]
    gold = gold_dust_event_daily(aerosol, columns)
    assert gold[0]["uv_aerosol_index_mean"] == 1.4
    assert gold[0]["dust_flag"] is True


def test_gold_dust_uses_wind_for_context_and_transport_flag():
    aerosol = [
        _aer_row("AOI-DXB", "2024-06-01", 0.8, uv=1.5),
        _aer_row("AOI-ARABIA", "2024-06-01", 1.2, uv=2.0),
    ]
    wind = {("AOI-DXB", "2024-06-01"): {
        "wind_speed_mean": 4.5,
        "wind_dir_dominant": 275.0,
    }}

    result = gold_dust_event_daily(aerosol, wind_by_aoi_day=wind)
    dxb = next(row for row in result if row["aoi_key"] == "AOI-DXB")

    assert dxb["wind_speed_mean"] == 4.5
    assert dxb["wind_dir_dominant"] == 275.0
    assert dxb["transport_flag"] is True


def test_gold_lakehouse_wires_silver_power_wind_into_dust_mart():
    marts = build_marts(
        {
            "aerosol": [
                _aer_row("AOI-DXB", "2024-06-01", 0.8, uv=1.5),
                _aer_row("AOI-ARABIA", "2024-06-01", 1.2, uv=2.0),
            ],
            "wind": [
                {"aoi_id": "AOI-DXB", "stat_date": "2024-06-01",
                 "parameter": "WS2M", "value_std": 4.5, "quality_flag": "valid"},
                {"aoi_id": "AOI-DXB", "stat_date": "2024-06-01",
                 "parameter": "WD2M", "value_std": 275.0, "quality_flag": "valid"},
            ],
        },
        [],
    )

    dxb = next(
        row for row in marts["fact_dust_event_daily"] if row["aoi_key"] == "AOI-DXB"
    )
    assert dxb["wind_speed_mean"] == 4.5
    assert dxb["wind_dir_dominant"] == 275.0
    assert dxb["transport_flag"] is True


# --- fact_vegetation_health_daily ------------------------------------------

def _index_row(name, day, mean, vf=0.9):
    return {"index_name": name, "event_ts": f"{day}T00:00:00Z",
            "stat_date": day, "bbox": _DXB_BBOX, "mean": mean,
            "valid_pixel_fraction": vf}


def test_gold_vegetation_health_grain_and_band():
    index_rows = [
        _index_row("NDVI", "2024-06-01", 0.6),
        _index_row("NDVI", "2024-06-02", 0.55),
        _index_row("EVI", "2024-06-01", 0.4),
        _index_row("NDVI", "2024-06-01", 0.6, vf=0.9),  # far AOI ignored below
    ]
    gold = gold_vegetation_health_daily(index_rows, [_DXB_AOI])
    keys = {(r["aoi_key"], r["date_key"]) for r in gold}
    assert len(keys) == len(gold)
    r0 = next(r for r in gold if r["date_key"] == "2024-06-01")
    assert r0["aoi_key"] == "AOI-DXB"
    assert r0["ndvi_mean"] == 0.6
    assert r0["ndvi_health_band"] == 3   # Healthy [0.5,0.7)
    assert r0["evi_mean"] == 0.4
    # second day has a downward NDVI trend
    r1 = next(r for r in gold if r["date_key"] == "2024-06-02")
    assert r1["ndvi_trend_30d"] < 0


def test_gold_vegetation_crop_stress():
    rows = [
        _index_row("NDVI", "2024-06-01", 0.25),
        _index_row("NDVI", "2024-06-02", 0.20),
    ]
    gold = gold_vegetation_health_daily(rows, [_DXB_AOI])
    r1 = next(r for r in gold if r["date_key"] == "2024-06-02")
    assert r1["crop_stress_flag"] is True   # low NDVI + declining


# --- fact_climate_indicator_daily ------------------------------------------

def test_gold_climate_indicator_ndwi_and_grain():
    rows = [
        _index_row("NDWI", "2024-06-01", 0.3),
        _index_row("NDVI", "2024-06-01", 0.5),
    ]
    gold = gold_climate_indicator_daily(rows, [_DXB_AOI])
    assert len(gold) == 1
    r = gold[0]
    assert r["aoi_key"] == "AOI-DXB"
    assert r["ndwi_mean"] == 0.3
    # No LST/SST ingested -> anomalies null, flags false.
    assert r["lst_c"] is None
    assert r["warming_flag"] is False

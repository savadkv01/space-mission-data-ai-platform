"""Offline unit tests for climate Bronze->Silver cleaning (Phase 9b)."""

from __future__ import annotations

from transformation.batch.climate_bronze_to_silver import (
    silver_aerosol,
    silver_air_quality,
    silver_atmos_column,
    silver_wind,
)
from transformation.cleaning.climate.units import (
    canonical_pollutant_code,
    standardize_pollutant_value,
)

_DXB_AOI = {
    "aoi_key": "AOI-DXB",
    "bbox": [54.9, 24.8, 55.6, 25.4],
    "polygons": [[[[54.9, 24.8], [55.6, 24.8], [55.6, 25.4],
                   [54.9, 25.4], [54.9, 24.8]]]],
}


def _aq(param, value, unit, ts, lat=25.1, lon=55.2, loc=123):
    return {
        "location": "Dubai-1", "locationId": loc, "sensorsId": 1,
        "parameter": param, "value": value, "unit": unit,
        "date": {"utc": ts}, "coordinates": {"latitude": lat, "longitude": lon},
        "aoi_id": "AOI-DXB", "_source": "OPENAQ", "_event_ts": ts,
        "_ingest_id": "i1", "_batch_id": "b1",
    }


def _bucket(mean, product, source, aoi="AOI-UAE-NAT",
            bbox=(51.0, 22.5, 56.5, 26.2), sample=90, nodata=10, **extra):
    rec = {
        "interval": {"from": "2024-06-01T00:00:00Z", "to": "2024-06-02T00:00:00Z"},
        "outputs": {"index": {"bands": {"B0": {"stats": {
            "mean": mean, "min": mean, "max": mean, "stDev": 0.1,
            "sampleCount": sample, "noDataCount": nodata}}}}},
        "product": product, "aoi_id": aoi, "bbox": list(bbox),
        "_source": source, "_ingest_id": "i1", "_batch_id": "b1",
    }
    rec.update(extra)
    return rec


# --- units -----------------------------------------------------------------

def test_canonical_pollutant_code_maps_aliases():
    assert canonical_pollutant_code("pm25") == "PM25"
    assert canonical_pollutant_code("PM2.5") == "PM25"
    assert canonical_pollutant_code("no2") == "NO2"
    assert canonical_pollutant_code("unknownium") is None


def test_particulate_passthrough_ugm3():
    v, flag = standardize_pollutant_value("PM25", 40.0, "µg/m³")
    assert v == 40.0 and flag == "valid"


def test_no2_ppb_to_ugm3_conversion():
    # 20 ppb NO2 * 46.0055 / 24.45 ~= 37.63 µg/m³
    v, flag = standardize_pollutant_value("NO2", 20.0, "ppb")
    assert flag == "valid"
    assert abs(v - 37.63) < 0.1


def test_co_ppm_to_mgm3_conversion():
    # 1 ppm CO * 28.01 / 24.45 = 1.1456 mg/m³
    v, flag = standardize_pollutant_value("CO", 1.0, "ppm")
    assert flag == "valid"
    assert abs(v - 1.1456) < 0.01


def test_unconvertible_unit_flagged_suspect():
    v, flag = standardize_pollutant_value("O3", 5.0, "DU")
    assert flag == "suspect" and v == 5.0


# --- obs_air_quality -------------------------------------------------------

def test_silver_air_quality_conforms_and_keys():
    rows = silver_air_quality([_aq("pm25", 40.0, "µg/m³", "2024-06-01T00:00:00Z")],
                              [_DXB_AOI]).rows
    assert len(rows) == 1
    r = rows[0]
    assert r["pollutant_code"] == "PM25"
    assert r["value_std"] == 40.0
    assert r["stat_date"] == "2024-06-01"
    assert r["aoi_id"] == "AOI-DXB"  # point-in-polygon tag
    assert r["quality_flag"] == "valid"


def test_silver_air_quality_rejects_unknown_pollutant():
    result = silver_air_quality([_aq("radon", 1.0, "µg/m³", "2024-06-01T00:00:00Z")])
    assert not result.rows
    assert "unknown:pollutant" in result.quarantine[0]["_reasons"]


def test_silver_air_quality_rejects_negative_value():
    result = silver_air_quality([_aq("pm10", -3.0, "µg/m³", "2024-06-01T00:00:00Z")])
    assert not result.rows
    assert "range:value" in result.quarantine[0]["_reasons"]


def test_silver_air_quality_dedup_keeps_latest():
    a = _aq("pm25", 10.0, "µg/m³", "2024-06-01T00:00:00Z")
    b = _aq("pm25", 99.0, "µg/m³", "2024-06-01T00:00:00Z")  # same key
    rows = silver_air_quality([a, b]).rows
    assert len(rows) == 1


def test_silver_air_quality_outside_aoi_keeps_bronze_fallback():
    rec = _aq("pm25", 12.0, "µg/m³", "2024-06-01T00:00:00Z", lat=0.0, lon=0.0)
    rows = silver_air_quality([rec], [_DXB_AOI]).rows
    assert rows[0]["aoi_id"] == "AOI-DXB"  # fallback to Bronze-stamped request AOI


# --- obs_aerosol -----------------------------------------------------------

def test_silver_aerosol_conforms():
    rows = silver_aerosol([_bucket(0.8, "AOD", "MODIS_AOD", sensor="MODIS")]).rows
    assert len(rows) == 1
    r = rows[0]
    assert r["aod_550nm"] == 0.8
    assert r["sensor"] == "MODIS"
    assert r["valid_fraction"] == 0.9
    assert r["quality_flag"] == "valid"


def test_silver_aerosol_rejects_out_of_range_aod():
    result = silver_aerosol([_bucket(7.0, "AOD", "MODIS_AOD", sensor="MODIS")])
    assert not result.rows
    assert "range:aod" in result.quarantine[0]["_reasons"]


def test_silver_aerosol_low_coverage_flagged_suspect():
    rows = silver_aerosol([_bucket(0.6, "AOD", "MODIS_AOD", sensor="VIIRS",
                                   sample=10, nodata=90)]).rows
    assert rows[0]["quality_flag"] == "suspect"


# --- obs_atmos_column ------------------------------------------------------

def test_silver_atmos_column_conforms():
    rows = silver_atmos_column([_bucket(0.00012, "NO2", "TROPOMI")]).rows
    assert len(rows) == 1
    r = rows[0]
    assert r["gas_code"] == "NO2"
    assert r["unit_std"] == "mol/m2"
    assert r["quality_flag"] == "valid"


def test_silver_atmos_column_low_coverage_flag():
    rows = silver_atmos_column([_bucket(0.0001, "SO2", "TROPOMI",
                                        sample=10, nodata=90)]).rows
    assert rows[0]["quality_flag"] == "low_coverage"


def test_silver_atmos_column_rejects_unknown_gas():
    result = silver_atmos_column([_bucket(0.1, "XYZ", "TROPOMI")])
    assert not result.rows
    assert "unknown:gas" in result.quarantine[0]["_reasons"]


def test_silver_wind_conforms_power_speed_and_direction():
    result = silver_wind([
        {"date": "20240601", "parameter": "WS2M", "value": 4.5, "aoi_id": "AOI-DXB",
         "latitude": 25.1, "longitude": 55.2, "_ingest_id": "speed"},
        {"date": "20240601", "parameter": "WD2M", "value": 275.0, "aoi_id": "AOI-DXB",
         "latitude": 25.1, "longitude": 55.2, "_ingest_id": "direction"},
        {"date": "20240601", "parameter": "T2M", "value": 35.0, "aoi_id": "AOI-DXB"},
        {"date": "20240601", "parameter": "WD2M", "value": -999, "aoi_id": "AOI-DXB"},
        {"date": "20240601", "parameter": "WS2M", "value": 151, "aoi_id": "AOI-DXB"},
    ])

    by_parameter = {row["parameter"]: row for row in result.rows}
    assert by_parameter["WS2M"]["value_std"] == 4.5
    assert by_parameter["WS2M"]["unit_std"] == "m/s"
    assert by_parameter["WD2M"]["value_std"] == 275.0
    assert by_parameter["WD2M"]["unit_std"] == "degree"
    assert len(result.quarantine) == 2
    reasons = [reason for row in result.quarantine for reason in row["_reasons"]]
    assert "range:wind_direction" in reasons
    assert "range:wind_speed" in reasons

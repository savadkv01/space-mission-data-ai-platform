"""Earth-observation quality suites (Phase 10 — Data Quality Framework).

Declarative quality-gate suites for the six MVP Earth-observation use cases,
built on the dependency-free expectation framework in
``transformation.cleaning.validation_framework`` (a laptop-friendly analogue of
Great Expectations). Each ``*_suite`` returns a list of ``Expectation`` objects;
run them with ``run_checkpoint`` to gate a Silver or Gold batch.

Field names mirror the actual Silver/Gold outputs produced by
``transformation.batch.bronze_to_silver`` and ``transformation.batch.silver_to_gold``.

Severity model: ``critical`` expectations fail (hold) a batch; ``warn``
expectations log a signal but allow promotion.
"""

from __future__ import annotations

from typing import Any, Callable

from transformation.cleaning.validation_framework import (
    Expectation,
    expect_not_null,
    expect_row_count_min,
    expect_unique,
    expect_value_in_range,
)

# A large finite upper bound for "non-negative" numeric checks.
_MAX = 1e12


def expect_predicate(name: str, predicate: Callable[[list[dict[str, Any]]], bool],
                     severity: str = "critical", description: str = "") -> Expectation:
    """Wrap an arbitrary batch-level predicate as an ``Expectation``."""
    return Expectation(name=name, predicate=predicate, severity=severity,
                       description=description)


def expect_referential_integrity(field: str, valid_keys: set[str],
                                 severity: str = "critical") -> Expectation:
    """Every non-null ``field`` value must exist in ``valid_keys``."""
    def _check(rows: list[dict[str, Any]]) -> bool:
        return all(r.get(field) in valid_keys for r in rows if r.get(field) is not None)

    return Expectation(
        name=f"referential_integrity:{field}",
        predicate=_check,
        severity=severity,
        description=f"{field} references an existing key.",
    )


# --- Silver suites ----------------------------------------------------------

def silver_fire_suite() -> list[Expectation]:
    """UC-15 wildfire — ``silver_fire`` conformance & validity."""
    return [
        expect_row_count_min(1),
        expect_not_null("fire_key"),
        expect_not_null("event_ts"),
        expect_not_null("latitude"),
        expect_not_null("longitude"),
        expect_not_null("geo_key"),
        expect_unique(["fire_key"]),
        expect_value_in_range("latitude", -90, 90),
        expect_value_in_range("longitude", -180, 180),
        expect_value_in_range("frp", 0, _MAX),
        expect_value_in_range("confidence", 0, 100),
        expect_value_in_range("brightness", 0, _MAX, severity="warn"),
    ]


def silver_vessel_suite() -> list[Expectation]:
    """UC-18 illegal fishing — ``silver_vessel`` identity & timeline."""
    return [
        expect_row_count_min(1),
        expect_not_null("vessel_key"),
        expect_not_null("last_transmission_ts"),
        expect_not_null("event_ts"),
        expect_unique(["vessel_key"]),
        expect_predicate(
            "timeline:first<=last",
            lambda rows: all(
                (r.get("first_transmission_ts") is None)
                or (str(r["first_transmission_ts"]) <= str(r.get("last_transmission_ts", "")))
                for r in rows
            ),
            description="first_transmission_ts <= last_transmission_ts (BR-06).",
        ),
    ]


def silver_scene_suite() -> list[Expectation]:
    """UC-25 catalog / UC-27 damage — ``silver_scene`` catalog quality."""
    return [
        expect_row_count_min(1),
        expect_not_null("scene_key"),
        expect_not_null("event_ts"),
        expect_unique(["scene_key"]),
        expect_value_in_range("cloud_cover", 0, 100),
        expect_value_in_range("completeness_score", 0, 1),
    ]


def silver_index_suite() -> list[Expectation]:
    """UC-16 flood / UC-14 change — ``silver_index`` spectral statistics."""
    return [
        expect_row_count_min(1),
        expect_not_null("event_ts"),
        expect_not_null("index_name"),
        expect_not_null("mean"),
        expect_not_null("geo_key"),
        expect_value_in_range("mean", -1, 1),
        expect_value_in_range("valid_pixel_fraction", 0, 1),
        expect_value_in_range(
            "valid_pixel_fraction", 0.2, 1, severity="warn"),
    ]


def ref_aoi_suite() -> list[Expectation]:
    """Validation ground truth — ``ref_aoi`` footprint sanity."""
    return [
        expect_row_count_min(1),
        expect_not_null("aoi_key"),
        expect_not_null("geo_key"),
        expect_unique(["aoi_key"]),
        expect_value_in_range("area_km2", 0, _MAX),
        expect_predicate(
            "event_type:vocab",
            lambda rows: all(
                r.get("event_type") in {"fire", "flood", "other", None} for r in rows),
            description="event_type in {fire, flood, other}.",
        ),
    ]


# --- Gold suites ------------------------------------------------------------

def gold_eo_daily_suite() -> list[Expectation]:
    """``kpi_eo_daily`` — daily fire KPIs per grid cell."""
    return [
        expect_not_null("geo_key"),
        expect_not_null("date_key"),
        expect_unique(["geo_key", "date_key"]),
        expect_value_in_range("detections", 0, _MAX),
        expect_value_in_range("mean_frp", 0, _MAX, severity="warn"),
        expect_value_in_range("max_frp", 0, _MAX, severity="warn"),
    ]


def gold_vessel_activity_suite() -> list[Expectation]:
    """``fact_vessel_activity`` — daily vessel activity roll-up."""
    return [
        expect_not_null("vessel_key"),
        expect_not_null("date_key"),
        expect_unique(["vessel_key", "date_key"]),
        expect_value_in_range("transmissions", 0, _MAX),
        expect_value_in_range("active_span_days", 0, _MAX, severity="warn"),
    ]


def gold_scene_catalog_suite() -> list[Expectation]:
    """``fact_scene_catalog`` — curated per-scene catalog (UC-25)."""
    return [
        expect_not_null("scene_key"),
        expect_unique(["scene_key"]),
        expect_value_in_range("completeness_score", 0, 1),
        expect_value_in_range("cloud_cover", 0, 100),
        expect_predicate(
            "searchable:consistent",
            lambda rows: all(
                bool(r.get("is_searchable"))
                == bool(r.get("geo_key") and r.get("date_key") and r.get("collection"))
                for r in rows
            ),
            description="is_searchable == (geo_key & date_key & collection) (BR-07).",
        ),
    ]


def gold_wildfire_aoi_suite(ref_aoi_keys: set[str] | None = None) -> list[Expectation]:
    """``kpi_wildfire_aoi_daily`` — daily wildfire KPIs per AOI (UC-15)."""
    suite = [
        expect_not_null("aoi_key"),
        expect_not_null("date_key"),
        expect_unique(["aoi_key", "date_key"]),
        expect_value_in_range("detections", 0, _MAX),
        expect_value_in_range("mean_frp", 0, _MAX, severity="warn"),
    ]
    if ref_aoi_keys is not None:
        suite.append(expect_referential_integrity("aoi_key", ref_aoi_keys))
    return suite


def gold_flood_aoi_suite(ref_aoi_keys: set[str] | None = None) -> list[Expectation]:
    """``kpi_flood_aoi_daily`` — daily flood KPIs per AOI (UC-16)."""
    suite = [
        expect_not_null("aoi_key"),
        expect_not_null("date_key"),
        expect_unique(["aoi_key", "date_key"]),
        expect_value_in_range("ndwi_mean", -1, 1),
        expect_value_in_range("valid_pixel_fraction", 0, 1, severity="warn"),
    ]
    if ref_aoi_keys is not None:
        suite.append(expect_referential_integrity("aoi_key", ref_aoi_keys))
    return suite


# --- Registries -------------------------------------------------------------

SILVER_SUITES: dict[str, Callable[[], list[Expectation]]] = {
    "silver_fire": silver_fire_suite,
    "silver_vessel": silver_vessel_suite,
    "silver_scene": silver_scene_suite,
    "silver_index": silver_index_suite,
    "ref_aoi": ref_aoi_suite,
}

GOLD_SUITES: dict[str, Callable[[], list[Expectation]]] = {
    "kpi_eo_daily": gold_eo_daily_suite,
    "fact_vessel_activity": gold_vessel_activity_suite,
    "fact_scene_catalog": gold_scene_catalog_suite,
    "kpi_wildfire_aoi_daily": gold_wildfire_aoi_suite,
    "kpi_flood_aoi_daily": gold_flood_aoi_suite,
}

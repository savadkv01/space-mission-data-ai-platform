"""Pollutant unit standardization (Phase 9b air-quality Silver).

Surface air-quality sources report a pollutant in different units (mass
concentration ``µg/m³`` / ``mg/m³`` or volumetric ``ppm`` / ``ppb``). The Silver
``obs_air_quality`` entity stores a single **canonical unit per pollutant** while
keeping the raw value/unit for audit (``value_raw`` / ``unit_raw``).

Canonical units (docs/data-modeling/climate/02-silver-entities.md):

* PM2.5 / PM10 / NO2 / SO2 / O3 / BC -> ``µg/m³``
* CO                                 -> ``mg/m³``

Volumetric -> mass conversion uses the ideal-gas relation at a documented
reference state (25 °C, 1 atm -> molar volume 24.45 L/mol)::

    mass_concentration = volume_mixing_ratio * molar_mass / molar_volume

Gases without a defensible conversion are flagged ``suspect`` rather than being
silently converted (the conversion is *versioned* in ``dim_pollutant``).
"""

from __future__ import annotations

from transformation.cleaning.cleaning_rules import to_float

#: Reference molar volume of an ideal gas at 25 °C, 1 atm (litres per mole).
MOLAR_VOLUME_L = 24.45

#: Molar mass (g/mol) per gaseous pollutant used for ppb/ppm -> µg/m³ conversion.
MOLAR_MASS_G = {
    "NO2": 46.0055,
    "SO2": 64.066,
    "O3": 48.00,
    "CO": 28.010,
}

#: Canonical unit each pollutant is standardized to.
POLLUTANT_CANONICAL_UNIT = {
    "PM25": "µg/m³",
    "PM10": "µg/m³",
    "NO2": "µg/m³",
    "SO2": "µg/m³",
    "O3": "µg/m³",
    "BC": "µg/m³",
    "CO": "mg/m³",
}

#: Source parameter name -> canonical pollutant code (``dim_pollutant`` PK).
_PARAM_ALIASES = {
    "pm25": "PM25",
    "pm2.5": "PM25",
    "pm2_5": "PM25",
    "pm10": "PM10",
    "no2": "NO2",
    "so2": "SO2",
    "co": "CO",
    "o3": "O3",
    "bc": "BC",
    "blackcarbon": "BC",
}

#: Pollutants measured as particulate mass — already in µg/m³, never converted.
_PARTICULATE = {"PM25", "PM10", "BC"}


def canonical_pollutant_code(parameter: object) -> str | None:
    """Map a source pollutant parameter name to its canonical code.

    Returns ``None`` for an unrecognised pollutant so the caller can reject the
    record (an unknown pollutant has no ``dim_pollutant`` row / threshold).
    """
    if parameter in (None, ""):
        return None
    token = str(parameter).strip().lower().replace(" ", "")
    return _PARAM_ALIASES.get(token)


def _normalize_unit(unit: object) -> str:
    return (
        str(unit or "")
        .strip()
        .lower()
        .replace("µ", "u")
        .replace("μ", "u")
        .replace("³", "3")
        .replace("²", "2")
    )


def standardize_pollutant_value(
    pollutant_code: str, value: object, unit: object
) -> tuple[float | None, str]:
    """Return ``(value_std, quality_flag)`` in the pollutant's canonical unit.

    ``quality_flag`` is ``valid`` when the value is present and either already
    canonical or converted via a defensible molar relation; it is ``suspect``
    when the unit cannot be defensibly converted (kept, not dropped, so the
    audit columns remain queryable downstream).
    """
    v = to_float(value)
    if v is None:
        return None, "suspect"

    canonical = POLLUTANT_CANONICAL_UNIT.get(pollutant_code)
    if canonical is None:
        return v, "suspect"

    u = _normalize_unit(unit)
    canonical_norm = _normalize_unit(canonical)

    # Already in the canonical unit -> pass through.
    if u in ("", canonical_norm):
        return round(v, 6), "valid"

    # Particulate mass never carries a volumetric unit; accept µg/m³ synonyms.
    if pollutant_code in _PARTICULATE:
        if u in ("ug/m3", "ugm3", "ug/m^3", "micrograms/m3"):
            return round(v, 6), "valid"
        return v, "suspect"

    molar_mass = MOLAR_MASS_G.get(pollutant_code)
    if molar_mass is None:
        return v, "suspect"

    # Volumetric mixing ratio -> mass concentration (µg/m³ base).
    if u in ("ppb", "ppbv"):
        ug_per_m3 = v * molar_mass / MOLAR_VOLUME_L
    elif u in ("ppm", "ppmv"):
        ug_per_m3 = v * 1000.0 * molar_mass / MOLAR_VOLUME_L
    elif u in ("ug/m3", "ugm3", "ug/m^3"):
        ug_per_m3 = v
    elif u in ("mg/m3", "mgm3"):
        ug_per_m3 = v * 1000.0
    else:
        return v, "suspect"

    # CO is reported in mg/m³; every other gas in µg/m³.
    if canonical_norm == "mg/m3":
        return round(ug_per_m3 / 1000.0, 6), "valid"
    return round(ug_per_m3, 6), "valid"

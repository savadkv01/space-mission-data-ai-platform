"""Climate / dust / air-quality Bronze -> Silver cleaning rules (Phase 9b).

Pure-Python, side-effect-free cleaners for the atmospheric domain, mirroring the
existing Earth-observation cleaners in :mod:`transformation.batch.bronze_to_silver`.
Each cleaner returns a :class:`~transformation.cleaning.cleaning_rules.CleanResult`
so it plugs into the shared Silver driver, and the same rules are re-used (as
Spark ``mapInPandas`` logic) by :mod:`transformation.batch.climate_bronze_to_silver`.

Entities (see docs/data-modeling/climate/02-silver-entities.md):

* ``obs_air_quality``  — OpenAQ surface pollutant readings (unit-standardized)
* ``obs_aerosol``      — MODIS/VIIRS AOD per AOI per day
* ``obs_atmos_column`` — TROPOMI trace-gas column densities per AOI per day
"""

from transformation.cleaning.climate.aerosol import clean_aerosol
from transformation.cleaning.climate.air_quality import clean_air_quality
from transformation.cleaning.climate.atmos_column import clean_atmos_column
from transformation.cleaning.climate.units import (
    POLLUTANT_CANONICAL_UNIT,
    canonical_pollutant_code,
    standardize_pollutant_value,
)

__all__ = [
    "clean_aerosol",
    "clean_air_quality",
    "clean_atmos_column",
    "POLLUTANT_CANONICAL_UNIT",
    "canonical_pollutant_code",
    "standardize_pollutant_value",
]

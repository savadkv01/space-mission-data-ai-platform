"""GEE MODIS/VIIRS Aerosol Optical Depth connector — free Sentinel Hub alternative.

Lands the same ``obs_aerosol`` Bronze buckets as
:class:`ingestion.api.modis_aod.ModisAodConnector`, sourced from Google Earth
Engine's MODIS MAIAC AOD collection (``MODIS/061/MCD19A2_GRANULES``, band
``Optical_Depth_055``) instead of the Sentinel Hub Statistical API, whose MODIS
AOD collection is account-dependent / not entitled on the free plan.

The MAIAC band stores AOD scaled by 1000 as an integer, so ``VALUE_SCALE=0.001``
converts it back to the physical 0–5 range the Silver ``clean_aerosol`` cleaner
expects. Source code is kept as ``MODIS_AOD`` so all downstream layers are
unchanged.
"""

from __future__ import annotations

from typing import Any

from ingestion.api.gee import EarthEngineStatsConnector
from ingestion.config.settings import settings


class GeeAodConnector(EarthEngineStatsConnector):
    source_code = "MODIS_AOD"
    rate_limit_per_s = 2
    #: MAIAC native grid ~ 1 km.
    SCALE_M = 1000.0
    #: MCD19A2 Optical_Depth_055 scale factor (raw = AOD * 1000).
    VALUE_SCALE = 0.001

    #: Default AOD collection + band (configurable per sensor / account).
    COLLECTION = "MODIS/061/MCD19A2_GRANULES"
    BAND = "Optical_Depth_055"
    #: Sensors this connector can source AOD from (stamped onto the record).
    SENSORS = ("MODIS", "VIIRS")

    def fetch_raw(self, *, aoi_id: str = "AOI-UAE-NAT",
                  bbox: list[float] | None = None,
                  sensor: str = "MODIS",
                  datetime_range: str = "2024-06-01T00:00:00Z/2024-06-07T23:59:59Z",
                  collection: str | None = None,
                  band: str | None = None,
                  **_: Any) -> tuple[list[dict[str, Any]], str]:
        sensor_code = sensor.upper()
        if sensor_code not in self.SENSORS:
            raise ValueError(
                f"unknown sensor {sensor!r}; choose from {list(self.SENSORS)}"
            )
        aoi = bbox or settings.climate.bbox(aoi_id)
        coll = collection or self.COLLECTION
        aod_band = band or self.BAND
        buckets = self._daily_buckets(
            band=aod_band, collection=coll, bbox=aoi, datetime_range=datetime_range
        )
        records: list[dict[str, Any]] = []
        for bucket in buckets:
            enriched = dict(bucket)
            enriched["product"] = "AOD"
            enriched["aoi_id"] = aoi_id
            enriched["bbox"] = aoi
            enriched["collection"] = coll
            enriched["sensor"] = sensor_code
            enriched["unit"] = "unitless"
            records.append(enriched)
        return records, "json"

"""MODIS / VIIRS Aerosol Optical Depth (AOD) connector — Sentinel Hub stats.

Lands per-AOI, per-day Aerosol Optical Depth aggregates as JSON records, feeding
the Silver ``obs_aerosol`` entity (UC-C2 dust-storm monitoring, PM proxy). Uses
the same Statistical-API mechanism as :class:`TropomiConnector` (the cleaner of
the two options in the Phase 8b prompt) so no binary HDF/NetCDF landing is
introduced.

Each record carries the AOD statistics plus retrieval context (``sensor``,
``valid vs no-data`` pixel counts inside the bucket outputs) so the Silver
cleaner can apply quality filtering and desert bright-surface handling.

The exact AOD data collection/band depends on the Sentinel Hub account's
available third-party collections; ``COLLECTION`` and the sampled band are
configurable and default to a documented placeholder. Landed under
``_source = "MODIS_AOD"``.
Docs: https://docs.sentinel-hub.com/api/latest/api/statistical/
"""

from __future__ import annotations

from typing import Any

from ingestion.api.sentinelhub_stats import SentinelHubStatsConnector
from ingestion.config.settings import settings


def _aod_evalscript(band: str) -> str:
    """VERSION=3 evalscript exposing a single AOD band as ``index`` + dataMask."""
    return (
        "//VERSION=3\n"
        "function setup() {\n"
        '  return {\n'
        f'    input: [{{ bands: ["{band}", "dataMask"] }}],\n'
        '    output: [\n'
        '      { id: "index", bands: 1 },\n'
        '      { id: "dataMask", bands: 1 }\n'
        "    ]\n"
        "  };\n"
        "}\n"
        "function evaluatePixel(s) {\n"
        f"  return {{ index: [s.{band}], dataMask: [s.dataMask] }};\n"
        "}\n"
    )


class ModisAodConnector(SentinelHubStatsConnector):
    source_code = "MODIS_AOD"
    rate_limit_per_s = 2

    #: AOD data collection (configurable; account-dependent third-party layer).
    COLLECTION = "modis"
    #: Sampled AOD band (550 nm optical depth) — configurable per collection.
    AOD_BAND = "AOD"

    #: Sensors this connector can source AOD from (stamped onto the record).
    SENSORS = ("MODIS", "VIIRS")

    def fetch_raw(self, *, aoi_id: str = "AOI-DXB",
                  bbox: list[float] | None = None,
                  sensor: str = "MODIS",
                  datetime_range: str = "2024-06-01T00:00:00Z/2024-06-30T23:59:59Z",
                  aggregation_interval: str = "P1D",
                  collection: str | None = None,
                  band: str | None = None,
                  resolution: float = 0.02,
                  **_: Any) -> tuple[list[dict[str, Any]], str]:
        sensor_code = sensor.upper()
        if sensor_code not in self.SENSORS:
            raise ValueError(
                f"unknown sensor {sensor!r}; choose from {list(self.SENSORS)}"
            )
        aoi = bbox or settings.climate.bbox(aoi_id)
        coll = collection or self.COLLECTION
        aod_band = band or self.AOD_BAND
        buckets = self._request_stats(
            evalscript=_aod_evalscript(aod_band),
            bbox=aoi,
            datetime_range=datetime_range,
            aggregation_interval=aggregation_interval,
            collection=coll,
            resolution=resolution,
        )
        records: list[dict[str, Any]] = []
        for bucket in buckets:
            if isinstance(bucket, dict):
                enriched = dict(bucket)
                enriched["product"] = "AOD"
                enriched["aoi_id"] = aoi_id
                enriched["bbox"] = aoi
                enriched["collection"] = coll
                enriched["sensor"] = sensor_code
                enriched["unit"] = "unitless"
                records.append(enriched)
        return records, "json"

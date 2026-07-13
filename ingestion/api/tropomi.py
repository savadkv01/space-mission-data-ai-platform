"""TROPOMI (Sentinel-5P) trace-gas connector — Sentinel Hub Statistical API.

Reuses the exact OAuth + evalscript + Statistical-API mechanism proven by
:class:`SentinelHubStatsConnector`, but requests **atmospheric column** products
from the Sentinel-5P L2 collection instead of Sentinel-2 spectral indices. Each
response bucket becomes one Bronze record per (AOI, product, time bucket) with
mean/min/max/valid-pixel stats, feeding the Silver ``obs_atmos_column`` entity
(UC-C2 dust/smoke, UC-C3 air quality).

Landed under ``_source = "TROPOMI"`` (distinct from ``SENTINELHUB_STATS`` which
carries the Sentinel-2 vegetation/water indices).
Docs: https://docs.sentinel-hub.com/api/latest/data/sentinel-5p-l2/
"""

from __future__ import annotations

from typing import Any

from ingestion.api.sentinelhub_stats import SentinelHubStatsConnector
from ingestion.config.settings import settings


def _s5p_evalscript(band: str) -> str:
    """VERSION=3 evalscript exposing one Sentinel-5P product band as ``index``.

    A ``dataMask`` output is always emitted so the Statistical API can report
    valid vs no-data pixel counts (retrieval completeness).
    """
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


class TropomiConnector(SentinelHubStatsConnector):
    source_code = "TROPOMI"
    rate_limit_per_s = 2

    #: Sentinel-5P L2 data collection on Sentinel Hub.
    COLLECTION = "sentinel-5p-l2"

    #: Trace-gas / aerosol products as single-band evalscripts.
    EVALSCRIPTS = {
        "NO2": _s5p_evalscript("NO2"),
        "SO2": _s5p_evalscript("SO2"),
        "CO": _s5p_evalscript("CO"),
        "O3": _s5p_evalscript("O3"),
        "CH4": _s5p_evalscript("CH4"),
        "AER_AI": _s5p_evalscript("AER_AI_354_388"),
    }

    #: Canonical unit per product (stamped onto each record for the cleaner).
    UNITS = {
        "NO2": "mol/m2", "SO2": "mol/m2", "CO": "mol/m2", "O3": "mol/m2",
        "CH4": "ppb", "AER_AI": "unitless",
    }

    def fetch_raw(self, *, product: str = "NO2",
                  aoi_id: str = "AOI-UAE-NAT",
                  bbox: list[float] | None = None,
                  datetime_range: str = "2024-06-01T00:00:00Z/2024-06-30T23:59:59Z",
                  aggregation_interval: str = "P1D",
                  collection: str | None = None,
                  resolution: float = 0.01,
                  **_: Any) -> tuple[list[dict[str, Any]], str]:
        product_code = product.upper()
        if product_code not in self.EVALSCRIPTS:
            raise ValueError(
                f"unknown product {product!r}; choose from {sorted(self.EVALSCRIPTS)}"
            )
        aoi = bbox or settings.climate.bbox(aoi_id)
        coll = collection or self.COLLECTION
        buckets = self._request_stats(
            evalscript=self.EVALSCRIPTS[product_code],
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
                enriched["product"] = product_code
                enriched["aoi_id"] = aoi_id
                enriched["bbox"] = aoi
                enriched["collection"] = coll
                enriched["unit"] = self.UNITS.get(product_code, "unitless")
                records.append(enriched)
        return records, "json"

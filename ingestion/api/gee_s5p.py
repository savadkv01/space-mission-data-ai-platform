"""GEE Sentinel-5P (TROPOMI) trace-gas connector — free Sentinel Hub alternative.

Lands the same ``obs_atmos_column`` Bronze buckets as
:class:`ingestion.api.tropomi.TropomiConnector`, but sources them from Google
Earth Engine's Sentinel-5P collections (free, non-commercial) instead of the
Sentinel Hub Statistical API, whose ``sentinel-5p-l2`` collection is not
entitled on the free / CDSE plan. NO₂ uses the faster NRTI collection with an
OFFL fallback; the other products use OFFL.

Source code is kept as ``TROPOMI`` so every downstream Silver / Gold / serving /
BI layer (which keys off ``_source``) is unchanged — only the ingestion backend
differs. Units match the existing ``GAS_UNIT`` map in the Silver cleaner
(mol/m² for NO₂/SO₂/CO/O₃, ppb for CH₄, unitless for the aerosol index).
"""

from __future__ import annotations

from datetime import timedelta
from typing import Any

from ingestion.api.gee import EarthEngineStatsConnector
from ingestion.config.settings import settings


class GeeS5pConnector(EarthEngineStatsConnector):
    source_code = "TROPOMI"
    rate_limit_per_s = 2
    #: Sentinel-5P OFFL native grid ~ 1113 m (0.01°) — sample at that scale.
    SCALE_M = 1113.2

    #: product -> (GEE image collection, band, canonical unit).
    PRODUCTS: dict[str, tuple[str, str, str]] = {
        "NO2": ("COPERNICUS/S5P/NRTI/L3_NO2",
                "tropospheric_NO2_column_number_density", "mol/m2"),
        "SO2": ("COPERNICUS/S5P/OFFL/L3_SO2",
                "SO2_column_number_density", "mol/m2"),
        "CO": ("COPERNICUS/S5P/OFFL/L3_CO",
               "CO_column_number_density", "mol/m2"),
        "O3": ("COPERNICUS/S5P/OFFL/L3_O3",
               "O3_column_number_density", "mol/m2"),
        "CH4": ("COPERNICUS/S5P/OFFL/L3_CH4",
                "CH4_column_volume_mixing_ratio_dry_air", "ppb"),
        "AER_AI": ("COPERNICUS/S5P/OFFL/L3_AER_AI",
                   "absorbing_aerosol_index", "unitless"),
    }
    FALLBACK_COLLECTIONS: dict[str, str] = {
        "NO2": "COPERNICUS/S5P/OFFL/L3_NO2",
    }

    def fetch_raw(self, *, product: str = "NO2",
                  aoi_id: str = "AOI-UAE-NAT",
                  bbox: list[float] | None = None,
                  datetime_range: str = "2024-06-01T00:00:00Z/2024-06-07T23:59:59Z",
                  **_: Any) -> tuple[list[dict[str, Any]], str]:
        product_code = product.upper()
        if product_code not in self.PRODUCTS:
            raise ValueError(
                f"unknown product {product!r}; choose from {sorted(self.PRODUCTS)}"
            )
        collection, band, unit = self.PRODUCTS[product_code]
        aoi = bbox or settings.climate.bbox(aoi_id)
        buckets = self._daily_buckets(
            band=band, collection=collection, bbox=aoi, datetime_range=datetime_range
        )
        bucket_collections = {
            bucket["interval"]["from"]: collection for bucket in buckets
        }
        fallback_collection = self.FALLBACK_COLLECTIONS.get(product_code)
        if fallback_collection:
            start_s, _, end_s = datetime_range.partition("/")
            day = self._parse_day(start_s)
            end_day = self._parse_day(end_s or start_s)
            while day <= end_day:
                day_start = day.strftime("%Y-%m-%dT00:00:00Z")
                if day_start not in bucket_collections:
                    day_end = (day + timedelta(days=1)).strftime("%Y-%m-%dT00:00:00Z")
                    fallback = self._daily_buckets(
                        band=band,
                        collection=fallback_collection,
                        bbox=aoi,
                        datetime_range=f"{day_start}/{day_end}",
                    )
                    buckets.extend(fallback)
                    bucket_collections.update({
                        bucket["interval"]["from"]: fallback_collection
                        for bucket in fallback
                    })
                day += timedelta(days=1)
        records: list[dict[str, Any]] = []
        for bucket in buckets:
            enriched = dict(bucket)
            enriched["product"] = product_code
            enriched["aoi_id"] = aoi_id
            enriched["bbox"] = aoi
            enriched["collection"] = bucket_collections[bucket["interval"]["from"]]
            enriched["unit"] = unit
            records.append(enriched)
        return records, "json"

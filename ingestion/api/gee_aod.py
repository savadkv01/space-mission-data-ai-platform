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
    #: MAIAC per-pixel QA: keep only AOD_QA bits 0-2 == 1 (clear) and bits
    #: 8-11 == 0 (best-quality AOD). Records are stamped with this mask id.
    QA_BAND = "AOD_QA"
    QA_MASK = "maiac_clear_bestqa_v1"
    #: AOD_QA bits 13-14 = MAIAC aerosol model (0 background, 1 smoke, 2 dust).
    #: Each bucket reports the share of QA-passing pixels retrieved with the smoke
    #: and dust models, so Gold can tell smoke from mineral dust (L5 / D-07).
    AEROSOL_MODEL = "maiac_aod_qa_bits13_14_v1"
    AEROSOL_MODEL_SHIFT = 13
    SMOKE_MODEL = 1
    DUST_MODEL = 2
    #: Sensors this connector can source AOD from (stamped onto the record).
    SENSORS = ("MODIS", "VIIRS")

    def fetch_raw(self, *, aoi_id: str = "AOI-DXB",
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
            if coll == self.COLLECTION:
                enriched["qa_mask"] = self.QA_MASK
                enriched["aerosol_model"] = self.AEROSOL_MODEL
            records.append(enriched)
        return records, "json"

    @staticmethod
    def maiac_qa_ok(ee: Any, qa: Any) -> Any:
        """Per-pixel boolean: MAIAC cloud mask clear AND best-quality AOD."""
        cloud = qa.bitwiseAnd(0b111)
        aod_qa = qa.rightShift(8).bitwiseAnd(0b1111)
        return cloud.eq(1).And(aod_qa.eq(0))

    @classmethod
    def maiac_aerosol_model(cls, qa: Any) -> Any:
        """Per-pixel MAIAC aerosol model code (AOD_QA bits 13-14)."""
        return qa.rightShift(cls.AEROSOL_MODEL_SHIFT).bitwiseAnd(0b11)

    def _ee_reduce_region(self, *, band: str, collection: str,
                          bbox: list[float], time_from: str,
                          time_to: str) -> dict[str, Any] | None:  # pragma: no cover
        if collection != self.COLLECTION:
            return super()._ee_reduce_region(band=band, collection=collection, bbox=bbox,
                                             time_from=time_from, time_to=time_to)
        ee = self._ee_client()
        self._ensure_init()
        geom = ee.Geometry.Rectangle(bbox)
        coll = (ee.ImageCollection(collection)
                .filterDate(time_from, time_to)
                .filterBounds(geom))
        if not coll.size().getInfo():
            return None
        qa_band = self.QA_BAND

        def masked(image: Any) -> Any:
            image = ee.Image(image)
            qa = image.select(qa_band)
            model = self.maiac_aerosol_model(qa)
            return (image.select(band).rename("index")
                    .addBands(model.eq(self.SMOKE_MODEL).rename("smoke"))
                    .addBands(model.eq(self.DUST_MODEL).rename("dust"))
                    .updateMask(self.maiac_qa_ok(ee, qa)))

        composite = coll.map(masked).mean()
        stats = self._summarize_image(composite.select("index"), geom, ee)
        if stats is None:
            return None
        fractions = composite.select(["smoke", "dust"]).reduceRegion(
            reducer=ee.Reducer.mean(), geometry=geom, scale=self.SCALE_M,
            bestEffort=True, maxPixels=self.MAX_PIXELS).getInfo() or {}
        stats["smokeFraction"] = fractions.get("smoke")
        stats["dustFraction"] = fractions.get("dust")
        return stats

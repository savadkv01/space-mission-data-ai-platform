# 14 — Glossary (Beginner-Oriented)

Terms used across the source guides. For the platform-wide glossary, see
[../13-glossary.md](../13-glossary.md) and [../climate/10-glossary.md](../climate/10-glossary.md).

| Term | Definition | Seen in |
| --- | --- | --- |
| **AER_AI** | UV Absorbing Aerosol Index from TROPOMI; positive values indicate UV-absorbing particles (dust, smoke) | 04 |
| **AIS** | Automatic Identification System: VHF radio broadcasts of ship identity, position and speed | 10 |
| **AOD** | Aerosol Optical Depth: unitless measure of light extinction by particles in the whole atmospheric column | 05 |
| **AOI** | Area of Interest: the polygon or bbox over which data is requested or aggregated | all |
| **ap / a_running** | Linear-scale equivalent of Kp, in units of ~2 nT | 08 |
| **bbox** | Bounding box `[min_lon, min_lat, max_lon, max_lat]` | all |
| **BSTAR** | SGP4 drag coefficient (1/Earth radii) | 09 |
| **Brightness temperature** | Temperature a black body would need to emit the observed radiance; Kelvin | 01 |
| **Bronze envelope** | Our provenance wrapper (`_ingest_id`, `_source`, `_event_ts`, …) around each raw record | README |
| **CMR** | NASA Common Metadata Repository: catalogue of NASA Earth-science granules | 12 |
| **Column density** | Amount of a gas in a vertical air column per unit area (mol/m²) | 04 |
| **Contextual fire algorithm** | Flags a pixel as fire when it is much hotter than its neighbours | 01 |
| **COSPAR ID** | International designator: launch year – launch number – piece (`1998-067A`) | 09 |
| **CRS / EPSG:4326** | Coordinate Reference System; 4326 = WGS 84 latitude/longitude in degrees | 00 |
| **DAAC** | NASA Distributed Active Archive Center (e.g., LP DAAC) | 05, 12 |
| **DOAS** | Differential Optical Absorption Spectroscopy: retrieves gases from spectral absorption features | 04 |
| **Epoch** | Reference time at which orbital elements are valid | 09 |
| **Evalscript** | Sentinel Hub JavaScript defining per-pixel band math | 12 |
| **Fill value** | Sentinel number meaning "missing" (e.g., −999 in POWER) | 07 |
| **FRP** | Fire Radiative Power: radiant energy released by a fire, in MW | 01 |
| **GEE** | Google Earth Engine: cloud platform for planetary-scale geospatial analysis; our raster-statistics backend | 02–05 |
| **GeoJSON** | JSON format for vector geometry (RFC 7946); coordinates `[lon, lat]` | 11 |
| **GP elements / OMM** | General Perturbations orbital elements; OMM = CCSDS Orbit Mean-Elements Message format | 09 |
| **Granule** | One chunk of satellite data, usually one overpass segment | 05, 12 |
| **Harmonized (S2)** | GEE Sentinel-2 collection with the 2022 processing-baseline offset removed | 02, 03 |
| **IMO number** | Permanent 7-digit vessel identifier | 10 |
| **Kp index** | Planetary geomagnetic activity index, 0–9 quasi-logarithmic, 3-hourly | 08 |
| **L1/L2/L3/L4** | Processing levels: calibrated radiance → per-pixel geophysical variable → gridded → model/analysis | 00 |
| **LANCE** | NASA Land, Atmosphere Near real-time Capability for EOS | 01 |
| **LEO** | Low Earth Orbit (< ~2,000 km) | 00, 09 |
| **LST (time)** | Local Solar Time: noon when the sun is highest; ≈ UTC + lon/15 h | 07 |
| **MAIAC** | Multi-Angle Implementation of Atmospheric Correction: MODIS 1 km aerosol algorithm | 05 |
| **Mean motion** | Revolutions per day of an orbiting object | 09 |
| **MGRS tile** | Military Grid Reference System 100 km tile used by Sentinel-2 (e.g., `T39RZH`) | 02 |
| **MMSI / ssvid** | 9-digit maritime radio identity broadcast via AIS | 10 |
| **NBR** | Normalized Burn Ratio, (NIR − SWIR)/(NIR + SWIR) | 03 |
| **NDVI** | Normalized Difference Vegetation Index, (NIR − Red)/(NIR + Red) | 03 |
| **NDWI** | Normalized Difference Water Index (McFeeters), (Green − NIR)/(Green + NIR) | 03 |
| **NORAD catalog ID** | US Space Force number for a tracked space object | 09 |
| **NRT / NRTI / OFFL** | Near-real-time vs offline (science-quality) processing streams | 01, 04 |
| **Overpass** | A satellite passing over a location | 00 |
| **Reanalysis** | Model reconstruction of past weather constrained by observations | 07 |
| **reduceRegion** | GEE operation computing statistics of an image over a geometry | 00, 03–05 |
| **SCL** | Sentinel-2 Scene Classification Layer (cloud, shadow, water, vegetation…) | 03 |
| **SGP4** | Simplified General Perturbations 4: standard propagator for GP elements | 09, 13 |
| **STAC** | SpatioTemporal Asset Catalog: open JSON standard for describing geospatial assets | 02, 12 |
| **Sun-synchronous orbit** | Orbit that crosses each latitude at the same local solar time every day | 00 |
| **Swath** | Width of ground imaged in one satellite pass | 00 |
| **TEME** | True Equator Mean Equinox: inertial frame of SGP4 output | 09 |
| **TLE** | Two-Line Element set: legacy text format for GP elements | 09 |
| **Valid-pixel fraction** | `sampleCount / (sampleCount + noDataCount)`: share of the AOI with usable data | 00, 03–05 |
| **VIIRS** | Visible Infrared Imaging Radiometer Suite on S-NPP, NOAA-20 and NOAA-21 | 01 |
| **WRS-2 path/row** | Landsat Worldwide Reference System scene grid | 12 |

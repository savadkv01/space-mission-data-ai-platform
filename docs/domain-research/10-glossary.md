# 10 Glossary

## Executive Summary

This glossary defines the domain, data, and technical terms used throughout the Phase 2 domain research. It is intended to give engineers and stakeholders a shared vocabulary for the space data ecosystem and the datasets selected for the platform.

## Space and Earth Observation Terms

| Term | Definition |
| --- | --- |
| Earth Observation (EO) | Collection of information about Earth's surface and atmosphere using satellite or airborne sensors |
| Optical imagery | Imagery captured in visible and infrared light; affected by clouds and daylight |
| Synthetic Aperture Radar (SAR) | Active radar imaging that works through clouds and at night |
| Multispectral | Imagery captured across several discrete spectral bands |
| Hyperspectral | Imagery captured across many narrow contiguous bands |
| Revisit time | Interval between successive satellite observations of the same location |
| Swath | Width of the ground strip a sensor images in one pass |
| Ground station | Facility that receives downlinked satellite data and uplinks commands |
| Downlink | Transmission of data from a satellite to the ground |
| Mission operations center | Facility that manages spacecraft and data product generation |

## Data Product and Processing Terms

| Term | Definition |
| --- | --- |
| Level 0 | Raw reconstructed instrument data |
| Level 1 | Radiometrically and geometrically corrected data |
| Level 2 | Geophysical variables, including atmospheric correction (e.g., surface reflectance) |
| Level 3 | Gridded, composited, time-aggregated products |
| Level 4 | Modeled or derived analytics products |
| Analysis-ready data | Data preprocessed to a state suitable for direct analysis |
| Granule | A discrete file or unit of a satellite data product |
| Scene | A single satellite image covering a defined area |
| Tile | A spatial subdivision of imagery for storage and access |
| Burned area | Product indicating fire-affected land |
| Active fire detection | Point detection of thermal anomalies indicating fire |

## Indices and Measurements

| Term | Definition |
| --- | --- |
| NDVI | Normalized Difference Vegetation Index; vegetation greenness |
| NDWI | Normalized Difference Water Index; surface water presence |
| NBR | Normalized Burn Ratio; burn severity assessment |
| FRP | Fire Radiative Power; intensity of detected fire |
| Reflectance | Fraction of solar radiation reflected by a surface |
| Backscatter | Radar energy returned to a SAR sensor |
| Aerosol Optical Depth (AOD) | Measure of aerosols (e.g., smoke) in the atmosphere |

## Orbital and Tracking Terms

| Term | Definition |
| --- | --- |
| TLE | Two-Line Element set encoding a satellite's orbit |
| GP | General Perturbations orbital data format |
| NORAD ID | Catalog number identifying a tracked space object |
| Ephemeris | Table of computed positions of a body over time |
| SGP4 | Standard model for propagating TLE orbits |
| Orbit determination | Process of estimating a satellite's orbit from observations |
| Epoch | Reference time for an orbital element set |

## Maritime Terms

| Term | Definition |
| --- | --- |
| AIS | Automatic Identification System broadcasting vessel position and identity |
| MMSI | Maritime Mobile Service Identity, a vessel's unique identifier |
| Fishing effort | Estimated time vessels spend fishing, derived from AIS |
| Spoofing | Falsifying AIS identity or position |
| SOG / COG | Speed Over Ground / Course Over Ground |

## Data Engineering Terms

| Term | Definition |
| --- | --- |
| Bronze layer | Raw ingested data preserved as received |
| Silver layer | Cleaned, conformed, and validated data |
| Gold layer | Analytics-ready, business-level data |
| Batch ingestion | Scheduled loading of bulk data |
| Streaming ingestion | Continuous loading of event data |
| Watermark | Marker tracking processed data progress |
| Schema drift | Unexpected change in data structure over time |
| Rate limit | Cap on requests to an API in a time window |
| Backfill | Loading historical data to populate a system |
| CRS | Coordinate Reference System defining spatial coordinates |

## Organizations

| Acronym | Organization |
| --- | --- |
| NASA | National Aeronautics and Space Administration |
| ESA | European Space Agency |
| NOAA | National Oceanic and Atmospheric Administration |
| USGS | United States Geological Survey |
| ECMWF | European Centre for Medium-Range Weather Forecasts |
| WRI | World Resources Institute |
| GFW | Global Fishing Watch |
| MBRSC | Mohammed Bin Rashid Space Centre |

## Cross References

- Terms are used throughout [01-space-data-ecosystem-overview.md](./01-space-data-ecosystem-overview.md) and [02-dataset-catalog.md](./02-dataset-catalog.md).
- Phase 1 glossary is in [../business/11-glossary.md](../business/11-glossary.md).

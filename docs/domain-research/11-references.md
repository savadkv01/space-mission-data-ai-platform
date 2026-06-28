# 11 References

## Executive Summary

This document lists the authoritative sources and access points for every dataset and concept referenced in the Phase 2 domain research. Access notes indicate whether free registration is required. URLs are provided to support the ingestion design in later phases. All sources are open and free at the tiers used by this project.

## Dataset Access Points

### Satellite Data

| Dataset | Access | Registration |
| --- | --- | --- |
| Copernicus Sentinel-2 / Sentinel-1 | https://dataspace.copernicus.eu | Free account |
| Landsat 8/9 | https://earthexplorer.usgs.gov and https://registry.opendata.aws/usgs-landsat | Free account / open S3 |
| NASA GIBS / Worldview | https://worldview.earthdata.nasa.gov and https://gibs.earthdata.nasa.gov | None |

### Earth Observation

| Dataset | Access | Registration |
| --- | --- | --- |
| NASA FIRMS | https://firms.modaps.eosdis.nasa.gov | Free API key |
| MODIS (LP DAAC) | https://lpdaac.usgs.gov | Earthdata login |
| VIIRS Active Fire | https://firms.modaps.eosdis.nasa.gov | Free API key |
| Copernicus EMS | https://emergency.copernicus.eu | None |
| NASA Earthdata Search | https://search.earthdata.nasa.gov | Earthdata login |
| Sentinel Hub | https://www.sentinel-hub.com | Free account |

### Space Weather

| Dataset | Access | Registration |
| --- | --- | --- |
| NOAA SWPC | https://www.swpc.noaa.gov and https://services.swpc.noaa.gov | None |
| NASA DONKI | https://api.nasa.gov (DONKI) | Free API key |
| GOES X-ray Flux | https://services.swpc.noaa.gov/json | None |

### Orbital / Trajectory

| Dataset | Access | Registration |
| --- | --- | --- |
| CelesTrak | https://celestrak.org | None |
| Space-Track | https://www.space-track.org | Free account |
| N2YO | https://www.n2yo.com/api | Free API key |

### Launch Data

| Dataset | Access | Registration |
| --- | --- | --- |
| Launch Library 2 | https://thespacedevs.com and https://ll.thespacedevs.com | None |
| SpaceX API | https://github.com/r-spacex/SpaceX-API | None |

### Astronomical Data

| Dataset | Access | Registration |
| --- | --- | --- |
| NASA Open APIs (APOD, NeoWs) | https://api.nasa.gov | Free API key |
| JPL Horizons | https://ssd.jpl.nasa.gov/horizons | None |
| Minor Planet Center | https://www.minorplanetcenter.net | None |

### Climate / Environmental

| Dataset | Access | Registration |
| --- | --- | --- |
| NOAA Climate Data Online | https://www.ncei.noaa.gov/cdo-web | Free token |
| Copernicus Climate Data Store (ERA5) | https://cds.climate.copernicus.eu | Free account |
| NASA POWER | https://power.larc.nasa.gov | None |
| Global Forest Watch | https://www.globalforestwatch.org and https://data-api.globalforestwatch.org | Free key for API |
| OpenAQ | https://openaq.org and https://docs.openaq.org | Free API key |
| Copernicus Atmosphere (CAMS) | https://ads.atmosphere.copernicus.eu | Free account |

### Real-time Telemetry APIs

| Dataset | Access | Registration |
| --- | --- | --- |
| Global Fishing Watch API | https://globalfishingwatch.org/our-apis | Free key |
| AISHub / AISStream | https://www.aishub.net and https://aisstream.io | Free account |
| Open Notify ISS | http://open-notify.org | None |

## Standards and Concepts

| Topic | Reference |
| --- | --- |
| EO processing levels | NASA EOSDIS Data Processing Levels documentation |
| TLE / SGP4 | CelesTrak documentation and NORAD models |
| Coordinate Reference Systems | EPSG registry (https://epsg.org) |
| Copernicus programme | https://www.copernicus.eu |
| NASA Earthdata | https://www.earthdata.nasa.gov |

## Access Notes and Assumptions

1. "Free API key" and "Free account" indicate no-cost registration with usage quotas.
2. Endpoints are current as of authoring; ingestion design should verify availability at build time.
3. Community-maintained APIs (e.g., SpaceX) may change; treat as non-critical reference sources.
4. All listed sources comply with the project's open-data and free-tier constraints.

## Cross References

- Full dataset descriptions are in [02-dataset-catalog.md](./02-dataset-catalog.md).
- MVP subset is in [07-mvp-datasets.md](./07-mvp-datasets.md).

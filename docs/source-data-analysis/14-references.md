# 14 References & Access Prerequisites

## Executive Summary

This document lists every source with its access point and the prerequisites required to use it: anonymous (no auth), free API key, or free account registration. This lets the ingestion team prepare credentials before designing pipelines.

## Access Prerequisite Legend

| Level | Meaning |
| --- | --- |
| Anonymous | No key or login; public REST/file access |
| Free API key | Free registration to obtain a key/token |
| Free account | Login required (username/password), free |
| Free account + token | Account plus generated API token/OAuth client |

## Reference Table

| Source | Access | Prerequisite | Notes |
| --- | --- | --- | --- |
| Sentinel-2 / Sentinel-1 (Copernicus Data Space) | dataspace.copernicus.eu | Free account + token | OAuth client for API; UI download free |
| Sentinel Hub | sentinel-hub.com | Free account + token | Free credits tier; OAuth client |
| NASA FIRMS | firms.modaps.eosdis.nasa.gov | Free API key (MAP_KEY) | Anonymous for UI; key for API |
| NASA Earthdata | earthdata.nasa.gov | Free account | Earthdata Login (EDL) for downloads |
| USGS Landsat | earthexplorer.usgs.gov | Free account | M2M API needs account; AWS Open Data anonymous |
| MODIS / VIIRS (LP DAAC) | ladsweb.modaps.eosdis.nasa.gov | Free account | Earthdata Login |
| Copernicus EMS | emergency.copernicus.eu | Anonymous | Public rapid-mapping products |
| NASA POWER | power.larc.nasa.gov | Anonymous | Open REST API |
| NOAA SWPC | swpc.noaa.gov | Anonymous | Open JSON products |
| NASA DONKI | ccmc.gsfc.nasa.gov/donki | Free API key | DEMO_KEY works; key for volume |
| GOES X-ray flux | services.swpc.noaa.gov | Anonymous | Open JSON |
| GFZ Kp index | kp.gfz-potsdam.de | Anonymous | File/API download |
| OMNIWeb | omniweb.gsfc.nasa.gov | Anonymous | Open API/file |
| DSCOVR / ACE | services.swpc.noaa.gov | Anonymous | Open JSON |
| CelesTrak TLE/GP/SatCat | celestrak.org | Anonymous | Open files; fair-use limits |
| Space-Track | space-track.org | Free account | Login required; throttled |
| SOCRATES | celestrak.org/SOCRATES | Anonymous | Open files |
| JPL Horizons / SBDB | ssd.jpl.nasa.gov | Anonymous | Open API |
| Launch Library 2 | thespacedevs.com | Anonymous (key optional) | 15 req/hr anon; key raises limit |
| SpaceX API | github.com/r-spacex/SpaceX-API | Anonymous | Maintenance mode |
| RocketLaunch.Live | rocketlaunch.live | Free API key | Free tier cap |
| NASA NeoWs / APOD | api.nasa.gov | Free API key | DEMO_KEY works |
| Minor Planet Center | minorplanetcenter.net | Anonymous | Open files |
| Global Fishing Watch | globalfishingwatch.org | Free account + token | Account for API token |
| ERA5 / CAMS (Copernicus CDS) | cds.climate.copernicus.eu | Free account + token | Accept license; CDS API key |
| NOAA Climate Data Online | ncei.noaa.gov | Free API key | Token via email |
| Global Forest Watch | globalforestwatch.org | Free API key | Account for API |
| OpenAQ | openaq.org | Anonymous (key optional) | Key raises limits |
| NOAA Tides & Currents | tidesandcurrents.noaa.gov | Anonymous | Open API |
| OISST | ncei.noaa.gov | Anonymous | Bulk download |
| N2YO | n2yo.com | Free API key | Account for key |
| Open Notify ISS | open-notify.org | Anonymous | Open API |
| ISS Lightstreamer | isslive.com | Anonymous | Public stream |
| SatNOGS | db.satnogs.org | Anonymous (key optional) | Key for write/extra |
| Heavens-Above | heavens-above.com | Anonymous | Scrape limits |
| NASA anomaly dataset | nasa.gov / kaggle | Free account | Kaggle/EDL login |

## Summary by Prerequisite

| Prerequisite | Sources |
| --- | --- |
| Anonymous | POWER, SWPC, GOES, Kp, OMNIWeb, DSCOVR, CelesTrak, SOCRATES, Horizons/SBDB, MPC, EMS, OISST, NOAA Tides, Open Notify, ISS stream, SpaceX |
| Free API key | FIRMS, DONKI, NeoWs/APOD, NOAA CDO, GFW forest, N2YO, RocketLaunch (optional: LL2, OpenAQ, SatNOGS) |
| Free account / +token | Copernicus, Sentinel Hub, Earthdata, Landsat M2M, MODIS/VIIRS, Space-Track, GFW, ERA5/CAMS, anomaly dataset |

## Cross References

- Phase 2 references: [../domain-research/11-references.md](../domain-research/11-references.md)
- Profiling: [02-dataset-profiling.md](./02-dataset-profiling.md)

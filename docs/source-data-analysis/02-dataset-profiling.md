# 02 Dataset Profiling

## Executive Summary

This document provides deep technical profiles for the 45 inventory datasets. Each profile covers source organization, format, high-level schema, granularity, update frequency, historical coverage, geospatial coverage, volume, API limits, and a reliability score. Profiles are grouped by category and condensed into comparison tables to keep the document usable for ingestion design.

## Reliability Scoring

| Score | Meaning |
| --- | --- |
| High | Authoritative, stable API, strong uptime, documented schema |
| Medium | Reliable but occasional latency, queues, or partial docs |
| Low | Community-maintained, rate-limited, or maintenance-mode |

---

## 1. Satellite Telemetry

| Dataset | Format | Granularity | Update | History | Geo | Volume | Limits | Reliability |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| N2YO | API/JSON | Event/pass | Real-time | None | Global | Small | Free key, rate-limited | Medium |
| Open Notify ISS | API/JSON | Second | Real-time | None | Global | Small | Soft limits | Medium |
| ISS Lightstreamer | Stream | Sub-second | Real-time | None | N/A | Small | Public stream | Medium |
| SatNOGS | API/JSON | Pass-based | Hourly | 2017+ | Global | Small-Med | Open | Medium |
| CelesTrak SatCat | API/File | Daily | Daily | Full catalog | Global | Small | None | High |

Schema commonality: `object_id`, `timestamp`, `lat/lon/alt`, `az/el`, `velocity`, `status`.

## 2. Earth Observation

| Dataset | Format | Granularity | Update | History | Geo | Volume | Limits | Reliability |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Sentinel-2 | API/Bulk | Scene | ~5 day | 2015+ | Global | Large | Quota/queue | High |
| Sentinel-1 SAR | API/Bulk | Scene | 6-12 day | 2014+ | Global | Large | Quota/queue | High |
| Landsat 8/9 | API/Bulk | Scene | 16 day | 1972+ | Global | Large | Open | High |
| FIRMS | API/File | Event | ~3 hr | 2000+ | Global | Small-Med | Map key cap | High |
| MODIS | Bulk/API | Daily | Daily | 2000+ | Global | Med-Large | Earthdata login | High |
| VIIRS | API/File | Event | NRT | 2012+ | Global | Small-Med | Map key cap | High |
| Copernicus EMS | File | Event | On activation | 2012+ | Global | Med | None | High |
| Sentinel Hub | API | AOI | On-demand | 2015+ | Global | Small | Free credits | High |

Schema commonality: `scene_id`, `acq_datetime`, `cloud_cover`, `bands`, `geometry`, `lat/lon`, `frp/confidence`.

## 3. Space Weather

| Dataset | Format | Granularity | Update | History | Volume | Limits | Reliability |
| --- | --- | --- | --- | --- | --- | --- | --- |
| NOAA SWPC | JSON | Minute | Real-time | Years | Small | None | High |
| NASA DONKI | JSON | Event | Event | 2010+ | Small | None | High |
| GOES X-ray | JSON | Minute | Real-time | Multi-year | Small | None | High |
| GFZ Kp | File/API | 3-hour | Daily | 1932+ | Small | None | High |
| OMNIWeb | API/File | Hour | Daily | 1963+ | Small-Med | None | High |
| DSCOVR/ACE | JSON | Minute | Real-time | Years | Small | None | Medium |

## 4. Orbital Mechanics

| Dataset | Format | Granularity | Update | History | Volume | Limits | Reliability |
| --- | --- | --- | --- | --- | --- | --- | --- |
| CelesTrak TLE/GP | API/File | Per-object | Daily+ | Current | Small | None | High |
| Space-Track | API | Per-object | Daily+ | Full | Small-Med | Auth + throttling | High |
| SOCRATES | File | Event | Daily | Rolling | Small | None | High |
| JPL Horizons | API/File | On-demand | On-demand | Long | Small | None | High |
| OEM samples | File | Discrete | Static | Static | Small | None | Medium |
| TLE history | File | Per-object | Daily | Full | Med | Auth | High |

## 5. Launch

| Dataset | Format | Granularity | Update | History | Volume | Limits | Reliability |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Launch Library 2 | API | Event | Continuous | Full | Small | 15 req/hr anon | High |
| SpaceX | API | Event | Event | 2006+ | Small | Maintenance mode | Low |
| RocketLaunch.Live | API | Event | Daily | Recent | Small | Free tier cap | Medium |
| NASA reference | File | Static | Rare | Historical | Small | None | Medium |

## 6. Astronomical

| Dataset | Format | Granularity | Update | History | Volume | Limits | Reliability |
| --- | --- | --- | --- | --- | --- | --- | --- |
| NeoWs | API | Daily | Daily | Ongoing | Small | 1000/hr key | High |
| APOD | API | Daily | Daily | 1995+ | Small | Key cap | High |
| MPC | File/API | Daily | Daily | Extensive | Small-Med | None | High |
| JPL SBDB | API | On-demand | Daily | Full | Small | None | High |
| Heavens-Above | File | Event | Daily | N/A | Small | Scrape limits | Low |

## 7. Environmental & Climate

| Dataset | Format | Granularity | Update | History | Volume | Limits | Reliability |
| --- | --- | --- | --- | --- | --- | --- | --- |
| NASA POWER | API | Daily | Daily | 1981+ | Small | None | High |
| ERA5 | API/Bulk | Hourly | ~5 day lag | 1940+ | Large | Queue | High |
| CAMS | API/Bulk | Daily | Daily | 2003+ | Large | Queue | High |
| NOAA CDO | API/Bulk | Daily | Daily | 100+ yr | Med | Token cap | High |
| GFW (forest) | API/Bulk | Weekly | Weekly | 2001+ | Med | Key | Medium |
| OpenAQ | API | Hourly | NRT | 2015+ | Small-Med | None | Medium |
| NOAA Tides | API | Minute | Real-time | Years | Small | None | High |
| OISST | Bulk | Daily | Daily | 1981+ | Med | None | High |

## 8. Simulation

| Dataset | Format | Granularity | Update | History | Volume | Limits | Reliability |
| --- | --- | --- | --- | --- | --- | --- | --- |
| NASA anomaly dataset | File | Per-cycle | Static | Static | Small-Med | None | High |
| sgp4 synthetic | Generated | Configurable | On-run | Synthetic | Small | None | High |
| ISS stream sim | API | Second | Real-time | None | Small | None | Medium |

## Cross References

- Structure analysis: [03-data-structure-analysis.md](./03-data-structure-analysis.md)
- Quality: [04-data-quality-assessment.md](./04-data-quality-assessment.md)

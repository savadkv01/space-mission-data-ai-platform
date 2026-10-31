# Prompt 26 - Space & Galactic 3D Analytics Track (New Domain, Design + Implementation)

# Enterprise Space Mission Data & AI Platform

> **Phase 26 - Space & Galactic 3D Analytics (CelesTrak/SGP4 + ESA Gaia)**
>
> Read `_shared.prompt.md` first. This adds a **new, self-contained domain track**
> (peer to the Earth-Observation, Climate, and Simulation tracks). It spans **two spatial
> scales that share one analytical spine** — a 3D point cloud + spatial density binning +
> motion/velocity vectors + 3D-scatter/heatmap BI:
>
> * **Near-Earth Orbital** (CelesTrak GP + SGP4) — objects around Earth.
> * **Galactic** (ESA Gaia DR3) — stars around the Sun.
>
> It introduces the domain end to end (ingestion → Silver → Gold → serving → BI) as one
> vertical slice.

---

# Objective

You are acting as:

* Principal Data Architect
* Staff Data Engineer
* Analytics Engineer

Stand up a **Space & Galactic 3D Analytics** domain delivering exactly **four use cases**
end to end, in two symmetric pairs (3D map + motion) at two scales:

**Near-Earth Orbital (CelesTrak GP + SGP4 — zero new ingestion dependency)**

1. **UC-O1 — Orbital 3D Mapping**: propagate the active-object GP catalog with SGP4 to
   3D positions (ECI + geodetic) and produce density/structure products (3D point cloud,
   LEO-congestion density heatmaps by altitude shell × inclination band).
2. **UC-O2 — Orbital Regime & Motion Analytics**: derive velocity vectors and orbital
   elements (apogee/perigee, period, inclination) → regime distribution (LEO/MEO/GEO/HEO),
   Gabbard diagram, and velocity-vs-altitude analytics.

**Galactic (ESA Gaia DR3)**

3. **UC-G1 — Milky Way 3D Mapping**: convert Gaia astrometry into 3D galactic positions
   and produce density/structure products (3D point cloud, density heatmaps by galactic
   region and distance shell, HR-diagram aggregate).
4. **UC-G2 — Stellar Motion Analytics**: derive stellar kinematics (proper motion →
   tangential velocity; with radial velocity → full U, V, W space velocity) and produce
   motion-distribution products per galactic region.

The orbital and galactic pairs deliberately mirror each other so the coordinate-frame,
density-binning, and 3D-visualization code is a **shared, reusable spine**.

This is a **DESIGN + IMPLEMENTATION** phase: specs (ADRs, coordinate model, trade-offs)
AND working, tested, runnable code following the medallion pattern.

---

# Scope Guardrails (NON-NEGOTIABLE)

* Deliver ONLY UC-O1, UC-O2, UC-G1, UC-G2. Explicitly **out of scope**: pairwise
  conjunction / close-approach screening (O(n²) — higher risk), collision-probability
  modelling, binary-star / comoving-pair analysis, black-hole candidate screening, any
  ML/anomaly model, and any non-Gaia astronomical source (APOD, NeoWs, Horizons, MPC).
  Do not build them.
* **Orbital source = the existing `CelestrakConnector` GP feed** (already anonymous,
  already landing Bronze). Do NOT add a new orbital connector. **`sgp4` is already a
  dependency** (`ingestion/requirements.txt`, `airflow.Dockerfile`); reuse it — the SGP4
  ECI→geodetic conversion in `ingestion/simulation/orbit_simulator.py` is the reference
  implementation, but propagation here runs analytically over the **real** GP catalog in
  the transformation layer, NOT the synthetic sim track.
* **Galactic source = ESA Gaia Archive TAP/ADQL only** (keyless, anonymous). No paid or
  registration-gated endpoints.
* **Bounded work is mandatory** (16 GB budget):
  * Gaia: every query MUST carry a magnitude cut (e.g. `phot_g_mean_mag < 13`), a
    parallax-quality cut (`parallax_over_error > 5`), an astrometric-quality cut
    (`ruwe < 1.4`), a hard `TOP`/row `LIMIT`, and an optional sky-region (cone or HEALPix)
    filter. Never pull full DR3. Treat unbounded pulls as the OpenAQ OOM class.
  * Orbital: propagate to a **single reference-epoch snapshot** (one position/velocity per
    object), not a long time series. Bound the object set to active-catalog GP groups.
* Reuse existing patterns: `ApiConnector` + JSONL Bronze writer (`ingestion/common/minio_io.py`),
  `settings.py` dataclass config, medallion Bronze→Silver→Gold, DuckDB-first compute,
  Superset for BI.
* New Gaia deps (`astroquery`, `astropy`) MUST be **optional / guarded imports** (mirror
  the Earth-Engine `ee` pattern in `ingestion/api/gee.py`) so the offline suite runs
  without them; isolate the live TAP call behind an injectable `query_fn` seam. The
  orbital side needs **no new dependency**.
* No secrets in code (both sources are keyless); env-driven config; open-source only.

---

# Context

**Orbital.** CelesTrak GP is already ingested to Bronze (`source_code = "CELESTRAK"`,
fields `NORAD_CAT_ID`, `OBJECT_NAME`, `EPOCH`, `INCLINATION`, `ECCENTRICITY`,
`MEAN_MOTION`, `RA_OF_ASC_NODE`, `ARG_OF_PERICENTER`, `MEAN_ANOMALY`, `BSTAR`, …). SGP4
propagates each GP set to an ECI position + velocity at a chosen epoch; ECI→geodetic gives
lat/lon/alt; the mean motion and eccentricity give period, semi-major axis, and
apogee/perigee altitude. Today this data is analytically untapped — SGP4 is only exercised
by the synthetic sim generator.

**Galactic.** Gaia DR3 publishes astrometry (`ra`, `dec`, `parallax`, `pmra`, `pmdec`,
`radial_velocity`) and photometry (`phot_g_mean_mag`, `bp_rp`) for ~1.8 B sources via a
free ADQL/TAP service (ESA `gea.esac.esa.int/tap-server`). Distance ≈ `1000 / parallax[mas]`
parsecs (high-quality parallaxes only).

Both are a **new data shape** for the platform: a 3D point cloud with **no Earth AOI/geo
grid**. The analog to `dim_geo` is a **quantized 3D spatial bin** — an altitude-shell ×
inclination-band grid for orbit, and **HEALPix** sky pixels + galactic Cartesian for stars.
This mirrors — but does not reuse — the EO geospatial model.

---

# Task 1 — Ingestion (Bronze)

**Orbital — reuse, do not rebuild.** Confirm the existing `CelestrakConnector`
(`ingestion/api/celestrak.py`) lands the GP groups needed for a representative active-object
catalog (e.g. `active`, `stations`, `starlink`, `last-30-days`), configured via settings —
no new connector, no new dependency.

**Galactic — new connector.** Implement `ingestion/api/gaia.py`:

* `GaiaConnector(ApiConnector)`, `source_code = "GAIA"`.
* `fetch_raw(...)` submits a **bounded ADQL query** to the Gaia TAP sync endpoint and
  returns `(records: list[dict], "json")`, one record per source, landing via the
  existing Bronze envelope/JSONL writer.
* Query is parameterized by: magnitude limit, `parallax_over_error` min, `ruwe` max,
  `TOP` row cap, and an optional sky region (cone `ra/dec/radius` or HEALPix level+ipix).
  Select only the columns Silver needs.
* Live TAP access goes through an injectable `query_fn` (default = `astroquery.gaia` /
  raw HTTP TAP), guarded so imports never fail offline. Implement `_event_ts` from the
  Gaia data-release reference epoch (J2016.0) — document that these are not wall-clock events.
* Add `GaiaSettings` + `OrbitalSettings` (GP groups, propagation reference-epoch policy) to
  `ingestion/config/settings.py`, and a Gaia pre-flight check in
  `tools/datasource-preflight/` (SKIP if `astroquery` absent; WARN otherwise, like GEE).
* Add an offline unit test with a mocked `query_fn` returning a small fixed star sample.

---

# Task 2 — Silver Entities (`orbit_object`, `obs_star`)

Implement cleaners/propagators (mirror `transformation/batch/*bronze_to_silver.py`;
reuse the SGP4 ECI→geodetic math from `ingestion/simulation/orbit_simulator.py`):

* **`orbit_object`** — grain = 1 / catalogued object (real GP snapshot). Columns:
  `norad_id`, `object_name`, `epoch`, ECI `x/y/z` (km) + velocity `vx/vy/vz` (km/s) at a
  common reference epoch (SGP4), derived geodetic `lat/lon/alt_km`, `speed_kms`,
  `inclination_deg`, `eccentricity`, `period_min`, `semi_major_axis_km`,
  `apogee_alt_km`, `perigee_alt_km`, and `regime` (LEO/MEO/GEO/HEO). Quality rules:
  drop SGP4 propagation errors, bound `alt_km >= 0`, flag decayed/invalid GP.
* **`obs_star`** — grain = 1 / Gaia source. Columns: `source_id`, `ra`, `dec`,
  `parallax`, `parallax_over_error`, `pmra`, `pmdec`, `radial_velocity`,
  `phot_g_mean_mag`, `bp_rp`, `ruwe`, plus derived `distance_pc = 1000/parallax`.
  Quality rules: drop `parallax <= 0`, enforce `parallax_over_error > 5` and `ruwe < 1.4`,
  flag/keep-null missing `radial_velocity` (many sources lack RV).
* Both entities MUST use an explicit Spark schema (no `CANNOT_DETERMINE_TYPE` — reuse the
  `coerce_rows_to_schema` lesson). Document both in `docs/data-modeling/space-3d/`.

---

# Task 3 — Shared 3D Spatial & Coordinate Model (design)

Author `docs/data-modeling/space-3d/` design docs defining ONE 3D spatial model with two
pixelization schemes (the shared spine):

* **Orbital:** `dim_orbit_shell` — quantized altitude-shell × inclination-band grid (the
  `dim_geo` analog for near-Earth space). Choose and justify shell/band widths and the
  LEO/MEO/GEO/HEO regime thresholds. Define ECI and ECI→geodetic frames.
* **Galactic:** `dim_healpix` — sky pixelization (nside/level, ipix, galactic l/b of
  centre). Choose and justify an `nside`. Define equatorial `(ra, dec)` → galactic
  `(l, b)` → galactic Cartesian `(X, Y, Z)` in parsecs (Sun-centered), stating the frame.
* An ADR: **a unified 3D point-cloud + quantized-bin spatial model (two scales) vs reusing
  the Earth geo grid** — why the EO model cannot be reused, and why orbit and galaxy share
  one abstraction with two concrete pixelizations.

---

# Task 4 — Gold Marts (UC-O1/O2 + UC-G1/G2)

Build Gold marts (DuckDB-first; Spark only if a join needs it). Empty marts still write a
schema-only parquet part so serving `read_parquet` globs always resolve.

**UC-O1 — Orbital 3D Mapping**

* `fact_orbit_position` — 1 / object: ECI `x/y/z`, geodetic `lat/lon/alt_km`, `regime`,
  `orbit_shell_id`, `object_name`.
* `kpi_orbit_density_shell` — 1 / altitude-shell × inclination-band: object count, mean
  altitude (the LEO-congestion heatmap).

**UC-O2 — Orbital Regime & Motion Analytics**

* `fact_orbit_kinematics` — 1 / object: `speed_kms`, `period_min`, `inclination_deg`,
  `apogee_alt_km`, `perigee_alt_km`, `eccentricity`, `regime`.
* `agg_gabbard` — apogee/perigee altitude vs orbital period, binned (the Gabbard diagram).
* `kpi_orbit_regime` — 1 / regime: object count, mean altitude, mean speed.

**UC-G1 — Milky Way 3D Mapping**

* `fact_star_position` — 1 / source: galactic `X, Y, Z`, `l`, `b`, `distance_pc`,
  `healpix_id`, `phot_g_mean_mag`, `bp_rp`.
* `kpi_galactic_density_healpix` — 1 / HEALPix cell / distance shell: star count, mean
  magnitude, density (stars per unit volume/solid angle).
* `agg_hr_diagram` — binned counts over (`bp_rp` colour × absolute magnitude
  `M_G = phot_g_mean_mag + 5*log10(parallax/100)`) for the HR diagram.

**UC-G2 — Stellar Motion Analytics**

* `fact_stellar_kinematics` — 1 / source: total proper motion, tangential velocity
  `v_tan = 4.74 * (pm/1000) * distance_pc`, and full `U, V, W` space velocity where RV exists.
* `kpi_kinematics_by_region` — 1 / HEALPix cell: mean/median tangential velocity, velocity
  dispersion, count with full 3D velocity.

Document marts in `docs/data-modeling/space-3d/` (Gold layer + star-schema alignment).

---

# Task 5 — Serving Products

Mirror the existing serving pattern (pure-Python builder canonical, dbt model duplicates,
contracts tested):

* `serving_orbit_map` — pre-denormalized orbital positions + shell density.
* `serving_orbit_regime` — pre-denormalized regime/kinematics + Gabbard inputs.
* `serving_star_map` — pre-denormalized 3D positions + density for the map/heatmap.
* `serving_stellar_kinematics` — pre-denormalized kinematics + per-region rollup.
* Register `orbital` and `galactic` metric blocks in the semantic layer's metric registry
  (do not fork the registry); reuse the certified-dataset governance pattern.

---

# Task 6 — BI (Superset assets-as-code)

Add certified datasets + a **Space & Galactic 3D Analytics** dashboard (two tabs:
*Near-Earth Orbit* and *Milky Way*), assets-as-code YAML under `bi/superset/`, matching
existing UUID/import conventions:

* **Near-Earth Orbit tab:** 3D/deck.gl scatter of ECI positions (the satellite shell);
  altitude-shell × inclination density heatmap; Gabbard diagram; regime-distribution bar;
  velocity-vs-altitude chart.
* **Milky Way tab:** 3D/deck.gl point cloud of galactic `X/Y` (Z colour); HEALPix density
  heatmap; HR-diagram density chart; tangential-velocity distribution + velocity-dispersion
  table.
* Follow the documented Superset asset-bundle import flow (`POST /api/v1/assets/import/`,
  forward-slash zip entries, `chartId`+`uuid` in position_json). Map slices needing a
  runtime token are described in the spec and added post-import (existing policy).

---

# Task 7 — Tests, ADRs, Docs

* Offline unit tests: Gaia connector (mocked `query_fn`); Silver `orbit_object` (SGP4
  propagation + regime classification) and `obs_star` (quality filters + distance); Gold
  (coordinate conversion, kinematics math, density binning, Gabbard/HR binning); serving
  contracts.
* ≥5 ADRs: Gaia-TAP-as-source; bounded-work strategy (Gaia query bounds + orbital
  single-epoch snapshot); unified 3D spatial model (orbit shells + HEALPix); reuse SGP4 for
  real-catalog propagation (vs sim track); DuckDB-first compute.
* Trade-offs: Gaia query bound vs coverage · single-epoch snapshot vs orbital time series ·
  DuckDB vs Spark · parallax-cut vs completeness · pairwise conjunction excluded (O(n²)).
* `docs/data-modeling/space-3d/` doc set ending in a glossary; update `DATA-INVENTORY.md`
  with the new Bronze source (GAIA), the `orbit_object` + `obs_star` Silver entities, Gold
  marts, and serving products.

---

# Deliverables

```
ingestion/api/gaia.py + tests            (orbital reuses existing CelestrakConnector)
transformation/  (orbit_object + obs_star cleaners/propagator + Gold marts + tests)
serving/  (serving_orbit_map, serving_orbit_regime, serving_star_map, serving_stellar_kinematics + dbt + tests)
bi/superset/  (orbital + galactic datasets + Space & Galactic 3D dashboard YAML)
docs/data-modeling/space-3d/  (bronze contract, silver, 3D coordinate model, gold, ADRs, glossary, README)
tools/datasource-preflight/  (Gaia check)
```

# Acceptance Criteria

* SGP4 over the real CelesTrak GP catalog lands `orbit_object` in Silver; a bounded Gaia
  query lands `obs_star` in Bronze/Silver with quality cuts + distance.
* Gold produces the orbital marts (`fact_orbit_position`, `kpi_orbit_density_shell`,
  `fact_orbit_kinematics`, `agg_gabbard`, `kpi_orbit_regime`) and the galactic marts
  (`fact_star_position`, `kpi_galactic_density_healpix`, `agg_hr_diagram`,
  `fact_stellar_kinematics`, `kpi_kinematics_by_region`).
* Serving products build and pass contract tests; offline suite is green **without**
  `astroquery`/`astropy` installed (orbital side needs no extra dep).
* Superset renders the Space & Galactic 3D dashboard (Near-Earth Orbit + Milky Way tabs).
* All work stays within the 16 GB budget (bounded Gaia query, single-epoch orbital snapshot,
  DuckDB-first).

# Definition of Done

An analyst can open the Space & Galactic 3D dashboard and (a) explore the near-Earth
satellite population in 3D with orbital-regime and congestion analytics from the real
CelesTrak GP catalog via SGP4, and (b) explore a bounded slice of the Milky Way in 3D with
stellar-motion analytics from ESA Gaia — both end to end through the medallion. Conjunction
screening, binary-star, black-hole, and ML use cases remain explicitly out of scope.
Stop here.

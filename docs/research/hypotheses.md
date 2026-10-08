# Candidate geological hypotheses — preregistration backlog

## Ranked hypotheses — updated 2026-10-08 (after the holdout run)

Ranking is qualitative (expected opportunity versus implementation cost). It is not a DTI projection and not a slot decision. Band names are from `training_features.tif` (19 float32 bands, read 2026-10-08; owner-mirrored, not organizer-authenticated).

| Rank | Hypothesis | Layers (band names) | Physical signature | Why it could be catalogue-missed | Difference from repo | Cost | Status |
|---|---|---|---|---|---|---|---|
| 1 | Magnetic edge ridge | `rtp` (edge direction), `tmi_hg` (edge strength); NMS ridge of total horizontal gradient | Linear magnetic edges that mark contacts and possibly faults under cover | Magnetic edges show blind contacts; the catalogue lists only mapped traces | Catalogue-free ridge (prior work used an SGMC proxy) | Done (~1 h) | **NEGATIVE** (E1 frozen dense, below matched null); E2 spaced exploratory, CI includes 0. See `evidence/run_card_mag_ridge.json` |
| 2 | Gravity horizontal-gradient ridge | `iso_grav_anom_hg`, `iso_grav_anom_vg` | Density contrasts along linear faults or fault-bounded basins | Same mechanism as rank 1, applied to gravity; may detect structures magnetics misses | Not tested in this repo; the same pipeline and holdout apply | Low (same code path) | **NOT TESTED**. Expect correlation with rank 1; must be run on the same holdout before any slot |
| 3 | Geodetic strain-rate lineaments | `geod_2ndinv`, `geod_shearrate`, `geod_dilaterate` | Concentrated shear or dilation along active structures | Aseismic or blind active faults lack surface mapping | Strain layer is already in the stack; source, licence and resolution not verified here | Medium (source check needed) | **NOT TESTED**. Source provenance unverified |
| 4 | Basement-step / sediment-thickness gradient | `depth_to_base_surf`, `det_elev_slope` | Offsets in basement depth that suggest normal faulting | Blind faults offset basement without a surface trace | Not tested; overlap with catalogue unknown | Low–medium | **NOT TESTED**. Check overlap before use |

Not yet tested and not ranked above: gravity tilt-derivative and Euler deconvolution. Both need a dedicated design. Earlier backlog items (InSAR, isotope/noble gas, thermal, groundwater) remain "not viable now" for lack of free data.

## Gate status

These are **proposals, not findings**. The merged main branch contains owner-mirrored labels and an SGMC raster, a prior H54-A candidate, but not the full numerical training-feature stack or an authenticated DrivenData download. A separate read-only clone of the owner-maintained GEMSDOE template contains a five-part feature bridge; every part and reconstructed-file hash matches that repository's pins, and the cube is structurally varied. This proves byte integrity against owner pins, not organizer provenance. The root template's end-to-end workflow uses spatial blocks; the local whole-segment helper's ignored-buffer bug was fixed in this PR, but the helper is not a complete evaluator. Public sibling artifacts remain an incomplete prior-art registry. Therefore, none of these external-data hypotheses is certified globally untried or viable for a compliant competition experiment, and none has a HOLDOUT-DTI value.

The ranking below is a qualitative research priority (expected opportunity versus implementation burden), not a DTI projection. It is intentionally not a slot-selection decision. All proposals need a pre-score protocol and an official-source/data-availability check before implementation.

## Ranked ideas

### Priority 1 — Time-series InSAR deformation discontinuities near geothermal upflow

- **Layers/data:** Sentinel-1 SAR single-look-complex time series, a validated DEM for topographic phase correction, and independently sourced well/spring locations for interpretation. The current repository contains none of these.
- **Physical signature:** spatially coherent, temporally persistent line-of-sight deformation gradients or phase discontinuities; test whether they align with structural boundaries rather than merely with mapped surface scarps.
- **Why it could expose a missing fault:** active fluid pressure or slip on a blind structure can deform the surface without producing a mapped scarp. Temporal deformation supplies an independent observation family from static gravity/magnetics, radiometrics, LiDAR morphology, and point-temperature predictors.
- **Difference from the accessible prior art:** time-series geodesy and phase-coherence analysis, rather than a new threshold or spacing rule on the existing static raster stack. This is not certified novel across all sibling repositories.
- **Named non-fault mimics:** groundwater pumping/recharge, volcanic deformation, landslides, atmospheric delay, vegetation decorrelation, and processing artifacts.
- **Official free source to check:** Copernicus Data Space Sentinel-1 access (<https://dataspace.copernicus.eu/>) and NASA ASF DAAC Sentinel-1 search (<https://search.asf.alaska.edu/>). Neither source was reachable under this session's network allow-list; availability over the exact footprint and dates is **not checked**. **Not viable now.**
- **Relative expected opportunity / cost:** highest potential among these proposals; very high processing and provenance cost. No numeric expected DTI is claimed.

### Priority 2 — Stable-isotope and noble-gas mixing gradients in springs and wells

- **Layers/data:** spring/well temperature and major-ion chemistry, plus stable isotopes (delta-18O/delta-2H) and/or noble-gas ratios only if those fields are actually present in a trusted official record. The current repository has no such table.
- **Physical signature:** geochemical evidence of deep-circulation mixing and fault-focused upflow, evaluated as spatially connected groups rather than isolated hot points; control for elevation, season, sampling method, and well depth.
- **Why it could expose a missing fault:** deep fluid ascent can mark permeable structures buried beneath basin fill, which surface fault catalogues may not map.
- **Difference from the accessible prior art:** source-water provenance and mixing, not simply proximity to thermal points or a static surface-temperature score. Prior sibling work already explored temperature/chemistry proxies, so only verified isotope/noble-gas fields would constitute a meaningful new information source.
- **Named non-fault mimics:** shallow aquifer mixing, irrigation return flow, evaporation, sampling/assay differences, and lithologic control on water chemistry.
- **Official free source to check:** the user-supplied GDR/DOE submission page for INGENIOUS, <https://gdr.openei.org/submissions/1391>, plus the underlying data package/license. The page and schema were not fetched here; presence of isotope/noble-gas columns and redistribution terms are **not verified**. **Not viable until checked.**
- **Relative expected opportunity / cost:** medium-high scientific opportunity if the fields exist; high data-cleaning and hydrogeochemical interpretation cost. No numeric expected DTI is claimed.

### Priority 3 — Multiseason thermal-inertia and anomaly persistence

- **Layers/data:** cloud-screened, atmospherically corrected Landsat Collection 2 Level-2 surface temperature/reflectance time series, with terrain/land-cover controls. Static thermal and heat proxies have already appeared in accessible sibling prior-art summaries, so temporal persistence is the novelty boundary.
- **Physical signature:** repeatable seasonal amplitude/phase or nighttime/cool-season thermal contrast that remains after topographic, vegetation, albedo, and acquisition-time adjustment.
- **Why it could expose a missing fault:** persistent fluid discharge or shallow hydrothermal alteration may generate a thermal response above a concealed structure without a visible scarp.
- **Difference from the accessible prior art:** a within-pixel seasonal time-series statistic, not a one-date thermal anomaly or a point-temperature-distance field. Global prior-art novelty is not certified.
- **Named non-fault mimics:** surface moisture, irrigation, wildfire, bare-rock albedo, topographic illumination, and sensor/acquisition artifacts.
- **Official free source to check:** USGS Landsat Collection 2 <https://www.usgs.gov/landsat-missions/landsat-collection-2> (link supplied for manual review; not fetched here). Availability of the required temporal coverage and product access is **not checked**. **Not viable now.**
- **Relative expected opportunity / cost:** medium opportunity; high preprocessing and confounder-control cost. No numeric expected DTI is claimed.

### Priority 4 — Groundwater head/discharge anomalies conditioned on structural corridors

- **Layers/data:** time-stamped USGS well levels/spring discharge and precipitation, plus a validated DEM-derived watershed network and only independently verified structural context.
- **Physical signature:** spatially localized, repeatable head/discharge response that is coherent across nearby wells and aligned with a structural corridor, after precipitation and pumping controls.
- **Why it could expose a missing fault:** a blind permeable fault can connect deep and shallow groundwater systems and create a localized hydraulic response without a mapped surface trace.
- **Difference from the accessible prior art:** temporal hydraulic response and source attribution, rather than static terrain lineaments or a single thermal/chemistry measurement. It is not certified globally untried.
- **Named non-fault mimics:** pumping, seasonal recharge, irrigation, basin-wide aquifer boundaries, and well-construction differences.
- **Official free source to check:** USGS National Water Information System / Water Data APIs, <https://waterdata.usgs.gov/nwis>. The endpoint, station density in the study footprint, and license for the needed variables were not checked in this environment. **Not viable now.**
- **Relative expected opportunity / cost:** medium opportunity; high data-linkage and causal-attribution cost. No numeric expected DTI is claimed.

## Selection and experiment budget

No candidate is selected in this audit pass because the owner-pinned bridge is not organizer-authenticated and no complete shared evaluator produces the required whole-segment holdout receipt. The existing H54-A artifact remains a separate, unvalidated prior experiment; the separate GEMSDOE52 cache remains rejected for hash and feature-information failures. No new holdout experiment was run and no weekly slot was touched. A future experiment requires verified data provenance, a complete shared segment-level evaluator, a feature-alone leakage canary, and a powered paired comparison. If any gate fails, keep the candidate blocked rather than fabricating a score.

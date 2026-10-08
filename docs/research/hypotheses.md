# Candidate geological hypotheses — ranked backlog (2026-10-08)

## Ranked hypotheses — updated 2026-10-08 (after the holdout run)

Ranking is qualitative (expected opportunity versus implementation cost). It is not a DTI projection and not a slot decision. Band names are from `training_features.tif` (19 float32 bands, read 2026-10-08; owner-mirrored, not organizer-authenticated).

| Rank | Hypothesis | Layers (band names) | Physical signature | Why it could be catalogue-missed | Difference from repo | Cost | Status |
|---|---|---|---|---|---|---|---|
| 1 | Magnetic edge ridge | `rtp` (edge direction), `tmi_hg` (edge strength); NMS ridge of total horizontal gradient | Linear magnetic edges that mark contacts and possibly faults under cover | Magnetic edges show blind contacts; the catalogue lists only mapped traces | Catalogue-free ridge (prior work used an SGMC proxy) | Done (~1 h) | **NEGATIVE** (E1 frozen dense, below matched null); E2 spaced exploratory, CI includes 0. See `evidence/run_card_mag_ridge.json` |
| 2 | Gravity horizontal-gradient ridge | `iso_grav_anom_hg`, `iso_grav_anom_vg` | Density contrasts along linear faults or fault-bounded basins | Same mechanism as rank 1, applied to gravity; may detect structures magnetics misses | Not tested in this repo; the same pipeline and holdout apply | Low (same code path) | **NOT TESTED**. Expect correlation with rank 1; must be run on the same holdout before any slot |
| 3 | Geodetic strain-rate lineaments | `geod_2ndinv`, `geod_shearrate`, `geod_dilaterate` | Concentrated shear or dilation along active structures | Aseismic or blind active faults lack surface mapping | Strain layer is already in the stack; source, licence and resolution not verified here | Medium (source check needed) | **NOT TESTED**. Source provenance unverified |
| 4 | Basement-step / sediment-thickness gradient | `depth_to_base_surf`, `det_elev_slope` | Offsets in basement depth that suggest normal faulting | Blind faults offset basement without a surface trace | Not tested; overlap with catalogue unknown | Low–medium | **NOT TESTED**. Check overlap before use |

Not yet tested and not ranked above: gravity tilt-derivative and Euler deconvolution. Both need a dedicated design. Earlier backlog items (InSAR, isotope/noble gas, thermal, groundwater) remain "not viable now" for lack of free data.

## Archive note — superseded by the current review

This is a prior shortlist retained for audit history. Source-access statements below reflect an earlier repository review and were not re-fetched in the current review. Use [`hypotheses-20261008.md`](hypotheses-20261008.md) as the current five-hypothesis ranking; it includes current provenance/availability caveats and the second surface-only preflight.

## Decision summary

These are hypotheses, not findings. Expected improvement is **qualitative only**; no DTI projection or leaderboard-score claim is used as an estimate. Public prior-art pages supplied in the project brief are owner-maintained, are not a complete scientific registry, and their scores were not independently confirmed from submission receipts. Therefore novelty means “distinct from the code paths visible in this checkout,” not globally novel.

The highest-priority locally testable idea was short endpoint-tangent continuation from visible catalogue faults. Its score surface was computed from the owner-mirrored label raster and checked against every local registry raster **before dot placement**. The strict lane rule rejected it: 74.79% of surface cells were within 3 px of `r11_greedy_mp`, 99.92% of `r13_lattice_s5_00904`, and 88.53% of `r14_union_tips10_lat6`. The run stopped before holdout scoring and before TIFF creation. No weekly slot was touched.

## Ranked candidates

### 1. Endpoint-tangent continuation beyond visible fault traces — local pilot stopped at lane gate

- **Layers:** visible catalogue-positive pixels in `data/grid/labels.tif`; no external layer. The local labels are hash-pinned owner mirrors, not authenticated in this session from DrivenData.
- **Physical signature:** at the two ends of a sufficiently elongated mapped trace, estimate a local tangent and project a short continuation under cover; suppress output within 300 m of any catalogue fault.
- **Why a missed fault is plausible:** mapped scarps and traces can become visually inconspicuous at alluvial cover boundaries while the structure continues. The continuation is outside the known trace, rather than re-emitting catalogue pixels.
- **Named mimics:** lithologic contacts, intrusive/dike boundaries, erosional truncations, structural intersections, and map-sheet/digitising terminations can look like trace ends.
- **Difference from this checkout:** no endpoint-tangent projector is otherwise implemented. Similar concepts (tips/stepovers) do appear in owner-reported sibling prior art, so global novelty is not claimed.
- **Expected DTI direction / cost:** *low-to-moderate, conditional* recall opportunity at low mass; low-to-medium coding cost. No numerical improvement is estimated.
- **Gate result:** **DUPLICATE — STOP** at pre-placement lane check; no holdout DTI or TIFF was produced. Reproducible receipt: [`endpoint-continuation-preflight.json`](../../evidence/endpoint-continuation-preflight.json).

### 2. Geothermal-expression gate on catalogue-excluded mapped structures

- **Layers:** catalogue-excluded fault traces plus independently recorded spring/well temperature, geochemistry, paleogeothermal deposits, and Quaternary volcanic features from the INGENIOUS GDR package.
- **Physical signature:** require fault-proximal geothermal expression (e.g. a spring/well temperature anomaly or sinter/tufa occurrence), preferably with multiple aligned observations along strike, rather than accepting an isolated nearest hot point.
- **Why a missed fault is plausible:** persistent geothermal discharge can indicate permeable structures beneath basin fill that lack a visible scarp; gating an independent mapped trace may reject old or non-fault map linework.
- **Named mimics:** shallow groundwater mixing, irrigation return flow, lithologic control on water chemistry, young volcanic heat, and biased well/spring sampling.
- **Difference from this checkout:** combines independently observed geothermal expression with the SGMC complement, rather than using SGMC geometry alone. Prior sibling summaries mention point-temperature/chemistry and vent work; novelty is not certified.
- **Expected DTI direction / cost:** *potentially moderate precision gain, unknown recall cost*; medium-to-high data integration and attribution cost. No numerical improvement is estimated.
- **Official-source check:** the public GDR page lists Quaternary faults, volcanics, wells/springs, geochemistry, and paleogeothermal data, with downloadable package entries. The page was inspected through search, but binaries, exact fields, footprint coverage, file-level license, and lineage against the competition labels were not checked. It is **not viable for holdout testing yet**. Source: [GDR INGENIOUS submission 1391](https://gdr.openei.org/submissions/1391).

### 3. Time-series InSAR deformation discontinuities

- **Layers:** Sentinel-1 SLC time series, DEM for topographic phase correction, and independent spring/well context.
- **Physical signature:** spatially coherent, temporally persistent line-of-sight deformation gradients or phase discontinuities aligned with candidate structures.
- **Why a missed fault is plausible:** blind slip or fluid-pressure change can deform the surface without a mapped scarp. It adds an observation family independent of static raster morphology.
- **Named mimics:** groundwater pumping/recharge, volcanic deformation, landslides, atmospheric delay, vegetation decorrelation, and processing artifacts.
- **Difference from this checkout:** time-series geodesy, not a new threshold or dot-spacing rule on existing static layers.
- **Expected DTI direction / cost:** *high scientific upside but highly uncertain*; very high processing and provenance cost. No numerical improvement is estimated.
- **Official-source check:** the Copernicus Data Space states that Sentinel data access is free/open and offers a browser/APIs; user registration is required for data access. NASA ASF search is a second official access route. Exact Sentinel-1 acquisitions over the competition footprint/time interval and processing feasibility were not queried; **not viable for this run**. Sources: [Copernicus Data Space](https://dataspace.copernicus.eu/), [NASA ASF Data Search](https://search.asf.alaska.edu/).

### 4. Multi-season Landsat surface-temperature persistence

- **Layers:** Landsat Collection 2 Level-2 surface temperature/reflectance time series, with terrain, land-cover, and acquisition-time controls.
- **Physical signature:** repeatable seasonal amplitude or phase / nighttime-cool-season contrast after controlling for topography, vegetation, moisture, albedo, and acquisition conditions.
- **Why a missed fault is plausible:** persistent fluid discharge or shallow hydrothermal alteration may create a thermal response above a concealed structure.
- **Named mimics:** surface moisture, irrigation, wildfire, bare-rock albedo, topographic illumination, and scene artifacts.
- **Difference from this checkout:** temporal within-pixel persistence rather than one-date temperature or static distance-to-point features; static thermal ideas already occur in prior-art summaries.
- **Expected DTI direction / cost:** *low-to-moderate, uncertain*; high preprocessing and confounder-control cost. No numerical improvement is estimated.
- **Official-source check:** USGS documents global Collection 2 Level-2 surface-temperature products and a no-cost open-data policy. Exact scene availability over the study footprint, cloud-free seasonal coverage, and the required date range were not checked; **not viable for this run**. Source: [USGS Landsat Collection 2](https://www.usgs.gov/landsat-missions/landsat-collection-2).

### 5. Groundwater head/discharge response conditioned on structure

- **Layers:** time-stamped USGS well levels/spring discharge, precipitation, and independently verified structure context.
- **Physical signature:** repeatable local hydraulic response coherent across nearby wells and aligned with a candidate corridor after accounting for precipitation, pumping, and well construction.
- **Why a missed fault is plausible:** a blind permeable fault may connect deep and shallow aquifers and create a localized hydraulic response without a mapped surface trace.
- **Named mimics:** pumping, seasonal recharge, irrigation, basin aquifer boundaries, and differences in well completion.
- **Difference from this checkout:** temporal hydraulic response and attribution, rather than static lineaments or one-time temperature/chemistry points.
- **Expected DTI direction / cost:** *low-to-moderate, uncertain*; high station matching and causal-attribution cost. No numerical improvement is estimated.
- **Official-source check:** USGS Water Data exposes modern APIs and groundwater field measurements. Station density and time series over the study footprint were not queried; **not viable for this run**. Source: [USGS Water Data](https://waterdata.usgs.gov/).

## Holdout, power, and submission gates

- No candidate received a compliant `HOLDOUT-DTI`; no evaluator version / withheld-positive count / paired 95% CI exists for this run.
- The owner-mirror label total (60,988 positive pixels) is a dataset property, not a withheld sample size or independent-unit count.
- The score gap 0.0028 cannot be classified as signal or noise without the actual holdout variance and effective independent segments. The old SGMC proxy is circular and is not a power analysis for expert labels.
- Before another experiment: resolve the lane-registry blanket failure, authenticate the competition data, obtain the full feature stack and correct sample grid, then use a shared evaluator that withholds whole segments plus a 300 m buffer, derives catalogue features from visible faults only, masks visible faults exactly, runs each feature-alone leakage canary, computes pooled DTI and cluster-bootstrap CI, and writes a frozen run card.
- No weekly submission slot was used or selected. The existing H54-A TIFF is **not approved for upload** under the strict lane rule.

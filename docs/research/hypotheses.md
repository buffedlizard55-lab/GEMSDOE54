# Candidate geological hypotheses — preregistration backlog

## Gate status

These are **proposals, not findings**. This checkout contains no local feature stack or label raster. A separate read-only clone of the owner-maintained GEMSDOE template contains a five-part feature bridge plus labels and sample raster; every part and reconstructed-file hash matches that repository's committed pins, and the feature cube has nonconstant bands. That establishes integrity against owner-maintained pins, not organizer provenance. The inspected shared holdout assigns spatial blocks rather than whole fault segments, so it does not satisfy this project's required hide-and-recover contract. Public sibling artifacts are also an incomplete prior-art registry. Therefore, none of the candidates is certified as globally untried, none is currently viable for a compliant competition experiment, and no candidate has a HOLDOUT-DTI value.

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

No candidate is selected because the current checkout has no local inputs, the owner-pinned mirror is not organizer-authenticated, and the available shared holdout is spatial-block based rather than whole-fault-segment based. The separate GEMSDOE52 cache remains rejected for hash and feature-information failures; the hash-matched GEMSDOE root bridge is retained only as a provenance caveat and structural-audit result. No holdout experiment was run; no weekly slot was touched. The first permissible experiment is the highest-priority hypothesis only after official source access, spatial coverage, license, feature provenance, a compliant shared evaluator, and the leakage canary are verified. If access fails, keep the hypothesis blocked rather than fabricating a raster or score.

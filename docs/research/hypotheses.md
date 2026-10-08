# Candidate geological hypotheses not yet tried (2026-10-08)

Each hypothesis names: the specific layer(s) involved, the physical signature being targeted,
why it should catch a fault *missing* from the USGS/INGENIOUS catalogue rather than one already
in it, and how it differs from anything already implemented in this repo or the registry. Ranked
by expected DTI improvement over implementation cost. H1 was validated on the spatially-blocked
whole-segment holdout this session; the others are proposals with named, obtainability-checked
data sources.

**Ranking key:** expected improvement judged against the corpus holdout best (0.1793, GEMSDOE32
greedy-surface arm on the catalogue-truth proxy) and the public board gap (0.3774 top). Cost =
data acquisition + engineering + compute from this sandbox's 2-core/4 GB environment.

---

## H1 — Catalogue Gap Relay Completion (CGRC) — *run and validated this session*

- **Layers:** competition catalogue mask only (`data/grid/labels.tif`, 60,988 cells, 3,118 kept
  components, 6,747 degree-1 tips).
- **Signature:** relay/stepover geometry — straight lines between facing, strike-compatible
  (≤25°) tips of different catalogue components with an empty gap (100–2,500 m, stepover ≤500 m),
  plus tangent continuations of segment ends (≤2,500 m). Metric-optimal dot emission, one dot per
  300 m kernel width, 200 m catalogue exclusion.
- **Why off-catalogue:** a national compilation misses exactly the low-displacement strands that
  link mapped segments; the gap between two mapped, facing tips is the most-likely-missed geometry
  in the region, and the gap is *by construction* off the catalogue.
- **Differs from repo:** the only registry lane predicting *between* tips. Dotted families emit on
  SGMC traces; tip-stepover emits tangent extensions only; lattices are uniform.
- **Result (v2, post IR-54-021):** HOLDOUT-DTI **0.091536 [0.087617, 0.094855]** (SGMC-corroborated
  arm, the shipped arm), 60,834 withheld positives, 3,118 whole segments, 1.50× mass-matched random
  (0.0610 @32,529 dots); leakage canary clean (max feature AUC 0.523); SGMC arm significantly beats
  pure-catalogue (A−B CI [−0.002163, −0.000204] excludes 0). Verdict **negative** (below corpus holdout
  best 0.1793); TIF generated, format- and lane-clean. The catalogue-truth proxy penalizes off-catalogue
  mass, so the corrected two-sided artefact scores lower on the proxy than the pre-fix one-sided variant
  (0.1091, 2.47×) — the proxy's bias, not a better method (IR-54-021).
- **Key diagnostic:** a 300 m catalogue exclusion collapses the mechanism (0.0753 → 0.0042 on the 1.5 km
  baseline): its operating band is 200–300 m around the catalogue — the same band the dotted family
  empirically validated (0.2600 → 0.2778 prune).

## H2 — Seismicity-prioritized CGRC — *top next candidate*

- **Layers:** H1 geometry (catalogue tips) + earthquake hypocentres: USGS ANSS Comprehensive
  Catalog (ComCat) and the NV relocated catalog. **Obtainability checked:** both are free,
  official, login-free public releases; this sandbox cannot reach their hosts (network allowlist),
  but owner-mirrored copies already exist in a sibling repository
  (`buffedlizard55-lab/GEMSDOE50`: `data/external/usgs_comcat_earthquakes.csv.gz`,
  `data/external/nvreloc_catalog_newmag.txt.gz`, fetchable via codeload), and a fresh pull from
  `earthquake.usgs.gov` on any unrestricted machine is the primary route.
- **Signature:** microseismicity traces *currently active* fault segments. Project hypocentres
  onto CGRC relay/continuation lines; prioritise (and gate) dot placement on lines with seismicity
  within ~500 m.
- **Why off-catalogue:** the catalogue is a static compilation; seismicity is a dynamic,
  independent observation of fault activity. A relay segment that is seismically alive but missing
  from the compilation is exactly the target class.
- **Differs from repo:** GEMSDOE50's h56/h59 used seismicity for "scarp disperse" / "topo
  lineament scatter" surfaces — not as a *prioritisation prior on gap geometry*. No registry
  raster combines seismicity with relay gaps.
- **Risk:** geothermal faults are frequently aseismic (creep); seismicity is a prior, not a
  filter. Cost: medium (two .gz files, vector projection). Expected: +0.01–0.03 holdout if the
  prior is real; unknown board value (seismicity's correlation with the *hidden expert set* is
  unmeasurable locally — the holdout can only test whether it changes recovery of withheld
  catalogue segments, which is a weak proxy for the activity prior).

## H3 — 3DEP 1 m DEM scarp-break transform on gap zones

- **Layers:** USGS 3DEP 1 m DEM (The National Map Elevation; free, official, login-free). The
  competition's own `1m_DEM_links.csv` lists the tiles covering the study area; tiles are ~52 ×
  (5×5 km) public downloads. **Obtainability checked:** reachable from any unrestricted machine;
  blocked from this sandbox (host not on the allowlist).
- **Signature:** a fault scarp is a narrow *break in slope* with a characteristic relief amplitude
  (Hawker–Snoke scarp criterion: scarp relief vs. lineament length). Detect the break (not just
  lineaments) with a signed slope-discontinuity transform, then intersect with the CGRC gap
  surface (H1) and emit dots on gap cells that carry a scarp signature.
- **Why off-catalogue:** DEMs image the ground surface directly, independently of every human
  compilation; young, low-displacement active faults produce scarps before (or without) ever
  entering a map compilation, and scarps are the canonical geothermal-relevant fault expression.
- **Differs from repo:** GEMSDOE46/47 did scarp–*radiometric* fusion; GEMSDOE50 h59 did topo
  *lineament scatter*. A scarp-**break** transform restricted to **gap zones** (H1 ∩ scarp) is a
  new intersection: the lineament scatter ignores the catalogue-tip geometry that anchors H1.
- **Cost:** high (52 tiles × ~50 MB, 1 m resampling, per-tile transforms on 4 GB RAM). Expected:
  highest-value *local-data* hypothesis if scarps align with gap zones; the holdout can test it
  (withheld catalogue segments with scarps are recoverable targets).

## H4 — Learned detector on the official Geodawn feature stack (U-Net path)

- **Layers:** `gems-geodawn-numerical-features.tif` (Geodawn airborne magnetic + radiometric
  derivatives provided by the competition) + `labels.tif`.
- **Signature:** a deep regression of fault-presence probability; the reference solution
  (drivendataorg/gems-prize-reference-solution, U-Net with TverskyLoss(0.2, 0.8)) is the
  organizer-endorsed baseline. Metric-optimal dot emission on the probability surface (break-even
  bar k > 0.2·DTI).
- **Why off-catalogue:** aeromagnetic structure tensor images basement fault structure
  independently of compilation history; faults too young, subtle, or obscured for mappers still
  displace magnetic units.
- **Differs from repo:** GEMSDOE49/50 (h60 "official stack" 50 k dots, "gate_ortho") consumed the
  stack as *hand-crafted gates*, not as a trained probability surface. A trained model +
  metric-optimal emission is the untried corpus path and the most likely explanation of the
  public 0.3221–0.3774 band.
- **Blocker (named, checked):** the feature stack is login-gated on the DrivenData data page
  (verified redirect to login, 2026-10-08). **Specific free, official source needed:** a
  DrivenData account (competition registration is free) to download
  `training_features.tif` / `gems-geodawn-numerical-features.tif` from
  https://www.drivendata.org/competitions/306/competition-doe-gems/data/. Plus a GPU for
  training (or long CPU time for the reference U-Net at 100 m). **Viability: NOT viable from
  this sandbox until an authenticated download is placed in `data/`.**

## H5 — Junction-node splay detection (fluid-pathway nodes)

- **Layers:** catalogue mask only.
- **Signature:** high-angle (30–80°) catalogue fault intersections are damage-concentration
  nodes that focus fluids; emit dots on the *splay* directions: short (≤500 m) off-line segments
  from each junction at the bisector angles of the intersecting strikes, 200 m catalogue
  exclusion, one dot per 300 m.
- **Why off-catalogue:** compilations digitize individual mapped faults; they do not digitize the
  interaction products (splays, relay bridges between crossing strands) that form at junctions —
  and geothermal systems preferentially develop there.
- **Differs from repo:** tip_stepover_r30 targets tip-to-tip stepovers; no registry lane emits
  from intersection nodes. Pure local geometry (low cost), testable on the same holdout
  instrument (withheld segments adjacent to junctions are recoverable).
- **Risk:** junctions are *on* the catalogue; the splay dots must sit in the 200–300 m band to
  carry off-catalogue information, which keeps mass small.

---

## What is NOT listed and why

- *SGMC complement variants* (any re-weighting of the dotted-family surface): lane-occupied by
  nine registry rasters; a new variant would trip the 3-px rule against the dotted family.
- *Pure SGMC or pure continuation surfaces*: lane-occupied (undercomplement, endpoint-continuation
  preflight).
- *Lattice/uniform*: control, lane-occupied (r13), and known to score low.

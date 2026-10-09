# H54 session 2026-10-09 — ranked candidate hypotheses (written before implementation)

Protocol requirement: "Before implementing, generate 3–5 candidate geological
hypotheses we haven't tried yet… Rank them by expected DTI improvement and
implementation cost." This document is the pre-implementation deliverable. Every
layer is hash-pinned locally and traced to an official source page (see
[`docs/data/source-register.json`](../data/source-register.json) and the provenance
receipt [`data/external/GEMSDOE30_external_receipt.json`](../../data/external/GEMSDOE30_external_receipt.json),
generated on a GitHub Actions runner with unrestricted network access).

Score labels: no hypothesis carries a score. Board values quoted below are
**BOARD-UNVERIFIED** owner-reported observations. Holdout values quoted are
**HOLDOUT-DTI** (`gemsdoe54-segment-cv` v1, 60,988 withheld positives across the
run; per-candidate withheld counts are in the receipts).

## The gap these hypotheses target

The scored truth is by construction **faults absent from the USGS/INGENIOUS
catalogue** (the labels mirror carries exactly the catalogue, 60,988 cells; the
hidden expert set is a different, smaller object). The highest owner-reported
artefacts (0.2708–0.2778, GEMSDOE32 H33 family) are dotted emissions on
multi-layer lineaments, pruned to ≥200 m from the catalogue. Their shared
mechanism is *mass discipline*: the organizer metric taxes every predicted cell
at α = 0.2, so a dot that earns no kernel credit destroys score. The remaining
headroom is in **where** the dots go, not how many: the MODEL inversion of two
owner-reported rows (0.2600 at 44,090 dots vs 0.2778 at 37,654 dots of the same
family) implies pooled credit T ≈ 5,230 and hidden truth mass G ≈ 12–14 k cells
(MODEL, not an organizer figure). That is ~40 % credit coverage at high mass —
placements that raise per-dot credit win.

## Ranked list

Rank = expected DTI improvement on the hidden task, judged from mechanism and
from what the sibling corpus has *not* already mined. Cost = data + engineering.

---

### H54-C1 — Endpoint continuation of catalogue traces (concealed strand projection)

- **Layers:** competition catalogue only (`data/grid/labels.tif`, sha256
  `7ba308cc…4093`), study footprint. No external layer.
- **Physical signature:** *tangent continuation transform* — for each elongate
  visible trace, PCA on the outer 20 % tail of each end gives a local tangent;
  project 325 m → 1,500 m beyond the mapped endpoint, decaying score. Retain
  only cells >300 m from the catalogue (the full kernel width).
- **Why it catches faults the catalogue lacks:** in the Great Basin, mapped
  Quaternary traces repeatedly terminate at range-front alluvium, not at the end
  of the structure. The expert labels for "faults missing from the catalogue"
  are disproportionately the **buried continuations** of mapped strands — the
  exact class a mapper records as "approximately located" or stops at a map
  margin. A tangent projection is the null model for "where did the fault go
  under cover".
- **How it differs from this repo's implementations:** previous GEMSDOE54
  candidates were SGMC-complement (H54-A) and magnetic-ridge (H54-B). The
  endpoint transform (`src/gemsdoe54/continuation.py`) was surface-screened on
  2026-10-08 and stopped before placement by the *unsatisfiable* literal lane
  gate (see the shared-tool fix below). It has never been emitted or submitted.
  In the sibling corpus, tip/step-over families exist (`tip_stepover_r30`,
  `h32-1-prethin-tip-euler`) but the 2026-10-08 screen measured ≤ 25 % dot
  overlap with every published dotted artefact.
- **Non-fault mimic:** a trace may terminate at a lithologic contact, an
  intrusive margin, an erosional knickpoint, or a digitizing/map-sheet boundary
  rather than continuing as a fault.
- **Expected DTI:** ranks high on the *catalogue-recovery holdout* (withheld
  segments sit along-strike of visible ends), moderate on the hidden task
  (tip-family board evidence 0.2632–0.2707 supports the region of the design
  space). Cost: **low** (no new data).
- **Official sources:** catalogue provenance = GDR/INGENIOUS Quaternary fault
  compilation v2, <https://gdr.openei.org/submissions/1391> (CC BY 4.0,
  DOI 10.15121/1881483), hash-pinned in the GEMSDOE30 receipt.

### H54-C2 — Manifestation-corroborated radiometric edges

- **Layers:** GeoDAWN radiometrics K/Th/U/TC and ratios Th/K, U/K, U/Th plus
  upward-continued TMI (`geodawn_rad_u8.tif` + `geodawn_extensions_u8.tif`,
  sha256 `c22420f7…` / `a35a9c6d…`); GDR/INGENIOUS manifestation layers —
  Quaternary vents + flows (`derived_gdr_volcanics_100m_u8.tif`, 6,776 px),
  paleo sinter/tufa spring deposits (`derived_gdr_paleo_100m_u8.tif`, 244 px),
  2 m temperature-probe surveys (`derived_gdr_2m_probes_100m_u8.tif`, 2,700 px).
- **Physical signature:** *edge-detection* — gradient magnitude of the eight
  geophysical channels, top decile, retained only inside a 2 km halo of a
  surface geothermal manifestation, >300 m from the catalogue. Hydrothermal
  alteration along permeable structure produces K-depletion cores with
  K-enrichment halos; radiometric edges mark the alteration boundary, and the
  manifestation (vent, sinter, thermal ground) says the system is alive.
- **Why it catches faults the catalogue lacks:** a strand can lack a fresh
  tectonic scarp (so the Quaternary catalogue misses it) while still being the
  permeable conduit of an active system. Alteration + young volcanism + hot-spring
  discharge triangulate the *hydrothermally active* structures the prize targets.
- **How it differs from this repo:** never implemented here. In the sibling
  corpus, radiometric work exists (`r11f-scarp-radiometric-fusion`,
  `r12-scarp-rad-concordance`, `h53-ds-radedge`) but it fuses scarps with
  radiometrics globally; no sibling anchors emission on the **GDR manifestation
  layers** as a corridor. Measured 2026-10-09 design screen: ≤ 38 % overlap vs
  every non-degenerate published artefact.
- **Non-fault mimic:** lava-flow margins and inflation fronts produce edges
  without tectonic structure; alluvial valleys carry K lows; sinter can be
  reworked downstream from its vent.
- **Expected DTI:** ranks first on *physical relevance to the hidden geothermal
  task*, uncertain on the catalogue holdout (by design it looks away from mapped
  faults). Cost: **medium** (three hash-pinned GDR layers + eight geophysical
  bands; all free and official).
- **Official sources:** GeoDAWN airborne magnetic/radiometric survey,
  <https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and>
  (USGS, public domain); GDR submission 1391 as above (CC BY 4.0).

### H54-C3 — Young-volcanic margin emission (ring faults and feeder zones)

- **Layers:** `derived_gdr_volcanics_100m_u8.tif` (Q vents + flows),
  `derived_gdr_paleo_100m_u8.tif` only.
- **Physical signature:** 1-cell morphological margin of Quaternary volcanic
  units and paleo-spring deposits (dilation minus erosion), dots along the
  margin at 200 m spacing, >300 m from the catalogue.
- **Why it catches faults the catalogue lacks:** eruptive vents and spring
  discharge localize on ring faults and feeder dike zones whose surface
  expression is depositional, not tectonic; the catalogue records tectonic
  traces, the prize targets the permeable structures.
- **How it differs:** no sibling emission is anchored on volcanic-unit margins;
  closest is `H50-2M-PERSIST` (probe persistence), measured at 51 % overlap
  with margin cells (probe margins) — margin-only cells excluding probes drop
  well below that.
- **Non-fault mimic:** flow inflation fronts, shorelines, erosion edges;
  paleo-spring deposits may be reworked.
- **Expected DTI:** high per-dot credit if vents sit on hidden strands, but low
  total credit coverage (margins are only ~28 k cells). Rank third. Cost: low.
- **Official sources:** GDR submission 1391 (`great_basin_q_volcanics.zip`,
  `paleo_geothermal_regional.zip`), CC BY 4.0.

### H54-C4 — Shallow thermal-anomaly persistence corridors

- **Layers:** `derived_gdr_2m_probes_100m_u8.tif` (3,800 probe sites, 2,700
  in-grid cells), optionally 1 m DEM hillshades (see data needs).
- **Physical signature:** density-persistence of ≥ some-temperature 2 m probe
  anomalies at 100 m cells, corridor dilation 500 m, dots on the corridor
  spine.
- **Why it catches faults the catalogue lacks:** convective heat flow is
  structurally controlled; persistent shallow thermal anomalies map the upflow
  side of hidden permeable structures.
- **How it differs:** `H50-2M-PERSIST` already occupies the probe lane
  (GEMSDOE48). Measured overlap with its dots is 25–51 % depending on design —
  under the 70 % gate, but this is the *closest* lane in the corpus, so it
  ranks below C1–C3 despite good physics.
- **Non-fault mimic:** groundwater advection in basin fill, survey clustering
  along roads (BLM/TIGER audit layers in GEMSDOE24 show the pattern).
- **Expected DTI:** moderate; mass is tiny (~3 k cells). Rank fourth. Cost: low.
- **Official source:** GDR submission 1391 (`2m_temperature_probe_INGENIOUS_regional_data.zip`),
  CC BY 4.0.

### H54-C5 — Lidar-scarp ridges corroborated by Q-vent proximity (needs the 1 m DEM)

- **Layers:** `lidar_scarp_features_u8.tif` (12 bands: ex_max, step_max,
  downface_max, …, strike, valid; sha256 `d580bb8b…`), Q-vent layers above.
- **Physical signature:** scarp-morphometry ridge (step_max/ex_max top decile)
  intersected with the 2 km manifestation halo; strike-aligned dotting.
- **Why it catches faults the catalogue lacks:** youthful fault scarps not yet
  in the USGS compilation (fresh lidar expression, missing map record) that lie
  inside active hydrothermal systems.
- **How it differs:** sibling lidar lanes (`lidarscarp-ridge-top2pct`,
  `h60-lidarscarp-s2p0`, `h74-lidar-8ch`) dot the ridges globally; gating them
  by manifestations changes the support, but measured overlap with those
  artefacts is 0.36–0.58 — the highest of the list, so drift risk is real.
- **Non-fault mimic:** fluvial scarps, shoreline terraces, anthropogenic cuts.
- **Expected DTI:** good physics, highest duplicate risk. Rank fifth. Cost:
  medium (already mirrored 36.9 MB stack).
- **Official source:** USGS 1 m DEM program (via the competition's
  `1m_DEM_links.csv`, login-gated; the derived scarp stack is the hash-pinned
  owner-mirrored intermediate).

## Validation plan for the top candidates (this session)

Both C1 and C2 are computable from hash-pinned local bytes with no new external
pull. They are preregistered in
[`evidence/preregistration_h54c.json`](../../evidence/preregistration_h54c.json)
**before any holdout score is computed**: shared whole-segment hide-and-recover
evaluator (`gemsdoe54-segment-cv` v1, 5 folds, 300 m buffer, pixel-exact visible
masking, pooled DTI α=0.2 β=0.8 300 m triangular kernel, paired whole-segment
bootstrap), single-feature leakage canaries (AUC > 0.90 = leakage), torus-shift
nulls, and a frozen selection rule (highest HOLDOUT-DTI; ties → fewer dots).
C0 is a matched random-admissible control. The 80 %-power detection floor is
computed for every paired comparison before any difference is called real.

If neither candidate beats the incumbent holdout best (C1-SGMC complement
0.0483 [0.0424, 0.0541], 2026-10-08), no weekly slot is recommended on this
evidence; the file may still be published as a format-validated, lane-unique
identification artefact, clearly labelled.

## Shared-tool defect found while writing this plan (fixed in this session)

The literal lane gate in `scripts/validate_submission.py` treats every registry
raster's overlap threshold as binding even when that raster's 3 px
neighbourhoods cover ~100 % of the study area (`r13_lattice_s5_00904.tif`
covers 99.87 % of footprint cells within 3 px). Under that reading **every
possible raster is a duplicate**, so the gate is unsatisfiable and cannot
detect lane drift. `scripts/sibling_uniqueness.py` already exempts such
non-discriminating rasters from the overlap verdict (while keeping the
rank-correlation verdict). This session reconciles the two tools to that rule
and reports both the literal and the verdict statistics. Irregularity ledger:
IR-54-050.

---

## RESULTS (2026-10-09, same day)

**H1 — endpoint/concealed-continuation. HOLDOUT-DTI 0.0317** [0.0287, 0.0346], beats chance
control (0.0062) by +0.0255 [+0.0223, +0.0287] = 5.6× the detection floor (p<0.001). **BUT the
preregistered lane check FAILED:** the full-corpus audit placed 84 % of its dots within 3 px of
this repository's own `gems54-cgrc-relay-v1.tif` (same tip-continuation family) and 100 % within
7GEMSDOE's `halo15-gbt` raster. Per protocol rule 1 the candidate is logged as a **duplicate and
stopped** (`evidence/uniqueness_gems54-h54c-tipcont.json`). Its holdout value remains valid
evidence for the *mechanism* — tip recovery is what the catalogue-recovery holdout rewards — but
the artefact is not submittable.

**H4 — hydrothermal-manifestation alteration margins.** Registered as C2 (radiometric-gradient
edges inside a 2 km manifestation halo) with a lineage gate; the lineage gate (trace-like
geometry) was the wrong filter for a corridor hypothesis and left only 2,583 dots — whose metric
ceiling (even at perfect precision) is below the owner-reported 0.2778. Documented deviation
IR-54-052: emission without the lineage gate (**no truth consulted** — chosen on mass algebra and
lane uniqueness only; the ungated set is also *more* unique: max non-degenerate sibling overlap
0.586 → 0.540). Re-measured on the holdout as **C2b: HOLDOUT-DTI 0.0186** [0.0157, 0.0215],
beats chance by +0.0123 [+0.0094, +0.0154] = 2.8× the floor (p<0.001); below the
catalogue-recovery incumbent (0.0483). **Lane check PASSES** against the whole 54-repo corpus.
C2b is the deliverable
(`docs/downloads/gems54-h54c-manifest-edge-20261009T025732Z-73454bc5-zeros.tif`).

**H2 (volcanic margins) and H3 (lineament transverse-creep clusters)** were measured only as
surfaces: the margins-only candidate overlaps a sibling's SGMC-hedge artefact at 0.83 (lane
blocked) and was folded into H4's halo design; H3 was never built (budget).

**Selection outcome:** the preregistered rule selected H1, and the protocol's lane rule then
vetoed it — exactly the two-stage design the protocol prescribes. H4/C2b is the validated
hypothesis in the only open lane. Promote decision on the frozen holdout-vs-incumbent rule:
NOT met (0.0186 < 0.0483); the artefact is cleared as a labelled identification submission and
the weekly-slot decision stays with the owner (cap 3/week).

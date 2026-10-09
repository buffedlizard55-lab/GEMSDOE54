# Run 2 summary (branch `arena/b479b5ba-gemsdoe54`, 2026-10-08)

This file holds the run-2 status, holdout, detection-floor, 0.2778, hypothesis and protocol sections. It is linked from the README. Main's 2026-10-09 review is the README's first status block. Both sessions agree that no file is cleared.

---

## ⬇️ SUBMISSION STATUS — read this first (updated 2026-10-08, run 2)

**OK to download: YES, for review.** [`docs/downloads/gems54-own-visible-hgb-q97.tif`](docs/downloads/gems54-own-visible-hgb-q97.tif) is this repository's own model output. It passes the format validator. It has 16,183 positive dots, 131,248 bytes, SHA-256 `04c201817c3ca39d1ea09e776d8d1e248f98fe578e0ddd2826835fe4bbe7883a`.

**OK to submit: NO.** Verdict **NEGATIVE** ([run card](docs/data/run-card.json)):
1. The holdout does not beat the current best. Learned model C4 0.0465 [0.0400, 0.0531] against SGMC complement C1 0.0483 [0.0424, 0.0541]. Paired C4 − C1 = −0.0018 [−0.0103, +0.0063].
2. The literal lane gate reports **DUPLICATE - STOP** against three dense registry rasters on both the pre-placement surface and the final dots (r11 81.8 % / 82.8 %, r13 98.6 % / 97.1 %, r14 79.8 % / 79.0 %). The 70 % test cannot discriminate there (IR-54-090).
3. The full sibling scan (1,194 grid-aligned rasters, 54 repositories) also **FAILS** on the literal rule. 225 rasters exceed 70 % overlap: 115 dense (degenerate) and 110 not dense. Max |ρ| is 0.106. The non-dense overlaps are about 3× chance (IR-54-097; receipts [`evidence/uniqueness_gems54-own-visible-hgb-q97.json`](evidence/uniqueness_gems54-own-visible-hgb-q97.json) and [`evidence/uniqueness_own_visible_rows_over70.json`](evidence/uniqueness_own_visible_rows_over70.json)).

No weekly slot is recommended, and none is selected here.

| File | Score (HOLDOUT-DTI, catalogue recovery) | Lane (literal) | Decision |
|---|---|---|---|
| [`gems54-own-visible-hgb-q97.tif`](docs/downloads/gems54-own-visible-hgb-q97.tif) (this run, own learned model) · name `gems54-own-visible-hgb-q97` | 0.0465 [0.0400, 0.0531]; tie with C1 (paired −0.0018) | DUPLICATE-STOP (dense rasters) | **Download for review. Do not submit.** |
| [`gems54-undercomplement-q200.tif`](docs/downloads/gems54-undercomplement-q200.tif) (H54-A, SGMC complement, archive) | 0.0483 [0.0424, 0.0541] (holdout best) | FAIL: 100 % of dots within 3 px of GEMSDOE3 `gapfinder-v2-sgmc-gap` | Archive only. Do not upload. |
| [`gems54-magedge-hgrad-ridge.tif`](docs/downloads/gems54-magedge-hgrad-ridge.tif) (H54-B, archive) | 0.0148 [0.0118, 0.0180] | FAIL | Archive only. Do not upload. |

**Submission name and note (this file, ≤140 characters).** Name: `gems54-own-visible-hgb-q97`. Note (123 characters): *Own model, not a copy: visible-only boosted fault probability, 19 bands + gradients, top 3% cells, 200 m dots. NOT CLEARED.*

**Official rules.** Submit only your own model's single-band GeoTIFF (§3.2; original work, A.5(1)). You must be eligible (§1.3) and sign the certification. Disclose generative-AI use (§3.2). Three submissions per week at most (§3.2, §3.4). Copying another team's file is not permitted, and this includes every GEMSDOE sibling artefact.

**Score labels.** `HOLDOUT-DTI` = local whole-segment holdout with evaluator `gemsdoe54-segment-cv` v2, withheld-positive count and paired 95 % CI. `ORGANIZER-CONFIRMED` = none. `BOARD-UNVERIFIED` = board values shown on the public page or supplied by the user. `MODEL` = inference. Projections are never scores.

**Step-by-step, and the one-page summary:** [`docs/run2/executive-summary.html`](docs/run2/executive-summary.html) · site entry point [`docs/index.html`](docs/index.html).

---

## Holdout results (run 2) — HOLDOUT-DTI, evaluator `gemsdoe54-segment-cv` v2

Receipt: [`evidence/holdout_segment_cv_run2_variant.json`](evidence/holdout_segment_cv_run2_variant.json). Command: `python scripts/holdout_segment_cv.py --features <bridge tif> --hypotheses --out evidence/holdout_segment_cv_run2_variant.json`. Design: 3,199 whole catalogue segments, 5 folds, 60,988 withheld positives, 300 m collar, visible-only features, organizer DTI (α 0.2, β 0.8, 300 m kernel), paired segment-cluster bootstrap (1,000 replicates), 30 torus-shift nulls, canary at AUC 0.90.

| Candidate | Pooled DTI | 95 % CI | Dots |
|---|---:|---|---:|
| C0 random admissible (chance) | 0.0104 | [0.0091, 0.0117] | 85,867 |
| **C1 SGMC state-map complement (holdout best; sibling-occupied family)** | **0.0483** | [0.0424, 0.0541] | 81,584 |
| C2 geodetic shear-rate ridge | 0.0098 | [0.0072, 0.0128] | 70,950 |
| C3 magnetic horizontal-gradient ridge | 0.0148 | [0.0118, 0.0180] | 88,090 |
| **C4 visible-only learned probability (this run's file)** | **0.0465** | [0.0400, 0.0531] | 75,562 |
| C5 H1 cross-gradient (magnetic × gravity) | 0.0128 | [0.0103, 0.0157] | 79,799 |
| C6 H2 basement-step gradient | 0.0097 | [0.0072, 0.0125] | 89,031 |

Paired: C4 − C1 −0.0018 [−0.0103, +0.0063] (tie; does not beat) · C4 − C0 +0.0361 [+0.0295, +0.0425] · C5 − C1 −0.0356 [−0.0421, −0.0287] · C5 − C0 +0.0024 [−0.0004, +0.0054] · C6 − C0 −0.0007 [−0.0035, +0.0025].

Reproducibility: C0–C3 match the run-1 v1 receipt exactly (point and CI). Canary: learned-model AUC max 0.822 (clear); single-feature max 0.594; distance to visible catalogue 0.756 (withholding artefact); SGMC layer 0.526. No flags.

**Limitation (IR-54-083).** These are catalogue-recovery numbers. The organizer's hidden set is new faults outside the catalogue, so no local number measures that objective.

---

## Detection floor — the 0.2778 vs 0.2750 question

Generated by [`scripts/power_floor_report.py`](scripts/power_floor_report.py) → [`evidence/power_floor_segment_cv_v2.json`](evidence/power_floor_segment_cv_v2.json). Full note: [`docs/run2/power-analysis.md`](docs/run2/power-analysis.md).

- Cohen (1988), α 0.05 two-sided, power 0.80, z = 2.8016.
- **Pixel-IID** with 60,988 positives: d_min = 0.0113. **Invalid for this design** (pixels inside a fault are dependent; the pixel count overstates information by about 4.4× in d).
- **Segment units** (3,199): d_min = **0.0495** (0.111 per fold).
- Paired MDE in DTI units (2.80 × SE): 0.0043 (smallest, C5 − C0) to 0.0121 (C4 − C1). A 0.0028 gap needs 7,635 to 60,073 independent units to clear the floor.
- **Decision: 0.0028 is inside the detection floor.** No ranking claim between 0.2778 and 0.2750 is supported. Caveats: the public split's unit count is unpublished; near-identical dot sets could have smaller paired SE; the 0.2750 raster is not in the registry, so that pair cannot be classified.

---

## The 0.2778 entry (GEMSDOE32 H33-2-B2) — verified mechanism, not a verified score

Site page: [`docs/run2/top-artefact.html`](docs/run2/top-artefact.html) · check: [`scripts/top_artefact_check.py`](scripts/top_artefact_check.py) → [`evidence/top_artefact_check.json`](evidence/top_artefact_check.json).

- **The brief's "highest score" claim is wrong.** On the displayed board, 0.2778 is rank 13, the top is 0.3774 at rank 1, and 0.3195 is at rank 7. 0.2778 is the **highest published value among the 15 GEMSDOE registry artefacts**.
- **Mechanism (VERIFIED on the rasters).** The child `dotted_b2_prune_02778` (37,654 dots) equals its parent `dotted_d2_8_02708` (40,199 dots) minus exactly the 2,545 parent dots within 2 px (200 m) of a USGS catalogue fault. None of those dots is kept. The kept child has 5.8 % of its dots within 300 m of the catalogue, against 11.7 % for the parent.
- **Why it helps under the metric.** DTI = TP / (TP + 0.2 FP + 0.8 FN). Round-1 truth is new faults only, so a dot within 200 m of a known fault earns credit only from a new fault within 300 m. Removing such dots lowers FP without costing TP.
- **MODEL (depends on unverified board values).** If the removed dots earned zero credit, the two board values imply a public denominator of about 20,200.
- **Can we beat 0.2778?** **Not demonstrated.** No file here has a board score. The holdout measures catalogue recovery and cannot rank files against 0.2778. The only holdout-tied file fails the literal lane gate. A stricter prune (for example 300 m) would need a new experiment; this session's three-experiment budget is spent.

---

## Hypotheses (ranked; the top one validated before any slot use)

Full write-up: [`docs/research/hypotheses-20261008.md`](docs/research/hypotheses-20261008.md) · site: [`docs/run2/hypotheses.html`](docs/run2/hypotheses.html).

| # | Hypothesis (layers) | Signature | Why it could catch a missing fault | Difference from repo | Cost | Status |
|---|---|---|---|---|---|---|
| 1 | Cross-gradient corroboration (`tmi_hg` × `iso_grav_anom_hg`) | edge in magnetic and gravity gradients at one place | density and magnetisation step with no scarp | adds a second independent family (C3 is magnetic only) | low | **Tested, negative** (C5 0.0128; vs C1 −0.0356) |
| 2 | Visible-only learned probability (19 bands + 5 gradient bands) | learned multi-family signature | combines weak signals | not SGMC, not a single ridge | medium (~2 min/fold) | **Tested, tie with C1, not better** (C4 0.0465; paired −0.0018) |
| 3 | Basement-step gradient (`depth_to_base_surf`) | step in basement depth | basin-bounding normal faults | new layer | low | **Tested, chance** (C6 0.0097) |
| 4 | 1 m DEM scarp curvature (USGS 3DEP) | paired slope breaks at several scales | young scarps at native resolution | native resolution | high | **Not tested.** Data not in sandbox. Free official source: USGS 3DEP (not reachable; not checked). |
| 5 | Sentinel-1 InSAR deformation discontinuities | persistent line-of-sight gradients | active slip on blind structures | no radar time series | very high | **Not tested.** Free official sources: NASA ASF DAAC, Copernicus Data Space (not reachable; not checked). |

---

## Parallel-run protocol — what was run

- **Feature stack.** Owner bridge at commit `dcbbb192…`, reassembled from five shards. SHA-256 `4371c82e…` matches the owner's pin. Not organizer-authenticated (IR-54-011, IR-54-043). Kept in `/tmp`, outside the repository.
- **Evaluator.** The shared `scripts/holdout_segment_cv.py` gained `--hypotheses` (v2). Scoring, folds, bootstrap and canary are unchanged. The bootstrap was made exact but faster, and the KD-tree is capped at the kernel radius (IR-54-091). The change is fixed once in the template and reported.
- **Writer.** `gemsdoe54.grid.write_submission` (float32, values in [0, 1] in the footprint, NaN outside, NaN nodata). The build is byte-reproducible (SHA-256 identical on rebuild).
- **Lane.** Literal rule (|ρ| ≤ 0.90 and ≤ 70 % of dots within 3 px of any registry raster), checked on the pre-placement surface and on the final dots. Also the full scan of 1,194 grid-aligned rasters (IR-54-097): FAIL.
- **Canary.** Model AUC max 0.822 over folds (≤ 0.90, clear).
- **Budget.** Three experiments, one per hypothesis (H1, H2, H3, one v2 run). About one hour of wall time from the first holdout launch. The first v2 attempt was stopped during the bootstrap (about 20 minutes in) and rerun after the exact speed-up (IR-54-091). **Exhausted.** No further tuning was done.
- **Run card.** [`docs/data/run-card.json`](docs/data/run-card.json), generated from receipts by [`scripts/make_parallel_run_card.py`](scripts/make_parallel_run_card.py). Verdict NEGATIVE.
- **Slots.** None used. None selected.
- **Tests.** 84 pass ([`tests/test_hypotheses.py`](tests/test_hypotheses.py), [`tests/test_segment_cv.py`](tests/test_segment_cv.py) updated to the new contract).

---

## Remaining work and limitations

1. **A candidate that beats 0.0483 with a paired CI above zero, in a lane no sibling occupies.** Not achieved.
2. **Organizer answers.** Scoring scope (IR-54-084). The exact "[0, 1]" rule and the portal error (IR-54-088). Label and feature licence (IR-54-031, IR-54-092).
3. **Lane rule.** The literal 70 % test is degenerate for dense rasters (IR-54-090). A coverage-adjusted rule needs owner or organizer approval. It is not changed here.
4. **Full sibling scan.** Done: FAIL (225 rasters above 70 %). A different lane is needed for any unique file (IR-54-097).
5. **Holdout target.** Catalogue recovery, not new faults (IR-54-083). The C1 advantage may partly come from SGMC lines near catalogue faults (IR-54-094 covers training negatives; the twin-geometry question is open).
6. **Untested hypotheses 4 and 5** need data from free official sources, not reachable from this sandbox.
7. **Submission count and eligibility** cannot be checked without a DrivenData login (IR-54-040).
8. **Feature band list does not match the official description** (IR-54-086). The reference notebook's channel-4 comment conflicts with the bridge order (IR-54-087).

Full irregularity ledger: [`docs/irregularities.html`](docs/irregularities.html) · [`docs/audit/irregularities.md`](docs/audit/irregularities.md).

---


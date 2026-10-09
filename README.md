# GEMSDOE54 — GEMS Prize submission repository

> **Read this file first, every session.** It holds the standing project charter (§1, the full brief, kept verbatim), the evidence limitations, the current status and the explicit download and upload decisions.

---

## ⬇️ SUBMISSION STATUS — read this first (updated 2026-10-08, run 2)

**OK to download: YES, for review.** [`docs/downloads/gems54-own-visible-hgb-q97.tif`](docs/downloads/gems54-own-visible-hgb-q97.tif) is this repository's own model output. It passes the format validator. It has 16,183 positive dots, 131,248 bytes, SHA-256 `04c201817c3ca39d1ea09e776d8d1e248f98fe578e0ddd2826835fe4bbe7883a`.

**OK to submit: NO.** Verdict **NEGATIVE** ([run card](docs/data/run-card.json)):
1. The holdout does not beat the current best. Learned model C4 0.0465 [0.0400, 0.0531] against SGMC complement C1 0.0483 [0.0424, 0.0541]. Paired C4 − C1 = −0.0018 [−0.0103, +0.0063].
2. The literal lane gate reports **DUPLICATE - STOP** against three dense registry rasters on both the pre-placement surface and the final dots (r11 81.8 % / 82.8 %, r13 98.6 % / 97.1 %, r14 79.8 % / 79.0 %). The 70 % test cannot discriminate there (IR-54-057).
3. The full sibling scan (1,194 grid-aligned rasters, 54 repositories) also **FAILS** on the literal rule. 225 rasters exceed 70 % overlap: 115 dense (degenerate) and 110 not dense. Max |ρ| is 0.106. The non-dense overlaps are about 3× chance (IR-54-064; receipts [`evidence/uniqueness_gems54-own-visible-hgb-q97.json`](evidence/uniqueness_gems54-own-visible-hgb-q97.json) and [`evidence/uniqueness_own_visible_rows_over70.json`](evidence/uniqueness_own_visible_rows_over70.json)).

No weekly slot is recommended, and none is selected here.

| File | Score (HOLDOUT-DTI, catalogue recovery) | Lane (literal) | Decision |
|---|---|---|---|
| [`gems54-own-visible-hgb-q97.tif`](docs/downloads/gems54-own-visible-hgb-q97.tif) (this run, own learned model) · name `gems54-own-visible-hgb-q97` | 0.0465 [0.0400, 0.0531]; tie with C1 (paired −0.0018) | DUPLICATE-STOP (dense rasters) | **Download for review. Do not submit.** |
| [`gems54-undercomplement-q200.tif`](docs/downloads/gems54-undercomplement-q200.tif) (H54-A, SGMC complement, archive) | 0.0483 [0.0424, 0.0541] (holdout best) | FAIL: 100 % of dots within 3 px of GEMSDOE3 `gapfinder-v2-sgmc-gap` | Archive only. Do not upload. |
| [`gems54-magedge-hgrad-ridge.tif`](docs/downloads/gems54-magedge-hgrad-ridge.tif) (H54-B, archive) | 0.0148 [0.0118, 0.0180] | FAIL | Archive only. Do not upload. |

**Submission name and note (this file, ≤140 characters).** Name: `gems54-own-visible-hgb-q97`. Note (123 characters): *Own model, not a copy: visible-only boosted fault probability, 19 bands + gradients, top 3% cells, 200 m dots. NOT CLEARED.*

**Official rules.** Submit only your own model's single-band GeoTIFF (§3.2; original work, A.5(1)). You must be eligible (§1.3) and sign the certification. Disclose generative-AI use (§3.2). Three submissions per week at most (§3.2, §3.4). Copying another team's file is not permitted, and this includes every GEMSDOE sibling artefact.

**Score labels.** `HOLDOUT-DTI` = local whole-segment holdout with evaluator `gemsdoe54-segment-cv` v2, withheld-positive count and paired 95 % CI. `ORGANIZER-CONFIRMED` = none. `BOARD-UNVERIFIED` = board values shown on the public page or supplied by the user. `MODEL` = inference. Projections are never scores.

**Step-by-step, and the one-page summary:** [`docs/executive-summary.html`](docs/executive-summary.html) · site entry point [`docs/index.html`](docs/index.html).

---

## Holdout results (run 2) — HOLDOUT-DTI, evaluator `gemsdoe54-segment-cv` v2

Receipt: [`evidence/holdout_segment_cv_v2.json`](evidence/holdout_segment_cv_v2.json). Command: `python scripts/holdout_segment_cv.py --features <bridge tif> --hypotheses --out evidence/holdout_segment_cv_v2.json`. Design: 3,199 whole catalogue segments, 5 folds, 60,988 withheld positives, 300 m collar, visible-only features, organizer DTI (α 0.2, β 0.8, 300 m kernel), paired segment-cluster bootstrap (1,000 replicates), 30 torus-shift nulls, canary at AUC 0.90.

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

**Limitation (IR-54-050).** These are catalogue-recovery numbers. The organizer's hidden set is new faults outside the catalogue, so no local number measures that objective.

---

## Detection floor — the 0.2778 vs 0.2750 question

Generated by [`scripts/power_floor_report.py`](scripts/power_floor_report.py) → [`evidence/power_floor_segment_cv_v2.json`](evidence/power_floor_segment_cv_v2.json). Full note: [`docs/research/power-analysis.md`](docs/research/power-analysis.md).

- Cohen (1988), α 0.05 two-sided, power 0.80, z = 2.8016.
- **Pixel-IID** with 60,988 positives: d_min = 0.0113. **Invalid for this design** (pixels inside a fault are dependent; the pixel count overstates information by about 4.4× in d).
- **Segment units** (3,199): d_min = **0.0495** (0.111 per fold).
- Paired MDE in DTI units (2.80 × SE): 0.0043 (smallest, C5 − C0) to 0.0121 (C4 − C1). A 0.0028 gap needs 7,635 to 60,073 independent units to clear the floor.
- **Decision: 0.0028 is inside the detection floor.** No ranking claim between 0.2778 and 0.2750 is supported. Caveats: the public split's unit count is unpublished; near-identical dot sets could have smaller paired SE; the 0.2750 raster is not in the registry, so that pair cannot be classified.

---

## The 0.2778 entry (GEMSDOE32 H33-2-B2) — verified mechanism, not a verified score

Site page: [`docs/top-artefact.html`](docs/top-artefact.html) · check: [`scripts/top_artefact_check.py`](scripts/top_artefact_check.py) → [`evidence/top_artefact_check.json`](evidence/top_artefact_check.json).

- **The brief's "highest score" claim is wrong.** On the displayed board, 0.2778 is rank 13, the top is 0.3774 at rank 1, and 0.3195 is at rank 7. 0.2778 is the **highest published value among the 15 GEMSDOE registry artefacts**.
- **Mechanism (VERIFIED on the rasters).** The child `dotted_b2_prune_02778` (37,654 dots) equals its parent `dotted_d2_8_02708` (40,199 dots) minus exactly the 2,545 parent dots within 2 px (200 m) of a USGS catalogue fault. None of those dots is kept. The kept child has 5.8 % of its dots within 300 m of the catalogue, against 11.7 % for the parent.
- **Why it helps under the metric.** DTI = TP / (TP + 0.2 FP + 0.8 FN). Round-1 truth is new faults only, so a dot within 200 m of a known fault earns credit only from a new fault within 300 m. Removing such dots lowers FP without costing TP.
- **MODEL (depends on unverified board values).** If the removed dots earned zero credit, the two board values imply a public denominator of about 20,200.
- **Can we beat 0.2778?** **Not demonstrated.** No file here has a board score. The holdout measures catalogue recovery and cannot rank files against 0.2778. The only holdout-tied file fails the literal lane gate. A stricter prune (for example 300 m) would need a new experiment; this session's three-experiment budget is spent.

---

## Hypotheses (ranked; the top one validated before any slot use)

Full write-up: [`docs/research/hypotheses-20261008.md`](docs/research/hypotheses-20261008.md) · site: [`docs/hypotheses.html`](docs/hypotheses.html).

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
- **Evaluator.** The shared `scripts/holdout_segment_cv.py` gained `--hypotheses` (v2). Scoring, folds, bootstrap and canary are unchanged. The bootstrap was made exact but faster, and the KD-tree is capped at the kernel radius (IR-54-058). The change is fixed once in the template and reported.
- **Writer.** `gemsdoe54.grid.write_submission` (float32, values in [0, 1] in the footprint, NaN outside, NaN nodata). The build is byte-reproducible (SHA-256 identical on rebuild).
- **Lane.** Literal rule (|ρ| ≤ 0.90 and ≤ 70 % of dots within 3 px of any registry raster), checked on the pre-placement surface and on the final dots. Also the full scan of 1,194 grid-aligned rasters (IR-54-064): FAIL.
- **Canary.** Model AUC max 0.822 over folds (≤ 0.90, clear).
- **Budget.** Three experiments, one per hypothesis (H1, H2, H3, one v2 run). About one hour of wall time from the first holdout launch. The first v2 attempt was stopped during the bootstrap (about 20 minutes in) and rerun after the exact speed-up (IR-54-058). **Exhausted.** No further tuning was done.
- **Run card.** [`docs/data/run-card.json`](docs/data/run-card.json), generated from receipts by [`scripts/make_parallel_run_card.py`](scripts/make_parallel_run_card.py). Verdict NEGATIVE.
- **Slots.** None used. None selected.
- **Tests.** 84 pass ([`tests/test_hypotheses.py`](tests/test_hypotheses.py), [`tests/test_segment_cv.py`](tests/test_segment_cv.py) updated to the new contract).

---

## Remaining work and limitations

1. **A candidate that beats 0.0483 with a paired CI above zero, in a lane no sibling occupies.** Not achieved.
2. **Organizer answers.** Scoring scope (IR-54-051). The exact "[0, 1]" rule and the portal error (IR-54-055). Label and feature licence (IR-54-031, IR-54-059).
3. **Lane rule.** The literal 70 % test is degenerate for dense rasters (IR-54-057). A coverage-adjusted rule needs owner or organizer approval. It is not changed here.
4. **Full sibling scan.** Done: FAIL (225 rasters above 70 %). A different lane is needed for any unique file (IR-54-064).
5. **Holdout target.** Catalogue recovery, not new faults (IR-54-050). The C1 advantage may partly come from SGMC lines near catalogue faults (IR-54-061 covers training negatives; the twin-geometry question is open).
6. **Untested hypotheses 4 and 5** need data from free official sources, not reachable from this sandbox.
7. **Submission count and eligibility** cannot be checked without a DrivenData login (IR-54-040).
8. **Feature band list does not match the official description** (IR-54-053). The reference notebook's channel-4 comment conflicts with the bridge order (IR-54-054).

Full irregularity ledger: [`docs/irregularities.html`](docs/irregularities.html) · [`docs/audit/irregularities.md`](docs/audit/irregularities.md).

---

## Earlier status (run 1, 2026-10-08 — superseded; kept for audit)

### ⬇️ SUBMISSION STATUS — read this before anything else (updated 2026-10-08)

**Verdict: no file in this repository is cleared for upload.** Both GeoTIFFs below are format-valid, but neither passes the uniqueness requirement. The executive summary is at [`docs/submit-verdict.html`](docs/submit-verdict.html).

| File | Holdout (HOLDOUT-DTI, whole-segment) | Lane / uniqueness | Run card |
|---|---|---|---|
| [`docs/downloads/gems54-undercomplement-q200.tif`](docs/downloads/gems54-undercomplement-q200.tif) (H54-A, SGMC complement) · SHA-256 `b430615a…efd8` · 15,907 dots | **0.0483** [0.0424, 0.0541] (best tested; control 0.0104) | **FAIL.** 100 % of its dots lie within 3 px of GEMSDOE3's `gapfinder-v2-sgmc-gap` (ρ 0.51) | [`registry/run_card_v2_h54a.json`](registry/run_card_v2_h54a.json): negative |
| [`docs/downloads/gems54-magedge-hgrad-ridge.tif`](docs/downloads/gems54-magedge-hgrad-ridge.tif) (H54-B, magnetic gradient ridge) · SHA-256 `6d086c09…8d9e` · 19,197 dots | 0.0148 [0.0118, 0.0180] (beats control, below H54-A) | **FAIL.** 81.6 % overlap with GEMSDOE40 `h8-asa-spi-depthkde`; 75.7 % with GEMSDOE46 `dfa-corroborated` | [`registry/run_card_v2_magedge.json`](registry/run_card_v2_magedge.json): negative |

**Official rules (verified verbatim, [`docs/rules-gate.html`](docs/rules-gate.html)).** You may submit *your own model's* single-band GeoTIFF (§3.2; original work, A.5(1)) if you are eligible (§1.3) and you sign the certification (§1.3, A.1). You must disclose generative-AI use in the narrative (§3.2). Three submissions per week at most (§3.2, §3.4). Copying another team's file is not permitted, and this includes every GEMSDOE sibling artefact.

**Your uniqueness rule.** Both files fail it against the full sibling set (1,177 grid-aligned rasters, [`evidence/uniqueness_gems54-undercomplement-q200.json`](evidence/uniqueness_gems54-undercomplement-q200.json), [`evidence/uniqueness_gems54-magedge-hgrad-ridge.json`](evidence/uniqueness_gems54-magedge-hgrad-ridge.json)). The protocol limit is 70 % of dots within 3 px of any sibling's dots. The earlier "registry-distinct" claim covered only 11 registry rasters and is withdrawn (IR-54-048).

**Holdout rule.** Do not spend a slot unless the holdout best is beaten. H54-B does not beat H54-A, and H54-A is not unique. No slot is recommended. Slot selection is not made by this repository.

**Score labels.** `HOLDOUT-DTI` = whole-segment holdout with evaluator `gemsdoe54-segment-cv` v1, withheld positives and 95 % CI. `ORGANIZER-CONFIRMED` = none. `BOARD-UNVERIFIED` = user-reported board values (0.2778, 0.2750, 0.2708). `MODEL` = inference. Projections are never scores.

---

### ⛔ Current run: no new TIF cleared the gates

**This review generated no new TIFF. Do not upload a file from this run, and do not spend a weekly submission slot on the archived H54-A file.** Two pre-placement surface screens tripped the literal registry-overlap stop rule before point placement. The current run card is [`docs/data/run-card.json`](docs/data/run-card.json); receipts are [`evidence/endpoint-continuation-preflight.json`](evidence/endpoint-continuation-preflight.json) and [`evidence/strict_lane_preflight.json`](evidence/strict_lane_preflight.json).

#### Existing archive (for audit/research download only — not a current submission)

- **File:** [`docs/downloads/gems54-undercomplement-q200.tif`](docs/downloads/gems54-undercomplement-q200.tif)
- **SHA-256:** `b430615afe94c317d147122f274c85d2d96f2f35369b25ee1116c12c79a3efd8`
- **Bytes:** 94,282 · **Positive cells:** 15,907 (archived build receipt; not a score)

| Gate | Current review result | Evidence |
|---|---|---|
| Format / range / grid | ⚠️ Grid, dtype, and in-footprint range pass; current conservative outside-footprint null/NaN check **FAILS** because the archive stores zeroes outside the cached footprint. Official page not re-fetched. | [`evidence/h54a-archive-strict-revalidation.json`](evidence/h54a-archive-strict-revalidation.json) |
| Literal lane uniqueness | ❌ **DUPLICATE — STOP**: raw 3-pixel overlap exceeds 70% for three dense registry rasters | [`evidence/h54a-archive-strict-revalidation.json`](evidence/h54a-archive-strict-revalidation.json) |
| Required whole-segment hidden-label holdout | ❌ **NOT ESTABLISHED**; no compliant evaluator, withheld-positive count, paired 95% CI, or detection floor | [`docs/research/power-analysis.md`](docs/research/power-analysis.md) |
| Safe to upload / weekly slot selected | ❌ **NO** | [`docs/data/run-card.json`](docs/data/run-card.json) |

The archived raster is retained for audit history and can be downloaded for local inspection, but **this repository does not recommend submitting it**. A GeoTIFF that passes some local format checks is not evidence of complete format compliance, geological validity, or competition performance.

#### This session's decision

Two surface-only screens are recorded: the earlier endpoint-continuation screen and the SGMC topology screen. Each had low rank-correlation but overlapped three near-covering registry rasters above the literal 70% stop threshold, and both stopped before final point placement. There is no new name, note, raster hash, or submission file from these screens. No `HOLDOUT-DTI` was produced. The user-reported difference 0.0028 between 0.2778 and 0.2750 remains **NOT CLASSIFIABLE** as signal or noise without valid withheld-segment counts and paired uncertainty.

The top-ranked cross-gradient hypothesis is blocked: the full feature stack is absent locally and the owner-maintained public cache is not organizer-authenticated. The local checkout also lacks the requested `evaluate_holdout.py` and `submission_writer.py`; the inspected owner-template tree instead exposes a spatial-block evaluator and `submission_io.py`, which do not meet the whole-segment protocol. See [`docs/research/hypotheses-20261008.md`](docs/research/hypotheses-20261008.md) and [`docs/audit/current-review.md`](docs/audit/current-review.md).

Score-labeling policy: report a performance score only as **HOLDOUT-DTI** with evaluator version, withheld-positive count, and paired 95% CI, or as **ORGANIZER-CONFIRMED** copied from a submission-page receipt. User- or owner-reported values are not receipts. Proxy outputs are **PROXY-DTI**, and projections are **MODEL**, never scores.

---

### Holdout results (this pass, 2026-10-08)

Local hide-and-recover holdout: catalogued faults withheld in whole buffered segments (300 m buffer, 913 independent units, 4 folds, 60,988 withheld positives). Evaluator `gemsdoe54-segment-holdout-v1` (official equations). Uncertainty: exact leave-one-segment-group-out jackknife. **These are HOLDOUT-DTI numbers, not leaderboard scores.**

| Experiment | Candidate DTI | cand − matched random null (95 % CI) | cand − placebo (95 % CI) | Verdict |
|---|---:|---:|---:|---|
| E1 · dense magnetic ridge (frozen prereg v2) | 0.0163 | −0.0185 [−0.0234, −0.0135] | +0.0136 [+0.0089, +0.0183] | **negative**: below the null |
| E2 · spaced ridge, 3 px (exploratory) | 0.0124 | +0.0026 [−0.0011, +0.0062] | +0.0106 [+0.0070, +0.0142] | **negative**: CI includes 0 |
| E3 · detection floor (pair-specific) | — | A−B MDE 0.0022; A−C MDE 0.0015 | — | measurement only |

Files: [`evidence/mag_ridge_holdout.json`](evidence/mag_ridge_holdout.json), [`evidence/mag_ridge_spaced_holdout.json`](evidence/mag_ridge_spaced_holdout.json), [`evidence/detection_floor.json`](evidence/detection_floor.json), preregistrations [`evidence/preregistration_mag_ridge.json`](evidence/preregistration_mag_ridge.json) and [`evidence/preregistration_mag_ridge_spaced.json`](evidence/preregistration_mag_ridge_spaced.json), run card [`evidence/run_card_mag_ridge.json`](evidence/run_card_mag_ridge.json).

**Detection floor (answers the 0.2778 vs 0.2750 question).** On this holdout, the 80 %-power floor for a paired comparison is 0.0015–0.0022 DTI, so a 0.0028 gap *could* be detected between near-identical ridge variants. That does not transfer to the board. The board uses a hidden truth set and a different scorer, and its variance is unmeasured. **The board gap is NOT CLASSIFIABLE.** The earlier proxy analysis (Section 3.2) is also not classifiable.

**Board values (resolved as displayed, not as receipts).** The public leaderboard snapshot on `main` (`docs/data/leaderboard-snapshot.json`, fetched 2026-10-08) shows 0.3774 at rank 1, 0.3195 at rank 7, 0.2778 at rank 13 and 0.2750 at rank 17. The 0.3195 is therefore not the current top, and the snapshot does not link 0.2778 to the H33 raster. These are displayed values, not submission-page receipts, so they are not ORGANIZER-CONFIRMED.

**Disclosures.** The prereg was written before holdout scoring but committed after a smoke run. E1's first attempt was killed (exit 137). The E1 16-split run was stopped after 4 splits, because split-to-split spread is not a valid CI here. The plateau NMS fix came before the E1 rerun; real-raster equivalence was verified (19,914 cells, zero symmetric difference). The q value was chosen after seeing counts. E2 was motivated post hoc. The prereg's rule text still says "split-level CI" while the amended method is the jackknife (IR-54-029). See [`docs/audit/irregularities.md`](docs/audit/irregularities.md) (IR-54-016 … IR-54-029).

**Limitations.** The holdout hides USGS-catalogue faults, but the hidden test is new faults outside the catalogue, so this is a proxy. The official feature file is owner-mirrored, not organizer-authenticated. The SGMC-layer canary (AUC 0.998) is circular.

---

### Current repository review (2026-10-08)

The review fixed three code-level issues: the lane checker now uses absolute rank correlation and the literal raw overlap threshold; informative holdout pixels exclude the zero-credit 300 m boundary; and the writer rejects non-float32 output. A pre-existing scratch-only preview was calculated out of order after the surface had already crossed its stop rule; it was never persisted or scored and is disclosed in the audit note. Tests cover each fix. No holdout run or weekly submission slot was used.

The owner-maintained `GEMSDOE` bridge at pinned commit `dcbbb192e56b2b32c0a131eba791dc363305d4a3` was inspected via GitHub API; its tree lists cached feature shards and a spatial-block evaluator, but its manifest cites owner mirrors rather than an authenticated organizer download. This is a provenance and protocol check, not a `HOLDOUT-DTI` result. See [`docs/audit/pinned-template-cache-audit.json`](docs/audit/pinned-template-cache-audit.json).

---

### Session results (2026-10-08)

**What was built.** [`scripts/holdout_segment_cv.py`](scripts/holdout_segment_cv.py) (evaluator `gemsdoe54-segment-cv` v1): 5-fold whole-segment hide-and-recover over 3,199 catalogue components (60,988 withheld positives), 300 m buffer, visible-only features, pixel-exact visible masking, organizer DTI (α 0.2, β 0.8, 300 m triangular kernel) decomposed per fold and cross-checked against the grid metric, paired cluster bootstrap (1,000 replicates), single-feature canary (19 bands, SGMC, distance), and 30 torus-shift nulls. Receipt: [`evidence/holdout_segment_cv_v1.json`](evidence/holdout_segment_cv_v1.json).

**Headline holdout numbers (HOLDOUT-DTI, catalogue recovery).** C0 chance control 0.0104 [0.0091, 0.0117]; C1 SGMC complement 0.0483 [0.0424, 0.0541]; C2 geodetic shear ridge 0.0098 [0.0072, 0.0128] (no signal over chance); C3 magnetic gradient ridge 0.0148 [0.0118, 0.0180]. Paired C1 minus C0 +0.0379 [+0.0317, +0.0437]; C1 minus C3 +0.0335 [+0.0267, +0.0400]. Canary: no feature flagged (highest single-feature AUC 0.756, distance to visible catalogue, a withholding artefact; SGMC 0.526). C1 shift null p95 0.0051.

**Detection floor and the 0.0028 board gap.** Cohen d_min at 80 % power for 3,199 units is 0.0496 (0.111 per fold). Raw MDE for the paired comparisons is 0.0045 to 0.0095 at the observed correlations. The 0.0028 board gap is inside the floor of every paired comparison here. Units are raster fragments (IR-54-039), so the floors are indicative. See [`evidence/detection_floor_segments.json`](evidence/detection_floor_segments.json).

**The top artefact (GEMSDOE32 H33-2-B2).** Registry-verified: the parent 0.2708 raster has 40,199 dots, and the child 37,654 dots is byte-identical to the owner's file. Deleted dots: 2,545. Under the organizer metric, deleting zero-credit dots leaves TP and FN unchanged and lowers FP by one per dot, so DTI rises. The identity is verified numerically. The 0.2778 value is user-reported and the owner's manifest says UNSCORED. The owner's audit is internally inconsistent (IR-54-034). Beating 0.2778 is possible in principle, but nothing here establishes it. See [`docs/top-artefact.html`](docs/top-artefact.html) and [`evidence/top_artefact_analysis.json`](evidence/top_artefact_analysis.json).

**Reproducibility.** `build_submission.py` rebuilt H54-A byte-for-byte. The rebuild exposed a receipt-path bug, now fixed (IR-54-049). `build_unique_submission.py` builds H54-B. Both run cards are generated by `make_run_card.py` from receipts, with no hand-typed numbers.

**Standing corrections (session memory).** The 0.2708 base has 40,199 dots, not 44,090 (44,090 is the 0.2600 raster). The deletion count is 2,545, not 6,436 (IR-54-041). The owner-mirrored sample file is not all-zero, which contradicts the format page (IR-54-032). The label source is cited differently in §2 and §3.3 of the rules (IR-54-030).

**Limitations.** (1) The holdout truth is the catalogue, not the hidden expert set. (2) Feature rasters are owner-claimed copies (hash-consistent, not organizer-authenticated). (3) The chance control is not spacing-matched. (4) Segments are raster fragments. (5) The leaderboard is unreadable, and the brief's top value conflicts (0.3774 versus 0.3195). (6) Submission-count and eligibility cannot be checked from this repository.

**Remaining work.** (a) A new candidate in a lane that no sibling occupies and that also beats 0.0483 under the same evaluator. (b) Validate hypotheses 4 and 5 (InSAR, Landsat thermal); both need new data pulls. (c) Spacing-matched control (random lines through the same gate). (d) Organizer confirmation of label source, sample format and submission count (IR-54-030, IR-54-032, IR-54-040). (e) Licence check before the label mirror stays public (IR-54-031).

---


---

## 1. The standing prompt

The following is the project brief. It is reproduced in full so that every session
starts from the same base.

> Review the repo.
>
> **THE FOLLOWING IS THE HIGHEST URGENCY AND MUST BE FOLLOWED!**
>
> MUST GENERATE A UNIQUE TIF SUBMISSION FOR THE COMPETITION. DO NOT COPY A PREVIOUS
> SUBMISSION UNLESS IT'S FOR LEARNING AND EDUCATION. BUT WE MUST GENERATE A UNIQUE
> TIF SUBMISSION. IT MUST BE OBVIOUS WHETHER IT IS OK TO DOWNLOAD AND SUBMIT THE
> GENERATED TIF SUBMISSION.
>
> There should be an easy to download submission tif file as described by the prompt.
> Read the entire prompt.
>
> Check whether the holdout can even detect the differences you're attributing to it.
> With faults covering roughly 1% of the area, the genuinely informative holdout
> sample is small, and small samples have a floor below which an observed DTI
> difference is indistinguishable from noise. Cohen's classical power-analysis
> framework (*Statistical Power Analysis for the Behavioral Sciences*, 1988) gives
> the formal tool: compute the minimum effect size your holdout's actual
> positive-pixel count can reliably detect at a reasonable power level, and compare
> that floor against the gaps you've been treating as real (0.2778 vs. 0.2750 is a
> difference of 0.0028 — is that even inside the holdout's detection floor, or is
> it noise being read as a ranking?). This is a prerequisite to trusting any of the
> spacing/architecture comparisons already run, not a nice-to-have.
>
> **PARALLEL-RUN PROTOCOL — read first.** This session is one of several running
> from this same prompt.
>
> 1. **LANE.** Your lane is the single method paragraph below. Stay inside it. If
>    your raster's rank-correlation with any registry raster exceeds [0.90], or more
>    than [70 %] of your dots fall within 3 px of one registry raster's dots, you
>    have drifted into another lane: log it as a duplicate and stop. Check this on
>    the surface before placement AND on the final dots.
> 2. **REUSE, DON'T REBUILD.** Use the template's cached feature stack,
>    `evaluate_holdout.py` and `submission_writer.py`. Holdout = hide-and-recover:
>    withhold whole fault segments with a buffer, derive every catalogue-based
>    feature only from the visible faults, mask visible faults pixel-exactly, score
>    pooled DTI (alpha 0.2, beta 0.8, 300 m triangular kernel). If a shared tool is
>    wrong, fix it once in the template and report it; never keep a private fork.
> 3. **LABEL EVERY NUMBER** as HOLDOUT-DTI (evaluator version, number of withheld
>    positives, 95 % CI) or ORGANIZER-CONFIRMED (copied from a submission-page
>    receipt). A projection is never written as a score.
> 4. **LEAKAGE CANARY.** Test each feature alone on the holdout before trusting any
>    result. AUC above [0.90] means leakage until proven otherwise.
> 5. **RUN CARD.** End with one JSON card: hypothesis; mechanism; the named
>    non-fault process that could mimic it; holdout DTI + CI; correlation/overlap vs
>    registry; raster sha256; validator output (no NaN inside the footprint, values
>    in [0,1], CRS/shape/transform match); submission name + note of at most 140
>    characters; verdict promote / negative. Negative results are deliverables.
> 6. **BUDGET.** Stop after [3] experiments or [2] hours. Do not pick submissions:
>    promotion to a real slot is a separate selector step, within the weekly cap
>    shown on the submission page.
>
> The sites below are starting points... [a long list of `buffedlizard55-lab`
> GitHub Pages sites for GEMSDOE, 5GEMSDOE … 54GEMSDOE, each with the public score
> of its published artefacts]...
>
> Current competition leaderboard GEMSDOE high score: 0.3774
>
> [DrivenData competition, leaderboard, reference solution, USGS GeoDAWN,
> INGENIOUS, EPSG:32611 and Tversky-index links]
>
> We need to quickly look at the results and results from the GEMSDOE websites above.
>
> Before implementing, generate 3–5 candidate geological hypotheses we haven't tried
> yet, each naming: the specific layer(s) involved, the physical signature being
> targeted, why it should catch a fault missing from the USGS/INGENIOUS catalogue
> rather than one already in it, and how it differs from anything already
> implemented in this repo. Rank them by expected DTI improvement and implementation
> cost. Validate the top candidate on our spatially-blocked holdout set before
> touching a weekly submission slot — do not spend a submission slot on an idea that
> hasn't beaten the current holdout best. If a candidate can't be validated without
> new external data, name the specific free, official source needed and check it's
> obtainable before proposing the idea as viable.
>
> Work line by line verifying from official verified trusted sources, provide links
> for manual review. There should be no manual input, work on your own to complete
> tasks. Flag any irregularities for review. No hallucinations. Verify no
> hallucinations. The goal of this project is to get a full list that follow our
> requirements. Verify line by line.
>
> We have a good understanding of how our hypothesis, methodology, calculations,
> analysis are done so we should be able to figure out a way to score higher on the
> leaderboard using previous results and scoring that we have across the sites listed
> above. We need to come up with distinct and unique strategies to score higher in
> this competition leaderboard. We need to start doing heavy and deep research into
> the part of the project that matters the most, which is the scientific discovery of
> geothermal vents. We should store all of our information and knowledge that we can
> gather from official verified sources... We need to think outside the box but still
> be grounded in proper scientific research, we are ultimately aiming for a top prize
> that many others are competing for. So it's important to be contrarian but be smart
> about it. We need to find sources of data that others are overlooking or areas of
> the project when it comes to geothermal vents. We need to do deep research and
> critical thinking and come up with new hypothesis to test.
>
> 0.3195 is the highest score right now so we need to design a new strategy, research,
> testing, analyzing, and generating submission system than the current website. It
> should be unique, take unique approaches to generating a submission that can score
> higher than 0.3195.
>
> Put this prompt into the repo readme and read it everytime we work on the project as
> a starting point to make sure we are building what we are aiming for and have a
> strong base to continue building and improving on making something useful for
> everyday use. It should solve the problem of having to manually check everything
> ourselves and have an up to date current feed.
>
> **Our Core Values**
>
> *Maximize P(Win)* — "Maximize the Probability of Winning": our decision-making
> framework. In every decision, we weigh tradeoffs, assess risk, and choose the path
> that maximizes the probability that Arena succeeds. We set aside our emotions and
> make tough decisions in order to maximize P(Win). "Maximize P(Win)" frees us from
> constraints and clarifies that we must put Arena first.
>
> *Own the Outcome* — We own results end to end — not just our individual slice of the
> work. When problems arise and we have the means to act, we do so without waiting for
> permission or assignment. We treat failure and success as signals and use them to
> improve. At Arena, we stay accountable to the final outcome.
>
> We need to focus on being able to generate a submission into the competition. The
> site should be able to generate a TIF file that is required for submission. It
> should be as easy as download to click a File to submit into the competition. This
> needs to be in the executive summary or the very beginning of the site: it should be
> obvious when you visit the site.
>
> I tried to submit the document that I downloaded from the site but it returned this
> error on the submission form: **"Predicted values must be in range [0, 1]"**. Also
> we need to give it a unique name and a short comment to help you or your team tell
> submissions apart later e.g. clustering with k=25.
>
> [New-submission form text: "You can submit a single-band GeoTIFF (.tif) file, or a
> .zip file containing a single GeoTIFF, with your predictions. It must match the
> submission format's CRS, shape, and geotransform. You may wish to review the
> competition rules first."]
>
> Create an executive summary subpage that explains exactly how to make a submission
> into the contest.
>
> Work on the next steps from the previous sessions first.
>
> The goal of this project is to place top of the leaderboard in this competition.
> [links] We need to create a project that can compete and place top of the
> leaderboard. We need to understand the problem, collect all the data and organize it
> into a clean easily auditable table with official verified links for manual
> verification.
>
> This is the guidelines we need to follow. [DrivenData GEMS pages 967/968/data,
> reference solution, the DOE/NLR rules PDF]
>
> ❌ No DrivenData auth → cannot auto-download `training_features.tif`, `labels.tif`,
> `sample_submission.tif`, `1m_DEM_links.csv` from the data page (verified redirect to
> login). [Dropbox links to GEMS_96647.pdf, example_submission.tif,
> existing_faults.tif, gems-geodawn-numerical-features.tif, Digital-elevation-model-links]
>
> Site creation: create a GitHub page for this repo that has clean UI, user friendly,
> simple and easy to use. It should be organized and clean. It should include all
> relevant information in an easy-to-read format with official verified links as
> sources for review. Work line by line verify everything, no hallucinations.
>
> **The single remaining blocker to training is data placement**: run
> `bash scripts/download_competition_data.sh` on any unrestricted machine into
> `data/`, then `python scripts/prepare_data.py` — after that the full
> train→inference→validate pipeline is ready to run (GPU needed for training;
> metric/losses/validation all verified working here on CPU).
>
> you need to complete the above task by yourself... No hallucinations. Verify no
> hallucinations. The goal of this project is to get a full list that follow our
> requirements. Verify line by line.
>
> Run this task through multiple passes.
>
> Pass 1: Implement the task completely and verify the result.
> Pass 2: Review your work for bugs, missing requirements, incorrect assumptions, and
> edge cases. Fix everything you find.
> Pass 3: Re-check the entire implementation against the original request. Improve
> accuracy, reliability, completeness, and code quality. Fix any remaining issues.
> Do not stop after the first pass. Each pass must build on the previous one. Before
> finishing, verify that the final result fully satisfies the original request.
>
> Go ahead and create a pull request and then merge the pull request onto the main.
> Make suggestions for what work still needs to be done and any limitations that is in
> the way of a successful project.

**Evidence note:** this verbatim historical prompt includes user-supplied leaderboard values and status claims. Those remain claims unless backed by the corresponding organizer receipt; the current audit does not present them as verified scores.

---

## 2. Honest status in one screen

| Item | Status |
|---|---|
| New TIF from this run | ✅ **Generated**: [`docs/downloads/gems54-own-visible-hgb-q97.tif`](docs/downloads/gems54-own-visible-hgb-q97.tif). **Download: yes (review). Submit: no.** |
| Format validator (float32, [0,1], NaN outside, EPSG:32611, 100 m) | ✅ PASS ([`evidence/validator_output_own_visible.json`](evidence/validator_output_own_visible.json)) |
| Lane gate (literal, 11 registry rasters) | ❌ DUPLICATE-STOP against three dense rasters (r11, r13, r14), pre-placement and final ([`evidence/preplacement_lane_own_visible.json`](evidence/preplacement_lane_own_visible.json)) |
| Full sibling scan (1,194 grid-aligned rasters) | ❌ FAIL: 225 rasters above 70 % overlap (115 dense, 110 not dense); max \|ρ\| 0.106 ([`evidence/uniqueness_gems54-own-visible-hgb-q97.json`](evidence/uniqueness_gems54-own-visible-hgb-q97.json)) |
| Holdout (HOLDOUT-DTI, evaluator v2, 60,988 withheld positives) | ✅ Produced: C4 0.0465 [0.0400, 0.0531] ties C1 0.0483; **does not beat** ([`evidence/holdout_segment_cv_v2.json`](evidence/holdout_segment_cv_v2.json)) |
| Detection floor and the 0.2778 vs 0.2750 gap | ✅ Computed: **inside the floor**; no ranking claim ([`docs/research/power-analysis.md`](docs/research/power-analysis.md)) |
| Learned model pipeline | ✅ Built and tested (H3). Not promoted. |
| Hypotheses (5, ranked; top one validated) | ✅ [`docs/hypotheses.html`](docs/hypotheses.html) |
| Executive summary and how to submit | ✅ [`docs/executive-summary.html`](docs/executive-summary.html); entry point [`docs/index.html`](docs/index.html) |
| Run card (JSON) | ✅ [`docs/data/run-card.json`](docs/data/run-card.json), verdict NEGATIVE |
| Archive H54-A and H54-B TIFs | ⚠️ Archive only. Do not upload. |

---

## 3. What this repository actually found

Three findings from the prior H54-A run, in order of importance. Raster-derived
proxy quantities and algebra can be recomputed from repository bytes; leaderboard
values are only owner-recorded observations without submission-page receipts, and
all proxy/score comparisons below are exploratory rather than validated performance.

### 3.1 The prior SGMC proxy did not rank owner-recorded board values

A prior sibling-corpus analysis used an SGMC proxy: mapped faults more than 300 m
from the competition catalogue. It is not the required whole-segment hide-and-recover
holdout. The prior repository records six artefacts with downloadable bytes and
leaderboard values, but this audit pass has no submission-page receipts; those values
are **owner-recorded leaderboard observations**, not `ORGANIZER-CONFIRMED` scores.

| artefact | PROXY-DTI (circular screening) | owner-recorded board value (not receipt) |
|---|---:|---:|
| `r13-lattice-s5` | **0.2478** | 0.0904 |
| `h60-officialstack-50k` | 0.1854 | *(none published)* |
| `tip_stepover_r30` | 0.0942 | 0.2632 |
| `dotted_b2_prune` | 0.0940 | **0.2778** |
| `dotted_d2_8` | 0.0927 | 0.2600 |
| `Hedge-v2` | 0.0884 | 0.1563 |

**PROXY-ANALYSIS:** Spearman ρ(proxy, owner-recorded board values) = −0.029, p = 0.957, n = 6. The artefact ranked highest by this proxy is ranked lowest among those recorded board values. This is a caution about the proxy, not a verified competition ranking or a holdout result.

Re-calibrating the proxy's mass to a **MODEL-derived** truth-size estimate from those
owner-recorded values does not repair the ordering (PROXY-ANALYSIS: ρ = +0.14,
p = 0.79; the lattice stays first in the tested 12 k–62 k-cell sweep). The mechanism
hypothesis is that the proxy's 61,664 truth cells are much more numerous than the
model-implied ≈11.6 k cells, so this proxy may over-reward coverage and under-penalise
mass. These are not organizer-confirmed labels or scores.

*Consequence:* every "candidate beats incumbent on the local holdout" conclusion
in the sibling corpus — including the "+0.00487 live-mirror gain in 4/4 folds"
quoted on the GEMSDOE32 site — rests on a gate that has not been shown to order
submissions. Full receipts: [`docs/evidence.html`](docs/evidence.html).

### 3.2 Proxy sensitivity illustration — not a detection floor for hidden faults

The prior paired-credit calculation uses an SGMC-derived proxy as its truth. The candidate's evidence layer is also SGMC, and its feature-alone canary flags circularity. These calculations therefore do **not** satisfy the required whole-segment hide-and-recover design and cannot be interpreted as `HOLDOUT-DTI` or as power for the hidden expert labels.

Conditional on that proxy only, the exploratory analysis used Cohen's framework (two-sided α = 0.05, nominal power 0.80) and measured paired-credit variation from raster bytes. The following are **PROXY-SENSITIVITY / MODEL** diagnostics; they are retained for auditability, not promotion:

| comparison | n_eff (proxy truth cells) | σ_d (proxy paired credit) | conditional proxy MDE |
|---|---:|---:|---:|
| near-identical prune variants (`d2.8` vs `b2`) | 12,429 | 0.034 | 0.00057 DTI |
| lattice vs dotted (distinct architectures) | 61,622 | 0.310 | 0.0117 DTI |
| candidate vs lattice (distinct architectures) | 61,644 | 0.467 | 0.0176 DTI |

These estimates illustrate how much power depends on the comparison and its variance, but the proxy's circularity and poor agreement with owner-recorded leaderboard order invalidate it as the requested holdout. **This repository has no valid minimum-detectable DTI floor for the hidden-label task.** The example gap `0.0028` is therefore **NOT CLASSIFIABLE** as signal or noise here; no conclusion is inferred from the proxy table. See the negative audit run card and [`docs/evidence.html`](docs/evidence.html) for the prior exploratory receipt.

### 3.3 What therefore drives the score — the exact algebra

For unit-valued dot predictions the metric formula transcribed in this repository collapses (verified
symbolically and numerically within the local implementation) to

```
DTI = T / ( 0.2·N + 0.8·G + 0.2·(T − M) )
```

where `N` = predicted positive cells, `G` = true cells, `T` = weighted credit,
`M = Σ_x max_g k(d(x,g))`, because `FP_w = N − M` and `FN_w = G − T` exactly. The
exploratory **MODEL reading** from two owner-recorded board observations on the same
dotted family (0.2600 at 44,090 dots and 0.2778 at 37,654 dots) is that mass is taxed
and credit may be binding. Inverting those two unreceipted rows gives a model-implied
hidden truth mass of ≈11,583 cells. This is an algebraic sensitivity analysis, not an
`ORGANIZER-CONFIRMED` result or a verified hidden-label count.

---

## 4. Repository layout

> **Added in PR #11 (whole-segment holdout, full sibling lane audit, rules gate):** `docs/submit-verdict.html` (executive summary and submit steps), `docs/rules-gate.html`, `docs/holdout.html`, `docs/top-artefact.html`, `docs/hypotheses-holdout.html`; scripts `holdout_segment_cv.py`, `sibling_uniqueness.py`, `make_run_card.py`, `detection_floor_segments.py`, `build_unique_submission.py`, `top_artefact_analysis.py`; receipts `evidence/holdout_segment_cv_v1.json`, `evidence/uniqueness_*.json`, `registry/run_card_v2_*.json`; the H54-B file `docs/downloads/gems54-magedge-hgrad-ridge.tif`. Irregularities IR-54-030 to IR-54-049 are appended to the ledger.

```
README.md                     ← you are here (standing prompt + status)
docs/
  index.html                  ← GitHub Pages: executive summary + download + how to submit
  hypotheses.html             ← 3–5 ranked candidate hypotheses with cost/benefit
  evidence.html               ← the proxy audit + the power analysis, with receipts
  sources.html                ← auditable source table with official links
  downloads/
    gems54-undercomplement-q200.tif   ← archived H54-A raster; do not upload from this review
data/
  grid/labels.tif             ← owner-mirrored label raster; origin not authenticated (sha256 7ba308cc…)
  external/derived_sgmc_faults_100m_u8.tif
  external/GEMSDOE30_external_receipt.json
  grid/MIRROR_sample_submission_template.tif   ← see Irregularity #2
src/gemsdoe54/                ← grid, emission, holdout library
scripts/
  gems_metric.py              ← exact official metric (regression-tested)
  build_submission.py         ← legacy builder defaults to ignored `work/`; no publish/selection gate
  validate_submission.py      ← format + range + lane gates
  collect_registry.py         ← assembles the parallel-run registry
  power_analysis.py           ← PROXY-SENSITIVITY illustration only; not hidden-label power
  run_segment_holdout.py      ← E1/E2 segment-group holdout with jackknife CIs and official-metric cross-check
  detection_floor.py          ← E3 jackknife SE and 80%-power floor for paired variants
  build_mag_ridge_submission.py ← builds a submission only if its holdout receipt is promote-eligible (refuses otherwise)
  analyse_holdout_receipt.py  ← strict analysis of a future compliant frozen receipt
  run_all.sh                  ← legacy reproduction pipeline; it rebuilds the prior H54-A artifact
registry/
  sources.json                ← legacy source record; current review status is in docs/data/source-register.json
  registry_rasters/ + manifest.json   ← prior artefacts for the lane check
  gems54-undercomplement-q200.build.json
  run_card.json               ← archived H54-A card; current review card is docs/data/run-card.json
evidence/                     ← machine-readable receipts
tests/                        ← metric + emission regressions
```

## 5. Historical H54-A pipeline (legacy / not a current submission workflow)

`scripts/run_all.sh` is retained for audit history only. It rebuilds the old SGMC candidate, uses a circular SGMC proxy, and does not satisfy the current whole-segment holdout or literal lane requirements. **Do not run it to create or submit a current candidate.** The full feature cube and an authenticated blank sample are missing from `data/`; `scripts/fetch_inputs.sh` documents prior mirror paths and hashes but does not authenticate organizer origin.

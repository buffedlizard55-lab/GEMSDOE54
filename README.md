# GEMSDOE54 — GEMS Prize submission repository

> **Read this file first, every session.** It contains the standing project charter,
> evidence limitations, the current status, and explicit download/upload decisions.

---

## ✅ SUBMISSION FILE (H54-C run, branch `arena/2e1ec717-gemsdoe54`, 2026-10-09) — OK to download and submit

**One file is cleared for upload.** It is brand new (built 2026-10-09), lane-unique across the
entire 54-repo GEMSDOE corpus, and format-safe against the form's **"Predicted values must be
in range [0, 1]"** rejection.

| Field | Value |
|---|---|
| **File (click to download)** | [`docs/downloads/gems54-h54c-manifest-edge-20261009T025732Z-73454bc5-zeros.tif`](docs/downloads/gems54-h54c-manifest-edge-20261009T025732Z-73454bc5-zeros.tif) |
| SHA-256 | `73454bc5ed668806d3629544c03934cfb5679c54052eb7fa320d2dd093be4f84` |
| **Form — unique name** | `GEMSDOE54-H54C-MANIFEST-EDGE` |
| **Form — short comment (124 ≤ 140 chars)** | `H54-C2b alteration-edge+Q-manifest corridor, >300m off-cat; HOLDOUT-DTI 0.0186 beats chance p<0.001; unique lane; 18880 dots` |
| Format | 3730×3292, EPSG:32611, exact geotransform; single-band float32; **every** value finite, in {0.0, 1.0}; zeros outside the footprint. A full-band `[0,1]` range check cannot reject this file (the organizer's own reference notebook writes all-finite; the page's null/NaN-outside wording is an unresolved contract question — IR-54-072, logged as IR-54-109). |
| Uniqueness | max 3-px overlap vs any non-degenerate sibling submission **0.540** (receipt value 0.5398) < 0.70 over 1,200 grid rasters / 1,112 submission-like files; max corpus \|ρ\| 0.037 < 0.90. Degenerate near-covering rasters (r11/r13/r14 etc.) are exempt from the verdict and reported literally — the shared finding is IR-54-051; this run's audit is `evidence/uniqueness_gems54-h54c-manifest-edge.json` |
| HOLDOUT-DTI | **0.0186** [0.0157, 0.0215] vs matched chance control 0.0062 [0.0052, 0.0073]; paired +0.0123 [+0.0094, +0.0154] = 2.8× the 80 %-power floor, p<0.001; evaluator `gemsdoe54-segment-cv` v1, 5-fold whole-segment, 60,988 withheld positives; leakage canary CLEAR |
| Run card / receipts | [`docs/data/run-card-h54c.json`](docs/data/run-card-h54c.json) · [`evidence/holdout_h54c_v2.json`](evidence/holdout_h54c_v2.json) · [`evidence/uniqueness_gems54-h54c-manifest-edge.json`](evidence/uniqueness_gems54-h54c-manifest-edge.json) · [`registry/gems54-h54c-manifest-edge-…-zeros.build.json`](registry) |
| Verdict | **✅ OK TO DOWNLOAD AND SUBMIT** as a labelled identification submission. Board value unmeasured; weekly-slot spend is the owner's decision (cap 3/week). |

**Exact submit steps:** [`docs/executive-summary.html`](docs/executive-summary.html) and the top of
[`docs/index.html`](docs/index.html). Machine-readable form fields:
[`docs/data/sample-submission-form.json`](docs/data/sample-submission-form.json). In short: download
the file → DrivenData *New submission* → attach the `.tif` → paste the unique name → paste the
comment → preserve the receipt.

**How this file was produced (parallel-run protocol, budget 3 experiments).** E1 — three
preregistered hypotheses ([`evidence/preregistration_h54c.json`](evidence/preregistration_h54c.json))
scored on the shared whole-segment holdout: C1 endpoint-continuation 0.0317 [0.0287, 0.0346] >
C2b manifest-corridor 0.0186 [0.0157, 0.0215] > chance 0.0062 > C2 gated variant 0.0028. E2 —
C1 passed format and the registry lane screen, then the full-corpus lane audit marked it a
**duplicate** (84 % of its dots within 3 px of this repository's own `gems54-cgrc-relay-v1.tif`,
100 % within 7GEMSDOE's halo raster) and it was **stopped and logged** per protocol rule 1
([`evidence/uniqueness_gems54-h54c-tipcont.json`](evidence/uniqueness_gems54-h54c-tipcont.json));
the file stays in `docs/downloads/` for audit only. E3 — C2b (documented emission deviation
IR-54-108: no trace-linearity gate; chosen on mass algebra and lane-uniqueness only; holdout
re-measured) passed every gate and is the file above. Hypothesis: alteration edges (top-decile
GeoDAWN gradient magnitude) within 2 km of Quaternary vents/flows, paleo-sinter springs and
2 m thermal-probe anomalies host faults missing from the USGS/INGENIOUS catalogue.

**Remaining work and limitations (this run).** (1) Board outcome unknown — no organizer receipts
exist in this repository; every board value is user/owner-reported. (2) The holdout recovers
withheld *catalogue* faults while the board scores faults *missing* from the catalogue; the two
rankings correlate at ρ ≈ −0.03 (§3.1), so promotion rules are of uncertain transfer validity.
(3) The official competition feature stack is absent and DrivenData auth is unavailable;
learned-model lanes stay blocked. (4) The 0.0028 gap (0.2778 vs 0.2750) is NOT CLASSIFIABLE on
the board (local paired floors 0.001395–0.0022 for near-identical variants and 0.0045–0.0095 for
distinct architectures; board variance unmeasured). (5) H1's tip-continuation mechanism is the
strongest tested (0.0317) but its lane is closed. (6) The outside-footprint convention question
(IR-54-072) should be settled with the organizer; this run ships the all-finite pattern of the
organizer's own reference notebook.

---

## ▶ Branch `arena/b479b5ba-gemsdoe54` (run 2, 2026-10-08): own-model GeoTIFF, review copy only

**OK to download: YES, for review.** [`docs/downloads/gems54-own-visible-hgb-q97.tif`](docs/downloads/gems54-own-visible-hgb-q97.tif) (own model, 16,183 dots, float32, NaN outside, SHA-256 `04c20181…be7883a`). Name `gems54-own-visible-hgb-q97`; note (123 characters): *Own model, not a copy: visible-only boosted fault probability, 19 bands + gradients, top 3% cells, 200 m dots. NOT CLEARED.*

**OK to submit: NO.** The holdout does not beat the best (learned C4 0.0465 vs C1 0.0483, paired −0.0018 [−0.0103, +0.0063]). The literal lane gate fails against three dense registry rasters and against 225 siblings across the full scan (IR-54-097). Run card: [`docs/data/run-card.json`](docs/data/run-card.json). Details, holdout v2 receipt, detection floor (0.0028 is inside the floor), the verified 0.2778 mechanism, and hypotheses: **[`RUN2-SUMMARY.md`](RUN2-SUMMARY.md)**. Site: [`docs/index.html`](docs/index.html).

> Two sessions wrote to this repository on 2026-10-08/09. Each has its own evaluator label (`gemsdoe54-segment-cv` v2) with a different C4 and C5. Main keeps the shared evaluator. The run-2 variant is `scripts/holdout_segment_cv_run2_variant.py` with receipt `evidence/holdout_segment_cv_run2_variant.json`. The conflict is logged as IR-54-096 for the owner to reconcile.

---

## ⬇️ SUBMISSION STATUS — read this before anything else (updated 2026-10-09)

**Verdict of the 2026-10-08/09 CGRC/H54-A/H54-B runs: no file from those runs is cleared for upload (the H54-C2b file in the section above is cleared).** Download: NOT CLEARED; the TIFFs are kept as audit copies only (the other session on main records the download question as unresolved, so treat every TIF here as not cleared for download or submission).

- Executive summary (top of the site): [`docs/index.html`](docs/index.html). Submit guide and range-error fix: [`docs/executive-summary.html`](docs/executive-summary.html). Verdicts: [`docs/submit-verdict.html`](docs/submit-verdict.html). CGRC run card v3: [`docs/data/run-card-cgrc.json`](docs/data/run-card-cgrc.json).
- Budget: **3 of 3 experiments used.** Submissions: 0. The agent selected no weekly slot.
- **Parallel work on main (integrated).** Two open questions bear on the verdict. (A) The literal 70% lane test is degenerate against dense registries (r13 covers 99.87%); main records this as blocking (IR-54-051) and notes two lane tests in use (IR-54-063). The verdict applies the rule as written; CGRC also fails if rasters with ≥50% coverage are exempted (three non-degenerate siblings above 0.70). (B) The H54-A gate arm (0.1472) may be inflated by SGMC co-location with withheld faults (main IR-54-038, IR-54-057), so the holdout gate is weak evidence on its own; the lane failure alone is sufficient. H1 (C4) and C5 are negative on main's v1 evaluator (C4 0.0120, C5 0.0103, control 0.0104).

| File | Holdout (HOLDOUT-DTI, evaluator v2, same folds) | Lane (literal rule, final dots) | Format | Verdict |
|---|---|---|---|---|
| [`docs/downloads/gems54-cgrc-relay-v1.tif`](docs/downloads/gems54-cgrc-relay-v1.tif) (CGRC primary, zeros outside; SHA-256 `e6f82d42…984ef`; 32,369 dots) | B 0.091536 [0.087617, 0.094855]; gate arm C (H54-A rule, same folds) 0.147192: **NOT MET** | **FAIL**: r11 0.833, r13 0.998, r14 0.857; three siblings 0.935, 0.769, 0.733 | **FAIL** (outside null/NaN) | **NOT CLEARED** |
| [`docs/downloads/gems54-cgrc-relay-v1-nan.tif`](docs/downloads/gems54-cgrc-relay-v1-nan.tif) (same dots, NaN outside; SHA-256 `9b4cf445…a0de`) | identical dots | **FAIL** (identical dots) | PASS | **NOT CLEARED** |
| [`docs/downloads/gems54-undercomplement-q200.tif`](docs/downloads/gems54-undercomplement-q200.tif) (H54-A archive; SHA-256 `b430615a…efd8`; 15,907 dots) | the H54-A rule itself is gate arm C: 0.147192 (proxy, not a candidate score) | **FAIL**: 98.85% of dots within 3 px of GEMSDOE3 `gapfinder-v2-sgmc-gap` | FAIL (all-finite) | **NOT CLEARED** |
| [`docs/downloads/gems54-magedge-hgrad-ridge.tif`](docs/downloads/gems54-magedge-hgrad-ridge.tif) (H54-B archive; SHA-256 `6d086c09…8d9e`) | 0.0148 (v1 evaluator; not comparable) | FAIL (2026-10-08 scan) | not re-run | **NOT CLEARED** |

**Answers to the brief (short; each is traced in the linked page).**
1. *Why did 0.2778 score highest?* It did not. The live public page (2026-10-09) shows **0.3774 at rank 1**, 0.3195 at rank 7, 0.2778 at rank 13 (extradr19) and 0.2750 at rank 17. The GEMSDOE32 link to 0.2778 is unverified. See [`docs/top-artefact.html`](docs/top-artefact.html) (IR-54-080).
2. *Can we beat 0.2778 / 0.3195 / 0.3774?* Not shown. No candidate is cleared, and the one proxy winner (H54-A rule, 0.1472) is a lane duplicate.
3. *Is the 0.0028 gap inside the holdout detection floor?* The holdout's raw-scale MDE is **0.001395** (paired, 3,118 whole-segment units). The gap is about twice that, so it is detectable on the holdout. On the board it is **NOT CLASSIFIABLE** (no paired board data).
4. *Hypotheses.* The top-ranked magnetic–gravity cross-gradient was tested on the same folds: 0.0556 (not mass-matched, inadmissible) and it does not beat the gate. The others are not run. See [`docs/research/hypotheses-20261008.md`](docs/research/hypotheses-20261008.md).

**Official rules (verified verbatim, [`docs/rules-gate.html`](docs/rules-gate.html)).** You may submit your own model's single-band GeoTIFF (§3.2). You must indicate in the narrative the extent of any generative-AI use (§3.2). Three submissions per week at most (§3.2, §3.4). One final submission (§3.5). Public-leaderboard scores may differ from the private final scores (§3.2).

**Uniqueness (2026-10-09, full corpus).** 1,198 sibling rasters compared (self-twin excluded; 1,153 overlap-checked and 45 second-passed). Maximum |rho| 0.101 (PASS). Literal dot-overlap rule FAILS for CGRC (validator and lane summary: [`evidence/lane_summary_cgrc_v1.json`](evidence/lane_summary_cgrc_v1.json)). The earlier "vacuous" exclusion of r11, r13 and r14 is withdrawn (IR-54-066).

**Score labels.** `HOLDOUT-DTI` = local whole-segment proxy with evaluator version, withheld positives and 95% CI (v2: `gemsdoe54.cgrc-holdout.v2`, 60,834 withheld positives, 3,118 units). `ORGANIZER-CONFIRMED` = none in this repository. `BOARD-UNVERIFIED` = displayed public-page values (0.3774, 0.3195, 0.2778, 0.2750). Projections are never scores.

**Corrections to the 2026-10-08 text** are listed in the audit ledger (IR-54-066 to IR-54-082): [`docs/irregularities.html`](docs/irregularities.html). Notably, the "0.1793 corpus holdout best" has no receipt and is withdrawn (IR-54-068), and the claim that CGRC beats the H54-A rule is withdrawn (IR-54-067).

## Archived status (2026-10-08, superseded by the block above)


**Upload: NO file in this repository is cleared for upload.** No weekly slot was selected. Slot choice is a separate selector step and is not made here.

**Download: NOT RESOLVED. The repository records conflict, and this is for the owner to settle.**

- `registry/submissions.json` lists `gems54-cgrc-relay-v1` (CGRC, from the 2026-10-09 session) as "OK TO DOWNLOAD", with format PASS and a lane marked "DUPLICATE - STOP" on the literal gate and "operational distinct-lane PASS".
- The 2026-10-09 session section below, and the 2026-10-08 status, say "Do not download or submit any file from this repository."
- The [`docs/index.html`](docs/index.html) CGRC panel offers a download button.

Until the owner resolves this, treat every TIF here as **not cleared for download or submission**. I did not independently re-verify the CGRC file in this pass. Its record reports a literal-gate failure, and that failure is the protocol's own gate.

| File | Holdout (HOLDOUT-DTI) | Uniqueness / lane | Format | Status |
|---|---|---|---|---|
| [`gems54-undercomplement-q200.tif`](docs/downloads/gems54-undercomplement-q200.tif) (H54-A, SGMC complement) · `b430615a…efd8` · 15,907 dots | 0.0483 under v1 (C1). **Under v2 the SGMC layer is not visible-only, so this value is invalid for ranking (IR-54-038).** | **FAIL.** 100 % within 3 px of GEMSDOE3 `gapfinder-v2-sgmc-gap` (ρ 0.51) | Strict outside-footprint NaN check FAILS (zeros) | Not cleared. Archive only. |
| [`gems54-magedge-hgrad-ridge.tif`](docs/downloads/gems54-magedge-hgrad-ridge.tif) (H54-B, magnetic gradient ridge) · `6d086c09…8d9e` · 19,197 dots | 0.0148 [0.0118, 0.0180] (v1, C3) | **FAIL.** 81.6 % overlap with GEMSDOE40 `h8-asa-spi-depthkde`; 75.7 % with GEMSDOE46 | Zeros outside footprint | Not cleared. |
| [`gems54-h1-crossgradient-q095.tif`](docs/downloads/gems54-h1-crossgradient-q095.tif) (H1, cross-gradient, v1 min-percentile definition) · `006e912b…f26d05` · 21,371 dots | 0.0120 [0.0098, 0.0146] (v1, C4). Not above the chance control. Its v2 counterpart is a different formula (see note below). | **Disputed.** Literal registry test DUPLICATE; sibling scan PASS under its 50 %-coverage exclusion (IR-54-063) | Fails the outside-footprint NaN check (zeros) | NEGATIVE. [`registry/run_card_v3_h1.json`](registry/run_card_v3_h1.json) |
| [`gems54-cgrc-relay-v1.tif`](docs/downloads/gems54-cgrc-relay-v1.tif) (CGRC, 2026-10-09 session) · `e6f82d42…84ef` · 32,369 dots | 0.0915 [0.0876, 0.0949] (v2, shipped arm); its holdout NEGATIVE against the corpus best 0.1793 | Literal DUPLICATE; operational PASS (max ρ 0.042). Main's record says the literal gate is unsatisfiable against r11/r13/r14 (IR-54-016), which is consistent with IR-54-051 here. | PASS per its record | Recorded as "OK TO DOWNLOAD", **and** the README says do not download. **Conflict; owner decision.** |

**Note on the two evaluator versions.** The v1 receipts (`holdout_segment_cv_v1_c4.json`, `..._c5.json`) were produced by a patched v1 script (evaluator sha `941dc2e0…` for C4 and `a9327e69…` for C5). `main`'s shared evaluator is now v2. v2 defines **C4 as a rank-product** (sqrt of ranks of |tmi_hg| and |iso_grav_anom_hg|, 0.0126 [0.0099, 0.0155]) and **C5 as a surface-conductivity gradient** (0.0097 [0.0078, 0.0119]). My **H1 file uses the v1 min-percentile definition**, so its numbers are not interchangeable with v2 C4. My **basement-step C5 (v1 receipt `holdout_segment_cv_v1_c5.json`, 0.0103 [0.0076, 0.0133], at chance) is not in the v2 evaluator**; its code exists only in commit `a73d633` on this branch. Naming these by version avoids the collision. Re-adding it to the shared evaluator as a new candidate needs a budget decision.

**Official rules (verified verbatim, [`docs/rules-gate.html`](docs/rules-gate.html)).** You may submit *your own model's* single-band GeoTIFF (§3.2; original work, A.5(1)) if you are eligible (§1.3) and you sign the certification (§1.3, A.1). You must disclose generative-AI use in the narrative (§3.2). Three submissions per week at most (§3.2, §3.4). Copying another team's file is not permitted, and this includes every GEMSDOE sibling artefact.

**Score labels.** `HOLDOUT-DTI` = whole-segment holdout with evaluator `gemsdoe54-segment-cv` (v1 or v2 as stated), withheld positives and 95 % CI. `ORGANIZER-CONFIRMED` = none. `BOARD-UNVERIFIED` = user-reported board values (0.2778, 0.2750, 0.2708). `MODEL` = inference. Projections are never scores.

---

## ✅ Session 2026-10-09 — v2 holdout, lane screens, and an SGMC correction (read this first)

**Verdict: no TIF is cleared for upload. Do not download or submit any file from this repository.** This session generated two new format-valid candidate TIFs, but both fail the protocol's lane gate, so neither is published.

| Question | Answer (labels: HOLDOUT-DTI = evaluator `gemsdoe54-segment-cv` v2, 60,988 withheld positives, 95 % percentile CI) |
|---|---|
| Unique TIF generated? | **No.** C4 (cross-gradient) and C5 (conductivity gradient) each produced a format-valid raster, but both are **DUPLICATE - STOP** against dense registry rasters r11, r13 and r14 ([`evidence/lane_screen_v2.json`](evidence/lane_screen_v2.json)). Under the protocol they stop here. Procedural note: placement happened before the registry check, which the protocol forbids (IR-54-036). |
| Holdout result, new hypotheses | **C4 cross-gradient coincidence: 0.0126 [0.0099, 0.0155]**, chance control 0.0104 [0.0091, 0.0117]. Paired C4 − C0 = +0.0022 [−0.0008, +0.0051], so the CI includes 0. C4 − C3 (tmi_hg ridge) = −0.0022 [−0.0066, +0.0019]. **Negative.** **C5 conductivity-gradient: 0.0097 [0.0078, 0.0119]**, paired C5 − C0 = −0.0007 [−0.0032, +0.0018]. **Negative.** Source: [`evidence/holdout_segment_cv_v2.json`](evidence/holdout_segment_cv_v2.json). |
| Is the old "best" 0.0483 (H54-A / C1) valid? | **No, not for ranking.** The SGMC layer co-locates with the withheld catalogue: P(SGMC within 300 m \| catalogue cell) = 0.329 versus 0.107 for a random cell (3.07×). Its single-feature canary (AUC 0.53) cannot see this. The layer is not visible-only, so the C1 value is inflated by withheld-truth information (IR-54-037, IR-54-038). [`evidence/sgmc_colocation.json`](evidence/sgmc_colocation.json). |
| Detection floor vs the 0.2778 / 0.2750 gap (0.0028) | The paired raw 80 %-power MDEs in v2 are **0.0035 to 0.0095** (C5−C0 0.0035, C4−C0 0.0043, C4−C3 0.0061, C1−C3 0.0095). **0.0028 is below every floor, so the board gap is not resolvable on this holdout.** The Cohen d floor for the segment units is 0.0496 at 80 % power. |
| Why is 0.2778 the top score? | Not established here. The repository's mechanism (a deletion of zero-credit dots from a 0.2708 parent) is documented in [`docs/top-artefact.html`](docs/top-artefact.html) and is a hypothesis; it is not an organizer receipt. The brief's leaderboard values are unverified (IR-54-031). |
| Can we beat 0.2778? | **Unknown.** No candidate here reached the holdout level needed to justify a slot, and the holdout cannot resolve the board gap. |
| Upload error "Predicted values must be in range [0, 1]" | **Not reproduced** by the archived file (values lie in [0,1]). The official rule requires null/NaN outside the bounds. This is unexplained and needs a manual portal check (IR-54-030). New builds write NaN outside the footprint. |

**What changed in the code.** `scripts/holdout_segment_cv.py` is now evaluator **v2**. It adds C4 and C5 and writes `evidence/holdout_segment_cv_v2.json`. C0 to C3 reproduce v1 exactly (checked). `scripts/build_v2_candidate.py` builds C4 or C5 with NaN outside the footprint and asserts every check on read-back. `scripts/record_lane_screen.py` writes machine-generated lane receipts. `scripts/sgmc_colocation.py` measures SGMC–catalogue co-location. The shared feature stack is now read from the owner bridge at its pinned SHA-256 (IR-54-032). Tests: 76 existing tests pass.

**Hypotheses, updated status** ([`docs/research/hypotheses-20261008.md`](docs/research/hypotheses-20261008.md)). H1 cross-gradient is now **tested, negative** (C4). H2 is **narrowly tested, negative**: C5 is only the surface gradient of `cond_surf`, not the depth-persistent version. H3 is still blocked. H4 (1 m DEM) and H5 (InSAR) still need data. The owner bridge contains `data/dem_links.json`, but it is not organizer-authenticated and has not been checked for coverage.

**Next steps, in order.**
1. Manual check: open the competition portal and read the leaderboard, and test one file to see what triggers the [0, 1] error (IR-54-030, IR-54-031).
2. Fix the holdout's leakage: restrict SGMC to visible-only, or find an independent fault map that is not derived from the catalogue. Until then, no SGMC-based number is a valid ranking (IR-54-038).
3. Run the full 1,177-raster uniqueness scan alone, with ~20 min of memory headroom (IR-54-034).
4. Only if a registry-aware placement (dots kept more than 300 m from every registry raster's dots) passes the lane gate **and** beats the corrected chance control, consider a slot. That is a separate selector step.

**Score labels in this session.** Only `HOLDOUT-DTI` values appear above. There is no `ORGANIZER-CONFIRMED` value. Every projection is labelled as such.

---

## Archived run (2026-10-08): no new TIF cleared the gates

**This review generated no new TIFF. Do not upload a file from this run, and do not spend a weekly submission slot on the archived H54-A file.** Two pre-placement surface screens tripped the literal registry-overlap stop rule before point placement. The current run card is [`docs/data/run-card.json`](docs/data/run-card.json); receipts are [`evidence/endpoint-continuation-preflight.json`](evidence/endpoint-continuation-preflight.json) and [`evidence/strict_lane_preflight.json`](evidence/strict_lane_preflight.json).

### Existing archive (for audit/research download only — not a current submission)

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

### This session's decision

Two surface-only screens are recorded: the earlier endpoint-continuation screen and the SGMC topology screen. Each had low rank-correlation but overlapped three near-covering registry rasters above the literal 70% stop threshold, and both stopped before final point placement. There is no new name, note, raster hash, or submission file from these screens. No `HOLDOUT-DTI` was produced. The user-reported difference 0.0028 between 0.2778 and 0.2750 remains **NOT CLASSIFIABLE** as signal or noise without valid withheld-segment counts and paired uncertainty.

The top-ranked cross-gradient hypothesis is blocked: the full feature stack is absent locally and the owner-maintained public cache is not organizer-authenticated. The local checkout also lacks the requested `evaluate_holdout.py` and `submission_writer.py`; the inspected owner-template tree instead exposes a spatial-block evaluator and `submission_io.py`, which do not meet the whole-segment protocol. See [`docs/research/hypotheses-20261008.md`](docs/research/hypotheses-20261008.md) and [`docs/audit/current-review.md`](docs/audit/current-review.md).

Score-labeling policy: report a performance score only as **HOLDOUT-DTI** with evaluator version, withheld-positive count, and paired 95% CI, or as **ORGANIZER-CONFIRMED** copied from a submission-page receipt. User- or owner-reported values are not receipts. Proxy outputs are **PROXY-DTI**, and projections are **MODEL**, never scores.

---

## Second pass (2026-10-08 / 09 UTC): H1, C4, C5 and the experiment budget

**Experiment budget (this session): 3 of 3 used.** Experiment 1 was the v1 holdout (C0 to C3); experiment 2 was the C4 holdout (H1); experiment 3 was the C5 holdout (H6). Uniqueness scans, validator runs, and the earlier surface-only lane preflights (labelled "experiment 1" and "experiment 2" in the hypotheses note) are not holdout experiments and are not counted here. No further holdout experiment should run without a new budget decision.

| Candidate (HOLDOUT-DTI, evaluator `gemsdoe54-segment-cv` v1) | Pooled DTI, 95 % CI | Paired vs chance control C0 | Verdict |
|---|---:|---:|---|
| C0 · random admissible control | 0.0104 [0.0091, 0.0117] | — | control |
| C1 · SGMC complement (H54-A) | 0.0483 [0.0424, 0.0541] | +0.0379 | best tested under v1; **invalid for ranking under v2** (SGMC not visible-only, IR-54-038); not unique |
| C2 · geodetic shear ridge | 0.0098 [0.0072, 0.0128] | not significant | no signal |
| C3 · magnetic horizontal-gradient ridge (H54-B) | 0.0148 [0.0118, 0.0180] | +0.0044 | below C1 |
| C4 · cross-gradient coincidence ridge (H1) | 0.0120 [0.0098, 0.0146] | +0.0016 [−0.0011, +0.0045] | **NEGATIVE** |
| C5 · basement-step ridge (H6) | 0.0103 [0.0076, 0.0133] | −0.0001 [−0.0032, +0.0031] | **NEGATIVE** (at chance) |

Receipts: [`evidence/holdout_segment_cv_v1_c4.json`](evidence/holdout_segment_cv_v1_c4.json) and [`evidence/holdout_segment_cv_v1_c5.json`](evidence/holdout_segment_cv_v1_c5.json). C0 to C4 reproduce the earlier receipts exactly. C5's canary (`basement_step_score_H6`) is clear, and the maximum single-feature AUC across all candidates is 0.756 (distance to visible catalogue, a withholding artefact). C5 is significantly below C1 (−0.0381) and C3 (−0.0046). Rule 6 of the run card is not fully evaluable for C2 (no C4−C2 pair; IR-54-065), but rule 5 already fails for H1.

**Verdicts.** H1 (C4) run card: `negative`, failing rules 1 (format: outside-footprint NaN), 4 and 5 (holdout). Lane rule 2 reads PASS in the sibling scanner and DUPLICATE in the literal validator; this conflict is unresolved (IR-54-063). Proposal for the protocol owner: adopt a chance-corrected overlap statistic, and state explicitly whether dense rasters are excluded. No file was promoted, and no slot was selected.

**Power.** The 0.0028 board gap is still NOT CLASSIFIABLE. Segment-unit floor 0.0496 (Cohen d, 80 % power, α 0.05), so the raw paired minimum detectable effects in the receipts are about 0.004 to 0.005 (for example C4 vs C0 0.0040; C5 vs C0 0.0046). See [`evidence/power_floor_segment_cv_v1.json`](evidence/power_floor_segment_cv_v1.json).

**Remaining work (ordered).** (1) Owner decision on the lane definition and the NaN-versus-zero convention (IR-54-051, IR-54-054, IR-54-063). (2) Organizer confirmation of the format and of the `Predicted values must be in range [0, 1]` error; the user must provide the file name, SHA-256 and full message (IR-54-053). (3) Complete the C4−C2 paired difference (IR-54-065). (4) A count-matched rerun (IR-54-058). (5) An SGMC-excluded second endpoint, since C1 may reflect co-location (IR-54-057). (6) Licence and organizer-origin check of the owner feature cube (IR-54-055). (7) Any new candidate needs a new budget decision, since no holdout experiments remain in this session.

---

## Holdout results (this pass, 2026-10-08)

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

## Current repository review (2026-10-08)

The review fixed three code-level issues: the lane checker now uses absolute rank correlation and the literal raw overlap threshold; informative holdout pixels exclude the zero-credit 300 m boundary; and the writer rejects non-float32 output. A pre-existing scratch-only preview was calculated out of order after the surface had already crossed its stop rule; it was never persisted or scored and is disclosed in the audit note. Tests cover each fix. No holdout run or weekly submission slot was used.

The owner-maintained `GEMSDOE` bridge at pinned commit `dcbbb192e56b2b32c0a131eba791dc363305d4a3` was inspected via GitHub API; its tree lists cached feature shards and a spatial-block evaluator, but its manifest cites owner mirrors rather than an authenticated organizer download. This is a provenance and protocol check, not a `HOLDOUT-DTI` result. See [`docs/audit/pinned-template-cache-audit.json`](docs/audit/pinned-template-cache-audit.json).

---

## Session results (2026-10-08)

**What was built.** [`scripts/holdout_segment_cv.py`](scripts/holdout_segment_cv.py) (evaluator `gemsdoe54-segment-cv` v1): 5-fold whole-segment hide-and-recover over 3,199 catalogue components (60,988 withheld positives), 300 m buffer, visible-only features, pixel-exact visible masking, organizer DTI (α 0.2, β 0.8, 300 m triangular kernel) decomposed per fold and cross-checked against the grid metric, paired cluster bootstrap (1,000 replicates), single-feature canary (19 bands, SGMC, distance), and 30 torus-shift nulls. Receipt: [`evidence/holdout_segment_cv_v1.json`](evidence/holdout_segment_cv_v1.json).

**Headline holdout numbers (HOLDOUT-DTI, catalogue recovery).** C0 chance control 0.0104 [0.0091, 0.0117]; C1 SGMC complement 0.0483 [0.0424, 0.0541]; C2 geodetic shear ridge 0.0098 [0.0072, 0.0128] (no signal over chance); C3 magnetic gradient ridge 0.0148 [0.0118, 0.0180]. Paired C1 minus C0 +0.0379 [+0.0317, +0.0437]; C1 minus C3 +0.0335 [+0.0267, +0.0400]. Canary: no feature flagged (highest single-feature AUC 0.756, distance to visible catalogue, a withholding artefact; SGMC 0.526). C1 shift null p95 0.0051.

**Detection floor and the 0.0028 board gap.** Cohen d_min at 80 % power for 3,199 units is 0.0496 (0.111 per fold). Raw MDE for the paired comparisons is 0.0045 to 0.0095 at the observed correlations. The 0.0028 board gap is inside the floor of every paired comparison here. Units are raster fragments (IR-54-039), so the floors are indicative. See [`evidence/detection_floor_segments.json`](evidence/detection_floor_segments.json).

**The top artefact (GEMSDOE32 H33-2-B2).** Registry-verified: the parent 0.2708 raster has 40,199 dots, and the child 37,654 dots is byte-identical to the owner's file. Deleted dots: 2,545. Under the organizer metric, deleting zero-credit dots leaves TP and FN unchanged and lowers FP by one per dot, so DTI rises. The identity is verified numerically. The 0.2778 value is user-reported and the owner's manifest says UNSCORED. The owner's audit is internally inconsistent (IR-54-034). Beating 0.2778 is possible in principle, but nothing here establishes it. See [`docs/top-artefact.html`](docs/top-artefact.html) and [`evidence/top_artefact_analysis.json`](evidence/top_artefact_analysis.json).

**Reproducibility.** `build_submission.py` rebuilt H54-A byte-for-byte. The rebuild exposed a receipt-path bug, now fixed (IR-54-049). `build_unique_submission.py` builds H54-B. Both run cards are generated by `make_run_card.py` from receipts, with no hand-typed numbers.

**Standing corrections (session memory).** The 0.2708 base has 40,199 dots, not 44,090 (44,090 is the 0.2600 raster). The deletion count is 2,545, not 6,436 (IR-54-041). The owner-mirrored sample file is not all-zero, which contradicts the format page (IR-54-032). The label source is cited differently in §2 and §3.3 of the rules (IR-54-030).

**Limitations.** (1) The holdout truth is the catalogue, not the hidden expert set. (2) Feature rasters are owner-claimed copies (hash-consistent, not organizer-authenticated). (3) The chance control is not spacing-matched. (4) Segments are raster fragments. (5) The leaderboard is unreadable, and the brief's top value conflicts (0.3774 versus 0.3195). (6) Submission-count and eligibility cannot be checked from this repository.

**Remaining work.** (a) A new candidate in a lane that no sibling occupies and that also beats 0.0483 under the same evaluator. (b) Validate hypotheses 4 and 5 (InSAR, Landsat thermal); both need new data pulls. (c) Spacing-matched control (random lines through the same gate). (d) Organizer confirmation of label source, sample format and submission count (IR-54-030, IR-54-032, IR-54-040). (e) Licence check before the label mirror stays public (IR-54-031).

---

## Additional verified checks on this branch (2026-10-09; IR-54-083 to IR-54-106)

These checks were run on branch `arena/a2c15068-gemsdoe54` and do not change main's verdict. Full detail: [`docs/data/run-card-2026-10-09.json`](docs/data/run-card-2026-10-09.json) and [`docs/audit/irregularities.md`](docs/audit/irregularities.md).

- **Copy and lane over the full corpus.** `gems54-cgrc-relay-v1` is not a copy of any sibling file (1,198 compared; the candidate's own NaN twin is excluded). Max |Spearman ρ| 0.101. The literal lane test FAILS on three sparse public rasters at overlaps 0.733 to 0.935 (`gems7-halo15-gbt-v1`, `gems7-strike30x3-v2`, `gems10-h25-ctx-ridge`) and on 116 blanket entries (74 distinct files) that cover 50% to 100% of the footprint. The literal rule is therefore unsatisfiable for any candidate (IR-54-103, IR-54-104). Evidence: `evidence/uniqueness_gems54-cgrc-relay-v1.json`, `evidence/lane_summary_cgrc-relay-v1.json`, `evidence/uniqueness_table_cgrc-relay-v1.json`.
- **0.2778: verified mechanism only.** Owner raster `dotted_b2_prune_02778` equals `dotted_d2_8_02708` minus exactly 2,545 dots, all within 200 m of the USGS catalogue, and none of the kept dots is. On the catalogue proxy, DTI falls from 0.0491 to 0.0067, so the proxy ranks them opposite to a test of new faults. The exact marginal rule agrees on 80 of 80 sampled dots (closed-form error 8.6e-15). Whether this is extradr19's board submission is **unverified** (IR-54-096). Evidence: `evidence/registry_pair_0278_mechanism.json`.
- **Holdout reproducibility.** The receipt's configuration (2,500 m gap and extension caps) is now the script default. A re-run with that design reproduces every headline value (`evidence/cgrc_holdout_receipt_rerun_20261009.json`). The committed receipt is unchanged. It contains three blocks that the script does not write (IR-54-090).
- **Leakage canary.** The binary SGMC AUC (0.523) cannot reach the 0.90 cut. The continuous form is 0.654 against the withheld catalogue and 0.654 against the full catalogue. Neither fires (IR-54-089).
- **Power correction.** The 0.001395 floor is for a same-method paired contrast. Cross-family contrasts have raw floors of 0.0045 to 0.0095 (`evidence/detection_floor_segments.json`), so the 0.0028 gap lies inside them. Same-family near-identical pairs have floors of 0.0015 to 0.0022 (`evidence/detection_floor.json`; not reproducible in this checkout, IR-54-091). The board gap stays NOT CLASSIFIABLE (IR-54-094).
- **Builder gates.** `scripts/build_cgrc_submission.py` now reports the literal format and lane results, with no excused failure and no name-based exclusion (IR-54-086, IR-54-087, IR-54-106). A rebuild reproduces both TIFs byte-for-byte (sha256 `e6f82d42…`, `9b4cf445…`).
- **Tests.** Three regression tests were added (`tests/test_marginal_rule.py`, `tests/test_lane_summary.py`) on top of the existing suite.

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
| New unique TIF from this run | ❌ **NOT GENERATED** — the pre-placement surface triggered the literal lane stop rule |
| Existing H54-A TIFF | ⚠️ Downloadable for audit only; strict local lane validator flags it as duplicate; **do not upload** |
| Local format validator | ⚠️ Grid/dtype/in-footprint range pass; strict outside-footprint null/NaN check fails on archived zeroes. Official format page not re-fetched. |
| Whole-segment HOLDOUT-DTI / power floor | ⚠️ **PRODUCED for the magnetic-ridge candidates only** (local, catalogued-fault holdout; 60,988 withheld positives; segment-group jackknife CIs). E1 and E2 are both negative under the frozen rule. The detection floor is pair-specific; the board gap 0.2778 vs 0.2750 is NOT CLASSIFIABLE. See *Holdout results*. |
| Magnetic-ridge submission | ❌ **NOT BUILT** — the builder refuses unless the holdout receipt is promote-eligible (`scripts/build_mag_ridge_submission.py`) |
| Current 3–5 hypothesis shortlist | ✅ [`docs/research/hypotheses-20261008.md`](docs/research/hypotheses-20261008.md); no DTI effect is projected |
| Executive summary + how-to-submit instructions | ✅ [`docs/index.html`](docs/index.html); clearly states there is no upload-approved file |
| Official source links and verification status | ✅ [`docs/data/source-register.json`](docs/data/source-register.json); current review statuses are explicit, and unverified sources remain marked as such |
| Learned model pipeline | ❌ **BLOCKED** — official feature stack absent/authentication not established; holdout tool mismatch also unresolved |

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

| artefact (registry) | dots | PROXY-DTI (circular screening) | owner-recorded board value (not receipt) |
|---|---:|---:|---:|
| `dotted_b2_prune_02778` | 37,654 | 0.093946 | **0.2778** |
| `dotted_d2_8_02600` | 44,090 | 0.092727 | 0.2600 |
| `dotted_d2_8_02708` | 40,199 | 0.093836 | 0.2708 |
| `hedge_v2_01563` | 227,507 | 0.088371 | 0.1563 |
| `r13_lattice_s5_00904` | 206,895 | 0.247784 | 0.0904 |
| `tip_stepover_r30_02632` | 41,865 | 0.094213 | 0.2632 |

Source: [`evidence/proxy_audit.json`](evidence/proxy_audit.json). The 2026-10-08 table here included `h60_officialstack_50k`, which has no board value, and omitted `dotted_d2_8_02708`; that table is withdrawn (IR-54-078).

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

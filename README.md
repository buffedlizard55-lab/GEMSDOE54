# GEMSDOE54 — GEMS Prize submission repository

> **Read this file first, every session.** It contains the standing project charter,
> evidence limitations, the current status, and explicit download/upload decisions.

---

## ⬇️ SUBMISSION STATUS — read this first (updated 2026-10-09)

**DOWNLOAD: audit copy only · SUBMIT: ⛔ NOT OK.** No file in this repository is cleared for upload. Start page: [`docs/index.html`](docs/index.html) · summary and how-to-submit: [`docs/executive-summary.html`](docs/executive-summary.html) · verdict and owner decisions: [`docs/submit-verdict.html`](docs/submit-verdict.html).

Why (the decisive reason is the lane gate; the holdout is not the reason):

1. **Not a copy.** No exact-file or decoded match against 1,198 public sibling rasters (the candidate's own NaN twin excluded). Max |Spearman ρ| = 0.101.
2. **Lane duplicate.** `gems54-cgrc-relay-v1` puts more than 70% of its dots within 3 px of dots in r11, r13 and r14 (this repository's registry), and of three sparse public rasters at 0.733 to 0.935. The protocol says log duplicate and stop.
3. **The literal rule cannot be met by any candidate** while blanket rasters remain in the reference set: 116 entries (74 distinct files) cover 50% to 100% of the footprint. Owner decision D1.

| File | Download | Submit | Format (validator) | Lane (literal) | HOLDOUT-DTI (v2, proxy) | sha256 |
|---|---|---|---|---|---|---|
| [`docs/downloads/gems54-cgrc-relay-v1.tif`](docs/downloads/gems54-cgrc-relay-v1.tif) (all finite) | audit copy | ⛔ NOT OK | fails "outside must be null or NaN" (7,111,787 cells); range test passes | DUPLICATE: r11 0.833, r13 0.998, r14 0.857 | arm B 0.0915 [0.0876, 0.0949] | `e6f82d42…84ef` |
| [`docs/downloads/gems54-cgrc-relay-v1-nan.tif`](docs/downloads/gems54-cgrc-relay-v1-nan.tif) (NaN outside) | audit copy | ⛔ NOT OK | passes all checks | DUPLICATE (same dots) | same dots | `9b4cf445…a0de` |
| [`docs/downloads/gems54-undercomplement-q200.tif`](docs/downloads/gems54-undercomplement-q200.tif) (H54-A, earlier) | audit copy | ⛔ NOT OK | not re-run | FAIL in the prior receipt (1.0 overlap with an SGMC input layer; blankets) | not reported | `b430615a…efd8` |

**Name:** GEMS54-CGRC-relay-v1 · **Note (124 characters):** Catalogue-tip relay dots, SGMC-weighted. NOT OK to submit: lane DUPLICATE (r11/r13/r14; 3 sparse siblings). Audit copy only.
Machine-readable run card: [`docs/data/run-card-2026-10-09.json`](docs/data/run-card-2026-10-09.json).

**Board facts (ORGANIZER-PUBLIC, leaderboard page fetched 2026-10-09; not submission-page receipts).** #1 0.3774 · #7 0.3195 · #13 0.2778 (extradr19) · #17 0.2750 (wbg1). The public board scores the public test set only. The initial prize round is scored on a private test set; the final round rescores against expanded labels.

**Answers to the review questions**

- **Why 0.2778 scored well.** Verified: the owner raster `dotted_b2_prune_02778` is `dotted_d2_8_02708` minus exactly 2,545 dots, all within 200 m of the USGS catalogue (`evidence/registry_pair_0278_mechanism.json`). On the catalogue proxy this deletion lowers DTI from 0.0491 to 0.0067, so the proxy ranks them opposite to a test of new faults. Hypothesis (untested): dots beside mapped faults earn little credit on new faults but cost false-positive mass; the exact marginal rule (verified 80/80) says removing them then helps. Unverified: that extradr19 used this method.
- **Can we beat it?** Not demonstrated. No candidate here has an organizer score, and the only evaluator is a catalogue proxy that ranks this design in reverse.
- **Can the holdout resolve 0.2778 vs 0.2750?** NOT CLASSIFIABLE. Cross-family paired floors are 0.0045 to 0.0095 (0.0028 is inside); same-family near-identical pairs have floors of 0.0015 to 0.0022. The board publishes no unit count or per-unit contributions, so no floor can be computed for it. (`evidence/detection_floor_segments.json`; `evidence/detection_floor.json` is not reproducible in this checkout, IR-54-058.)
- **Hypotheses.** Five ranked in [`docs/research/hypotheses-20261008.md`](docs/research/hypotheses-20261008.md) (re-ranked 2026-10-09 at the top): cross-gradient potential fields; depth-persistent conductivity; seismicity lineaments; state-map node topology; 1 m DEM scarps. All are blocked or circular here. The top one is **not validated**, so no slot is used.
- **Reproducibility.** Both CGRC TIFs rebuild byte-identically. The CGRC holdout reproduces every headline value exactly once the CLI defaults are corrected (IR-54-057). Magnetic-ridge and raster-floor numbers are receipt-only (IR-54-058).
- **Irregularities.** IR-54-050 to IR-54-073 in [`docs/audit/irregularities.md`](docs/audit/irregularities.md). IR-54-050 records that earlier citations to IR-54-030 to -049 are undefined.

**Decisions the owner must make** (details in [`docs/submit-verdict.html`](docs/submit-verdict.html#decisions)):
- **D1** lane-rule scope: the literal rule is unsatisfiable over the corpus; decide whether to exempt blanket rasters and whether input layers count.
- **D2** the meaning of "data outside the bounds is null or nan": raster extent (all-finite file complies) or study footprint (NaN twin complies). The portal's "[0,1]" error is a range failure, so the all-finite encoding is the range-safe choice.
- **D3** the promotion comparator "0.1793" has no receipt; drop it or source it.

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

## 2. Honest status in one screen (updated 2026-10-09)

| Item | Status |
|---|---|
| Unique TIF (CGRC v1) | ⚠️ **Not a copy, but a lane duplicate** of r11, r13, r14 and of three sparse public rasters. Not cleared. Rebuilds byte-identically. |
| H54-A TIF | ⛔ Lane FAIL in the prior receipt (1.0 overlap with an SGMC input layer). Audit copy only. |
| Local format validator | ✅ NaN twin passes every check. ⛔ All-finite primary fails the outside-cells reading (D2). |
| Whole-segment HOLDOUT-DTI | ✅ CGRC arm B 0.0915 [0.0876, 0.0949] (gemsdoe54.cgrc-holdout.v2, reproduced 2026-10-09). ⚠️ Magnetic-ridge numbers are receipt-only (IR-54-058). |
| Leakage canary | ✅ Fixed: the binary form cannot fire; the continuous form is 0.654 (withheld) and 0.654 (full catalogue). Below the 0.90 cut. |
| Detection floor and the 0.0028 gap | ✅ Answered: NOT CLASSIFIABLE on the board. The power-analysis note is marked superseded (IR-54-060). |
| Hypotheses (ranked) | ✅ Re-ranked with layers, signature, rationale, cost. Top hypothesis not validated (feature file absent). No slot used. |
| Executive summary and how-to-submit | ✅ [`docs/executive-summary.html`](docs/executive-summary.html) and [`docs/submit-verdict.html`](docs/submit-verdict.html) |
| Official source links and verification | ✅ Re-verified 2026-10-09: DrivenData overview (wording quoted), leaderboard, NLR rules PDF (chunks 0 to 6), HeroX landing. See [`docs/data/source-register.json`](docs/data/source-register.json). |
| Learned model pipeline | ❌ Blocked: the official feature file is absent and its authenticated copy is not available. |
| Tests | ✅ `PYTHONPATH=src pytest -q`: 97 passed on 2026-10-09 (94 before this review, plus 3 regression tests for the marginal rule and the lane summary). |

---

## 3. What this repository actually found

_Written on 2026-10-08. Corrections from the 2026-10-09 review are in the status block above and in `docs/audit/irregularities.md` (IR-54-050 to IR-54-073). Where this section and the status block disagree, the status block is current._

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

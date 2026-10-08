# GEMSDOE54 — GEMS Prize submission repository

> **Read this file first, every session.** It contains the standing project charter,
> evidence limitations, the current status, and explicit download/upload decisions.

---

## ⛔ Current run: no new TIF cleared the gates

**This review generated no new TIFF. Do not upload a file from this run, and do not spend a weekly submission slot on the archived H54-A file.** The pre-placement surface screen tripped the literal registry-overlap stop rule before point placement. The full run card is [`docs/data/run-card.json`](docs/data/run-card.json), and its reproducible preflight receipt is [`evidence/strict_lane_preflight.json`](evidence/strict_lane_preflight.json).

### Existing archive (for audit/research download only — not a current submission)

- **File:** [`docs/downloads/gems54-undercomplement-q200.tif`](docs/downloads/gems54-undercomplement-q200.tif)
- **SHA-256:** `b430615afe94c317d147122f274c85d2d96f2f35369b25ee1116c12c79a3efd8`
- **Bytes:** 94,282 · **Positive cells:** 15,907 (archived build receipt; not a score)

| Gate | Current review result | Evidence |
|---|---|---|
| Format / range / grid | ✅ **PASS** under the current local validator; not organizer acceptance | [`evidence/h54a-archive-strict-revalidation.json`](evidence/h54a-archive-strict-revalidation.json) |
| Literal lane uniqueness | ❌ **DUPLICATE — STOP**: raw 3-pixel overlap exceeds 70% for three dense registry rasters | [`evidence/h54a-archive-strict-revalidation.json`](evidence/h54a-archive-strict-revalidation.json) |
| Required whole-segment hidden-label holdout | ❌ **NOT ESTABLISHED**; no compliant evaluator, withheld-positive count, paired 95% CI, or detection floor | [`docs/research/power-analysis.md`](docs/research/power-analysis.md) |
| Safe to upload / weekly slot selected | ❌ **NO** | [`docs/data/run-card.json`](docs/data/run-card.json) |

The archived raster is retained for audit history and can be downloaded for local inspection, but **this repository does not recommend submitting it**. A format-valid GeoTIFF is not evidence of geological validity or competition performance.

### This session's decision

The single surface-only screen used owner-mirrored SGMC and local catalogue rasters. It had low registry rank-correlation, but its support overlapped three near-covering registry rasters above the literal 70% stop threshold. The run stopped before final point placement; there is no new name, note, raster hash, validator receipt, or submission file from this session. No `HOLDOUT-DTI` was produced. The user-reported difference 0.0028 between 0.2778 and 0.2750 remains **NOT CLASSIFIABLE** as signal or noise without valid withheld-segment counts and paired uncertainty.

The top-ranked cross-gradient hypothesis is blocked: the full feature stack is absent locally and the owner-maintained public cache is not organizer-authenticated. The local checkout also lacks the requested `evaluate_holdout.py` and `submission_writer.py`; the inspected owner-template tree instead exposes a spatial-block evaluator and `submission_io.py`, which do not meet the whole-segment protocol. See [`docs/research/hypotheses-20261008.md`](docs/research/hypotheses-20261008.md) and [`docs/audit/current-review.md`](docs/audit/current-review.md).

Score-labeling policy: report a performance score only as **HOLDOUT-DTI** with evaluator version, withheld-positive count, and paired 95% CI, or as **ORGANIZER-CONFIRMED** copied from a submission-page receipt. User- or owner-reported values are not receipts. Proxy outputs are **PROXY-DTI**, and projections are **MODEL**, never scores.

---

## Current repository review (2026-10-08)

The review fixed three code-level issues: the lane checker now uses absolute rank correlation and the literal raw overlap threshold; informative holdout pixels exclude the zero-credit 300 m boundary; and the writer rejects non-float32 output. A pre-existing scratch-only preview was calculated out of order after the surface had already crossed its stop rule; it was never persisted or scored and is disclosed in the audit note. Tests cover each fix. No holdout run or weekly submission slot was used.

The owner-maintained `GEMSDOE` bridge at pinned commit `dcbbb192e56b2b32c0a131eba791dc363305d4a3` was inspected via GitHub API; its tree lists cached feature shards and a spatial-block evaluator, but its manifest cites owner mirrors rather than an authenticated organizer download. This is a provenance and protocol check, not a `HOLDOUT-DTI` result. See [`docs/audit/pinned-template-cache-audit.json`](docs/audit/pinned-template-cache-audit.json).

---

## 1. The standing prompt

The following is the persistent project charter distilled from the full user prompt. It preserves the actionable requirements and exact holdout/lane rules; repeated prose and the long sibling-site score inventory are summarized because those values are user/owner claims, not verified organizer receipts. Read the linked current run card and source register for this session's status.

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

**Evidence note:** the standing charter above summarizes the user's repeated requirements and preserves the main protocol. The long historical sibling-site score inventory is user-supplied/owner-reported and is not treated as verified without a corresponding organizer receipt.

---

## 2. Honest status in one screen

| Item | Status |
|---|---|
| New unique TIF from this run | ❌ **NOT GENERATED** — the pre-placement surface triggered the literal lane stop rule |
| Existing H54-A TIFF | ⚠️ Downloadable for audit only; strict local lane validator flags it as duplicate; **do not upload** |
| Local format validator | ✅ Re-read and passes the archived raster's range/grid checks; not organizer acceptance |
| Compliant whole-segment HOLDOUT-DTI / power floor | ❌ **NOT PRODUCED** — no complete evaluator, withheld-positive count, or paired CI |
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

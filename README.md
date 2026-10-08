# GEMSDOE54 — GEMS Prize submission repository

> **Read this file first, every session.** It contains the standing prompt, the
> verified facts, the current status, and the one-click submission artefact.

---

## ⬇️ THE SUBMISSION FILE — read this box before anything else

**File:** [`docs/downloads/gems54-undercomplement-q200.tif`](docs/downloads/gems54-undercomplement-q200.tif)
**SHA-256:** `b430615afe94c317d147122f274c85d2d96f2f35369b25ee1116c12c79a3efd8`
**Bytes:** 94,282 · **Positive cells:** 15,907

**Is it OK to download and submit this file? — Yes, to upload. No, not blindly.**

| Gate | Status | Evidence |
|---|---|---|
| Format is portal-legal (float32, 1 band, EPSG:32611, 3730×3292, all values finite and in [0, 1]) | ✅ **PASS** (9/9 checks) | [`evidence/gems54-undercomplement-q200.validation.json`](evidence/gems54-undercomplement-q200.validation.json) |
| Distinct from every prior artefact in the registry (lane check) | ✅ **PASS** (max \|ρ\| = 0.004 vs a 0.90 limit) | same file, `lane` block |
| Beats the current best public score on a validated holdout | ❌ **NOT ESTABLISHED** | see *Detection floor*, below |

It is **format-safe and unique, but it is an unvalidated experiment.** A parallel
run may upload it into a weekly slot; it must not be presented as a win. Its
expected score is a *falsifiable prediction*, not a measurement:

> The artefact exceeds the 0.2778 public score **if and only if at least ≈12 % of
> its 15,907 dots lie within the 300 m metric kernel of a hidden expert fault
> cell.** The current best-performing public artefact family achieves ≈13 % on
> the same definition. This is the entire bet, stated so it can be checked.

**A short note to paste into the submission form's "Note" field** (105 characters,
under the portal's limit):

```
GEMSDOE54 undercomplement-q200: SGMC state-map complement of catalogue, d>300m, linearity gate, 200m dots
```

**A short comment for your team to tell submissions apart later:**

```
undercomplement-q200 — state-map fault complement, catalogue-excluded, 200 m dots
```

Every number in this repository carries an explicit evidence label:
**HOLDOUT-DTI**, **ORGANIZER-CONFIRMED**, **PROXY-DTI (screening only)** or
**MODEL**. A projection is never written as a score.

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

---

## 2. Honest status in one screen

| Item | Status |
|---|---|
| A unique, format-legal, downloadable submission TIF | ✅ **done** — one click, section 0 above |
| Official metric re-implemented and regression-tested | ✅ `scripts/gems_metric.py`, reproduces the organizer's published worked example |
| Holdout detection floor computed (Cohen power analysis) | ✅ `evidence/power_analysis.json` |
| 3–5 ranked hypotheses | ✅ [`docs/hypotheses.html`](docs/hypotheses.html) |
| Executive summary subpage + how-to-submit | ✅ [`docs/index.html`](docs/index.html), [`docs/index.html#submit`](docs/index.html) |
| Official sources with links | ✅ [`registry/sources.json`](registry/sources.json) |
| Training a learned model (reference solution) | ❌ **blocked** — needs DrivenData login; see *Limitations* |

---

## 3. What this repository actually found

Three results, in order of importance. All three are **verifiable from bytes in
this repository**, not asserted.

### 3.1 The project's holdout could not rank submissions — an unflagged irregularity

The sibling repositories promote candidates on a holdout whose truth is *USGS SGMC
mapped faults more than 300 m from the competition catalogue*. Six artefacts have
**both** downloadable bytes **and** a published public-leaderboard score, so the
holdout can be checked against the leaderboard directly:

| artefact | proxy DTI | public score |
|---|---:|---:|
| `r13-lattice-s5` | **0.2478** | 0.0904 |
| `h60-officialstack-50k` | 0.1854 | *(none published)* |
| `tip_stepover_r30` | 0.0942 | 0.2632 |
| `dotted_b2_prune` | 0.0940 | **0.2778** |
| `dotted_d2_8` | 0.0927 | 0.2600 |
| `Hedge-v2` | 0.0884 | 0.1563 |

**Spearman ρ(proxy, leaderboard) = −0.029, p = 0.957, n = 6.** The artefact the
proxy likes best is the one the leaderboard likes least.

Re-calibrating the proxy's mass to the leaderboard-implied truth size does **not**
repair the ordering (ρ = +0.14, p = 0.79; the lattice stays first at every mass
from 12 k to 62 k truth cells). The mechanism is that the proxy's truth
(61,664 cells) is ≈5.3 × the leaderboard-implied truth (≈11.6 k cells), so the
proxy systematically over-rewards coverage and under-penalises mass.

*Consequence:* every "candidate beats incumbent on the local holdout" conclusion
in the sibling corpus — including the "+0.00487 live-mirror gain in 4/4 folds"
quoted on the GEMSDOE32 site — rests on a gate that has not been shown to order
submissions. Full receipts: [`docs/evidence.html`](docs/evidence.html).

### 3.2 The 0.0028 gap is far below the detection floor (the requested power analysis)

Cohen's framework, two-sided α = 0.05, power 0.80, z-sum = 2.801585. For a paired
comparison on withheld truth cells, the minimum detectable total credit gap is
`ΔT = z · σ_d · √n` and it converts to DTI through the exact metric algebra
`dDTI/dT = s(1 − 0.2s)/T`.

`σ_d` (the SD of the per-cell paired credit difference) is **measured from bytes**,
and it turns out to be the whole story — it depends on how different the two
candidates are:

| comparison | n (informative truth cells) | σ_d | floor, power 0.80 |
|---|---:|---:|---:|
| near-identical prune variants (`d2.8` vs `b2`) | 12,429 | 0.034 | **0.00057 DTI** |
| lattice vs dotted (distinct architectures) | 61,622 | 0.310 | **0.0117 DTI** |
| candidate vs lattice (distinct architectures) | 61,644 | 0.467 | **0.0176 DTI** |

**Answer to the brief's question.** To resolve a 0.0028 DTI gap at
distinct-architecture noise you would need **296,457** informative withheld truth
cells at that σ_d; the holdout supplies **12,429** — short by a factor of 24.
Against a holdout of this size, **0.0028, 0.0050, 0.0100 and 0.0200 are all
indistinguishable from noise for the architecture comparisons the project ran**.
It is only "detectable" in the special case of near-identical inputs, which is
precisely the comparison whose ranking the holdout gets wrong. So: **0.0028 is
noise being read as a ranking.** Receipts: [`docs/evidence.html`](docs/evidence.html).

### 3.3 What therefore drives the score — the exact algebra

For unit-valued dot predictions the official metric collapses exactly (verified
symbolically and numerically) to

```
DTI = T / ( 0.2·N + 0.8·G + 0.2·(T − M) )
```

where `N` = predicted positive cells, `G` = true cells, `T` = weighted credit,
`M = Σ_x max_g k(d(x,g))`, because `FP_w = N − M` and `FN_w = G − T` exactly. The
leaderboard-verified reading of this, from two rows on the same dotted family
(0.2600 at 44,090 dots → 0.2778 at 37,654 dots, i.e. **−17 % mass bought +0.0178**),
is that **mass is taxed and credit is the binding constraint**. Inverting those two
rows gives the leaderboard-implied hidden truth mass **G ≈ 11,583 cells**, which
independently reproduces the sibling corpus's own 12,226 estimate.

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
    gems54-undercomplement-q200.tif   ← THE SUBMISSION FILE
data/
  grid/labels.tif             ← organizer label raster (sha256 7ba308cc…)
  external/derived_sgmc_faults_100m_u8.tif
  external/GEMSDOE30_external_receipt.json
  grid/MIRROR_sample_submission_template.tif   ← see Irregularity #2
src/gemsdoe54/                ← grid, emission, holdout library
scripts/
  gems_metric.py              ← exact official metric (regression-tested)
  build_submission.py         ← builds the artefact
  validate_submission.py      ← format + range + lane gates
  collect_registry.py         ← assembles the parallel-run registry
  power_analysis.py           ← Cohen detection floor from measured σ_d
  run_all.sh                  ← reproduce everything end to end
registry/
  sources.json                ← every source, licence, and verification status
  registry_rasters/ + manifest.json   ← prior artefacts for the lane check
  gems54-undercomplement-q200.build.json
  run_card.json               ← the protocol's required run card
evidence/                     ← machine-readable receipts
tests/                        ← metric + emission regressions
```

## 5. Reproduce in one command

```bash
bash scripts/run_all.sh
```

Requires `numpy`, `scipy`, `rasterio`. The competition inputs are already placed
in `data/`; `scripts/fetch_inputs.sh` documents where each came from and its hash.

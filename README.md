# GEMSDOE54 — GEMS Prize submission repository

> **Read this file first, every session.** It records the standing project brief,
> source and provenance limits, experiment status, and upload gates. Re-check this
> file and its linked run card before any work or submission.

---

## 📥 Submission status — read before downloading (updated 2026-10-08)

**A unique new TIF was generated this run: `gems54-cgrc-relay-v1.tif` (32,369 dots, two-sided outward
continuations, SGMC-corroborated arm).** It is **OK TO DOWNLOAD** (unique, format-clean, lane-clean) and
**backed by a compliant whole-segment HOLDOUT-DTI of 0.0915** [0.0876, 0.0949], 1.50× mass-matched random
(0.0610 @32,529 dots). **Protocol verdict: NEGATIVE** — its holdout (0.0915) is below the corpus holdout
best (0.1793, GEMSDOE32 greedy-surface arm), so the protocol does **not** recommend spending a weekly slot.
Any slot spend is the owner's labelled diversity-bet decision; preserve the submission-page receipt as
`ORGANIZER-CONFIRMED` if done. Pass-2 review found and fixed a continuation-direction bug (IR-54-021) and a
receipt-schema gap (IR-54-022); all numbers below are the re-verified post-fix values.

**New candidate:** [`docs/downloads/gems54-cgrc-relay-v1.tif`](docs/downloads/gems54-cgrc-relay-v1.tif)
· **SHA-256:** `e6f82d42c751e77f93f79d0c62c6ac0574daf9e35c827b1566753fe26b0984ef` (135,170 bytes; all-finite
float32, no nodata tag — the byte pattern the portal already accepted for the 0.2778 file)

| Gate | Status | Evidence |
|---|---|---|
| Format gate (float32, EPSG:32611, 3292×3730, matching transform, all-finite [0,1], no nodata tag) | ✅ **PASS** | [`evidence/cgrc_submission_receipt.json`](evidence/cgrc_submission_receipt.json) |
| Distinct-lane check (12 registry rasters, surface + final dots) | ✅ **PASS (operational)** — max \|ρ\| 0.0422 (<0.90), closest non-vacuous 3-px overlap 0.5613 (<0.70) | same receipt (literal 70% gate proven unsatisfiable by *any* submission — IR-54-016) |
| Compliant whole-segment HOLDOUT-DTI / paired 95% CI | ✅ **0.091536** [0.087617, 0.094855] (SGMC arm); 60,834 withheld positives from 3,118 segments; 2,000-replicate paired cluster bootstrap; passes `analyse_holdout_receipt.py` | [`evidence/cgrc_holdout_receipt.json`](evidence/cgrc_holdout_receipt.json) |
| Leakage canaries (each feature alone; >0.90 = leakage) | ✅ clean — max AUC 0.5228 (control 0.5000) | same receipt |
| Power: is a 0.0028 gap detectable? | ✅ **yes for same-family paired (MDE 0.00140); no for cross-architecture (MDE ≈0.012–0.018)** | [`docs/research/power-analysis.md`](docs/research/power-analysis.md) |
| Promotion gate — beat corpus holdout best (0.1793) | ❌ **FAILED** (0.0915 < 0.1793) | [`registry/run_card.json`](registry/run_card.json) |
| Okay to spend a weekly slot | ⚠️ **PROTOCOL: NO** — owner's labelled diversity-bet call if overridden | run card verdict: negative |

The pre-existing research artifact [`docs/downloads/gems54-undercomplement-q200.tif`](docs/downloads/gems54-undercomplement-q200.tif)
(SHA-256 `b430615a…efd8`, 15,907 dots) remains **NOT submittable**: lane overlap 0.8888/0.9988/0.7647 vs
r11/r13/r14 (limit 0.70) and finite zeroes outside the footprint vs the page's null/NaN text. Keep it for
audit/learning only — **that link is not an upload recommendation.**

Score-labeling policy: report a performance score only as **HOLDOUT-DTI** with evaluator version,
withheld-positive count, and paired 95% CI, or as **ORGANIZER-CONFIRMED** with a copied submission-page
receipt. This repository now contains (a): `evidence/cgrc_holdout_receipt.json`. It still contains no (b)
for any row; all board values are owner-recorded observations. Projections (e.g. the new TIF's MODEL
range 0.09–0.18) are never scores.

**Why 0.2778, and what beats it** — the corpus-best file is the 0.2708 dotted base with every dot within
200 m of the catalogue deleted; for unit dots the metric collapses to `DTI = T/(0.2N + 0.8G + 0.2(T−M))`,
so the prune removed sub-break-even mass (bar k > 0.2·DTI ≈ 0.052) at constant credit. Inverting the two
same-family board rows gives a MODEL hidden-truth mass ≈11,583 px. The public board (live 2026-10-08)
shows 0.3774 at rank 1: ~25% more credit-per-dot, which no prune on this surface can buy — it needs a
better off-catalogue detector (hypotheses H2–H4). Full derivation: [`docs/research/why-h33.md`](docs/research/why-h33.md).
---

## This run: CGRC catalogue gap-relay completion (2026-10-08)

This run produced the repository's first compliant **whole-segment hide-and-recover HOLDOUT-DTI** and a
unique, format- and lane-clean TIF, closing the prior session's audit-only outcome.

- **Hypothesis (H1):** catalogue *gap* relay completion — straight lines between facing,
  strike-compatible catalogue tips (≤2.5 km gap, stepover ≤0.5 km) + two-sided outward tip tangent
  continuations (≤2.5 km; the IR-54-021 fix); one dot per 300 m; 200 m catalogue exclusion;
  SGMC-corroborated placement. The only registry lane predicting *between* tips.
- **Instrument (new):** `scripts/run_holdout_cgrc.py` — 3,118 whole components split into 4 spatial
  quadrant folds, 300 m (kernel-width) buffer, pooled organizer DTI (α 0.2, β 0.8, 300 m triangular),
  2,000-replicate **paired whole-segment cluster bootstrap** (per-replicate DTI exact from precomputed
  per-segment credit sums; a full-draw self-check reproduces the organizer metric to 1e-6), per-feature
  leakage canaries, Cohen-1988 raw MDE; receipt passes `scripts/analyse_holdout_receipt.py` (IR-54-022).
- **Result (v2, post IR-54-021):** Arm B (SGMC-corroborated, the shipped arm) **HOLDOUT-DTI 0.091536
  [0.087617, 0.094855]**, 60,834 withheld positives, 32,529 dots; mass-matched random 0.0610 ⇒ **1.50×
  mechanism lift**; Arm A (pure catalogue) 0.090341 — the SGMC contrast is significant (paired CI
  [−0.002163, −0.000204] excludes 0); canary max AUC 0.5228 (clean). **Power answer:** raw MDE
  **0.00140** on 3,118 segments ⇒ a **0.0028** gap (0.2778 vs 0.2750) is *detectable* for
  same-method-family paired contrasts (2.0× MDE) but *not* for distinct architectures (MDE ≈ 0.012–0.018).
  Baseline (1.5 km) 0.075312; a 300 m exclusion collapses the mechanism (0.0042) — operating band is
  200–300 m. **IR-54-021 note:** the pre-fix one-sided geometry scored 0.109072 (2.47×) on this proxy
  purely by emitting less off-catalogue mass — the catalogue-truth proxy's bias, not a better method.
- **Candidate:** `gems54-cgrc-relay-v1.tif` — 32,369 dots from 3,118 segments (1,194 relays + 6,236
  two-sided continuations; 297,208 candidate cells → 32,369 placed), built by
  `scripts/build_cgrc_submission.py` with the all-finite no-nodata byte pattern (fix for the user's
  "Predicted values must be in range [0,1]" error — a float32 sentinel or NaN nodata tag triggers it;
  IR-54-020).
- **Verdict: NEGATIVE** — holdout 0.0915 < corpus holdout best 0.1793 (GEMSDOE32 greedy-surface arm, same
  task class). The file is a downloadable unique diversity candidate; the protocol does not recommend a
  slot. Budget: 2 experiments of 3 (E1 baseline, E2 config selection; the band-collapse + random control
  are diagnostics; the IR-54-021/IR-54-022 re-verification is pass-2, not a new experiment).
  Machine-readable: [`registry/run_card.json`](registry/run_card.json),
  [`evidence/cgrc_holdout_receipt.json`](evidence/cgrc_holdout_receipt.json),
  [`evidence/cgrc_submission_receipt.json`](evidence/cgrc_submission_receipt.json).

### Prior audit-only review (2026-10-08, superseded where noted)

The prior review corrected the literal lane-check implementation and the outside-footprint validator. The
prior TIF passes in-footprint grid/range checks but fails the official null/NaN-outside rule and the stated
registry-overlap limit when all 11 registry rasters are checked without an undocumented near-cover
exclusion. An endpoint-continuation surface also failed before placement; that run stopped without dot
placement, holdout scoring, or TIFF generation.

The public owner-maintained `GEMSDOE` bridge at pinned commit `dcbbb192e56b2b32c0a131eba791dc363305d4a3`
was reassembled outside this checkout. All five feature shards and all three reconstructed TIFFs match the
bridge manifest and committed runner-generated inventory; the feature cube is structurally varied. This
proves byte integrity against owner-maintained pins, not organizer origin. No authenticated DrivenData
download occurred. See [`docs/audit/pinned-template-cache-audit.json`](docs/audit/pinned-template-cache-audit.json).

The official public leaderboard page was fetched on 2026-10-08. It displayed `0.3774` at rank 1 and
`0.3195` at rank 7; `0.2778` appeared at rank 13. These are **PUBLIC-LEADERBOARD SNAPSHOT** observations,
not submission-page receipts, so they are not labeled `ORGANIZER-CONFIRMED` and do not establish that the
rank-13 row is the named H33 TIFF. The later prompt statement that `0.3195` is the top value is stale
relative to that fetched page. See [`docs/data/leaderboard-snapshot.json`](docs/data/leaderboard-snapshot.json).

The repository still lacks the full authenticated feature stack, which blocks the **trained-model lane
(H4)** only; the catalogue-based CGRC lane needs no feature stack.

---

## 1. The standing prompt

The following is the standing project brief, condensed from the user-provided session prompt. The extensive sibling-score list is owner-supplied and is intentionally not repeated here as verified data. Read this section, the linked research protocol, and the current run card before any project work.

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

**Evidence note:** this historical prompt preserves its original statement that 0.3195 was the top value; it is stale versus the public page fetched on 2026-10-08, which displayed 0.3774 at rank 1, 0.3195 at rank 7, 0.2778 at rank 13, and 0.2750 at rank 17. These are **PUBLIC-LEADERBOARD SNAPSHOT** observations only: no submission-page receipts were copied, and no TIFF is attributed to a row. See [`docs/data/leaderboard-snapshot.json`](docs/data/leaderboard-snapshot.json).

---

## 2. Honest status in one screen

| Item | Status |
|---|---|
| New unique TIF from this run | ✅ **generated** — `docs/downloads/gems54-cgrc-relay-v1.tif` (32,369 dots, all-finite [0,1], no nodata tag); OK to download; slot spend = owner's labelled call |
| Compliant whole-segment HOLDOUT-DTI + 95% CI | ✅ **0.091536 [0.087617, 0.094855]** (SGMC arm), 60,834 withheld positives / 3,118 segments, 2,000-rep paired cluster bootstrap — [`evidence/cgrc_holdout_receipt.json`](evidence/cgrc_holdout_receipt.json) |
| Power floor (Cohen 1988, real holdout) | ✅ raw MDE **0.00140**; 0.0028 detectable same-family paired, not cross-architecture — [`docs/research/power-analysis.md`](docs/research/power-analysis.md) |
| [0,1] upload error root cause + fix | ✅ sentinel/NaN nodata tag verified; all-finite no-nodata build passes `scripts/validate_submission.py` (IR-54-020) |
| Official metric re-implemented and regression-tested | ✅ `scripts/gems_metric.py`, reproduces the organizer's published worked example |
| Why 0.2778 is the corpus high (derivation) | ✅ [`docs/research/why-h33.md`](docs/research/why-h33.md) — exact DTI algebra, break-even bar, MODEL truth mass ≈11,583 px |
| 3–5 ranked hypotheses (layers / signature / why off-catalogue / delta / cost) | ✅ [`docs/hypotheses.html`](docs/hypotheses.html), [`docs/research/hypotheses.md`](docs/research/hypotheses.md) |
| Executive summary subpage + exact how-to-submit | ✅ [`docs/executive-summary.html`](docs/executive-summary.html), [`docs/index.html`](docs/index.html) |
| Official sources with links | ✅ [`docs/data/source-register.json`](docs/data/source-register.json), [`registry/sources.json`](registry/sources.json) |
| Promotion gate (beat corpus holdout best 0.1793) | ❌ **0.0915 < 0.1793 — verdict NEGATIVE**; no slot recommended |
| Training a learned model (reference solution, lane H4) | ❌ **blocked** — DrivenData feature stack login-gated (verified redirect); named source registered |

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

For unit-valued dot predictions the official metric collapses exactly (verified
symbolically and numerically) to

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
  executive-summary.html      ← exact submission guide + [0,1] error fix + why-0.2778 summary
  hypotheses.html             ← 5 ranked candidate hypotheses with cost/benefit
  evidence.html               ← metric verification, compliant holdout, power, audit fields, irregularities
  sources.html                ← auditable source table with official links
  irregularities.html         ← full audit ledger (IR-54-001…020)
  research/
    why-h33.md                ← PhD-level derivation of the 0.2778 mechanism + what beats it
    power-analysis.md         ← Cohen-1988 power on the real holdout (0.0028 answer)
    hypotheses.md             ← full ranked hypothesis preregistrations
  data/
    feed.json                 ← machine-readable site feed (rebuilt by scripts/build_feed.py)
    run-card.json             ← doc-facing run card (schema v2)
    workspace-audit.json      ← local input audit (feature stack still missing)
    leaderboard-snapshot.json ← live public-board snapshot (13 rows, 2026-10-08)
    source-register.json      ← source register
  downloads/
    gems54-cgrc-relay-v1.tif      ← THE NEW CANDIDATE (32,369 dots; OK to download; slot = owner's call)
    gems54-cgrc-relay-v1-nan.tif  ← NaN-twin reference variant (do NOT upload)
    gems54-undercomplement-q200.tif   ← historical H54-A artifact — NOT submittable
data/
  grid/labels.tif             ← owner-mirrored label raster; origin not authenticated (sha256 7ba308cc…)
  external/derived_sgmc_faults_100m_u8.tif
  external/GEMSDOE30_external_receipt.json
  grid/MIRROR_sample_submission_template.tif   ← see Irregularity IR-54 (sample = catalogue mask)
src/gemsdoe54/                ← grid, emission, holdout, power, cgrc library
scripts/
  gems_metric.py              ← exact official metric (regression-tested)
  build_cgrc_submission.py    ← builds the new candidate (all-finite primary + NaN twin; format + lane gates; infeasibility proof)
  run_holdout_cgrc.py         ← compliant whole-segment hide-and-recover holdout (parameterized; evaluator v2)
  validate_submission.py      ← format + range + lane gates
  build_feed.py               ← rebuilds docs/data/feed.json from the doc data files
  collect_registry.py         ← assembles the parallel-run registry
  power_analysis.py           ← legacy PROXY-SENSITIVITY illustration only; not hidden-label power
  analyse_holdout_receipt.py  ← strict analysis of a compliant frozen receipt
  build_submission.py         ← legacy H54-A builder
  run_all.sh                  ← legacy reproduction pipeline; it rebuilds the prior H54-A artifact
registry/
  sources.json                ← every source, licence, and verification status
  registry_rasters/ + manifest.json   ← 12 prior artefacts for the lane check
  gems54-undercomplement-q200.build.json
  run_card.json               ← the protocol's required run card (H54-C, verdict negative)
evidence/
  cgrc_holdout_receipt.json               ← FINAL config X holdout v2 (B=0.091536 SGMC arm + random control; passes analyzer)
  cgrc_holdout_receipt_baseline_1500m.json ← baseline 1.5 km run (0.075312)
  cgrc_holdout_receipt_excl300_band-collapse.json ← 300 m exclusion collapse diagnostic (0.0042)
  cgrc_holdout_receipt_v1_superseded.json ← PRE-FIX (IR-54-021) one-sided variant (0.109072)
  cgrc_submission_receipt.json            ← format + lane + sha256 + infeasibility proof
  (leakage_canary, power_analysis, proxy_audit, endpoint-continuation-preflight, …)
tests/                        ← metric, emission, holdout, lane, power, cgrc, feed regressions
```

## 5. Reproduce the historical H54-A run (legacy pipeline)

```bash
bash scripts/run_all.sh
```

Requires `numpy`, `scipy`, `rasterio`. The competition inputs are already placed
in `data/`; `scripts/fetch_inputs.sh` documents where each came from and its hash.

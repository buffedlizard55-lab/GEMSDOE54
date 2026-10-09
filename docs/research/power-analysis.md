> **2026-10-09 update.** Answer to the 0.0028 question (2026-10-09). Holdout raw-scale MDE for the paired CGRC contrast is 0.001395 (bootstrap SE 0.000498; 3,118 whole-segment units; Cohen framework, alpha 0.05, power 0.80, z_sum 2.801585). The 0.0028 gap is about twice that floor, so it would be detectable on the holdout. It is NOT CLASSIFIABLE on the board: no paired board data and no published test-set size. Sections below using the earlier 1500 m or v1 numbers are superseded. Source: evidence/cgrc_holdout_receipt.json (power block).

# Holdout power: required before ranking any method

## Decision

**No valid power estimate or HOLDOUT-DTI result was produced in the earlier audit pass or in the 2026-10-08 review.** The checkout contains owner-mirrored labels and an SGMC layer plus a prior H54-A candidate, but not the full training feature stack or an authenticated DrivenData download. An earlier separate read-only audit reported that the owner-maintained `GEMSDOE` bridge shards and reconstructed TIFFs matched owner pins and contained nonconstant feature bands; this verifies integrity against owner-maintained pins, not organizer origin. The pinned template's workflow assigns spatial blocks, not whole fault segments. The local `segment_blocks` helper provides buffered groups but is not a full trainer/evaluator. The separate `GEMSDOE52` cache remains quarantined per its prior failed integrity audit. Consequently, no compliant withheld-positive count, paired variance, detection floor, or confidence interval for the cited leaderboard-gap example is available.

**DATA-AUDIT (not HOLDOUT-DTI):** the hash-matched owner-mirror label raster contains 60,988 positive pixels in total. This is not a withheld-positive count, not an independent sample size, and not a score. The value is recorded only as a property of the cached input in [`pinned-template-cache-audit.json`](../audit/pinned-template-cache-audit.json).

The score pair in the prompt is not a `HOLDOUT-DTI` receipt and is not an `ORGANIZER-CONFIRMED` submission-page receipt. It remains an unverified claim and is excluded from the ranking decision. A difference of two reported leaderboard values is not an estimate of holdout uncertainty.

## Why positive-pixel count alone is insufficient

Cohen's framework distinguishes a standardized effect from its standard error. For a paired comparison, the classical effect is

\[
 d_z = \frac{\mathbb{E}(D)}{\operatorname{SD}(D)},
\]

where \(D\) is the paired difference. The exact two-sided minimum detectable standardized effect at target power is obtained by solving the noncentral-*t* power equation, which `gemsdoe54.power.minimum_detectable_cohen_d` implements.

Raster positives are not independent experimental units. Pixels on one mapped fault segment are spatially correlated; nearby target pixels also share overlapping neighborhoods under the triangular kernel. Pooled DTI is a nonlinear ratio whose numerator and penalties are coupled. Treating every positive pixel as an independent replicate therefore produces an optimistic, generally invalid power floor. The number of withheld positive pixels must still be recorded, but the effective replication must be based on whole withheld fault segments defined before scoring; generic spatial blocks are not a substitute for this project's required holdout unit.

Even an independent-unit count does not turn Cohen's standardized effect into a raw DTI increment. A raw-scale floor requires a variance estimate. For pooled DTI, the primary uncertainty estimate should come from paired cluster-bootstrap replicates that re-sample whole withheld fault segments and recompute the *pooled* metric for both candidate and baseline on every replicate.

## Required estimand and protocol

The holdout receipt must identify:

- evaluator version and a hash of the evaluator code;
- whole fault segments withheld with a spatial buffer, with their positive-pixel count;
- catalogue-derived features recomputed from visible faults only;
- exact pixel-level masking of visible faults;
- pooled DTI with alpha 0.2, beta 0.8, and a 300 m triangular kernel;
- the same folds and masks for candidate and baseline;
- a paired whole-segment cluster-bootstrap distribution of pooled DTI differences;
- leakage-canary results for each feature by itself, with any AUC above 0.90 treated as leakage until explained.

Do not tune the holdout or candidate after looking at the same fold results. Any adjustment requires a newly frozen registration and fresh folds.

## What the analysis reports once a valid receipt exists

`python scripts/analyse_holdout_receipt.py path/to/frozen-holdout-receipt.json` rejects receipts missing the evaluator version, scoring contract, withheld-positive count, independent-unit count, pixel-exact visible mask, visible-only catalogue features, or at least 1,000 finite cluster-bootstrap replicates. (The repository's existing `scripts/power_analysis.py` is a separate exploratory proxy-sensitivity report and is not a compliant holdout receipt.) It then reports:

1. `HOLDOUT-DTI` — evaluator version, number of withheld positives, observed pooled difference, and the paired cluster-bootstrap 95% CI;
2. Cohen's minimum detectable standardized effect for the independent whole-segment count;
3. an approximate raw-scale detectable pooled-DTI difference based on the paired cluster-bootstrap standard error;
4. a separate pixel-IID Cohen floor, explicitly marked **not valid for inference** and never used to promote a candidate.

The 95% interval, not the power calculation alone, decides whether the measured local difference is distinguishable from zero. A holdout win is not an organizer score and is not proof that the hidden test set shares the same distribution.

## Current machine-readable run state

See [`../data/run-card.json`](../data/run-card.json) and [`../data/workspace-audit.json`](../data/workspace-audit.json). Both deliberately record the holdout and raster fields as unavailable; no score or projection is substituted.

## 2026-10-08 run update

The current run still has no compliant `HOLDOUT-DTI`: evaluator version, withheld-positive count, independent whole-segment count, paired bootstrap distribution, 95% CI, and raw-scale detection floor are all unavailable. Therefore the user-reported difference 0.0028 between 0.2778 and 0.2750 remains **NOT CLASSIFIABLE** as signal or noise. The earlier values in `evidence/power_analysis.json` remain **PROXY-SENSITIVITY / MODEL** diagnostics against the circular SGMC-derived target; they must not be substituted for the missing holdout power calculation.

The two recorded experiments were registry-lane surface screens, not DTI evaluations. Their overlap figures are screening diagnostics only. The exact stop reason is in [`../data/run-card.json`](../data/run-card.json); no weekly slot or performance claim follows from them.

## References

- Cohen, J. (1988), *Statistical Power Analysis for the Behavioral Sciences*, 2nd edition. The request identifies this as the intended framework; the book itself was not available in the checkout.
- The user-supplied competition metric page: <https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/> (not fetched in this environment).
- The accessible official reference-solution repository: <https://github.com/drivendataorg/gems-prize-reference-solution>.

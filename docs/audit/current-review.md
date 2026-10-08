# Repository review and experiment outcome — 2026-10-08

**Checkout:** `arena/0c810456-gemsdoe54`, starting at `4bd30d98503b970c520dace9e34f9d8829e88916` (`main`). Work remained on the assigned branch.

## Executive decision

**Negative. No new submission TIFF was emitted, and no weekly slot was touched.** Two pre-placement surface screens stopped before point placement because their candidate supports exceeded the literal 70% overlap gate against three registry rasters. Separately, a valid whole-fault-segment hide-and-recover result cannot be produced from the checked-out files: the official feature cube and a valid blank sample raster are absent, and the available public owner-template evaluator is spatial-block based rather than the required whole-segment evaluator.

The older `docs/downloads/gems54-undercomplement-q200.tif` remains in the repository for audit history. It passes local single-band, float32, grid, in-footprint finite-value, and [0, 1] checks, but fails the current conservative null/NaN-outside-footprint contract because it stores finite zeroes outside the cached footprint. It is also flagged as a duplicate by raw 3-pixel overlap with `r11_greedy_mp`, `r13_lattice_s5_00904`, and `r14_union_tips10_lat6`. The official format page was not fetched in this review; the outside-NaN check follows prior repository notes and the mirrored template. The archive has no compliant HOLDOUT-DTI and is **not recommended for upload**.

## Repository inventory and data/protocol blockers

The local checkout contains `data/grid/labels.tif`, `data/external/derived_sgmc_faults_100m_u8.tif`, and a file named `MIRROR_sample_submission_template.tif`. This review confirmed that it has the same 60,988 positive cells and 0/1 values as the labels on the local footprint, while storing NaN outside the footprint where the label raster uses nodata −1; the files are not byte-identical and this does not authenticate organizer origin. The checkout does not contain `training_features.tif` / `numeric_features.tif`, an authenticated blank `sample_submission.tif`, `evaluate_holdout.py`, or `submission_writer.py`.

I checked the public owner-maintained `buffedlizard55-lab/GEMSDOE` repository at its pinned `main` commit, `dcbbb192e56b2b32c0a131eba791dc363305d4a3`, using GitHub's API. The tree exposes `data/bridge/` shards, a bridge manifest, `scripts/block_holdout_eval.py`, and `src/submission_io.py`; it does not expose the protocol's named evaluator/writer files. The manifest describes owner-pinned Dropbox mirrors, not an organizer-authenticated download. The evaluator configuration describes spatial blocks, not whole-fault-segment hide-and-recover. These remote bytes were not imported into this checkout, and no private evaluator fork was built.

The official DrivenData data tab and user-supplied USGS / DOE / NLR pages were not fetched in this run. No DrivenData authentication was available. The public official reference-solution GitHub repository was checked at commit `aebe92f7c8a990f0e3443451b7a825d9afd6336b` for its README only; it is a baseline repository, not a holdout evaluator or score receipt.

## Experiment 1: endpoint-continuation surface preflight (carried from merged PR #7)

The repository already contains a 2026-10-08 in-memory endpoint-continuation surface receipt from PR #7; this review did not rerun it. It projects local catalogue-trace endpoints up to 1.5 km along their tangents, outside a 300 m visible-catalogue buffer. The surface had 32,491 positive cells. Its receipt is [`../../evidence/endpoint-continuation-preflight.json`](../../evidence/endpoint-continuation-preflight.json).

- Maximum absolute Spearman correlation: 0.0585.
- Raw fraction of surface-support cells within 3 px of `r11_greedy_mp`, `r13_lattice_s5_00904`, and `r14_union_tips10_lat6`: 0.7479, 0.9992, and 0.8853. Each exceeds the literal 0.70 threshold.
- Result: **DUPLICATE — STOP before placement.** No holdout, final dots, or TIFF.

## Experiment 2: SGMC topology surface preflight

A second surface was constructed **in memory only**: local SGMC pixels farther than 300 m from the local catalogue were scored by an 8-neighbour angular-transition count and a 5×5 local line-density term. It produced 57,758 positive support cells. The receipt is [`../../evidence/strict_lane_preflight.json`](../../evidence/strict_lane_preflight.json).

- Pre-placement maximum absolute Spearman correlation: 0.010694, below the 0.90 threshold.
- Raw fraction of surface-support cells within 3 px of existing registry dots: `r11_greedy_mp` 0.901537, `r13_lattice_s5_00904` 0.999740, `r14_union_tips10_lat6` 0.765833. Each exceeds the literal 0.70 threshold.
- Result: **DUPLICATE — STOP before point placement.** No final dot set, final-raster lane comparison, raster hash, or submission note exists for this run.
- Both screens are lane diagnostics, not DTI scores. The three registries cover much of the footprint, making raw overlap non-discriminating; the protocol nevertheless gives no exception, so both screens stopped rather than silently overriding its gate.

**Process deviation, disclosed:** an earlier non-persisted scratch calculation formed a hypothetical top-200 point preview after Experiment 2's surface already exceeded the literal threshold. It was not written to disk, not used as a candidate or score, and no TIF was created from it. This was out of order relative to the stop rule. The formal repeatable SGMC script now checks the surface and stops before placement; do not treat the scratch preview as a valid experiment result. Total accounting is **two surface-only screens, zero holdout runs, zero TIFFs, zero slots**.

## Code-review fixes

1. `scripts/validate_submission.py` previously used one-sided Spearman (`rho > 0.90`) and exempted near-covering registry rasters from the overlap verdict. It now uses **absolute** rank correlation and applies the stated raw 70% overlap threshold to all registry rasters, while retaining a diagnostic field that identifies degenerate near-covering comparisons. It also reports undefined correlations as JSON `null`, avoiding non-standard `NaN` values.
2. `src/gemsdoe54/holdout.py::informative_truth_cells` previously counted truths exactly 300 m from predictions even though the triangular kernel credit is zero at the radius. It now counts strictly positive-credit cells (`distance < 300 m`) and validates mask shapes.
3. `src/gemsdoe54/grid.py::write_submission` previously allowed a caller-specified non-float32 dtype despite the submission format; it now fails closed unless the dtype is float32.
4. The legacy submission builder now defaults to ignored `work/` rather than the public downloads directory, and the old `run_all.sh` has been retired as a side-effect-free failure stub.
5. Added tests cover anti-correlation, dense-registry overlap, undefined Spearman, missing-registry indeterminacy, surface construction, the zero-credit kernel boundary, writer dtype, and the retired-pipeline guard. The full test suite passed locally (56 tests).

## Power / score conclusion

No `HOLDOUT-DTI` was produced, so the evaluator version, withheld-positive count, paired 95% CI, and raw DTI detection floor remain null. The owner-mirror total label count and the earlier circular SGMC-proxy sensitivity figures are not substitutes. Therefore the user-reported 0.0028 gap between 0.2778 and 0.2750 remains **NOT CLASSIFIABLE** as signal or noise from this checkout. Those values are not copied submission-page receipts and are not labeled `ORGANIZER-CONFIRMED` here.

The five current geological hypotheses and exact availability caveats are in [`../research/hypotheses-20261008.md`](../research/hypotheses-20261008.md). The top-ranked cross-gradient idea is blocked by the missing/authentication-unverified feature stack. No claim is made that any candidate exceeds 0.2778, 0.3195, or any other user-supplied leaderboard value.

## Remaining work, ordered by gate

1. Obtain the official competition rasters through the authenticated DrivenData data tab; verify names, checksums, shape, CRS, transform, nodata, and license/terms before using them.
2. Reconcile the shared evaluator/writer filename mismatch with the template owner. A compliant runner must withhold whole fault segments plus a buffer, derive catalogue features from visible faults only, mask visible fault cells pixel-exactly, score pooled DTI with the specified kernel, and emit per-feature AUC canaries. Do not use the spatial-block workflow as a substitute for the stated segment holdout.
3. Resolve the lane-rule degeneracy in a shared protocol revision: three registry rasters cover most of the footprint, so the literal raw overlap threshold labels many unrelated candidates duplicates. Until the rule is formally revised, apply the literal rule and stop on a breach.
4. Re-run power and paired whole-segment bootstrap analysis only after a frozen compliant receipt exists; keep `0.0028` unclassified until then.
5. Generate, validate, hash, and link a new GeoTIFF only after the above gates pass. Keep promotion/slot selection separate and within the current cap shown on the submission page.
6. Refresh the organizer leaderboard from an authenticated or otherwise official source and record receipts; do not transform owner-site claims into confirmed scores.

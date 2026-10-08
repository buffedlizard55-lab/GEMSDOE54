# Forensic note: the H33 artifact and its reported score

## What the artifact record supports

The read-only owner-maintained GEMSDOE32 record for `h33-h33-2-b2` describes the raster as a base emission followed by deletion of predicted pixels within a small buffer around the known-fault catalogue. Its accompanying audit describes it as a post-processing variant, not as a newly trained geological detector. The repository's README and audit file are available at:

- <https://github.com/buffedlizard55-lab/GEMSDOE32/blob/0d6a6243147cd63a2000412d575d4c80a36d3a62/README.md>
- <https://github.com/buffedlizard55-lab/GEMSDOE32/blob/0d6a6243147cd63a2000412d575d4c80a36d3a62/docs/downloads/gemsdoe32-h33-h33-2-b2-20261004T220000Z-e5eb6e7e-audit.json>

These are owner-published technical records, not organizer receipts. On 2026-10-08 the official public leaderboard displayed 0.2778 at rank 13 and 0.3774 at rank 1. The owner's registry associates 0.2778 with `dotted_b2_prune`, but the public page snapshot contains no receipt tying that row to the exact H33 raster/hash. Treat 0.2778 as a PUBLIC-LEADERBOARD SNAPSHOT plus owner-side attribution, not ORGANIZER-CONFIRMED performance for these bytes. The rank-1 method/artifact is also unidentified by our evidence.

## Plausible metric mechanism — not a causal proof

The competition task, as described in the supplied prompt, uses a distance-weighted Tversky-type metric. Under such a metric, predictions receive partial credit near withheld target faults and uncredited emission contributes false-positive cost. A spatial deletion can improve a realized test score if it removes low-credit predictions while retaining predictions near the hidden target set. It can also hurt if the deleted pixels were useful continuations. Which outcome occurs depends on the hidden labels and exact mask, not on the visual appearance of the raster.

The owner-side comparison is consistent with a sparsity story: `dotted_d2_8` is listed with 44,090 dots and 0.2600, while `dotted_b2_prune` is listed with 37,654 dots and 0.2778 (6,436 fewer, about 14.6%). If the row/file mapping and score records are correct, deleting low-credit dots could have reduced false-positive mass while retaining enough predictions near hidden faults. This is only a plausible mechanism: the score pair is not backed here by submission-page receipts or a paired independent holdout, and the difference cannot be causally assigned to pruning.

Thus, the defensible explanation is **selection/placement efficiency may have improved**, not that the catalogue-buffer operation discovered a new fault-generating process. A favorable score could also reflect hidden-test sampling variation, multiple-candidate selection, label/catalogue construction effects, or an unverified score attribution. The owner record does not identify which of these caused the claimed leaderboard result. It cannot explain the current public rank-1 observation of 0.3774, whose method/artifact is not identified in this audit.

## What would establish the explanation

- The original submitted bytes and an organizer submission-page receipt matching the file hash;
- the exact competition metric/version and test-time mask semantics;
- a preregistered hide-and-recover experiment using whole fault segments with a buffer, visible-only catalogue-derived features, pixel-exact visible masking, and pooled DTI;
- paired cluster-bootstrap uncertainty for the change from the base raster;
- feature-only leakage canaries and an audit that the pruning radius was not selected on the scored hidden labels;
- decoded-raster correlation and dot-overlap tests against all accessible prior rasters.

None of these proof conditions is available in this checkout. The reported difference between two leaderboard entries is not a substitute for the paired holdout distribution. No claim is made that this repository can now beat the reported score; no prior raster was copied or edited into a new artifact.

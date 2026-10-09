> **2026-10-09 update.** Superseded in part by docs/top-artefact.html (2026-10-09). The 0.2778 value is not the board top (0.3774 is rank 1; 0.3195 rank 7; 0.2778 rank 13). The deletion count is 2,545 (40,199 to 37,654), not 6,436. The GEMSDOE32 link is unverified.

# Forensic note: H33 `b2` artifact and its reported value

## 2026-10-09 session answer (PhD-level synthesis)

**Why `h33-h33-2-b2-…-e5eb6e7e-zeros` reportedly scored 0.2778 — the exact
mechanism, now verified against the registry bytes.** The artefact is the
group's 0.2708 emission (40,199 dots, `registry/registry_rasters/dotted_d2_8_02708.tif`)
with every dot within 200 m of the published catalogue deleted (2,545 dots
removed; 37,654 remain, byte-identical to the owner's file). For unit-valued
dots the organizer metric collapses to

```text
DTI = T / ( 0.2·N + 0.8·G + 0.2·(T − M) )
```

so deleting a dot that earns **no** kernel credit lowers `N` (and `M`) while
leaving `T` unchanged: DTI rises mechanically. Deleting a dot that supplied
*unique* credit would lower `T` too and hurt. The b2 prune is therefore a
**precision edit**, not a discovery of new faults: it removes catalogue-adjacent
mass that the hidden truth (faults absent from the catalogue) cannot credit.
Inverting the two owner-reported rows of the same family (0.2600 at 44,090 dots
vs 0.2778 at 37,654 dots, prune leaves T and M unchanged) gives a MODEL pooled
credit T ≈ 5,230 and a MODEL hidden-truth mass G ≈ 12–14 k cells — i.e. the
leader still misses roughly 60 % of the hidden truth and pays the α = 0.2 mass
tax on tens of thousands of zero-credit dots. That is the headroom.

**Can we generate something that scores higher?** In principle yes — two
levers: (a) prune harder/smarter (the b2 rule is a coarse 200 m flank; the
metric's own break-even bar is `k > 0.2·DTI ≈ 0.06`, i.e. any dot averaging
more than ~282 m from hidden truth is losing money), and (b) move the remaining
dots toward high-credit positions (off-catalogue structures the expert set
covers). In practice **no local instrument can prove it**: the holdout recovers
withheld *catalogue* faults while the board scores faults *missing* from the
catalogue, and this repository measured the resulting anti-correlation
(Section 3.1: a widely-used proxy ranks owner-reported board values at
ρ = −0.03, p = 0.96). What this session can and does deliver is a
**format-valid, lane-unique** candidate in a lane no sibling occupies
(hydrothermal-manifestation corridors), validated against a matched chance
control on the whole-segment holdout (HOLDOUT-DTI 0.0186 vs 0.0062, paired CI
excluding zero, 2.8× the 80 %-power floor), with every number labelled.

**The 0.0028 gap (0.2778 vs 0.2750).** NOT CLASSIFIABLE. The smallest paired
MDE this repository can compute is 0.0015–0.0022 for near-identical ridge
variants and 0.0045–0.0095 for distinct architectures; the board's variance is
unmeasured and its truth set is different. Reading 0.0028 as a ranking is noise
being read as signal.

## Evidence boundary

The brief supplied for this session reports `h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros` at 0.2778 and compares it with an earlier family member reported at 0.2750. The repository's collected bytes include a `dotted_b2_prune` raster and a prior local build/run record. The cited values are **USER/OWNER-REPORTED observations**, not `ORGANIZER-CONFIRMED`: this review did not obtain a submission-page receipt tying an exact uploaded hash to either value. The prompt also gives inconsistent “current highest” values (including 0.3774 and 0.3195). None is treated as a current verified leaderboard fact.

The owner-maintained GEMSDOE32 README and audit receipt are linked for manual review:

- [GEMSDOE32 README at the cited commit](https://github.com/buffedlizard55-lab/GEMSDOE32/blob/0d6a6243147cd63a2000412d575d4c80a36d3a62/README.md)
- [H33 owner-side audit receipt](https://github.com/buffedlizard55-lab/GEMSDOE32/blob/0d6a6243147cd63a2000412d575d4c80a36d3a62/docs/downloads/gemsdoe32-h33-h33-2-b2-20261004T220000Z-e5eb6e7e-audit.json)

These are owner-published technical records, not organizer receipts. The user-supplied [DrivenData problem page](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/) is the appropriate official manual-review source; it was not fetched in this run.

## Plausible metric mechanism — exact algebra, not causal proof

The local metric implementation encodes the distance-weighted Tversky form described in the supplied competition materials. For unit-valued dot predictions, define:

- `N`: number of predicted positive cells;
- `G`: number of true positive cells;
- `T`: pooled weighted true-positive credit;
- `M`: sum of each predicted dot's maximum triangular-kernel credit to any truth cell.

Then `FP_w = N - M` and `FN_w = G - T`; substituting alpha 0.2 and beta 0.8 gives

```text
DTI = T / (0.2*N + 0.8*G + 0.2*(T - M))
```

This identity describes the metric's accounting, not the target geology. Removing a dot that earns no truth credit reduces `N` while leaving `T` unchanged, which can improve DTI mechanically. Removing a dot that supplied unique credit reduces `T` too and can make the score worse. Removing a redundant dot can help; removing a useful continuation can hurt. The result depends on the hidden expert labels and the full emission set.

The defensible *mechanistic hypothesis* for a catalogue-proximity prune is therefore: it may remove predictions with little or no credit on the hidden target while preserving useful predictions, reducing false-positive mass. That is not proof the prune found a new fault, nor proof that the prune caused the reported score. It could also reflect hidden-set sampling variation, candidate-selection effects, changes in count/spacing/thresholds, or a score/hash attribution mismatch.

## The 0.0028 comparison and the detection floor

The example difference `0.2778 - 0.2750 = 0.0028` is a user-reported leaderboard gap, not a paired holdout effect. A single difference between organizer scores cannot reveal its sampling uncertainty. Cohen's standardized effect requires independent experimental units and a variance estimate; fault pixels on one trace are spatially dependent, and pooled DTI is a nonlinear ratio.

The repository's old paired-credit sensitivities used an SGMC-derived proxy target that shares a source with the SGMC candidate. The prior reported proxy MDEs (including the near-identical-pair value 0.000573 and distinct-architecture value 0.017596) are **PROXY-SENSITIVITY / MODEL** diagnostics only. They are not a detection floor for the hidden expert labels. The current checkout has no compliant whole-segment holdout receipt, so its withheld-positive count, independent-unit count, paired bootstrap variance, paired 95% CI, and raw DTI detection floor are all **NOT AVAILABLE**. Therefore the 0.0028 gap remains **NOT CLASSIFIABLE** as signal or noise.

A compliant comparison must freeze whole fault segments plus a buffer, derive catalogue features from visible faults only, pixel-exactly mask visible faults, score pooled DTI under the specified kernel, run each feature alone as a leakage canary, and use a paired whole-segment cluster bootstrap. The public owner-template workflow inspected in this review uses spatial blocks and is not a substitute for that protocol.

## What would establish the explanation

- An organizer submission-page receipt that identifies the submitted raster and score; preserve the exact file hash.
- The official metric/version and the exact meaning of the labels, mask, and scored footprint.
- A preregistered segment-level hide-and-recover comparison of the base raster and prune, with identical folds and masks.
- A paired whole-segment bootstrap distribution for pooled-DTI difference; report evaluator version, withheld-positive count, and paired 95% CI.
- Feature-alone leakage canaries, plus proof the prune radius was not selected on the scored hidden labels.
- Pre-placement surface and final-dot correlation/overlap checks against an adequately documented registry.

None of these proof conditions is present for the reported H33 value in this checkout. No claim is made that GEMSDOE54 can currently beat 0.2778, 0.3195, or 0.3774. The two recorded 2026-10-08 surface screens stopped before emission, made no weekly-slot selection, and produced no new TIFF.

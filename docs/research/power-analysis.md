# Holdout power: the 0.0028 detection-floor question — answered

*Updated 2026-10-08 with a compliant whole-segment measurement (this session replaced the prior
circular proxy analysis with the required hide-and-recover instrument). Receipts:
[`evidence/cgrc_holdout_receipt.json`](../../evidence/cgrc_holdout_receipt.json) (final
configuration), [`evidence/cgrc_holdout_receipt_baseline_1500m.json`](../../evidence/cgrc_holdout_receipt_baseline_1500m.json),
[`evidence/cgrc_holdout_receipt_excl300_band-collapse.json`](../../evidence/cgrc_holdout_receipt_excl300_band-collapse.json).*

## Answer

**Can the holdout detect a 0.0028 DTI difference (the 0.2778 vs 0.2750 gap)?**

- **Yes — for a same-method-family paired contrast.** With the actual holdout positive-pixel count
  of **60,834 withheld catalogue cells** (drawn from **3,118 whole fault segments**, 4 spatial
  quadrant folds + 300 m buffer) and the measured paired-difference variance of a
  same-mechanism contrast (bootstrap SE 0.000498, post IR-54-021 re-verification), the raw-scale
  minimum detectable difference at two-sided α = 0.05, power 0.80 (Cohen 1988; z-sum 2.801585) is
  **MDE = 0.00140**. The 0.0028 gap is **2.0× the MDE** — comfortably above the floor. Two
  candidates that differ by 0.0028 on this holdout, compared **paired** on the same whole-segment
  draws, are distinguishable from noise at power > 0.8.
- **No — as an architecture-level ranking.** Distinct architectures (dotted vs lattice vs relay)
  carry ~10× the paired variance. The prior circular proxy measured σ_d ≈ 0.31–0.47 for
  distinct-architecture contrasts, i.e. MDE ≈ **0.012–0.018** at the same sample size. A 0.0028
  gap between *different* methods is below that floor: reading "0.2778 beats 0.2750, therefore
  architecture A beats architecture B" is reading noise.

**Consequence for the corpus:** the h33-vs-anderson 0.0028 gap (owner-recorded board values, no
receipts) is meaningful only if those two files were near-identical variants of one method family
compared paired — and even then it says nothing about which *architecture* is better. Spacing and
architecture comparisons that rest on such gaps are **not** trustworthy; only paired,
whole-segment cluster-bootstrap contrasts are.

## How it was measured (method)

1. **Withhold whole segments, not pixels.** The catalogue's 3,118 components (≥3 cells) were
   split into 4 spatial quadrant folds at centroid medians; each fold's held segments were
   expanded by a 300 m (3 px = kernel width) buffer and removed from the catalogue
   pixel-exactly. Pooled withheld positives: **60,834**.
2. **Re-derive features from the visible catalogue only** (CGRC relay/continuation geometry);
   score the **pooled** organizer DTI (α 0.2, β 0.8, 300 m triangular kernel) of the union
   emission against the union withheld truth.
3. **Whole-segment cluster bootstrap**, 2,000 replicates, paired across arms on the same draws.
   Per-replicate DTI is computed *exactly* from precomputed per-segment credit sums (T and FN are
   additive over drawn segments; M is the per-dot max over drawn segments) — a self-check
   replicate drawing every segment once reproduced the exact organizer-metric headline to 1e-6.
4. **Cohen's framework** (1988): standardized MDE from the noncentral-t power function at
   3,111 degrees of freedom (d_min = 0.0502); raw-scale MDE = 2.801585 × SE(paired delta)
   = **0.00140**. A pixel-IID floor (n = 60,834) is reported in the receipt but explicitly
   marked invalid (positives are spatially correlated within segments).

## Why positive-pixel count alone is insufficient (unchanged, and now demonstrated)

Cohen's d is a standardized effect; a raw DTI floor additionally requires a variance estimate.
Pixels on one segment are spatially correlated and share kernel neighbourhoods, so pixel counts
overstate replication. The effective unit is the **whole withheld segment** (3,118 units, not
60,834). The pixel-IID Cohen floor (0.0114 at 60,834) is ~5× *tighter* than the segment-level
floor (0.0502) — using it would overstate power five-fold. This is exactly the trap the prompt's
question targets: the sample is small *in independent units*, and the floor must be computed from
those units.

## Protocol (still in force)

A HOLDOUT-DTI receipt must identify: evaluator version; whole segments withheld with buffer and
positive-pixel count; visible-faults-only catalogue features; pixel-exact visible mask; pooled
DTI (0.2/0.8/300 m triangular); ≥1,000 paired whole-segment cluster-bootstrap replicates;
per-feature leakage canaries (AUC > 0.90 = leakage until explained). Do not tune after looking
at fold results; any adjustment requires a fresh frozen registration. `scripts/analyse_holdout_receipt.py`
enforces this schema.

## References

- Cohen, J. (1988), *Statistical Power Analysis for the Behavioral Sciences*, 2nd ed.
- Official metric/format page: https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/ (fetched 2026-10-08).
- Reference solution: https://github.com/drivendataorg/gems-prize-reference-solution.

# Power analysis: is the 0.0028 board gap inside the detection floor?

**Labels.** Holdout floors are computed from receipts, not scores. Board values are BOARD-UNVERIFIED.
Generator: `scripts/power_floor_report.py` → `evidence/power_floor_segment_cv_v2.json` (and `_v1.json`).
Evaluator: `gemsdoe54-segment-cv` v2 (receipt `evidence/holdout_segment_cv_run2_variant.json`, 3,199 segment units, 60,988 withheld positive cells).

## 1. Cohen (1988) floors, two-sided α = 0.05, power 0.80

Let z = z₀.₉₇₅ + z₀.₈₀ = 1.96 + 0.8416 = 2.8016. The minimum detectable standardized effect is d_min = z / √n.

| Unit of n | n | d_min | Status |
|---|---:|---:|---|
| Positive pixels (IID) | 60,988 | **0.0113** | **Invalid for this design.** Pixels inside one fault are strongly dependent, so the pixel count overstates information by about 4.4× in d (19× in n). |
| Independent catalogue segments | 3,199 | **0.0495** | Valid unit for this design. |
| Segments in the smallest fold | 639 | 0.1108 | Per-fold check. |

The valid unit is the segment, because the bootstrap resamples whole segments. The pixel-IID figure is reported only to show why it must not be used.

## 2. Paired-difference floors in DTI units

The receipt's own bootstrap gives the paired SE for each difference. MDE = 2.80 × SE. For a board gap Δ, the number of independent units needed for Δ to clear the same 2.80-SE margin is n_needed = 3,199 × (SE₃₁₉₉ / (Δ/2.80))².

| Paired comparison (holdout) | SE | MDE (DTI) | Units needed for Δ = 0.0028 |
|---|---:|---:|---:|
| C5 − C0 (cross-gradient vs chance) | 0.00154 | 0.0043 | 7,635 |
| C6 − C0 (basement vs chance) | 0.00156 | 0.0044 | 7,754 |
| C2 − C0 (shear ridge vs chance) | 0.00161 | 0.0045 | 8,291 |
| C3 − C0 (magnetic ridge vs chance) | 0.00174 | 0.0049 | 9,696 |
| C1 − C0 (SGMC complement vs chance) | 0.00294 | 0.0082 | 27,682 |
| C4 − C0 (learned model vs chance) | 0.00332 | 0.0093 | 35,322 |
| C1 − C2 | 0.00334 | 0.0094 | 35,749 |
| C1 − C3 | 0.00341 | 0.0095 | 37,175 |
| C4 − C1 (learned vs holdout best) | 0.00433 | 0.0121 | 60,073 |

## 3. Decision on the 0.2778 vs 0.2750 gap

**Decision: inside the floor.** The gap is 0.0028. The smallest MDE measured in this design is 0.0043, and every pair needs between 7,635 and 60,073 independent units to clear a 0.0028 difference at 80 % power. The holdout has 3,199.

**Limits of this decision:**
- The board's public split size is not published. If it contains far more independent units than 3,199, the floor is lower. The rules say only that the region is "chunked".
- The floors are for different architectures. A near-identical pair (for example a prune that removes 6 % of dots) would have a smaller paired SE and could clear 0.0028. This holdout did not measure such a pair, and the 0.2750 raster is not in the registry, so the board pair cannot be classified.
- The board values themselves are BOARD-UNVERIFIED.

**So:** no ranking claim between 0.2778 and 0.2750 is supported. Treat them as indistinguishable on the evidence available.

## 4. Reproduce

```bash
python scripts/power_floor_report.py --receipt evidence/holdout_segment_cv_run2_variant.json --tag segment_cv_v2
```

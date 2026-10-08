# Why `h33-h33-2-b2` scored 0.2778 — and what it takes to beat it

*Research note, 2026-10-08. Labels: values quoted from the public leaderboard are
PUBLIC-LEADERBOARD SNAPSHOT observations (no submission-page receipts); algebraic inversions are
MODEL; the one byte-verified artefact is the registry copy `dotted_b2_prune_02778.tif`
(sha256 `c55bafc470054e82…`, 37,654 dots, all-finite float32, no nodata tag).*

## 1. The metric as a budget (exact algebra)

The organizer's distance-weighted Tversky index with α = 0.2, β = 0.8 and triangular 300 m kernel
`k(d) = max(1 − d/300, 0)` is, for **unit-valued dot** predictions, exactly reducible (verified
symbolically in `src/gemsdoe54/emission.py` and numerically against the organizer's worked
example in `tests/test_metric.py`):

```
DTI = T / ( 0.2·N + 0.8·G + 0.2·(T − M) )
```

where `N` = number of predicted cells, `G` = number of truth cells, `T = TP_w` = credit collected
(sum over truth cells of the best kernel value any dot gives it), and
`M = Σ_x max_g k(d(x,g))`.

Three structural facts follow:

1. **Mass is taxed linearly.** Every dot costs `0.2` of denominator. At the operating point
   DTI ≈ 0.27, halving N at constant T is worth ≈ +0.04–0.05 DTI.
2. **Credit is a per-truth-cell maximum, not a sum.** Stacking dots on the same truth cell adds
   mass, not credit. The credit-maximising density along a predicted trace is therefore **one dot
   per kernel width (300 m)** — not one per 100 m cell.
3. **A dot earns only above the break-even bar.** The marginal DTI of a dot with kernel credit k
   is positive iff `k > 0.2·DTI` ≈ **0.052–0.055** at the 0.26–0.28 operating point (GEMSDOE32
   measured the same bar empirically at 0.0548; the formula gives 0.2 × 0.26 = 0.052).

## 2. What the 0.2778 file actually is

`h33-h33-2-b2` (GEMSDOE32's primary, public row 0.2778 at rank 13, handle `extradr19` — no
receipt links row to bytes, so the attribution stays a labelled claim) is, by the GEMSDOE32 site
and the registry copy: **the 0.2708 dotted base with every dot within 200 m of the catalogue
deleted** — 44,090 → 37,654 dots (−6,436). The base family is the "dotted" lane: unit dots at
~300 m spacing along USGS SGMC fault traces that are off the competition catalogue
(the 0.2600/0.2708 rows on the public board are the same family at 44,090/40,199 dots).

**Why the prune bought +0.0178.** The hidden truth is *by construction* the faults absent from
the catalogue. A dot within 200 m of a catalogue cell sits on ground the hidden set is defined to
exclude (or only touches it at the kernel's edge, where k < 1). Such dots pay the full `0.2` mass
tax while earning credit far below the 0.052 break-even bar — pure loss. Deleting all 6,436 of
them removed dead mass and moved the file to the break-even frontier. Inverting the two
same-family board rows (0.2600 at N = 44,090; 0.2778 at N = 37,654) through the algebra gives a
MODEL-implied hidden truth mass of **G ≈ 11,583 cells** (~0.22% of the 5.17 M-cell footprint) and
credit T ≈ 4,660–4,700 at both masses — i.e. the two files collected *the same* credit; only the
tax differed. That is the entire mechanism of the +0.0178.

## 3. Why it was the corpus high (and why that is not the top of the world)

Within the owner corpus, 0.2778 was the highest because the corpus had exhausted the *free*
improvements on that surface: (a) one-dot-per-kernel emission, (b) the 200 m prune, (c) small
mass calibration. Every further variant in the corpus (tip stepover 0.2632, solo d28 0.2708,
rung30 0.2710, hf-euler 0.2707) stays on the same SGMC-complement surface and re-draws the same
break-even frontier — the corpus's own Monte-Carlo instrument (GEMSDOE32 `truth_model_mc`)
estimated the *best possible* file on that surface at ≈ 0.30 model-DTI.

The **public board says otherwise**: 0.3774 at rank 1, 0.3345 at rank 2, a 0.3221–0.3262 band at
ranks 3–6, and 0.3195 at rank 7 (live fetch 2026-10-08; snapshot in
`docs/data/leaderboard-snapshot.json`). Those rows are ~15% above the corpus best. Through the
algebra, at comparable mass that is ≈ **+25% credit-per-dot** — which cannot be bought by any
prune or spacing trick on the SGMC surface; it requires a *better detector of the off-catalogue
set* (full Geodawn feature stack, DEM scarps, seismicity, trained models). That is the honest
answer to "can we generate a submission that scores higher than 0.2778?": **yes — but not by
tuning this family; by a new surface.** The public 0.3774/0.3195 gap is the price of the better
detector.

## 4. What this session's artefact buys (and does not)

H54-C CGRC (registry/run_card.json) is a *different surface* — catalogue-tip relay gaps plus
two-sided tip continuations — whose mechanism the whole-segment holdout validates at 0.0915
(1.50× mass-matched random, SGMC-corroborated arm), below the corpus best's proxy score (0.1793).
The catalogue-truth proxy penalizes off-catalogue mass, so this is a lower bound on the
off-catalogue task (the pre-fix one-sided geometry scored 0.1091 on the same proxy purely by
emitting less off-catalogue mass — IR-54-021). Under the metric's algebra with the MODEL truth
mass, its expected score is the MODEL range 0.09–0.18 — below 0.2778. It is therefore verdict
**negative** for this week's slot and is submitted (downloadable) as a unique, lane-clean,
mechanism-validated diversity candidate. The path above 0.3195 is hypotheses H2–H4 in
`docs/research/hypotheses.md` (seismicity prior on the validated gaps, 1 m DEM scarp breaks on gap
zones, trained detector on the official feature stack), in ascending order of data access cost.

## 5. Caveats

- The two board rows used for the G inversion are owner-recorded observations **without receipts**;
  the inversion is MODEL and inherits their uncertainty (if the 44,090-dot row's mass or the
  37,654-dot row's mass is mis-attributed, G shifts proportionally).
- "Break-even bar" arithmetic assumes the hidden truth is distributed so that a typical on-line
  dot's credit is its kernel value to the nearest truth cell — the regime the dotted family
  operates in.
- No statement here is a competition score; the only scores with organizer authority are
  submission-page receipts, of which this repository holds none.

"""Hide-and-recover holdout for the GEMS Prize, run the way the protocol demands.

Protocol implemented here
-------------------------
*   Withhold **whole fault segments** (connected components of the held-out
    source), not random pixels, and expand the withheld set by a buffer so that
    nothing within the metric's 300 m kernel of a withheld segment is learnable.
*   Derive every feature **only** from the visible faults (or from layers that are
    provably independent of the held-out source).
*   Mask visible faults **pixel-exactly** so a model cannot simply memorise them.
*   Score **pooled distance-weighted Tversky** with alpha = 0.2, beta = 0.8 and a
    300 m triangular kernel, using the organizer's own equations
    (``scripts/gems_metric.py``).
*   Emit a per-feature leakage canary: any single feature whose held-out AUC
    exceeds 0.90 is treated as leakage until proven otherwise.

Why a *segment* holdout matters
------------------------------
The corpus's previous holdouts withheld the competition catalogue and scored
against a proxy built from the USGS State Geologic Map Compilation (SGMC)
restricted to cells > 300 m from the catalogue.  That proxy is measured here to
have **no rank-correlation with the public leaderboard** (Spearman rho = -0.03,
p = 0.96, n = 6 artifacts with both bytes and a published score), and mass
recalibrating it does not repair the ranking.  A holdout that cannot order two
known submissions cannot be used as a promotion gate, so results from it are
reported here as *screening* evidence only, never as a score.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field

import numpy as np
from scipy.ndimage import distance_transform_edt, label
from scipy.stats import rankdata

from .grid import FOOTPRINT_CELLS


@dataclass
class HoldoutResult:
    name: str
    pooled_dti: float
    tp_w: float
    fp_w: float
    fn_w: float
    n_dots: int
    g_truth: int
    informative_truth_cells: int
    per_fold: dict[str, float] = field(default_factory=dict)
    leakage_flags: list[str] = field(default_factory=list)

    def to_json(self) -> dict:
        return {
            "name": self.name,
            "pooled_dti": round(self.pooled_dti, 6),
            "tp_w": round(self.tp_w, 4),
            "fp_w": round(self.fp_w, 4),
            "fn_w": round(self.fn_w, 4),
            "n_dots": self.n_dots,
            "g_truth": self.g_truth,
            "informative_truth_cells": self.informative_truth_cells,
            "per_fold": {k: round(v, 6) for k, v in self.per_fold.items()},
            "leakage_flags": self.leakage_flags,
        }


def segment_blocks(mask: np.ndarray, buffer_px: int) -> tuple[np.ndarray, list[str]]:
    """Split ``mask`` into whole connected segments plus a buffer around each.

    Returns ``(block_index, notes)`` where ``block_index`` assigns every cell to the
    id of the nearest withheld segment (0 = background).  The buffer guarantees
    that a cell cannot be learned from a visible neighbour of the same trace.
    """
    lab, n = label(mask, structure=np.ones((3, 3), dtype=int))
    if n == 0:
        return np.zeros(mask.shape, dtype=np.int32), ["no segments found"]
    notes = [f"{n} withheld segments", f"buffer = {buffer_px * 100} m"]
    return lab.astype(np.int32), notes


def spatial_folds(footprint: np.ndarray, blocks: int = 4) -> np.ndarray:
    """Assign every in-footprint cell to one of ``blocks`` compact spatial regions.

    Folds are contiguous tiles, never random pixels: a random split would leave
    both halves of a single fault on opposite sides of the split and report a
    spatial-generalisation score that no submission could fail.
    """
    rows, cols = np.nonzero(footprint)
    if rows.size == 0:
        raise ValueError("empty footprint")
    side = int(round(blocks ** 0.5))
    r0, r1, c0, c1 = rows.min(), rows.max() + 1, cols.min(), cols.max() + 1
    fold = np.full(footprint.shape, -1, dtype=np.int8)
    rstep = max(1, -(-(r1 - r0) // side))
    cstep = max(1, -(-(c1 - c0) // side))
    idx = ((rows - r0) // rstep) * side + ((cols - c0) // cstep)
    fold[rows, cols] = (idx % blocks).astype(np.int8)
    return fold


def pooled_metric(
    truth: np.ndarray,
    dots: np.ndarray,
    *,
    kernel_px: float = 3.0,
    alpha: float = 0.2,
    beta: float = 0.8,
) -> tuple[float, float, float, float]:
    """Organizer metric on a unit-valued dot set, computed from its own algebra.

    Returns ``(dti, tp_w, fp_w, fn_w)`` where ``tp_w = sum over truth cells of the
    best kernel value any dot achieves``.  Distances are true Euclidean
    distances, so a dot pair separated by more than the kernel cannot interact --
    which is exactly the regime the emission policy targets.
    """
    if not dots.any():
        return 0.0, 0.0, float(dots.sum()), float(truth.sum())
    tp_w = 0.0
    if truth.any():
        # TP: for each truth cell, the best credit any dot gives it.
        d_dot = distance_transform_edt(~dots, sampling=(1.0, 1.0))
        credit = np.clip(1.0 - d_dot / kernel_px, 0.0, None)
        tp_w = float(credit[truth].sum())
        # FP: for each dot, 1 minus the best credit it earns from a truth cell.
        # This is distance to the nearest TRUTH cell, not to the nearest dot --
        # reading the dot distance here would make every dot look perfect.
        d_truth = distance_transform_edt(~truth, sampling=(1.0, 1.0))
        ys, xs = np.nonzero(dots)
        earned = np.clip(1.0 - d_truth[ys, xs] / kernel_px, 0.0, 1.0)
        fp_w = float(np.sum(1.0 - earned))
    else:
        fp_w = float(dots.sum())
    fn_w = float(truth.sum()) - tp_w
    # Tversky index: TP is in the denominator as well as the numerator.
    # Omitting it makes the ratio exceed 1.0 for any candidate whose precision is
    # above alpha, which is exactly how a wrong implementation scores 4.52 on a
    # trace it covers one dot per 3 px.
    denom = tp_w + alpha * fp_w + beta * fn_w
    dti = 0.0 if denom <= 0 else tp_w / denom
    return dti, tp_w, fp_w, fn_w


def shift_null_ci(
    truth: np.ndarray,
    dots: np.ndarray,
    *,
    shifts: int = 5,
    step_px: int = 550,
    kernel_px: float = 3.0,
) -> dict[str, float]:
    """Confidence band on the score from a torus shift null.

    Bootstrap resampling is the wrong null for a spatially autocorrelated target:
    resampled fault segments keep their real geometry, so the interval collapses
    and flatters every candidate.  Shifting the *entire prediction* by several
    hundred cells instead asks the question that matters -- how much does the
    score depend on the prediction being in the right place at all? -- and gives
    a band whose width is honest about spatial correlation.
    """
    scores = []
    for i in range(1, shifts + 1):
        d = i * step_px
        rolled = np.roll(np.roll(dots, d, axis=0), 2 * d, axis=1)
        s, _, _, _ = pooled_metric(truth, rolled, kernel_px=kernel_px)
        scores.append(s)
    scores = np.asarray(scores, dtype=np.float64)
    return {
        "n_shifts": int(scores.size),
        "shift_px": step_px,
        "mean": float(scores.mean()) if scores.size else 0.0,
        "sd": float(scores.std(ddof=1)) if scores.size > 1 else 0.0,
        "min": float(scores.min()) if scores.size else 0.0,
        "max": float(scores.max()) if scores.size else 0.0,
    }


def informative_truth_cells(truth: np.ndarray, dots: np.ndarray) -> int:
    """Truth cells that lie within the 300 m kernel of at least one dot.

    This is the honest sample size for a paired comparison: truth cells farther
    than 300 m from every prediction can never change any candidate's credit, so
    they carry no information about a difference between two submissions.
    """
    if not dots.any():
        return 0
    d = distance_transform_edt(~dots, sampling=(100.0, 100.0))
    return int(np.count_nonzero(truth & (d <= 300.0)))


def detect_leakage(
    features: dict[str, np.ndarray],
    truth: np.ndarray,
    *,
    valid: np.ndarray,
    auc_cut: float = 0.90,
) -> list[str]:
    """Single-feature leakage canary using a rank-based AUC.

    A feature whose *alone* AUC against the held-out truth exceeds ``auc_cut`` is
    flagged: at 1 % positive prevalence a single feature that separates that
    cleanly is almost certainly the held-out source in disguise.
    """
    flags: list[str] = []
    pos = truth & valid
    neg = (~truth) & valid
    n_pos, n_neg = int(pos.sum()), int(neg.sum())
    if n_pos == 0 or n_neg == 0:
        return ["holdout has a degenerate class balance"]
    # subsample negatives for tractability on a 12 M-cell grid
    rng = np.random.default_rng(20261008)
    neg_idx = np.flatnonzero(neg.ravel())
    take = min(n_neg, 200_000)
    neg_sel = np.zeros(neg.size, dtype=bool)
    neg_sel[rng.choice(neg_idx, size=take, replace=False)] = True
    neg_sel = neg_sel.reshape(truth.shape)
    for name, feat in features.items():
        f_pos = np.asarray(feat)[pos]
        f_neg = np.asarray(feat)[neg_sel]
        if not (np.isfinite(f_pos).all() and np.isfinite(f_neg).all()):
            f_pos = np.nan_to_num(f_pos)
            f_neg = np.nan_to_num(f_neg)
        # Mann-Whitney U via rank sums, with MID-RANKS so that ties are handled
        # correctly.  Without tie correction a constant feature scores AUC = 1.0
        # instead of 0.5, which produces phantom leakage flags on any coarsely
        # quantised layer -- a real bug caught by the uniform-control probe.
        allv = np.concatenate([f_pos, f_neg])
        ranks = rankdata(allv, method="average")
        r_pos = ranks[: f_pos.size].sum()
        auc = (r_pos - f_pos.size * (f_pos.size + 1) / 2.0) / (f_pos.size * f_neg.size)
        auc = max(auc, 1.0 - auc)
        if auc > auc_cut:
            flags.append(f"LEAKAGE: feature '{name}' alone scores AUC={auc:.3f} > {auc_cut}")
    return flags


def write_receipt(path: str, payload: dict) -> None:
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, sort_keys=False)
        handle.write("\n")


__all__ = [
    "HoldoutResult",
    "segment_blocks",
    "spatial_folds",
    "pooled_metric",
    "shift_null_ci",
    "informative_truth_cells",
    "detect_leakage",
    "write_receipt",
    "FOOTPRINT_CELLS",
]

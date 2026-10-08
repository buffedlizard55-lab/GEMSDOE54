"""Exact leave-one-segment-group-out jackknife for the pooled distance-weighted Tversky index.

Why this module exists
----------------------
A split-to-split spread is NOT a valid uncertainty for the pooled holdout: the pooled
design withholds every catalogue neighbourhood exactly once per split, so a candidate's
pooled score is nearly invariant to the random partition (observed: identical to five
decimals across splits).  The independent unit is the buffered segment group.

For binary dots P and a truth set G split into groups g:
  * TP_w   = sum_c best_c,    best_c = max(0, 1 - d(c, P)/R)   (exact per truth cell)
  * FN_w   = |G| - TP_w                                         (exact)
  * FP_w   = sum_x (1 - K1(x)),  K1(x) = max_g k(d(x, g))        (exact)
Removing group g changes only FP_w (for dots whose best group is g, K1 falls to the
second-best group K2) and TP_w (by TP_g) and |G| (by n_g).  So each leave-one-out value
is exact, not an approximation:
  FP'  = FP + sum_{x: G1(x)=g} (K1(x) - K2(x))
  TP'  = TP - TP_g,  FN' = (|G| - n_g) - TP'
Tests in tests/test_jackknife.py compare every leave-one-out value with brute-force
recomputation via scripts/gems_metric.py.
"""

from __future__ import annotations

import numpy as np
from scipy.ndimage import distance_transform_edt

PIXEL_M = 100.0
RADIUS_M = 300.0
ALPHA = 0.2
BETA = 0.8


def _kernel(d_m: np.ndarray) -> np.ndarray:
    return np.maximum(1.0 - d_m / RADIUS_M, 0.0)


def group_jackknife_counts(dots: np.ndarray, truth: np.ndarray, group_id: np.ndarray,
                           valid: np.ndarray) -> dict:
    """Pooled counts for one evaluation plus exact per-group leave-one-out deltas.

    Parameters
    ----------
    dots      boolean dot mask (footprint-restricted by the caller)
    truth     boolean truth mask (catalogue cells withheld in THIS evaluation)
    group_id  int array, buffered-group id per cell (0 = none); must be defined on truth
    valid     boolean scored footprint

    Returns
    -------
    dict with totals (TP, FP, FN, G) and arrays ``gids``, ``tp_g``, ``n_g``, ``dfp_g``
    describing the leave-one-group-out change of each group in ``gids``.
    """
    dots = np.asarray(dots, dtype=bool) & valid
    truth = np.asarray(truth, dtype=bool) & valid
    gid = np.asarray(group_id)
    gids = np.unique(gid[truth & (gid > 0)])
    G = int(truth.sum())
    if G == 0:
        raise ValueError("truth is empty")
    if not dots.any():
        zeros = np.zeros(gids.size)
        n_g = np.array([int(np.count_nonzero(truth & (gid == g))) for g in gids], dtype=np.int64)
        return {"TP": 0.0, "FP": 0.0, "FN": float(G), "G": G, "gids": gids,
                "tp_g": zeros, "n_g": n_g, "dfp_g": zeros.copy()}

    # Exact TP per truth cell from the distance to the nearest dot.
    d_dot = distance_transform_edt(~dots, sampling=PIXEL_M)
    best = _kernel(d_dot)

    shape = dots.shape
    K1 = np.zeros(shape, dtype=np.float64)
    K2 = np.zeros(shape, dtype=np.float64)
    G1 = np.full(shape, -1, dtype=np.int64)
    radius_px = int(np.ceil(RADIUS_M / PIXEL_M))

    tp_g = np.zeros(gids.size)
    n_g = np.zeros(gids.size, dtype=np.int64)
    for i, g in enumerate(gids):
        cells = truth & (gid == g)
        n_g[i] = int(cells.sum())
        tp_g[i] = float(best[cells].sum())
        rr, cc = np.nonzero(cells)
        r0 = max(0, rr.min() - radius_px)
        r1 = min(shape[0], rr.max() + radius_px + 1)
        c0 = max(0, cc.min() - radius_px)
        c1 = min(shape[1], cc.max() + radius_px + 1)
        win = (slice(r0, r1), slice(c0, c1))
        d_loc = distance_transform_edt(~cells[win], sampling=PIXEL_M)
        kern = _kernel(d_loc)
        on = dots[win] & (kern > 0)
        if not on.any():
            continue
        k1 = K1[win]
        k2 = K2[win]
        g1 = G1[win]
        upd = on & (kern > k1)
        k2[upd] = k1[upd]
        g1[upd] = g
        k1[upd] = kern[upd]
        upd2 = on & ~upd & (kern > k2)
        k2[upd2] = kern[upd2]
        # views write back automatically; assign explicitly for clarity
        K1[win], K2[win], G1[win] = k1, k2, g1

    dot_idx = dots
    fp = float(np.sum(1.0 - K1[dot_idx]))
    tp = float(tp_g.sum())
    fn = float(G - tp)

    dfp_g = np.zeros(gids.size)
    sel = dot_idx & (G1 >= 0)
    g_of = G1[sel]
    delta = (K1 - K2)[sel]
    order = np.argsort(gids)
    pos = np.searchsorted(gids[order], g_of)
    idx = order[pos]
    np.add.at(dfp_g, idx, delta)

    return {"TP": tp, "FP": fp, "FN": fn, "G": G, "gids": gids,
            "tp_g": tp_g, "n_g": n_g, "dfp_g": dfp_g}


def pooled_dti_from_counts(tp: float, fp: float, fn: float) -> float:
    denom = tp + ALPHA * fp + BETA * fn
    return tp / denom if denom > 0 else 0.0


def leave_one_out_dti(counts: dict) -> np.ndarray:
    """DTI with each group removed from the truth set (predictions held fixed)."""
    tp, fp, G = counts["TP"], counts["FP"], counts["G"]
    tp_loo = tp - counts["tp_g"]
    fp_loo = fp + counts["dfp_g"]
    fn_loo = (G - counts["n_g"]) - tp_loo
    denom = tp_loo + ALPHA * fp_loo + BETA * fn_loo
    with np.errstate(divide="ignore", invalid="ignore"):
        out = np.where(denom > 0, tp_loo / denom, 0.0)
    return out


def jackknife_se(theta_loo: np.ndarray) -> float:
    n = theta_loo.size
    if n < 2:
        raise ValueError("need at least two groups")
    mean = theta_loo.mean()
    return float(np.sqrt((n - 1) / n * np.sum((theta_loo - mean) ** 2)))


__all__ = [
    "group_jackknife_counts",
    "pooled_dti_from_counts",
    "leave_one_out_dti",
    "jackknife_se",
]

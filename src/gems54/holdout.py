"""Spatially-blocked hide-and-recover holdout -- the shared evaluator for this project.

Design (fixed before results were read; registered in ``registry/preregistration.json``):

1. The catalogue (``labels.tif``, 60,988 px) is split into 8-connected components ("segments").
2. Segments are assigned to one of four spatial quadrants by their centroid.  Whole segments are
   withheld, never pixel subsets: this is what "hide whole fault segments" means.
3. Visible segments are dilated by the buffer (default 3 px = 300 m) and those pixels are removed
   from the withheld truth, so a withheld pixel cannot be hit by simply painting a visible fault.
4. For every fold, every *catalogue-derived feature* (distance to fault, fault density ... ) is
   derived ONLY from that fold's visible segments.
5. Predictions are built per-fold inside the fold's quadrant and scored, then pooled:
   ``T = sum_folds T_f``, ``F = sum_folds F_f``, ``K = sum_folds K_f`` -- the pooled DTI.

The metric is the exact one from :mod:`gems54.metric`, verified against the organizers' published
worked example and against the exact homogeneity law DTI(lam p) = lam T / (lam a (T+F) + b K).
"""
from __future__ import annotations

import numpy as np
from scipy import ndimage

from . import metric as M

QUADRANTS = ("NW", "NE", "SW", "SE")


def catalogue_segments(min_px: int = 5) -> np.ndarray:
    """8-connected component labels of the catalogue; components < ``min_px`` are dropped."""
    from . import data as D

    lab = D.labels()
    comp, n = ndimage.label(lab, structure=np.ones((3, 3), int))
    sizes = np.bincount(comp.ravel())
    keep = np.zeros(n + 1, bool)
    keep[1:] = sizes[1:] >= min_px
    return np.where(keep[comp], comp, 0)


def fold_assignment(comp: np.ndarray, footprint: np.ndarray) -> dict[str, np.ndarray]:
    """Assign each component to a quadrant by its centroid."""
    ys, xs = np.nonzero(footprint)
    y0, y1, x0, x1 = ys.min(), ys.max(), xs.min(), xs.max()
    ymid, xmid = (y0 + y1) / 2.0, (x0 + x1) / 2.0
    ids = np.arange(1, comp.max() + 1)
    cents = ndimage.center_of_mass(comp > 0, comp, ids)
    out: dict[str, list[int]] = {q: [] for q in QUADRANTS}
    for i, (cy, cx) in zip(ids, cents):
        q = ("N" if cy <= ymid else "S") + ("W" if cx <= xmid else "E")
        out[q].append(int(i))
    return {q: np.array(v, dtype=int) for q, v in out.items()}


def build_folds(comp: np.ndarray, footprint: np.ndarray, buffer_px: int = 3):
    """Yield ``(name, truth_mask, visible_mask, quadrant_slice)`` for each fold."""
    assign = fold_assignment(comp, footprint)
    ys, xs = np.nonzero(footprint)
    y0, y1, x0, x1 = ys.min(), ys.max(), xs.min(), xs.max()
    ymid, xmid = (y0 + y1) // 2, (x0 + x1) // 2
    quads = {"NW": (slice(y0, ymid), slice(x0, xmid)), "NE": (slice(y0, ymid), slice(xmid, x1 + 1)),
             "SW": (slice(ymid, y1 + 1), slice(x0, xmid)), "SE": (slice(ymid, y1 + 1), slice(xmid, x1 + 1))}
    for q in QUADRANTS:
        held_ids = assign[q]
        held = np.isin(comp, held_ids) & footprint
        vis = (comp > 0) & ~np.isin(comp, held_ids) & footprint
        if not held.any():
            continue
        vis_buf = ndimage.binary_dilation(vis, np.ones((2 * buffer_px + 1, 2 * buffer_px + 1), bool))
        truth = held & ~vis_buf
        if truth.sum() < 50:
            continue
        yield q, truth, vis, quads[q]


def pooled_dti(preds: dict[str, np.ndarray], truths: dict[str, np.ndarray],
               alpha: float = M.ALPHA, beta: float = M.BETA) -> dict:
    """Pool the metric terms over folds before forming the index (the protocol's pooled DTI)."""
    tp = fp = fn = k = 0.0
    per_fold = {}
    for q in preds:
        _, t = M.dti(preds[q], truths[q], alpha=alpha, beta=beta, return_terms=True)
        per_fold[q] = t["TPw"] / (t["TPw"] + alpha * t["FPw"] + beta * t["FNw"] + 1e-12)
        tp += t["TPw"]; fp += t["FPw"]; fn += t["FNw"]; k += t["K"]
    pooled = tp / (tp + alpha * fp + beta * fn + 1e-12)
    return {"pooled_dti": pooled, "TPw": tp, "FPw": fp, "FNw": fn, "K": k, "per_fold": per_fold}


# --------------------------------------------------------------------------------------- power
def mde_from_differences(diffs: np.ndarray, alpha: float = 0.05, power: float = 0.80) -> dict:
    """Cohen-style minimum detectable effect for a PAIRED design with n folds.

    MDE = (t_{1-alpha/2, n-1} + t_{power, n-1}) * s_d / sqrt(n).
    Returns the MDE, the observed mean difference and whether it clears the floor.
    """
    from scipy import stats

    d = np.asarray([x for x in diffs if np.isfinite(x)], dtype=float)
    n = len(d)
    if n < 2:
        return {"n": n, "mde": float("nan")}
    sd = float(d.std(ddof=1))
    se = sd / np.sqrt(n)
    t_crit = stats.t.ppf(1 - alpha / 2, n - 1)
    t_pow = stats.t.ppf(power, n - 1)
    mde = (t_crit + t_pow) * se
    mean = float(d.mean())
    from scipy import stats as st
    tt = st.ttest_rel(d, np.zeros_like(d)) if n > 1 else None
    return {"n": n, "mean_diff": mean, "sd": sd, "se": se,
            "t_crit": float(t_crit), "t_power": float(t_pow),
            "mde_power80_alpha05": float(mde),
            "detected": bool(abs(mean) > mde),
            "p_value": float(tt.pvalue) if tt is not None else float("nan")}


def single_truth_pixel_step(tp: float, fp: float, k: float, alpha: float = M.ALPHA,
                            beta: float = M.BETA) -> float:
    """The DTI change from covering ONE more withheld truth pixel (the instrument's resolution).

    dDTI/dT = (beta*K + alpha*F) / D^2 with D = alpha*(T+F) + beta*K.
    """
    d = alpha * (tp + fp) + beta * k
    return (beta * k + alpha * fp) / (d * d)


def unit_floor(k_truth_px: int, mean_credit_loss: float = 0.5) -> float:
    """Binomial noise floor: the DTI shift expected from ``sqrt(K)`` independent coin-flip credits.

    A paired comparison can only distinguish changes larger than the sampling granularity of a
    finite truth set; with K independent truth pixels and a typical per-pixel credit change of
    ``mean_credit_loss``, the standard error of the summed credit is ``mean_credit_loss*sqrt(K)``.
    """
    return mean_credit_loss * np.sqrt(max(k_truth_px, 1))

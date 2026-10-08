"""Exact re-implementation of the ORGANIZER-PUBLISHED GEMS distance-weighted Tversky index.

Source of truth (verified 2026-10-08):
  https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/
  "# Performance metric" / "# Mathematical representation"

Official definitions transcribed verbatim from that page:

    TI(a,b) = sum_x p(x)g(x)
              / ( sum_x p(x)g(x) + a*sum_x p(x)(1-g(x)) + b*sum_x (1-p(x))g(x) )

    k(d) = max(1 - d/R, 0),  R = 300 m

    TP_w = sum_{g in G} max_{x: d(x,g) <= R} p(x) k(d(x,g))
    FP_w = sum_{x: p(x) > 0} p(x) [ 1 - max_{g in G} k(d(x,g)) ]
    FN_w = sum_{g in G} [ 1 - max_{x: d(x,g) <= R} p(x) k(d(x,g)) ]
    DTI(a,b) = TP_w / (TP_w + a*FP_w + b*FN_w + eps),  a=0.2, b=0.8

Organizer worked example (same page, "# Scoring example"): TP_w=3.00, FP_w=1.89,
FN_w=2.00 -> TI_w = 3.00/(3.00 + 0.2*1.89 + 0.8*2.00) = 0.60.  Regression-tested in
tests/test_metric.py.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import ceil

import numpy as np
from scipy.ndimage import distance_transform_edt

ALPHA = 0.2
BETA = 0.8
RADIUS_M = 300.0


@dataclass(frozen=True)
class Components:
    tp_w: float
    fp_w: float
    fn_w: float
    dti: float


def dti_components(
    prediction: np.ndarray,
    truth: np.ndarray,
    *,
    valid: np.ndarray | None = None,
    pixel_size_m: float | tuple[float, float] = 100.0,
    radius_m: float = RADIUS_M,
    alpha: float = ALPHA,
    beta: float = BETA,
    epsilon: float = 1e-8,
) -> Components:
    """Return (TP_w, FP_w, FN_w, DTI) exactly as the organizer defines them.

    ``valid`` selects the scored footprint.  Predictions outside ``valid`` never enter
    either term (the organizer rasterises the submission onto the training grid and only
    in-footprint cells are scored).
    """
    pred = np.asarray(prediction)
    lab = np.asarray(truth)
    if pred.shape != lab.shape or pred.ndim != 2:
        raise ValueError("prediction and truth must be same-shape 2-D arrays")

    row_m, col_m = (pixel_size_m, pixel_size_m) if np.isscalar(pixel_size_m) else tuple(pixel_size_m)
    if valid is None:
        valid = np.ones(pred.shape, dtype=bool)
    else:
        valid = np.asarray(valid, dtype=bool)
        if valid.shape != pred.shape:
            raise ValueError("valid mask shape must match")

    if np.any(~np.isfinite(pred[valid])):
        raise ValueError("prediction has non-finite values inside the scored footprint")
    if np.any((pred[valid] < 0) | (pred[valid] > 1)):
        raise ValueError("prediction has values outside [0,1] inside the scored footprint")

    p = np.where(valid, pred, 0.0).astype(np.float64, copy=False)
    g = (lab == 1) & valid

    if not g.any():
        tp = 0.0
        fp = float(p[valid].sum())
        return Components(tp, fp, 0.0, tp / (tp + alpha * fp + epsilon))

    # FP_w: distance from every *positive* prediction cell to the nearest truth cell.
    d_to_truth = distance_transform_edt(~g, sampling=(row_m, col_m))
    kernel_to_truth = np.maximum(1.0 - d_to_truth / radius_m, 0.0)
    fp = float(np.sum(p[valid] * (1.0 - kernel_to_truth[valid])))

    # TP_w / FN_w: for each truth cell, the best p(x)*k(d) among predictions within R.
    best = np.zeros(p.shape, dtype=np.float64)
    dr = int(ceil(radius_m / row_m))
    dc = int(ceil(radius_m / col_m))
    for dy in range(-dr, dr + 1):
        for dx in range(-dc, dc + 1):
            d = float(np.hypot(dy * row_m, dx * col_m))
            if d > radius_m:
                continue
            y0, y1 = max(0, -dy), min(p.shape[0], p.shape[0] - dy)
            x0, x1 = max(0, -dx), min(p.shape[1], p.shape[1] - dx)
            if y0 >= y1 or x0 >= x1:
                continue
            w = 1.0 - d / radius_m
            tgt = best[y0:y1, x0:x1]
            np.maximum(tgt, p[y0 + dy:y1 + dy, x0 + dx:x1 + dx] * w, out=tgt)

    tp = float(best[g].sum())
    fn = float(g.sum() - tp)
    return Components(tp, fp, fn, tp / (tp + alpha * fp + beta * fn + epsilon))


def dti(prediction: np.ndarray, truth: np.ndarray, **kw) -> float:
    return dti_components(prediction, truth, **kw).dti


def kernel_mass(prediction: np.ndarray, truth: np.ndarray, *,
                valid: np.ndarray | None = None, pixel_size_m=100.0,
                radius_m: float = RADIUS_M) -> float:
    """M = sum_x max_g k(d(x,g)) over predicted cells.

    Identity (exact, binary or continuous predictions):
        FP_w = sum_x p(x) - M_p   where M_p = sum_x p(x) * max_g k(d(x,g))
    With unit-valued predictions FP_w = N - M, giving the closed form used in
    registry/score_algebra.json:
        DTI = T / (0.2N + 0.8G + 0.2(T - M))
    """
    pred = np.asarray(prediction)
    lab = np.asarray(truth)
    if valid is None:
        valid = np.ones(pred.shape, dtype=bool)
    valid = np.asarray(valid, dtype=bool)
    g = (lab == 1) & valid
    p = np.where(valid, pred, 0.0).astype(np.float64, copy=False)
    if not g.any():
        return 0.0
    d = distance_transform_edt(~g, sampling=(pixel_size_m, pixel_size_m))
    k = np.maximum(1.0 - d / radius_m, 0.0)
    return float(np.sum(p[valid] * k[valid]))

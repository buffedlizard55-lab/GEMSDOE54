"""Exact Distance-weighted Tversky Index (DTI) for the DOE GEMS Prize, and its decision theory.

Official definition (https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/,
fetched and read 2026-10-08 from this environment):

    TP_w = sum_{g in G} max_{x : d(x,g) <= R} p(x) k(d(x,g))
    FP_w = sum_{x : p(x) > 0} p(x) [1 - max_{g in G} k(d(x,g))]
    FN_w = sum_{g in G} [1 - max_{x : d(x,g) <= R} p(x) k(d(x,g))]
    k(d) = (1 - d/R)_+ ,  R = 300 m
    DTI  = TP_w / (TP_w + alpha*FP_w + beta*FN_w + eps),  alpha = 0.2, beta = 0.8

Identities used everywhere below (exact, derived not fitted):

    FN_w = K - TP_w                     with K = |G| (sum of truth mass)
    FP_w = S - M                        with S = sum_x p(x), M = sum_x p(x)*max_g k(d(x,g))
    DTI  = T / ( alpha*(T + F) + beta*K )
    1/DTI = alpha + alpha*(F/T) + beta*(K/T)

Decision theory: adding one unit of mass at x changes the denominator by
``alpha * (dT + 1 - kbar(x))`` where ``kbar(x) = max_g k(d(x,g))`` and ``dT`` is the newly claimed
credit, so a dot pays iff ``dT > kbar(x) - 1 + alpha*DTI``; for a dot sitting on a truth pixel
(``kbar = 1``) any ``dT > alpha*DTI`` pays.

The published worked example (TP_w = 3.00, FP_w = 1.89, FN_w = 2.00 -> 0.60) is asserted in
``tests`` via :func:`dti_from_terms`.
"""
from __future__ import annotations

import numpy as np
from scipy import ndimage

ALPHA = 0.2
BETA = 0.8
R_M = 300.0
RES_M = 100.0


def dti_from_terms(tp: float, fp: float, fn: float, alpha: float = ALPHA, beta: float = BETA) -> float:
    """DTI from already-computed weighted terms (used for the official worked example)."""
    return tp / (tp + alpha * fp + beta * fn + 1e-12)


def _offsets(radius_m: float, res_m: float) -> list[tuple[int, int, float]]:
    """Pixel offsets within ``radius_m`` and their kernel weights k(d)."""
    r = int(np.floor(radius_m / res_m))
    out = []
    for dy in range(-r, r + 1):
        for dx in range(-r, r + 1):
            d = res_m * float(np.hypot(dx, dy))
            if d <= radius_m:
                out.append((dy, dx, 1.0 - d / radius_m))
    return out


def _shift(a: np.ndarray, dy: int, dx: int) -> np.ndarray:
    """Shift ``a`` by (dy, dx) with zero fill; result[y, x] == a[y - dy, x - dx]."""
    out = np.zeros_like(a)
    h, w = a.shape
    ys0, ys1 = max(0, dy), min(h, h + dy)
    xs0, xs1 = max(0, dx), min(w, w + dx)
    if ys0 < ys1 and xs0 < xs1:
        out[ys0:ys1, xs0:xs1] = a[ys0 - dy:ys1 - dy, xs0 - dx:xs1 - dx]
    return out


def kernel_cover(pred: np.ndarray, radius_m: float = R_M, res_m: float = RES_M) -> np.ndarray:
    """For every cell g, ``max_{x : d(x,g) <= R} pred(x) * k(d(x,g))`` (the TP integrand)."""
    cover = np.zeros_like(pred, dtype=np.float32)
    offs = _offsets(radius_m, res_m)
    for dy, dx, k in offs:
        if k <= 0.0:
            continue
        np.maximum(cover, _shift(pred, dy, dx) * np.float32(k), out=cover)
    return cover


def nearest_kernel(truth: np.ndarray, radius_m: float = R_M, res_m: float = RES_M) -> np.ndarray:
    """For every cell x, ``max_{g in G} k(d(x,g))`` (1 on truth, linear falloff, 0 beyond R)."""
    if not truth.any():
        return np.zeros_like(truth, dtype=np.float32)
    # Euclidean distance in metres to the nearest truth cell.
    dist_px = ndimage.distance_transform_edt(~truth.astype(bool))
    dist_m = dist_px * res_m
    return np.maximum(1.0 - dist_m / radius_m, 0.0).astype(np.float32)


def dti(pred: np.ndarray, truth: np.ndarray, alpha: float = ALPHA, beta: float = BETA,
        radius_m: float = R_M, res_m: float = RES_M, return_terms: bool = False):
    """Exact distance-weighted Tversky index.

    ``pred``  float array, values expected in [0, 1]; NaNs are treated as 0 (no prediction).
    ``truth`` boolean/0-1 array of the scored ground-truth pixels.
    """
    pred = np.nan_to_num(np.asarray(pred, dtype=np.float32), nan=0.0, posinf=0.0, neginf=0.0)
    truth = np.asarray(truth).astype(bool)
    cover = kernel_cover(pred, radius_m, res_m)
    kbar = nearest_kernel(truth, radius_m, res_m)

    tp = float(np.sum(cover[truth])) if truth.any() else 0.0
    k = float(truth.sum())
    fn = k - tp
    fp = float(np.sum(pred * (1.0 - kbar)))
    value = dti_from_terms(tp, fp, fn, alpha, beta)
    if return_terms:
        return value, {"TPw": tp, "FPw": fp, "FNw": fn, "K": k,
                       "S": float(pred.sum()), "M": float(np.sum(pred * kbar))}
    return value


def scaling_check(pred: np.ndarray, truth: np.ndarray, lam: float, **kw) -> tuple[float, float]:
    """Verify the exact homogeneity law DTI(lam*p) = lam*T / (lam*alpha*(T+F) + beta*K)."""
    _, terms = dti(pred, truth, return_terms=True, **kw)
    t, f, k = terms["TPw"], terms["FPw"], terms["K"]
    predicted = lam * t / (lam * ALPHA * (t + f) + BETA * k + 1e-12)
    return dti(pred * lam, truth, **kw), predicted


def marginal_bar(dti_value: float, alpha: float = ALPHA) -> float:
    """Credit a newly added unit of mass must exceed to raise DTI: alpha * DTI."""
    return alpha * dti_value


def recall_required(target: float, rho: float, alpha: float = ALPHA, beta: float = BETA) -> float:
    """Weighted recall of hidden truth x = T/K needed for ``target`` at false-positive ratio rho = F/K."""
    return (alpha * rho + beta) / (1.0 / target - alpha)


def dti_sparse(pred: np.ndarray, truth: np.ndarray, knear: np.ndarray | None = None,
               radius_m: float = R_M, res_m: float = RES_M,
               alpha: float = ALPHA, beta: float = BETA) -> dict:
    """Exact DTI in O(#truth + #support) after one distance transform.

    Mathematically identical to :func:`dti`; used because the arm sweep needs ~100x the speed.
    ``knear`` (from :func:`nearest_kernel`) may be reused across arms scored on the same truth.
    """
    pred = np.nan_to_num(np.asarray(pred, dtype=np.float32), nan=0.0, posinf=0.0, neginf=0.0)
    truth = np.asarray(truth).astype(bool)
    if knear is None:
        knear = nearest_kernel(truth, radius_m, res_m)
    ty, tx = np.nonzero(truth)
    k = float(truth.sum())
    cover = np.zeros(len(ty), dtype=np.float32)
    h, w = pred.shape
    for dy, dx, kk in _offsets(radius_m, res_m):
        if kk <= 0.0:
            continue
        yy, xx = ty + dy, tx + dx
        ok = (yy >= 0) & (yy < h) & (xx >= 0) & (xx < w)
        if not ok.any():
            continue
        vals = np.zeros(len(ty), dtype=np.float32)
        vals[ok] = pred[yy[ok], xx[ok]] * np.float32(kk)
        np.maximum(cover, vals, out=cover)
    tp = float(cover.sum())
    support = pred > 0
    fp = float(np.sum(pred[support] * (1.0 - knear[support])))
    fn = k - tp
    return {"DTI": dti_from_terms(tp, fp, fn, alpha, beta), "TPw": tp, "FPw": fp, "FNw": fn,
            "K": k, "S": float(pred.sum()), "support_px": int(support.sum())}

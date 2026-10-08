"""Candidate fields and emission rules.

The metric's exact first-order condition (see :mod:`gems54.metric`) is that a unit of mass at x
pays iff ``dT > alpha*DTI`` -- for a dot sitting on a truth pixel (``kbar = 1``) any positive
newly-claimed credit pays, while a dot far from any truth pixel pays nothing and costs ``alpha``.
So the emission problem is a *coverage* problem: choose the dot set that maximises newly claimed
kernel credit per unit of wasted mass.
"""
from __future__ import annotations

import numpy as np
from scipy import ndimage

from . import metric as M


def distance_to(mask: np.ndarray) -> np.ndarray:
    """Euclidean distance in pixels to the nearest True cell of ``mask``."""
    return ndimage.distance_transform_edt(~mask.astype(bool))


def offset_band(mask: np.ndarray, offset_px: float, tol_px: float = 0.5) -> np.ndarray:
    """All cells whose distance to ``mask`` lies in ``[offset-tol, offset+tol]``."""
    d = distance_to(mask)
    return (np.abs(d - offset_px) <= tol_px)


def thin_along_trace(band: np.ndarray, spacing_px: int) -> np.ndarray:
    """Keep one dot every ~``spacing_px`` along each trace (raster-order thinning).

    Vectorised: walks the support in raster order and keeps a pixel only if no kept pixel lies
    within ``spacing_px``.  This reproduces the group's ``d = 2.8 px``-style dot-thinning sweeps.
    """
    if spacing_px <= 1:
        return band.copy()
    out = np.zeros_like(band, bool)
    ys, xs = np.nonzero(band)
    s = int(spacing_px)
    for y, x in zip(ys.tolist(), xs.tolist()):
        if out[max(0, y - s):y + s + 1, max(0, x - s):x + s + 1].any():
            continue
        out[y, x] = True
    return out


def greedy_max_coverage(field: np.ndarray, budget: int, exclude: np.ndarray | None = None,
                        min_sep_px: float = 0.0) -> np.ndarray:
    """Greedy (1-1/e)-optimal coverage packing of ``field`` under a dot budget.

    Gain of a dot = sum over kernel offsets of ``max(0, field(x')k - claimed(x'))``, i.e. the
    newly claimed expectation-weighted credit.  Dots are placed in descending field order, which
    is the submodular greedy order for this objective.
    """
    f = np.nan_to_num(field.astype(np.float32), nan=0.0)
    cand = f > 0
    if exclude is not None:
        cand &= ~exclude
    vals = np.where(cand, f, -1.0).ravel()
    order = np.argsort(-vals)
    h, w = f.shape
    offs = np.array([(dy, dx, k) for dy, dx, k in M._offsets(M.R_M, M.RES_M) if k > 0],
                    dtype=np.float64)
    dy = offs[:, 0].astype(int); dx = offs[:, 1].astype(int); kk = offs[:, 2]
    claimed = np.zeros_like(f)
    out = np.zeros_like(f, bool)
    used = np.zeros_like(f, bool)
    n = 0
    for idx in order:
        if n >= budget:
            break
        if vals[idx] < 0:
            break
        y, x = divmod(int(idx), w)
        if min_sep_px > 0 and used[max(0, y - int(min_sep_px)):y + int(min_sep_px) + 1,
                                   max(0, x - int(min_sep_px)):x + int(min_sep_px) + 1].any():
            continue
        yy = np.clip(y + dy, 0, h - 1); xx = np.clip(x + dx, 0, w - 1)
        free = f[yy, xx] * kk - claimed[yy, xx]
        if free.max() <= 0:
            continue
        gain = float(np.clip(free, 0, None).sum())
        if gain <= 0:
            continue
        out[y, x] = True; used[y, x] = True; n += 1
        np.maximum(claimed[yy, xx], f[yy, xx] * kk, out=claimed[yy, xx])
    return out

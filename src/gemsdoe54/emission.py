"""Metric-aware dot emission.

Why dots, and why the spacing matters
-------------------------------------

The organizer's metric (transcribed and verified in ``scripts/gems_metric.py``) is

    DTI = T / ( T + 0.2*FP_w + 0.8*FN_w )

with, for unit-valued ("dot") predictions,

    FP_w = N - M,     FN_w = G - T,     T = TP_w,     M = SUM_x max_g k(d(x,g))
    =>  DTI = T / ( 0.2*N + 0.8*G + 0.2*(T - M) )                       (exact)

where ``N`` is the number of predicted positive cells, ``G`` the number of true
cells and ``k`` the triangular kernel of 300 m support.

Three consequences drive every design choice in this repository:

1.  **Mass is taxed linearly.**  ``0.2*N`` sits in the denominator, so halving
    the dot count at constant credit is worth roughly +0.07 DTI at the operating
    point of the public leaderboard's 0.26-0.28 cluster.  This is corroborated by
    two public leaderboard observations on byte-identical families: deleting
    6,436 dots (44,090 -> 37,654, all within 200 m of the catalogue) moved a
    sibling artifact from an owner-quoted 0.2600 to 0.2778.

2.  **Credit is a per-truth-cell maximum, not a sum.**  Redundant predictions do
    not add credit but do add mass, so the credit-maximising density along a
    predicted trace is one dot per kernel width (300 m), not one dot per cell.

3.  **Far dots are pure loss.**  A dot more than 300 m from every true cell
    contributes ``max_g k = 0``, so it adds ``0.2`` to the denominator and
    nothing to the numerator.

``emit_spaced_dots`` implements rule 2 directly: a deterministic greedy that
keeps a candidate cell only if no already-kept cell lies within ``spacing_px``.
Candidates are visited in an evidence-priority order, so the retained dots are
the highest-ranked cells of each trace.
"""

from __future__ import annotations

import numpy as np

# Pre-computed offset table for an exact Euclidean spacing constraint.
def _offsets(radius_px: float) -> np.ndarray:
    r = int(np.ceil(radius_px))
    dy, dx = np.mgrid[-r : r + 1, -r : r + 1]
    keep = (dy * dy + dx * dx) <= radius_px * radius_px
    return np.column_stack([dy[keep], dx[keep]]).astype(np.int32)


def emit_spaced_dots(
    candidates: np.ndarray,
    *,
    priority: np.ndarray | None = None,
    spacing_px: float = 3.0,
    out: np.ndarray | None = None,
) -> np.ndarray:
    """Greedily thin ``candidates`` so that kept cells are >= ``spacing_px`` apart.

    Parameters
    ----------
    candidates
        Boolean mask of admissible cells (for example: state-map faults at least
        300 m from the competition catalogue).
    priority
        Float array of the same shape; larger values are visited first.  Defaults
        to a deterministic row-major order.  Ties are resolved by row-major order
        so the output is bit-reproducible.
    spacing_px
        Minimum Euclidean separation of kept cells, in pixels (100 m each).  The
        default of 3 px equals the metric's 300 m kernel support.
    out
        Optional preallocated boolean output array.

    Returns
    -------
    Boolean mask of emitted dots.
    """
    cand = np.asarray(candidates, dtype=bool)
    if cand.ndim != 2:
        raise ValueError("candidates must be a 2-D boolean mask")
    if spacing_px <= 0:
        raise ValueError("spacing_px must be positive")
    if priority is None:
        flat_order = np.flatnonzero(cand.ravel())
    else:
        prio = np.asarray(priority, dtype=np.float64)
        if prio.shape != cand.shape:
            raise ValueError("priority shape must match candidates")
        idx = np.flatnonzero(cand.ravel())
        # sort by (-priority, flat index) for a deterministic, reproducible order
        order = np.lexsort((idx, -prio.ravel()[idx]))
        flat_order = idx[order]

    # ``emitted`` holds the returned dots; ``occupied`` is the exclusion zone built
    # from the emitted dots.  They must be separate arrays: a cell inside a dot's
    # exclusion zone is *blocked*, not itself a dot.
    emitted = np.zeros(cand.shape, dtype=bool) if out is None else out
    emitted[:] = False
    occupied = np.zeros(cand.shape, dtype=bool)
    height, width = cand.shape
    offs = _offsets(spacing_px)
    for flat in flat_order:
        y, x = divmod(int(flat), width)
        if occupied[y, x]:
            continue
        emitted[y, x] = True
        yy = y + offs[:, 0]
        xx = x + offs[:, 1]
        ok = (yy >= 0) & (yy < height) & (xx >= 0) & (xx < width)
        occupied[yy[ok], xx[ok]] = True
    return emitted


def dot_count(dots: np.ndarray) -> int:
    return int(np.count_nonzero(dots))


def trim_to_budget(dots: np.ndarray, priority: np.ndarray | None,
                   budget: int) -> np.ndarray:
    """Keep the top-``budget`` dots by placement priority (spacing preserved).

    A subset of a valid spaced packing is still a valid spaced packing, so this
    only removes the lowest-priority retained dots.  Ties break on row-major
    order so the result is bit-reproducible.  Used to match mass between
    compared arms so a contrast can never be won by emitting more pixels.
    """
    dots = np.asarray(dots, dtype=bool)
    n = int(dots.sum())
    if budget >= n:
        return dots.copy()
    ys, xs = np.nonzero(dots)
    flat = ys * dots.shape[1] + xs
    if priority is None:
        order = np.argsort(flat, kind="stable")
    else:
        prio = np.asarray(priority, dtype=np.float64).ravel()
        order = np.lexsort((flat, -prio[flat]))
    keep = np.zeros(dots.shape, dtype=bool)
    keep[ys[order[:budget]], xs[order[:budget]]] = True
    return keep

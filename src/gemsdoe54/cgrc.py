"""H54-C: Catalogue Gap Relay Completion (CGRC).

Lane statement (single method paragraph)
----------------------------------------
The competition catalogue is a *fragmented* digitisation: 3,199 connected
components with a median of 12 cells and 6,747 degree-1 tips on a 100 m grid.
En-echelon fault arrays and relay/stepover geometries are the canonical
reason a compilation misses a strand: the short segment that links two
mapped, roughly parallel, facing tips is exactly the kind of low-displacement
trace that drops out of a national compilation while remaining on state
geologic maps. CGRC therefore predicts only the *gap* cells: straight relay
lines between catalogue tips of different components whose strikes agree,
whose tips face each other along the shared strike, whose stepover offset is
small, and whose gap is empty of catalogue cells, plus tip tangent
continuations. The USGS SGMC raster (an independently compiled product) is
used *only* as a corroboration weight on which relay lines to keep and how to
prioritise dot placement along them — it is never used as a placement surface.
Dots are emitted by metric-optimal greedy packing (one dot per 300 m kernel
width) with the break-even credit bar ``k > 0.2*DTI``.  This differs from
every registry lane: dotted families emit on SGMC traces off the catalogue;
tip-stepover/continuation lanes emit only tangent extensions; lattices are
uniform. CGRC emits on catalogue-tip-to-catalogue-tip gap geometry.

Geometry definitions
--------------------
* segment     : connected component of the (visible) catalogue mask, >= MIN_PX cells
* tip         : degree-1 cell of a segment (exactly one 8-neighbour)
* strike      : principal axis (PCA) unit vector of a segment, undirected
* relay pair  : tips (t1, A), (t2, B), A != B, with
    - 100 m <= |t1 t2| <= MAX_GAP_M (1500 m)
    - |angle(t1t2, shared strike)| <= MAX_ALONG (25 deg)
    - perpendicular offset of t1t2 w.r.t. shared strike <= MAX_OFFSET_M (500 m)
    - no catalogue cell on the open segment (the gap is empty)
* relay line  : the straight segment t1 -> t2; candidate cells are its
    SCAFFOLD_PX (2) px Euclidean buffer so that metric-optimal dots may sit
    off-centre (hidden faults are observed to scatter ~185 m around mapped
    traces; GEMSDOE25/H28 inference, owner-report-derived).
* continuation: each segment end extended along its local tangent for at most
    MAX_EXT_M (1500 m), same candidate scaffolding.

All cells within EXCLUDE_CAT_M (200 m) of the (visible) catalogue are removed
from the candidate set: the 0.2600 -> 0.2778 prune of the dotted family
removed precisely this mass (owner-recorded board observations; see
docs/research/why-h33.md) and the break-even bar does not clear it.

Memory note: the grid is 3730x3292 (12.28 M cells).  Per-line full-raster
masks are never stored in lists; lines are rasterised into a single
accumulator (one 12 MB boolean) or checked transiently and discarded.
"""

from __future__ import annotations

import numpy as np
from scipy.ndimage import distance_transform_edt, label

MIN_PX = 3                 # smallest segment (cells)
MAX_GAP_M = 1500.0         # max tip-to-tip relay gap (m)
MAX_ALONG_DEG = 25.0       # max angular deviation of tip-to-tip line from shared strike
MAX_OFFSET_M = 500.0       # max lateral stepover offset (m)
MAX_EXT_M = 1500.0         # max tangent continuation length (m)
EXCLUDE_CAT_M = 200.0      # catalogue exclusion zone for candidate cells (m)
SCAFFOLD_PX = 2            # candidate buffer around relay/continuation lines (px)


def _neighbour_count(mask: np.ndarray) -> np.ndarray:
    n = np.zeros(mask.shape, dtype=np.int32)
    for dy in (-1, 0, 1):
        for dx in (-1, 0, 1):
            if dy == 0 and dx == 0:
                continue
            n += np.roll(np.roll(mask.astype(np.int32), dy, axis=0), dx, axis=1)
    return n


def segment_stats(catalogue: np.ndarray) -> dict:
    """Per-segment strike, extremes and tips for components >= MIN_PX cells."""
    lab, ncomp = label(catalogue, structure=np.ones((3, 3), dtype=int))
    ne = _neighbour_count(catalogue)
    ys, xs = np.nonzero(catalogue)
    lids = lab[ys, xs]
    my = ys.astype(np.float64)
    mx = xs.astype(np.float64)
    cnt = np.bincount(lids, minlength=ncomp + 1)
    seg: dict = {}
    for a in range(1, ncomp + 1):
        if cnt[a] < MIN_PX:
            continue
        sel = lids == a
        yy, xx = my[sel], mx[sel]
        c = np.array([yy.mean(), xx.mean()])
        centered = np.column_stack([yy - c[0], xx - c[1]])
        cov = centered.T @ centered
        evals, evecs = np.linalg.eigh(cov)
        strike = evecs[:, np.argmax(evals)]
        strike = strike / np.hypot(*strike)
        proj = centered @ strike
        p0, p1 = int(np.argmin(proj)), int(np.argmax(proj))
        e0 = (int(yy[p0]), int(xx[p0]))
        e1 = (int(yy[p1]), int(xx[p1]))
        tips = [(int(y), int(x)) for y, x, k in
                zip(ys[sel], xs[sel], ne[ys[sel], xs[sel]]) if k == 1]
        seg[a] = {"size": int(cnt[a]), "strike": strike, "ends": (e0, e1), "tips": tips}
    return {"segments": seg, "n_kept": len(seg)}


def _line_cells(a: tuple[int, int], b: tuple[int, int], shape: tuple[int, int]) -> tuple[np.ndarray, np.ndarray]:
    """Cells along a -> b (Bresenham by linear sampling), clipped to the grid."""
    y0, x0 = a
    y1, x1 = b
    steps = max(abs(y1 - y0), abs(x1 - x0), 1)
    t = np.linspace(0.0, 1.0, steps * 2 + 1)
    pts = np.column_stack([
        np.round(y0 + (y1 - y0) * t).astype(np.int64),
        np.round(x0 + (x1 - x0) * t).astype(np.int64),
    ])
    pts = np.unique(pts, axis=0)
    return pts[:, 0], pts[:, 1]


def _gap_is_empty(shape: tuple[int, int], catalogue: np.ndarray,
                  a: tuple[int, int], b: tuple[int, int]) -> bool:
    yy, xx = _line_cells(a, b, shape)
    body = np.ones(yy.shape, dtype=bool)
    if (yy[0], xx[0]) == a:
        body[0] = False
    if (yy[-1], xx[-1]) == b:
        body[-1] = False
    return not bool((catalogue[yy[body], xx[body]]).any())


def relay_pairs(stats: dict, catalogue: np.ndarray,
                max_gap_m: float = MAX_GAP_M,
                max_along_deg: float = MAX_ALONG_DEG,
                max_offset_m: float = MAX_OFFSET_M) -> list[dict]:
    """Find catalogue tip pairs that form empty, strike-compatible relay gaps.

    Returns lightweight geometry dicts (no per-line rasters) so the list stays
    small; lines are rasterised later into a single accumulator.
    """
    segs = stats["segments"]
    tips: list[tuple[tuple[int, int], int, np.ndarray]] = []
    for a, s in segs.items():
        for t in s["tips"]:
            tips.append((t, a, s["strike"]))
    cell = 10  # 1000 m bins
    grid: dict[tuple[int, int], list[int]] = {}
    for i, (t, a, st) in enumerate(tips):
        grid.setdefault((t[0] // cell, t[1] // cell), []).append(i)
    cos_along = np.cos(np.deg2rad(max_along_deg))
    shape = catalogue.shape
    pairs: list[dict] = []
    for i in range(len(tips)):
        t1, a1, s1 = tips[i]
        for ky in range(t1[0] // cell - 2, t1[0] // cell + 3):
            for kx in range(t1[1] // cell - 2, t1[1] // cell + 3):
                for j in grid.get((ky, kx), ()):
                    if j <= i:
                        continue
                    t2, a2, s2 = tips[j]
                    if a1 == a2:
                        continue
                    dy, dx = t2[0] - t1[0], t2[1] - t1[1]
                    gap_m = np.hypot(dy, dx) * 100.0
                    if not (100.0 <= gap_m <= max_gap_m):
                        continue
                    dvec = np.array([dy, dx]) / (gap_m / 100.0)
                    shared = s1 if abs(float(np.dot(s1, s2))) >= abs(float(np.dot(s1, -s2))) else s2
                    shared = np.where(shared[1] < 0, -shared, shared)
                    along = abs(float(np.dot(dvec, shared)))
                    if along < cos_along:
                        continue
                    perp = abs(float(np.dot(dvec, np.array([-shared[1], shared[0]])))) * gap_m
                    if perp > max_offset_m:
                        continue
                    if not _gap_is_empty(shape, catalogue, t1, t2):
                        continue
                    pairs.append({
                        "t1": t1, "t2": t2, "seg_a": a1, "seg_b": a2,
                        "gap_m": float(gap_m), "along": float(along), "offset_m": float(perp),
                        "quality": float(along) * (1.0 - perp / (2.0 * max_offset_m)),
                    })
    return pairs


def continuation_lines(stats: dict, catalogue: np.ndarray,
                       max_ext_m: float = MAX_EXT_M) -> list[dict]:
    """Tangent extensions of every segment end (both PCA extremes). Lightweight."""
    lines = []
    h, w = catalogue.shape
    npx = int(round(max_ext_m / 100.0))
    for a, s in stats["segments"].items():
        (y0, x0), (y1, x1) = s["ends"]
        strike = s["strike"]
        for (y, x), other in (((y0, x0), (y1, x1)), ((y1, x1), (y0, x0))):
            # The vector from the OTHER extreme to THIS end already points
            # outward (away from the segment interior) at this end, so use it
            # as-is as the tangent direction. Do NOT realign it to the PCA
            # strike sign: the strike is undirected and its eigenvector sign is
            # arbitrary, so re-aligning both ends to the same sign would extend
            # both ends in one direction and drop the outward extension at the
            # other end (IR-54-021).
            outdir = np.array([y - other[0], x - other[1]], dtype=np.float64)
            norm = np.hypot(*outdir)
            outdir = outdir / norm if norm > 0 else strike
            ey = int(np.clip(round(y + outdir[0] * npx), 0, h - 1))
            ex = int(np.clip(round(x + outdir[1] * npx), 0, w - 1))
            lines.append({"t1": (y, x), "t2": (ey, ex), "seg": a})
    return lines


def rasterize_lines(shape: tuple[int, int], lines: list[dict]) -> np.ndarray:
    """Rasterise many lightweight line dicts into ONE boolean accumulator."""
    out = np.zeros(shape, dtype=bool)
    for p in lines:
        yy, xx = _line_cells(p["t1"], p["t2"], shape)
        out[yy, xx] = True
    return out


def build(shape: tuple[int, int],
          catalogue: np.ndarray,
          sgmc: np.ndarray,
          footprint: np.ndarray,
          *,
          with_sgmc: bool = True,
          exclude_cat_m: float = EXCLUDE_CAT_M,
          max_gap_m: float = MAX_GAP_M,
          max_ext_m: float = MAX_EXT_M) -> dict:
    """Full CGRC surface construction for one (visible) catalogue mask.

    Returns the relay/continuation geometry plus the candidate mask and the
    placement priority field (line Gaussian x optional SGMC corroboration).
    ``exclude_cat_m`` is the catalogue exclusion zone for candidate cells
    (200 m is the dotted-family prune threshold; 300 m is the full metric
    kernel width and the configuration verified lane-clean against every
    non-vacuous registry raster).
    Memory: at most ~4 full-size arrays live at once.
    """
    stats = segment_stats(catalogue)
    relay = relay_pairs(stats, catalogue, max_gap_m=max_gap_m)
    # one relay per tip: keep the highest-quality pair per tip
    best: dict[tuple[int, int], dict] = {}
    for p in sorted(relay, key=lambda q: -q["quality"]):
        if p["t1"] in best or p["t2"] in best:
            continue
        best[p["t1"]] = p
        best[p["t2"]] = p
    seen: set[tuple] = set()
    relay = []
    for p in best.values():
        key = (p["t1"], p["t2"], p["seg_a"], p["seg_b"])
        if key in seen:
            continue
        seen.add(key)
        relay.append(p)
    relay.sort(key=lambda q: (q["t1"][0], q["t1"][1], q["t2"][0], q["t2"][1]))
    cont = continuation_lines(stats, catalogue, max_ext_m=max_ext_m)
    relay_centre = rasterize_lines(shape, relay)
    cont_centre = rasterize_lines(shape, cont)
    centre = relay_centre | cont_centre
    relay_centre = None
    cont_centre = None
    d = distance_transform_edt(~centre)
    surf = d <= float(SCAFFOLD_PX - 1)
    del d
    dcat = distance_transform_edt(~catalogue, sampling=(100.0, 100.0))
    surf = surf & (dcat >= exclude_cat_m)
    del dcat
    surf &= footprint
    # priority: Gaussian decay from the centreline (off-centre scatter, sigma 1.85 px)
    d = distance_transform_edt(~centre)
    w_line = np.exp(-0.5 * (d / 1.85) ** 2)
    del d, centre
    priority = w_line.copy()
    if with_sgmc:
        w_sg = _sgmc_weight(sgmc)
        # corroboration: 0.5 baseline so uncorroborated lines still rank, x2 where SGMC agrees
        priority = priority * (0.5 + w_sg)
        del w_sg
    priority[~surf] = 0.0
    del w_line
    return {
        "n_segments": len(stats["segments"]),
        "n_relays": len(relay),
        "n_continuations": len(cont),
        "surface_cells": int(surf.sum()),
        "candidates": surf,
        "priority": priority,
        "relay": relay,
        "cont": cont,
    }


def _sgmc_weight(sgmc: np.ndarray) -> np.ndarray:
    """Triangular-kernel proximity of every cell to the SGMC fault raster."""
    if not sgmc.any():
        return np.zeros(sgmc.shape)
    d = distance_transform_edt(~sgmc, sampling=(100.0, 100.0))
    return np.maximum(1.0 - d / 300.0, 0.0)

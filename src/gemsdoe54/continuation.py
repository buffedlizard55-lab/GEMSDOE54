"""End-of-trace continuation hypothesis for concealed fault segments.

This is a deliberately small, auditable geometry transform over visible catalogue
faults. It is not a trained model and should be treated as an exploratory feature.
"""
from __future__ import annotations

import numpy as np
from scipy.ndimage import label


def endpoint_continuation_surface(
    visible_faults: np.ndarray,
    footprint: np.ndarray,
    *,
    min_component_cells: int = 8,
    min_elongation: float = 8.0,
    local_tail_fraction: float = 0.2,
    max_extension_px: float = 15.0,
    start_extension_px: float = 3.25,
) -> np.ndarray:
    """Project short, straight extensions from visible fault-trace endpoints.

    For each 8-connected trace component, PCA gives an orientation and the
    extreme projected cells define the two ends. A local PCA over the outer
    ``local_tail_fraction`` of the component estimates the tangent at each end;
    only linearly elongated components are used. Candidate traces begin beyond
    ``start_extension_px`` (normally just beyond the 300 m catalogue exclusion)
    and stop at ``max_extension_px``. Scores decay linearly with extension
    distance. The returned surface is finite float32 in [0, 1].

    This transform does not use the held-out mask or held-out labels. Callers must
    pass only visible faults when running hide-and-recover evaluation.
    """
    faults = np.asarray(visible_faults, dtype=bool)
    foot = np.asarray(footprint, dtype=bool)
    if faults.ndim != 2 or foot.shape != faults.shape:
        raise ValueError("visible_faults and footprint must be same-shape 2-D arrays")
    if not (0.0 < local_tail_fraction <= 1.0):
        raise ValueError("local_tail_fraction must be in (0, 1]")
    if min_component_cells < 2 or min_elongation <= 1:
        raise ValueError("component size must be >=2 and elongation must exceed 1")
    if not (0 <= start_extension_px < max_extension_px):
        raise ValueError("extension distances must satisfy 0 <= start < max")

    lab, ncomp = label(faults, structure=np.ones((3, 3), dtype=np.uint8))
    out = np.zeros(faults.shape, dtype=np.float32)
    if ncomp == 0:
        return out

    ys, xs = np.nonzero(faults)
    ids = lab[ys, xs]
    counts = np.bincount(ids, minlength=ncomp + 1)
    # Group component coordinates once so each component is processed without
    # rescanning the full raster (the production grid has millions of cells).
    order = np.argsort(ids, kind="stable")
    ys, xs, ids = ys[order], xs[order], ids[order]
    starts = np.cumsum(np.r_[0, counts[1:-1]])

    step = 0.5
    distances = np.arange(start_extension_px, max_extension_px + step / 2.0, step)
    for component_id in range(1, ncomp + 1):
        count = int(counts[component_id])
        if count < min_component_cells:
            continue
        begin = int(starts[component_id - 1])
        coords = np.column_stack((ys[begin:begin + count], xs[begin:begin + count])).astype(np.float64)
        center = coords.mean(axis=0)
        centered = coords - center
        cov = centered.T @ centered / max(count, 1)
        vals, vecs = np.linalg.eigh(cov)
        if vals[-1] <= 0 or vals[-1] / max(vals[0], 1e-9) < min_elongation:
            continue
        major = vecs[:, -1]
        projection = centered @ major
        threshold = max(float(np.ptp(projection)) * local_tail_fraction, 1.0)

        for high_end in (False, True):
            extreme = float(projection.max() if high_end else projection.min())
            tail = projection >= extreme - threshold if high_end else projection <= extreme + threshold
            local = coords[tail]
            if len(local) < 2:
                local = coords[np.argsort(projection)[-min(count, 3):] if high_end
                               else np.argsort(projection)[:min(count, 3)]]
            local_center = local.mean(axis=0)
            local_cov = (local - local_center).T @ (local - local_center) / max(len(local), 1)
            local_vals, local_vecs = np.linalg.eigh(local_cov)
            tangent = local_vecs[:, -1]
            # Orient the local tangent away from the component interior.
            sign = 1.0 if high_end else -1.0
            if float(np.dot(tangent, major)) * sign < 0:
                tangent = -tangent
            endpoint = coords[int(np.argmax(projection) if high_end else np.argmin(projection))]
            quality = float(np.clip((vals[-1] / max(vals[0], 1e-9) - 1.0) / 15.0, 0.25, 1.0))
            for distance in distances:
                point = endpoint + tangent * distance
                row, col = np.rint(point).astype(int)
                if row < 0 or row >= faults.shape[0] or col < 0 or col >= faults.shape[1]:
                    continue
                if not foot[row, col] or faults[row, col]:
                    continue
                value = quality * (1.0 - 0.5 * (distance - start_extension_px) /
                                   (max_extension_px - start_extension_px))
                if value > out[row, col]:
                    out[row, col] = np.float32(value)
    return out

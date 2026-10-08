"""Catalogue-free magnetic edge ridges for the GEMS fault task.

Physical signature
------------------
A steeply dipping fault or fault-controlled contact commonly produces a lineament of
strong horizontal magnetic gradient (the "edge" of a magnetic step).  The ridge of the
total horizontal gradient (THD), located with a non-maximum suppression (NMS) across the
edge, traces that lineament at 100 m resolution.

Inputs (official competition feature stack, ``training_features.tif``)
-----------------------------------------------------------------------
* band 2 ``rtp``      reduced-to-pole magnetic anomaly, used only for the edge *direction*
* band 3 ``tmi_hg``   total magnetic intensity horizontal gradient, used for the edge *strength*

Neither band depends on the fault catalogue, so the ridge set is catalogue-free.  The
catalogue enters only through :func:`gate_by_visible`, which removes ridge cells within
300 m of a catalogue fault that is *visible* to the caller.  In a hide-and-recover
holdout the visible set excludes the withheld segments and their buffer, so a withheld
fault's ridge survives the gate and can be scored; in the final submission the full
catalogue is visible, so only new (non-catalogued) ridges remain.

Known non-fault mimics: lithologic contacts (volcanic flows, intrusions, basement
steps), cultural magnetic noise (fences, rails, power lines, buildings), topographic
edge effects, and flight-line / levelling artifacts in the magnetic survey.
"""

from __future__ import annotations

import numpy as np
from scipy.ndimage import distance_transform_edt, gaussian_filter, label

SENTINEL_FLOAT32 = float(np.float32(-3.4028234663852886e38))
PIXEL_M = 100.0
KEEP_BEYOND_M = 300.0  # ridge cells must be farther than this from a visible catalogue cell


def invalid_feature_mask(*bands: np.ndarray) -> np.ndarray:
    """True where any of the bands is non-finite or equals the float32 nodata sentinel."""
    bad = np.zeros(bands[0].shape, dtype=bool)
    for b in bands:
        bad |= ~np.isfinite(b) | (b == np.float32(SENTINEL_FLOAT32))
    return bad


def ridge_candidate(
    rtp: np.ndarray,
    thd: np.ndarray,
    valid: np.ndarray,
    *,
    sigma_px: float = 1.0,
    quantile: float = 0.98,
    min_len_px: int = 8,
    invalid_buffer_px: int = 2,
) -> np.ndarray:
    """Catalogue-free ridge cells of the magnetic total-horizontal-gradient edge.

    Steps (all parameters are fixed in ``evidence/preregistration_mag_ridge.json``):
      1. fill invalid cells with the valid median, Gaussian-smooth both bands (sigma 1 px);
      2. take the RTP gradient direction n = grad/|grad|;
      3. keep cells whose smoothed THD is a local maximum across the edge, i.e.
         THD >= THD(x + n) and THD >= THD(x - n) (nearest-neighbour sampling);
      4. keep those in the top ``1 - quantile`` fraction of valid THD;
      5. drop cells within ``invalid_buffer_px`` of invalid feature cells;
      6. keep 8-connected ridge components of at least ``min_len_px`` cells.
    """
    rtp = np.asarray(rtp, dtype=np.float64)
    thd = np.asarray(thd, dtype=np.float64)
    valid = np.asarray(valid, dtype=bool)
    if rtp.shape != thd.shape or rtp.shape != valid.shape:
        raise ValueError("rtp, thd and valid must share one shape")
    if not valid.any():
        raise ValueError("no valid cells")

    from scipy.ndimage import binary_dilation

    edge_guard = binary_dilation(~valid, iterations=invalid_buffer_px) if invalid_buffer_px > 0 else ~valid
    rtp_f = np.where(valid, rtp, np.median(rtp[valid]))
    thd_f = np.where(valid, thd, 0.0)
    rtp_s = gaussian_filter(rtp_f, sigma_px)
    thd_s = gaussian_filter(thd_f, sigma_px)

    gy, gx = np.gradient(rtp_s, PIXEL_M, PIXEL_M)
    mag = np.hypot(gx, gy) + 1e-12
    ny, nx = gy / mag, gx / mag

    rows, cols = np.indices(thd_s.shape)

    def sample(dy: np.ndarray, dx: np.ndarray) -> np.ndarray:
        rr = np.clip(np.rint(rows + dy).astype(np.int64), 0, thd_s.shape[0] - 1)
        cc = np.clip(np.rint(cols + dx).astype(np.int64), 0, thd_s.shape[1] - 1)
        return thd_s[rr, cc]

    # One-sided strict NMS: a plateau of tied values (e.g. a flat background) is not a
    # ridge, and a strictly positive edge strength is required.
    nms = (thd_s >= sample(ny, nx)) & (thd_s > sample(-ny, -nx)) & (thd_s > 0.0)
    thr = float(np.quantile(thd_s[valid], quantile))
    ridge = nms & (thd_s >= thr) & valid & ~edge_guard

    lab, n = label(ridge, structure=np.ones((3, 3), dtype=int))
    if n == 0:
        return np.zeros(ridge.shape, dtype=bool)
    sizes = np.bincount(lab.ravel())
    keep_ids = np.flatnonzero(sizes >= min_len_px)
    keep_ids = keep_ids[keep_ids > 0]
    return np.isin(lab, keep_ids)


def gate_by_visible(ridge: np.ndarray, visible_catalogue: np.ndarray,
                    keep_beyond_m: float = KEEP_BEYOND_M) -> np.ndarray:
    """Keep ridge cells farther than ``keep_beyond_m`` from every visible catalogue cell."""
    ridge = np.asarray(ridge, dtype=bool)
    vis = np.asarray(visible_catalogue, dtype=bool)
    if not vis.any():
        return ridge.copy()
    d = distance_transform_edt(~vis, sampling=PIXEL_M)
    return ridge & (d > keep_beyond_m)


__all__ = [
    "SENTINEL_FLOAT32",
    "invalid_feature_mask",
    "ridge_candidate",
    "gate_by_visible",
]

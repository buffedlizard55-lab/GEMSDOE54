"""Catalogue-free candidate fields for the parallel-run holdout (evaluator ``gemsdoe54-segment-cv`` v2).

Every function here reads only the owner-bridge feature bands (``training_features.tif``,
SHA-256 pinned in ``scripts/holdout_segment_cv.py``). The fault catalogue never enters a
feature. It enters only through the *visible* mask that the caller passes to the learned
model, and in the hide-and-recover holdout that mask already excludes the withheld segments
and their 300 m collar.

Candidates
----------
H1  ``cross_gradient_score``  geometric mean of within-footprint percentiles of the magnetic
    total-horizontal-gradient (``tmi_hg``) and the isostatic-gravity horizontal gradient
    (``iso_grav_anom_hg``). High only where two independent potential-field families both show
    an edge (density *and* magnetisation contrast).
H2  ``basement_step_score``   gradient magnitude of the depth-to-basement surface
    (``depth_to_base_surf``), a basin-margin step that a buried normal fault can produce.
H3  ``learned_visible_probability``  histogram gradient-boosted classifier trained per fold on
    the visible catalogue (positives) against footprint cells that are neither visible nor in
    the collar (negatives). Withheld faults are *not* excluded from the negatives, which mirrors
    a real competition where unknown faults are unlabelled background. Inputs are the 19 bands
    plus gradient magnitudes of five geophysical bands. No distance-to-catalogue feature is used.

Known non-fault mimics (recorded in the run card): lithologic contacts and basin margins for
H1 and H2; any cell whose potential-field edges arise from surveys seams or cultural sources.
"""

from __future__ import annotations

import numpy as np
from scipy.ndimage import gaussian_filter

PIXEL_M = 100.0
GRAD_BANDS = ("rtp", "tmi_hg", "iso_grav_anom", "depth_to_base_surf", "cond_surf")
MODEL_PARAMS = {
    "max_iter": 200,
    "learning_rate": 0.1,
    "max_leaf_nodes": 31,
    "min_samples_leaf": 100,
    "l2_regularization": 1.0,
    "class_weight": "balanced",
}
N_POS_TRAIN = 40_000
N_NEG_TRAIN = 160_000


def gradient_magnitude(band: np.ndarray, valid: np.ndarray, sigma_px: float = 1.0) -> np.ndarray:
    """|grad| per 100 m cell of a band, NaN outside ``valid``.

    Invalid cells are filled with the valid median before smoothing so that the nodata
    sentinel cannot create a fake edge at the footprint boundary.
    """
    band = np.asarray(band)
    valid = np.asarray(valid, dtype=bool)
    if not valid.any():
        raise ValueError("no valid cells")
    filled = np.where(valid, band, np.float32(np.median(band[valid]))).astype(np.float64)
    if sigma_px > 0:
        filled = gaussian_filter(filled, sigma_px)
    gy, gx = np.gradient(filled, PIXEL_M, PIXEL_M)
    out = np.hypot(gx, gy).astype(np.float32)
    out[~valid] = np.nan
    return out


def within_footprint_percentile(feat: np.ndarray, valid: np.ndarray) -> np.ndarray:
    """Empirical CDF of ``feat`` over the valid cells, in (0, 1]; NaN outside ``valid``."""
    feat = np.asarray(feat)
    valid = np.asarray(valid, dtype=bool)
    out = np.full(feat.shape, np.nan, dtype=np.float32)
    vals = feat[valid]
    order = np.argsort(vals, kind="mergesort")
    ranks = np.empty(vals.size, dtype=np.float64)
    ranks[order] = (np.arange(vals.size) + 1) / vals.size
    out[valid] = ranks
    return out


def cross_gradient_score(tmi_hg: np.ndarray, iso_grav_anom_hg: np.ndarray, valid: np.ndarray) -> np.ndarray:
    """H1: geometric mean of two independent horizontal-gradient percentiles (both must be high)."""
    valid = np.asarray(valid, dtype=bool) & np.isfinite(tmi_hg) & np.isfinite(iso_grav_anom_hg)
    a = within_footprint_percentile(tmi_hg, valid)
    b = within_footprint_percentile(iso_grav_anom_hg, valid)
    score = np.sqrt(a.astype(np.float64) * b.astype(np.float64)).astype(np.float32)
    score[~valid] = np.nan
    return score


def basement_step_score(depth_to_base: np.ndarray, valid: np.ndarray) -> np.ndarray:
    """H2: |grad| of the depth-to-basement surface, smoothed at 1 px."""
    valid = np.asarray(valid, dtype=bool) & np.isfinite(depth_to_base)
    return gradient_magnitude(depth_to_base, valid, sigma_px=1.0)


def fit_visible_classifier(X: np.ndarray, y: np.ndarray, seed: int):
    """Fit the H3 classifier. scikit-learn is imported lazily so the rest of the package does not need it."""
    from sklearn.ensemble import HistGradientBoostingClassifier

    clf = HistGradientBoostingClassifier(random_state=seed, **MODEL_PARAMS)
    clf.fit(X, y)
    return clf


def learned_visible_probability(
    F: np.ndarray,
    visible_rows: np.ndarray,
    excluded_rows: np.ndarray,
    predict_rows: np.ndarray,
    seed: int,
    n_pos: int = N_POS_TRAIN,
    n_neg: int = N_NEG_TRAIN,
) -> tuple[np.ndarray, dict]:
    """H3: per-fold probability for the footprint rows in ``predict_rows``.

    ``F`` is the footprint-row feature matrix (rows x features, float32, NaN allowed).
    ``visible_rows`` marks positives (visible catalogue). Negatives are drawn from every row that
    is neither visible nor in ``excluded_rows`` (the collar), so withheld faults can appear as
    unlabelled negatives, as they would in the real competition.
    Returns (probability per predict row, diagnostics).
    """
    rng = np.random.default_rng(seed)
    pos_all = np.flatnonzero(visible_rows)
    neg_all = np.flatnonzero(~visible_rows & ~excluded_rows)
    if pos_all.size == 0 or neg_all.size == 0:
        raise ValueError("degenerate training set")
    pos = rng.choice(pos_all, size=min(n_pos, pos_all.size), replace=False)
    neg = rng.choice(neg_all, size=min(n_neg, neg_all.size), replace=False)
    X = np.vstack([F[pos], F[neg]]).astype(np.float32)
    y = np.concatenate([np.ones(pos.size), np.zeros(neg.size)])
    clf = fit_visible_classifier(X, y, seed)
    out = np.empty(predict_rows.size, dtype=np.float32)
    chunk = 1_000_000
    for start in range(0, predict_rows.size, chunk):
        sl = slice(start, min(start + chunk, predict_rows.size))
        out[sl] = clf.predict_proba(F[predict_rows[sl]])[:, 1]
    diag = {
        "n_train_pos": int(pos.size),
        "n_train_neg": int(neg.size),
        "n_features": int(F.shape[1]),
        "n_predict": int(predict_rows.size),
        "model": "HistGradientBoostingClassifier",
        "params": MODEL_PARAMS,
        "seed": int(seed),
    }
    return out, diag


__all__ = [
    "GRAD_BANDS",
    "MODEL_PARAMS",
    "gradient_magnitude",
    "within_footprint_percentile",
    "cross_gradient_score",
    "basement_step_score",
    "fit_visible_classifier",
    "learned_visible_probability",
]

"""Fast synthetic tests for the catalogue-free candidate builders (src/gemsdoe54/hypotheses.py)."""

from __future__ import annotations

import numpy as np
import pytest

from gemsdoe54.hypotheses import (
    basement_step_score,
    cross_gradient_score,
    gradient_magnitude,
    learned_visible_probability,
    within_footprint_percentile,
)


def _step(h: int = 60, w: int = 80) -> np.ndarray:
    band = np.zeros((h, w), dtype=np.float32)
    band[:, w // 2:] = 10.0
    return band


def test_gradient_magnitude_peaks_on_a_step_and_is_nan_outside_valid():
    band = _step()
    valid = np.ones(band.shape, dtype=bool)
    valid[:5, :] = False
    g = gradient_magnitude(band, valid, sigma_px=0.0)
    assert np.isnan(g[0, 0])
    interior = g[10:-10, 10:-10]
    peak_col = np.nanargmax(np.nanmean(interior, axis=0)) + 10
    assert abs(peak_col - band.shape[1] // 2) <= 2


def test_gradient_magnitude_rejects_empty_mask():
    with pytest.raises(ValueError):
        gradient_magnitude(_step(), np.zeros((60, 80), dtype=bool))


def test_within_footprint_percentile_is_monotone_and_reaches_one():
    rng = np.random.default_rng(0)
    feat = rng.normal(size=(20, 30)).astype(np.float32)
    valid = np.ones_like(feat, dtype=bool)
    valid[0, :] = False
    pct = within_footprint_percentile(feat, valid)
    assert np.isnan(pct[0, 0])
    v = pct[valid]
    assert v.max() == pytest.approx(1.0)
    order = np.argsort(feat[valid], kind="mergesort")
    assert np.all(np.diff(v[order]) >= 0)


def test_cross_gradient_requires_both_families_to_be_high():
    h, w = 40, 40
    a = np.zeros((h, w), dtype=np.float32)
    b = np.zeros((h, w), dtype=np.float32)
    a[:, 10] = 5.0          # magnetic edge only
    b[20, :] = 5.0          # gravity edge only
    a[:, 30] = 5.0
    b[:, 30] = 5.0          # co-located edge
    valid = np.ones((h, w), dtype=bool)
    s = cross_gradient_score(a, b, valid)
    assert np.isfinite(s).all()
    assert s[:, 30].mean() > s[:, 10].mean()
    assert s[:, 30].mean() > s[20, :].mean()
    assert float(np.nanmax(s)) <= 1.0 + 1e-6


def test_cross_gradient_is_nan_where_either_band_is_nonfinite():
    a = np.ones((10, 10), dtype=np.float32)
    b = np.ones((10, 10), dtype=np.float32)
    b[3, 3] = np.nan
    s = cross_gradient_score(a, b, np.ones((10, 10), dtype=bool))
    assert np.isnan(s[3, 3])


def test_basement_step_score_is_high_at_the_step():
    band = _step()
    s = basement_step_score(band, np.ones(band.shape, dtype=bool))
    col = np.nanmean(s[10:-10, :], axis=0)
    assert abs(int(np.nanargmax(col)) - band.shape[1] // 2) <= 2


def test_learned_probability_separates_a_planted_signal_and_respects_collar():
    """Visible faults 0..999 and withheld faults 1000..1999 share a feature signature; collar 2000..2199."""
    rng = np.random.default_rng(1)
    n = 20_000
    F = rng.normal(size=(n, 4)).astype(np.float32)
    visible = np.zeros(n, dtype=bool)
    visible[:1000] = True
    withheld = np.zeros(n, dtype=bool)
    withheld[1000:2000] = True
    F[visible | withheld, 0] += 2.5
    collar = np.zeros(n, dtype=bool)
    collar[2000:2200] = True
    predict = np.flatnonzero(~visible & ~collar)
    p, diag = learned_visible_probability(
        F, visible, collar, predict, seed=3, n_pos=1000, n_neg=5000)
    assert p.shape == predict.shape
    assert np.isfinite(p).all()
    from sklearn.metrics import roc_auc_score
    y = withheld[predict]
    assert y.any() and (~y).any()
    assert roc_auc_score(y, p) > 0.85
    assert diag["n_train_pos"] == 1000
    assert diag["model"] == "HistGradientBoostingClassifier"


def test_learned_probability_rejects_degenerate_training():
    F = np.zeros((10, 2), dtype=np.float32)
    with pytest.raises(ValueError):
        learned_visible_probability(
            F, np.zeros(10, dtype=bool), np.zeros(10, dtype=bool), np.arange(10), seed=0)

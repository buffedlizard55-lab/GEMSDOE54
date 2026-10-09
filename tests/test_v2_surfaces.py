"""Synthetic checks for the v2 feature surfaces (C4 cross-gradient, C5 conductivity gradient)."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))


def _load_evaluator():
    spec = importlib.util.spec_from_file_location("holdout_segment_cv", ROOT / "scripts" / "holdout_segment_cv.py")
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


def test_cross_gradient_is_unit_bounded_and_zero_outside_valid():
    ev = _load_evaluator()
    rng = np.random.default_rng(1)
    foot = np.ones((40, 50), dtype=bool)
    tmi = rng.normal(size=foot.shape)
    grav = rng.normal(size=foot.shape)
    tmi[0, :5] = np.nan
    surf, valid = ev.cross_gradient_surface(tmi, grav, foot)
    assert valid.sum() == foot.sum() - 5
    assert np.all(surf[valid] > 0) and np.all(surf[valid] <= 1.0)
    assert np.all(surf[~valid] == 0.0)


def test_cross_gradient_high_only_where_both_fields_are_high():
    ev = _load_evaluator()
    foot = np.ones((20, 20), dtype=bool)
    tmi = np.zeros(foot.shape)
    grav = np.zeros(foot.shape)
    tmi[10, :] = 5.0          # magnetic edge only on row 10
    grav[10, :10] = 5.0       # gravity edge only on the left half of row 10
    surf, _ = ev.cross_gradient_surface(tmi, grav, foot)
    coincident = surf[10, :10].mean()
    magnetic_only = surf[10, 10:].mean()
    assert coincident > magnetic_only


def test_conductivity_gradient_does_not_leak_filled_nans():
    ev = _load_evaluator()
    foot = np.ones((30, 30), dtype=bool)
    cond = np.full(foot.shape, 2.0)
    cond[5:8, 5:8] = np.nan
    mag, valid = ev.conductivity_gradient_surface(cond, foot)
    assert not valid[5, 5]
    assert mag[5, 5] == 0.0
    assert np.all(np.isfinite(mag))
    assert np.allclose(mag[valid], 0.0)  # constant field -> zero gradient on valid cells

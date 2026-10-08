"""Regression tests for the whole-segment hide-and-recover protocol.

These use small synthetic grids, so they run in seconds.  They check the properties the
pre-registration depends on:
  * whole buffered segment groups are assigned to one fold (no split segment);
  * a fold's visible catalogue stays more than the collar away from its withheld truth;
  * the two independent pooled-DTI implementations agree on binary dot predictions.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import numpy as np
from scipy.ndimage import distance_transform_edt

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from gemsdoe54.holdout import pooled_metric, segment_blocks  # noqa: E402
from gems_metric import dti_components  # noqa: E402

_spec = importlib.util.spec_from_file_location("run_segment_holdout", ROOT / "scripts/run_segment_holdout.py")
rsh = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(rsh)


def _catalogue(shape=(60, 60), seed=3):
    rng = np.random.default_rng(seed)
    cat = np.zeros(shape, dtype=bool)
    for _ in range(9):
        r0, c0 = rng.integers(0, shape[0] - 12), rng.integers(0, shape[1] - 12)
        length = int(rng.integers(6, 12))
        cat[r0:r0 + length, c0 + (np.arange(length) // 2)] = True
    return cat


def test_fold_assignment_keeps_each_buffered_group_whole():
    cat = _catalogue()
    blocks, _ = segment_blocks(cat.astype(np.uint8), buffer_px=3)
    fold_of = rsh.assign_folds(blocks, cat, 4, np.random.default_rng(1))
    assert (fold_of[np.unique(blocks[blocks > 0])] >= 0).all()
    grp_fold = np.where(blocks > 0, fold_of[blocks], -1)
    for g in np.unique(blocks[blocks > 0]):
        assert np.unique(grp_fold[blocks == g]).size == 1


def test_visible_catalogue_is_outside_the_withheld_collar():
    cat = _catalogue()
    blocks, _ = segment_blocks(cat.astype(np.uint8), buffer_px=3)
    fold_of = rsh.assign_folds(blocks, cat, 4, np.random.default_rng(2))
    grp_fold = np.where(blocks > 0, fold_of[blocks], -1)
    for k in range(4):
        in_k = grp_fold == k
        truth = cat & in_k
        visible = cat & ~in_k
        if not truth.any():
            continue
        d_to_truth = distance_transform_edt(~truth, sampling=100.0)
        # no visible catalogue cell lies within the 300 m collar of withheld truth
        assert not np.any(visible & (d_to_truth <= 300.0))


def test_two_independent_pooled_dti_implementations_agree_on_dots():
    rng = np.random.default_rng(7)
    shape = (120, 120)
    truth = np.zeros(shape, dtype=bool)
    truth[30:90, 60] = True
    truth[10:40, 20:24] = True
    dots = rng.random(shape) < 0.01
    dots[30:90:4, 59] = True  # dots that really sit near truth
    valid = np.ones(shape, dtype=bool)

    official = dti_components(dots.astype(float), truth, valid=valid).dti
    holdout_impl, _, _, _ = pooled_metric(truth, dots, kernel_px=3.0)
    assert abs(official - holdout_impl) < 1e-6, (official, holdout_impl)


def test_matched_random_control_has_requested_count_and_stays_allowed():
    allowed = np.zeros((20, 20), dtype=bool)
    allowed[:, :10] = True
    out = rsh.matched_random(15, allowed, np.random.default_rng(0))
    assert out.sum() == 15
    assert not out[:, 10:].any()

"""Synthetic checks for the whole-segment holdout evaluator and the metric identities it relies on."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import numpy as np
from scipy.ndimage import distance_transform_edt

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from gemsdoe54.holdout import pooled_metric, single_feature_auc  # noqa: E402


def _load_evaluator():
    spec = importlib.util.spec_from_file_location("holdout_segment_cv", ROOT / "scripts" / "holdout_segment_cv.py")
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


def _synthetic():
    rng = np.random.default_rng(3)
    truth = np.zeros((120, 140), bool)
    seg_local = np.full(truth.shape, -1, dtype=np.int64)
    truth[20, 10:60] = True
    seg_local[20, 10:60] = 0
    truth[70:90, 100] = True
    seg_local[70:90, 100] = 1
    dots = rng.random(truth.shape) < 0.01
    return truth, seg_local, dots


def test_fold_scorer_matches_grid_metric():
    ev = _load_evaluator()
    truth, seg_local, dots = _synthetic()
    scored = np.ones_like(truth)
    scorer = ev.FoldScorer(truth, seg_local, 2, scored)
    sc = scorer.score(dots, with_D=True)
    dti_grid, tp, fp, fn = pooled_metric(truth, dots)
    assert abs(sc["TP"] - tp) < 1e-9
    assert abs(sc["FP"] - fp) < 1e-9
    assert abs(sc["FN"] - fn) < 1e-9
    assert abs(ev.dti_from(sc["TP"], sc["FP"], sc["FN"]) - dti_grid) < 1e-12


def test_segment_distance_matrix_equals_grid_distance_to_truth():
    ev = _load_evaluator()
    truth, seg_local, dots = _synthetic()
    scorer = ev.FoldScorer(truth, seg_local, 2, np.ones_like(truth))
    sc = scorer.score(dots, with_D=True)
    ys, xs = np.nonzero(dots)
    grid_d = distance_transform_edt(~truth)[ys, xs]
    assert np.allclose(sc["D"].min(axis=1), grid_d, atol=1e-5)


def test_segment_sums_reproduce_total_tp():
    ev = _load_evaluator()
    truth, seg_local, dots = _synthetic()
    scorer = ev.FoldScorer(truth, seg_local, 2, np.ones_like(truth))
    sc = scorer.score(dots, with_D=False)
    assert abs(float(sc["TP_seg"].sum()) - sc["TP"]) < 1e-9


def test_deleting_zero_credit_dots_only_changes_fp():
    truth = np.zeros((200, 200), bool)
    truth[100, 20:180] = True
    dots = np.zeros_like(truth)
    dots[98, 50] = True  # earns credit
    dots[10, 10] = True  # zero credit
    dots[190, 190] = True  # zero credit
    _, tp0, fp0, fn0 = pooled_metric(truth, dots)
    pruned = dots.copy()
    pruned[10, 10] = False
    pruned[190, 190] = False
    _, tp1, fp1, fn1 = pooled_metric(truth, pruned)
    assert abs(tp1 - tp0) < 1e-12 and abs(fn1 - fn0) < 1e-12
    assert abs((fp0 - fp1) - 2.0) < 1e-12


def test_single_feature_auc_is_symmetric_and_tie_safe():
    truth = np.zeros((50, 50), bool)
    truth[:5, :] = True
    valid = np.ones_like(truth)
    perfect = truth.astype(np.float32)
    assert abs(single_feature_auc(perfect, truth, valid=valid) - 1.0) < 1e-9
    assert abs(single_feature_auc(-perfect, truth, valid=valid) - 1.0) < 1e-9
    constant = np.zeros(truth.shape, np.float32)
    assert abs(single_feature_auc(constant, truth, valid=valid) - 0.5) < 1e-9

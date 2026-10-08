"""Exact group jackknife must equal brute-force recomputation with the official metric."""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from gemsdoe54.jackknife import (  # noqa: E402
    group_jackknife_counts,
    jackknife_se,
    leave_one_out_dti,
)
from gems_metric import dti_components  # noqa: E402


def _synthetic(seed: int):
    rng = np.random.default_rng(seed)
    shape = (70, 70)
    truth = np.zeros(shape, dtype=bool)
    gid = np.zeros(shape, dtype=np.int64)
    g = 0
    for _ in range(7):
        g += 1
        r0, c0 = rng.integers(2, 60, size=2)
        length = int(rng.integers(5, 14))
        rows = np.clip(r0 + np.arange(length), 0, shape[0] - 1)
        cols = np.clip(c0 + (np.arange(length) // 3), 0, shape[1] - 1)
        truth[rows, cols] = True
        gid[rows, cols] = g
    dots = rng.random(shape) < 0.02
    dots[truth] = dots[truth] & (rng.random(truth.sum()) < 0.5)  # some dots on truth
    valid = np.ones(shape, dtype=bool)
    return dots, truth, gid, valid


def test_pooled_counts_match_official_metric():
    for seed in (1, 2, 3):
        dots, truth, gid, valid = _synthetic(seed)
        counts = group_jackknife_counts(dots, truth, gid, valid)
        c = dti_components(dots.astype(float), truth, valid=valid)
        assert abs(counts["TP"] - c.tp_w) < 1e-6
        assert abs(counts["FP"] - c.fp_w) < 1e-6
        assert abs(counts["FN"] - c.fn_w) < 1e-6


def test_every_leave_one_group_out_value_matches_brute_force():
    dots, truth, gid, valid = _synthetic(5)
    counts = group_jackknife_counts(dots, truth, gid, valid)
    loo = leave_one_out_dti(counts)
    for i, g in enumerate(counts["gids"]):
        truth_wo = truth & (gid != g)
        brute = dti_components(dots.astype(float), truth_wo, valid=valid).dti
        assert abs(loo[i] - brute) < 1e-9, (g, loo[i], brute)


def test_jackknife_se_is_nonnegative_and_zero_for_constant_estimates():
    assert abs(jackknife_se(np.full(10, 0.3))) < 1e-12
    assert jackknife_se(np.array([0.1, 0.2, 0.3, 0.4])) > 0.0

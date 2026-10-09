#!/usr/bin/env python3
"""Brute-force check of the exact marginal rule used in docs and evidence (2026-10-09).

For a binary prediction with unit mass, with t = change in TP_w caused by one dot and
k = the dot's own kernel mass max_g k(d(x,g)):
    deleting x raises DTI  iff  t <  0.2 * DTI * (1 + t - k)
    adding x   raises DTI  iff  t >  0.2 * DTI * (1 + t - k)
and the closed form DTI' = T' / (0.2 N' + 0.8 G + 0.2 (T' - M')) equals the brute-force DTI.
Synthetic 40 x 40 grid at 100 m; no registry data is read.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
from scipy.ndimage import distance_transform_edt

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from gems_metric import dti_components, kernel_mass  # noqa: E402

R_M = 300.0


def _setup(seed: int):
    rng = np.random.default_rng(seed)
    truth = np.zeros((40, 40), dtype=bool)
    truth[4:36, 20] = True                      # one vertical "fault" of 32 cells
    truth[10:30, 31] = True                     # a second, offset segment
    foot = np.ones_like(truth)
    pred = (rng.random(truth.shape) < 0.08) & foot
    return rng, truth, foot, pred


def _check(seed: int) -> None:
    rng, truth, foot, pred = _setup(seed)
    lab = truth.astype(np.int16)
    d_truth = distance_transform_edt(~truth, sampling=(100.0, 100.0))
    kern = np.maximum(1.0 - d_truth / R_M, 0.0)
    G = int(truth.sum())
    base = dti_components(pred.astype(np.float64), lab, valid=foot)
    dti0, T0 = base.dti, base.tp_w
    M0 = kernel_mass(pred.astype(np.float64), lab, valid=foot)
    N0 = float(pred.sum())
    dots = np.argwhere(pred)
    empties = np.argwhere(~pred)
    picks = [("delete", tuple(p)) for p in dots[rng.choice(len(dots), size=min(12, len(dots)), replace=False)]]
    picks += [("add", tuple(p)) for p in empties[rng.choice(len(empties), size=12, replace=False)]]
    checked = 0
    for op, (y, x) in picks:
        mod = pred.copy()
        mod[y, x] = not mod[y, x]
        c1 = dti_components(mod.astype(np.float64), lab, valid=foot)
        k = float(kern[y, x])
        if op == "delete":
            t = T0 - c1.tp_w
            N1, M1, T1 = N0 - 1, M0 - k, c1.tp_w
        else:
            t = c1.tp_w - T0
            N1, M1, T1 = N0 + 1, M0 + k, c1.tp_w
        closed = T1 / (0.2 * N1 + 0.8 * G + 0.2 * (T1 - M1))
        assert abs(closed - c1.dti) < 1e-9, (op, y, x, closed, c1.dti)
        threshold = 0.2 * dti0 * (1.0 + t - k)
        if abs(t - threshold) < 1e-12:
            continue                                     # tie: rule is silent
        predicted_up = (t < threshold) if op == "delete" else (t > threshold)
        actual_up = c1.dti > dti0
        assert predicted_up == actual_up, (op, y, x, t, k, dti0)
        checked += 1
    assert checked >= 20


def test_exact_marginal_rule_and_closed_form_match_bruteforce():
    for seed in (1, 2, 3):
        _check(seed)


def test_zero_credit_dot_deletion_raises_dti_and_addition_lowers_it():
    rng, truth, foot, pred = _setup(7)
    lab = truth.astype(np.int16)
    # a cell far from every truth cell (distance > R): its kernel mass and credit are both zero
    d_truth = distance_transform_edt(~truth, sampling=(100.0, 100.0))
    far = np.argwhere(d_truth > R_M + 100.0)
    y, x = map(int, far[0])
    base = dti_components(pred.astype(np.float64), lab, valid=foot)
    pred_add = pred.copy()
    pred_add[y, x] = True
    assert not pred[y, x]
    assert dti_components(pred_add.astype(np.float64), lab, valid=foot).dti < base.dti
    pred_del = pred.copy()
    pred_del[y, x] = True          # start from a state where the far dot exists
    b2 = dti_components(pred_del.astype(np.float64), lab, valid=foot)
    pred_del[y, x] = False
    assert dti_components(pred_del.astype(np.float64), lab, valid=foot).dti > b2.dti

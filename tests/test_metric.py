#!/usr/bin/env python3
"""Regression tests for the official GEMS metric.

Test 1 is the organizer's own published worked example.  If this passes, the
implementation is anchored to the competition page rather than to anyone's
recollection of it.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from gems_metric import ALPHA, BETA, RADIUS_M, dti_components, kernel_mass  # noqa: E402


def test_official_worked_example() -> None:
    """Page 967 '# Scoring example': TP_w=3.00, FP_w=1.89, FN_w=2.00 -> 0.60."""
    tp, fp, fn = 3.00, 1.89, 2.00
    got = tp / (tp + ALPHA * fp + BETA * fn + 1e-8)
    assert abs(got - 0.60) < 0.005, f"expected ~0.60, got {got}"
    print(f"  OK  organizer worked example -> {got:.6f} (page states 0.60)")


def test_constants_match_the_published_definition() -> None:
    assert ALPHA == 0.2 and BETA == 0.8 and RADIUS_M == 300.0
    print("  OK  alpha=0.2, beta=0.8, R=300 m")


def test_exact_algebraic_identities() -> None:
    """FP_w = sum(p) - M exactly, and TP_w + FN_w = G exactly."""
    rng = np.random.default_rng(0)
    pred = (rng.random((90, 90)) < 0.02) * rng.random((90, 90))
    truth = (rng.random((90, 90)) < 0.05).astype(float)
    comp = dti_components(pred, truth)
    mass = kernel_mass(pred, truth)
    lhs = float(pred.sum()) - mass
    assert np.isclose(comp.fp_w, lhs, rtol=1e-9), f"{comp.fp_w} != {lhs}"
    g = int((truth == 1).sum())
    assert np.isclose(comp.tp_w + comp.fn_w, g, rtol=1e-9), f"{comp.tp_w + comp.fn_w} != {g}"
    print(f"  OK  FP_w == sum(p) - M ({lhs:.6f});  TP_w + FN_w == G ({g})")


def test_closed_form_for_unit_predictions() -> None:
    """For unit-valued dots, DTI must equal T / (0.2N + 0.8G + 0.2(T - M))."""
    rng = np.random.default_rng(7)
    dots = np.zeros((80, 80))
    idx = rng.choice(80 * 80, size=120, replace=False)
    dots.ravel()[idx] = 1.0
    truth = np.zeros((80, 80))
    t_idx = rng.choice(80 * 80, size=200, replace=False)
    truth.ravel()[t_idx] = 1.0
    comp = dti_components(dots, truth)
    mass = kernel_mass(dots, truth)
    n = int(dots.sum())
    g = int(truth.sum())
    closed = comp.tp_w / (0.2 * n + 0.8 * g + 0.2 * (comp.tp_w - mass) + 1e-8)
    assert np.isclose(comp.dti, closed, rtol=1e-6), f"{comp.dti} != {closed}"
    print(f"  OK  closed form matches: {comp.dti:.6f} == {closed:.6f}")


def test_no_truth_gives_zero() -> None:
    pred = np.zeros((20, 20))
    pred[5, 5] = 1.0
    comp = dti_components(pred, np.zeros((20, 20)))
    assert comp.dti == 0.0 and comp.tp_w == 0.0 and comp.fp_w == 1.0
    print("  OK  empty truth -> DTI 0.0, FP_w = 1.0")


def test_rejects_illegal_values() -> None:
    pred = np.zeros((20, 20))
    pred[5, 5] = 1.5
    truth = np.zeros((20, 20))
    try:
        dti_components(pred, truth)
    except ValueError as exc:
        print(f"  OK  out-of-range prediction rejected: {exc}")
        return
    raise AssertionError("value 1.5 was not rejected")


def test_perfect_prediction_scores_one() -> None:
    truth = np.zeros((60, 60))
    truth[30, 10:50] = 1.0
    comp = dti_components(truth.copy(), truth)
    assert comp.dti > 0.999, f"perfect prediction scored {comp.dti}"
    print(f"  OK  exact reproduction of truth -> DTI {comp.dti:.6f}")


if __name__ == "__main__":
    test_official_worked_example()
    test_constants_match_the_published_definition()
    test_exact_algebraic_identities()
    test_closed_form_for_unit_predictions()
    test_no_truth_gives_zero()
    test_rejects_illegal_values()
    test_perfect_prediction_scores_one()
    print("all metric tests passed")

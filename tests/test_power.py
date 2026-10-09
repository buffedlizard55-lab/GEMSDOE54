from __future__ import annotations

import numpy as np
import pytest

from gemsdoe54.power import analyse_holdout_receipt, minimum_detectable_cohen_d


def _receipt() -> dict:
    bootstrap = np.random.default_rng(7).normal(loc=0.003, scale=0.01, size=1500).tolist()
    return {
        "evaluator": {
            "version": "test-evaluator-v1",
            "metric": {
                "name": "DTI",
                "alpha": 0.2,
                "beta": 0.8,
                "kernel": "triangular",
                "kernel_radius_m": 300.0,
                "aggregation": "pooled",
            },
        },
        "design": {
            "whole_fault_segments_withheld": True,
            "catalogue_features_from_visible_faults_only": True,
            "visible_fault_mask": "pixel_exact",
            "buffer_m": 500.0,
            "bootstrap_unit": "whole_fault_segment",
            "withheld_positive_count": 500,
            "independent_unit_count": 16,
        },
        "comparison": {
            "observed_pooled_delta_dti": 0.003,
            "pooled_delta_bootstrap": bootstrap,
        },
    }


def test_cohen_d_mde_decreases_with_more_independent_units():
    assert minimum_detectable_cohen_d(100) > minimum_detectable_cohen_d(1000) > 0


def test_receipt_reports_holdout_ci_and_separate_iid_warning():
    report = analyse_holdout_receipt(_receipt())
    holdout = report["holdout_dti"]
    assert holdout["label"] == "HOLDOUT-DTI"
    assert holdout["evaluator_version"] == "test-evaluator-v1"
    assert holdout["withheld_positive_count"] == 500
    assert len(holdout["paired_cluster_bootstrap_95_percent_ci"]) == 2
    power = report["power"]
    assert power["independent_unit_count"] == 16
    assert power["cohen_d_minimum_detectable_at_independent_unit_level"] > 0
    assert power["pooled_dti_raw_scale_mde_approximation"] > 0
    assert "not valid" in power["pixel_iid_warning"].lower()


def test_receipt_rejects_wrong_kernel_and_nonvisible_catalogue_features():
    bad_kernel = _receipt()
    bad_kernel["evaluator"]["metric"]["kernel_radius_m"] = 200.0
    with pytest.raises(ValueError, match="kernel_radius_m"):
        analyse_holdout_receipt(bad_kernel)

    bad_features = _receipt()
    bad_features["design"]["catalogue_features_from_visible_faults_only"] = False
    with pytest.raises(ValueError, match="visible faults only"):
        analyse_holdout_receipt(bad_features)


def test_receipt_rejects_spatial_block_substitute():
    bad = _receipt()
    bad["design"]["bootstrap_unit"] = "spatial_block"
    with pytest.raises(ValueError, match="spatial blocks are not an accepted substitute"):
        analyse_holdout_receipt(bad)


def test_receipt_rejects_too_few_bootstrap_draws():
    bad = _receipt()
    bad["comparison"]["pooled_delta_bootstrap"] = [0.0] * 999
    with pytest.raises(ValueError, match="at least 1000"):
        analyse_holdout_receipt(bad)


def test_large_n_small_d_is_finite():
    # regression (IR-54-050): nct returned NaN at n = 60,988 and brentq crashed; the normal fallback is ~ 2.80 / sqrt(n)
    from gemsdoe54.power import minimum_detectable_cohen_d

    d = minimum_detectable_cohen_d(60988)
    assert np.isfinite(d)
    assert abs(d - (1.959964 + 0.841621) / np.sqrt(60988)) < 1e-3

"""Power calculations for paired, spatially clustered holdout comparisons.

Cohen's d is a standardized effect, not a raw DTI increment. For a DTI comparison, a raw
minimum-detectable difference also requires a variance estimate from paired holdout resamples.
Pixels are not independent experimental units when faults form spatially autocorrelated segments.
"""

from __future__ import annotations

from typing import Any

import numpy as np
from scipy.optimize import brentq
from scipy.stats import nct, norm, t


ALPHA = 0.05
TARGET_POWER = 0.80


def minimum_detectable_cohen_d(
    independent_units: int,
    alpha: float = ALPHA,
    target_power: float = TARGET_POWER,
) -> float:
    """Return the smallest positive paired-t Cohen's d detectable at the requested power.

    The calculation uses an exact noncentral-t power function for a two-sided one-sample t-test
    on paired differences. ``independent_units`` must be the count of independent paired units
    (for this study, at minimum whole withheld fault segments separated by the registered buffer),
    not the number of raster pixels.
    """
    if isinstance(independent_units, bool) or int(independent_units) != independent_units:
        raise ValueError("independent_units must be an integer")
    n = int(independent_units)
    if n < 2:
        raise ValueError("at least two independent paired units are required")
    if not np.isfinite(alpha) or not (0.0 < alpha < 1.0):
        raise ValueError("alpha must be between zero and one")
    if not np.isfinite(target_power) or not (0.5 < target_power < 1.0):
        raise ValueError("target_power must be between 0.5 and one")

    df = n - 1
    critical = float(t.ppf(1.0 - alpha / 2.0, df))

    def achieved_power(d: float) -> float:
        noncentrality = d * np.sqrt(n)
        return float(nct.cdf(-critical, df, noncentrality) +
                     nct.sf(critical, df, noncentrality))

    upper = 0.1
    # Bracket adaptively. Very large, unnecessary noncentrality parameters can make scipy's
    # noncentral-t CDF numerically indeterminate, so do not start with an arbitrary huge bound.
    while upper <= 64.0:
        value = achieved_power(upper)
        if np.isfinite(value) and value >= target_power:
            break
        upper *= 2.0
    else:
        raise ArithmeticError("could not bracket the requested power with a finite noncentral-t value")
    return float(brentq(lambda d: achieved_power(d) - target_power, 0.0, upper,
                        xtol=1e-12, rtol=1e-12, maxiter=1000))


def normal_approx_mde_from_se(standard_error: float, alpha: float = ALPHA,
                              target_power: float = TARGET_POWER) -> float:
    """Approximate raw-scale two-sided MDE from a valid estimator standard error.

    A cluster-bootstrap standard error for *pooled DTI differences* is a defensible input here;
    the result remains an approximation under a normal-shift alternative. It is not a projection
    of a competition score.
    """
    if not np.isfinite(standard_error) or standard_error < 0:
        raise ValueError("standard_error must be finite and nonnegative")
    if not np.isfinite(alpha) or not (0.0 < alpha < 1.0):
        raise ValueError("alpha must be between zero and one")
    if not np.isfinite(target_power) or not (0.5 < target_power < 1.0):
        raise ValueError("target_power must be between 0.5 and one")
    z_alpha = float(norm.ppf(1.0 - alpha / 2.0))
    z_power = float(norm.ppf(target_power))
    return (z_alpha + z_power) * float(standard_error)


def analyse_holdout_receipt(receipt: dict[str, Any]) -> dict[str, Any]:
    """Validate and summarize a preregistered pooled-DTI holdout receipt.

    Required receipt keys are intentionally strict. The holdout runner must provide the evaluator
    version, exact scoring contract, withheld-positive count, number of whole-segment units, the
    paired pooled-DTI difference, and segment/block-bootstrap differences. Missing evidence is an
    error; no value is inferred from a leaderboard or from a user's reported score.
    """
    evaluator = receipt.get("evaluator", {})
    design = receipt.get("design", {})
    comparison = receipt.get("comparison", {})
    metric = evaluator.get("metric", {})

    version = evaluator.get("version")
    if not isinstance(version, str) or not version.strip():
        raise ValueError("evaluator.version is required")
    expected_metric = {
        "name": "DTI",
        "alpha": 0.2,
        "beta": 0.8,
        "kernel": "triangular",
        "kernel_radius_m": 300.0,
        "aggregation": "pooled",
    }
    for key, expected in expected_metric.items():
        observed = metric.get(key)
        if isinstance(expected, float):
            if not isinstance(observed, (int, float)) or not np.isclose(observed, expected, rtol=0, atol=1e-12):
                raise ValueError(f"evaluator.metric.{key} must equal {expected}")
        elif observed != expected:
            raise ValueError(f"evaluator.metric.{key} must equal {expected!r}")
    if design.get("whole_fault_segments_withheld") is not True:
        raise ValueError("whole fault segments must be withheld")
    if design.get("catalogue_features_from_visible_faults_only") is not True:
        raise ValueError("catalogue-derived features must use visible faults only")
    if design.get("visible_fault_mask") != "pixel_exact":
        raise ValueError("visible faults must be masked pixel-exactly")
    buffer_m = design.get("buffer_m")
    if isinstance(buffer_m, bool) or not isinstance(buffer_m, (int, float)) or not np.isfinite(buffer_m) or buffer_m <= 0:
        raise ValueError("a positive whole-segment buffer_m is required")
    if design.get("bootstrap_unit") != "whole_fault_segment_or_spatial_block":
        raise ValueError("bootstrap_unit must preserve whole fault segments or spatial blocks")

    n_positive = design.get("withheld_positive_count")
    n_units = design.get("independent_unit_count")
    if isinstance(n_positive, bool) or not isinstance(n_positive, int) or n_positive < 2:
        raise ValueError("design.withheld_positive_count must be an integer >= 2")
    if isinstance(n_units, bool) or not isinstance(n_units, int) or n_units < 2:
        raise ValueError("design.independent_unit_count must be an integer >= 2")

    observed_delta = comparison.get("observed_pooled_delta_dti")
    if isinstance(observed_delta, bool) or not isinstance(observed_delta, (int, float)) or not np.isfinite(observed_delta):
        raise ValueError("comparison.observed_pooled_delta_dti must be finite")
    bootstrap = np.asarray(comparison.get("pooled_delta_bootstrap", []), dtype=np.float64)
    if bootstrap.ndim != 1 or bootstrap.size < 1000 or not np.isfinite(bootstrap).all():
        raise ValueError("comparison.pooled_delta_bootstrap needs at least 1000 finite cluster-bootstrap replicates")

    ci_low, ci_high = np.quantile(bootstrap, [0.025, 0.975])
    bootstrap_se = float(bootstrap.std(ddof=1))
    d_min_segments = minimum_detectable_cohen_d(n_units)
    d_min_iid_pixels = minimum_detectable_cohen_d(n_positive)
    raw_mde = normal_approx_mde_from_se(bootstrap_se)
    ci_excludes_zero = bool(ci_low > 0.0 or ci_high < 0.0)

    return {
        "schema": "gemsdoe54.power-report.v1",
        "holdout_dti": {
            "label": "HOLDOUT-DTI",
            "evaluator_version": version,
            "withheld_positive_count": n_positive,
            "observed_pooled_delta_dti": float(observed_delta),
            "paired_cluster_bootstrap_95_percent_ci": [float(ci_low), float(ci_high)],
            "bootstrap_replicates": int(bootstrap.size),
            "ci_excludes_zero": ci_excludes_zero,
        },
        "power": {
            "alpha": ALPHA,
            "target_power": TARGET_POWER,
            "independent_unit": "whole withheld fault segments or preregistered spatial blocks",
            "independent_unit_count": n_units,
            "cohen_d_minimum_detectable_at_independent_unit_level": d_min_segments,
            "pooled_dti_raw_scale_mde_approximation": raw_mde,
            "pooled_dti_bootstrap_standard_error": bootstrap_se,
            "pixel_iid_cohen_d_floor_not_valid_for_decision": d_min_iid_pixels,
            "pixel_iid_warning": (
                "The pixel-count result is only an optimistic independence calculation. Spatially "
                "correlated positives do not supply that many independent observations; this pixel-IID floor is not valid for inference."
            ),
            "interpretation": (
                "Use the pooled-DTI cluster-bootstrap confidence interval for the actual comparison. "
                "Cohen's d is standardized; a raw DTI detection floor additionally depends on the "
                "observed uncertainty. Do not infer a leaderboard ranking from this local analysis."
            ),
        },
        "protocol": {
            "alpha": metric["alpha"],
            "beta": metric["beta"],
            "kernel": metric["kernel"],
            "kernel_radius_m": metric["kernel_radius_m"],
            "aggregation": metric["aggregation"],
            "withheld_whole_segments": True,
            "catalogue_features_visible_only": True,
            "visible_mask": "pixel_exact",
            "buffer_m": float(buffer_m),
            "bootstrap_unit": design["bootstrap_unit"],
        },
        "decision": "not_enough_information_to_claim_a_win" if not ci_excludes_zero else
                    "local_holdout_difference_ci_excludes_zero_not_organizer_confirmation",
    }

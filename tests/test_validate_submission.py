from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from preflight_junction_lane import angular_transition_surface  # noqa: E402
from validate_submission import check_format, check_lane_arrays  # noqa: E402
from gemsdoe54.grid import write_submission  # noqa: E402


def test_cached_label_mirror_passes_local_null_outside_format_check():
    report = check_format(
        ROOT / "data/grid/MIRROR_sample_submission_template.tif",
        ROOT / "data/grid/labels.tif",
    )
    assert report["passed"] is True
    assert report["values"]["positive_cells"] == 60_988
    assert report["values"]["nan_outside_footprint"] > 0


def test_archived_h54a_passes_all_finite_outside_format_gate():
    # IR-54-051: the organizer form check is "Predicted values must be in range
    # [0, 1]" over the whole raster; finite zeros outside the footprint are the
    # organizer-form-safe convention (the 0.2778 artefact is a -zeros file).
    report = check_format(
        ROOT / "docs/downloads/gems54-undercomplement-q200.tif",
        ROOT / "data/grid/labels.tif",
    )
    assert report["passed"] is True
    assert "all-finite-outside" in report["checks"]["outside_footprint_convention"]["detail"]
    assert report["checks"]["all_values_in_0_1_wherever_finite"]["ok"] is True


def test_angular_transition_surface_marks_crossing_but_not_straight_trace():
    sgmc = np.zeros((15, 15), dtype=bool)
    catalogue = np.zeros_like(sgmc)
    catalogue[0, 0] = True
    sgmc[7, 4:11] = True
    sgmc[4:11, 7] = True

    surface, support_count = angular_transition_surface(sgmc, catalogue)

    assert surface[7, 7] > 0
    assert support_count > 0
    assert surface[7, 4] == 0  # a straight endpoint has only two angular transitions


def test_lane_gate_uses_absolute_rank_correlation():
    foot = np.ones((10, 10), dtype=bool)
    candidate = np.arange(100, dtype=np.float64).reshape(10, 10)
    registry = 100.0 - candidate

    result = check_lane_arrays(candidate, [("anti-correlated.tif", registry)], foot)

    row = result["rows"][0]
    assert row["spearman_rho"] == -1.0
    assert row["absolute_spearman_rho"] == 1.0
    assert row["rho_flag"] is True
    assert result["lane_drift_detected"] is True
    assert result["verdict"] == "DUPLICATE - STOP"


def test_near_covering_registry_overlap_is_reported_but_exempt_from_verdict():
    # IR-54-050: a blanket/near-covering registry raster cannot discriminate
    # overlap (r13_lattice covers 99.87% of the footprint; the literal gate is
    # otherwise unsatisfiable).  The literal statistic is still reported, the
    # verdict exempts it, and rank correlation still applies to it.
    foot = np.ones((25, 25), dtype=bool)
    candidate = np.zeros((25, 25), dtype=np.float32)
    candidate[::4, ::4] = 1.0
    # near-covering, non-constant registry (constant => rho undefined, different path)
    registry = np.full((25, 25), 0.1, dtype=np.float32)
    registry += np.linspace(0.0, 0.5, 25, dtype=np.float32)[None, :]

    result = check_lane_arrays(candidate, [("blanket.tif", registry)], foot)

    row = result["rows"][0]
    assert row["registry_covers_fraction_of_footprint"] > 0.99
    assert row["overlap_test_admissible"] is False
    assert row["fraction_of_my_dots"] == 1.0
    assert row["overlap_flag_literal"] is True
    assert row["overlap_flag"] is False
    assert result["lane_drift_detected"] is False
    assert result["verdict"] == "distinct lane"
    assert "blanket.tif" in result["flagged_registry_literal"]


def test_binding_overlap_still_stops_on_non_degenerate_registry():
    foot = np.ones((25, 25), dtype=bool)
    candidate = np.zeros((25, 25), dtype=np.float32)
    candidate[10, 10] = 1.0
    candidate[15, 15] = 1.0
    registry = np.zeros((25, 25), dtype=np.float32)
    registry[10, 11] = 1.0
    registry[16, 15] = 1.0  # covers a small fraction of the footprint

    result = check_lane_arrays(candidate, [("subset.tif", registry)], foot)

    row = result["rows"][0]
    assert row["overlap_test_admissible"] is True
    assert row["overlap_flag"] is True
    assert result["lane_drift_detected"] is True
    assert result["verdict"] == "DUPLICATE - STOP"


def test_missing_registry_is_indeterminate_not_a_lane_pass():
    foot = np.ones((4, 4), dtype=bool)
    candidate = np.eye(4, dtype=np.float32)

    result = check_lane_arrays(candidate, [], foot)

    assert result["verdict"] == "INDETERMINATE - no registry rasters"
    assert result["lane_drift_detected"] is None


def test_constant_surface_is_json_safe_and_indeterminate_when_empty():
    foot = np.ones((8, 8), dtype=bool)
    candidate = np.zeros((8, 8), dtype=np.float32)
    registry = np.zeros((8, 8), dtype=np.float32)

    result = check_lane_arrays(candidate, [("constant.tif", registry)], foot)

    assert result["verdict"] == "INDETERMINATE - no positive candidate cells"
    assert result["rows"][0]["spearman_rho"] is None
    assert result["rows"][0]["fraction_of_my_dots"] is None
    assert result["lane_drift_detected"] is False


def test_submission_writer_refuses_non_float32_dtype(tmp_path):
    with np.testing.assert_raises_regex(ValueError, "dtype must be float32"):
        write_submission(tmp_path / "wrong-dtype.tif", np.zeros((1, 1)), dtype="float64")


def test_lane_surface_rejects_nonfinite_values_and_bad_shapes():
    foot = np.ones((3, 4), dtype=bool)
    with np.testing.assert_raises_regex(ValueError, "non-finite"):
        check_lane_arrays(np.full((3, 4), np.nan), [], foot)
    with np.testing.assert_raises_regex(ValueError, "same-shape"):
        check_lane_arrays(np.zeros((4, 3)), [], foot)

#!/usr/bin/env python3
"""Regression tests for the dot emitter and the grid contract."""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest
from scipy.ndimage import distance_transform_edt

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from gemsdoe54.emission import emit_spaced_dots  # noqa: E402
from gemsdoe54.grid import EXPECTED_SHAPE, EXPECTED_TRANSFORM, footprint, write_submission  # noqa: E402


def test_emitted_dots_are_a_subset_of_candidates() -> None:
    """Regression: an earlier version used one array for both the emitted dots and
    the exclusion zone, which marked non-dot cells as positives."""
    cand = np.zeros((40, 40), dtype=bool)
    cand[10:30, 10:30] = True
    dots = emit_spaced_dots(cand, spacing_px=3.0)
    assert dots.dtype == bool
    assert not (dots & ~cand).any(), "emitter produced dots outside the candidate set"
    print(f"  OK  dots are a subset of candidates ({int(dots.sum())} emitted)")


def test_minimum_separation_is_enforced() -> None:
    cand = np.zeros((60, 60), dtype=bool)
    cand[5:55, 5:55] = True
    spacing = 3.0
    dots = emit_spaced_dots(cand, spacing_px=spacing)
    # Distance from each dot to its nearest *other* dot.  A distance transform to
    # the dot set reads 0 at every dot, so a k-d tree is the correct tool here.
    from scipy.spatial import cKDTree

    coords = np.argwhere(dots).astype(float)
    tree = cKDTree(coords)
    nn = tree.query(coords, k=2)[0][:, 1]
    worst = float(nn.min())
    assert worst >= spacing - 1e-9, f"two dots only {worst} apart (limit {spacing})"
    print(f"  OK  min separation {worst:.4f} >= {spacing}")


def test_deterministic_and_priority_respected() -> None:
    cand = np.zeros((30, 30), dtype=bool)
    cand[5:25, 5:25] = True
    prio = np.zeros((30, 30))
    prio[10, 10] = 100.0
    a = emit_spaced_dots(cand, priority=prio, spacing_px=3.0)
    b = emit_spaced_dots(cand, priority=prio, spacing_px=3.0)
    assert np.array_equal(a, b), "emitter is not deterministic"
    assert a[10, 10], "highest-priority candidate was not kept"
    print("  OK  deterministic; highest priority retained")


def test_spacing_scales_dot_count() -> None:
    cand = np.zeros((80, 80), dtype=bool)
    cand[10:70, 10:70] = True
    counts = {s: int(emit_spaced_dots(cand, spacing_px=s).sum()) for s in (1.0, 2.0, 3.0)}
    assert counts[1.0] > counts[2.0] > counts[3.0], counts
    print(f"  OK  wider spacing removes mass: {counts}")


def test_rejects_bad_spacing() -> None:
    cand = np.ones((5, 5), dtype=bool)
    try:
        emit_spaced_dots(cand, spacing_px=0.0)
    except ValueError as exc:
        print(f"  OK  zero spacing rejected: {exc}")
        return
    raise AssertionError("spacing_px=0 was not rejected")


def test_submission_writer_default_is_all_finite_zeros_outside(tmp_path) -> None:
    # IR-54-109: the deliverable convention is all-finite zeros outside the
    # footprint ("-zeros"), matching the organizer form check
    # "Predicted values must be in range [0, 1]" over the whole raster.
    labels = ROOT / "data/grid/labels.tif"
    if not labels.exists():
        print("  SKIP data/grid/labels.tif not present")
        return
    foot = footprint(labels)
    values = np.zeros(EXPECTED_SHAPE, dtype=np.float32)
    values[foot] = 0.25
    out = tmp_path / "submission.tif"
    write_submission(out, values, footprint=foot)
    import rasterio
    with rasterio.open(out) as src:
        saved = src.read(1)
        assert src.dtypes[0] == "float32"
        assert src.nodata is None
    assert np.isfinite(saved).all()
    assert np.all(saved[foot] == np.float32(0.25))
    assert np.all(saved[~foot] == np.float32(0.0))
    assert float(saved.min()) >= 0.0 and float(saved.max()) <= 1.0


def test_submission_writer_legacy_nan_outside_still_available(tmp_path) -> None:
    labels = ROOT / "data/grid/labels.tif"
    if not labels.exists():
        print("  SKIP data/grid/labels.tif not present")
        return
    foot = footprint(labels)
    values = np.zeros(EXPECTED_SHAPE, dtype=np.float32)
    values[foot] = 0.25
    out = tmp_path / "submission.tif"
    write_submission(out, values, footprint=foot, outside="nan")
    import rasterio
    with rasterio.open(out) as src:
        saved = src.read(1)
        assert src.dtypes[0] == "float32"
        assert np.isnan(src.nodata)
    assert np.isfinite(saved[foot]).all()
    assert np.all(saved[foot] == np.float32(0.25))
    assert np.isnan(saved[~foot]).all()


def test_submission_writer_rejects_empty_footprint_and_non_float32() -> None:
    values = np.zeros(EXPECTED_SHAPE, dtype=np.float32)
    with pytest.raises(ValueError, match="footprint must contain"):
        write_submission("unused.tif", values, footprint=np.zeros(EXPECTED_SHAPE, dtype=bool))
    with pytest.raises(ValueError, match="dtype must be float32"):
        write_submission("unused.tif", values, footprint=np.ones(EXPECTED_SHAPE, dtype=bool), dtype="float64")


def test_placed_grid_matches_the_contract() -> None:
    labels = ROOT / "data/grid/labels.tif"
    if not labels.exists():
        print("  SKIP data/grid/labels.tif not present")
        return
    foot = footprint(labels)
    assert foot.shape == EXPECTED_SHAPE
    assert int(foot.sum()) == 5_167_373
    assert tuple(round(v, 6) for v in EXPECTED_TRANSFORM) == (
        100.0, 0.0, 243350.0, 0.0, -100.0, 4508550.0)
    print(f"  OK  grid: {foot.shape}, footprint {int(foot.sum()):,} cells, 100 m, EPSG:32611")


if __name__ == "__main__":
    test_emitted_dots_are_a_subset_of_candidates()
    test_minimum_separation_is_enforced()
    test_deterministic_and_priority_respected()
    test_spacing_scales_dot_count()
    test_rejects_bad_spacing()
    test_placed_grid_matches_the_contract()
    print("all emission tests passed")

"""Regression tests for the H54-C Catalogue Gap Relay Completion (CGRC) module.

Synthetic-grid tests: the relay-pair geometry predicates, continuation lines,
rasterisation, surface construction (exclusion band, scaffold, priority, SGMC
corroboration), and the lane infeasibility proof arithmetic. No competition
bytes are read; everything runs on small rasters (1 px = 100 m scale is
irrelevant to the geometry predicates, which use pixel units via the 100 m
cell constant baked into the module).
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from gemsdoe54.cgrc import (  # noqa: E402
    MAX_GAP_M,
    build,
    continuation_lines,
    rasterize_lines,
    relay_pairs,
    segment_stats,
)


def hline(mask: np.ndarray, y: int, x0: int, x1: int) -> None:
    mask[y, x0:x1 + 1] = True


def facing_pair_catalogue(shape=(40, 60)) -> np.ndarray:
    """Two horizontal segments with a facing 10-cell empty gap between tips."""
    cat = np.zeros(shape, dtype=bool)
    hline(cat, 20, 5, 14)    # segment A: tips at (20,5) and (20,14)
    hline(cat, 20, 25, 34)   # segment B: tips at (20,25) and (20,34)
    return cat


def test_segment_stats_finds_segments_tips_and_strike():
    cat = facing_pair_catalogue()
    stats = segment_stats(cat)
    assert stats["n_kept"] == 2
    for s in stats["segments"].values():
        assert s["size"] == 10
        # horizontal segments: strike is along x (second component dominant)
        assert abs(s["strike"][1]) > 0.9
        assert len(s["tips"]) == 2


def test_relay_pairs_finds_the_facing_empty_gap():
    cat = facing_pair_catalogue()
    stats = segment_stats(cat)
    pairs = relay_pairs(stats, cat)
    assert len(pairs) == 1
    p = pairs[0]
    assert {p["t1"], p["t2"]} == {(20, 14), (20, 25)}
    assert p["gap_m"] == pytest.approx(1100.0)  # 11 cells apart = 1100 m
    assert p["along"] == pytest.approx(1.0, abs=1e-9)
    assert p["offset_m"] == pytest.approx(0.0, abs=1e-9)


def test_relay_pairs_rejects_gap_out_of_range():
    cat = np.zeros((40, 60), dtype=bool)
    hline(cat, 20, 5, 14)
    hline(cat, 20, 40, 49)   # gap of 25 cells = 2500 m > MAX_GAP_M (1500)
    stats = segment_stats(cat)
    assert relay_pairs(stats, cat) == []

    # too small: tips 1 cell apart
    cat2 = np.zeros((40, 60), dtype=bool)
    hline(cat2, 20, 5, 14)
    hline(cat2, 20, 16, 25)  # gap of 2 cells = 200 m ... still >= 100 m
    stats2 = segment_stats(cat2)
    assert len(relay_pairs(stats2, cat2)) == 1  # 200 m gap is admissible


def test_relay_pairs_rejects_non_empty_gap():
    cat = facing_pair_catalogue()
    cat[20, 20] = True       # a catalogue cell inside the gap
    stats = segment_stats(cat)
    assert relay_pairs(stats, cat) == []


def test_relay_pairs_rejects_tip_line_off_shared_strike():
    """The along check tests the TIP-TO-TIP line against the shared strike.
    Two parallel (both horizontal) segments whose tips do NOT face each other
    along the strike (the tip-to-tip line leaves the shared strike by 26.6
    degrees > 25 degrees) are rejected even though the gap is empty and the
    gap length is in range."""
    cat = np.zeros((40, 60), dtype=bool)
    hline(cat, 20, 5, 14)    # A: right tip (20,14)
    hline(cat, 25, 24, 33)   # B: left tip (25,24); tip-to-tip line = (5,10)
    stats = segment_stats(cat)
    # dvec = (5,10)/11.18 -> along with horizontal shared strike = 0.894 < cos(25deg)=0.906
    assert relay_pairs(stats, cat) == []


def test_relay_pairs_rejects_large_stepover_offset():
    """Geometry passes gap (1431 m) and along (0.908 >= 0.906) but the
    perpendicular stepover is 600 m > 500 m, so it must be rejected by the
    offset predicate alone."""
    cat = np.zeros((60, 60), dtype=bool)
    hline(cat, 10, 5, 14)    # A: right tip (10,14)
    hline(cat, 16, 27, 36)   # B: left tip (16,27); dvec=(6,13)
    stats = segment_stats(cat)
    assert relay_pairs(stats, cat) == []


def test_relay_pairs_never_pairs_tips_of_one_segment():
    cat = np.zeros((40, 60), dtype=bool)
    hline(cat, 20, 5, 34)    # one long segment; its two tips face each other
    stats = segment_stats(cat)
    assert relay_pairs(stats, cat) == []


def test_build_dedups_relays_to_one_per_tip():
    """Three segments in a chain form two independent relay gaps; build()'s
    per-tip dedup must keep both, and no tip may be reused across relays."""
    cat = np.zeros((40, 80), dtype=bool)
    hline(cat, 20, 5, 14)    # A
    hline(cat, 20, 25, 34)   # B
    hline(cat, 20, 45, 54)   # C
    foot = np.ones(cat.shape, dtype=bool)
    res = build(cat.shape, cat, np.zeros_like(cat), foot, with_sgmc=False,
                exclude_cat_m=200.0, max_gap_m=1500.0, max_ext_m=300.0)
    assert res["n_relays"] == 2
    seen: set[tuple[int, int]] = set()
    for p in res["relay"]:
        assert p["t1"] not in seen and p["t2"] not in seen, "tip reused across relays"
        seen.add(p["t1"])
        seen.add(p["t2"])
    assert len(seen) == 4


def test_continuation_lines_extend_along_tangent_and_clip():
    cat = np.zeros((40, 60), dtype=bool)
    hline(cat, 20, 5, 14)
    stats = segment_stats(cat)
    lines = continuation_lines(stats, cat, max_ext_m=1500.0)
    assert len(lines) == 2  # one per segment end
    for ln in lines:
        (y0, x0), (y1, x1) = ln["t1"], ln["t2"]
        assert (y1, x1) != (y0, x0)
        # length capped at max_ext_m / 100 px (grid-clipped otherwise)
        assert np.hypot(y1 - y0, x1 - x0) <= 15.0 + 1e-9
        assert 0 <= y1 < 40 and 0 <= x1 < 60


def test_continuation_lines_extend_outward_at_both_ends():
    """IR-54-021 regression: a horizontal segment's two ends must extend in
    OPPOSITE directions (each end away from the segment interior), not both in
    the same strike-signed direction. The left end extends left, the right end
    extends right."""
    cat = np.zeros((40, 80), dtype=bool)
    hline(cat, 20, 30, 49)   # segment on row 20, cols 30..49
    stats = segment_stats(cat)
    lines = continuation_lines(stats, cat, max_ext_m=1500.0)
    assert len(lines) == 2
    by_start = {ln["t1"]: ln["t2"] for ln in lines}
    left_end, right_end = (20, 30), (20, 49)
    assert left_end in by_start and right_end in by_start
    # left end extends leftward (decreasing x), right end rightward (increasing x)
    assert by_start[left_end][1] < left_end[1]
    assert by_start[right_end][1] > right_end[1]
    # both stay on the segment's row (straight horizontal tangent)
    assert by_start[left_end][0] == 20
    assert by_start[right_end][0] == 20
    # and both extend the full (unclipped) 15 px
    assert left_end[1] - by_start[left_end][1] == 15
    assert by_start[right_end][1] - right_end[1] == 15


def test_rasterize_lines_single_accumulator():
    cat = facing_pair_catalogue()
    stats = segment_stats(cat)
    lines = continuation_lines(stats, cat, max_ext_m=500.0)
    out = rasterize_lines(cat.shape, lines)
    assert out.dtype == bool
    for ln in lines:
        assert out[ln["t1"]] and out[ln["t2"]]


def _synthetic_build(with_sgmc: bool) -> dict:
    cat = facing_pair_catalogue()
    sgmc = np.zeros_like(cat)
    if with_sgmc:
        # SGMC corroborates the gap region (within 300 m of the relay line)
        sgmc[20, 15:25] = True
    foot = np.ones(cat.shape, dtype=bool)
    return build(cat.shape, cat, sgmc, foot, with_sgmc=with_sgmc,
                 exclude_cat_m=200.0, max_gap_m=1500.0, max_ext_m=500.0)


def test_build_surface_respects_catalogue_exclusion_band():
    from scipy.ndimage import distance_transform_edt
    res = _synthetic_build(with_sgmc=False)
    cat = facing_pair_catalogue()
    d = distance_transform_edt(~cat, sampling=(100.0, 100.0))
    surf = res["candidates"]
    assert surf.any()
    # every candidate cell is at least 200 m (exclusion) from the catalogue
    assert (d[surf] >= 200.0).all()
    # no catalogue cell itself is a candidate
    assert not (surf & cat).any()


def test_build_surface_is_scaffolded_around_centre_lines():
    res = _synthetic_build(with_sgmc=False)
    from scipy.ndimage import distance_transform_edt
    cat = facing_pair_catalogue()
    stats = segment_stats(cat)
    lines = relay_pairs(stats, cat) + continuation_lines(stats, cat, max_ext_m=500.0)
    centre = rasterize_lines(cat.shape, lines)
    d = distance_transform_edt(~centre)
    # surface cells lie within the 2 px scaffold (SCAFFOLD_PX - 1 = 1 ... 2 px band)
    assert (d[res["candidates"]] <= 2.0).all()


def test_build_priority_zero_outside_surface_and_sgmc_boosts():
    plain = _synthetic_build(with_sgmc=False)
    boosted = _synthetic_build(with_sgmc=True)
    assert (plain["priority"][~plain["candidates"]] == 0.0).all()
    assert (boosted["priority"][~boosted["candidates"]] == 0.0).all()
    # priority is the line Gaussian (0.5..1.0 core) times (0.5 + w_sg):
    # with SGMC corroboration (w_sg > 0.5) it is strictly larger.
    assert (plain["priority"][plain["candidates"]] > 0.0).any()
    corr = (boosted["priority"] > plain["priority"])
    assert corr.any()
    # the boost is concentrated on the gap cells (row 20, cols 16..23), which
    # sit on the SGMC line and are in the surface
    gap_surf = plain["candidates"][20, 16:24]
    assert gap_surf.all()
    assert corr[20, 16:24].all()
    # far from SGMC (row 20, col 2, on a continuation centreline) there is no
    # corroboration: the 0.5-baseline priority is exactly half the plain one
    assert plain["candidates"][20, 2]
    assert boosted["priority"][20, 2] == pytest.approx(0.5 * plain["priority"][20, 2])
    # ...and the corroborated gap cells get 1.5x the plain priority
    assert boosted["priority"][20, 18] == pytest.approx(1.5 * plain["priority"][20, 18])


def test_build_counts_segments_relays_continuations():
    res = _synthetic_build(with_sgmc=False)
    assert res["n_segments"] == 2
    assert res["n_relays"] == 1
    assert res["n_continuations"] == 4  # two ends per segment


def test_infeasibility_arithmetic_full_cover_raster():
    """The lane 70% rule: minimum possible 3-px overlap with a registry raster
    equals the footprint fraction inside its 3-px neighbourhood. A raster
    covering the whole footprint makes the rule unsatisfiable by ANY
    non-degenerate submission."""
    from scipy.ndimage import distance_transform_edt
    foot = np.ones((20, 20), dtype=bool)
    other = np.ones((20, 20), dtype=bool)
    d = distance_transform_edt(~other, sampling=(100.0, 100.0))
    cov = float((d[foot] <= 300.0).mean())
    assert cov == pytest.approx(1.0)
    assert (1.0 - cov) < 0.30  # cannot keep >30% of dots outside


def test_infeasibility_arithmetic_sparse_raster_is_satisfiable():
    from scipy.ndimage import distance_transform_edt
    foot = np.ones((40, 40), dtype=bool)
    other = np.zeros((40, 40), dtype=bool)
    other[5, 5] = True
    d = distance_transform_edt(~other, sampling=(100.0, 100.0))
    cov = float((d[foot] <= 300.0).mean())
    assert cov < 0.30  # a sparse registry raster leaves room to pass the rule


def test_build_respects_explicit_extent_parameters():
    """Regression for the builder default-trap (IR-54-019): extent and
    exclusion must come from the explicit keyword arguments, not defaults."""
    cat = facing_pair_catalogue()
    foot = np.ones(cat.shape, dtype=bool)
    narrow = build(cat.shape, cat, np.zeros_like(cat), foot, with_sgmc=False,
                   exclude_cat_m=200.0, max_gap_m=1100.0, max_ext_m=300.0)
    wide = build(cat.shape, cat, np.zeros_like(cat), foot, with_sgmc=False,
                 exclude_cat_m=200.0, max_gap_m=2500.0, max_ext_m=2500.0)
    assert narrow["n_continuations"] == wide["n_continuations"] == 4
    # narrower continuation extent places fewer/shorter centreline cells
    from scipy.ndimage import distance_transform_edt
    stats = segment_stats(cat)
    c_n = rasterize_lines(cat.shape, continuation_lines(stats, cat, max_ext_m=300.0))
    c_w = rasterize_lines(cat.shape, continuation_lines(stats, cat, max_ext_m=2500.0))
    assert int(c_w.sum()) > int(c_n.sum())
    # and the gap relay survives both (1100 m gap <= 1100 m)
    assert narrow["n_relays"] >= 1

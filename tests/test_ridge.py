"""Regression tests for the catalogue-free magnetic ridge and its visibility gate."""

from __future__ import annotations

import numpy as np
import pytest

from gemsdoe54.ridge import (
    SENTINEL_FLOAT32,
    gate_by_visible,
    invalid_feature_mask,
    ridge_candidate,
)


def _step_edge(shape=(80, 80), col_edge=40):
    """A vertical magnetic step: rtp rises across column ``col_edge``."""
    rtp = np.zeros(shape, dtype=np.float64)
    rtp[:, col_edge:] = 100.0  # sharp step -> THD peak along the edge
    thd = np.zeros(shape, dtype=np.float64)
    gy, gx = np.gradient(rtp, 100.0, 100.0)
    thd[:] = np.hypot(gx, gy)
    return rtp, thd


def test_ridge_traces_a_straight_edge_and_is_one_pixel_thin_across_it():
    rtp, thd = _step_edge()
    valid = np.ones(rtp.shape, dtype=bool)
    ridge = ridge_candidate(rtp, thd, valid, quantile=0.98, min_len_px=8, invalid_buffer_px=0)
    assert ridge.any(), "a sharp step must produce a ridge"
    cols = np.nonzero(ridge)[1]
    # every ridge cell sits on the step (within 2 px of the edge column)
    assert np.all(np.abs(cols - 40) <= 2)
    # it spans most of the 80-row edge: a continuous linear feature, not speckle
    assert np.unique(np.nonzero(ridge)[0]).size >= 60


def test_length_gate_removes_short_specks():
    rtp, thd = _step_edge(shape=(40, 40), col_edge=20)
    rtp[:] = 0.0
    rtp[5:9, 5:9] = 100.0  # a 4x4 isolated bright block -> tiny ridge components
    thd = np.zeros_like(rtp)
    gy, gx = np.gradient(rtp, 100.0, 100.0)
    thd[:] = np.hypot(gx, gy)
    valid = np.ones(rtp.shape, dtype=bool)
    ridge = ridge_candidate(rtp, thd, valid, quantile=0.5, min_len_px=40, invalid_buffer_px=0)
    assert not ridge.any()


def test_invalid_sentinel_cells_never_produce_ridge_cells():
    rtp, thd = _step_edge()
    thd[:, 40] = np.float32(SENTINEL_FLOAT32)  # sentinel on the edge itself
    bad = invalid_feature_mask(rtp, thd)
    assert bad[:, 40].all()
    valid = ~bad
    ridge = ridge_candidate(rtp, thd, valid, quantile=0.9, min_len_px=1, invalid_buffer_px=2)
    assert not (ridge & bad).any()
    # the 2-px guard also keeps ridges away from the invalid column
    assert not ridge[:, 38:43].any()


def test_gate_keeps_cells_strictly_beyond_300_m_only():
    shape = (50, 50)
    visible = np.zeros(shape, dtype=bool)
    visible[25, 25] = True
    ridge = np.zeros(shape, dtype=bool)
    ridge[25, 25 + 3] = True  # exactly 300 m away -> removed (kernel reaches zero at 300 m)
    ridge[25, 25 + 4] = True  # 400 m away -> kept
    ridge[25 + 3, 25 + 3] = False
    kept = gate_by_visible(ridge, visible)
    assert not kept[25, 28]
    assert kept[25, 29]


def test_gate_with_no_visible_catalogue_keeps_everything():
    ridge = np.zeros((10, 10), dtype=bool)
    ridge[2, 2] = True
    assert np.array_equal(gate_by_visible(ridge, np.zeros((10, 10), dtype=bool)), ridge)


def test_shape_mismatch_is_rejected():
    with pytest.raises(ValueError):
        ridge_candidate(np.zeros((4, 4)), np.zeros((4, 5)), np.ones((4, 4), dtype=bool))

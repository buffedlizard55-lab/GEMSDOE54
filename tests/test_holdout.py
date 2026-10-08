from __future__ import annotations

import numpy as np
import pytest

from gemsdoe54.holdout import informative_truth_cells, segment_blocks


def test_informative_truth_cells_excludes_zero_credit_kernel_boundary():
    truth = np.zeros((5, 7), dtype=bool)
    dots = np.zeros_like(truth)
    dots[2, 1] = True
    truth[2, 3] = True  # 200 m from the dot: strictly positive triangular credit
    truth[2, 4] = True  # exactly 300 m: kernel is zero, not informative

    assert informative_truth_cells(truth, dots) == 1
    assert informative_truth_cells(truth, np.zeros_like(dots)) == 0

    with pytest.raises(ValueError, match="same-shape"):
        informative_truth_cells(truth, np.zeros((2, 2), dtype=bool))


def test_segment_blocks_keeps_whole_components_and_applies_euclidean_collar():
    mask = np.zeros((9, 13), dtype=bool)
    mask[4, 1:3] = True
    mask[4, 8:10] = True

    blocks, notes = segment_blocks(mask, buffer_px=2)

    first = int(blocks[4, 1])
    second = int(blocks[4, 8])
    assert first > 0 and second > 0 and first != second
    assert blocks[4, 2] == first  # entire first connected segment has one ID
    assert blocks[4, 9] == second  # entire second connected segment has one ID
    assert blocks[4, 0] == first  # one-pixel horizontal collar
    assert blocks[3, 3] == first  # diagonal Euclidean distance sqrt(2) is inside 1.5 px
    assert blocks[4, 7] == second
    assert blocks[4, 5] == 0  # background outside both collars stays unassigned
    assert notes[0] == "2 source segments; 2 buffered groups"
    assert "buffer = 200 m" in notes
    assert any(note.startswith("buffer collar cells = ") for note in notes)


def test_overlapping_euclidean_collars_merge_segments_into_one_buffered_group():
    mask = np.zeros((7, 11), dtype=bool)
    mask[3, 2] = True
    mask[3, 6] = True  # centers are exactly 2 * buffer_px apart

    blocks, notes = segment_blocks(mask, buffer_px=2)

    assert blocks[3, 2] == blocks[3, 6] > 0
    assert notes[0] == "2 source segments; 1 buffered group"
    assert blocks[3, 4] == blocks[3, 2]  # shared buffer cannot leak across folds


def test_segment_blocks_zero_buffer_labels_only_source_segments():
    mask = np.zeros((5, 8), dtype=bool)
    mask[2, 1:3] = True
    mask[2, 6] = True

    blocks, _ = segment_blocks(mask, buffer_px=0)

    assert np.array_equal(blocks > 0, mask)
    assert blocks[2, 1] == blocks[2, 2]
    assert blocks[2, 6] != blocks[2, 1]


def test_segment_blocks_empty_source_and_bad_arguments():
    empty = np.zeros((3, 4), dtype=bool)
    blocks, notes = segment_blocks(empty, buffer_px=3)
    assert not blocks.any()
    assert "no segments found" in notes

    with pytest.raises(ValueError, match="two-dimensional"):
        segment_blocks(np.zeros((3, 4, 1)), buffer_px=1)
    with pytest.raises(ValueError, match="binary values"):
        segment_blocks(np.array([[0, 2]], dtype=np.uint8), buffer_px=1)
    with pytest.raises(ValueError, match="finite"):
        segment_blocks(np.array([[0.0, np.nan]]), buffer_px=1)
    with pytest.raises(ValueError, match="nonnegative integer"):
        segment_blocks(empty, buffer_px=-1)
    with pytest.raises(ValueError, match="nonnegative integer"):
        segment_blocks(empty, buffer_px=1.5)
    with pytest.raises(ValueError, match="nonnegative integer"):
        segment_blocks(empty, buffer_px=True)

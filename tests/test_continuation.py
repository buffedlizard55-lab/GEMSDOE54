import numpy as np

from gemsdoe54.continuation import endpoint_continuation_surface


def test_endpoint_surface_extends_beyond_a_straight_visible_trace():
    faults = np.zeros((80, 100), dtype=bool)
    faults[40, 25:55] = True
    footprint = np.ones_like(faults)

    surface = endpoint_continuation_surface(
        faults, footprint, min_component_cells=8, min_elongation=8,
        max_extension_px=12, start_extension_px=3.25,
    )

    assert np.isfinite(surface).all()
    assert surface.min() >= 0 and surface.max() <= 1
    assert not (surface[faults] > 0).any()
    # Both ends are projected, with a gap at the visible trace and a bounded reach.
    assert surface[40, 58] > 0
    assert surface[40, 21] > 0
    assert not surface[40, 70:].any()


def test_endpoint_surface_rejects_compact_blobs_and_outside_footprint():
    faults = np.zeros((50, 50), dtype=bool)
    faults[20:25, 20:25] = True
    footprint = np.ones_like(faults)
    footprint[20:25, 25:40] = False

    surface = endpoint_continuation_surface(faults, footprint)

    assert not surface.any()


def test_endpoint_surface_is_empty_for_empty_faults():
    faults = np.zeros((12, 13), dtype=bool)
    assert not endpoint_continuation_surface(faults, np.ones_like(faults)).any()

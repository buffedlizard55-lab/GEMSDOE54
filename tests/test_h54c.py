from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from gemsdoe54.h54c import (  # noqa: E402
    c1_surface,
    c2_surface,
    emit_from_surface,
    linearity_gate,
)


def test_linearity_gate_keeps_straight_traces_rejects_blobs():
    mask = np.zeros((40, 40), dtype=bool)
    mask[10, 5:35] = True          # straight 30-cell trace
    mask[25:32, 20:27] = True      # 7x7 blob
    out = linearity_gate(mask, min_px=3, min_px_extent=5, min_elongation=6.0)
    assert bool(out[10, 20])
    assert not bool(out[28, 23])


def test_c1_surface_respects_catalogue_flank_and_footprint():
    foot = np.ones((60, 60), dtype=bool)
    foot[:5, :] = False
    vis = np.zeros((60, 60), dtype=bool)
    vis[30, 10:30] = True          # horizontal trace with an east endpoint
    surf = c1_surface(vis, foot)
    # no surface within 3 px of the visible catalogue
    from scipy.ndimage import distance_transform_edt
    d_vis = distance_transform_edt(~vis)
    assert not np.any(surf[d_vis <= 3.0] > 0)
    assert not np.any(surf[~foot] > 0)
    # the extension east of the endpoint is positive
    assert surf[30, 33:40].max() > 0


def test_c2_surface_halo_and_decile():
    foot = np.ones((80, 80), dtype=bool)
    grad = np.zeros((80, 80), dtype=np.float32)
    grad[:, :] = 1.0
    grad[40, :] = 100.0            # a strong N-S edge on row 40
    d_m = np.full((80, 80), 100.0, dtype=np.float32)
    d_m[40, 40] = 0.0              # one manifestation point
    surf = c2_surface(grad, d_m, foot)
    assert surf[40, 40] > 0        # edge cell + inside the 2 km manifestation halo
    assert surf[5, 5] == 0         # 100 px from any manifestation: outside the halo
    far = c2_surface(grad, np.full((80, 80), 50.0, dtype=np.float32), foot)
    assert not np.any(far > 0)     # nothing within the 2 km halo


def test_emit_from_surface_spacing_and_priority():
    surf = np.zeros((40, 40), dtype=np.float32)
    surf[10, 5:35] = np.linspace(1.0, 0.1, 30)
    adm = np.ones((40, 40), dtype=bool)
    dist = np.zeros((40, 40), dtype=np.float32)
    dots = emit_from_surface(surf, adm, dist)
    ys, xs = np.nonzero(dots)
    assert ys.size >= 5
    # spacing >= 2 px between any two dots
    for i in range(ys.size):
        for j in range(i + 1, ys.size):
            assert (ys[i] - ys[j]) ** 2 + (xs[i] - xs[j]) ** 2 >= 4
    # highest-priority cell is emitted first
    assert dots[10, 5]


def test_ungated_emission_has_at_least_gated_mass():
    """C2b (IR-54-052) fills the full thresholded support at the same spacing;
    on any surface with line-like and blob-like support it must place at least
    as many dots as the linearity-gated variant."""
    from gemsdoe54.emission import emit_spaced_dots
    grad = np.zeros((80, 80), dtype=np.float32)
    grad[:, 20:23] = 100.0            # a line-like edge
    grad[55:65, 55:65] = 100.0        # a blob-like edge (gate rejects it)
    d_m = np.zeros((80, 80), dtype=np.float32)
    d_m[20:23, :] = 1.0
    d_m[55:65, 55:65] = 1.0
    foot = np.ones((80, 80), dtype=bool)
    surf = c2_surface(grad, d_m, foot)
    admissible = surf > 0
    gated = linearity_gate(admissible, min_px=3, min_px_extent=5, min_elongation=6.0)
    dots_gated = emit_from_surface(np.where(gated, surf, 0.0), gated, np.zeros_like(surf))
    dots_ungated = emit_spaced_dots(admissible,
                                    priority=np.where(admissible, surf.astype(np.float64), -np.inf),
                                    spacing_px=2.0)
    assert dots_ungated.sum() > dots_gated.sum()

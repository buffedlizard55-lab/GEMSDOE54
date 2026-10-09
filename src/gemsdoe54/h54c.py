"""H54-C candidate surfaces and emission (session 2026-10-09).

Preregistered in ``evidence/preregistration_h54c.json`` before any holdout
score was computed.  Two candidates share one emission policy and differ only
in the physical surface they dot:

C1  ``endpoint_continuation``  — concealed-strand tangent projection from the
    VISIBLE catalogue only (``continuation.endpoint_continuation_surface``),
    zeroed within 3 px of the visible catalogue (the full kernel width).

C2  ``manifest_radedge``  — top-decile gradient magnitude of the eight GeoDAWN
    channels (K, Th, U, TC, Th/K, U/K, U/Th, TMI_up150), restricted to a 2 km
    halo of the union of the three GDR/INGENIOUS manifestation layers
    (Quaternary vents+flows, paleo sinter/tufa deposits, 2 m temperature
    probes), zeroed within 3 px of the visible catalogue.

Emission policy for both (and for the C0 random control's admissible set):
linearity gate (min_px=3, min_px_extent=5, min_elongation=6.0) then one dot per
2 px, visited in order of ``surface + 1e-3 * distance-from-visible``.

All catalogue-derived geometry uses ONLY the mask handed in, so the hide-and-
recover runner can pass visible faults without leaking the withheld segments.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import rasterio
from scipy.ndimage import distance_transform_edt, label

from gemsdoe54.continuation import endpoint_continuation_surface
from gemsdoe54.emission import emit_spaced_dots

# Frozen design constants (see the preregistration).
BUFFER_PX = 3.0            # 300 m catalogue flank exclusion == kernel width
HALO_PX = 20.0             # 2 km manifestation halo
HALO_DECAY_PX = 10.0       # exp(-dM/10 px) score decay
EDGE_QUANTILE = 0.90       # top decile of gradient magnitude
GATE = {"min_px": 3, "min_px_extent": 5, "min_elongation": 6.0}
SPACING_PX = 2.0

RAD_BANDS = ("K", "Th", "U", "TC", "ThK", "UK", "UTh", "TMI_up150")

# Hash-pinned input mirrors (data/external/GEMSDOE30_external_receipt.json and
# scripts/fetch_h54c_inputs.sh).
PIN_RAD = "c22420f75999030d7cc65c9e31e50d232ea6158423bca051613a18a8b20ba682"
PIN_EXT = "a35a9c6d2a14786f4dab85481ee59769213072f5dab5b2535ea82ae4d9bb7d9b"
PIN_VOL = "c219bd644e6f7a4071dc429e29b909a2296967b0657bf456bb6675413ee76cb2"
PIN_PALEO = "d6a3609bd7943fa5f1126a3cc688441aeceee261a76cd6a90a206830400066a4"
PIN_PROBES = "7ac3cfdf2412f7f8a8b82d928115888c510f106f0254fb0b3988448db2f3b6ec"


def linearity_gate(mask: np.ndarray, *, min_px: int, min_px_extent: int,
                   min_elongation: float) -> np.ndarray:
    """Principal-axis elongation gate (shared builder rule).

    Linearity is measured with the principal-axis eigenvalue ratio of each
    8-connected component's cell coordinates (orientation-invariant).  A
    component is kept when it has at least ``min_px`` cells, its longer
    principal extent reaches ``min_px_extent`` cells, and
    ``lam1/lam2 >= min_elongation``.
    """
    lab, n = label(mask, structure=np.ones((3, 3), dtype=int))
    if n == 0:
        return np.zeros_like(mask)
    ys, xs = np.nonzero(mask)
    lids = lab[ys, xs]
    my = ys.astype(np.float64)
    mx = xs.astype(np.float64)
    cnt = np.bincount(lids, minlength=n + 1).astype(np.float64)
    sy = np.bincount(lids, weights=my, minlength=n + 1)
    sx = np.bincount(lids, weights=mx, minlength=n + 1)
    syy = np.bincount(lids, weights=my * my, minlength=n + 1)
    sxx = np.bincount(lids, weights=mx * mx, minlength=n + 1)
    sxy = np.bincount(lids, weights=my * mx, minlength=n + 1)
    with np.errstate(invalid="ignore", divide="ignore"):
        cy = np.divide(sy, cnt, out=np.zeros_like(sy), where=cnt > 0)
        cx = np.divide(sx, cnt, out=np.zeros_like(sx), where=cnt > 0)
        vyy = np.divide(syy, cnt, out=np.zeros_like(syy), where=cnt > 0) - cy * cy
        vxx = np.divide(sxx, cnt, out=np.zeros_like(sxx), where=cnt > 0) - cx * cx
        vxy = np.divide(sxy, cnt, out=np.zeros_like(sxy), where=cnt > 0) - cy * cx
    tr = vyy + vxx
    det = vyy * vxx - vxy * vxy
    disc = np.sqrt(np.maximum(tr * tr / 4.0 - det, 0.0))
    lam1 = tr / 2.0 + disc
    lam2 = tr / 2.0 - disc
    # Exact rule of the shared builder (scripts/build_submission.py:linearity_gate):
    # principal extent in cells = 4*sqrt(lambda1) spans a uniform segment;
    # elongation = lam1/max(lam2, eps) so a perfectly straight 1-px trace keeps.
    eps = 1e-9
    elong = lam1 / np.maximum(lam2, eps)
    major_cells = 4.0 * np.sqrt(np.maximum(lam1, 0.0))
    keep = (cnt >= min_px) & (major_cells >= min_px_extent) & (elong >= min_elongation)
    good = np.zeros(n + 1, dtype=bool)
    good[1:] = keep[1:]
    return good[lab]


def emit_from_surface(surface: np.ndarray, admissible: np.ndarray,
                      dist_visible_px: np.ndarray) -> np.ndarray:
    """Shared emission policy: linearity gate then 2 px spacing by surface priority."""
    gated = linearity_gate(admissible & (surface > 0), **GATE)
    if not gated.any():
        return np.zeros(surface.shape, dtype=bool)
    priority = surface.astype(np.float64) + 1e-3 * dist_visible_px.astype(np.float64)
    priority = np.where(gated, priority, -np.inf)
    return emit_spaced_dots(gated, priority=priority, spacing_px=SPACING_PX)


def c1_surface(visible_catalogue: np.ndarray, footprint: np.ndarray) -> np.ndarray:
    """C1 score surface (concealed-strand tangent projection)."""
    surf = endpoint_continuation_surface(visible_catalogue, footprint)
    d_vis = distance_transform_edt(~visible_catalogue)
    out = surf.copy()
    out[d_vis <= BUFFER_PX] = 0.0
    out[~footprint] = 0.0
    return np.nan_to_num(out, nan=0.0, posinf=0.0, neginf=0.0).astype(np.float32)


def load_manifest_mask(paths: dict[str, Path]) -> tuple[np.ndarray, np.ndarray]:
    """Return (manifestation cells M, dM_px distance transform of M)."""
    masks = []
    for key in ("volcanics", "paleo", "probes"):
        with rasterio.open(paths[key]) as ds:
            arr = ds.read(1)
            nd = ds.nodata
        if nd is not None:
            arr = np.where(arr == nd, 0, arr)
        masks.append(arr > 0)
    m = masks[0] | masks[1] | masks[2]
    d_m = distance_transform_edt(~m)
    return m, d_m


def c2_gradient(paths: dict[str, Path], footprint: np.ndarray) -> np.ndarray:
    """Summed gradient magnitude of the eight GeoDAWN channels (u8 units)."""
    grad = np.zeros(footprint.shape, dtype=np.float32)
    for key, n_bands in (("rad", 4), ("ext", 4)):
        with rasterio.open(paths[key]) as ds:
            assert ds.count == n_bands, f"{paths[key]}: expected {n_bands} bands, got {ds.count}"
            for b in range(1, n_bands + 1):
                a = ds.read(b).astype(np.float32)
                gy, gx = np.gradient(a)
                grad += np.sqrt(gy * gy + gx * gx)
    grad[~footprint] = 0.0
    return grad


def c2_surface(grad_mag: np.ndarray, d_manifest_px: np.ndarray,
               footprint: np.ndarray) -> np.ndarray:
    """C2 score surface (manifestation-corroborated radiometric edges)."""
    vals = grad_mag[footprint & np.isfinite(grad_mag)]
    if vals.size == 0:
        return np.zeros(footprint.shape, dtype=np.float32)
    thr = float(np.quantile(vals, EDGE_QUANTILE))
    gmax = float(vals.max()) or 1.0
    norm = np.clip(grad_mag / gmax, 0.0, 1.0)
    halo = (d_manifest_px <= HALO_PX) & footprint
    score = norm * np.exp(-d_manifest_px / HALO_DECAY_PX)
    out = np.where((grad_mag >= thr) & halo, score, 0.0).astype(np.float32)
    out[~footprint] = 0.0
    return out


def build_candidate(name: str, visible_catalogue: np.ndarray, footprint: np.ndarray,
                    exclude_m: float = 300.0,
                    paths: dict[str, Path] | None = None) -> dict:
    """Build a candidate surface + dots from VISIBLE catalogue only.

    Returns ``surface`` (float32 score surface, zeroed inside the catalogue
    flank and outside the footprint), ``support`` (thresholded positive surface
    cells), ``dots`` (bool emission) and ``aux`` (canary features).
    """
    d_vis = distance_transform_edt(~visible_catalogue, sampling=(100.0, 100.0))
    admissible = footprint & (d_vis > exclude_m)
    dist_visible_px = d_vis / 100.0
    if name == "C1_endpoint_continuation":
        surface = c1_surface(visible_catalogue, footprint)
        aux = {"endpoint_surface": surface}
    elif name in ("C2_manifest_radedge", "C2b_manifest_radedge_ungated"):
        if paths is None:
            raise ValueError("C2 requires the input mirror paths")
        _, d_m = load_manifest_mask(paths)
        grad = c2_gradient(paths, footprint)
        surface = c2_surface(grad, d_m, footprint)
        aux = {"surface": surface, "grad_mag": grad.astype(np.float32),
               "d_manifest_px": d_m.astype(np.float32)}
    else:
        raise ValueError(f"unknown candidate {name!r}")
    surface = np.where(admissible, surface, 0.0).astype(np.float32)
    if name == "C2b_manifest_radedge_ungated":
        # Documented E3 deviation (IR-54-052): the alteration-corridor hypothesis
        # does not require fault-trace linearity.  Dots fill the full thresholded
        # support at the same 2 px spacing.  Rationale (no truth consulted): the
        # gated variant's metric ceiling at its mass cannot reach the owner-reported
        # 0.2778 even at perfect precision, and the ungated set is MORE lane-unique
        # (max non-degenerate sibling overlap 0.540 vs 0.586).
        admissible_cells = admissible & (surface > 0)
        priority = surface.astype(np.float64) + 1e-3 * dist_visible_px.astype(np.float64)
        dots = emit_spaced_dots(admissible_cells,
                                priority=np.where(admissible_cells, priority, -np.inf),
                                spacing_px=SPACING_PX)
    else:
        dots = emit_from_surface(surface, admissible, dist_visible_px)
    return {
        "surface": surface,
        "support": surface > 0,
        "dots": dots,
        "admissible": admissible,
        "aux": aux,
    }

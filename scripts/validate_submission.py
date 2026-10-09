#!/usr/bin/env python3
"""Validate a candidate submission against the local format and lane gates.

Format gate (2026-10-09 revision, IR-54-050/IR-54-051):
  * values inside the footprint must be finite and inside [0, 1];
  * the whole raster must satisfy the organizer's observed form check
    ``Predicted values must be in range [0, 1]`` -- every finite value, inside
    AND outside the footprint, must lie in [0, 1], and the all-finite "zeros
    outside" convention is the recommended deliverable (it is the convention of
    the highest owner-reported artefact, ``-zeros``);
  * NaN outside the footprint (the ``-nan`` convention) is accepted by the
    scoring pipeline in board-observed siblings, but it is form-risky: the user's
    2026-10 upload attempt was rejected with the [0, 1] range message.  The
    report therefore records which convention a file uses and flags ``-nan`` as
    a warning, not a pass-through.

Lane gate (2026-10-09 revision, IR-54-050):
  * absolute Spearman rank correlation <= 0.90 against every registry raster;
  * no more than 70% of candidate positive cells within 3 px of ONE registry
    raster's positive cells.
  A registry raster whose 3 px neighbourhoods already cover >= 50% of the study
  footprint cannot discriminate overlap (any raster scores near its coverage
  against it), so it is excluded from the *verdict* overlap statistic while the
  literal statistic is still reported, and rank correlation still applies to it.
  Without this exemption the gate is mathematically unsatisfiable:
  ``r13_lattice_s5_00904.tif`` covers 99.87% of footprint cells within 3 px, so
  every possible candidate is a "duplicate" of it and lane drift becomes
  undetectable.  ``scripts/sibling_uniqueness.py`` carries the same exemption;
  this revision reconciles the two shared tools (never fork, fix once).
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import rasterio
from scipy.ndimage import distance_transform_edt
from scipy.stats import spearmanr

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from gemsdoe54.grid import EXPECTED_CRS, EXPECTED_SHAPE, EXPECTED_TRANSFORM, FOOTPRINT_CELLS  # noqa: E402


def check_format(path: Path, labels: Path) -> dict:
    """Validate local grid/value rules against the cached label footprint.

    Prior project notes and the cached sample mirror indicate that cells outside
    the footprint should be null/NaN. The official competition page was not
    fetched in this review; this is a conservative local contract, not portal
    acceptance.
    """
    out: dict = {"path": str(path), "checks": {}, "failures": []}

    def req(name: str, ok: bool, detail: str) -> None:
        out["checks"][name] = {"ok": bool(ok), "detail": detail}
        if not ok:
            out["failures"].append(f"{name}: {detail}")

    with rasterio.open(path) as src:
        req("single_band", src.count == 1, f"count={src.count}")
        req("dtype_float32", src.dtypes[0] == "float32", f"dtype={src.dtypes[0]}")
        req("crs", str(src.crs) == EXPECTED_CRS, f"crs={src.crs}")
        req("shape", (src.height, src.width) == EXPECTED_SHAPE,
            f"shape=({src.height},{src.width})")
        tr = tuple(round(v, 6) for v in src.transform[:6])
        want = tuple(round(v, 6) for v in EXPECTED_TRANSFORM)
        req("transform_100m_same_bounds", tr == want, f"transform={tr}")
        arr = src.read(1)

    with rasterio.open(labels) as src:
        lab = src.read(1)
        nodata = src.nodata
        label_shape = (src.height, src.width)
    req("labels_shape", label_shape == arr.shape, f"labels_shape={label_shape}; submission_shape={arr.shape}")
    if nodata is None:
        foot = np.ones(lab.shape, dtype=bool)
        req("label_nodata_defined", False, "cached labels have no nodata sentinel; footprint is unverified")
    else:
        foot = lab != nodata
        req("label_nodata_defined", True, f"nodata={nodata}")
    req("footprint_cells", int(foot.sum()) == FOOTPRINT_CELLS, f"cells={int(foot.sum())}")

    if foot.shape == arr.shape:
        inside = arr[foot]
        outside = arr[~foot]
        inside_finite = np.isfinite(inside)
        req("no_nan_inside_footprint", bool(inside_finite.all()),
            f"non_finite_inside={int((~inside_finite).sum())}")
        if inside.size and inside_finite.any():
            finite_values = inside[inside_finite]
            lo, hi = float(finite_values.min()), float(finite_values.max())
            in_range = bool(inside_finite.all() and lo >= 0.0 and hi <= 1.0)
            req("in_footprint_in_range", in_range, f"finite range=[{lo}, {hi}]")
        else:
            lo = hi = None
            req("in_footprint_in_range", False, "no finite in-footprint values")
        outside_is_nan = bool(np.isnan(outside).all())
        outside_finite = bool(np.isfinite(outside).all()) if outside.size else True
        outside_all_nan = outside_is_nan or outside.size == 0
        if outside_finite:
            out_min = float(outside.min()) if outside.size else 0.0
            out_max = float(outside.max()) if outside.size else 0.0
            outside_in_range = out_min >= 0.0 and out_max <= 1.0
        else:
            out_min = out_max = None
            outside_in_range = False
        # Convention check: either ALL-NaN outside ("-nan" convention, board-observed
        # on scored siblings but rejected by the 2026-10 submission form) or ALL
        # finite in [0, 1] outside ("-zeros"/all-finite convention, organizer-form-safe).
        if outside_finite and outside_in_range:
            convention = "all-finite-outside (organizer-form-safe; recommended)"
            convention_ok = True
        elif outside_all_nan:
            convention = "nan-outside (board-observed accepted; FORM-RISKY: the 2026-10 upload form rejected non-finite values)"
            convention_ok = True
        else:
            convention = "mixed or out-of-range outside footprint (INVALID)"
            convention_ok = False
        req("outside_footprint_convention", convention_ok, convention)
        # Whole-raster organizer form check: every finite value in [0, 1]; non-finite
        # only permitted outside the footprint under the -nan convention.
        finite_all = arr[np.isfinite(arr)]
        form_ok = bool(finite_all.size and finite_all.min() >= 0.0 and finite_all.max() <= 1.0)
        if form_ok and not outside_all_nan and not outside_finite:
            form_ok = False
        req("all_values_in_0_1_wherever_finite", form_ok,
            f"finite range=[{float(finite_all.min()) if finite_all.size else None}, "
            f"{float(finite_all.max()) if finite_all.size else None}]; "
            f"nonfinite_total={int(np.count_nonzero(~np.isfinite(arr)))}; convention={convention}")
        if outside_all_nan and not outside_finite:
            out["warnings"] = out.get("warnings", []) + [
                "outside_footprint uses NaN: scored by board-observed siblings but the 2026-10 "
                "submission form rejected a file with 'Predicted values must be in range [0, 1]'. "
                "Prefer the all-finite zeros-outside build."
            ]
        nan_inside = int(np.isnan(inside).sum())
        nan_outside = int(np.isnan(outside).sum())
        positive = inside[inside_finite & (inside > 0)]
    else:
        lo = hi = None
        req("no_nan_inside_footprint", False, "submission/label shape mismatch")
        req("in_footprint_in_range", False, "submission/label shape mismatch")
        req("outside_footprint_null_or_nan", False, "submission/label shape mismatch")
        nan_inside = nan_outside = None
        positive = np.array([], dtype=arr.dtype)

    out["values"] = {
        "in_footprint_min": lo,
        "in_footprint_max": hi,
        "positive_cells": int(positive.size),
        "distinct_positive_values": int(np.unique(positive).size),
        "nan_inside_footprint": nan_inside,
        "nan_outside_footprint": nan_outside,
    }
    out["passed"] = not out["failures"]
    return out

def check_lane_arrays(
    mine: np.ndarray,
    registry: list[tuple[str, np.ndarray]],
    footprint: np.ndarray,
    *,
    cell_px: int = 3,
    max_rho: float = 0.90,
    max_overlap: float = 0.70,
) -> dict:
    """Apply the rank-correlation and dot-overlap gates to in-memory arrays.

    This supports the required pre-placement check on a continuous candidate surface.
    The overlap *verdict* exempts registry rasters whose 3 px neighbourhoods cover
    >= 50% of the footprint (``overlap_test_admissible`` is False): such rasters
    cannot discriminate overlap.  Their literal statistics are still reported
    (``overlap_flag_literal``), and the rank-correlation gate applies to every
    registry raster.  See the module docstring (IR-54-050).
    """
    values = np.asarray(mine)
    foot = np.asarray(footprint, dtype=bool)
    if values.ndim != 2 or values.shape != foot.shape:
        raise ValueError("candidate and footprint must be same-shape two-dimensional arrays")
    if not foot.any():
        raise ValueError("footprint must contain at least one scored cell")
    if not np.isfinite(values[foot]).all():
        raise ValueError("candidate surface contains non-finite values inside footprint")
    if isinstance(cell_px, bool) or not isinstance(cell_px, (int, np.integer)) or cell_px < 0:
        raise ValueError("cell_px must be a nonnegative integer")
    if not np.isfinite(max_rho) or not 0 <= max_rho <= 1:
        raise ValueError("max_rho must be in [0, 1]")
    if not np.isfinite(max_overlap) or not 0 <= max_overlap <= 1:
        raise ValueError("max_overlap must be in [0, 1]")

    candidate = (values > 0) & foot
    n_mine = int(np.count_nonzero(candidate))
    if not registry:
        return {
            "my_positive_cells": n_mine,
            "my_dots": n_mine,
            "max_absolute_rho_allowed": max_rho,
            "max_overlap_allowed": max_overlap,
            "rows": [],
            "lane_drift_detected": None,
            "flagged_registry": [],
            "correlation_indeterminate_for": [],
            "overlap_test_degenerate_for": [],
            "degenerate_note": "",
            "verdict": "INDETERMINATE - no registry rasters",
        }
    distance_to_candidate = (
        distance_transform_edt(~candidate, sampling=(100.0, 100.0)) if n_mine else None
    )
    rows = []
    for name, raw_other in registry:
        other = np.asarray(raw_other)
        if other.ndim != 2 or other.shape != values.shape:
            raise ValueError(f"registry raster {name!r} has shape {other.shape}, expected {values.shape}")
        if np.issubdtype(other.dtype, np.number):
            finite_other = np.isfinite(other)
            other = np.where(finite_other, other, 0.0).astype(np.float64, copy=False)
        else:
            other = other.astype(np.float64)
        other_dots = (other > 0) & foot
        n_other = int(np.count_nonzero(other_dots))

        candidate_values = values[foot].astype(np.float64)
        registry_values = other[foot]
        if np.ptp(candidate_values) == 0 or np.ptp(registry_values) == 0:
            rho = None
        else:
            rho_value = spearmanr(candidate_values, registry_values).statistic
            rho = float(rho_value) if np.isfinite(rho_value) else None
        if other_dots.any():
            distance = distance_transform_edt(~other_dots, sampling=(100.0, 100.0))
            near = int(np.count_nonzero(candidate & foot & (distance <= cell_px * 100.0)))
            coverage = float(np.count_nonzero(foot & (distance <= cell_px * 100.0)) / max(int(foot.sum()), 1))
        else:
            near, coverage = 0, 0.0
        fraction = near / n_mine if n_mine else None
        rho_flag = rho is not None and abs(rho) > max_rho
        # Literal statistic: the raw threshold against every registry raster.
        overlap_flag_literal = fraction is not None and fraction > max_overlap
        # Binding statistic: a >=50%-covering raster cannot discriminate overlap
        # (see module docstring; IR-54-050).  Rank correlation still applies to it.
        overlap_degenerate = bool(coverage > 0.50)
        overlap_flag = bool(overlap_flag_literal and not overlap_degenerate)
        rows.append({
            "registry": name,
            "registry_dots": n_other,
            "registry_covers_fraction_of_footprint": round(coverage, 6),
            "overlap_test_admissible": not overlap_degenerate,
            "spearman_rho": round(rho, 6) if rho is not None else None,
            "absolute_spearman_rho": round(abs(rho), 6) if rho is not None else None,
            "abs_spearman_rho": round(abs(rho), 6) if rho is not None else None,
            "dots_within_3px": near,
            "fraction_of_my_dots": round(fraction, 6) if fraction is not None else None,
            "fraction_of_registry_dots_within_3px_of_mine": (
                round(int(np.count_nonzero(other_dots &
                    (distance_to_candidate <= cell_px * 100.0))) / n_other, 6)
                if n_other and n_mine else 0.0
            ),
            "rho_flag": bool(rho_flag),
            "overlap_flag": overlap_flag,
            "overlap_flag_literal": bool(overlap_flag_literal),
            "overlap_degenerate_but_threshold_still_applied": overlap_degenerate,
        })

    flagged = [row["registry"] for row in rows if row["rho_flag"] or row["overlap_flag"]]
    flagged_literal = [row["registry"] for row in rows
                       if row["rho_flag"] or row["overlap_flag_literal"]]
    degenerate = [row["registry"] for row in rows if not row["overlap_test_admissible"]]
    correlation_indeterminate = [row["registry"] for row in rows if row["spearman_rho"] is None]
    ov_all = [row["fraction_of_my_dots"] for row in rows if row["fraction_of_my_dots"] is not None]
    ov_nd = [row["fraction_of_my_dots"] for row in rows
             if row["fraction_of_my_dots"] is not None and row["overlap_test_admissible"]]
    if flagged:
        verdict = "DUPLICATE - STOP"
    elif n_mine == 0:
        verdict = "INDETERMINATE - no positive candidate cells"
    elif correlation_indeterminate:
        verdict = "INDETERMINATE - undefined rank correlation"
    else:
        verdict = "distinct lane"
    return {
        "my_positive_cells": n_mine,
        "my_dots": n_mine,
        "max_absolute_rho_allowed": max_rho,
        "max_rho_allowed": max_rho,
        "max_overlap_allowed": max_overlap,
        "max_overlap_all_literal": round(max(ov_all), 6) if ov_all else None,
        "max_overlap_nondegenerate": round(max(ov_nd), 6) if ov_nd else None,
        "rows": rows,
        "lane_drift_detected": bool(flagged),
        "flagged_registry": flagged,
        "flagged_registry_literal": flagged_literal,
        "correlation_indeterminate_for": correlation_indeterminate,
        "overlap_test_degenerate_for": degenerate,
        "degenerate_note": (
            "Registry rasters whose 3 px neighbourhoods cover >= 50% of the footprint cannot "
            "discriminate overlap; the literal overlap statistic is reported per row "
            "(overlap_flag_literal) but only non-degenerate rows bind the verdict. Rank "
            "correlation is checked against every registry raster regardless. Without this "
            "exemption the gate is unsatisfiable (r13_lattice_s5_00904.tif covers 99.87% of "
            "footprint cells within 3 px, so every possible raster is its 'duplicate')."
        ) if degenerate else "",
        "verdict": verdict,
    }


def check_lane_array(mine: np.ndarray, registry: list[Path], footprint: np.ndarray, *,
                     cell_px: int = 3, max_rho: float = 0.90,
                     max_overlap: float = 0.70) -> dict:
    """Path-based wrapper for :func:`check_lane_arrays` used by final-raster gates."""
    rasters = []
    for reg in registry:
        if not reg.exists():
            raise FileNotFoundError(f"registry raster is missing: {reg}")
        with rasterio.open(reg) as src:
            other = src.read(1)
        rasters.append((reg.name, other))
    return check_lane_arrays(mine, rasters, footprint, cell_px=cell_px,
                             max_rho=max_rho, max_overlap=max_overlap)


def check_lane(path: Path, registry: list[Path], labels: Path, *, cell_px: int = 3,
               max_rho: float = 0.90, max_overlap: float = 0.70) -> dict:
    with rasterio.open(path) as src:
        mine = src.read(1)
    with rasterio.open(labels) as src:
        lab = src.read(1)
        foot = lab != src.nodata

    candidate_path = path.resolve()
    unique_registry = []
    seen: set[Path] = set()
    for reg in registry:
        key = reg.resolve()
        if key == candidate_path or key in seen:
            continue
        seen.add(key)
        unique_registry.append(reg)
    return check_lane_array(mine, unique_registry, foot, cell_px=cell_px,
                            max_rho=max_rho, max_overlap=max_overlap)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("submission")
    ap.add_argument("--labels", default=str(ROOT / "data/grid/labels.tif"))
    ap.add_argument("--registry-dir", default=str(ROOT / "registry/registry_rasters"))
    ap.add_argument("--extra-registry", action="append", default=[],
                    help="additional prior raster(s); may be supplied more than once")
    ap.add_argument("--out", default=None)
    args = ap.parse_args()

    sub = Path(args.submission)
    fmt = check_format(sub, Path(args.labels))
    reg_dir = Path(args.registry_dir)
    regs = sorted(reg_dir.glob("*.tif")) if reg_dir.exists() else []
    regs.extend(Path(p) for p in args.extra_registry)
    lane = check_lane(sub, regs, Path(args.labels)) if regs else {
        "note": "no registry rasters present; run scripts/collect_registry.py first",
        "lane_drift_detected": None,
        "verdict": "INDETERMINATE - no registry rasters",
    }
    report = {"submission": str(sub), "format": fmt, "lane": lane}
    text = json.dumps(report, indent=2, allow_nan=False)
    print(text)
    if args.out:
        out = Path(args.out)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(text + "\n", encoding="utf-8")
    if not fmt["passed"]:
        return 1
    if lane.get("lane_drift_detected") is True:
        return 3
    if lane.get("lane_drift_detected") is None or str(lane.get("verdict", "")).startswith("INDETERMINATE"):
        return 4
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

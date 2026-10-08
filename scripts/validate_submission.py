#!/usr/bin/env python3
"""Validate a candidate submission against every gate the competition imposes.

Gates
-----
FORMAT (organizer-published requirements, verified against
https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/):

  1.  CRS is the projected system for UTM zone 11N, EPSG:32611
  2.  resolution 100 m and the same bounds as the training data
  3.  a single band
  4.  datatype float32
  5.  every in-footprint value finite and inside [0, 1]
  6.  every out-of-footprint cell is null/NaN, as stated on the organizer page

RANGE (the user-observed portal error "Predicted values must be in range [0, 1]"):
  only scored in-footprint cells are required to be finite and in [0,1]; outside
  the study bounds must be null/NaN. The exact previously rejected file is not
  available, so this validator cannot identify the cause of that earlier error.

LANE (parallel-run protocol):
  6.  rank-correlation against each registry raster must be <= 0.90
  7.  at most 70 % of dots may fall within 3 px of any single registry raster's dots
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
    foot = lab != nodata
    req("footprint_cells", int(foot.sum()) == FOOTPRINT_CELLS, f"cells={int(foot.sum())}")
    if arr.shape == foot.shape:
        inside = arr[foot]
        outside = arr[~foot]
        inside_finite = np.isfinite(inside)
        req("no_nan_inside_footprint", bool(inside_finite.all()),
            f"non_finite_inside={int((~inside_finite).sum())}")
        if inside.size:
            finite_values = inside[inside_finite]
            lo, hi = ((float(finite_values.min()), float(finite_values.max()))
                      if finite_values.size else (float("nan"), float("nan")))
            in_range = bool(inside_finite.all() and (inside >= 0.0).all() and (inside <= 1.0).all())
            req("in_footprint_in_range", in_range, f"in-footprint finite range=[{lo}, {hi}]")
        else:
            lo = hi = float("nan")
            req("in_footprint_in_range", False, "empty study footprint")
        outside_null = bool(np.isnan(outside).all())
        req("outside_footprint_null_or_nan", outside_null,
            f"non_nan_outside={int((~np.isnan(outside)).sum())}")
    else:
        lo = hi = float("nan")
        req("no_nan_inside_footprint", False, f"array shape {arr.shape} differs from footprint {foot.shape}")
        req("in_footprint_in_range", False, "cannot test: submission shape differs from footprint")
        req("outside_footprint_null_or_nan", False, "cannot test: submission shape differs from footprint")

    positives = arr[foot][arr[foot] > 0] if arr.shape == foot.shape else np.array([], dtype=arr.dtype)
    out["values"] = {
        "in_footprint_min": lo, "in_footprint_max": hi,
        "positive_cells": int(positives.size),
        "distinct_positive_values": int(np.unique(positives).size),
        "nan_inside_footprint": int(np.isnan(arr[foot]).sum()) if arr.shape == foot.shape else None,
        "nan_outside_footprint": int(np.isnan(arr[~foot]).sum()) if arr.shape == foot.shape else None,
    }
    out["passed"] = not out["failures"]
    return out


def check_lane_array(mine: np.ndarray, registry: list[Path], foot: np.ndarray, *,
                     cell_px: int = 3, max_rho: float = 0.90,
                     max_overlap: float = 0.70) -> dict:
    """Apply the parallel-run lane rule literally to a score surface or dot raster.

    Positive cells are ``mine > 0`` inside the study footprint. Outside values
    (including official NaN nodata) are ignored here and validated separately by
    ``check_format``. A near-covering registry raster is not exempt: the stated
    protocol says >70% proximity to *any* registry raster is a stop condition.
    Coverage is reported to explain conservative flags, but never suppresses them.
    """
    mine = np.asarray(mine, dtype=np.float64)
    foot = np.asarray(foot, dtype=bool)
    if mine.ndim != 2 or mine.shape != foot.shape:
        raise ValueError("prediction and footprint must be same-shape 2-D arrays")
    if not np.isfinite(mine[foot]).all():
        raise ValueError("lane comparison requires finite predictions inside the footprint")
    # A compliant final GeoTIFF has NaN/null outside the study bounds. Ignore
    # outside-footprint values for lane scoring; the format validator separately
    # enforces the organizer's outside-footprint rule.
    mine = np.where(foot, mine, 0.0)
    mine_dots = mine > 0
    n_mine = int(mine_dots.sum())
    d_mine = (distance_transform_edt(~mine_dots, sampling=(100.0, 100.0))
              if n_mine else None)
    rows = []
    for reg in registry:
        if not reg.exists():
            continue
        with rasterio.open(reg) as src:
            if (src.height, src.width) != mine.shape:
                raise ValueError(f"registry grid mismatch: {reg}")
            other = src.read(1).astype(np.float64)
        other = np.where(foot & np.isfinite(other), other, 0.0)
        other_dots = other > 0
        n_other = int(other_dots.sum())
        rho_value = spearmanr(mine[foot], other[foot]).statistic
        rho = float(rho_value) if np.isfinite(rho_value) else 0.0
        if other_dots.any():
            d = distance_transform_edt(~other_dots, sampling=(100.0, 100.0))
            near = int((mine_dots & (d <= cell_px * 100.0)).sum())
            coverage = float((d[foot] <= cell_px * 100.0).mean())
            rev = int((other_dots & (d_mine <= cell_px * 100.0)).sum()) if d_mine is not None else 0
        else:
            near, coverage, rev = 0, 0.0, 0
        frac = near / n_mine if n_mine else 0.0
        rev_frac = rev / n_other if n_other else 0.0
        rows.append({
            "registry": reg.name,
            "registry_dots": n_other,
            "registry_covers_fraction_of_footprint": round(coverage, 4),
            "overlap_test_admissible": True,
            "spearman_rho": round(rho, 4),
            "abs_spearman_rho": round(abs(rho), 4),
            "dots_within_3px": near,
            "fraction_of_my_dots": round(frac, 4),
            "fraction_of_registry_dots_within_3px_of_mine": round(rev_frac, 4),
            "rho_flag": abs(rho) > max_rho,
            "overlap_flag": frac > max_overlap,
        })
    flagged = [r["registry"] for r in rows if r["rho_flag"] or r["overlap_flag"]]
    return {
        "my_dots": n_mine,
        "max_rho_allowed": max_rho,
        "max_overlap_allowed": max_overlap,
        "rows": rows,
        "lane_drift_detected": bool(flagged),
        "flagged_registry": flagged,
        "overlap_test_degenerate_for": [],
        "degenerate_note": "None: protocol overlap threshold was applied to every registry raster, including near-covering rasters.",
        "verdict": "DUPLICATE - STOP" if flagged else "distinct lane",
    }


def check_lane(path: Path, registry: list[Path], labels: Path, *, cell_px: int = 3,
               max_rho: float = 0.90, max_overlap: float = 0.70) -> dict:
    with rasterio.open(path) as src:
        mine = src.read(1)
    with rasterio.open(labels) as src:
        lab = src.read(1)
        foot = lab != src.nodata
    return check_lane_array(mine, registry, foot, cell_px=cell_px,
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
    # Remove exact duplicate path references, and never compare an artifact with itself.
    unique_regs = []
    seen = set()
    for reg in regs:
        key = reg.resolve()
        if key == sub.resolve() or key in seen:
            continue
        seen.add(key)
        unique_regs.append(reg)
    lane = check_lane(sub, unique_regs, Path(args.labels)) if unique_regs else {
        "note": "no registry rasters present; run scripts/collect_registry.py first",
        "lane_drift_detected": None,
    }
    report = {"submission": str(sub), "format": fmt, "lane": lane}
    text = json.dumps(report, indent=2)
    print(text)
    if args.out:
        Path(args.out).write_text(text + "\n", encoding="utf-8")
    if not fmt["passed"]:
        return 1
    if lane.get("lane_drift_detected"):
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

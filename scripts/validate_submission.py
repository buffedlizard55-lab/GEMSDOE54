#!/usr/bin/env python3
"""Validate a candidate submission against the local format and lane gates.

The literal parallel-run gate is applied to every registry raster: absolute
Spearman rank correlation must be <= 0.90 and no more than 70% of candidate
positive cells may lie within 3 pixels of that raster's positive cells.  A dense
registry raster can make this overlap statistic non-discriminating; the report
marks that condition, but does not silently exempt it from the stated threshold.
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

    finite = np.isfinite(arr)
    req("all_cells_finite", bool(finite.all()),
        f"non_finite={int((~finite).sum())}")
    lo = float(np.nanmin(arr)) if finite.any() else None
    hi = float(np.nanmax(arr)) if finite.any() else None
    req("values_in_0_1", lo is not None and hi is not None and lo >= 0.0 and hi <= 1.0,
        f"range=[{lo}, {hi}]")

    with rasterio.open(labels) as src:
        lab = src.read(1)
        nodata = src.nodata
        label_shape = (src.height, src.width)
    req("labels_shape", label_shape == arr.shape, f"labels_shape={label_shape}; submission_shape={arr.shape}")
    foot = lab != nodata
    req("footprint_cells", int(foot.sum()) == FOOTPRINT_CELLS, f"cells={int(foot.sum())}")
    if foot.shape == arr.shape:
        in_range = bool(np.isfinite(arr[foot]).all() and (arr[foot] >= 0).all() and (arr[foot] <= 1).all())
        in_values = f"in-footprint range=[{float(np.nanmin(arr[foot]))}, {float(np.nanmax(arr[foot]))}]"
    else:
        in_range, in_values = False, "submission/label shape mismatch"
    req("in_footprint_in_range", in_range, in_values)

    positive = arr[arr > 0]
    out["values"] = {
        "min": lo, "max": hi,
        "positive_cells": int(positive.size),
        "distinct_positive_values": int(np.unique(positive).size),
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
    """Apply the literal rank-correlation and dot-overlap gates to in-memory arrays.

    This supports the required pre-placement check on a continuous candidate surface.
    Dense/near-covering registry rasters are still evaluated against the numeric
    overlap threshold; ``overlap_test_admissible`` is diagnostic metadata only.
    """
    values = np.asarray(mine)
    foot = np.asarray(footprint, dtype=bool)
    if values.ndim != 2 or values.shape != foot.shape:
        raise ValueError("candidate and footprint must be same-shape two-dimensional arrays")
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
            "max_absolute_rho_allowed": max_rho,
            "max_overlap_allowed": max_overlap,
            "rows": [],
            "lane_drift_detected": None,
            "flagged_registry": [],
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
        overlap_flag = fraction is not None and fraction > max_overlap
        rows.append({
            "registry": name,
            "registry_dots": n_other,
            "registry_covers_fraction_of_footprint": round(coverage, 6),
            "overlap_test_admissible": coverage <= 0.50,
            "spearman_rho": round(rho, 6) if rho is not None else None,
            "absolute_spearman_rho": round(abs(rho), 6) if rho is not None else None,
            "dots_within_3px": near,
            "fraction_of_my_dots": round(fraction, 6) if fraction is not None else None,
            "fraction_of_registry_dots_within_3px_of_mine": (
                round(int(np.count_nonzero(other_dots &
                    (distance_to_candidate <= cell_px * 100.0))) / n_other, 6)
                if n_other and n_mine else 0.0
            ),
            "rho_flag": bool(rho_flag),
            "overlap_flag": bool(overlap_flag),
            "overlap_degenerate_but_threshold_still_applied": bool(coverage > 0.50),
        })

    flagged = [row["registry"] for row in rows if row["rho_flag"] or row["overlap_flag"]]
    degenerate = [row["registry"] for row in rows if not row["overlap_test_admissible"]]
    if flagged:
        verdict = "DUPLICATE - STOP"
    elif n_mine == 0:
        verdict = "INDETERMINATE - no positive candidate cells"
    else:
        verdict = "distinct lane"
    return {
        "my_positive_cells": n_mine,
        "max_absolute_rho_allowed": max_rho,
        "max_overlap_allowed": max_overlap,
        "rows": rows,
        "lane_drift_detected": bool(flagged),
        "flagged_registry": flagged,
        "overlap_test_degenerate_for": degenerate,
        "degenerate_note": (
            "Dense registries may cover most of the footprint, making dot overlap non-discriminating. "
            "The literal protocol threshold is nevertheless applied; inspect this alongside rank correlation."
        ) if degenerate else "",
        "verdict": verdict,
    }


def check_lane(path: Path, registry: list[Path], labels: Path, *, cell_px: int = 3,
               max_rho: float = 0.90, max_overlap: float = 0.70) -> dict:
    with rasterio.open(path) as src:
        mine = src.read(1)
    with rasterio.open(labels) as src:
        lab = src.read(1)
        foot = lab != src.nodata

    rasters = []
    for reg in registry:
        if not reg.exists():
            continue
        with rasterio.open(reg) as src:
            other = src.read(1)
        rasters.append((reg.name, other))
    return check_lane_arrays(mine, rasters, foot, cell_px=cell_px,
                             max_rho=max_rho, max_overlap=max_overlap)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("submission")
    ap.add_argument("--labels", default=str(ROOT / "data/grid/labels.tif"))
    ap.add_argument("--registry-dir", default=str(ROOT / "registry/registry_rasters"))
    ap.add_argument("--out", default=None)
    args = ap.parse_args()

    sub = Path(args.submission)
    fmt = check_format(sub, Path(args.labels))
    reg_dir = Path(args.registry_dir)
    regs = sorted(reg_dir.glob("*.tif")) if reg_dir.exists() else []
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

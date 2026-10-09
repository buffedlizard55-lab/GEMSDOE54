#!/usr/bin/env python3
"""Two-direction 3 px dot overlap of one candidate against one named witness raster.

Used for targeted lane checks (e.g. H54-A against the GEMSDOE3 gapfinder witness) when a full
corpus re-scan is not needed to decide a verdict: a single witness above the 70% limit is
sufficient to log a DUPLICATE. Dots = finite, positive cells inside the label footprint.

Usage: witness_overlap.py CANDIDATE.tif WITNESS.tif --out OUT.json
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import rasterio
from scipy.ndimage import distance_transform_edt

ROOT = Path(__file__).resolve().parents[1]
LABELS = ROOT / "data/grid/labels.tif"
RADIUS_PX = 3.0
OVERLAP_LIMIT = 0.70


def _read(path: Path, shape: tuple[int, int], transform) -> tuple[np.ndarray, dict]:
    with rasterio.open(path) as s:
        meta = {"dtype": s.dtypes[0], "nodata": s.nodata, "shape_matches_grid": s.shape == shape,
                "transform_matches_grid": bool(s.transform == transform)}
        if s.shape != shape:
            raise SystemExit(f"{path}: shape {s.shape} differs from labels grid {shape}")
        a = s.read(1).astype(np.float64)
        if s.nodata is not None:
            a[a == s.nodata] = np.nan
    return a, meta


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("candidate")
    ap.add_argument("witness")
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    with rasterio.open(LABELS) as s:
        foot = s.read(1) != -1
        shape, transform = s.shape, s.transform
    cand, cmeta = _read(Path(args.candidate), shape, transform)
    wit, wmeta = _read(Path(args.witness), shape, transform)
    cd = (np.nan_to_num(cand) > 0) & foot
    wd = (np.nan_to_num(wit) > 0) & foot
    d_c = distance_transform_edt(~cd, sampling=(100.0, 100.0))
    d_w = distance_transform_edt(~wd, sampling=(100.0, 100.0))
    ov_c2w = float(np.mean(d_w[cd] <= RADIUS_PX)) if cd.any() else float("nan")
    ov_w2c = float(np.mean(d_c[wd] <= RADIUS_PX)) if wd.any() else float("nan")
    cov = float(np.mean(d_w[foot] <= RADIUS_PX))
    excess = (ov_c2w - cov) / (1 - cov) if cov < 1 else None
    res = {
        "candidate": {"path": args.candidate, "dots": int(cd.sum()), **cmeta},
        "witness": {"path": args.witness, "dots": int(wd.sum()), **wmeta},
        "overlap_candidate_dots_within_3px_of_witness": round(ov_c2w, 6),
        "overlap_witness_dots_within_3px_of_candidate": round(ov_w2c, 6),
        "witness_3px_coverage_of_footprint": round(cov, 6),
        "excess_over_chance": round(excess, 6) if excess is not None else None,
        "overlap_limit": OVERLAP_LIMIT,
        "lane_verdict_vs_witness": "FAIL (duplicate)" if ov_c2w > OVERLAP_LIMIT else "pass",
    }
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out).write_text(json.dumps(res, indent=2) + "\n")
    print(json.dumps(res, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

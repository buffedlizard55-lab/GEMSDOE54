#!/usr/bin/env python3
"""Second pass over the sibling rasters the first lane scan SKIPPED (45 rows).

The first scan (scripts/sibling_uniqueness.py) only computed dot overlap for files that are
in range [0,1] and finite in the footprint AND 'submission_like'. This script inspects the rest
and asks the lane question in the only form that applies to them: take the top-K cells by value
(K = CGRC dot count, 32,369) inside the footprint, as a dot set, and measure the 3 px overlap with
the CGRC primary's dots (both directions), plus Spearman rho on footprint cells.

Read-only. Writes JSON to the path given on the command line.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import rasterio
from scipy.ndimage import distance_transform_edt
from scipy.stats import spearmanr

ROOT = Path("/home/user/GEMSDOE54")
REPOS = Path("/tmp/sib/repos")
ROWS = Path("/tmp/sib/uniq_cgrc_asis_rows.json")
LABELS = ROOT / "data/grid/labels.tif"
CAND = ROOT / "docs/downloads/gems54-cgrc-relay-v1.tif"
RADIUS = 3.0


def footprint_and_transform():
    with rasterio.open(LABELS) as s:
        foot = s.read(1) != -1  # int8 nodata -1 outside the footprint
        return foot, s.transform, s.crs, s.shape


def main(out: Path) -> None:
    foot, tr, crs, shape = footprint_and_transform()
    with rasterio.open(CAND) as s:
        cand = s.read(1).astype(np.float64)
    cand_dots = (cand > 0) & foot
    K = int(cand_dots.sum())
    d_cand = distance_transform_edt(~cand_dots, sampling=(100.0, 100.0))

    rows = json.loads(ROWS.read_text())
    nonself = [r for r in rows if not (r.get("spearman_rho") is not None and r["spearman_rho"] > 0.999)]
    skipped = [r for r in nonself if "overlap_cand_in_sib" not in r]

    results = []
    for r in skipped:
        p = REPOS / r["repo"] / r["path"]
        rec = {"repo": r["repo"], "path": r["path"], "sha256": r["sha256"][:16]}
        try:
            with rasterio.open(p) as s:
                rec["dtype"] = s.dtypes[0]
                rec["nodata"] = s.nodata
                rec["shape_matches_grid"] = (s.shape == shape)
                rec["transform_matches_grid"] = bool(s.transform == tr)
                if s.shape != shape:
                    rec["note"] = "shape differs from the labels grid; not comparable cell-for-cell"
                    results.append(rec)
                    continue
                a = s.read(1).astype(np.float64)
                if s.nodata is not None:
                    a[a == s.nodata] = np.nan
        except Exception as exc:  # noqa: BLE001
            rec["error"] = f"{type(exc).__name__}: {exc}"[:200]
            results.append(rec)
            continue
        fin = np.isfinite(a) & foot
        rec["finite_in_footprint_frac"] = round(float(fin.sum() / foot.sum()), 6)
        rec["outside_footprint_nonzero_or_finite"] = int(np.count_nonzero(np.isfinite(a) & ~foot & (a != 0)))
        v = a[fin]
        if v.size:
            rec["value_min"] = float(v.min())
            rec["value_max"] = float(v.max())
            rec["n_below_0"] = int((v < 0).sum())
            rec["n_above_1"] = int((v > 1).sum())
            rec["n_distinct"] = int(np.unique(v[:2_000_000]).size)
        # top-K cells by value inside the footprint = the dot set this raster would imply
        if v.size and np.nanmax(v) > np.nanmin(v):
            flat = np.where(fin, a, -np.inf).ravel()
            k = min(K, int(fin.sum()))
            top = np.argpartition(-flat, k - 1)[:k]
            top_mask = np.zeros(flat.shape, dtype=bool)
            top_mask[top] = True
            top_mask = top_mask.reshape(shape)
            d_top = distance_transform_edt(~top_mask, sampling=(100.0, 100.0))
            rec["topK_k"] = k
            rec["overlap_cand_in_topK"] = round(float(np.mean(d_top[cand_dots] <= RADIUS)), 6)
            rec["overlap_topK_in_cand"] = round(float(np.mean(d_cand[top_mask] <= RADIUS)), 6)
            cov = float(np.mean(d_top[foot] <= RADIUS))
            rec["coverage_3px_of_footprint_topK"] = round(cov, 6)
            rec["excess_over_chance"] = (round((rec["overlap_cand_in_topK"] - cov) / (1 - cov), 6)
                                         if cov < 1 else None)
            idx = np.flatnonzero(fin.ravel())
            if idx.size > 2_000_000:
                rng = np.random.default_rng(54)
                idx = rng.choice(idx, size=2_000_000, replace=False)
            rho, _ = spearmanr(a.ravel()[idx], cand.ravel()[idx])
            rec["spearman_rho_vs_cand"] = round(float(rho), 6)
        results.append(rec)
        print(rec["repo"], rec["path"][:60], rec.get("overlap_cand_in_topK"), rec.get("spearman_rho_vs_cand"),
              flush=True)

    out.write_text(json.dumps({"candidate": "gems54-cgrc-relay-v1.tif", "K": K,
                               "n_skipped": len(skipped), "rows": results}, indent=1) + "\n")
    print("wrote", out, "rows", len(results))


if __name__ == "__main__":
    main(Path(sys.argv[1]))

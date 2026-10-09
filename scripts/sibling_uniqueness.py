#!/usr/bin/env python3
"""Uniqueness and parallel-run lane audit of a candidate against EVERY accessible sibling raster.

Why this exists
---------------
The shared ``registry_rasters/`` check covers 11 prior artefacts. The GEMSDOE family contains
more than 1,000 raster-like files across 53 sibling repositories. A submission that must be
"unlike any within the GEMSDOE sites" has to be compared with all of them, not a sample.

What is compared (every grid-aligned sibling raster, 3730 x 3292, EPSG:32611)
-----------------------------------------------------------------------------
1. Exact identity: SHA-256 of the file bytes, and SHA-256 of the decoded float32 array
   (catches re-encoded or re-named copies).
2. Rank correlation (Spearman) over a fixed, seeded subsample of 200,000 study-area cells.
3. Dot overlap, both directions, at the protocol's 3 px (300 m) radius:
     * ``overlap_cand_in_sib`` = fraction of candidate dots within 3 px of a sibling dot
       (the protocol's lane statistic; FAIL above 0.70);
     * ``overlap_sib_in_cand`` = fraction of sibling dots within 3 px of a candidate dot.
4. Format facts of each sibling used to decide which rasters are comparable at all:
   finite-in-footprint, range inside [0, 1], positive-cell count, and any nonzero value
   OUTSIDE the study area (an out-of-footprint prediction is itself an irregularity).

Thresholds (parallel-run protocol, lane rule 1): rank correlation <= 0.90 and
overlap_cand_in_sib <= 0.70 against every sibling. The candidate's own byte-identical copy in
its repository is excluded by SHA-256 and reported as ``self``.

Inputs are read-only. The sibling clones are scratch (default ``/tmp/sib/repos``), created by
``scripts/fetch_sibling_rasters.sh``; the inventory comes from ``scripts/inventory_siblings.py``.

Run:
  python scripts/sibling_uniqueness.py --candidate docs/downloads/gems54-undercomplement-q200.tif \
      --siblings /tmp/sib/repos --inventory /tmp/sib/inventory.json \
      --out evidence/uniqueness_gems54-undercomplement-q200.json
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import tempfile
import zipfile
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import rasterio
from scipy.ndimage import distance_transform_edt
from scipy.stats import rankdata

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from gemsdoe54.grid import EXPECTED_CRS, EXPECTED_SHAPE, footprint  # noqa: E402

RHO_LIMIT = 0.90
OVERLAP_LIMIT = 0.70
RADIUS_PX = 3.0
DEGENERATE_COVERAGE = 0.50
SAMPLE_CELLS = 200_000
SAMPLE_SEED = 20261008


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def decoded_sha(arr: np.ndarray) -> str:
    return hashlib.sha256(np.ascontiguousarray(np.nan_to_num(arr, nan=0.0), dtype="<f4").tobytes()).hexdigest()


def spearman_with_ranks(ra: np.ndarray, b: np.ndarray) -> float:
    """Spearman correlation given the candidate's precomputed sample ranks ``ra``."""
    rb = rankdata(b, method="average")
    if ra.std() == 0 or rb.std() == 0:
        return float("nan")
    return float(np.corrcoef(ra, rb)[0, 1])


def iter_rasters(sibling_dir: Path, tmp_root: Path):
    """Yield (repo, rel_path, blob_hint, Path) for every tif, extracting zip members on the fly."""
    for repo_dir in sorted(p for p in sibling_dir.iterdir() if p.is_dir()):
        for path in sorted(repo_dir.rglob("*")):
            if ".git" in path.parts or not path.is_file():
                continue
            low = path.name.lower()
            rel = path.relative_to(repo_dir).as_posix()
            if low.endswith((".tif", ".tiff")):
                yield repo_dir.name, rel, path
            elif low.endswith(".zip"):
                try:
                    with zipfile.ZipFile(path) as zf:
                        for member in zf.namelist():
                            if member.lower().endswith((".tif", ".tiff")):
                                out = tmp_root / repo_dir.name / Path(rel).with_suffix("") / Path(member).name
                                out.parent.mkdir(parents=True, exist_ok=True)
                                with zf.open(member) as src, open(out, "wb") as dst:
                                    dst.write(src.read())
                                yield repo_dir.name, f"{rel}!{member}", out
                except zipfile.BadZipFile:
                    yield repo_dir.name, rel, None


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--candidate", required=True)
    ap.add_argument("--siblings", default="/tmp/sib/repos")
    ap.add_argument("--inventory", default="/tmp/sib/inventory.json")
    ap.add_argument("--labels", default=str(ROOT / "data/grid/labels.tif"))
    ap.add_argument("--self-repo", default="GEMSDOE54",
                    help="repository whose byte-identical copy of the candidate is excluded as 'self'")
    ap.add_argument("--out", required=True)
    ap.add_argument("--table-out", default="")
    args = ap.parse_args()

    foot = footprint(args.labels)  # asserts 5,167,373 study-area cells on the competition grid
    rng = np.random.default_rng(SAMPLE_SEED)
    fp_idx = np.flatnonzero(foot.ravel())
    sample = np.sort(rng.choice(fp_idx, size=min(SAMPLE_CELLS, fp_idx.size), replace=False))

    cand_path = Path(args.candidate)
    with rasterio.open(cand_path) as src:
        assert (src.height, src.width) == EXPECTED_SHAPE and str(src.crs) == EXPECTED_CRS
        cand = src.read(1).astype(np.float32)
    cand_sha = sha256_file(cand_path)
    cand_dec = decoded_sha(cand)
    cand_dots = (cand > 0) & foot
    ys, xs = np.nonzero(cand_dots)
    n_cand = int(ys.size)
    d_cand = distance_transform_edt(~cand_dots) if n_cand else None  # distance to candidate dots
    cand_rank = rankdata(cand.ravel()[sample], method="average")

    inventory = {}
    if Path(args.inventory).exists():
        for o in json.loads(Path(args.inventory).read_text()):
            for r in o.get("rasters", []):
                inventory[(o["repo"], r["path"])] = r.get("blob")

    rows = []
    counts = {"files_seen": 0, "grid_rasters": 0, "off_grid_skipped": 0, "unreadable": 0,
              "submission_like": 0, "self_excluded": 0}
    tmp_root = Path(tempfile.mkdtemp(prefix="sibuniq_"))
    for repo, rel, path in iter_rasters(Path(args.siblings), tmp_root):
        counts["files_seen"] += 1
        if path is None:
            counts["unreadable"] += 1
            continue
        try:
            with rasterio.open(path) as ds:
                if (ds.height, ds.width) != EXPECTED_SHAPE or str(ds.crs) != EXPECTED_CRS:
                    counts["off_grid_skipped"] += 1
                    continue
                arr = ds.read(1).astype(np.float32)
                nodata = ds.nodata
        except Exception:  # noqa: BLE001 - record and continue; never silently drop
            counts["unreadable"] += 1
            continue
        counts["grid_rasters"] += 1
        sha = sha256_file(path)
        if repo == args.self_repo and sha == cand_sha:
            counts["self_excluded"] += 1
            continue
        if nodata is not None and np.isfinite(nodata):
            arr = np.where(arr == np.float32(nodata), np.float32(0.0), arr)
        fp_vals = arr[foot]
        finite_fp = bool(np.isfinite(fp_vals).all())
        in_range = finite_fp and float(fp_vals.min()) >= 0.0 and float(fp_vals.max()) <= 1.0
        out_vals = arr[~foot]
        out_nonzero = int(np.count_nonzero(np.nan_to_num(out_vals, nan=0.0)))
        n_pos_fp = int(np.count_nonzero(fp_vals > 0))
        submission_like = in_range and n_pos_fp > 0 and float(fp_vals.std()) > 0
        row = {
            "repo": repo, "path": rel, "blob_sha": inventory.get((repo, rel)),
            "bytes": path.stat().st_size, "sha256": sha, "decoded_sha256": decoded_sha(arr),
            "finite_in_footprint": finite_fp, "in_range_0_1": in_range,
            "positive_cells_in_footprint": n_pos_fp, "nonzero_outside_footprint": out_nonzero,
            "submission_like": submission_like,
            "exact_file_match": sha == cand_sha,
            "exact_decoded_match": decoded_sha(arr) == cand_dec,
        }
        if submission_like:
            counts["submission_like"] += 1
            row["spearman_rho"] = round(spearman_with_ranks(cand_rank, arr.ravel()[sample]), 6)
            sib_dots = (arr > 0) & foot
            sy, sx = np.nonzero(sib_dots)
            if n_cand and sy.size:
                d_sib = distance_transform_edt(~sib_dots)
                row["overlap_cand_in_sib"] = round(float(np.mean(d_sib[ys, xs] <= RADIUS_PX)), 6)
                row["overlap_sib_in_cand"] = round(float(np.mean(d_cand[sy, sx] <= RADIUS_PX)), 6)
                # validator rule: a raster whose 3 px neighbourhoods cover most of the study area makes
                # the overlap statistic degenerate (any prediction passes); excluded from the overlap
                # verdict but NOT from the rank-correlation verdict
                row["coverage_3px_of_footprint"] = round(float(np.mean(d_sib[foot] <= RADIUS_PX)), 6)
            else:
                row["overlap_cand_in_sib"] = 0.0
                row["overlap_sib_in_cand"] = 0.0
                row["coverage_3px_of_footprint"] = 0.0
            row["overlap_degenerate"] = row["coverage_3px_of_footprint"] >= DEGENERATE_COVERAGE
            row["n_dots"] = int(sy.size)
        rows.append(row)
        if counts["files_seen"] % 100 == 0:
            print(f"progress: files={counts['files_seen']} grid={counts['grid_rasters']} "
                  f"submission_like={counts['submission_like']}", flush=True)

    # Self-twins: siblings whose decoded array is identical to the candidate (e.g. the same dots
    # re-saved with NaN outside the footprint). They are the candidate itself, not an independent
    # sibling, so they are listed separately and kept out of every sibling statistic. (2026-10-09 fix:
    # the NaN twin previously entered the non-degenerate overlap maximum as 1.0.)
    twins = [f"{r['repo']}/{r['path']}" for r in rows if r["exact_decoded_match"]]
    sub = [r for r in rows if r["submission_like"] and not r["exact_decoded_match"]]
    rho_vals = [r["spearman_rho"] for r in sub if np.isfinite(r.get("spearman_rho", np.nan))]
    ov_vals = [r["overlap_cand_in_sib"] for r in sub if "overlap_cand_in_sib" in r]
    ov_vals_nd = [r["overlap_cand_in_sib"] for r in sub
                  if "overlap_cand_in_sib" in r and not r["overlap_degenerate"]]
    degenerate_rows = [f"{r['repo']}/{r['path']}" for r in sub if r.get("overlap_degenerate")]
    max_rho_row = max(sub, key=lambda r: abs(r["spearman_rho"]) if np.isfinite(r.get("spearman_rho", np.nan))
                      else -1.0) if sub else None
    max_ov_row = max(sub, key=lambda r: r.get("overlap_cand_in_sib", -1)) if sub else None
    exact_file = [f"{r['repo']}/{r['path']}" for r in rows if r["exact_file_match"]]
    exact_dec = [f"{r['repo']}/{r['path']}" for r in rows if r["exact_decoded_match"]]
    # |rho| as in validate_submission.check_lane_arrays (absolute Spearman, the stricter reading)
    max_rho = float(max(abs(v) for v in rho_vals)) if rho_vals else float("nan")
    max_ov_nd = float(max(ov_vals_nd)) if ov_vals_nd else float("nan")
    max_ov = float(max(ov_vals)) if ov_vals else float("nan")
    # Protocol verdict is LITERAL: the 70 % overlap limit applies to EVERY sibling raster with dots.
    # Blanket rasters (coverage >= DEGENERATE_COVERAGE) are reported but do not get an exemption here.
    lane_pass = (not exact_file) and (max_rho <= RHO_LIMIT) and (max_ov <= OVERLAP_LIMIT)
    # Diagnostic only (the earlier repository convention): excludes blanket rasters from the overlap test.
    lane_pass_nondegenerate = (not exact_file) and (max_rho <= RHO_LIMIT) and (max_ov_nd <= OVERLAP_LIMIT)
    overlap_fail_rows = [f"{r['repo']}/{r['path']}" for r in sub
                         if r.get("overlap_cand_in_sib", 0.0) > OVERLAP_LIMIT]
    top_rho = sorted(sub, key=lambda r: -r.get("spearman_rho", -9))[:10]
    top_ov = sorted(sub, key=lambda r: -r.get("overlap_cand_in_sib", -1))[:10]

    def slim(r):
        keep = ("repo", "path", "blob_sha", "sha256", "spearman_rho", "overlap_cand_in_sib",
                "overlap_sib_in_cand", "n_dots", "positive_cells_in_footprint")
        return {k: r[k] for k in keep if k in r}

    summary = {
        "candidate": {"path": str(cand_path), "sha256": cand_sha, "decoded_sha256": cand_dec,
                      "dots_in_footprint": n_cand},
        "protocol": {"rank_rho_limit": RHO_LIMIT, "dot_overlap_limit": OVERLAP_LIMIT,
                     "dot_radius_px": RADIUS_PX, "rank_sample_cells": int(sample.size),
                     "rank_sample_seed": SAMPLE_SEED},
        "scan": counts | {"sibling_repos": len({r["repo"] for r in rows}) if rows else 0},
        "result": {
            "exact_file_matches": exact_file,
            "exact_decoded_matches": exact_dec,
            "self_twins_excluded_from_sibling_stats": twins,
            "max_abs_spearman_rho": round(max_rho, 6) if np.isfinite(max_rho) else None,
            "max_spearman_rho_source": f"{max_rho_row['repo']}/{max_rho_row['path']}" if max_rho_row else None,
            "max_overlap_cand_in_sib_all": round(max_ov, 6) if np.isfinite(max_ov) else None,
            "max_overlap_cand_in_sib_nondegenerate": round(max_ov_nd, 6) if np.isfinite(max_ov_nd) else None,
            "overlap_fail_rows_literal": overlap_fail_rows,
            "lane_check_nondegenerate_diagnostic": "PASS" if lane_pass_nondegenerate else "FAIL",
            "max_overlap_source": f"{max_ov_row['repo']}/{max_ov_row['path']}" if max_ov_row else None,
            "overlap_degenerate_siblings": degenerate_rows,
            "siblings_with_abs_rho_above_limit": sum(1 for v in rho_vals if abs(v) > RHO_LIMIT),
            "siblings_with_overlap_above_limit": sum(1 for v in ov_vals if v > OVERLAP_LIMIT),
            "lane_check": "PASS" if lane_pass else "FAIL",
        },
        "top10_by_rho": [slim(r) for r in top_rho],
        "top10_by_overlap": [slim(r) for r in top_ov],
        "submission_like_count": len(sub),
        "generated_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "method_note": ("Spearman over a seeded 200k-cell subsample of the study area; "
                        "dot overlap is an exact EDT test on the full grid. Sibling files are read "
                        "read-only from partial clones of public repositories."),
    }
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out).write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    if args.table_out:
        Path(args.table_out).write_text(json.dumps(rows, indent=1) + "\n", encoding="utf-8")
    print(json.dumps(summary["result"], indent=2))
    print(json.dumps(counts))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

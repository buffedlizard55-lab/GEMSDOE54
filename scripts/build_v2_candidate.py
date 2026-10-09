#!/usr/bin/env python3
"""Build a catalogue-independent submission from a v2 feature surface (C4 or C5).

Same emission rules as scripts/build_unique_submission.py (shared helpers in
scripts/holdout_segment_cv.py, evaluator v2):

  1. Admissible cells: study footprint, minus cells within 300 m (3 px) of the FULL published
     catalogue (the builder never places a dot on or next to a catalogued fault).
  2. Surface: C4 cross-gradient coincidence (tmi_hg x iso_grav_anom_hg, rank geometric mean)
     or C5 |grad cond_surf|. Ridge = cells at or above the quantile threshold whose gated dot
     count is closest to --target (default: the H54-A dot count, 15,907).
  3. Linearity gate, then one dot per 2 px along each trace (shared with holdout C1-C5).
  4. Output: float32 single band, EPSG:32611, 3730 x 3292, 100 m. Dots = 1.0, other footprint
     cells = 0.0, cells outside the footprint = NaN (the official rule: "data outside the bounds
     is null or nan"). The file is read back and every check is asserted before a receipt is
     written.

Run:
  python scripts/build_v2_candidate.py --feature cross_gradient \
      --features /tmp/training_features.tif --out docs/downloads/<name>.tif \
      --receipt registry/<name>.build.json
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import rasterio
from scipy.ndimage import distance_transform_edt

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from gemsdoe54.grid import FOOTPRINT_CELLS, footprint, read_band, write_submission  # noqa: E402
import holdout_segment_cv as ev  # noqa: E402

H54A_DOTS = 15907


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def display(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(ROOT))
    except ValueError:
        return str(path.resolve())


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--feature", required=True, choices=["cross_gradient", "cond_gradient"])
    ap.add_argument("--features", default="/tmp/training_features.tif")
    ap.add_argument("--labels", default=str(ROOT / "data/grid/labels.tif"))
    ap.add_argument("--target", type=int, default=H54A_DOTS)
    ap.add_argument("--out", required=True)
    ap.add_argument("--receipt", required=True)
    args = ap.parse_args()

    feat_path = Path(args.features)
    feat_sha = sha256_file(feat_path)
    if feat_sha != ev.FEATURE_PIN:
        raise SystemExit(f"feature SHA-256 mismatch: {feat_sha}")
    with rasterio.open(feat_path) as ds:
        names = [ds.tags(i).get("band_name") for i in range(1, ds.count + 1)]

    def band(n: str) -> np.ndarray:
        return ev.load_band(feat_path, names.index(n) + 1)

    foot = footprint(args.labels)
    labels_raw, _ = read_band(args.labels)
    cat = (labels_raw == 1) & foot
    dist_cat_px = distance_transform_edt(~cat)
    dist_m = dist_cat_px * 100.0
    admissible_base = foot & (dist_cat_px > ev.BUFFER_PX)

    if args.feature == "cross_gradient":
        surf, valid = ev.cross_gradient_surface(band("tmi_hg"), band("iso_grav_anom_hg"), foot)
        source = "rank-geometric-mean of |tmi_hg| and |iso_grav_anom_hg| (C4)"
        bands_used = ["tmi_hg", "iso_grav_anom_hg"]
    else:
        surf, valid = ev.conductivity_gradient_surface(band("cond_surf"), foot)
        source = "|grad cond_surf| at 100 m (C5)"
        bands_used = ["cond_surf"]

    best = ev.ridge_matched(surf, admissible_base & valid, args.target, dist_m)
    dots = best["dots"]
    n_dots = int(dots.sum())
    values = np.zeros(foot.shape, dtype=np.float64)
    values[dots] = 1.0

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    write_submission(out, values, footprint=foot)

    with rasterio.open(out) as src:
        back = src.read(1)
        dtype = src.dtypes[0]
        crs = str(src.crs)
        shape = (src.height, src.width)
        transform = tuple(src.transform)[:6]
    inside = back[foot]
    outside = back[~foot]
    checks = {
        "dtype_float32": dtype == "float32",
        "crs_epsg_32611": crs == "EPSG:32611",
        "shape_3730x3292": shape == (3730, 3292),
        "transform_100m": tuple(round(v, 6) for v in transform) == (100.0, 0.0, 243350.0, 0.0, -100.0, 4508550.0),
        "finite_inside_footprint": bool(np.isfinite(inside).all()),
        "in_0_1_inside_footprint": bool(inside.min() >= 0.0 and inside.max() <= 1.0),
        "nan_outside_footprint": bool(np.isnan(outside).all()),
        "positive_count_matches_gate": int((inside > 0).sum()) == n_dots,
        "no_dot_on_or_within_300m_of_catalogue": int(((inside > 0) & (dist_cat_px[foot] <= ev.BUFFER_PX)).sum()) == 0,
        "footprint_cells": int(foot.sum()) == FOOTPRINT_CELLS,
    }
    if not all(checks.values()):
        raise SystemExit(f"output validation failed: {checks}")

    receipt = {
        "slug": out.stem,
        "generated_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "builder": "scripts/build_v2_candidate.py",
        "evaluator_helpers": {"name": ev.EVALUATOR["name"], "version": ev.EVALUATOR["version"]},
        "source_layer": {"surface": source, "bands": bands_used, "features_sha256": feat_sha,
                         "provenance": "owner bridge copy of the GeoDAWN feature stack; SHA-256 matches the "
                                       "owner manifest; NOT organizer-authenticated"},
        "rule": "ridge of surface >= quantile threshold, gated, 2 px spacing, >= 300 m from the full catalogue",
        "parameters": {"quantile": best["quantile"], "threshold": best["threshold"],
                       "target_dots": args.target, "achieved_dots": n_dots,
                       "spacing_px": ev.SPACING_PX, "gate": ev.GATE, "buffer_px": ev.BUFFER_PX},
        "output": {"path": display(out), "sha256": sha256_file(out), "bytes": out.stat().st_size,
                   "dtype": "float32", "crs": "EPSG:32611", "shape": list(shape),
                   "nodata": "NaN outside footprint", "positive_cells": n_dots,
                   "footprint_cells": int(foot.sum())},
        "checks": checks,
        "label": "MODEL (no score). Holdout and uniqueness are reported separately as HOLDOUT-DTI / lane receipts.",
    }
    Path(args.receipt).parent.mkdir(parents=True, exist_ok=True)
    Path(args.receipt).write_text(json.dumps(receipt, indent=2, default=float) + "\n", encoding="utf-8")
    print(json.dumps({"out": receipt["output"]["path"], "sha256": receipt["output"]["sha256"],
                      "dots": n_dots, "quantile": best["quantile"], "checks": checks}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

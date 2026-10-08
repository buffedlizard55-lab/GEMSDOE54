#!/usr/bin/env python3
"""Build a lane-distinct submission from a catalogue-independent feature ridge (full-data build).

Same rules as scripts/build_submission.py, with one change of source layer:
  1. Admissible cells: study footprint minus cells within 300 m (3 px) of the FULL published catalogue.
  2. Source: ridge = the cells whose feature value is at or above a quantile threshold, the quantile
     chosen so that the gated dot count is as close as possible to --target (default: the H54-A count,
     so both files carry the same number of dots).
  3. Linearity gate (builder defaults) then one dot per 2 px, longest trace first (same priority rule).
  4. Values: 1 on dots, 0 elsewhere, float32, EPSG:32611, 3730 x 3292, 100 m. Read back and asserted.

The feature raster is the owner's bridge copy of the official GeoDAWN feature stack (SHA-256 pinned).
Its provenance is owner-claimed; the file therefore carries that caveat in its receipt.

Run (example):
  python scripts/build_unique_submission.py --feature geod_shearrate \
      --out docs/downloads/gems54-geodshear-ridge-q.tif --receipt registry/gems54-geodshear-ridge-q.build.json
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
import holdout_segment_cv as ev  # noqa: E402  (shared gate, emission, and quantile-match helpers)

FEATURE_PIN = ev.FEATURE_PIN
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
    ap.add_argument("--feature", required=True, choices=["geod_shearrate", "tmi_hg"])
    ap.add_argument("--features", default="/tmp/sib/gems-geodawn-numerical-features.tif")
    ap.add_argument("--labels", default=str(ROOT / "data/grid/labels.tif"))
    ap.add_argument("--target", type=int, default=H54A_DOTS)
    ap.add_argument("--out", required=True)
    ap.add_argument("--receipt", required=True)
    args = ap.parse_args()

    feat_path = Path(args.features)
    feat_sha = sha256_file(feat_path)
    if feat_sha != FEATURE_PIN:
        raise SystemExit(f"feature SHA-256 mismatch: {feat_sha}")
    with rasterio.open(feat_path) as ds:
        names = [ds.tags(i).get("band_name") for i in range(1, ds.count + 1)]
    band = names.index(args.feature) + 1
    feat = ev.load_band(feat_path, band)

    foot = footprint(args.labels)
    labels_raw, _ = read_band(args.labels)
    cat = (labels_raw == 1) & foot
    dist_cat_px = distance_transform_edt(~cat)
    dist_m = dist_cat_px * 100.0
    adm = foot & (dist_cat_px > ev.BUFFER_PX) & np.isfinite(feat)

    best = ev.ridge_matched(feat, adm, args.target, dist_m)
    dots = best["dots"]
    n_dots = int(dots.sum())
    values = np.zeros(foot.shape, dtype=np.float64)
    values[dots] = 1.0
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    write_submission(out, values)

    back, _ = read_band(out)
    assert back.shape == foot.shape, "shape changed on write"
    assert np.isfinite(back).all(), "written raster contains non-finite values"
    assert back.min() >= 0.0 and back.max() <= 1.0, "written raster outside [0, 1]"
    assert int((back > 0).sum()) == n_dots, "dot count changed on write"
    assert int(((back > 0) & cat).sum()) == 0, "dots placed on the published catalogue"
    assert int(((back > 0) & (dist_cat_px <= ev.BUFFER_PX)).sum()) == 0, "dots within 300 m of catalogue"

    receipt = {
        "slug": out.stem,
        "generated_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "source_layer": {"feature": args.feature, "band": band, "features_sha256": feat_sha,
                         "provenance": "owner bridge copy of the official GeoDAWN feature stack; "
                                       "hash-consistent with manifest; not organizer-authenticated"},
        "rule": "ridge of feature >= quantile threshold, gated, 2 px spacing, >= 300 m from full catalogue",
        "parameters": {"quantile": best["quantile"], "threshold": best["threshold"], "target_dots": args.target,
                       "achieved_dots": n_dots, "spacing_px": ev.SPACING_PX, "gate": ev.GATE,
                       "buffer_px": ev.BUFFER_PX, "quantile_grid": list(ev.RIDGE_QUANTILES)},
        "output": {"path": display(out), "sha256": sha256_file(out), "bytes": out.stat().st_size,
                   "dtype": "float32", "crs": "EPSG:32611", "shape": list(foot.shape),
                   "positive_cells": n_dots, "footprint_cells": int(foot.sum()),
                   "footprint_expected": FOOTPRINT_CELLS},
        "checks": {"finite": True, "in_0_1": True, "no_dot_on_catalogue": True,
                   "no_dot_within_300m_of_catalogue": True},
    }
    Path(args.receipt).parent.mkdir(parents=True, exist_ok=True)
    Path(args.receipt).write_text(json.dumps(receipt, indent=2, default=float) + "\n", encoding="utf-8")
    print(json.dumps({"out": receipt["output"]["path"], "sha256": receipt["output"]["sha256"],
                      "dots": n_dots, "quantile": best["quantile"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

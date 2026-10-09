#!/usr/bin/env python3
"""Build one hypothesis-family GeoTIFF on the full catalogue (parallel-run candidate builder).

This is the *final-file* counterpart of the holdout candidates in ``holdout_segment_cv.py``
(evaluator v2). It reuses the same pieces so that the file and the holdout receipt describe
the same method:

* feature fields      -> ``gemsdoe54.hypotheses`` (H1 cross-gradient, H2 basement step, H3 learned)
* dot emission        -> ``holdout_segment_cv.gated_dots`` (builder linearity gate + 200 m spacing)
* writer / validator  -> ``gemsdoe54.grid.write_submission`` (float32, NaN outside, [0,1] inside)

Scoring target reminder: the official round-1 truth is a private set of *new* faults outside the
USGS catalogue, so dots within 300 m of a catalogue fault are excluded exactly as in the holdout.

The quantile is passed explicitly (``--quantile``). It must be the value that the holdout receipt
selected (median of the per-fold selections), so the file is not tuned on the full catalogue.

Run (example):
  python scripts/build_hypothesis_submission.py --family learned --quantile 0.95 \
      --out docs/downloads/<name>.tif --receipt registry/<name>_build.json
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
from scipy.ndimage import distance_transform_edt, label

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from gemsdoe54.grid import EXPECTED_SHAPE, binary_mask, footprint, read_band, write_submission  # noqa: E402
from gemsdoe54.hypotheses import (  # noqa: E402
    GRAD_BANDS,
    MODEL_PARAMS,
    basement_step_score,
    cross_gradient_score,
    gradient_magnitude,
    learned_visible_probability,
)
from holdout_segment_cv import FEATURE_PIN, KERNEL_PX, SEED, gated_dots, load_band, sha256_file  # noqa: E402

BUFFER_PX = 3.0
FAMILIES = ("learned", "cross_gradient", "basement_step")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--family", choices=FAMILIES, required=True)
    ap.add_argument("--quantile", type=float, required=True,
                    help="quantile of the admissible field above which cells are kept (from the holdout receipt)")
    ap.add_argument("--features", default="/tmp/gemsbridge/training_features.tif")
    ap.add_argument("--labels", default=str(ROOT / "data/grid/labels.tif"))
    ap.add_argument("--out", required=True)
    ap.add_argument("--receipt", required=True)
    ap.add_argument("--name", required=True)
    ap.add_argument("--note", required=True)
    ap.add_argument("--surface-out", default="",
                    help="optional .npz (outside the repository) with the pre-placement surface for the lane check")
    args = ap.parse_args()
    if len(args.note) > 140:
        raise SystemExit(f"note is {len(args.note)} characters; the limit is 140")
    if not 0.0 < args.quantile < 1.0:
        raise SystemExit("quantile must lie strictly between 0 and 1")

    feat_path = Path(args.features)
    feat_sha = sha256_file(feat_path)
    if feat_sha != FEATURE_PIN:
        raise SystemExit(f"feature SHA-256 mismatch: {feat_sha}")
    with rasterio.open(feat_path) as ds:
        band_names = [ds.tags(i).get("band_name", f"band{i}") for i in range(1, ds.count + 1)]

    foot = footprint(args.labels)
    labels_raw, _ = read_band(args.labels)
    cat = (labels_raw == 1) & foot
    d_cat_px = distance_transform_edt(~cat)
    adm = foot & (d_cat_px > BUFFER_PX)            # same exclusion as the holdout (within 3 px of catalogue)
    dist_m = d_cat_px * 100.0

    if args.family == "cross_gradient":
        tmi_hg = load_band(feat_path, band_names.index("tmi_hg") + 1)
        grav_hg = load_band(feat_path, band_names.index("iso_grav_anom_hg") + 1)
        field = cross_gradient_score(tmi_hg, grav_hg, foot)
        del tmi_hg, grav_hg
        extra = {"formula": "geometric mean of within-footprint percentiles of tmi_hg and iso_grav_anom_hg"}
    elif args.family == "basement_step":
        dtb = load_band(feat_path, band_names.index("depth_to_base_surf") + 1)
        field = basement_step_score(dtb, foot)
        del dtb
        extra = {"formula": "|grad| of depth_to_base_surf, 1 px Gaussian, 100 m cells"}
    else:
        rows = np.flatnonzero(foot.ravel())
        n_raw = len(band_names)
        F = np.empty((rows.size, n_raw + len(GRAD_BANDS)), dtype=np.float32)
        for bi in range(1, n_raw + 1):
            arr = load_band(feat_path, bi)
            F[:, bi - 1] = arr.ravel()[rows]
            del arr
        for j, bn in enumerate(GRAD_BANDS):
            arr = load_band(feat_path, band_names.index(bn) + 1)
            g = gradient_magnitude(arr, foot & np.isfinite(arr), sigma_px=1.0)
            F[:, n_raw + j] = g.ravel()[rows]
            del arr, g
        pred_rows = np.flatnonzero(adm.ravel()[rows])
        p_rows, diag = learned_visible_probability(
            F, cat.ravel()[rows], np.zeros(rows.size, dtype=bool), pred_rows, seed=SEED + 9000)
        field = np.full(foot.size, np.nan, dtype=np.float32)
        field[rows[pred_rows]] = p_rows
        field = field.reshape(foot.shape)
        extra = {"model": diag, "features": band_names + [f"grad_{b}" for b in GRAD_BANDS],
                 "training": "all catalogue cells positive; footprint cells outside the catalogue negative (PU)"}

    ok = adm & np.isfinite(field)
    vals = field[ok]
    thr = float(np.quantile(vals, args.quantile))
    mask = ok & (field >= thr)
    dots = gated_dots(mask, dist_m)
    if args.surface_out:
        np.savez_compressed(args.surface_out, field=field.astype(np.float32), mask=mask, dots=dots, foot=foot)
    n_dots = int(dots.sum())
    if n_dots == 0:
        raise SystemExit("no dots survived the linearity gate at this quantile")

    out = np.zeros(EXPECTED_SHAPE, dtype=np.float64)
    out[dots] = 1.0
    write_submission(args.out, out, footprint=foot)

    with rasterio.open(args.out) as ds:
        arr = ds.read(1)
        nod = ds.nodata
        dtype = ds.dtypes[0]
    inside = arr[foot]
    stats = {
        "dtype": dtype, "nodata": None if nod is None else str(nod),
        "finite_inside_footprint": int(np.isfinite(inside).sum()), "footprint_cells": int(foot.sum()),
        "min_inside": float(np.nanmin(inside)), "max_inside": float(np.nanmax(inside)),
        "nonfinite_outside_footprint": int(np.isfinite(arr[~foot]).sum()),
        "positive_cells": int((np.nan_to_num(arr, nan=0.0) > 0).sum()),
    }
    if not (dtype == "float32" and stats["nonfinite_outside_footprint"] == 0
            and 0.0 <= stats["min_inside"] and stats["max_inside"] <= 1.0
            and stats["finite_inside_footprint"] == stats["footprint_cells"]):
        raise SystemExit(f"format self-check failed: {stats}")

    receipt = {
        "name": args.name,
        "note": args.note,
        "note_chars": len(args.note),
        "family": args.family,
        "quantile": args.quantile,
        "threshold": thr,
        "admissible_cells": int(adm.sum()),
        "field_cells_used": int(vals.size),
        "dots": n_dots,
        "gate": "linearity gate (min_px 3, min_px_extent 5, min_elongation 6.0) + 200 m spacing (builder rules)",
        "exclusion": "cells within 300 m of a catalogue fault are excluded",
        "output": {"path": args.out, "sha256": sha256_file(Path(args.out)), "bytes": Path(args.out).stat().st_size},
        "format_self_check": stats,
        "features": {"path": str(feat_path), "sha256": feat_sha, "provenance": "owner bridge; not organizer-authenticated"},
        "labels": {"path": args.labels, "sha256": sha256_file(Path(args.labels))},
        "method_extra": extra,
        "generated_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
    }
    Path(args.receipt).parent.mkdir(parents=True, exist_ok=True)
    Path(args.receipt).write_text(json.dumps(receipt, indent=2, default=float) + "\n", encoding="utf-8")
    print(json.dumps({k: receipt[k] for k in ("name", "family", "quantile", "dots", "output", "format_self_check")}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

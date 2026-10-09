#!/usr/bin/env python3
"""Build the H1 cross-gradient coincidence submission candidate (float32 GeoTIFF).

H1 (see docs/research/hypotheses-20261008.md, rank 1, now implemented):
  Score  = min( percentile rank of tmi_hg , percentile rank of |iso_grav_anom_hg| )  over the footprint.
  Dots   = the repository's builder rules (linearity gate, then longest trace first, 2 px spacing)
           applied to cells whose score is at or above a quantile threshold q, outside the 300 m
           exclusion of the known catalogue (the submission sees the full catalogue as visible).
  q      = the quantile that the holdout (scripts/holdout_segment_cv.py, candidate C4) selected in
           the median fold, read from the receipt; it is passed explicitly so the build is reproducible.

The score and gate are imported from the shared evaluator; nothing here is a private copy.
Output: single-band float32, EPSG:32611, same grid/transform as the label raster, values exactly
0.0 or 1.0, zeros outside the footprint, no NaN and no nodata tag (written by the shared
gemsdoe54.grid.write_submission with footprint=None). The organizer reference notebook writes this
same convention; the repo's older NaN-outside convention is the alternative. This is an
interpretation and is listed as an open review item in the run card.

Run:
  python scripts/build_h1_crossgradient.py --features /tmp/bridge/training_features.tif \
      --quantile 0.90 --out work/h1-crossgradient.tif
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

from gemsdoe54.grid import FOOTPRINT_CELLS, binary_mask, footprint, write_submission  # noqa: E402
from holdout_segment_cv import (  # noqa: E402
    BUFFER_PX,
    FEATURE_PIN,
    coincidence_score,
    gated_dots,
    load_band,
    sha256_file,
)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--features", required=True)
    ap.add_argument("--labels", default=str(ROOT / "data/grid/labels.tif"))
    ap.add_argument("--quantile", type=float, required=True, help="score quantile threshold q over admissible cells")
    ap.add_argument("--out", required=True)
    ap.add_argument("--receipt", default=None, help="optional JSON receipt path")
    args = ap.parse_args()

    feat = Path(args.features)
    fsha = sha256_file(feat)
    if fsha != FEATURE_PIN:
        raise SystemExit(f"feature SHA-256 mismatch: {fsha} != pinned {FEATURE_PIN}")
    # band names in this cube are carried in the band description (the part before " - ")
    with rasterio.open(feat) as ds:
        desc = list(ds.descriptions)
    def idx(token: str) -> int:
        hits = [i for i, d in enumerate(desc) if d and d.split(" - ")[0] == token]
        if len(hits) != 1:
            raise SystemExit(f"expected exactly one band named {token!r}, found {len(hits)}")
        return hits[0] + 1

    foot = footprint(args.labels)
    cat = (binary_mask(args.labels) & foot)  # visible to the submission: the whole catalogue
    tmihg = load_band(feat, idx("tmi_hg"))
    gravhg = load_band(feat, idx("iso_grav_anom_hg"))
    score = coincidence_score(tmihg, gravhg, foot)

    dist_px = distance_transform_edt(~cat)
    excl = dist_px <= BUFFER_PX
    adm = foot & ~excl & np.isfinite(score)
    thr = float(np.quantile(score[adm], args.quantile))
    dots = gated_dots(adm & (score >= thr), dist_px * 100.0)

    out = np.zeros(foot.shape, dtype=np.float32)
    out[dots] = 1.0
    # shared writer, no footprint argument: all-finite float32 in [0, 1], no nodata tag (reference convention)
    write_submission(args.out, out, footprint=None, dtype="float32")

    raw = Path(args.out).read_bytes()
    receipt = {
        "schema": "gemsdoe54.build-h1.v1",
        "generated_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "hypothesis": "H1 cross-gradient coincidence ridge",
        "score_definition": "min(pct_rank(tmi_hg), pct_rank(|iso_grav_anom_hg|)) over footprint",
        "quantile": args.quantile,
        "threshold": thr,
        "positive_cells": int(dots.sum()),
        "exclusion_buffer_px": BUFFER_PX,
        "footprint_cells": int(foot.sum()),
        "footprint_expected": FOOTPRINT_CELLS,
        "features_sha256": fsha,
        "labels_sha256": sha256_file(Path(args.labels)),
        "output_path": str(args.out),
        "output_bytes": len(raw),
        "output_sha256": hashlib.sha256(raw).hexdigest(),
        "dtype": "float32",
        "nodata": None,
        "values": "exactly 0.0 or 1.0; zeros outside footprint; no NaN",
        "label": "MODEL (inference). Not a score. See holdout receipt for HOLDOUT-DTI.",
    }
    if args.receipt:
        Path(args.receipt).write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(receipt, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

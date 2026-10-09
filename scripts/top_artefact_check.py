#!/usr/bin/env python3
"""Reproduce the 0.2778 (dotted_b2_prune) vs 0.2708 (dotted_d2_8_02708) raster comparison.

Writes evidence/top_artefact_check.json. Reads only tracked registry rasters and the cached label mask.
Board values are NOT used here; they are recorded only as BOARD-UNVERIFIED labels.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import rasterio
from scipy.ndimage import distance_transform_edt

ROOT = Path(__file__).resolve().parents[1]
PARENT = ROOT / "registry/registry_rasters/dotted_d2_8_02708.tif"
CHILD = ROOT / "registry/registry_rasters/dotted_b2_prune_02778.tif"
LABELS = ROOT / "data/grid/labels.tif"


def dots(path: Path) -> np.ndarray:
    with rasterio.open(path) as src:
        return np.nan_to_num(src.read(1), nan=0.0) > 0


def main() -> int:
    P, C = dots(PARENT), dots(CHILD)
    with rasterio.open(LABELS) as src:
        cat = src.read(1) == 1
    d_px = distance_transform_edt(~cat)            # 100 m cells
    removed = P & ~C
    kept_child = C
    out = {
        "label": "VERIFIED (raster comparison); board values BOARD-UNVERIFIED",
        "parent": {"file": str(PARENT.relative_to(ROOT)), "published_unverified": 0.2708, "dots": int(P.sum())},
        "child": {"file": str(CHILD.relative_to(ROOT)), "published_unverified": 0.2778, "dots": int(C.sum())},
        "child_subset_of_parent": bool(np.all(P[C])),
        "removed_dots": int(removed.sum()),
        "added_dots": int((C & ~P).sum()),
        "removed_within_1px_of_catalogue": int((removed & (d_px <= 1)).sum()),
        "removed_within_2px_of_catalogue": int((removed & (d_px <= 2)).sum()),
        "removed_beyond_2px": int((removed & (d_px > 2)).sum()),
        "parent_dots_within_2px": int((P & (d_px <= 2)).sum()),
        "parent_dots_within_3px": int((P & (d_px <= 3)).sum()),
        "kept_child_dots_within_2px": int((kept_child & (d_px <= 2)).sum()),
        "kept_child_dots_200_to_300m": int((kept_child & (d_px > 2) & (d_px <= 3)).sum()),
        "median_distance_removed_m": float(np.median(d_px[removed]) * 100.0),
        "median_distance_kept_child_m": float(np.median(d_px[kept_child]) * 100.0),
        "share_kept_child_within_300m": float((d_px[kept_child] <= 3).mean()),
        "share_parent_within_300m": float((d_px[P] <= 3).mean()),
        "rule_identified": "child = parent minus parent dots within 2 px (200 m) of the catalogue",
        "implied_denominator_MODEL_if_removed_dots_earned_zero_credit": round(
            0.2 * int(removed.sum()) * 0.2778 / (0.2778 - 0.2708), 1),
        "generated_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }
    dest = ROOT / "evidence/top_artefact_check.json"
    dest.write_text(json.dumps(out, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: out[k] for k in ("child_subset_of_parent", "removed_dots", "removed_within_2px_of_catalogue",
                                          "removed_beyond_2px", "kept_child_dots_200_to_300m")}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

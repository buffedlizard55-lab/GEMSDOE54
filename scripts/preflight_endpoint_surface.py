#!/usr/bin/env python3
"""Pre-placement lane gate for the endpoint-continuation hypothesis.

This script writes a score-surface audit only. If the strict registry lane gate
fails, it exits 2 and does not place dots or write a submission TIFF.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
import sys

import numpy as np
import rasterio
from scipy.ndimage import distance_transform_edt

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))
from gemsdoe54.continuation import endpoint_continuation_surface  # noqa: E402
from validate_submission import check_lane_array  # noqa: E402


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--labels", default=str(ROOT / "data/grid/labels.tif"))
    parser.add_argument("--prior-artifact", default=str(ROOT / "docs/downloads/gems54-undercomplement-q200.tif"))
    parser.add_argument("--registry-dir", default=str(ROOT / "registry/registry_rasters"))
    parser.add_argument("--exclude-m", type=float, default=300.0)
    parser.add_argument("--out", default=str(ROOT / "evidence/endpoint-continuation-preflight.json"))
    args = parser.parse_args()

    with rasterio.open(args.labels) as src:
        labels = src.read(1)
        footprint = labels != src.nodata
        input_meta = {"shape": [src.height, src.width], "crs": str(src.crs),
                      "transform": list(src.transform[:6])}
    visible_catalogue = (labels == 1) & footprint
    surface = endpoint_continuation_surface(visible_catalogue, footprint)
    distance_m = distance_transform_edt(~visible_catalogue, sampling=(100.0, 100.0))
    surface[(distance_m <= args.exclude_m) | ~footprint] = 0.0
    surface = np.nan_to_num(surface, nan=0.0, posinf=0.0, neginf=0.0).astype(np.float32)

    registry_dir = Path(args.registry_dir)
    registry = sorted(registry_dir.glob("*.tif")) if registry_dir.exists() else []
    prior = Path(args.prior_artifact)
    if prior.exists():
        registry.append(prior)
    lane = check_lane_array(surface, registry, footprint)
    rows = lane.get("rows", [])
    max_abs_rho = max((float(row["abs_spearman_rho"]) for row in rows), default=None)
    max_overlap = max((float(row["fraction_of_my_dots"]) for row in rows), default=None)
    top_overlap = max(rows, key=lambda row: row["fraction_of_my_dots"], default=None)
    record = {
        "schema": "gemsdoe54.surface-preflight.v1",
        "generated_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "hypothesis": "Extend sufficiently elongated visible catalogue fault traces along their endpoint tangent for at most 1.5 km; retain only cells more than 300 m from the visible catalogue.",
        "mechanism": "Fault strands may continue beneath cover beyond a mapper's visible trace endpoint; local tangent projection tests that continuation without using an external feature layer.",
        "named_non_fault_mimic": "A mapped trace may terminate at a lithologic contact, intrusive body, erosional boundary, or digitizing/map-sheet boundary rather than continuing as a fault.",
        "data_provenance": "Owner-mirrored labels; hash-pinned locally but not authenticated from DrivenData in this session.",
        "inputs": {"labels_path": str(Path(args.labels).relative_to(ROOT)),
                   "labels_sha256": hashlib.sha256(Path(args.labels).read_bytes()).hexdigest(),
                   "grid": input_meta},
        "surface": {
            "kind": "unplaced candidate score surface; not a submission raster",
            "positive_cells": int(np.count_nonzero(surface > 0)),
            "minimum_positive": float(surface[surface > 0].min()) if np.any(surface > 0) else None,
            "maximum": float(surface.max()),
            "float32_c_order_sha256": sha256_bytes(surface.astype("<f4", copy=False).tobytes(order="C")),
        },
        "lane_preplacement": lane,
        "summary": {"registry_raster_count": len(rows),
                    "max_abs_spearman_rho": max_abs_rho,
                    "rho_limit": 0.90,
                    "max_fraction_surface_cells_within_3px": max_overlap,
                    "overlap_limit": 0.70,
                    "max_overlap_registry": (top_overlap["registry"] if top_overlap else None),
                    "lane_drift_detected": lane.get("lane_drift_detected"),
                    "decision": "DUPLICATE - STOP before dot placement, holdout scoring, or TIFF writing"
                    if lane.get("lane_drift_detected") else "surface passed; proceed to holdout before any slot selection"},
        "holdout_dti": {"label": "HOLDOUT-DTI", "value": None,
                         "status": "NOT RUN: strict pre-placement lane gate failed",
                         "evaluator_version": None, "withheld_positive_count": None,
                         "ci95": None},
        "submission": {"tif_generated": False, "upload_approved": False},
    }
    output = Path(args.out)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(record, indent=2))
    return 2 if lane.get("lane_drift_detected") else 0


if __name__ == "__main__":
    raise SystemExit(main())

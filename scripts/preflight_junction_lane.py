#!/usr/bin/env python3
"""Pre-placement lane screen for a local SGMC fault-network topology hypothesis.

This script writes only a JSON diagnostic. It never emits a submission TIFF. If
its surface crosses either literal lane threshold, it records the duplicate and
stops before point placement, in accordance with the parallel-run protocol.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys

import numpy as np
import rasterio
from scipy.ndimage import convolve, distance_transform_edt

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from gemsdoe54.grid import binary_mask, footprint, read_band  # noqa: E402
from validate_submission import check_lane_arrays  # noqa: E402


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def angular_transition_surface(sgmc: np.ndarray, catalogue: np.ndarray) -> tuple[np.ndarray, int]:
    """Build an exploratory high-angular-transition surface outside a 300 m buffer.

    The score is a deterministic transform of the 8-neighbour occupancy ring on
    the rasterized SGMC mask plus local line density. It is a *surface screen*, not
    a validated physical fault-junction detector; rasterization artifacts can
    create the same pattern.
    """
    sgmc = np.asarray(sgmc, dtype=bool)
    catalogue = np.asarray(catalogue, dtype=bool)
    if sgmc.ndim != 2 or catalogue.shape != sgmc.shape:
        raise ValueError("SGMC and catalogue masks must be same-shape 2-D arrays")

    padded = np.pad(sgmc, 1, mode="constant", constant_values=False)
    ring = [
        padded[:-2, 1:-1], padded[:-2, 2:], padded[1:-1, 2:], padded[2:, 2:],
        padded[2:, 1:-1], padded[2:, :-2], padded[1:-1, :-2], padded[:-2, :-2],
    ]
    transitions = np.zeros(sgmc.shape, dtype=np.uint8)
    for idx in range(8):
        transitions += np.logical_xor(ring[idx], ring[(idx + 1) % 8])

    distance_to_catalogue = distance_transform_edt(~catalogue, sampling=(100.0, 100.0))
    eligible = sgmc & (distance_to_catalogue > 300.0)
    local_density = convolve(
        sgmc.astype(np.float32), np.ones((5, 5), dtype=np.float32), mode="constant"
    )
    surface = np.zeros(sgmc.shape, dtype=np.float32)
    support = eligible & (transitions >= 4)
    surface[support] = transitions[support].astype(np.float32) * 100.0 + local_density[support]
    return surface, int(support.sum())


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--labels", type=Path, default=ROOT / "data/grid/labels.tif")
    parser.add_argument("--sgmc", type=Path, default=ROOT / "data/external/derived_sgmc_faults_100m_u8.tif")
    parser.add_argument("--registry-dir", type=Path, default=ROOT / "registry/registry_rasters")
    parser.add_argument("--output", type=Path, default=ROOT / "evidence/strict_lane_preflight.json")
    args = parser.parse_args()

    labels_raw, _ = read_band(args.labels)
    foot = footprint(args.labels)
    catalogue = (labels_raw == 1) & foot
    sgmc = binary_mask(args.sgmc) & foot
    surface, support_cells = angular_transition_surface(sgmc, catalogue)

    registry_paths = sorted(args.registry_dir.glob("*.tif"))
    registry_arrays: list[tuple[str, np.ndarray]] = []
    for path in registry_paths:
        with rasterio.open(path) as src:
            if (src.height, src.width) != surface.shape:
                raise ValueError(f"registry raster {path} does not match the candidate grid")
            registry_arrays.append((path.name, src.read(1)))

    lane = check_lane_arrays(surface, registry_arrays, foot, cell_px=3,
                             max_rho=0.90, max_overlap=0.70)
    lane_is_indeterminate = lane["lane_drift_detected"] is None or lane["verdict"].startswith("INDETERMINATE")
    stop = bool(lane["lane_drift_detected"]) or lane_is_indeterminate
    result = (
        "STOP_DUPLICATE_BEFORE_EMISSION" if lane["lane_drift_detected"] is True else
        "STOP_INDETERMINATE_BEFORE_EMISSION" if lane_is_indeterminate else
        "SURFACE_PASSES_LANE_GATE"
    )
    report = {
        "schema": "gemsdoe54.strict-lane-preflight.v1",
        "run_id": "GEMSDOE54-E1-SGMC-topology-surface-20261008",
        "result": result,
        "candidate_hypothesis": "High-angular-transition nodes in the owner-mirrored SGMC fault mask may mark connected damage zones outside the known catalogue.",
        "mechanism_status": "untested hypothesis; not evidence for a mapped Quaternary fault or geothermal upflow",
        "named_non_fault_mimic": "Rasterization, snapping, and cartographic linework can create high-neighbour transition nodes; lithologic or map-compilation artifacts can mimic network junctions.",
        "inputs": {
            "labels_path": str(args.labels.relative_to(ROOT) if args.labels.is_relative_to(ROOT) else args.labels),
            "labels_sha256": sha256(args.labels),
            "sgmc_path": str(args.sgmc.relative_to(ROOT) if args.sgmc.is_relative_to(ROOT) else args.sgmc),
            "sgmc_sha256": sha256(args.sgmc),
            "data_provenance": "owner-mirrored pins; organizer origin not authenticated in this run",
        },
        "surface": {
            "definition": "SGMC cells outside >300 m from the local catalogue, retained where the 8-neighbour occupancy ring has at least four angular transitions; score = 100*transition_count + 5x5 SGMC density",
            "positive_support_cells": support_cells,
            "registry_raster_count": len(registry_arrays),
            "not_a_submission_raster": True,
        },
        "pre_placement_registry_check": lane,
        "holdout_dti": {
            "label": "HOLDOUT-DTI",
            "status": "NOT RUN — no compliant whole-segment evaluator/receipt and the strict surface lane gate stopped this experiment",
            "evaluator_version": None,
            "withheld_positive_count": None,
            "ci95": None,
        },
        "emission": {
            "performed": False,
            "reason": (
                "The literal raw-overlap lane gate was exceeded before placement; no dot set or TIF was written."
                if lane["lane_drift_detected"] is True else
                "The registry lane could not be checked; no dot set or TIF was written."
                if lane_is_indeterminate else
                "No emission was performed by this surface-only preflight."
            ),
            "final_dot_count": None,
            "raster_sha256": None,
            "validator_output": None,
        },
        "slot_used": False,
        "verdict": "negative",
        "score_labeling": "No score was produced. Registry overlap and Spearman statistics are screening diagnostics, not HOLDOUT-DTI or ORGANIZER-CONFIRMED scores.",
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2, allow_nan=False))
    print(f"\nwrote {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Write a machine-generated lane receipt for one or more candidate rasters.

Applies the parallel-run protocol's literal lane gate (scripts/validate_submission.check_lane)
against every local registry raster and records the verdict, the per-registry rank correlation,
and the 3-px dot-overlap fractions. No number in the receipt is typed by hand.

Run:
  python scripts/record_lane_screen.py --out evidence/lane_screen_v2.json \
      --candidate NAME=/path/to/candidate.tif [--candidate ...]
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "src"))

import validate_submission as v  # noqa: E402


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--candidate", action="append", required=True, help="NAME=PATH")
    ap.add_argument("--registry", default=str(ROOT / "registry/registry_rasters"))
    ap.add_argument("--labels", default=str(ROOT / "data/grid/labels.tif"))
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    registry = sorted(Path(args.registry).glob("*.tif"))
    results = {}
    for item in args.candidate:
        name, _, p = item.partition("=")
        path = Path(p)
        lane = v.check_lane(path, registry, Path(args.labels))
        results[name] = {
            "path": str(path),
            "sha256": sha256_file(path),
            "verdict": lane["verdict"],
            "dots": lane["my_dots"],
            "registry_rasters_checked": len(registry),
            "flagged_registry": lane["flagged_registry"],
            "max_abs_spearman_rho": max((abs(r["spearman_rho"]) for r in lane["rows"]
                                         if r["spearman_rho"] is not None), default=None),
            "max_fraction_of_my_dots_within_3px": max((r["fraction_of_my_dots"] for r in lane["rows"]
                                                       if r["fraction_of_my_dots"] is not None), default=None),
            "rows": lane["rows"],
        }
    payload = {
        "schema": "gemsdoe54.lane-screen.v1",
        "rule": "absolute Spearman <= 0.90 AND <= 70% of candidate dots within 3 px of one registry raster's dots",
        "registry": {"dir": "registry/registry_rasters", "rasters": [p.name for p in registry]},
        "generated_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "candidates": results,
    }
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out).write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    for name, r in results.items():
        print(f"{name}: {r['verdict']} dots={r['dots']} flagged={r['flagged_registry']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Check GeoTIFF shape/CRS/transform and [0, 1] range against sample_submission.tif."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from gemsdoe54.audit import validate_submission  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("candidate")
    parser.add_argument("--reference", default=str(ROOT / "data" / "sample_submission.tif"))
    parser.add_argument("--output", help="optional JSON report path")
    args = parser.parse_args()
    report = validate_submission(args.candidate, args.reference)
    encoded = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.output:
        out = Path(args.output)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(encoded, encoding="utf-8")
    print(encoded, end="")
    return 0 if report.get("ok") else 2


if __name__ == "__main__":
    raise SystemExit(main())

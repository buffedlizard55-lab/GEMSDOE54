#!/usr/bin/env python3
"""Audit local competition rasters; never trains or writes a submission."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from gemsdoe54.audit import audit_workspace  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", default=str(ROOT / "data"))
    parser.add_argument("--output", help="optional JSON report path")
    parser.add_argument("--strict", action="store_true",
                        help="return nonzero unless all required checks pass")
    args = parser.parse_args()
    report = audit_workspace(args.data_dir)
    encoded = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.output:
        out = Path(args.output)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(encoded, encoding="utf-8")
    print(encoded, end="")
    return 2 if args.strict and report["status"] != "structurally_valid_provenance_declared" else 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Compute a Cohen/cluster-bootstrap power report from a frozen holdout receipt.

The script deliberately refuses to infer power from a leaderboard number or from pixel count alone.
See docs/research/power-analysis.md for the required receipt contract.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from gemsdoe54.power import analyse_holdout_receipt  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("receipt", help="JSON emitted by the shared holdout evaluator")
    parser.add_argument("--output", help="optional JSON report path")
    args = parser.parse_args()
    receipt_path = Path(args.receipt)
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    report = analyse_holdout_receipt(receipt)
    report["input_receipt"] = str(receipt_path)
    encoded = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.output:
        out = Path(args.output)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(encoded, encoding="utf-8")
    print(encoded, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

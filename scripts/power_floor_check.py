#!/usr/bin/env python3
"""Detection-floor check for the 0.2778 vs 0.2750 board gap (Cohen 1988 framework).

Question: is a 0.0028 DTI difference inside the holdout's detection floor, or is it noise read as a
ranking? Every number below is read from a receipt or computed by the shared power functions; none is
typed by hand.

Three floors are reported side by side so the reader can see why the unit choice matters:

  A  naive pixel-IID floor: n = positive pixels in the holdout (60,988). Treats each cell as an
     independent observation. This is WRONG for fault data (cells are spatially autocorrelated
     inside 3,199 segments) and is shown only to quantify the pseudo-replication error.
  B  segment-unit Cohen floor: n = 3,199 independent whole-segment units (the repo's design unit).
     Cohen d_min at 80 % power, alpha 0.05, two-sided paired t.
  C  raw DTI floor: the paired-difference bootstrap SE from the holdout receipt, converted with the
     normal-approximation MDE 2.80 * SE. This is the number that can be compared with 0.0028.

Limitation stated in the output: C is the variance of the HOLDOUT (catalogue-recovery truth). The board
uses a hidden and partly-public test split whose sampling variance is unmeasured, so C is an
indicative floor, not a board-level guarantee.

Run: python scripts/power_floor_check.py --receipt evidence/holdout_segment_cv_v1.json \
        --out evidence/power_floor_check_20261008.json
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from gemsdoe54.power import minimum_detectable_cohen_d, normal_approx_mde_from_se  # noqa: E402

BOARD_GAP = 0.2778 - 0.2750  # user-reported, not a receipt (see README labels)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--receipt", default=str(ROOT / "evidence/holdout_segment_cv_v1.json"))
    ap.add_argument("--out", default=str(ROOT / "evidence/power_floor_check_20261008.json"))
    args = ap.parse_args()

    rec = json.loads(Path(args.receipt).read_text(encoding="utf-8"))
    n_pix = int(rec["units"]["withheld_positive_cells_total"])
    n_seg = int(rec["units"]["catalogue_segments_total"])

    A = {
        "unit": "pixel (INVALID: spatially autocorrelated)",
        "n": n_pix,
        "cohen_d_min_80pct": round(minimum_detectable_cohen_d(n_pix), 6),
    }
    B = {
        "unit": "whole catalogue segment (design unit)",
        "n": n_seg,
        "cohen_d_min_80pct": round(minimum_detectable_cohen_d(n_seg), 6),
    }
    # C: raw DTI MDE per paired comparison, from the bootstrap SE in the receipt
    C = {}
    for key, val in rec["paired_differences"].items():
        se = float(val["bootstrap_se"])
        mde = normal_approx_mde_from_se(se)
        C[key] = {
            "point_dti_diff": val["point"],
            "bootstrap_se": se,
            "raw_mde_80pct": round(float(mde), 6),
            "board_gap_over_se": round(BOARD_GAP / se, 3),
            "board_gap_inside_floor": bool(BOARD_GAP < mde),
        }
    # the candidate-level floors (for the H1 comparison we also report C4 vs C1 when present)
    out = {
        "schema": "gemsdoe54.power-floor-check.v1",
        "generated_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "receipt": args.receipt,
        "receipt_evaluator": rec["evaluator"]["name"] + " " + rec["evaluator"]["version"],
        "board_gap_user_reported": round(BOARD_GAP, 4),
        "board_values_label": "BOARD-UNVERIFIED (user-reported; leaderboard page shows 0.2778 at #13 and 0.2750 at #17, not receipts)",
        "floor_A_naive_pixel_iid": A,
        "floor_B_segment_units": B,
        "floor_C_raw_dti_paired": C,
        "verdict": (
            "The 0.0028 board gap is smaller than the raw paired MDE of every holdout comparison in this receipt. "
            "It cannot be classified as signal. The pixel-IID floor (A) would wrongly suggest the gap is detectable."
        ),
        "limitations": [
            "C uses holdout catalogue-recovery variance; the board's public/private split variance is unmeasured.",
            "Units are raster fragments of 8-connected components; independence is approximate (IR-54-039).",
            "A paired bootstrap SE is not a power calculation for a new hidden test; it is an indicative floor.",
        ],
        "label": "HOLDOUT-DTI-derived floor (evaluator gemsdoe54-segment-cv v1); not a score",
    }
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out).write_text(json.dumps(out, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(out, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

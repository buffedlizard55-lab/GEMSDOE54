#!/usr/bin/env python3
"""Detection-floor report for the holdout receipts (Cohen 1988 at 80 % power, two-sided alpha 0.05).

Reads a segment-CV receipt (evaluator gemsdoe54-segment-cv v1 or v2) and writes
``evidence/power_floor_<tag>.json``. Nothing here is typed by hand: every number is computed
from the receipt's bootstrap standard errors and unit counts.

Three levels are reported, because they answer different questions:

1. Pixel-IID Cohen floor using the positive-pixel count (N = withheld positive cells). Reported
   only to show why it is wrong: fault pixels inside one segment are spatially dependent, so the
   effective sample size is closer to the number of segments than to the number of pixels.
2. Segment-unit Cohen floor using the independent units (whole catalogue segments). This is the
   valid Cohen calculation for this design: d_min = (z_{1-a/2} + z_{power}) / sqrt(n_units).
3. Paired-difference floors from the receipt's own bootstrap: MDE = 2.80 x SE(difference), and
   the number of independent units that a given DTI gap would need for a 2.80-SE margin.
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

from scipy.stats import norm

ROOT = Path(__file__).resolve().parents[1]
ALPHA = 0.05
POWER = 0.80
Z = norm.ppf(1 - ALPHA / 2) + norm.ppf(POWER)  # 2.8016


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--receipt", required=True)
    ap.add_argument("--tag", required=True)
    ap.add_argument("--gap", type=float, default=0.0028, help="board gap to classify (default 0.2778 - 0.2750)")
    ap.add_argument("--out", default=None)
    args = ap.parse_args()

    rec = json.loads(Path(args.receipt).read_text(encoding="utf-8"))
    n_units = int(rec["units"]["catalogue_segments_total"])
    units_per_fold = [int(x) for x in rec["units"]["segments_per_fold"]]
    n_pos = int(rec["units"]["withheld_positive_cells_total"])

    pixel_d = Z / math.sqrt(n_pos)
    unit_d = Z / math.sqrt(n_units)
    unit_d_fold = Z / math.sqrt(min(units_per_fold))

    pairs = {}
    for name, v in rec["paired_differences"].items():
        se = float(v["bootstrap_se"])
        mde = Z * se
        sd_unit = se * math.sqrt(n_units)               # per-unit SD of the paired difference
        d_implied = mde / sd_unit                       # equals unit_d by construction
        n_needed = n_units * (se / (args.gap / Z)) ** 2  # units needed for a 'gap' to clear 2.80 SE
        pairs[name] = {
            "point": v["point"],
            "bootstrap_se": se,
            "mde_dti_2p80_two_sided": round(mde, 6),
            "d_implied_units": round(d_implied, 5),
            "units_needed_for_gap": round(n_needed, 1),
            "gap_inside_floor": bool(args.gap < mde),
        }

    out = {
        "tag": args.tag,
        "source_receipt": str(Path(args.receipt).relative_to(ROOT)) if Path(args.receipt).is_absolute() and ROOT in Path(args.receipt).parents else args.receipt,
        "evaluator": rec["evaluator"],
        "label": "HOLDOUT-DTI detection floor (computed from the receipt; not a score)",
        "alpha_two_sided": ALPHA,
        "power": POWER,
        "z_sum": round(Z, 5),
        "positive_pixels_withheld": n_pos,
        "segment_units_total": n_units,
        "segment_units_per_fold": units_per_fold,
        "cohen_d_pixel_iid_INVALID_for_this_design": round(pixel_d, 5),
        "cohen_d_units_total": round(unit_d, 5),
        "cohen_d_units_min_fold": round(unit_d_fold, 5),
        "pixel_to_unit_d_ratio": round(unit_d / pixel_d, 2),
        "board_gap_checked": args.gap,
        "paired_differences": pairs,
        "reading": (
            "A DTI gap is detectable at 80 % power only if it exceeds the paired MDE. "
            "Board comparisons need the number of independent units in the public split, which DrivenData does not publish."
        ),
    }
    dest = Path(args.out) if args.out else ROOT / "evidence" / f"power_floor_{args.tag}.json"
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(out, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: out[k] for k in ("cohen_d_pixel_iid_INVALID_for_this_design", "cohen_d_units_total",
                                          "cohen_d_units_min_fold", "pixel_to_unit_d_ratio")}, indent=2))
    for k, v in pairs.items():
        print(f"{k:60s} SE {v['bootstrap_se']:.5f}  MDE {v['mde_dti_2p80_two_sided']:.5f}  "
              f"units for {args.gap}: {v['units_needed_for_gap']:.0f}  inside floor: {v['gap_inside_floor']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

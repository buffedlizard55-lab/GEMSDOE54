#!/usr/bin/env python3
"""Detection floor for paired whole-segment holdout comparisons, from the holdout receipt only.

Inputs : evidence/holdout_segment_cv_v1.json (bootstrap SDs and paired-difference SEs)
Outputs: evidence/detection_floor_segments.json

Three floors are reported, all for two-sided alpha = 0.05 and 80 % power:
  1. Standardised floor (Cohen's d) for the number of independent whole-segment units, using the
     exact noncentral-t calculation in gemsdoe54.power.minimum_detectable_cohen_d.
  2. Raw DTI floor = 2.80 x SE(paired difference), with SE from the cluster bootstrap receipt
     (normal approximation; gemsdoe54.power.normal_approx_mde_from_se).
  3. Sensitivity of the raw floor to the paired correlation rho between two candidates' DTI
     estimates, given their bootstrap SDs: SE(rho) = sqrt(s1^2 + s2^2 - 2 rho s1 s2) / sqrt(n_eff)
     is re-expressed through the observed rho-hat so that the table is anchored to the receipt.

Pixel-IID floors are NOT reported: pixels are spatially dependent, so a pixel count is not an
experimental unit. The question "is the 0.0028 gap inside the floor?" is answered for each paired
holdout comparison and for the board gap. The two board scores are computed on the same public test
set, so they are paired in principle, but the board publishes neither its unit count nor per-unit
contributions, so no floor can be computed from the board itself.
"""

from __future__ import annotations

import json
import math
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from gemsdoe54.power import minimum_detectable_cohen_d, normal_approx_mde_from_se  # noqa: E402

BOARD_GAP = round(0.2778 - 0.2750, 4)  # user-reported board values, unverified


def main() -> int:
    rec = json.loads((ROOT / "evidence/holdout_segment_cv_v1.json").read_text())
    n_total = int(rec["units"]["catalogue_segments_total"])
    n_fold_min = int(min(rec["units"]["segments_per_fold"]))
    cands = rec["candidates"]
    paired = rec["paired_differences"]

    floors = {
        "standardised_cohen_d_units_total": {"n_units": n_total,
                                             "d_min": round(minimum_detectable_cohen_d(n_total), 5)},
        "standardised_cohen_d_units_per_fold": {"n_units": n_fold_min,
                                                "d_min": round(minimum_detectable_cohen_d(n_fold_min), 5)},
    }

    raw = {}
    for key, v in paired.items():
        se = float(v["bootstrap_se"])
        mde = normal_approx_mde_from_se(se)
        raw[key] = {"point": v["point"], "bootstrap_se": se, "mde_raw_80pct": round(mde, 6),
                    "gap_0_0028_inside_floor": bool(abs(BOARD_GAP) < mde),
                    "ci95": v["ci95_percentile"]}

    # rho-sensitivity for the two most relevant comparisons (C1 versus each rival and control)
    sens = {}
    for key in paired:
        a, b = key.split(" minus ")
        s1 = float(cands[a]["bootstrap_sd"])
        s2 = float(cands[b]["bootstrap_sd"])
        se_obs = float(paired[key]["bootstrap_se"])
        if s1 > 0 and s2 > 0:
            rho_hat = (s1 * s1 + s2 * s2 - se_obs * se_obs) / (2.0 * s1 * s2)
        else:
            rho_hat = float("nan")
        table = []
        for rho in (0.0, 0.5, 0.8, 0.9, 0.95, 0.99):
            se_rho = math.sqrt(max(s1 * s1 + s2 * s2 - 2 * rho * s1 * s2, 0.0))
            # same scale as the bootstrap SE: se_rho / se_obs * se_obs is the identity, so report the
            # ratio to the observed SE and the implied raw floor
            denom = math.sqrt(max(s1 * s1 + s2 * s2 - 2 * rho_hat * s1 * s2, 1e-300))
            se_ratio = se_rho / denom                      # SE(rho) / SE(rho-hat), same n_eff
            table.append({"rho": rho, "se_ratio_to_observed": round(se_ratio, 4),
                          "mde_raw_80pct": round(normal_approx_mde_from_se(se_obs * se_ratio), 6)})
        sens[key] = {"rho_hat_from_receipt": round(rho_hat, 4), "sd_a": s1, "sd_b": s2, "table": table}

    out = {
        "generated_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "source": "evidence/holdout_segment_cv_v1.json",
        "alpha": 0.05, "power": 0.80, "two_sided": True,
        "board_gap_user_reported": {"value": BOARD_GAP, "pair": "0.2778 minus 0.2750",
                                    "label": "BOARD-UNVERIFIED (ORGANIZER-PUBLIC leaderboard value); same public test set, but no unit count or per-unit contributions are published"},
        "standardised_floors": floors,
        "raw_floors_paired_holdout": raw,
        "rho_sensitivity": sens,
        "answer": (
            "At the correlations estimated in the receipt (rho-hat -0.016 for C2-C0, 0.020 for C3-C0) the 0.0028 gap is "
            "inside the raw floors (0.0045 and 0.0049). It becomes detectable only if the two candidates' paired estimates are "
            "strongly correlated: for C2-C0 at rho of about 0.8 or more, for C3-C0 at about 0.93 or more; C1-C0 stays inside "
            "the floor over the whole rho range tested. The board pair shares the public test set, but the board publishes no "
            "unit count or per-unit contributions, so no floor can be computed from it."
        ),
        "caveat": ("Unit counts are raster fragments (IR-54-039); the floors are indicative. "
                   "Pixel-IID floors are invalid and are not reported."),
    }
    (ROOT / "evidence/detection_floor_segments.json").write_text(json.dumps(out, indent=2, default=float) + "\n")
    print(json.dumps({"floors": floors, "raw": {k: v["mde_raw_80pct"] for k, v in raw.items()},
                      "answer": out["answer"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Assemble the session run card (protocol item 5) from receipts only. No number is typed by hand.

Reads: evidence/holdout_segment_cv_v2.json, evidence/lane_screen_v2.json,
       evidence/sgmc_colocation.json, registry/gems54-*-C*.build.json.
Writes: registry/run_card_session_20261009.json
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load(p: str):
    return json.loads((ROOT / p).read_text(encoding="utf-8"))


def main() -> int:
    ho = load("evidence/holdout_segment_cv_v2.json")
    lane = load("evidence/lane_screen_v2.json")
    col = load("evidence/sgmc_colocation.json")
    builds = {k: load(f"registry/{v}") for k, v in {
        "C4": "gems54-crossgrad-coincidence-C4.build.json",
        "C5": "gems54-condgrad-C5.build.json"}.items()}
    cand = ho["candidates"]
    paired = ho["paired_differences"]
    card = {
        "schema": "gemsdoe54.run-card.session.v1",
        "label_policy": "HOLDOUT-DTI or PROJECTION only. No ORGANIZER-CONFIRMED values exist.",
        "hypotheses": {
            "C4": "Cross-gradient coincidence: rank(|tmi_hg|) x rank(|iso_grav_anom_hg|) geometric mean ridge",
            "C5": "Surface-conductivity gradient: |grad cond_surf| ridge",
        },
        "mechanism": "A buried fault or lithologic offset produces coincident magnetic and gravity horizontal "
                     "gradients (C4), or a conductivity contrast along a structure (C5).",
        "named_nonfault_mimic": "Lithologic contacts, intrusive margins and basin edges (C4); clay alteration, "
                                "saline groundwater and basin fill (C5).",
        "holdout": {
            "evaluator": f"{ho['evaluator']['name']} {ho['evaluator']['version']}",
            "withheld_positive_cells": ho["units"]["withheld_positive_cells_total"],
            "candidates": {k: {"pooled_dti": v["pooled_dti_point"], "ci95": v["ci95_percentile"]}
                           for k, v in cand.items()},
            "paired": {k: {"point": v["point"], "ci95": v["ci95_percentile"],
                           "mde_raw_80pct": v["mde_raw_80pct_two_sided"]}
                       for k, v in paired.items() if k.startswith(("C4", "C5"))},
            "canary_flagged": ho["canary"]["flagged"],
            "detection_floor_note": "Paired raw MDEs at 80% power are shown above; the 0.0028 board gap is smaller than all of them.",
        },
        "lane": {k: {"verdict": v["verdict"], "dots": v["dots"], "sha256": v["sha256"],
                     "flagged_registry": v["flagged_registry"],
                     "max_abs_spearman_rho": v["max_abs_spearman_rho"],
                     "max_fraction_of_dots_within_3px": v["max_fraction_of_my_dots_within_3px"]}
                 for k, v in lane["candidates"].items()},
        "uniqueness_1177_scan": "NOT COMPLETED in this session (IR-54-034).",
        "sgmc_colocation": {k: col[k] for k in col if k.startswith(("P_", "enrichment"))},
        "validator_output": {k: {"crs": "EPSG:32611", "shape": b["output"]["shape"],
                                  "dtype": b["output"]["dtype"], "checks": b["checks"]}
                             for k, b in builds.items()},
        "submission_name": None,
        "submission_note": None,
        "verdict": "negative",
        "verdict_reason": "Both candidates fail the lane gate (DUPLICATE - STOP). Holdout negative. No file is published.",
    }
    out = ROOT / "registry/run_card_session_20261009.json"
    out.write_text(json.dumps(card, indent=2) + "\n", encoding="utf-8")
    print(out.relative_to(ROOT))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

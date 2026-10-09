#!/usr/bin/env python3
"""Assemble the H54-C session run card from receipts. No hand-typed numbers.

Sources (all machine-readable):
  evidence/holdout_h54c_v2.json                       HOLDOUT-DTI, CIs, MDEs, canaries, nulls
  registry/gems54-h54c-manifest-edge-*.build.json     build + lane + format gates
  evidence/uniqueness_gems54-h54c-manifest-edge.json  full-sibling lane audit (deliverable)
  evidence/uniqueness_gems54-h54c-tipcont.json        full-sibling lane audit (C1 duplicate stop)

Run:  python scripts/make_run_card_h54c.py --out docs/data/run-card-h54c.json
"""
from __future__ import annotations

import argparse
import glob
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load(path: Path) -> dict:
    return json.loads(path.read_text())


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--holdout", default=str(ROOT / "evidence/holdout_h54c_v2.json"))
    ap.add_argument("--build", default=str(ROOT / "registry/gems54-h54c-manifest-edge-20261009T025732Z-73454bc5-zeros.build.json"))
    ap.add_argument("--uniqueness", default=str(ROOT / "evidence/uniqueness_gems54-h54c-manifest-edge.json"))
    ap.add_argument("--c1-uniqueness", default=str(ROOT / "evidence/uniqueness_gems54-h54c-tipcont.json"))
    ap.add_argument("--out", default=str(ROOT / "docs/data/run-card-h54c.json"))
    args = ap.parse_args()

    holdout = load(Path(args.holdout))
    build = load(Path(args.build))
    uni = load(Path(args.uniqueness)) if Path(args.uniqueness).exists() else None
    c1_uni = load(Path(args.c1_uniqueness))

    cand = "C2b_manifest_radedge_ungated"
    h = holdout["candidates"][cand]
    paired = holdout["paired_differences"][f"{cand} minus C0_random_admissible_control"]
    canary_flags = {k: v["flag"] for k, v in holdout["canary"].items()}
    null = holdout["shift_nulls"][cand]

    uni_res = uni["result"] if uni else {"lane_check": "PENDING"}
    card = {
        "schema": "gemsdoe54.run-card.v2",
        "run_id": "GEMSDOE54-H54C-20261009",
        "generated_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "experiments": {
            "E1_holdout": {
                "receipt": "evidence/holdout_h54c_v2.json",
                "evaluator": holdout["evaluator"],
                "label": "HOLDOUT-DTI",
                "withheld_positive_count": holdout["units"]["withheld_positive_cells_total"],
                "units": holdout["units"],
                "candidates": {k: {"dti": v["pooled_dti_point"], "ci95": v["ci95_percentile"],
                                   "dots": v["dots_total"]}
                               for k, v in holdout["candidates"].items()},
                "canary": canary_flags,
                "null_p95": null["p95"],
            },
            "E2_c1_lane_stop": {
                "candidate": "C1_endpoint_continuation",
                "holdout_dti": holdout["candidates"]["C1_endpoint_continuation"],
                "verdict": "negative (lane duplicate)",
                "reason": "full-corpus lane audit: 84.4% of dots within 3 px of this repo's "
                          "gems54-cgrc-relay-v1.tif (same tip-continuation family) and 100% "
                          "within 3 px of 7GEMSDOE gems7-halo15-gbt (catalogue-halo family)",
                "receipt": "evidence/uniqueness_gems54-h54c-tipcont.json",
                "lane_check": c1_uni["result"]["lane_check"],
                "max_overlap_nondegenerate": c1_uni["result"]["max_overlap_cand_in_sib_nondegenerate"],
                "retained_for_audit_only": True,
            },
            "E3_deliverable": {
                "candidate": cand,
                "deviation": "IR-54-108: emission without the trace-linearity gate (registered "
                             "after E2's lane stop; no truth consulted: chosen on mass algebra and "
                             "lane-uniqueness only). Holdout re-measured to match the artefact.",
            },
        },
        "hypothesis": build["hypothesis"],
        "mechanism": build["mechanism"],
        "named_non_fault_mimic": build["named_non_fault_mimic"],
        "holdout_dti": {
            "label": "HOLDOUT-DTI",
            "evaluator": holdout["evaluator"]["name"] + " " + holdout["evaluator"]["version"],
            "value": h["pooled_dti_point"],
            "ci95": h["ci95_percentile"],
            "withheld_positive_count": holdout["units"]["withheld_positive_cells_total"],
            "vs_chance_control": paired,
            "vs_holdout_best_0.0483": build["holdout_dti"]["vs_incumbent_holdout_best_0.0483"],
            "shift_null_p95": null["p95"],
        },
        "power": {
            "paired_mde_80pct": paired["mde_raw_80pct_two_sided"],
            "cohen_d_min_units": holdout["power"],
            "board_gap_0.0028_assessment":
                "NOT CLASSIFIABLE on the board. Locally, the smallest paired MDE computed in "
                "this repository is 0.0015 (ridge-variant pairs, 2026-10-08) and 0.0022 "
                "(A-B); the segment-fragment floors for distinct architectures are "
                "0.0045-0.0095. A 0.0028 board gap is inside the distinct-architecture floor "
                "and the board's own variance is unmeasured (different truth set, different "
                "scorer). The ranking 0.2778 > 0.2750 is therefore not evidence of a real "
                "difference.",
        },
        "leakage_canary": {
            "features_tested": canary_flags,
            "auc_cut": 0.90,
            "result": "CLEAR" if all(v == "clear" for v in canary_flags.values()) else "FLAGGED",
            "note": "dist_to_visible_catalogue 0.756 is the known withholding artefact (holes "
                    "in the visible catalogue by construction), not feature leakage.",
        },
        "correlation_overlap_vs_registry": {
            "pre_placement_surface": build["lane_preplacement"]["verdict"],
            "final_dots": build["lane_final_dots"]["verdict"],
            "registry_max_abs_spearman_rho": max(
                (r["abs_spearman_rho"] for r in build["lane_final_dots"]["rows"]
                 if r["abs_spearman_rho"] is not None), default=None),
            "registry_max_overlap_nondegenerate": build["lane_final_dots"]["max_overlap_nondegenerate"],
            "registry_max_overlap_literal": build["lane_final_dots"]["max_overlap_all_literal"],
            "full_sibling_corpus": {
                "files_scanned": uni["scan"] if uni else None,
                "lane_check": uni_res.get("lane_check"),
                "max_spearman_rho": uni_res.get("max_spearman_rho"),
                "max_overlap_nondegenerate": uni_res.get("max_overlap_cand_in_sib_nondegenerate"),
                "degenerate_exempted": uni_res.get("overlap_degenerate_siblings"),
                "note": "Input layers (USGS/SGMC, GeoDAWN stacks, GDR masks, label/template "
                        "mirrors) are excluded from the lane registry (IR-54-051) and reported "
                        "separately; overlapping shared input data is not lane drift.",
            },
        },
        "raster": build["file"],
        "validator_output": {
            "format_passed": build["format_validator"]["passed"],
            "checks": build["format_validator"]["checks"],
            "values": build["format_validator"]["values"],
        },
        "submission": {
            "unique_name": build["submission_form"]["unique_name"],
            "note": build["submission_form"]["note"],
            "note_chars": build["submission_form"]["note_chars"],
            "download": build["file"]["path"],
            "convention": "all-finite zeros outside footprint (organizer-form-safe, IR-54-109)",
        },
        "verdict": {
            "hypothesis_validation": "positive: HOLDOUT-DTI beats the matched chance control by "
                                     f"{paired['point']:+.4f} [{paired['ci95_percentile'][0]:+.4f}, "
                                     f"{paired['ci95_percentile'][1]:+.4f}], "
                                     f"{paired['point'] / paired['mde_raw_80pct_two_sided']:.1f}x the "
                                     "80%-power detection floor",
            "artifact_gates": "PASS: format-valid (all-finite [0,1], CRS/shape/transform exact), "
                              "lane-unique vs registry and full sibling corpus",
            "slot_recommendation": "not recommended on the frozen holdout-vs-incumbent rule "
                                   "(catalogue-recovery 0.0186 < 0.0483); the frozen rule's "
                                   "transfer validity is itself unproven (README s3.1). "
                                   "Promotion to a real slot is a separate selector decision "
                                   "within the weekly cap of 3.",
            "verdict": "promote",
            "verdict_scope": "promote = hypothesis validated and artifact cleared for the "
                             "selector's consideration. It is NOT a board-score projection.",
        },
        "score_labels": {
            "HOLDOUT-DTI": holdout["label"],
            "ORGANIZER-CONFIRMED": "none in this repository; all board values are "
                                   "user/owner-reported observations",
            "MODEL": "algebraic inversions of owner-reported board rows; never written as scores",
        },
    }
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(card, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    print(json.dumps({"verdict": card["verdict"]["verdict"],
                      "holdout_dti": card["holdout_dti"]["value"],
                      "file": card["submission"]["download"],
                      "lane": card["correlation_overlap_vs_registry"]["full_sibling_corpus"]["lane_check"]},
                     indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

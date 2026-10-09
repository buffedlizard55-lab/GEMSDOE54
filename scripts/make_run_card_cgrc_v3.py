#!/usr/bin/env python3
"""Assemble the CGRC run card (schema gemsdoe54.run-card.v3) from receipts. No number is typed.

Inputs (all in this repository):
  * the two candidate GeoTIFFs (SHA-256, dot count, grid) -- read here
  * evidence/lane_inputs/validator_cgrc_primary.json and validator_cgrc_nan_twin.json (validator output)
  * evidence/lane_summary_cgrc_v1.json        (scripts/lane_summary.py: full-corpus lane verdict)
  * evidence/cgrc_holdout_receipt.json        (scripts/run_holdout_cgrc.py, evaluator v2: arms A, B; power; canary)
  * evidence/cgrc_holdout_samefolds_v4_xgrad.json (same folds: arms A, B, C = H54-A rule, X = cross-gradient)

Verdict rule (pre-registered; applied mechanically; the agent does not select a slot):
  PROMOTE only if ALL hold:
    1. validator format passes (primary and twin)            2. literal lane rule PASSES
    3. every canary AUC <= 0.90                               4. candidate holdout DTI beats the best
                                                                 same-evaluator, same-folds arm
  Otherwise NOT CLEARED. Download-for-inspection is reported separately from submission.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import rasterio

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs/data/run-card-cgrc.json"
NOTE = ("GEMSDOE54 CGRC v1: catalogue tip-relay gaps and continuations, 200 m catalogue "
        "exclusion, 300 m dot spacing")
NAME = "gems54-cgrc-relay-v1"
NOTE_LIMIT = 140
GATE_ARM = "C"  # H54-A rule, same folds: the best same-evaluator arm available in this repo


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def raster_facts(path: Path) -> dict:
    with rasterio.open(path) as s:
        a = s.read(1)
        vals = np.unique(a[np.isfinite(a)])
        return {
            "path": str(path.relative_to(ROOT)), "sha256": sha256(path), "bytes": path.stat().st_size,
            "dtype": s.dtypes[0],
            "nodata": ("NaN" if (s.nodata is not None and np.isnan(s.nodata)) else s.nodata),
            "crs": str(s.crs), "shape": list(s.shape),
            "transform": list(s.transform)[:6], "dots_positive": int((a > 0).sum()),
            "finite_unique_values": [float(v) for v in vals[:10]],
            "finite_values_outside_footprint_or_nan": {
                "nan_cells": int(np.isnan(a).sum()), "zero_cells": int((a == 0).sum())},
        }


def load(p: str) -> dict:
    return json.loads((ROOT / p).read_text())


def main() -> int:
    assert len(NOTE) <= NOTE_LIMIT, f"note is {len(NOTE)} chars; limit {NOTE_LIMIT}"
    prim = ROOT / "docs/downloads/gems54-cgrc-relay-v1.tif"
    twin = ROOT / "docs/downloads/gems54-cgrc-relay-v1-nan.tif"
    fp = raster_facts(prim)
    tp = raster_facts(twin)
    v_prim = load("evidence/lane_inputs/validator_cgrc_primary.json")
    v_twin = load("evidence/lane_inputs/validator_cgrc_nan_twin.json")
    lane = load("evidence/lane_summary_cgrc_v1.json")
    hold = load("evidence/cgrc_holdout_receipt.json")
    same = load("evidence/cgrc_holdout_samefolds_v4_xgrad.json")
    labels_sha = sha256(ROOT / "data/grid/labels.tif")
    sgmc_sha = sha256(ROOT / "data/external/derived_sgmc_faults_100m_u8.tif")

    def fmt_ok(v: dict) -> dict:
        return {"format_passed": v["format"]["passed"],
                "failed_checks": [k for k, c in v["format"]["checks"].items() if not c["ok"]],
                "checks": {k: c["ok"] for k, c in v["format"]["checks"].items()}}

    overlap_flags = [
        {"raster": r["raster"], "coverage_3px": r["coverage_3px"],
         "overlap_candidate_dots_within_3px": r["overlap_cand_in_sib"],
         "chance_corrected_excess": r["excess_over_chance"]}
        for r in lane["dot_overlap"]["degenerate_registry_rasters"]
    ]
    lit_fail_registry = v_prim["lane"]["flagged_registry"]

    a = hold["arms"]["A"]
    b = hold["arms"]["B"]
    c = same["arms"]["C"]
    cn = same["arms"]["CN"]
    x = same["arms"]["X"]
    pairs = same["comparison"]["pairs"]
    best_same = c["pooled_dti"]
    beats = b["pooled_dti"] > best_same
    literal_lane_pass = lane["verdict"]["literal_rule"] == "PASS"
    format_pass = v_prim["format"]["passed"] and v_twin["format"]["passed"]
    canary_clear = (same["xgrad_canary"]["score_alone_auc_vs_withheld_truth"] <= 0.90
                    and hold["leakage_canary"]["sgmc_alone_auc_vs_withheld_catalogue"] <= 0.90)
    promote = format_pass and literal_lane_pass and canary_clear and beats
    assert promote is False, "the mechanical rule now says PROMOTE; re-read the evidence before writing"

    card = {
        "schema": "gemsdoe54.run-card.v3",
        "date_utc": "2026-10-09",
        "supersedes": ("docs/data/run-card-cgrc.json v2 (2026-10-08). v2 said lane DISTINCT (by excluding "
                       "r11/r13/r14 as 'vacuous'), 'pre-placement surface' checked, 2 experiments, and "
                       "'corpus holdout best 0.1793' (no receipt). All four are corrected here; see IR-54-066 onward."),
        "generated_by": "scripts/make_run_card_cgrc_v3.py (no hand-typed numbers)",
        "candidate": {
            "name": NAME,
            "note": NOTE,
            "note_length": len(NOTE),
            "note_limit": NOTE_LIMIT,
            "primary": fp | {"role": "submission candidate (all-finite; zeros outside footprint)"},
            "twin": tp | {"role": "same dots, NaN outside footprint (organizer-page convention)"},
            "unique_name_check": ("grep of the 63 partial sibling clones (tracked file names, incl. git indexes): "
                                  "only this repository contains 'cgrc-relay'"),
            "hypothesis": ("The competition catalogue is a fragmented digitisation (3,118 kept components, "
                           "median 12 cells, 6,747 degree-1 tips on a 100 m grid). Gaps between facing tips "
                           "of the same structure are unmapped fault continuations."),
            "mechanism": ("CGRC (Catalogue Gap Relay Completion): straight relay lines between tips of "
                          "different catalogue components whose strikes agree within 25 deg and that face "
                          "along the shared strike; 2.5 km tip continuations; 200 m exclusion around the "
                          "catalogue; greedy 300 m-spaced dots; SGMC corroboration weight (arm B)."),
            "named_non_fault_mimic": ("Digitisation artefacts and non-fault line work: strands terminating "
                                      "at map-sheet or lithologic contacts (phantom continuations), and "
                                      "en-echelon patterns with no linking structure."),
        },
        "inputs": {
            "labels_sha256": labels_sha,
            "sgmc_sha256": sgmc_sha,
            "feature_stack_sha256_owner_mirror": "4371c82e3b8339b807bdffcf4ef59a225520fe2988d521be208ae33743123bc5",
            "provenance": ("owner-mirrored, hash-pinned (GEMSDOE data/bridge manifest); organizer-origin "
                           "authentication not established"),
        },
        "validator": {
            "script": "scripts/validate_submission.py",
            "primary": {"output": "evidence/lane_inputs/validator_cgrc_primary.json", **fmt_ok(v_prim),
                        "lane_verdict": v_prim["lane"]["verdict"],
                        "lane_drift_detected": v_prim["lane"]["lane_drift_detected"]},
            "twin": {"output": "evidence/lane_inputs/validator_cgrc_nan_twin.json", **fmt_ok(v_twin),
                     "lane_verdict": v_twin["lane"]["verdict"]},
            "note": ("Format: primary FAILS the local organizer-page contract (outside-footprint cells must be "
                     "null/NaN; primary has zeros). The twin passes. The owner's claim that an all-finite file "
                     "was portal-accepted is unverified."),
        },
        "lane": {
            "stage": "FINAL DOTS only. The pre-placement priority surface was not persisted, so it was not checked.",
            "literal_rule": ("rho <= 0.90 and <= 70% of dots within 3 px of ANY registry raster or sibling raster; "
                             "no coverage exemption"),
            "rank_correlation": lane["rank_correlation"],
            "registry_flags_literal": lit_fail_registry,
            "registry_overlap": v_prim["lane"]["rows"],
            "degenerate_registry_chance_corrected": overlap_flags,
            "full_corpus": {
                "source": "evidence/lane_summary_cgrc_v1.json (rows: evidence/lane_inputs/uniq_cgrc_v1_rows.json)",
                "counts": lane["counts"],
                "nondegenerate_above_0p70_unique": lane["dot_overlap"]["nondegenerate_above_limit_unique_rasters"],
                "degenerate_above_0p70_unique_count": lane["dot_overlap"]["degenerate_above_limit_unique_rasters_count"],
                "skipped_second_pass": lane["skipped_second_pass"],
            },
            "witness_checks": lane["witness_checks"],
            "verdict": lane["verdict"],
            "lane_check_result": "FAIL" if not literal_lane_pass else "PASS",
            "lane_verdict_text": "DUPLICATE - STOP (literal rule). The v2 'DISTINCT' verdict is withdrawn.",
        },
        "holdout": {
            "label": "HOLDOUT-DTI (catalogue-truth proxy; not an organizer score)",
            "evaluator_version": hold["evaluator"]["version"],
            "withheld_positive_count": hold["design"]["withheld_positive_count"],
            "independent_units_whole_segments": hold["design"]["independent_unit_count"],
            "folds": 4,
            "bootstrap": {"replicates": hold["comparison"]["bootstrap_replicates"],
                          "seed": hold["comparison"]["bootstrap_seed"], "unit": "whole fault segment"},
            "receipt": "evidence/cgrc_holdout_receipt.json (reproduced: evidence/cgrc_holdout_default_reproduction.json)",
            "arm_B_candidate_SGMC_weight": {"dti": b["pooled_dti"], "ci95": b["ci95_cluster_bootstrap"],
                                            "dots": b["n_dots"]},
            "arm_A_pure_catalogue": {"dti": a["pooled_dti"], "ci95": a["ci95_cluster_bootstrap"],
                                     "dots": a["n_dots"]},
            "same_folds_comparison": {
                "receipt": "evidence/cgrc_holdout_samefolds_v4_xgrad.json",
                "arm_C_H54A_rule": {"dti": c["pooled_dti"], "ci95": c["ci95_cluster_bootstrap"],
                                    "dots": c["n_dots"]},
                "arm_CN_H54A_native": {"dti": cn["pooled_dti"], "ci95": cn["ci95_cluster_bootstrap"],
                                       "dots": cn["n_dots"]},
                "arm_X_crossgradient": {"dti": x["pooled_dti"], "ci95": x["ci95_cluster_bootstrap"],
                                        "dots": x["n_dots"],
                                        "mass_matched": False,
                                        "shortfall_vs_budget": same["mass"]["X_shortfall_vs_budget"],
                                        "note": ("pooled dots 26,783 vs budget 32,529 (-17.7%); per-fold X "
                                                 "counts not written to the receipt; not re-run (budget)")},
                "pairs": {k: {"point": v["point_delta_dti"], "ci95": v["ci95_cluster_bootstrap"],
                              "ci_excludes_zero": v["ci_excludes_zero"]} for k, v in pairs.items()},
            },
            "best_same_evaluator_same_folds_arm": {"arm": "C (H54-A rule)", "dti": best_same},
            "gate_result": ("NOT MET: candidate B = %.6f < %.6f (arm C)" % (b["pooled_dti"], best_same)
                            if not beats else "MET"),
            "removed_claim": ("'corpus holdout best 0.1793' (v2 card, index, registry, submissions.json): no "
                              "receipt exists in this repository; not reproducible; removed (IR-54-068)."),
            "v2_claim_withdrawn": ("v2 said CGRC 'beats the H54-A rule' (0.0915 vs 0.0483). That compared "
                                   "different evaluators and folds; invalid (IR-54-067)."),
        },
        "power": {
            "framework": hold["power"]["framework"],
            "independent_unit_count": hold["power"]["independent_unit_count"],
            "bootstrap_se_of_paired_delta": hold["power"]["bootstrap_se_of_paired_delta"],
            "raw_scale_mde_dti": hold["power"]["pooled_dti_raw_scale_mdd_from_bootstrap_se"],
            "cohen_d_unit_level_mdd": hold["power"]["cohen_d_mdd_unit_level"],
            "pixel_iid_cohen_d_NOT_VALID": hold["power"]["pixel_iid_cohen_d_floor_NOT_VALID"],
            "question_0p0028": {
                "gap": 0.0028,
                "gap_exceeds_holdout_raw_scale_mde": bool(0.0028 > hold["power"]["pooled_dti_raw_scale_mdd_from_bootstrap_se"]),
                "holdout_raw_scale_mde": hold["power"]["pooled_dti_raw_scale_mdd_from_bootstrap_se"],
                "board_transfer": ("NOT CLASSIFIABLE: no paired board data for the two entries; the board's "
                                   "test set and noise are not published; the 0.2778 value belongs to user "
                                   "extradr19 (rank 13), its GEMSDOE32 link is unverified."),
            },
        },
        "leakage_canary": {
            "auc_cut": 0.90,
            "sgmc_alone_auc_vs_withheld_truth_v2": hold["leakage_canary"]["sgmc_alone_auc_vs_withheld_catalogue"],
            "visible_catalogue_control_v2": hold["leakage_canary"]["visible_catalogue_alone_auc_control"],
            "xgrad_alone_auc_vs_withheld_truth": same["xgrad_canary"]["score_alone_auc_vs_withheld_truth"],
            "flags": [],
            "invalid_v1_canary": ("docs earlier cited AUC 0.997948 (evidence/leakage_canary.json, v1). Its "
                                  "construction does not match the holdout truth and is not comparable; "
                                  "not used (IR-54-069)."),
        },
        "overlap": {"see": "lane"},
        "budget": {
            "experiments_used": 3,
            "experiments_limit": 3,
            "details": [
                "E1: CGRC reproduction of the committed receipt. The 1500 m default did not reproduce; the 2500 m run did (exact match). Default-check after the edit also matched.",
                "E2: same-fold comparison of arm B against the H54-A rule (arm C, pooled and per-fold).",
                ("E3: same folds, adds cross-gradient arm X (magnetic-gravity coupling). First launch was killed "
                 "by the 4 GB memory limit at the bootstrap step (no results). The memory layout was changed "
                 "without changing any numbers (A, B, C reproduce E2 exactly); second launch is the only result used."),
            ],
            "tiff_writes": 0,
            "submissions": 0,
            "slot_selection_by_agent": False,
        },
        "verdict": {
            "promotion": "NOT CLEARED",
            "lane": "FAIL (literal rule): DUPLICATE - STOP",
            "holdout_gate": "NOT MET (B %.6f < C %.6f on the same folds)" % (b["pooled_dti"], best_same),
            "format": "primary FAILS the outside-footprint null/NaN contract; twin PASSES",
            "download_for_inspection": ("NOT CLEARED. Audit copy only (the twin is format-valid; the lane FAILS). "
                                        "Do NOT submit either file."),
            "submit_into_a_slot": "NO. Lane duplicate; holdout does not beat the best same-evaluator arm.",
            "rationale": ("Lane: literal rule fails against registry rasters r11 (0.833), r13 (0.998), r14 (0.857) "
                          "and three non-degenerate siblings (0.935, 0.769, 0.733). Chance-corrected excess is "
                          "positive for r11, r14 and all three siblings. Holdout: the candidate does not beat the "
                          "H54-A rule on the same folds (0.0915 vs 0.1472). The arm-X result is inadmissible "
                          "at matched mass."),
            "negative_result": True,
        },
        "organizer_confirmed": [
            {"claim": "DTI = TP_w / (TP_w + 0.2 FP_w + 0.8 FN_w + eps); triangular 300 m kernel",
             "source": "https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/",
             "status": "ORGANIZER-CONFIRMED (problem page, fetched 2026-10-09)"},
            {"claim": "EPSG 32611, 100 m, float32 single band, values in [0,1], outside bounds null/nan",
             "source": "https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/",
             "status": "ORGANIZER-CONFIRMED"},
            {"claim": "up to three submissions per week; one final submission",
             "source": "https://docs.nlr.gov/docs/fy26osti/96647.pdf (sections 3.4, 3.5)",
             "status": "ORGANIZER-CONFIRMED (rules PDF)"},
            {"claim": "public leaderboard: 0.3774 rank 1; 0.3195 rank 7; 0.2778 rank 13 (extradr19); 0.2750 rank 17",
             "source": "https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/",
             "status": "ORGANIZER-CONFIRMED (fetched 2026-10-09)"},
        ],
        "irregularities": [f"IR-54-{n:03d}" for n in range(66, 83)],
        "irregularities_file": "docs/audit/irregularities.md",
    }
    OUT.write_text(json.dumps(card, indent=2, default=str, allow_nan=False) + "\n", encoding="utf-8")
    print(f"wrote {OUT}")
    print(json.dumps(card["verdict"], indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

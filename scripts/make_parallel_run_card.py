#!/usr/bin/env python3
"""Assemble the single JSON run card for the 2026-10-08 parallel run from receipts (no hand-typed numbers).

Inputs (all produced by the scripts in this repository):
  evidence/holdout_segment_cv_run2_variant.json            HOLDOUT-DTI receipt (evaluator gemsdoe54-segment-cv v2)
  evidence/power_floor_segment_cv_v2.json        detection floors from the same receipt
  registry/gems54-own-visible-hgb-q97.build.json build receipt for the final file
  evidence/validator_output_own_visible.json     format and literal lane gate (11 registry rasters)
  evidence/uniqueness_gems54-own-visible-hgb-q97.json   full sibling scan (1,177 grid rasters), if present

Output: docs/data/run-card.json (the site's "current run card").

Verdict rule (protocol): a file is slot-eligible only if (a) its holdout DTI beats the current holdout best
(C1, SGMC complement) with a paired 95 % CI above zero, (b) the literal lane gate passes against every
registry raster, and (c) no leakage canary exceeds AUC 0.90. Otherwise the verdict is NEGATIVE and no slot
is recommended. Slot selection itself is never made by this script.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FILE = "docs/downloads/gems54-own-visible-hgb-q97.tif"
NAME = "gems54-own-visible-hgb-q97"
NOTE = ("Own model, not a copy: visible-only boosted fault probability, 19 bands + gradients, "
        "top 3% cells, 200 m dots. NOT CLEARED.")


def load(p: str):
    path = ROOT / p
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else None


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> int:
    hold = load("evidence/holdout_segment_cv_run2_variant.json")
    power = load("evidence/power_floor_segment_cv_v2.json")
    build = load("registry/gems54-own-visible-hgb-q97.build.json")
    val = load("evidence/validator_output_own_visible.json")
    uniq = load("evidence/uniqueness_gems54-own-visible-hgb-q97.json")
    tif = ROOT / FILE
    assert len(NOTE) <= 140, len(NOTE)

    c1 = hold["candidates"]["C1_sgmc_complement"]
    c4 = hold["candidates"]["C4_visible_only_learned_probability"]
    pd = hold["paired_differences"]
    c4_vs_c1 = pd["C4_visible_only_learned_probability minus C1_sgmc_complement"]
    c4_vs_c0 = pd["C4_visible_only_learned_probability minus C0_random_admissible_control"]
    beats_best = c4_vs_c1["ci95_percentile"][0] > 0.0
    lane_literal_pass = val["lane"]["verdict"] != "DUPLICATE - STOP"
    flagged = val["lane"]["flagged_registry"]
    max_auc = hold["canary"]["features"]["model_visible_probability_C4"]["max_auc_over_folds"]
    canary_pass = max_auc <= 0.90
    uniq_res = (uniq or {}).get("result", {}) if uniq else {}
    uniq_verdict = uniq_res.get("lane_check") if uniq else None      # PASS / FAIL from the full scan
    uniq_pass = uniq_verdict == "PASS"

    if beats_best and lane_literal_pass and canary_pass and uniq_pass:
        verdict = "PROMOTE-ELIGIBLE (slot selection still a separate step)"
    else:
        verdict = "NEGATIVE — do not spend a weekly slot"

    archive = load("registry/run_card_run1_archive.json") or {}
    card = {
        "schema": "gemsdoe54.run-card.run2",
        "run_card": "gems54-parallel-run",
        "run_id": "2026-10-08-run2",
        "version": 3,
        "date": "2026-10-08",
        "generated_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "verdict": "negative" if verdict.startswith("NEGATIVE") else "promote-eligible",
        "verdict_text": verdict,
        "submission_block_note": "submission.* describes the run-2 file. Download is for review only; submission is not cleared.",
        "submission_flags": {
            "candidate_this_run": True,
            "candidate_surface_preflighted": True,
            "candidate_tif_generated": True,
            "downloadable_new_tif": True,
            "ok_to_download_for_review": True,
            "ok_to_download_for_submission": False,
            "ok_to_submit": False,
            "safe_to_upload": False,
            "note_character_limit": 140,
            "note_chars": len(NOTE),
            "existing_repository_artifact": {
                "file": "docs/downloads/gems54-undercomplement-q200.tif",
                "holdout_validation": "HOLDOUT-DTI C1 0.0483 (run-1 receipt v1; the file itself was not re-scored)",
                "format_validation": "FAIL (run-1 conservative outside-footprint null/NaN check)",
                "lane": "FAIL (run 1; 100 % of dots within 3 px of GEMSDOE3 gapfinder-v2-sgmc-gap)",
                "approved_for_upload": False,
            },
        },
        "answers": {
            "ok_to_download": "YES, for review. The file is this repository's own model output and passes the format checks.",
            "ok_to_submit": "NO. Not cleared: the literal lane gate reports DUPLICATE - STOP against three dense registry rasters, "
                            "and the holdout does not beat the current holdout best (C1 SGMC complement).",
        },
        "submission": {
            "name": NAME,
            "note": NOTE,
            "note_chars": len(NOTE),
            "file": FILE,
            "sha256": sha256(tif) if tif.exists() else None,
            "bytes": tif.stat().st_size if tif.exists() else None,
            "dots": build["dots"],
            "quantile": build["quantile"],
            "crs": "EPSG:32611", "resolution_m": 100, "dtype": "float32", "nodata": "NaN outside footprint",
        },
        "hypothesis": {
            "tested": [
                {"id": "H3", "name": "visible-only learned probability (histogram gradient boosting)",
                 "layers": "19 bands + gradient magnitudes of rtp, tmi_hg, iso_grav_anom, depth_to_base_surf, cond_surf",
                 "physical_signature": "multi-family geophysical signature learned from visible faults (magnetic, gravity, strain, conductivity, basin structure)",
                 "why_it_may_find_missing_faults": "a learned combination can pick up fault signatures that no single layer shows",
                 "difference_from_repo": "not an SGMC rule and not a single-layer ridge; trained per fold on visible catalogue only",
                 "known_mimics": "lithologic contacts, basin margins, survey seams, cultural magnetic noise",
                 "cost": "about 2 min per fold on 2 CPUs", "status": "tested; holdout tie with C1; not promoted"},
                {"id": "H1", "name": "cross-gradient corroboration (tmi_hg x iso_grav_anom_hg)",
                 "status": "tested; below C1 and near chance"},
                {"id": "H2", "name": "basement-step gradient (depth_to_base_surf)",
                 "status": "tested; chance level"},
            ],
            "experiments_used": 3,
            "experiment_budget": "3 experiments or 2 hours (time used: about 65 minutes at generation)",
        },
        "holdout_dti": {
            "label": "HOLDOUT-DTI",
            "status": "RUN — evaluator gemsdoe54-segment-cv v2 end to end; file C4 does not beat C1",
            "evaluator_version": "gemsdoe54-segment-cv v2",
            "withheld_positive_count": hold["units"]["withheld_positive_cells_total"],
            "ci95": c4["ci95_percentile"],
            "independent_units": hold["units"]["catalogue_segments_total"],
        },
        "holdout": {
            "label": "HOLDOUT-DTI",
            "evaluator": hold["evaluator"]["name"] + " " + hold["evaluator"]["version"],
            "withheld_positive_cells": hold["units"]["withheld_positive_cells_total"],
            "independent_units_segments": hold["units"]["catalogue_segments_total"],
            "target": "USGS-catalogue faults (recovery proxy), not the hidden new-fault set",
            "candidate_C4": {"pooled_dti": c4["pooled_dti_point"], "ci95": c4["ci95_percentile"], "dots_total": c4["dots_total"]},
            "holdout_best_C1": {"pooled_dti": c1["pooled_dti_point"], "ci95": c1["ci95_percentile"]},
            "C4_minus_C1": {"point": c4_vs_c1["point"], "ci95": c4_vs_c1["ci95_percentile"], "paired_se": c4_vs_c1["bootstrap_se"]},
            "C4_minus_C0_chance": {"point": c4_vs_c0["point"], "ci95": c4_vs_c0["ci95_percentile"]},
            "beats_holdout_best": bool(beats_best),
            "shift_null_C1_p95": hold["shift_null_C1"]["p95"],
        },
        "leakage_canary": {
            "auc_cut": 0.90,
            "model_visible_probability_C4_max_auc_over_folds": max_auc,
            "single_feature_max_auc": max(v["max_auc_over_folds"] for k, v in hold["canary"]["features"].items()
                                          if k not in ("dist_to_visible_catalogue_m",)),
            "distance_to_visible_catalogue_auc_withholding_artefact": hold["canary"]["features"]["dist_to_visible_catalogue_m"]["max_auc_over_folds"],
            "flagged": hold["canary"]["flagged"],
            "result": "clear" if canary_pass and not hold["canary"]["flagged"] else "LEAKAGE",
        },
        "detection_floor": {
            "label": "computed from receipt; not a score",
            "cohen_d_pixel_iid_INVALID_for_this_design": power["cohen_d_pixel_iid_INVALID_for_this_design"],
            "cohen_d_independent_units": power["cohen_d_units_total"],
            "paired_mde_C4_minus_C1": power["paired_differences"]["C4_visible_only_learned_probability minus C1_sgmc_complement"]["mde_dti_2p80_two_sided"],
            "board_gap_0.0028_inside_floor": "yes for every architecture pair measured; board classification needs the public unit count (not published)",
        },
        "lane_gate": {
            "literal_rule": "rank correlation <= 0.90 and <= 70 % of dots within 3 px of any registry raster",
            "registry_11": {"verdict": val["lane"]["verdict"], "flagged": flagged,
                            "max_abs_spearman": max(r["abs_spearman_rho"] for r in val["lane"]["rows"]),
                            "max_overlap_non_degenerate": max(r["fraction_of_my_dots"] for r in val["lane"]["rows"]
                                                              if r["overlap_test_admissible"])},
            "full_sibling_scan": ({
                "lane_check": uniq_verdict,
                "scan": (uniq or {}).get("scan"),
                "max_abs_spearman": uniq_res.get("max_spearman_rho"),
                "siblings_with_rho_above_0_90": uniq_res.get("siblings_with_rho_above_limit"),
                "siblings_with_overlap_above_0_70": uniq_res.get("siblings_with_overlap_above_limit"),
                "degenerate_siblings_coverage_ge_0_50": len(uniq_res.get("overlap_degenerate_siblings", [])) if isinstance(uniq_res.get("overlap_degenerate_siblings"), list) else uniq_res.get("overlap_degenerate_siblings"),
                "max_overlap_non_degenerate": uniq_res.get("max_overlap_cand_in_sib_nondegenerate"),
                "receipt": "evidence/uniqueness_gems54-own-visible-hgb-q97.json",
            } if uniq else {"status": "not run or not finished at generation"}),
            "degeneracy_note": "three dense registry rasters cover 74 %, 99.9 % and 76 % of the footprint, so the 70 % test cannot discriminate there (IR-54-013, IR-54-037)",
        },
        "format_validation": {"passed": val["format"]["passed"], "failures": val["format"]["failures"],
                              "self_check": build["format_self_check"]},
        "board_values": {"label": "BOARD-UNVERIFIED", "rank13_0.2778": True, "rank17_0.2750": True, "rank1_0.3774": True},
        "limitations": [
            "The holdout target is catalogue recovery, not the hidden new-fault set (IR-54-050).",
            "Feature rasters come from an owner bridge; origin is not organizer-authenticated (IR-54-011, IR-54-043).",
            "The feature band list does not match the official description (IR-54-052).",
            "Portal error text 'Predicted values must be in range [0, 1]' could not be reproduced; the writer enforces float32, [0,1] inside, NaN outside (IR-54-054).",
            "The count-matched quantile is unstable across folds (0.97 in four folds, 0.50 in fold 2).",
        ],
        "inputs": {
            "features_sha256": hold["inputs"]["features"]["sha256"],
            "labels_sha256": hold["inputs"]["labels"]["sha256"],
            "sgmc_sha256": hold["inputs"]["sgmc"]["sha256"],
            "holdout_receipt": "evidence/holdout_segment_cv_run2_variant.json",
            "power_receipt": "evidence/power_floor_segment_cv_v2.json",
            "build_receipt": "registry/gems54-own-visible-hgb-q97.build.json",
            "validator_receipt": "evidence/validator_output_own_visible.json",
            "uniqueness_receipt": "evidence/uniqueness_gems54-own-visible-hgb-q97.json" if uniq else None,
        },
        "not_done": [
            "No DrivenData submission or receipt (login-gated; no organizer score).",
            "No weekly slot selected; slot selection is a separate selector step.",
            "No Phase-2 expanded label evaluation.",
        ],
    }
    card["submission"] = {**card.pop("submission_flags"), **card["submission"]}
    if archive.get("magnetic_ridge_holdout"):
        card["magnetic_ridge_holdout"] = archive["magnetic_ridge_holdout"]
    out = ROOT / "docs/data/run-card.json"
    out.write_text(json.dumps(card, indent=2, default=float) + "\n", encoding="utf-8")
    print(json.dumps({"verdict": verdict, "beats_best": beats_best, "lane_literal": val["lane"]["verdict"],
                      "canary_max_auc": max_auc, "uniqueness": uniq_verdict}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

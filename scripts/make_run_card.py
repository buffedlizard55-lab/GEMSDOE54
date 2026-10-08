#!/usr/bin/env python3
"""Assemble the protocol run card from receipts. No number is typed by hand.

Inputs (all produced by scripts in this repository):
  * the submission GeoTIFF itself (SHA-256, grid, positives, nodata)
  * evidence/validator_output.json      (scripts/validate_submission.py)
  * evidence/uniqueness_<slug>.json     (scripts/sibling_uniqueness.py, all sibling rasters)
  * evidence/holdout_segment_cv_v1.json (scripts/holdout_segment_cv.py, evaluator v1)
  * registry/<slug>.build.json          (scripts/build_submission.py receipt)

Pre-registered verdict rule (applied mechanically; a slot is NOT selected by this script):
  PROMOTE  iff ALL of
    1. validator: every check passes;
    2. lane: uniqueness lane_check == PASS (no exact sibling match; max rank rho <= 0.90;
       max dot overlap within 3 px <= 0.70, against every grid-aligned sibling raster);
    3. canary: the candidate's own feature(s) are CLEAR (AUC <= 0.90 in every fold);
    4. pooled HOLDOUT-DTI 95% CI lower bound > the control's 95% CI upper bound (non-overlapping
       CIs against the count-matched random control; the shift null exists for C1 only and is
       reported separately);
    5. paired HOLDOUT-DTI difference vs the chance control (C0) has 95% CI lower bound > 0;
    6. no other tested candidate is significantly better: for each rival, the 95% CI upper bound of
       (candidate minus rival) must be >= 0.
  NEGATIVE otherwise.

The verdict is a holdout verdict on catalogue recovery. It is not an organizer score and it is
not a submission-slot choice (protocol: do not pick submissions).
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import rasterio

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from gemsdoe54.grid import footprint  # noqa: E402

NOTES = {
    "C1_sgmc_complement": ("GEMSDOE54 undercomplement-q200: SGMC state-map complement of catalogue, d>300m, "
                           "linearity gate, 200m dots"),
    "C3_magnetic_hgrad_ridge": ("GEMSDOE54 magedge-hgrad-ridge: tmi_hg magnetic gradient ridges, >300m from "
                                "catalogue, linearity gate, 200m dots"),
}
NOTE_LIMIT = 140
DEFAULT_CANDIDATE = "C1_sgmc_complement"
CONTROL = "C0_random_admissible_control"
ALL_CANDIDATES = ("C1_sgmc_complement", "C2_geodetic_shear_ridge", "C3_magnetic_hgrad_ridge")


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def submission_facts(path: Path, labels: Path) -> dict:
    path = path.resolve()
    foot = footprint(str(labels))
    with rasterio.open(path) as ds:
        arr = ds.read(1)
        facts = {
            "path": path.relative_to(ROOT).as_posix(),
            "sha256": sha256_file(path),
            "bytes": path.stat().st_size,
            "driver": ds.driver,
            "bands": ds.count,
            "dtype": ds.dtypes[0],
            "nodata": ds.nodata,
            "crs": str(ds.crs),
            "shape": [ds.height, ds.width],
            "transform": list(ds.transform)[:6],
        }
    finite = np.isfinite(arr)
    facts["nan_cells"] = int((~finite).sum())
    facts["unique_values_in_footprint"] = sorted({float(v) for v in np.unique(arr[foot & finite])})
    facts["positive_cells"] = int(np.count_nonzero(np.nan_to_num(arr, nan=0.0) > 0))
    facts["min_in_footprint"] = float(np.nanmin(arr[foot]))
    facts["max_in_footprint"] = float(np.nanmax(arr[foot]))
    facts["nonzero_outside_footprint"] = int(np.count_nonzero(np.nan_to_num(arr[~foot], nan=0.0)))
    return facts


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--submission", default=str(ROOT / "docs/downloads/gems54-undercomplement-q200.tif"))
    ap.add_argument("--labels", default=str(ROOT / "data/grid/labels.tif"))
    ap.add_argument("--validator", default=str(ROOT / "evidence/validator_output.json"))
    ap.add_argument("--uniqueness", default=str(ROOT / "evidence/uniqueness_gems54-undercomplement-q200.json"))
    ap.add_argument("--holdout", default=str(ROOT / "evidence/holdout_segment_cv_v1.json"))
    ap.add_argument("--build", default=str(ROOT / "registry/gems54-undercomplement-q200.build.json"))
    ap.add_argument("--out", default=str(ROOT / "registry/run_card_v2.json"))
    ap.add_argument("--candidate", default=DEFAULT_CANDIDATE, choices=ALL_CANDIDATES)
    args = ap.parse_args()
    CANDIDATE = args.candidate
    RIVALS = tuple(c for c in ALL_CANDIDATES if c != CANDIDATE)
    NOTE = NOTES.get(CANDIDATE, NOTES["C1_sgmc_complement"])

    sub = submission_facts(Path(args.submission), Path(args.labels))
    val = json.loads(Path(args.validator).read_text())
    uniq = json.loads(Path(args.uniqueness).read_text())
    ho = json.loads(Path(args.holdout).read_text())
    build = json.loads(Path(args.build).read_text()) if Path(args.build).exists() else {}

    cands = ho["candidates"]
    c1 = cands[CANDIDATE]
    paired = ho["paired_differences"]
    null = ho["shift_null_C1"]
    canary = ho["canary"]["features"]
    status = ho["candidate_leakage_status"]

    def diff(a: str, b: str) -> dict:
        key = f"{a} minus {b}"
        if key in paired:
            return paired[key]
        inv = f"{b} minus {a}"
        if inv not in paired:
            return None  # pair not present in the receipt: the rule is then treated as not satisfied
        d = paired[inv]
        return {"point": -d["point"], "bootstrap_se": d["bootstrap_se"],
                "ci95_percentile": [-d["ci95_percentile"][1], -d["ci95_percentile"][0]],
                "mde_raw_80pct_two_sided": d["mde_raw_80pct_two_sided"]}

    vs_control = diff(CANDIDATE, CONTROL)
    rival_checks = {r: diff(CANDIDATE, r) for r in RIVALS}
    rival_checks = {r: (rc if rc is not None else {"ci95_percentile": None, "note": "pair not in receipt"})
                    for r, rc in rival_checks.items()}
    checks = {
        "1_validator_all_pass": bool(val["format"]["passed"]) and val["lane"]["verdict"] == "distinct lane",
        "2_lane_check_pass": uniq["result"]["lane_check"] == "PASS",
        "3_candidate_canary_clear": status[CANDIDATE] == "CLEAR",
        "4_pooled_ci_lower_above_control_ci_upper": c1["ci95_percentile"][0] > cands[CONTROL]["ci95_percentile"][1],
        "5_paired_vs_control_ci_lower_above_0": vs_control["ci95_percentile"][0] > 0,
        "6_no_rival_significantly_better": all(rc is not None and rc["ci95_percentile"][1] >= 0
                                              for rc in rival_checks.values()),
    }
    promote = all(checks.values())

    card = {
        "run_card_version": "parallel-run protocol v2 (whole-segment holdout, evaluator gemsdoe54-segment-cv v1)",
        "generated_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "experiment": {
            "id": "H54-A" if CANDIDATE == DEFAULT_CANDIDATE else "H54-B",
            "slug": Path(args.submission).stem,
            "candidate_key_in_holdout": CANDIDATE,
            "status": "re-evaluated under the whole-segment holdout; not an organizer score",
        },
        "hypothesis": (
            "Faults absent from the competition catalogue are most likely to be mapped on the USGS State "
            "Geologic Map Compilation (SGMC) as linework lying more than one kernel width (300 m) from every "
            "catalogue cell. A linearity gate and 200 m dot spacing turn that linework into a sparse "
            "prediction with low false-positive mass."),
        "mechanism": (
            "Visible-catalogue exclusion (300 m) removes linework whose credit is already claimed; the "
            "linearity gate keeps long traces and drops blob-shaped map artefacts; spaced dots reduce "
            "redundant false positives. Under the organizer metric, dots that earn zero credit only raise "
            "the FP term (see scripts/holdout_segment_cv.py docstring and tests/test_segment_cv.py)."),
        "mimic_process": (
            "Map linework that is not a Quaternary fault: pre-Quaternary faults without scarps, dikes and "
            "veins digitised as lines, lithologic contacts, and neatlines. The linearity gate removes only "
            "blob-shaped artefacts; it does not remove long non-fault contacts."),
        "holdout": {
            "label": ho["label"],
            "evaluator": ho["evaluator"],
            "candidate": CANDIDATE,
            "pooled_dti": c1["pooled_dti_point"],
            "ci95_percentile": c1["ci95_percentile"],
            "bootstrap_sd": c1["bootstrap_sd"],
            "withheld_positive_cells": ho["units"]["withheld_positive_cells_total"],
            "independent_units_segments": ho["units"]["catalogue_segments_total"],
            "folds": ho["design"]["folds"],
            "controls": {CONTROL: {"pooled_dti": cands[CONTROL]["pooled_dti_point"],
                                   "ci95_percentile": cands[CONTROL]["ci95_percentile"]}},
            "paired_vs_control": vs_control,
            "paired_vs_rivals": rival_checks,
            "shift_null_C1": null,
            "shift_null_scope": "computed for C1 (SGMC-complement dot pattern) only",
            "canary_flagged_features": ho["canary"]["flagged"],
            "candidate_leakage_status": status[CANDIDATE],
            "cohen_d_min_units_total": ho["power"]["cohen_d_min_80pct_alpha05_units_total"],
            "cohen_d_min_units_per_fold": ho["power"]["cohen_d_min_80pct_alpha05_units_per_fold"],
            "mde_raw_from_paired_bootstrap_se": {k: v["mde_raw_80pct_two_sided"] for k, v in paired.items()},
            "limitations": [
                "Truth is the owner-mirrored catalogue (labels==1), not the organizer's hidden expert set.",
                "Hidden test faults are by construction absent from the catalogue; catalogue faults are better mapped.",
                "Feature rasters are owner-claimed bridge copies (hash-consistent, not organizer-authenticated).",
            ],
        },
        "overlap_vs_registry": {
            "scope": "every grid-aligned sibling raster in the GEMSDOE family (not only the 11 registry rasters)",
            "siblings_scanned": uniq["scan"],
            "exact_file_matches": uniq["result"]["exact_file_matches"],
            "exact_decoded_matches": uniq["result"]["exact_decoded_matches"],
            "max_spearman_rho": uniq["result"]["max_spearman_rho"],
            "max_spearman_rho_source": uniq["result"]["max_spearman_rho_source"],
            "max_overlap_cand_in_sib_all": uniq["result"]["max_overlap_cand_in_sib_all"],
            "max_overlap_cand_in_sib_nondegenerate": uniq["result"]["max_overlap_cand_in_sib_nondegenerate"],
            "max_overlap_source": uniq["result"]["max_overlap_source"],
            "overlap_degenerate_siblings_count": len(uniq["result"]["overlap_degenerate_siblings"]),
            "siblings_with_overlap_above_limit": uniq["result"]["siblings_with_overlap_above_limit"],
            "lane_check": uniq["result"]["lane_check"],
            "protocol": uniq["protocol"],
        },
        "submission_file": sub,
        "builder_receipt_ref": "registry/gems54-undercomplement-q200.build.json",
        "builder_receipt_summary": {k: build.get(k) for k in ("slug", "emitted_dots", "dots") if k in build},
        "validator_output": {"path": "evidence/validator_output.json",
                             "format_passed": val["format"]["passed"],
                             "format_checks": val["format"]["checks"],
                             "format_failures": val["format"]["failures"],
                             "lane_verdict": val["lane"]["verdict"]},
        "note": NOTE,
        "note_chars": len(NOTE),
        "note_within_limit": len(NOTE) <= NOTE_LIMIT,
        "verdict_rule_checks": checks,
        "verdict": "promote" if promote else "negative",
        "verdict_meaning": ("passes the pre-registered holdout gates; this is NOT a submission-slot selection"
                            if promote else "does not pass the pre-registered holdout gates"),
        "labels_policy": ("HOLDOUT-DTI = whole-segment holdout receipt with evaluator, withheld positives and 95% CI. "
                          "ORGANIZER-CONFIRMED = none for this artefact. MODEL/PROXY values are not scores."),
    }
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out).write_text(json.dumps(card, indent=2, default=float) + "\n", encoding="utf-8")
    print(json.dumps({"verdict": card["verdict"], "checks": checks, "note_chars": len(NOTE)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

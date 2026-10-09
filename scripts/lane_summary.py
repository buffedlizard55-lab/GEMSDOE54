#!/usr/bin/env python3
"""Assemble the CGRC lane verdict from the full-corpus rows table, the skipped-row second pass,
the validator output and the witness checks. Nothing here is typed by hand.

Protocol (parallel-run, requirement 1): a candidate is a DUPLICATE if absolute Spearman rho > 0.90
or more than 70% of its dots lie within 3 px of any registry raster / sibling dot set. Degenerate
rasters (3 px neighbourhoods cover >= 50% of the footprint) are NOT exempt from the literal rule;
they are reported separately with a chance-corrected excess so the reader can see that the
overlap is not only coverage.

Chance correction: excess = (observed - coverage) / (1 - coverage), where coverage is the fraction
of the footprint within 3 px of the sibling's dots (the overlap a random candidate would get).
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

DEGENERATE_COVERAGE = 0.50
RHO_LIMIT = 0.90
OVERLAP_LIMIT = 0.70


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def excess(obs: float, cov: float) -> float | None:
    return round((obs - cov) / (1.0 - cov), 6) if cov < 1.0 else None


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--rows", required=True, help="uniq_*_rows.json from scripts/sibling_uniqueness.py")
    ap.add_argument("--scan", required=True, help="uniq_*.json summary from scripts/sibling_uniqueness.py")
    ap.add_argument("--skipped", required=True, help="lane_skipped_rows.json (second pass, 45 rows)")
    ap.add_argument("--validator", action="append", default=[], help="validator output JSON(s)")
    ap.add_argument("--witness", action="append", default=[], help="witness_overlap.py output JSON(s)")
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    rows_all = json.loads(Path(args.rows).read_text())
    scan = json.loads(Path(args.scan).read_text())
    skipped = json.loads(Path(args.skipped).read_text())

    twins = [r for r in rows_all if r.get("exact_decoded_match")]
    sibs = [r for r in rows_all if not r.get("exact_decoded_match")]
    checked = [r for r in sibs if "overlap_cand_in_sib" in r]
    not_checked = [r for r in sibs if "overlap_cand_in_sib" not in r]
    nondeg = [r for r in checked if not r["overlap_degenerate"]]
    deg = [r for r in checked if r["overlap_degenerate"]]

    rhos = [abs(r["spearman_rho"]) for r in sibs if r.get("spearman_rho") is not None]
    max_rho = max(rhos) if rhos else None
    max_rho_row = max((r for r in sibs if r.get("spearman_rho") is not None),
                      key=lambda r: abs(r["spearman_rho"]))

    def label(r: dict) -> str:
        return f"{r['repo']}/{r['path']}"

    # de-duplicate byte-identical copies (zip members, duplicate uploads) by file sha256
    def dedupe(rs: list[dict]) -> list[dict]:
        seen: dict[str, dict] = {}
        for r in rs:
            key = r["sha256"]
            seen.setdefault(key, {"sha256": key, "copies": [], **{k: r[k] for k in (
                "spearman_rho", "overlap_cand_in_sib", "overlap_sib_in_cand",
                "coverage_3px_of_footprint", "n_dots") if k in r}})["copies"].append(label(r))
        out = []
        for v in seen.values():
            v["excess_over_chance"] = excess(v["overlap_cand_in_sib"], v["coverage_3px_of_footprint"])
            out.append(v)
        return sorted(out, key=lambda v: -v["overlap_cand_in_sib"])

    over_nd = dedupe([r for r in nondeg if r["overlap_cand_in_sib"] > OVERLAP_LIMIT])
    over_deg = dedupe([r for r in deg if r["overlap_cand_in_sib"] > OVERLAP_LIMIT])
    deg_registry = [
        {"raster": label(r), "coverage_3px": r["coverage_3px_of_footprint"],
         "overlap_cand_in_sib": r["overlap_cand_in_sib"], "excess_over_chance": excess(
             r["overlap_cand_in_sib"], r["coverage_3px_of_footprint"]),
         "sha256": r["sha256"][:16]}
        for r in deg if r["repo"] == "GEMSDOE54"
    ]

    skip_rows = skipped["rows"]
    skip_ov = [r["overlap_cand_in_topK"] for r in skip_rows if "overlap_cand_in_topK" in r]
    skip_rho = [abs(r["spearman_rho_vs_cand"]) for r in skip_rows if "spearman_rho_vs_cand" in r]

    literal_fail = bool(over_nd or over_deg)
    summary = {
        "schema": "gemsdoe54.lane-summary.v1",
        "generated_utc_source": "derived from the rows table; no manual numbers",
        "protocol": {"rho_limit": RHO_LIMIT, "overlap_limit": OVERLAP_LIMIT, "radius_px": 3,
                     "degenerate_coverage": DEGENERATE_COVERAGE,
                     "literal_rule_applies_to_degenerate_rasters": True},
        "inputs": {"rows": {"path": args.rows, "sha256": sha256(Path(args.rows))},
                   "scan": {"path": args.scan, "sha256": sha256(Path(args.scan))},
                   "skipped": {"path": args.skipped, "sha256": sha256(Path(args.skipped))}},
        "scan": scan["scan"],
        "counts": {
            "grid_rasters_seen": len(rows_all),
            "self_twins_excluded": [label(r) for r in twins],
            "sibling_rows": len(sibs),
            "overlap_checked": len(checked),
            "overlap_checked_degenerate": len(deg),
            "overlap_checked_nondegenerate": len(nondeg),
            "not_overlap_checked": len(not_checked),
            "not_overlap_checked_reasons": {
                "out_of_range_or_nonfinite_non_submission": sum(
                    1 for r in not_checked if not (r["in_range_0_1"] and r["finite_in_footprint"])),
                "in_range_finite_not_submission_like": sum(
                    1 for r in not_checked if r["in_range_0_1"] and r["finite_in_footprint"]),
            },
        },
        "rank_correlation": {
            "max_abs_rho_siblings": round(max_rho, 6) if max_rho is not None else None,
            "max_abs_rho_source": label(max_rho_row),
            "siblings_rho_above_limit": sum(1 for v in rhos if v > RHO_LIMIT),
            "verdict": "PASS" if (max_rho is not None and max_rho <= RHO_LIMIT) else "FAIL",
        },
        "dot_overlap": {
            "max_nondegenerate": round(max(r["overlap_cand_in_sib"] for r in nondeg), 6),
            "nondegenerate_above_limit_unique_rasters": over_nd,
            "degenerate_above_limit_unique_rasters_count": len(over_deg),
            "degenerate_registry_rasters": deg_registry,
        },
        "skipped_second_pass": {
            "n": len(skip_rows),
            "K_top_cells": skipped["K"],
            "max_overlap_cand_in_topK": round(max(skip_ov), 6) if skip_ov else None,
            "max_abs_rho": round(max(skip_rho), 6) if skip_rho else None,
            "method": "top-K cells by value inside the footprint as the dot set (K = CGRC dot count)",
            "constant_rasters_no_dots": sum(1 for r in skip_rows if "overlap_cand_in_topK" not in r
                                            and "error" not in r and "note" not in r),
        },
        "validator_runs": [],
        "witness_checks": [],
        "verdict": {
            "literal_rule": "FAIL (duplicate)" if literal_fail else "PASS",
            "non_degenerate_only": ("FAIL (duplicate)" if over_nd else "PASS"),
            "note": ("Literal protocol applied to every sibling and registry raster. The degenerate "
                     "registry rasters r11/r13/r14 are not exempt: the protocol's 70% rule has no "
                     "coverage exemption, and the chance-corrected excess is positive for r11 and r14."),
        },
    }
    for vp in args.validator:
        v = json.loads(Path(vp).read_text())
        summary["validator_runs"].append({
            "file": vp, "file_sha256": sha256(Path(vp)),
            "submission": v["submission"],
            "format_passed": v["format"]["passed"],
            "format_failures": [k for k, c in v["format"]["checks"].items() if not c["ok"]],
            "lane_verdict": v["lane"]["verdict"],
            "lane_drift_detected": v["lane"]["lane_drift_detected"],
            "flagged_registry": v["lane"]["flagged_registry"],
        })
    for wp in args.witness:
        w = json.loads(Path(wp).read_text())
        summary["witness_checks"].append({
            "file": wp, "candidate": w["candidate"]["path"], "witness": w["witness"]["path"],
            "overlap_candidate_within_3px": w["overlap_candidate_dots_within_3px_of_witness"],
            "witness_coverage": w["witness_3px_coverage_of_footprint"],
            "excess_over_chance": w["excess_over_chance"], "verdict": w["lane_verdict_vs_witness"],
        })
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary["verdict"], indent=2))
    print("wrote", out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

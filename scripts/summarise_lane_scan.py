#!/usr/bin/env python3
"""Summarise a sibling-corpus lane scan (output of scripts/sibling_uniqueness.py --table-out).

Adds what the raw scan summary cannot say on its own:
  * which rows are the candidate's own twin or other same-design files from the same repository
    (excluded from the sibling verdict, reported separately);
  * the literal overlap verdict over every remaining sibling (protocol reading);
  * the list of NON-degenerate siblings above the overlap limit (coverage < 0.5), which are the
    rasters that carry real lane information;
  * blanket rasters (coverage >= 0.5), reported with their coverage so they can be discounted
    explicitly by the protocol owner rather than silently;
  * the maximum |Spearman rho| and exact or decoded copies over the remaining siblings.

Usage:
  python scripts/summarise_lane_scan.py --table /tmp/sib/uniq_cgrc_v1_table.json \
      --scan evidence/uniqueness_gems54-cgrc-relay-v1.json --exclude-same-design-prefix GEMSDOE54/docs/downloads/gems54-cgrc-relay-v1 \
      --out evidence/lane_summary_cgrc-relay-v1.json
Labels: CATALOGUE-FREE LANE STATISTICS. Not a DTI score. Not ORGANIZER-CONFIRMED.
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

OVERLAP_LIMIT = 0.70
RHO_LIMIT = 0.90
DEGENERATE = 0.50


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--table", required=True)
    ap.add_argument("--scan", required=True, help="summary JSON written by sibling_uniqueness.py")
    ap.add_argument("--exclude-same-design-prefix", action="append", default=[],
                    help="repo-relative path prefix of the candidate's own files (its twin), excluded as same-design")
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    rows = json.loads(Path(args.table).read_text(encoding="utf-8"))
    scan = json.loads(Path(args.scan).read_text(encoding="utf-8"))
    key = lambda r: f"{r['repo']}/{r['path']}"  # noqa: E731

    same_design, siblings = [], []
    for r in rows:
        k = key(r)
        if any(k.startswith(p) for p in args.exclude_same_design_prefix):
            same_design.append({"file": k, "decoded_match": bool(r.get("exact_decoded_match")),
                                "rho": r.get("spearman_rho"), "overlap": r.get("overlap_cand_in_sib")})
        elif not r.get("exact_file_match"):
            siblings.append(r)

    def ov(r):
        return float(r.get("overlap_cand_in_sib", 0.0))

    def cov(r):
        return float(r.get("coverage_3px_of_footprint", 0.0))

    literal_fail = [r for r in siblings if ov(r) > OVERLAP_LIMIT]
    nondeg_fail = [r for r in literal_fail if cov(r) < DEGENERATE]
    blanket_fail = [r for r in literal_fail if cov(r) >= DEGENERATE]
    rho_vals = [(abs(r["spearman_rho"]), key(r)) for r in siblings if r.get("spearman_rho") is not None
                and r["spearman_rho"] == r["spearman_rho"]]
    max_rho = max(rho_vals) if rho_vals else (None, None)
    exact_copies = [key(r) for r in rows if r.get("exact_file_match") and key(r) not in
                    [s["file"] for s in same_design]]
    decoded_copies = [key(r) for r in siblings if r.get("exact_decoded_match")]
    fail_rows = [{"file": key(r), "coverage_3px_of_footprint": round(cov(r), 6),
                  "overlap_cand_in_sib": round(ov(r), 6), "n_dots": r.get("n_dots")}
                 for r in sorted(nondeg_fail, key=lambda r: -ov(r))]

    out = {
        "label": "LANE STATISTICS (sibling corpus). Not a DTI score. Not ORGANIZER-CONFIRMED.",
        "generated_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "source_table": args.table,
        "source_scan": args.scan,
        "rule": {"overlap_limit": OVERLAP_LIMIT, "rho_limit": RHO_LIMIT, "degenerate_coverage": DEGENERATE,
                 "reading": "literal: the overlap limit applies to every sibling raster with dots; "
                            "same-design twins of the candidate are excluded and listed separately"},
        "same_design_excluded": same_design,
        "siblings_compared": len(siblings),
        "exact_file_copies": exact_copies,
        "decoded_copies_of_other_repos": decoded_copies,
        "max_abs_spearman_rho": {"value": round(max_rho[0], 6) if max_rho[0] is not None else None,
                                 "source": max_rho[1]},
        "literal_overlap_fail_count": len(literal_fail),
        "literal_overlap_fail_nondegenerate_count": len(nondeg_fail),
        "literal_overlap_fail_blanket_count": len(blanket_fail),
        "nondegenerate_overlap_failures": fail_rows,
        "blanket_overlap_failures_sample": [
            {"file": key(r), "coverage_3px_of_footprint": round(cov(r), 6), "overlap_cand_in_sib": round(ov(r), 6)}
            for r in sorted(blanket_fail, key=lambda r: -cov(r))[:12]],
        "blanket_overlap_failures_total": len(blanket_fail),
        "scan_summary_reported_fail_count": scan["result"].get("siblings_with_overlap_above_limit"),
        "verdict_literal": "FAIL" if literal_fail else "PASS",
        "verdict_rho": "FAIL" if (max_rho[0] or 0) > RHO_LIMIT else "PASS",
        "verdict_copy": "FAIL" if (exact_copies or decoded_copies) else "PASS",
    }
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out).write_text(json.dumps(out, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: out[k] for k in ("siblings_compared", "literal_overlap_fail_count",
                                          "literal_overlap_fail_nondegenerate_count",
                                          "literal_overlap_fail_blanket_count", "max_abs_spearman_rho",
                                          "verdict_literal", "verdict_rho", "verdict_copy")}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

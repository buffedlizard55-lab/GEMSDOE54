#!/usr/bin/env python3
"""Exploratory comparison of an SGMC-derived proxy with owner-recorded board values.

The proxy target is USGS SGMC mapped faults more than 300 m from the competition
catalogue. It is not a whole-segment holdout and is not a valid performance gate.
This script compares prior proxy calculations with historical, owner-recorded board
observations; there are no submission-page receipts, so the board values are not
ORGANIZER-CONFIRMED. The result is exploratory and cannot validate a candidate.

A matched-count random field is retained as a proxy-sensitivity control only.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from scipy.stats import spearmanr  # noqa: E402

SCREENING = ROOT / "evidence/holdout_screening.json"
MANIFEST = ROOT / "registry/registry_manifest.json"


def main() -> int:
    screening = json.loads(SCREENING.read_text())
    manifest = json.loads(MANIFEST.read_text())
    published = {
        e["alias"]: e.get("published_public_score")
        for e in manifest["entries"]
        if e.get("alias")
    }

    rows = []
    for r in screening["results"]:
        lb = published.get(r["candidate"])
        if lb is None:
            continue
        rows.append({
            "candidate": r["candidate"],
            "n_dots": r["n_dots"],
            "proxy_dti": r["proxy_dti"],
            "lift_vs_matched_random": r["lift_vs_matched_random"],
            "owner_recorded_board_value_unreceipted": lb,
        })

    if len(rows) < 4:
        raise SystemExit("need at least 4 paired points to test the ordering")

    proxy = [r["proxy_dti"] for r in rows]
    lift = [r["lift_vs_matched_random"] for r in rows]
    lb = [r["owner_recorded_board_value_unreceipted"] for r in rows]

    rho, p = spearmanr(proxy, lb)
    rho_lift, p_lift = spearmanr(lift, lb)

    best_proxy = max(rows, key=lambda r: r["proxy_dti"])
    best_lb = max(rows, key=lambda r: r["owner_recorded_board_value_unreceipted"])
    worst_lb = min(rows, key=lambda r: r["owner_recorded_board_value_unreceipted"])

    out = {
        "analysis_label": "PROXY-ANALYSIS / exploratory; not HOLDOUT-DTI or ORGANIZER-CONFIRMED",
        "board_value_status": "Historical owner-recorded values without submission-page receipts",
        "question": "Does the SGMC-derived proxy order candidates like the historical owner-recorded board observations?",
        "answer": "No. The ordering is inverted at both ends.",
        "n_paired_artefacts": len(rows),
        "spearman_proxy_dti_vs_owner_recorded_board_values": {
            "rho": round(float(rho), 4), "p_value": round(float(p), 4),
        },
        "spearman_lift_vs_owner_recorded_board_values": {
            "rho": round(float(rho_lift), 4), "p_value": round(float(p_lift), 4),
        },
        "inversion": {
            "proxy_ranks_first": best_proxy["candidate"],
            "proxy_ranks_first_owner_recorded_board_value": best_proxy["owner_recorded_board_value_unreceipted"],
            "owner_recorded_board_ranks_first": best_lb["candidate"],
            "owner_recorded_board_value_first": best_lb["owner_recorded_board_value_unreceipted"],
            "owner_recorded_board_ranks_last": worst_lb["candidate"],
            "owner_recorded_board_value_last": worst_lb["owner_recorded_board_value_unreceipted"],
            "proxy_dti_of_owner_recorded_board_last": worst_lb["proxy_dti"],
        },
        "rows": rows,
        "conclusion": (
            "This exploratory six-row comparison does not validate candidate performance. The board "
            "inputs are unreceipted owner-recorded observations. The SGMC proxy can describe "
            "agreement with the SGMC layer only; it cannot confirm hidden faults or predict "
            "competition performance. Do not use it to choose candidates or quote a score."
        ),
    }
    path = ROOT / "evidence/proxy_audit.json"
    path.write_text(json.dumps(out, indent=2) + "\n", encoding="utf-8")

    print(f"paired artefacts: {len(rows)}")
    print(f"PROXY-ANALYSIS Spearman(proxy DTI, owner-recorded board) rho = {rho:+.3f} p = {p:.3f}")
    print(f"PROXY-ANALYSIS Spearman(lift, owner-recorded board) rho = {rho_lift:+.3f} p = {p_lift:.3f}")
    print()
    print(f"  proxy ranks FIRST : {best_proxy['candidate']} "
          f"(PROXY-DTI {best_proxy['proxy_dti']:.4f} -> owner-recorded board {best_proxy['owner_recorded_board_value_unreceipted']})")
    print(f"  owner-recorded board FIRST : {best_lb['candidate']} "
          f"(board observation {best_lb['owner_recorded_board_value_unreceipted']} -> PROXY-DTI {best_lb['proxy_dti']:.4f})")
    print(f"  owner-recorded board LAST  : {worst_lb['candidate']} "
          f"(board observation {worst_lb['owner_recorded_board_value_unreceipted']} -> PROXY-DTI {worst_lb['proxy_dti']:.4f}, "
          f"lift {worst_lb['lift_vs_matched_random']}x)")
    print(f"\nwrote {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

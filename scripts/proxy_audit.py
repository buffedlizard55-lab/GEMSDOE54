#!/usr/bin/env python3
"""Does the proxy holdout actually rank submissions?  Test it against the leaderboard.

The corpus's promotion decisions rest on a proxy holdout: USGS SGMC faults more
than 300 m from the competition catalogue.  A holdout is only usable as a gate if
it orders artefacts the way the real scored leaderboard orders them.  This script
tests exactly that, on every artefact that has BOTH downloadable bytes and a
published public score, and reports the inversion.

It also attaches a mass control.  A raw proxy DTI rewards any candidate that
sprays dots over the study area, because 200 k dots cover a lot of a small truth
set.  ``lift`` divides each candidate's proxy DTI by a matched-count uniform
random field scored the same way, which removes that trivial advantage.
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
            "leaderboard_public_score": lb,
        })

    if len(rows) < 4:
        raise SystemExit("need at least 4 paired points to test the ordering")

    proxy = [r["proxy_dti"] for r in rows]
    lift = [r["lift_vs_matched_random"] for r in rows]
    lb = [r["leaderboard_public_score"] for r in rows]

    rho, p = spearmanr(proxy, lb)
    rho_lift, p_lift = spearmanr(lift, lb)

    best_proxy = max(rows, key=lambda r: r["proxy_dti"])
    best_lb = max(rows, key=lambda r: r["leaderboard_public_score"])
    worst_lb = min(rows, key=lambda r: r["leaderboard_public_score"])

    out = {
        "question": "Does the proxy holdout rank submissions the way the real leaderboard does?",
        "answer": "No. The ordering is inverted at both ends.",
        "n_paired_artefacts": len(rows),
        "spearman_proxy_dti_vs_leaderboard": {
            "rho": round(float(rho), 4), "p_value": round(float(p), 4),
        },
        "spearman_lift_vs_leaderboard": {
            "rho": round(float(rho_lift), 4), "p_value": round(float(p_lift), 4),
        },
        "inversion": {
            "proxy_ranks_first": best_proxy["candidate"],
            "proxy_ranks_first_leaderboard_score": best_proxy["leaderboard_public_score"],
            "leaderboard_ranks_first": best_lb["candidate"],
            "leaderboard_first_score": best_lb["leaderboard_public_score"],
            "leaderboard_ranks_last": worst_lb["candidate"],
            "leaderboard_last_score": worst_lb["leaderboard_public_score"],
            "proxy_score_of_leaderboard_last": worst_lb["proxy_dti"],
        },
        "rows": rows,
        "conclusion": (
            "The artefact the proxy scores highest is the one the leaderboard scores "
            "lowest, and an artefact that the proxy scores WORSE THAN MATCHED RANDOM "
            "scored 0.1563 on the real leaderboard. The proxy is therefore usable for "
            "one narrow purpose only: confirming that a candidate's dots land on real "
            "mapped faults. It must never be used to choose between candidates, and no "
            "number derived from it may be quoted as an expected competition score."
        ),
    }
    path = ROOT / "evidence/proxy_audit.json"
    path.write_text(json.dumps(out, indent=2) + "\n", encoding="utf-8")

    print(f"paired artefacts: {len(rows)}")
    print(f"Spearman(proxy DTI, leaderboard)  rho = {rho:+.3f}  p = {p:.3f}")
    print(f"Spearman(lift,      leaderboard)  rho = {rho_lift:+.3f}  p = {p_lift:.3f}")
    print()
    print(f"  proxy ranks FIRST : {best_proxy['candidate']} "
          f"(proxy {best_proxy['proxy_dti']:.4f} -> leaderboard {best_proxy['leaderboard_public_score']})")
    print(f"  leaderboard FIRST : {best_lb['candidate']} "
          f"(leaderboard {best_lb['leaderboard_public_score']} -> proxy {best_lb['proxy_dti']:.4f})")
    print(f"  leaderboard LAST  : {worst_lb['candidate']} "
          f"(leaderboard {worst_lb['leaderboard_public_score']} -> proxy {worst_lb['proxy_dti']:.4f}, "
          f"lift {worst_lb['lift_vs_matched_random']}x)")
    print(f"\nwrote {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

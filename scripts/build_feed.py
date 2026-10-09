#!/usr/bin/env python3
"""Build a small repository-local status feed; this does not scrape the leaderboard."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]



def candidate_block(card: dict) -> dict:
    """Map the current run card to the feed's candidate fields.

    Accepts the 2026-10-09 schema (docs/data/run-card-2026-10-09.json). Upload flags are taken from the card's
    submission decision and are False unless that decision says OK; nothing here can promote a file.
    """
    sub = card.get("submission", {})
    decision = str(sub.get("decision_submit", "")).upper()
    ok = decision == "OK"
    hold = card.get("holdout", {})
    holdout_text = (f"{hold.get('label', 'HOLDOUT-DTI')}: arm B {hold.get('arm_B_SGMC_weight_pooled_DTI')} "
                    f"CI {hold.get('arm_B_ci95')} ({hold.get('evaluator', 'evaluator not recorded')})") if hold else "not recorded"
    return {
        "verdict": card.get("verdict", "unknown"),
        "candidate_surface_preflighted": True,
        "candidate_tif_generated": bool(card.get("rasters", {}).get("primary", {}).get("sha256")),
        "new_candidate_downloadable": True,
        "safe_to_upload": ok,
        "holdout_status": holdout_text,
        "existing_repository_artifact": {"name": sub.get("name"), "decision_submit": sub.get("decision_submit"),
                                         "decision_download": sub.get("decision_download")},
        "existing_artifact_downloadable_for_research": True,
        "existing_artifact_approved_for_upload": False,
        "ok_to_submit": ok,
        "ok_to_download_for_submission": ok,
        "magnetic_ridge_holdout": "receipt-only in this checkout (IR-54-058)",
        "lane_gate": card.get("validator_output", {}).get("primary", {}).get("lane", "not recorded"),
    }

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--audit", default=str(ROOT / "docs/data/workspace-audit.json"))
    parser.add_argument("--run-card", default=str(ROOT / "docs/data/run-card-2026-10-09.json"))  # current review (2026-10-09)
    parser.add_argument("--sources", default=str(ROOT / "docs/data/source-register.json"))
    parser.add_argument("--leaderboard", default=str(ROOT / "docs/data/leaderboard-snapshot.json"))
    parser.add_argument("--output", default=str(ROOT / "docs/data/feed.json"))
    args = parser.parse_args()
    audit = json.loads(Path(args.audit).read_text(encoding="utf-8"))
    run_card = json.loads(Path(args.run_card).read_text(encoding="utf-8"))
    source_register = json.loads(Path(args.sources).read_text(encoding="utf-8"))
    leaderboard = json.loads(Path(args.leaderboard).read_text(encoding="utf-8")) if Path(args.leaderboard).exists() else {
        "status": "not_fetched", "fetched_utc": None, "selected_rows": [], "source_url": None
    }
    feed = {
        "schema": "gemsdoe54.local-feed.v1",
        "generated_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "scope": "This pass's repository-local audit records only; not a DrivenData leaderboard feed and not a replacement for registry/run_card.json.",
        "leaderboard": {
            "status": leaderboard.get("status", "not_fetched"),
            "fetched_utc": leaderboard.get("fetched_utc"),
            "source_url": leaderboard.get("source_url"),
            "selected_rows": leaderboard.get("selected_rows", []),
            "score_claims_are_organizer_confirmed": False,
            "receipt_policy": leaderboard.get("receipt_policy", "No copied submission-page receipt is available."),
        },
        "workspace": {
            "status": audit.get("status", "unknown"),
            "missing_inputs": audit.get("missing_inputs", []),
            "ready_for_holdout": audit.get("ready_for_holdout", False),
        },
        "candidate": candidate_block(run_card),
        "sources": {
            "registered": len(source_register.get("sources", [])),
            "official_data_download_authenticated": False,
        },
    }
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(feed, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(feed, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

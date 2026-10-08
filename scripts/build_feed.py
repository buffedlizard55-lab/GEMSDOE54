#!/usr/bin/env python3
"""Build a small repository-local status feed; this does not scrape the leaderboard."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--audit", default=str(ROOT / "docs/data/workspace-audit.json"))
    parser.add_argument("--run-card", default=str(ROOT / "docs/data/run-card.json"))
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
        "candidate": {
            "verdict": run_card.get("verdict", "unknown"),
            "candidate_surface_preflighted": run_card.get("submission", {}).get("candidate_surface_preflighted", False),
            "candidate_tif_generated": run_card.get("submission", {}).get("candidate_tif_generated", False),
            "new_candidate_downloadable": run_card.get("submission", {}).get("downloadable_new_tif", False),
            "safe_to_upload": run_card.get("submission", {}).get("safe_to_upload", run_card.get("submission", {}).get("safe_to_upload_from_this_run", False)),
            "holdout_status": run_card.get("holdout_dti", {}).get("status", "not recorded"),
            "existing_repository_artifact": run_card.get("submission", {}).get("existing_repository_artifact"),
            "existing_artifact_downloadable_for_research": True,
            "existing_artifact_approved_for_upload": False,
        },
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

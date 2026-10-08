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
    parser.add_argument("--output", default=str(ROOT / "docs/data/feed.json"))
    args = parser.parse_args()
    audit = json.loads(Path(args.audit).read_text(encoding="utf-8"))
    run_card = json.loads(Path(args.run_card).read_text(encoding="utf-8"))
    source_register = json.loads(Path(args.sources).read_text(encoding="utf-8"))
    feed = {
        "schema": "gemsdoe54.local-feed.v1",
        "generated_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "scope": "This repository's local audit records only; not a DrivenData leaderboard feed.",
        "leaderboard": {"status": "not_fetched", "score_claims_are_organizer_confirmed": False},
        "workspace": {
            "status": audit.get("status", "unknown"),
            "missing_inputs": audit.get("missing_inputs", []),
            "ready_for_holdout": audit.get("ready_for_holdout", False),
        },
        "candidate": {
            "verdict": run_card.get("verdict", "unknown"),
            "tif_downloadable": run_card.get("submission", {}).get("downloadable_tif", False),
            "safe_to_upload": run_card.get("submission", {}).get("safe_to_upload", False),
            "holdout_status": run_card.get("holdout_dti", {}).get("status", "not recorded"),
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

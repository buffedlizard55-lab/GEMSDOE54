#!/usr/bin/env python3
"""Write docs/data/feed.json (schema gemsdoe54.local-feed.v2) from receipts. No hand-typed status.

Sources: docs/data/run-card-cgrc.json (run card v3), evidence/lane_summary_cgrc_v1.json,
docs/data/leaderboard-snapshot.json (the only typed input: displayed public-page values).
scripts/build_feed.py is the legacy H54-A feed generator and is kept for its regression tests.
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    card = json.loads((ROOT / "docs/data/run-card-cgrc.json").read_text(encoding="utf-8"))
    lane = json.loads((ROOT / "evidence/lane_summary_cgrc_v1.json").read_text(encoding="utf-8"))
    snap = json.loads((ROOT / "docs/data/leaderboard-snapshot.json").read_text(encoding="utf-8"))
    rows = {r["rank"]: r["displayed_value"] for r in snap["selected_rows"]}
    feed = {
        "schema": "gemsdoe54.local-feed.v2",
        "generated_from": ["docs/data/run-card-cgrc.json", "evidence/lane_summary_cgrc_v1.json",
                           "docs/data/leaderboard-snapshot.json"],
        "scope": "Repository-local status only. Not a DrivenData feed.",
        "candidate": {
            "name": card["candidate"]["name"],
            "primary_path": card["candidate"]["primary"]["path"],
            "primary_sha256": card["candidate"]["primary"]["sha256"],
            "twin_path": card["candidate"]["twin"]["path"],
            "twin_sha256": card["candidate"]["twin"]["sha256"],
            "verdict": card["verdict"]["promotion"],
            "ok_to_submit": False,
            "download_for_inspection_only": True,
            "lane": card["verdict"]["lane"],
            "lane_literal_rule": lane["verdict"]["literal_rule"],
            "format": card["verdict"]["format"],
            "holdout_gate": card["holdout"]["gate_result"],
        },
        "experiments": {"used": card["budget"]["experiments_used"], "limit": card["budget"]["experiments_limit"],
                        "submissions": card["budget"]["submissions"],
                        "slots_selected_by_agent": 0},
        "leaderboard": {
            "fetched_utc": snap["fetched_utc"],
            "status": "PUBLIC-LEADERBOARD SNAPSHOT (displayed values, not organizer receipts)",
            "source_url": snap["source_url"],
            "score_claims_are_organizer_confirmed": False,
            "top_displayed": {"rank_1": rows.get(1), "rank_7": rows.get(7), "rank_13": rows.get(13),
                              "rank_17": rows.get(17)},
            "selected_rows": snap["selected_rows"],
        },
        "workspace": {"status": "same-fold holdout and lane audit complete; no file cleared",
                      "ready_for_submission": False},
    }
    out = ROOT / "docs/data/feed.json"
    out.write_text(json.dumps(feed, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    print(f"wrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

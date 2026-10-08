from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_workspace_audit_cli_writes_blocked_report(tmp_path):
    output = tmp_path / "report.json"
    completed = subprocess.run(
        [sys.executable, str(ROOT / "scripts/audit_workspace.py"),
         "--data-dir", str(tmp_path / "absent"), "--output", str(output)],
        check=True, capture_output=True, text=True,
    )
    assert json.loads(completed.stdout)["status"] == "blocked_missing_inputs"
    assert json.loads(output.read_text())["ready_for_holdout"] is False


def test_local_feed_never_claims_leaderboard_refresh(tmp_path):
    output = tmp_path / "feed.json"
    subprocess.run(
        [sys.executable, str(ROOT / "scripts/build_feed.py"), "--output", str(output)],
        check=True, capture_output=True, text=True,
    )
    feed = json.loads(output.read_text())
    assert feed["leaderboard"]["status"] == "not_fetched"
    assert feed["leaderboard"]["score_claims_are_organizer_confirmed"] is False
    assert feed["candidate"]["safe_to_upload"] is False


def test_audit_and_run_artifacts_are_strict_json_and_stay_fail_closed():
    paths = [
        ROOT / "docs/data/workspace-audit.json",
        ROOT / "docs/data/run-card.json",
        ROOT / "docs/data/source-register.json",
        ROOT / "docs/data/feed.json",
        ROOT / "docs/audit/pinned-template-cache-audit.json",
    ]
    records = [json.loads(path.read_text(encoding="utf-8")) for path in paths]
    run_card = records[1]
    cache_audit = records[4]
    assert run_card["verdict"] == "negative"
    assert run_card["submission"]["downloadable_tif_from_this_run"] is False
    assert run_card["submission"]["existing_repository_artifact"]["holdout_validation"].startswith("NOT ESTABLISHED")
    assert run_card["holdout_dti"]["withheld_positive_count"] == 60988
    assert run_card["holdout_dti"]["status"].startswith("RUN")
    assert run_card["submission"]["ok_to_submit"] is False
    assert run_card["submission"]["ok_to_download_for_submission"] is False
    assert cache_audit["result"].startswith("HASHES_MATCH_OWNER_PINS")
    assert "not an organizer-authenticated" in cache_audit["source"]["role"]
    assert cache_audit["shared_tool_review"]["matches_required_whole_segment_hide_recover"] is False


def test_feed_link_is_outside_element_replaced_by_audit_javascript():
    page = (ROOT / "docs/index.html").read_text(encoding="utf-8")
    status_line = next(line for line in page.splitlines() if 'id="local-audit-status"' in line)
    assert "<a " not in status_line
    assert '<a href="data/feed.json">Open this review\'s local status feed →</a>' in page


def test_mag_ridge_builder_refuses_negative_variants():
    import subprocess
    import sys

    for variant in ("dense", "spaced"):
        proc = subprocess.run(
            [sys.executable, str(ROOT / "scripts/build_mag_ridge_submission.py"),
             "--variant", variant, "--name", "gate-regression-test", "--note", "x", "--team-label", "t"],
            capture_output=True, text=True, cwd=ROOT,
        )
        assert proc.returncode != 0
        assert "REFUSED" in proc.stderr
        assert not (ROOT / "docs/downloads/gate-regression-test.tif").exists()

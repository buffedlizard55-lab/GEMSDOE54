from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_retired_legacy_pipeline_fails_closed_without_side_effects():
    env = os.environ.copy()
    completed = subprocess.run(
        ["bash", str(ROOT / "scripts/run_all.sh")],
        check=False, capture_output=True, text=True, env=env,
    )
    assert completed.returncode == 2
    assert "historical H54-A pipeline is retired" in completed.stderr
    assert "No build or registry update was performed" in completed.stderr


def test_workspace_audit_cli_writes_blocked_report(tmp_path):
    output = tmp_path / "report.json"
    completed = subprocess.run(
        [sys.executable, str(ROOT / "scripts/audit_workspace.py"),
         "--data-dir", str(tmp_path / "absent"), "--output", str(output)],
        check=True, capture_output=True, text=True,
    )
    assert json.loads(completed.stdout)["status"] == "blocked_missing_inputs"
    assert json.loads(output.read_text())["ready_for_holdout"] is False


def test_local_feed_carries_a_timestamped_public_snapshot_without_receipt_claim(tmp_path):
    output = tmp_path / "feed.json"
    subprocess.run(
        [sys.executable, str(ROOT / "scripts/build_feed.py"), "--output", str(output)],
        check=True, capture_output=True, text=True,
    )
    feed = json.loads(output.read_text())
    assert feed["leaderboard"]["status"].startswith("PUBLIC-LEADERBOARD SNAPSHOT")
    assert feed["leaderboard"]["fetched_utc"] == "2026-10-09"  # re-fetched 2026-10-09
    assert feed["leaderboard"]["score_claims_are_organizer_confirmed"] is False
    assert {1, 7, 13, 17} <= {row["rank"] for row in feed["leaderboard"]["selected_rows"]}  # named board rows kept
    assert feed["candidate"]["candidate_surface_preflighted"] is True
    # run 2: the own-model TIF exists and is downloadable for review only; it is never cleared to submit
    assert feed["candidate"]["candidate_tif_generated"] is True
    assert feed["candidate"]["new_candidate_downloadable"] is True
    assert feed["candidate"]["safe_to_upload"] is False
    assert feed["candidate"]["ok_to_submit"] is False
    assert feed["candidate"]["existing_artifact_downloadable_for_research"] is True
    assert feed["candidate"]["existing_artifact_approved_for_upload"] is False
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
    assert run_card["submission"]["candidate_surface_preflighted"] is True
    assert run_card["submission"]["candidate_tif_generated"] is True  # run 2 generated the review copy
    assert run_card["submission"]["safe_to_upload"] is False
    assert run_card["submission"]["existing_repository_artifact"]["holdout_validation"].startswith("HOLDOUT-DTI")
    assert run_card["submission"]["existing_repository_artifact"]["format_validation"].startswith("FAIL")
    assert run_card["holdout_dti"]["withheld_positive_count"] == 60988
    assert cache_audit["result"].startswith("HASHES_MATCH_OWNER_PINS")
    assert "not an organizer-authenticated" in cache_audit["source"]["role"]
    assert cache_audit["shared_tool_review"]["matches_required_whole_segment_hide_recover"] is False


def test_feed_link_is_outside_element_replaced_by_audit_javascript():
    page = (ROOT / "docs/index.html").read_text(encoding="utf-8")
    status_line = next(line for line in page.splitlines() if 'id="local-audit-status"' in line)
    assert "<a " not in status_line
    assert '<a href="data/feed.json">data/feed.json</a>' in page  # landing-page feed link (2026-10-09 wording)


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


def test_magnetic_ridge_holdout_is_recorded_as_negative_and_not_submittable():
    card = json.loads((ROOT / "docs/data/run-card.json").read_text(encoding="utf-8"))
    block = card["magnetic_ridge_holdout"]
    assert block["withheld_positive_count"] == 60988
    assert block["E1_dense_frozen"]["promote_eligible"] is False
    assert block["E2_spaced_exploratory"]["promote_eligible"] is False
    assert block["ok_to_submit"] is False
    assert card["submission"]["ok_to_submit"] is False
    assert card["submission"]["ok_to_download_for_submission"] is False

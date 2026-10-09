#!/usr/bin/env python3
"""Regression tests for scripts/summarise_lane_scan.py (2026-10-09).

Protocol reading under test: the 70% overlap limit applies to every sibling raster with dots, the candidate's
own same-design twin is excluded and listed, and rank correlation is tested as an absolute value.
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
_spec = importlib.util.spec_from_file_location("summarise_lane_scan", ROOT / "scripts/summarise_lane_scan.py")
mod = importlib.util.module_from_spec(_spec)
sys.modules["summarise_lane_scan"] = mod
_spec.loader.exec_module(mod)


def _row(repo, path, *, cov, ov, rho, decoded=False, exact=False):
    return {"repo": repo, "path": path, "coverage_3px_of_footprint": cov, "overlap_cand_in_sib": ov,
            "spearman_rho": rho, "exact_decoded_match": decoded, "exact_file_match": exact, "n_dots": 10}


def test_literal_verdict_twin_blanket_sparse_and_absolute_rho(tmp_path: Path):
    rows = [
        _row("GEMSDOE54", "docs/downloads/cand-nan.tif", cov=1.0, ov=1.0, rho=1.0, decoded=True),  # own twin
        _row("B", "blanket.tif", cov=1.0, ov=1.0, rho=0.1),                                       # literal fail
        _row("C", "sparse.tif", cov=0.3, ov=0.8, rho=0.2),                                        # non-degenerate fail
        _row("D", "clean.tif", cov=0.2, ov=0.1, rho=-0.95),                                       # |rho| > 0.9
        _row("E", "unrelated.tif", cov=0.1, ov=0.0, rho=0.0),
    ]
    table = tmp_path / "table.json"
    table.write_text(json.dumps(rows))
    scan = tmp_path / "scan.json"
    scan.write_text(json.dumps({"result": {"siblings_with_overlap_above_limit": 3}}))
    out = tmp_path / "summary.json"
    sys.argv = ["summarise_lane_scan.py", "--table", str(table), "--scan", str(scan),
                "--exclude-same-design-prefix", "GEMSDOE54/docs/downloads/cand", "--out", str(out)]
    assert mod.main() == 0
    s = json.loads(out.read_text())
    assert [x["file"] for x in s["same_design_excluded"]] == ["GEMSDOE54/docs/downloads/cand-nan.tif"]
    assert s["literal_overlap_fail_count"] == 2
    assert s["literal_overlap_fail_blanket_count"] == 1
    assert s["literal_overlap_fail_nondegenerate_count"] == 1
    assert s["nondegenerate_overlap_failures"][0]["file"] == "C/sparse.tif"
    assert s["max_abs_spearman_rho"]["value"] == 0.95
    assert s["verdict_literal"] == "FAIL"
    assert s["verdict_rho"] == "FAIL"
    assert s["verdict_copy"] == "PASS"

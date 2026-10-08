#!/usr/bin/env python3
"""Reproducible analysis of the top-scoring GEMSDOE32 artefact (H33-2-B2) and its closed-form algebra.

Everything derivable is recomputed here from bytes or from exact arithmetic. Owner-recorded values
are copied from the owner's public files, cited by path, and labelled OWNER-RECORDED. A board value
is labelled BOARD-UNVERIFIED because no organizer receipt is available to this repository.

Outputs evidence/top_artefact_analysis.json.

Run:  python scripts/top_artefact_analysis.py
"""

from __future__ import annotations

import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import rasterio

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from gemsdoe54.holdout import pooled_metric  # noqa: E402

ALPHA, BETA = 0.2, 0.8

# OWNER-RECORDED (GEMSDOE32 public files; not organizer-confirmed)
OWNER = {
    "h33_audit_json": "GEMSDOE32/docs/downloads/gemsdoe32-h33-h33-2-b2-20261004T220000Z-e5eb6e7e-audit.json",
    "zeros_sha256": "c55bafc470054e8271dcb89347a17e07fefe50de6af6e6ba6c4b169ef7ab6fa9",
    "zeros_positive_pixels": 37654,
    "base_dots_per_owner_readme": 40199,      # GEMSDOE32 README line ~100: "best live-scored emission (40,199 dots)"
    "base_board_value_user_reported": 0.2708,
    "claimed_board_value_user_reported": 0.2778,
    "owner_predicted_leaderboard_dti": 0.27467315976932155,
    "owner_ei_drift_corrected_gain": 0.004869544019442784,
    "owner_catalogue_hidden_mean": 0.004600104084398947,
    "owner_catalogue_hidden_per_quadrant": {"foldNW": 0.17845441391493597, "foldNE": 0.4228785103505033,
                                            "foldSW": 0.21382513739633008, "foldSE": 0.25652406461743227},
    "owner_drift_corrected_holdout_mean": 0.04504333270394367,
    "owner_manifest_label": "UNSCORED",
}


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> int:
    reg = ROOT / "registry/registry_rasters"
    top_path = reg / "dotted_b2_prune_02778.tif"
    base_path = reg / "dotted_d2_8_02708.tif"
    ref_path = reg / "dotted_d2_8_02600.tif"
    rasters = {}
    for name, p in [("top_0.2778_registry_copy", top_path), ("base_0.2708_registry", base_path),
                    ("reference_0.2600_registry", ref_path)]:
        with rasters_open(p) as arr:
            rasters[name] = {"path": p.relative_to(ROOT).as_posix(), "sha256": sha256_file(p),
                             "dots": int(np.count_nonzero(arr > 0))}
    top_bytes_match = rasters["top_0.2778_registry_copy"]["sha256"] == OWNER["zeros_sha256"]

    # ---- exact algebra -------------------------------------------------------------------
    k_deleted = OWNER["base_dots_per_owner_readme"] - OWNER["zeros_positive_pixels"]
    dti0 = OWNER["base_board_value_user_reported"]
    dti1 = OWNER["claimed_board_value_user_reported"]
    # If every deleted dot earns zero credit, deletion changes only FP (by -k), so
    #   DTI1 = T / (T + 0.2 (FP - k) + 0.8 FN)  and  DTI0 = T / (T + 0.2 FP + 0.8 FN).
    # Eliminating the denominator's unknown part gives T = 0.2 k / (1/DTI0 - 1/DTI1).
    T_implied = ALPHA * k_deleted / (1.0 / dti0 - 1.0 / dti1)
    denom0_implied = T_implied * (1.0 / dti0 - 1.0)  # = 0.2 FP + 0.8 FN at the base
    # sensitivity: if only a fraction f of deleted dots had zero credit, the identity changes
    sens = {}
    for f in (1.0, 0.9, 0.75, 0.5):
        k_eff = f * k_deleted
        sens[f"zero_credit_fraction_{f}"] = round(ALPHA * k_eff / (1.0 / dti0 - 1.0 / dti1), 1)

    # owner's own arithmetic consistency checks
    owner_checks = {
        "per_quadrant_mean_vs_recorded_mean": {
            "per_quadrant_mean": round(float(np.mean(list(OWNER["owner_catalogue_hidden_per_quadrant"].values()))), 6),
            "recorded_mean": round(OWNER["owner_catalogue_hidden_mean"], 6),
            "consistent": bool(abs(np.mean(list(OWNER["owner_catalogue_hidden_per_quadrant"].values()))
                                   - OWNER["owner_catalogue_hidden_mean"]) < 1e-3),
        },
        "base_plus_gain_vs_projection": {
            "base_plus_gain": round(OWNER["base_board_value_user_reported"] + OWNER["owner_ei_drift_corrected_gain"], 6),
            "owner_projection": round(OWNER["owner_predicted_leaderboard_dti"], 6),
            "consistent": bool(abs(OWNER["base_board_value_user_reported"] + OWNER["owner_ei_drift_corrected_gain"]
                                   - OWNER["owner_predicted_leaderboard_dti"]) < 5e-4),
        },
        "board_gain_vs_owner_gain": {
            "board_gain": round(dti1 - dti0, 6),
            "owner_recorded_gain": round(OWNER["owner_ei_drift_corrected_gain"], 6),
        },
    }

    # Worked example: verify the closed form on a synthetic grid (same identity as the repo test)
    rng = np.random.default_rng(11)
    truth = np.zeros((200, 200), bool)
    truth[60:140, 100] = True
    dots = np.zeros_like(truth)
    dots[60:140:8, 100] = True
    far = rng.choice(200 * 200, size=30, replace=False)
    dots.ravel()[far] = True
    dti_a, tp_a, fp_a, fn_a = pooled_metric(truth, dots)
    from scipy.ndimage import distance_transform_edt
    dd = distance_transform_edt(~truth)
    ys, xs = np.nonzero(dots)
    zero = np.flatnonzero(np.clip(1 - dd[ys, xs] / 3.0, 0, 1) == 0)
    pr = dots.copy()
    pr[ys[zero], xs[zero]] = False
    dti_b, tp_b, fp_b, fn_b = pooled_metric(truth, pr)
    closed = tp_a / (tp_a + ALPHA * (fp_a - zero.size) + BETA * fn_a)
    synthetic = {
        "zero_credit_dots_deleted": int(zero.size),
        "tp_unchanged": bool(abs(tp_b - tp_a) < 1e-9),
        "fn_unchanged": bool(abs(fn_b - fn_a) < 1e-9),
        "fp_drop_equals_deleted_count": bool(abs((fp_a - fp_b) - zero.size) < 1e-9),
        "closed_form_matches_grid": bool(abs(closed - dti_b) < 1e-9),
        "dti_before": round(dti_a, 9), "dti_after": round(dti_b, 9),
    }
    if not all(synthetic[k] for k in ("tp_unchanged", "fn_unchanged", "fp_drop_equals_deleted_count",
                                       "closed_form_matches_grid")):
        raise SystemExit("closed-form identity failed on the synthetic check")

    out = {
        "generated_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "label": "analysis of owner-recorded and registry-verified facts; not a score",
        "registry_verified_rasters": rasters,
        "top_artefact_registry_copy_is_byte_identical_to_owner_zeros_file": top_bytes_match,
        "owner_recorded": {k: v for k, v in OWNER.items()},
        "base_dots_registry_vs_owner": {
            "registry_0.2708_raster_dots": rasters["base_0.2708_registry"]["dots"],
            "owner_readme_base_dots": OWNER["base_dots_per_owner_readme"],
            "consistent": rasters["base_0.2708_registry"]["dots"] == OWNER["base_dots_per_owner_readme"],
        },
        "deleted_dots_k": int(k_deleted),
        "algebra": {
            "identity": "DTI1 = T/(T+0.2(FP-k)+0.8FN) when all k deleted dots earn zero credit",
            "T_implied_credit_mass": round(T_implied, 1),
            "denominator_0_2FP_plus_0_8FN_at_base": round(denom0_implied, 1),
            "sensitivity_zero_credit_fraction": sens,
            "caveat": ("Requires the board pair to be correct and unscored-by-receipt values to be exact; "
                       "a single unreceipted pair identifies T only under this assumption."),
        },
        "owner_internal_consistency": owner_checks,
        "synthetic_identity_check": synthetic,
        "achievability_note": (
            "Under the metric, DTI is bounded above by 1. Zero-credit deletions raise DTI monotonically. "
            "A score above the board value requires more credited truth per dot than the parent, which the "
            "catalogue holdout cannot establish for the hidden set (see evidence/holdout_segment_cv_v1.json)."),
    }
    out_path = ROOT / "evidence/top_artefact_analysis.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(out, indent=2, default=float) + "\n", encoding="utf-8")
    print(json.dumps({"registry_top_bytes_match_owner": top_bytes_match,
                      "base_dots_registry": rasters["base_0.2708_registry"]["dots"],
                      "k_deleted": int(k_deleted), "T_implied": round(T_implied, 1),
                      "owner_checks": owner_checks, "synthetic": synthetic}, indent=2, default=float))
    return 0


class rasters_open:  # small context manager returning the positive-cell array
    def __init__(self, path: Path):
        self.path = path

    def __enter__(self):
        with rasterio.open(self.path) as ds:
            return np.nan_to_num(ds.read(1).astype(np.float64), nan=0.0)

    def __exit__(self, *exc):
        return False


if __name__ == "__main__":
    raise SystemExit(main())

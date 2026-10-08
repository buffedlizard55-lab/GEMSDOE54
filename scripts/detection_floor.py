#!/usr/bin/env python3
"""Experiment E3: the holdout's detection floor for near-identical submissions.

The user's question: is a 0.0028 pooled-DTI gap (0.2778 vs 0.2750) distinguishable from
noise on a whole-segment holdout?  Cohen's framework needs the SD of the paired difference,
not the pixel count.  This script measures that SD directly with the exact leave-one-
segment-group-out jackknife (src/gemsdoe54/jackknife.py) for three pairs on the same
partition used by E1/E2:

  A  dense ridge, quantile 0.98          (the E1 candidate)
  B  dense ridge, quantile 0.97          (near-identical: one threshold step apart)
  C  spaced emission of A, 3 px          (the E2 candidate)

Output: evidence/detection_floor.json.  Labels: HOLDOUT-DTI-derived floor measurement,
not a candidate score and not ORGANIZER-CONFIRMED.
"""

from __future__ import annotations

import importlib.util
import json
import sys
import time
from pathlib import Path

import numpy as np
import rasterio
from scipy.ndimage import distance_transform_edt
from scipy.stats import norm

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from gemsdoe54.emission import emit_spaced_dots  # noqa: E402
from gemsdoe54.holdout import segment_blocks  # noqa: E402
from gemsdoe54.jackknife import (  # noqa: E402
    group_jackknife_counts,
    jackknife_se,
    leave_one_out_dti,
    pooled_dti_from_counts,
)
from gemsdoe54.power import minimum_detectable_cohen_d, normal_approx_mde_from_se  # noqa: E402
from gemsdoe54.ridge import gate_by_visible, invalid_feature_mask, ridge_candidate  # noqa: E402

_spec = importlib.util.spec_from_file_location("rsh", ROOT / "scripts/run_segment_holdout.py")
rsh = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(rsh)

LABELS = ROOT / "data/grid/labels.tif"
FEATURES = Path("/tmp/gems-cache/training_features.tif")
OUT = ROOT / "evidence/detection_floor.json"
BASE_SEED = 20261008
K = 4


def main() -> int:
    t0 = time.time()
    assert rsh.sha256(LABELS) == rsh.LABELS_SHA
    assert rsh.sha256(FEATURES) == rsh.FEATURES_SHA
    lab = rasterio.open(LABELS).read(1)
    foot = lab >= 0
    cat = lab == 1
    with rasterio.open(FEATURES) as ds:
        rtp = ds.read(2)
        thd = ds.read(3)
    bad = invalid_feature_mask(rtp, thd)
    ridge_a = ridge_candidate(rtp, thd, foot & ~bad, quantile=0.98)
    ridge_b = ridge_candidate(rtp, thd, foot & ~bad, quantile=0.97)
    priority = np.where(foot & ~bad, thd.astype(np.float64), -1.0)
    blocks, _ = segment_blocks(cat.astype(np.uint8), buffer_px=3)
    fold_of = rsh.assign_folds(blocks, cat, K, np.random.default_rng(BASE_SEED))
    grp_fold = np.where(blocks > 0, fold_of[blocks], -1)

    per = {"A": [], "B": [], "C": []}
    for k in range(K):
        in_k = grp_fold == k
        truth = cat & in_k
        visible = cat & ~in_k
        a = gate_by_visible(ridge_a, visible) & foot
        b = gate_by_visible(ridge_b, visible) & foot
        c = emit_spaced_dots(a, priority=priority, spacing_px=3.0)
        for name, pred in (("A", a), ("B", b), ("C", c)):
            per[name].append(group_jackknife_counts(pred, truth, blocks, foot))
        print(f"fold {k}: A={int(a.sum()):,} B={int(b.sum()):,} C={int(c.sum()):,} dots  "
              f"[{time.time() - t0:.0f}s]", flush=True)

    def pooled(name: str):
        cs = per[name]
        TP = sum(c["TP"] for c in cs); FP = sum(c["FP"] for c in cs); G = sum(c["G"] for c in cs)
        loo = leave_one_out_dti({
            "TP": TP, "FP": FP, "G": G,
            "tp_g": np.concatenate([c["tp_g"] for c in cs]),
            "n_g": np.concatenate([c["n_g"] for c in cs]),
            "dfp_g": np.concatenate([c["dfp_g"] for c in cs]),
        })
        gids = np.concatenate([c["gids"] for c in cs])
        return gids, loo, pooled_dti_from_counts(TP, FP, G - TP), int(sum(c["n_g"].sum() for c in cs))

    res = {k: pooled(k) for k in per}
    gids_ref = res["A"][0]
    for k in res:
        assert np.array_equal(res[k][0], gids_ref)
    z = float(norm.ppf(0.975))
    rows = []
    for x, y, label in (("A", "B", "near-identical pair (quantile 0.98 vs 0.97)"),
                        ("A", "C", "dense vs spaced emission (same ridge)")):
        theta = res[x][1] - res[y][1]
        se = jackknife_se(theta)
        diff = res[x][2] - res[y][2]
        mde = float(normal_approx_mde_from_se(se))
        rows.append({
            "pair": f"{x} - {y}",
            "description": label,
            "point_difference_pooled_dti": round(diff, 6),
            "jackknife_se": round(se, 6),
            "ci95": [round(diff - z * se, 6), round(diff + z * se, 6)],
            "mde_80pct_power_alpha05_raw_dti": round(mde, 6),
            "gap_0_0028_inside_detection_floor": bool(abs(0.0028) < mde),
            "ci_excludes_zero": bool((diff - z * se) > 0 or (diff + z * se) < 0),
        })
    n_units = int(gids_ref.size)
    n_pos = int(cat.sum())
    naive_d = 2.0 * float(norm.ppf(0.975) + norm.ppf(0.80)) / np.sqrt(n_pos)
    out = {
        "label": "HOLDOUT-DTI-derived detection floor (E3). Not a candidate score; not ORGANIZER-CONFIRMED.",
        "experiment": "E3 detection floor",
        "partition": {"seed": BASE_SEED, "folds": K, "units_segment_groups": n_units},
        "withheld_positives": n_pos,
        "pooled_dti_first_partition": {k: round(res[k][2], 6) for k in res},
        "pairs": rows,
        "cohen_framework": {
            "minimum_detectable_cohen_d_units": round(float(minimum_detectable_cohen_d(n_units)), 4),
            "naive_pixel_level_d_if_pixels_were_independent": round(naive_d, 5),
            "note": ("The pixel-level d is anti-conservative: fault pixels within a segment are spatially "
                     "dependent and pooled DTI is nonlinear, so the segment-group jackknife is the "
                     "valid floor. The naive pixel d is shown only to make the error visible."),
        },
        "interpretation": (
            "A gap of 0.0028 is compared with the MDE of each pair. If it is below the MDE, the gap cannot "
            "be separated from noise by this holdout, so no ranking should be read from it."
        ),
        "runtime_s": round(time.time() - t0, 1),
    }
    OUT.write_text(json.dumps(out, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"pairs": rows, "cohen": out["cohen_framework"]}, indent=2))
    print(f"wrote {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

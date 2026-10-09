#!/usr/bin/env python3
"""E1 — whole-segment hide-and-recover holdout for the H54-C candidates.

Reuses the shared evaluator machinery of ``scripts/holdout_segment_cv.py``
(``gemsdoe54-segment-cv`` v1: FoldScorer exact decomposition, dti_from, seeds,
folds) and the candidate library ``src/gemsdoe54/h54c.py``.  Candidates C1
(endpoint continuation) and C2 (manifestation-corroborated radiometric edges)
are scored against withheld catalogue segments under the preregistered rule
(``evidence/preregistration_h54c.json``); C0 is the matched random-admissible
control.  Each candidate's dots are built from VISIBLE faults only.

Every number this script writes is HOLDOUT-DTI (catalogue-recovery truth, not
hidden-test labels).  Canary: single-feature AUC > 0.90 = LEAKAGE.  Paired
whole-segment cluster bootstrap percentile CIs; normal-approximation MDE at
80 % power (Cohen 1988) for every paired comparison.

Run:  python scripts/run_holdout_h54c.py --boot 1000 --shifts 20
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import rasterio
from scipy.ndimage import distance_transform_edt, label

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from gemsdoe54.grid import FOOTPRINT_CELLS, footprint, read_band  # noqa: E402
from gemsdoe54.holdout import pooled_metric, single_feature_auc  # noqa: E402
from gemsdoe54.power import minimum_detectable_cohen_d, normal_approx_mde_from_se  # noqa: E402
from holdout_segment_cv import FoldScorer, dti_from  # noqa: E402  (shared evaluator machinery)
from gemsdoe54 import h54c  # noqa: E402

EVALUATOR = {"name": "gemsdoe54-segment-cv", "version": "v1"}
K_FOLDS = 5
SEED = 20261008
BUFFER_PX = 3.0
KERNEL_PX = 3.0
ALPHA, BETA = 0.2, 0.8
AUC_CUT = 0.90
NAMES = ["C0_random_admissible_control", "C1_endpoint_continuation", "C2_manifest_radedge",
         "C2b_manifest_radedge_ungated"]


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def default_paths() -> dict[str, Path]:
    return {
        "volcanics": ROOT / "data/external/derived_gdr_volcanics_100m_u8.tif",
        "paleo": ROOT / "data/external/derived_gdr_paleo_100m_u8.tif",
        "probes": ROOT / "data/external/derived_gdr_2m_probes_100m_u8.tif",
        "rad": ROOT / "data/external/geodawn_rad_u8.tif",
        "ext": ROOT / "data/external/geodawn_extensions_u8.tif",
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--labels", default=str(ROOT / "data/grid/labels.tif"))
    ap.add_argument("--out", default=str(ROOT / "evidence/holdout_h54c_v1.json"))
    ap.add_argument("--boot", type=int, default=1000)
    ap.add_argument("--shifts", type=int, default=20)
    args = ap.parse_args()

    paths = default_paths()
    missing = [k for k, p in paths.items() if not p.exists()]
    if missing:
        raise SystemExit(f"missing input mirrors: {missing}; run scripts/fetch_h54c_inputs.sh")

    foot = footprint(args.labels)
    labels_raw, _ = read_band(args.labels)
    cat = (labels_raw == 1) & foot
    seg_lab, n_seg_total = label(cat, structure=np.ones((3, 3), dtype=int))
    rng = np.random.default_rng(SEED)
    order = rng.permutation(n_seg_total) + 1
    fold_of_seg = np.full(n_seg_total + 1, -1, dtype=np.int16)
    for i, sid in enumerate(order):
        fold_of_seg[sid] = i % K_FOLDS
    cell_fold = fold_of_seg[seg_lab]
    seg_fold_counts = [int(np.sum(fold_of_seg[1:] == k)) for k in range(K_FOLDS)]

    # C2 auxiliary fields are catalogue-independent: compute once.
    _, d_manifest_px = h54c.load_manifest_mask(paths)
    grad_mag = h54c.c2_gradient(paths, foot)

    per_fold = []
    t0 = datetime.now(timezone.utc)
    for k in range(K_FOLDS):
        W = cat & (cell_fold == k)
        dW = distance_transform_edt(~W)
        collar = (dW <= BUFFER_PX) & ~W
        V = cat & ~W & ~collar
        S = foot & ~V & ~collar
        dV_px = distance_transform_edt(~V)
        dist_m = dV_px * 100.0
        E = dV_px <= BUFFER_PX
        adm = foot & ~E

        segs_k = np.unique(seg_lab[W])
        local_map = np.full(n_seg_total + 1, -1, dtype=np.int64)
        local_map[segs_k] = np.arange(segs_k.size)
        seg_local = np.where(W, local_map[seg_lab], -1)
        scorer = FoldScorer(W, seg_local, int(segs_k.size), S)

        c1 = h54c.build_candidate("C1_endpoint_continuation", V, foot)
        c2 = h54c.build_candidate("C2_manifest_radedge", V, foot, paths=paths)
        c2b = h54c.build_candidate("C2b_manifest_radedge_ungated", V, foot, paths=paths)
        # C0: chance control, uniformly random admissible cells, count-matched to C1.
        rng_c0 = np.random.default_rng(SEED + 1000 + k)
        adm_idx = np.flatnonzero(adm.ravel())
        target = int(c1["dots"].sum())
        c0 = np.zeros(adm.size, dtype=bool)
        c0[rng_c0.choice(adm_idx, size=min(target, adm_idx.size), replace=False)] = True
        c0 = c0.reshape(adm.shape)
        dots_by = {NAMES[0]: c0, NAMES[1]: c1["dots"], NAMES[2]: c2["dots"], NAMES[3]: c2b["dots"]}

        fold_rec = {
            "fold": k,
            "withheld_segments": int(segs_k.size),
            "withheld_positive_cells": int(W.sum()),
            "buffer_collar_cells": int(collar.sum()),
            "visible_catalogue_cells": int(V.sum()),
            "scored_cells": int(S.sum()),
            "exclusion_cells_E": int((E & foot).sum()),
            "C1_support_cells": int(c1["support"].sum()),
            "C2_support_cells": int(c2["support"].sum()),
            "C2b_support_cells": int(c2b["support"].sum()),
            "candidates": {},
            "canary": {},
            "nulls": {},
        }
        boot_idx = rng.integers(0, segs_k.size, size=(args.boot, segs_k.size))
        for nm in NAMES:
            sc = scorer.score(dots_by[nm], with_D=True)
            if k == 0 and nm == NAMES[0]:
                chk_dti, chk_tp, chk_fp, chk_fn = pooled_metric(W, dots_by[nm] & S, kernel_px=KERNEL_PX,
                                                                alpha=ALPHA, beta=BETA)
                assert abs(chk_tp - sc["TP"]) < 1e-6 and abs(chk_fp - sc["FP"]) < 1e-6 \
                    and abs(chk_fn - sc["FN"]) < 1e-6, "decomposed metric disagrees with grid implementation"
                fold_rec["cross_check_fold0_C0"] = {
                    "grid_dti": round(chk_dti, 9),
                    "decomposed_dti": round(dti_from(sc["TP"], sc["FP"], sc["FN"]), 9),
                }
            boot_tp = np.zeros(args.boot)
            boot_fp = np.zeros(args.boot)
            boot_fn = np.zeros(args.boot)
            D = sc["D"] if sc["n"] and sc["D"] is not None and sc["D"].shape[0] == sc["n"] \
                else np.zeros((0, segs_k.size), np.float32)
            G = scorer.G_seg
            TPs = sc["TP_seg"]
            for b in range(args.boot):
                mult = np.bincount(boot_idx[b], minlength=segs_k.size).astype(np.float64)
                boot_tp[b] = mult @ TPs
                boot_fn[b] = mult @ (G - TPs)
                present = mult > 0
                if D.shape[0]:
                    dmin = D[:, present].min(axis=1)
                    boot_fp[b] = float(np.sum(1.0 - np.clip(1.0 - dmin / KERNEL_PX, 0.0, 1.0)))
            fold_rec["candidates"][nm] = {
                "dots_in_scored_area": sc["n"], "TP_w": sc["TP"], "FP_w": sc["FP"], "FN_w": sc["FN"],
                "boot_tp": boot_tp, "boot_fp": boot_fp, "boot_fn": boot_fn,
                "tp_seg": TPs, "G_seg": G,
            }
            del D
            # torus-shift null, restricted to the scored area at scoring time
            nulls = []
            for _ in range(args.shifts):
                dy = int(rng.integers(-(foot.shape[0] - 1), foot.shape[0]))
                dx = int(rng.integers(-(foot.shape[1] - 1), foot.shape[1]))
                shifted = np.roll(np.roll(dots_by[nm], dy, axis=0), dx, axis=1)
                nsc = scorer.score(shifted, with_D=False)
                nulls.append((nsc["TP"], nsc["FP"], nsc["FN"]))
            fold_rec["nulls"][nm] = [list(map(float, x)) for x in nulls]

        # leakage canaries: each candidate's feature alone + the withholding artefacts
        fold_rec["canary"]["C1_endpoint_surface"] = round(
            single_feature_auc(c1["surface"], W, valid=S), 6)
        fold_rec["canary"]["C2_grad_mag"] = round(
            single_feature_auc(grad_mag.astype(np.float32), W, valid=S), 6)
        fold_rec["canary"]["C2_d_manifest_px"] = round(
            single_feature_auc(d_manifest_px.astype(np.float32), W, valid=S), 6)
        fold_rec["canary"]["dist_to_visible_catalogue_m"] = round(
            single_feature_auc(dist_m.astype(np.float32), W, valid=S), 6)
        per_fold.append(fold_rec)
        print(f"fold {k}: segs={segs_k.size} W={int(W.sum())} C1={target} "
              f"C2={int(c2['dots'].sum())} elapsed={(datetime.now(timezone.utc) - t0).seconds}s", flush=True)

    cand_out, pooled_boot = {}, {}
    for nm in NAMES:
        tp = sum(f["candidates"][nm]["TP_w"] for f in per_fold)
        fp = sum(f["candidates"][nm]["FP_w"] for f in per_fold)
        fn = sum(f["candidates"][nm]["FN_w"] for f in per_fold)
        point = dti_from(tp, fp, fn)
        btp = sum(f["candidates"][nm]["boot_tp"] for f in per_fold)
        bfp = sum(f["candidates"][nm]["boot_fp"] for f in per_fold)
        bfn = sum(f["candidates"][nm]["boot_fn"] for f in per_fold)
        bdti = np.array([dti_from(btp[b], bfp[b], bfn[b]) for b in range(args.boot)])
        pooled_boot[nm] = bdti
        cand_out[nm] = {
            "pooled_dti_point": round(point, 6),
            "pooled_tp_w": round(tp, 4), "pooled_fp_w": round(fp, 4), "pooled_fn_w": round(fn, 4),
            "dots_total": int(sum(f["candidates"][nm]["dots_in_scored_area"] for f in per_fold)),
            "bootstrap_sd": round(float(bdti.std(ddof=1)), 6),
            "ci95_percentile": [round(float(np.percentile(bdti, 2.5)), 6),
                                round(float(np.percentile(bdti, 97.5)), 6)],
            "label": "HOLDOUT-DTI",
        }

    paired = {}
    for a, b in [(NAMES[1], NAMES[0]), (NAMES[2], NAMES[0]), (NAMES[1], NAMES[2]),
                 (NAMES[3], NAMES[0]), (NAMES[3], NAMES[2]), (NAMES[3], NAMES[1])]:
        d = pooled_boot[a] - pooled_boot[b]
        point = cand_out[a]["pooled_dti_point"] - cand_out[b]["pooled_dti_point"]
        se = float(d.std(ddof=1))
        paired[f"{a} minus {b}"] = {
            "point": round(point, 6),
            "bootstrap_se": round(se, 6),
            "ci95_percentile": [round(float(np.percentile(d, 2.5)), 6),
                                round(float(np.percentile(d, 97.5)), 6)],
            "mde_raw_80pct_two_sided": round(normal_approx_mde_from_se(se), 6),
            "bootstrap_sign_p": round(float(min(1.0, 2 * min((d <= 0).mean(), (d >= 0).mean()))), 4),
        }

    null_summary = {}
    for nm in NAMES:
        vals = []
        for s in range(args.shifts):
            ntp = sum(f["nulls"][nm][s][0] for f in per_fold)
            nfp = sum(f["nulls"][nm][s][1] for f in per_fold)
            nfn = sum(f["nulls"][nm][s][2] for f in per_fold)
            vals.append(dti_from(ntp, nfp, nfn))
        vals = np.array(vals)
        null_summary[nm] = {
            "n": int(args.shifts),
            "mean": round(float(vals.mean()), 6),
            "sd": round(float(vals.std(ddof=1)), 6),
            "p95": round(float(np.percentile(vals, 95)), 6),
            "max": round(float(vals.max()), 6),
        }

    canary_summary = {}
    for bn in ["C1_endpoint_surface", "C2_grad_mag", "C2_d_manifest_px",
               "dist_to_visible_catalogue_m"]:
        aucs = [f["canary"][bn] for f in per_fold]
        canary_summary[bn] = {
            "max_auc_over_folds": round(max(aucs), 6),
            "mean_auc": round(float(np.mean(aucs)), 6),
            "flag": "LEAKAGE" if max(aucs) > AUC_CUT else "clear",
        }

    n_total_pos = int(sum(f["withheld_positive_cells"] for f in per_fold))
    payload = {
        "evaluator": EVALUATOR | {
            "metric": "organizer DTI alpha=0.2 beta=0.8 kernel=300 m triangular",
            "seed": SEED, "bootstrap_replicates": args.boot, "shift_nulls": args.shifts,
            "script_sha256": sha256_file(Path(__file__)),
            "preregistration": "evidence/preregistration_h54c.json",
        },
        "label": "HOLDOUT-DTI (evaluator gemsdoe54-segment-cv v1; catalogue-recovery truth, not hidden-test labels)",
        "inputs": {
            "labels": {"path": args.labels, "sha256": sha256_file(Path(args.labels))},
            "paths": {k: {"path": str(p), "sha256": sha256_file(p)} for k, p in paths.items()},
            "footprint_cells": int(foot.sum()), "footprint_expected": FOOTPRINT_CELLS,
        },
        "design": {
            "folds": K_FOLDS, "unit": "8-connected catalogue component (whole segment)",
            "buffer_m": 300, "scored_area": "footprint minus visible catalogue minus buffer collar",
            "visible_only_features": True, "pixel_exact_visible_mask": True,
            "emission": "linearity gate (3,5,6) + 2 px spacing, priority = surface + 1e-3*dist_visible_px",
        },
        "units": {
            "catalogue_segments_total": int(n_seg_total),
            "segments_per_fold": seg_fold_counts,
            "withheld_positive_cells_total": n_total_pos,
            "withheld_positive_cells_per_fold": [f["withheld_positive_cells"] for f in per_fold],
        },
        "candidates": cand_out,
        "paired_differences": paired,
        "shift_nulls": null_summary,
        "canary": canary_summary,
        "power": {
            "cohen_d_min_80pct_alpha05_units_total": round(minimum_detectable_cohen_d(n_seg_total), 5),
            "cohen_d_min_80pct_alpha05_units_per_fold":
                round(minimum_detectable_cohen_d(min(seg_fold_counts)), 5),
            "paired_mde_reported_per_comparison": True,
            "note": "Units are whole segments; paired MDEs come from the cluster bootstrap SE (2.80*SE).",
        },
        "selection_rule": "preregistered: higher pooled HOLDOUT-DTI wins; exact tie -> fewer dots",
        "generated_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(payload, indent=2, allow_nan=False)
    out.write_text(text + "\n", encoding="utf-8")
    print(json.dumps({"candidates": {k: {kk: v[kk] for kk in
                                         ("pooled_dti_point", "ci95_percentile", "dots_total")}
                                     for k, v in cand_out.items()},
                      "canary": canary_summary}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Experiment E2 (2026-10-09): mechanism check for the registry pair behind the 0.2778 board entry.

Pair   : dotted_d2_8_02708 (A, 40,199 dots)  ->  dotted_b2_prune_02778 (B, 37,654 dots)
Claims tested (each recorded as a number, not as a verdict on the board):
  1. B is a strict subset of A (no dot added by pruning).
  2. Every deleted dot lies within 200 m (2 px) of the USGS catalogue cells (labels == 1).
  3. Pooled DTI of A and B against the FULL catalogue (catalogue-proxy, NOT a holdout and NOT an
     organizer score), and the exact algebra DTI = T / (0.2N + 0.8G + 0.2(T - M)).
  4. Marginal rule, exact form, checked by brute force on sampled dots:
        deleting dot x raises DTI  iff  t < 0.2 * DTI * (1 + t - k)
        adding dot x raises DTI    iff  t > 0.2 * DTI * (1 + t - k)
     where t = change in TP_w magnitude caused by the dot and k = its own kernel mass
     max_g k(d(x,g)).  (The short form "credit per unit mass > 0.2 DTI" in earlier notes is the
     small-t, small-k approximation of this rule.)
  5. Leakage canary, continuous form: AUC of the score (-distance to the SGMC-derived fault layer)
     against the full catalogue (positives) vs footprint background.  The binary-mask AUC written
     by run_holdout_cgrc.py is bounded near 0.5 and cannot exceed the leakage cut; this reports the
     continuous version beside it.

Outputs: evidence/registry_pair_0278_mechanism.json
Labels : CATALOGUE-PROXY (full truth, not holdout). Not a candidate score. Not ORGANIZER-CONFIRMED.
"""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import rasterio
from scipy.ndimage import distance_transform_edt
from scipy.stats import rankdata

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from gemsdoe54.grid import footprint  # noqa: E402
from gems_metric import dti_components, kernel_mass  # noqa: E402

A_PATH = ROOT / "registry/registry_rasters/dotted_d2_8_02708.tif"
B_PATH = ROOT / "registry/registry_rasters/dotted_b2_prune_02778.tif"
LABELS = ROOT / "data/grid/labels.tif"
SGMC = ROOT / "data/external/derived_sgmc_faults_100m_u8.tif"
OUT = ROOT / "evidence/registry_pair_0278_mechanism.json"
CELL_M = 100.0
R_M = 300.0
ALPHA, BETA = 0.2, 0.8
N_SAMPLE = 40
SEED = 20261009


def read(path: Path) -> np.ndarray:
    with rasterio.open(path) as src:
        return src.read(1).astype(np.float32)


def main() -> int:
    foot = footprint(LABELS)
    with rasterio.open(LABELS) as src:
        lab = src.read(1)
    truth = (lab == 1) & foot
    a_raw, b_raw = read(A_PATH), read(B_PATH)
    a_dots = (a_raw > 0) & foot
    b_dots = (b_raw > 0) & foot
    out: dict = {
        "label": "CATALOGUE-PROXY (full catalogue as truth; not a holdout; not an organizer score)",
        "generated_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "inputs": {"A": "registry/registry_rasters/dotted_d2_8_02708.tif",
                   "B": "registry/registry_rasters/dotted_b2_prune_02778.tif",
                   "labels": "data/grid/labels.tif", "sgmc": "data/external/derived_sgmc_faults_100m_u8.tif"},
        "counts": {"A_dots": int(a_dots.sum()), "B_dots": int(b_dots.sum()),
                   "catalogue_cells": int(truth.sum()), "footprint_cells": int(foot.sum()),
                   "A_values_unique": sorted(np.unique(a_raw[a_raw != 0]).tolist())[:5],
                   "B_values_unique": sorted(np.unique(b_raw[b_raw != 0]).tolist())[:5]},
    }

    # 1. subset test
    removed = a_dots & ~b_dots
    added = b_dots & ~a_dots
    out["subset"] = {"removed_by_pruning": int(removed.sum()), "added_by_pruning": int(added.sum()),
                     "B_is_subset_of_A": bool(added.sum() == 0)}

    # 2. distance of removed / kept dots to the catalogue
    d_cat_m = distance_transform_edt(~truth) * CELL_M
    dr = d_cat_m[removed]
    kept = b_dots
    dk = d_cat_m[kept]
    out["distance_to_catalogue_m"] = {
        "removed_min": float(dr.min()) if dr.size else None,
        "removed_median": float(np.median(dr)) if dr.size else None,
        "removed_max": float(dr.max()) if dr.size else None,
        "removed_within_200m_fraction": float(np.mean(dr <= 200.0)) if dr.size else None,
        "removed_within_300m_fraction": float(np.mean(dr <= 300.0)) if dr.size else None,
        "kept_B_within_200m_fraction": float(np.mean(dk <= 200.0)),
        "kept_B_within_300m_fraction": float(np.mean(dk <= 300.0)),
    }

    # 3. catalogue-proxy DTI and algebra identity
    rows = {}
    for name, dots in (("A", a_dots), ("B", b_dots)):
        pred = dots.astype(np.float64)
        comp = dti_components(pred, lab.astype(np.int16), valid=foot)
        n_mass = float(pred[foot].sum())
        g_count = int(truth.sum())
        m_mass = kernel_mass(pred, lab.astype(np.int16), valid=foot)
        closed = comp.tp_w / (0.2 * n_mass + 0.8 * g_count + 0.2 * (comp.tp_w - m_mass))
        rows[name] = {"N": n_mass, "G": g_count, "T": comp.tp_w, "FP_w": comp.fp_w, "FN_w": comp.fn_w,
                      "M": m_mass, "DTI_direct": comp.dti, "DTI_closed_form": closed,
                      "identity_abs_error": abs(comp.dti - closed)}
    out["catalogue_proxy_dti"] = rows

    # 4. marginal rule, brute force on sampled dots (deletions from A, additions to A)
    rng = np.random.default_rng(SEED)
    g_count = int(truth.sum())
    n0 = float(a_dots[foot].sum())
    base = dti_components(a_dots.astype(np.float64), lab.astype(np.int16), valid=foot)
    dti0, t0 = base.dti, base.tp_w
    m0 = kernel_mass(a_dots.astype(np.float64), lab.astype(np.int16), valid=foot)
    d_truth_cell = distance_transform_edt(~truth) * CELL_M
    del_idx = np.flatnonzero(a_dots.ravel())
    empty_idx = np.flatnonzero((~a_dots & foot).ravel())
    picks_del = rng.choice(del_idx, size=N_SAMPLE, replace=False)
    picks_add = rng.choice(empty_idx, size=N_SAMPLE, replace=False)
    table = []
    agree = 0
    max_identity_err = 0.0
    for op, idxs in (("delete", picks_del), ("add", picks_add)):
        sign = -1.0 if op == "delete" else 1.0
        for flat in idxs:
            y, x = np.unravel_index(int(flat), a_dots.shape)
            mod = a_dots.copy()
            mod[y, x] = not mod[y, x]
            comp1 = dti_components(mod.astype(np.float64), lab.astype(np.int16), valid=foot)
            k = max(1.0 - float(d_truth_cell[y, x]) / R_M, 0.0)  # the dot's own kernel mass
            t = (t0 - comp1.tp_w) if op == "delete" else (comp1.tp_w - t0)  # credit gained/lost
            predicted_up = (t < ALPHA * dti0 * (1.0 + t - k)) if op == "delete" else (
                t > ALPHA * dti0 * (1.0 + t - k))
            actual_up = comp1.dti > dti0
            agree += int(predicted_up == actual_up)
            # closed form with the same (t, k): N, M, T move by the dot's mass, kernel mass and credit
            t1 = t0 + sign * t if op == "add" else t0 - t
            n1, m1 = n0 + sign, m0 + sign * k
            closed = t1 / (0.2 * n1 + 0.8 * g_count + 0.2 * (t1 - m1))
            max_identity_err = max(max_identity_err, abs(closed - comp1.dti))
            table.append({"op": op, "row": int(y), "col": int(x), "kernel_k": round(k, 6),
                          "t_credit": round(float(t), 6), "DTI_before": round(dti0, 6),
                          "DTI_after_bruteforce": round(comp1.dti, 6),
                          "DTI_after_closed_form": round(closed, 6),
                          "predicted_raises_DTI": bool(predicted_up), "actual_raises_DTI": bool(actual_up),
                          "rule_agrees": bool(predicted_up == actual_up)})
    out["marginal_rule_check"] = {
        "n_samples": 2 * N_SAMPLE, "rule_agreement": agree,
        "max_abs_error_closed_form_vs_bruteforce": max_identity_err,
        "exact_rule": "delete raises DTI iff t < 0.2*DTI*(1+t-k); add raises DTI iff t > 0.2*DTI*(1+t-k)",
        "rows": table,
    }

    # 5. continuous leakage canary: SGMC distance score vs full catalogue (positives) and background
    with rasterio.open(SGMC) as src:
        sg = src.read(1)
    sg_mask = (sg > 0) & foot
    d_sg = distance_transform_edt(~sg_mask)
    score = -d_sg[foot].ravel()
    y_pos = truth[foot].ravel()
    ranks = rankdata(score)
    n_pos = int(y_pos.sum())
    n_neg = int((~y_pos).sum())
    auc_cont = float((ranks[y_pos].sum() - n_pos * (n_pos + 1) / 2) / (n_pos * n_neg))
    binary_score = sg_mask[foot].ravel().astype(np.float64)
    p1 = float(sg_mask[truth].mean())
    p0 = float(sg_mask[foot & ~truth].mean())
    out["leakage_canary"] = {
        "auc_continuous_neg_distance_to_sgmc_vs_full_catalogue": round(auc_cont, 6),
        "auc_binary_mask_as_in_run_holdout_cgrc": round(0.5 * (p1 + (1.0 - p0)), 6),
        "p_sgmc_given_catalogue": round(p1, 6),
        "p_sgmc_given_background": round(p0, 6),
        "binary_score_check": float(binary_score.mean()),
        "cut": 0.90,
        "note": ("Full-catalogue canary, not the withheld-segment canary. Binary AUC is the balanced accuracy of "
                 "one threshold and is bounded near 0.5 for a 4x enrichment; the continuous AUC is the test "
                 "that can fire. Above 0.90 = leakage until proven otherwise."),
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(out, indent=2) + "\n", encoding="utf-8")
    summary = {k: out[k] for k in ("subset", "distance_to_catalogue_m", "leakage_canary")}
    summary["catalogue_proxy_dti"] = {k: {kk: round(vv, 6) for kk, vv in v.items()} for k, v in rows.items()}
    summary["marginal_rule_agreement"] = f"{agree}/{2 * N_SAMPLE}"
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

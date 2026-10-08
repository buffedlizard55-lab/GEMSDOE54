#!/usr/bin/env python3
"""Whole-segment hide-and-recover holdout for H54-C (CGRC), protocol-compliant.

Design (parallel-run protocol, requirements 2/4)
------------------------------------------------
* Withhold WHOLE catalogue fault segments (connected components, >= 3 cells)
  in 4 spatial quadrant folds, each expanded by a 300 m (3 px = metric kernel
  width) buffer so nothing inside the kernel of a withheld segment is visible.
* Every catalogue-based feature is derived ONLY from the visible catalogue
  (pixel-exact mask of the hold zones). The USGS SGMC layer is an independent,
  non-catalogue product, available in both arms; its circularity with the
  catalogue-truth holdout is measured by the leakage canary and reported
  (holdout truth = visible catalogue, so it cannot reward a genuinely new
  off-catalogue fault — same limitation GEMSDOE32 labels IR-32-PROXY-01).
* Score the POOLED distance-weighted Tversky (alpha 0.2, beta 0.8, 300 m
  triangular kernel) with the organizer's equations (scripts/gems_metric.py):
  one prediction (the union of the four folds' emissions) scored against the
  full withheld truth (the union of all withheld segments).
* Arms: A = pure catalogue geometry (no SGMC anywhere); B = CGRC with the SGMC
  corroboration weight. Same candidate mask and spacing; only placement
  priority differs, and mass is matched per fold so no contrast is won by
  emitting more pixels.
* Inference: cluster (whole-segment) bootstrap, 2000 replicates, paired across
  arms on the same segment draws.  Per-replicate DTI is computed exactly from
  precomputed per-segment credit sums: T and FN are additive over drawn
  segments; M = sum over dots of the max kernel over drawn segments (the
  organizer algebra, no full-grid EDT per replicate).

Output: evidence/cgrc_holdout_receipt.json, labelled HOLDOUT-DTI.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np
import rasterio
from scipy.ndimage import distance_transform_edt, label

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from gemsdoe54.cgrc import build  # noqa: E402
from gemsdoe54.emission import emit_spaced_dots, trim_to_budget  # noqa: E402
from gemsdoe54.grid import binary_mask, footprint  # noqa: E402
from gemsdoe54.holdout import pooled_metric  # noqa: E402
from gemsdoe54.power import (  # noqa: E402
    minimum_detectable_cohen_d,
    normal_approx_mde_from_se,
)

EVALUATOR_VERSION = "gemsdoe54.cgrc-holdout.v2"
BUFFER_PX = 3
ALPHA_M, BETA_M = 0.2, 0.8
BOOTSTRAP = 2000
SEED = 54
MIN_PX = 3


def quadrant_folds(centroids: np.ndarray) -> np.ndarray:
    r, c = centroids[:, 0], centroids[:, 1]
    return ((r >= np.median(r)).astype(np.int64) * 2
            + (c >= np.median(c)).astype(np.int64))


def dot_segment_kernels(shape: tuple[int, int], dots: np.ndarray,
                        cell2seg: np.ndarray) -> list[tuple[int, int, list]]:
    """For every dot, the held segments within 300 m and each segment's max kernel.

    Returns a list of (row, col, [(seg_idx, max_kernel), ...]) for dots with at
    least one nearby held segment.  Window scan over the (sparse) hold cells:
    the 300 m kernel spans at most a 7x7 window on the 100 m grid.
    """
    h, w = shape
    out: list[tuple[int, int, list]] = []
    dy, dx = np.nonzero(dots)
    c2s = cell2seg.reshape(h, w)
    for y, x in zip(dy, dx):
        y0, y1 = max(0, y - 3), min(h, y + 4)
        x0, x1 = max(0, x - 3), min(w, x + 4)
        win = c2s[y0:y1, x0:x1]
        yy, xx = np.nonzero(win >= 0)
        if yy.size == 0:
            continue
        dist = np.hypot(yy + y0 - y, xx + x0 - x) * 100.0
        k = 1.0 - dist / 300.0
        keep = k > 0
        if not keep.any():
            continue
        segs = win[yy[keep], xx[keep]]
        kk = k[keep]
        m = np.zeros(int(segs.max()) + 1, dtype=np.float64)
        np.maximum.at(m, segs, kk)
        out.append((int(y), int(x),
                    [(int(s), float(m[s])) for s in np.unique(segs) if m[s] > 0]))
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--max-gap-m", type=float, default=1500.0)
    ap.add_argument("--max-ext-m", type=float, default=1500.0)
    ap.add_argument("--exclude-cat-m", type=float, default=200.0)
    ap.add_argument("--out", default=None)
    args = ap.parse_args()
    t0 = time.time()
    foot = footprint(ROOT / "data/grid/labels.tif")
    with rasterio.open(ROOT / "data/grid/labels.tif") as src:
        lab = src.read(1)
    cat = (lab == 1) & foot
    sgmc = binary_mask(ROOT / "data/external/derived_sgmc_faults_100m_u8.tif") & foot

    # ---------------- segment inventory ----------------
    seg_lab, ncomp = label(cat, structure=np.ones((3, 3), dtype=int))
    cnt = np.bincount(seg_lab.ravel(), minlength=ncomp + 1)
    seg_ids = [a for a in range(1, ncomp + 1) if cnt[a] >= MIN_PX]
    S = len(seg_ids)
    idx_map = np.full(ncomp + 1, -1, dtype=np.int32)
    idx_map[seg_ids] = np.arange(S)
    cell2seg = idx_map[seg_lab.ravel()]  # -1 outside kept segments

    ys, xs = np.nonzero(cat)
    lids = seg_lab[ys, xs]
    cent = np.zeros((S, 2), dtype=np.float64)
    for i, a in enumerate(seg_ids):
        sel = lids == a
        cent[i] = (ys[sel].mean(), xs[sel].mean())
    fold_of_seg = quadrant_folds(cent)

    # ---------------- folds: zones, visible catalogues, matched dots --------
    per_fold: list[dict] = []
    for f in range(4):
        held_ids = [i for i in range(S) if fold_of_seg[i] == f]
        held = np.isin(seg_lab, [seg_ids[i] for i in held_ids]) & cat
        zone = distance_transform_edt(~held) <= float(BUFFER_PX)
        visible = cat & ~zone
        assert not bool((visible & zone).any())
        res_a = build(foot.shape, visible, np.zeros_like(sgmc), foot, with_sgmc=False,
                    exclude_cat_m=args.exclude_cat_m, max_gap_m=args.max_gap_m,
                    max_ext_m=args.max_ext_m)
        res_b = build(foot.shape, visible, sgmc, foot, with_sgmc=True,
                exclude_cat_m=args.exclude_cat_m, max_gap_m=args.max_gap_m,
                max_ext_m=args.max_ext_m)
        assert np.array_equal(res_a["candidates"], res_b["candidates"]), "candidate masks differ"
        dots_a = emit_spaced_dots(res_a["candidates"], priority=res_a["priority"], spacing_px=3.0)
        dots_b = emit_spaced_dots(res_b["candidates"], priority=res_b["priority"], spacing_px=3.0)
        budget = min(int(dots_a.sum()), int(dots_b.sum()))  # match mass per fold
        dots_a = trim_to_budget(dots_a, res_a["priority"], budget)
        dots_b = trim_to_budget(dots_b, res_b["priority"], budget)
        assert int(dots_a.sum()) == int(dots_b.sum()) == budget
        per_fold.append({
            "fold": f, "n_held_segments": len(held_ids), "held_ids": held_ids,
            "held_cells": int(held.sum()), "visible_cells": int(visible.sum()),
            "n_dots": int(dots_a.sum()),
            "dots": {"A": dots_a, "B": dots_b}, "truth": held,
            "prio": {"A": res_a["priority"], "B": res_b["priority"]},
        })
        print(f"fold {f}: held_segs={len(held_ids)} held_cells={int(held.sum()):,} "
              f"matched_dots={int(dots_a.sum()):,} t={time.time()-t0:.0f}s", flush=True)

    # ---------------- pooled prediction and pooled truth ----------------
    all_truth = np.zeros(cat.shape, dtype=bool)
    dots_all = {"A": np.zeros(cat.shape, dtype=bool), "B": np.zeros(cat.shape, dtype=bool)}
    prio_all = {"A": np.zeros(cat.shape, dtype=np.float64), "B": np.zeros(cat.shape, dtype=np.float64)}
    for fd in per_fold:
        all_truth |= fd["truth"]
        dots_all["A"] |= fd["dots"]["A"]
        dots_all["B"] |= fd["dots"]["B"]
        np.maximum(prio_all["A"], fd["prio"]["A"], out=prio_all["A"])
        np.maximum(prio_all["B"], fd["prio"]["B"], out=prio_all["B"])
    # cross-fold union overlaps can leave the arms at slightly different mass;
    # match on the pooled prediction so no contrast is won by emitting more pixels
    pooled_budget = min(int(dots_all["A"].sum()), int(dots_all["B"].sum()))
    dots_all["A"] = trim_to_budget(dots_all["A"], prio_all["A"], pooled_budget)
    dots_all["B"] = trim_to_budget(dots_all["B"], prio_all["B"], pooled_budget)
    n_pos = int(all_truth.sum())
    N = {"A": int(dots_all["A"].sum()), "B": int(dots_all["B"].sum())}
    assert N["A"] == N["B"] == pooled_budget, "pooled mass mismatch"

    # ---------------- headline exact pooled DTI ----------------
    dti_A, tp_A, fp_A, fn_A = pooled_metric(all_truth, dots_all["A"])
    dti_B, tp_B, fp_B, fn_B = pooled_metric(all_truth, dots_all["B"])

    # ---------------- cluster bootstrap precomputation ----------------
    # Per arm: per-segment credit sums (T_s, fn_s) using the POOLED dot union,
    # and per-dot segment kernels for M.
    arms: dict[str, dict] = {}
    for a in "AB":
        dots = dots_all[a]
        d_dot = distance_transform_edt(~dots, sampling=(100.0, 100.0))
        credit = np.clip(1.0 - d_dot / 300.0, 0.0, None)
        tcells = np.flatnonzero(all_truth.ravel())
        segs_here = cell2seg[tcells]
        tc = credit.ravel()[tcells]
        T_s = np.bincount(segs_here, weights=tc, minlength=S)
        fn_s = (np.bincount(segs_here, minlength=S) - T_s)  # |s| - T_s
        dot_segs = dot_segment_kernels(foot.shape, dots, cell2seg)
        arms[a] = {"T_s": T_s, "fn_s": fn_s, "N": N[a], "dot_segs": dot_segs}
        print(f"arm {a}: pooled dots={N[a]:,} dot-seg pairs with k>0: {len(dot_segs)} "
              f"t={time.time()-t0:.0f}s", flush=True)

    # ---- SELF-CHECK: bootstrap algebra vs the exact organizer metric ----
    # Drawing every segment exactly once must reproduce the headline pooled DTI.
    for a in "AB":
        T_full = arms[a]["T_s"].sum()
        FN_full = arms[a]["fn_s"].sum()
        M_full = 0.0
        for y, x, segk in arms[a]["dot_segs"]:
            M_full += max(k for _, k in segk)
        D_full = T_full + ALPHA_M * (arms[a]["N"] - M_full) + BETA_M * FN_full
        dti_full = T_full / D_full if D_full > 0 else 0.0
        headline = dti_A if a == "A" else dti_B
        assert abs(dti_full - headline) < 1e-6, (
            f"bootstrap algebra mismatch arm {a}: full-draw {dti_full:.6f} vs "
            f"headline pooled {headline:.6f}")
        print(f"self-check arm {a}: full-draw DTI {dti_full:.6f} == headline "
              f"{headline:.6f}  OK", flush=True)

    rng = np.random.default_rng(SEED)
    draws = rng.integers(0, S, size=(BOOTSTRAP, S))
    cnts = np.zeros((BOOTSTRAP, S), dtype=np.float64)
    for b in range(BOOTSTRAP):
        np.add.at(cnts[b], draws[b], 1.0)
    del draws

    dti_b = {}
    for a in "AB":
        T_b = cnts @ arms[a]["T_s"]
        FN_b = cnts @ arms[a]["fn_s"]
        M_b = np.zeros(BOOTSTRAP)
        for y, x, segk in arms[a]["dot_segs"]:
            cols = np.array([s for s, _ in segk], dtype=np.int64)
            vals = np.array([k for _, k in segk], dtype=np.float64)
            cc = cnts[:, cols]
            M_b += np.where(cc > 0, vals[None, :], 0.0).max(axis=1)
        D = T_b + ALPHA_M * (arms[a]["N"] - M_b) + BETA_M * FN_b
        dti_b[a] = np.where(D > 0, T_b / np.where(D > 0, D, 1.0), 0.0)
        print(f"arm {a} bootstrap done t={time.time()-t0:.0f}s", flush=True)

    diff = dti_b["A"] - dti_b["B"]
    se_diff = float(diff.std(ddof=1))
    mean_diff = float(diff.mean())
    ci_diff = [float(np.quantile(diff, 0.025)), float(np.quantile(diff, 0.975))]
    ci_A = [float(np.quantile(dti_b["A"], 0.025)), float(np.quantile(dti_b["A"], 0.975))]
    ci_B = [float(np.quantile(dti_b["B"], 0.025)), float(np.quantile(dti_b["B"], 0.975))]
    raw_mde = normal_approx_mde_from_se(se_diff)
    d_cohen_units = minimum_detectable_cohen_d(S)
    d_cohen_pixels = minimum_detectable_cohen_d(n_pos)

    # ---------------- leakage canary (single-feature AUC) ----------------
    p1 = float(sgmc[all_truth].mean())
    neg = foot & ~all_truth
    p0 = float(sgmc[neg].mean())
    auc_sgmc = 0.5 * (p1 + (1.0 - p0))
    vis_all = cat & ~all_truth  # background control feature (should be ~0.5)
    p1v = float(vis_all[all_truth].mean())
    p0v = float(vis_all[neg].mean())
    auc_visible = 0.5 * (p1v + (1.0 - p0v))

    receipt = {
        "schema": "gemsdoe54.holdout-receipt.v1",
        "evaluator": {
            "version": EVALUATOR_VERSION,
            "metric": {"name": "DTI", "alpha": ALPHA_M, "beta": BETA_M,
                       "kernel": "triangular", "kernel_radius_m": 300.0,
                       "aggregation": "pooled"},
        "aggregation_note": "union of the four folds' emissions scored against the union of all withheld segments",
        },
        "design": {
            "whole_fault_segments_withheld": True,
            "catalogue_features_from_visible_faults_only": True,
            "visible_fault_mask": "pixel_exact",
            "buffer_m": 300.0,
            "bootstrap_unit": "whole_fault_segment",
            "withheld_positive_count": n_pos,
            "independent_unit_count": S,
            "folds": 4,
            "fold_assignment": "spatial quadrants at segment-centroid medians",
            "mass_matched_across_arms": True,
            "catalogue_exclusion_m": args.exclude_cat_m,
            "max_gap_m": args.max_gap_m,
            "max_ext_m": args.max_ext_m,
            "truth_label": ("HOLDOUT-DTI (catalogue-truth proxy): truth = withheld catalogue "
                            "segments; cannot reward genuinely new off-catalogue faults"),
        },
        "arms": {
            "A": {"description": "CGRC, pure catalogue geometry, no SGMC",
                  "n_dots": N["A"],
                  "pooled_dti": round(dti_A, 6),
                  "tp_w": round(tp_A, 2), "fp_w": round(fp_A, 2), "fn_w": round(fn_A, 2),
                  "ci95_cluster_bootstrap": [round(v, 6) for v in ci_A]},
            "B": {"description": "CGRC with SGMC corroboration weight",
                  "n_dots": N["B"],
                  "pooled_dti": round(dti_B, 6),
                  "tp_w": round(tp_B, 2), "fp_w": round(fp_B, 2), "fn_w": round(fn_B, 2),
                  "ci95_cluster_bootstrap": [round(v, 6) for v in ci_B]},
        },
        "comparison": {
            "observed_pooled_delta_dti": round(mean_diff, 6),
            "pooled_delta_ci95_cluster_bootstrap": [round(v, 6) for v in ci_diff],
            "pooled_delta_bootstrap": [round(float(v), 6) for v in diff],
            "bootstrap_replicates": BOOTSTRAP,
            "bootstrap_seed": SEED,
            "paired_across_arms": True,
        },
        "power": {
            "framework": "Cohen (1988); two-sided alpha=0.05, power=0.80, z_sum=2.801585",
            "independent_unit": "whole withheld fault segments",
            "independent_unit_count": S,
            "cohen_d_mdd_unit_level": round(float(d_cohen_units), 6),
            "pooled_dti_raw_scale_mdd_from_bootstrap_se": round(float(raw_mde), 6),
            "bootstrap_se_of_paired_delta": round(se_diff, 8),
            "pixel_iid_cohen_d_floor_NOT_VALID": round(float(d_cohen_pixels), 6),
            "pixel_iid_warning": ("pixel count is an optimistic independence bound; spatially "
                                  "correlated positives do not supply that many independent "
                                  "observations; not valid for decisions"),
            "question_0.0028": {
                "gap": 0.0028,
                "above_raw_scale_mdd": bool(0.0028 > raw_mde),
                "interpretation": (
                    "compare the gap to the bootstrap raw-scale MDE of a same-method-family "
                    "paired contrast (the kind of comparison 0.2778 vs 0.2750 would be)"),
            },
        },
        "leakage_canary": {
            "auc_cut": 0.90,
            "sgmc_alone_auc_vs_withheld_catalogue": round(auc_sgmc, 6),
            "p_sgmc_given_withheld_truth": round(p1, 6),
            "p_sgmc_given_background": round(p0, 6),
            "visible_catalogue_alone_auc_control": round(auc_visible, 6),
            "flags": (["LEAKAGE: SGMC alone AUC > 0.90 vs withheld catalogue (expected circularity: "
                       "SGMC independently maps the same structures the catalogue holds)"]
                      if auc_sgmc > 0.90 else []),
            "note": ("Catalogue-truth holdout: any layer that independently maps catalogue faults "
                     "will score high. This measures circularity, not hidden-label skill."),
        },
        "folds_detail": [
            {"fold": fd["fold"], "held_segments": fd["n_held_segments"],
             "held_cells": fd["held_cells"], "visible_cells": fd["visible_cells"],
             "n_dots": fd["n_dots"]}
            for fd in per_fold
        ],
        "inputs": {
            "labels_sha256": "7ba308ccdc4418b31a178f4f1ef21aaa6e152e4028f2f6f64b01f7eb25ae4093",
            "sgmc_sha256": "26d142c4c93282cd94f6950ab96f22aeff59fbbea523d43d662e76fa1b161b5c",
        },
        "timing_s": round(time.time() - t0, 1),
    }
    out = Path(args.out) if args.out else ROOT / "evidence/cgrc_holdout_receipt.json"
    out.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    print(f"\nHOLDOUT-DTI A={dti_A:.4f} B={dti_B:.4f} delta={mean_diff:+.4f} "
          f"SE={se_diff:.5f} MDE(raw)={raw_mde:.5f} 0.0028_above={0.0028 > raw_mde}")
    print(f"wrote {out} in {time.time()-t0:.0f}s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

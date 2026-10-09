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

Output: evidence/cgrc_holdout_receipt.json, labelled HOLDOUT-DTI (pass --out explicitly to
avoid overwriting the committed receipt).

Optional arms (``--with-h54a-arm``, added 2026-10-09)
------------------------------------------------------
C  = the H54-A rule (scripts/build_submission.py) rebuilt PER FOLD from the VISIBLE catalogue only:
     SGMC cells > 300 m from the visible catalogue -> linearity gate (min_px 3, extent 5 px,
     elongation 6) -> priority (component size, distance tie-break) -> 2 px spacing.
     C is trimmed to the arms' per-fold budget (mass-matched; unchanged where it has fewer dots).
CN = the same rule at its native mass (no trimming): the as-deployed comparison.

Optional arm X (``--with-xgrad-arm``, added 2026-10-09): the top-ranked untested hypothesis, a
magnetic-gravity cross-gradient coincidence score computed from the OWNER-MIRRORED official feature
stack (band 2 = reduced-to-pole magnetic, band 13 = isostatic gravity anomaly; band names verified
against the official reference notebook). score = |grad M| * |grad G| * |cos(angle)| (each magnitude
normalised by its footprint 99th percentile; Gaussian sigma 1 cell). Catalogue-independent; per fold
only the 200 m visible-catalogue exclusion and the score are used, 3 px spacing, mass-matched budget.
Both are scored with the identical folds, pooled union, bootstrap seed and metric as A and B.
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
from scipy.stats import rankdata

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

sys.path.insert(0, str(ROOT / "scripts"))
from build_submission import linearity_gate  # noqa: E402  (H54-A rule, optional arm C)
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


def h54a_arm(visible: np.ndarray, sgmc: np.ndarray, foot: np.ndarray):
    """H54-A rule (scripts/build_submission.py) computed on one fold's VISIBLE catalogue."""
    d_vis = distance_transform_edt(~visible, sampling=(100.0, 100.0))
    excl = sgmc & foot & (d_vis > 300.0)
    gated = linearity_gate(excl, min_px=3, min_px_extent=5, min_elongation=6.0)
    lab, ncomp = label(gated, structure=np.ones((3, 3), dtype=int))
    size = np.bincount(lab.ravel(), minlength=ncomp + 1)
    prio = size[lab].astype(np.float64) + 1e-3 * d_vis
    prio[~gated] = -np.inf
    dots = emit_spaced_dots(gated, priority=prio, spacing_px=2.0)
    return dots, prio


def xgrad_score(features_path: Path, foot: np.ndarray) -> np.ndarray:
    """Magnetic-gravity cross-gradient coincidence score (catalogue-independent)."""
    from scipy.ndimage import gaussian_filter
    with rasterio.open(features_path) as src:
        M = src.read(2).astype(np.float64)   # reduced-to-pole magnetic anomaly
        G = src.read(13).astype(np.float64)  # isostatic gravity anomaly
    bad = (~np.isfinite(M)) | (M < -1e38) | (~np.isfinite(G)) | (G < -1e38)
    M[bad] = 0.0
    G[bad] = 0.0
    M = gaussian_filter(M, 1.0)
    G = gaussian_filter(G, 1.0)
    My, Mx = np.gradient(M, 100.0)
    Gy, Gx = np.gradient(G, 100.0)
    mM = np.hypot(Mx, My)
    mG = np.hypot(Gx, Gy)
    cos = (Mx * Gx + My * Gy) / np.maximum(mM * mG, 1e-12)
    nM = mM / max(float(np.percentile(mM[foot], 99)), 1e-12)
    nG = mG / max(float(np.percentile(mG[foot], 99)), 1e-12)
    score = np.clip(nM, 0.0, None) * np.clip(nG, 0.0, None) * np.abs(cos)
    score[~foot] = 0.0
    return score


def xgrad_arm(visible: np.ndarray, score: np.ndarray, foot: np.ndarray, thr: float):
    """Cross-gradient arm on one fold: top-8 % score cells, >200 m from the visible catalogue, 3 px."""
    d_vis = distance_transform_edt(~visible, sampling=(100.0, 100.0))
    cand = foot & (d_vis > 200.0) & (score >= thr)
    prio = np.where(cand, score, -np.inf)
    dots = emit_spaced_dots(cand, priority=prio, spacing_px=3.0)
    return dots, prio


def auc_rank(pos: np.ndarray, neg: np.ndarray) -> float:
    from scipy.stats import rankdata
    r = rankdata(np.concatenate([pos, neg]))
    n1, n0 = pos.size, neg.size
    return float((r[:n1].sum() - n1 * (n1 + 1) / 2.0) / (n1 * n0))


def main() -> int:
    ap = argparse.ArgumentParser()
    # defaults = the committed receipt's configuration (evidence/cgrc_holdout_receipt.json:
    # max_gap_m 2500, max_ext_m 2500, catalogue exclusion 200 m). The earlier 1500 m default did
    # NOT reproduce that receipt (see IR-54-074 in audit/irregularities.md).
    ap.add_argument("--max-gap-m", type=float, default=2500.0)
    ap.add_argument("--max-ext-m", type=float, default=2500.0)
    ap.add_argument("--exclude-cat-m", type=float, default=200.0)
    ap.add_argument("--with-h54a-arm", action="store_true",
                    help="add arms C (H54-A rule, mass-matched) and CN (native mass) on the same folds")
    ap.add_argument("--with-xgrad-arm", action="store_true",
                    help="add arm X (magnetic-gravity cross-gradient, owner-mirrored official features)")
    ap.add_argument("--features", default="/home/user/work/feature_stack/training_features.tif",
                    help="assembled official feature stack (kept outside the repo; sha256 checked)")
    ap.add_argument("--out", default=None,
                    help="output receipt path (default: ignored work/ directory; never the committed receipt)")
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

    # ---------------- optional cross-gradient score (once; catalogue-independent) ----------
    xscore = xthr = None
    if args.with_xgrad_arm:
        import hashlib
        fpath = Path(args.features)
        h = hashlib.sha256()
        with open(fpath, "rb") as fh:
            for chunk in iter(lambda: fh.read(1 << 24), b""):
                h.update(chunk)
        if h.hexdigest() != "4371c82e3b8339b807bdffcf4ef59a225520fe2988d521be208ae33743123bc5":
            raise SystemExit(f"feature stack sha256 mismatch: {h.hexdigest()}")
        xscore = xgrad_score(fpath, foot)
        xthr = float(np.quantile(xscore[foot], 0.92))
        print(f"xgrad score: threshold(top 8% of footprint)={xthr:.4f} t={time.time()-t0:.0f}s", flush=True)

    # ---------------- folds: zones, visible catalogues, matched dots --------
    # Pooled prediction/truth are accumulated inside the fold loop (OR / elementwise max are
    # order-independent, so this equals a post-loop pass). Holding per-fold full-grid arrays for
    # every arm exhausted memory on the 4 GB sandbox (run killed at bootstrap, 2026-10-09).
    arm_names = ["A", "B"] + (["C", "CN"] if args.with_h54a_arm else []) + (["X"] if args.with_xgrad_arm else [])
    all_truth = np.zeros(cat.shape, dtype=bool)
    dots_all = {a: np.zeros(cat.shape, dtype=bool) for a in arm_names}
    prio_all = {a: np.zeros(cat.shape, dtype=np.float64) for a in arm_names}
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
        fd_dots = {"A": dots_a, "B": dots_b}
        fd_prio = {"A": res_a["priority"], "B": res_b["priority"]}
        fd_extra = {}
        if args.with_h54a_arm:
            dots_cn, prio_c = h54a_arm(visible, sgmc, foot)
            dots_c = trim_to_budget(dots_cn, prio_c, budget)  # no-op where C has fewer dots
            fd_dots["C"], fd_dots["CN"] = dots_c, dots_cn
            fd_prio["C"] = fd_prio["CN"] = prio_c
            fd_extra = {"n_dots_C_native": int(dots_cn.sum()), "n_dots_C_matched": int(dots_c.sum())}
        if args.with_xgrad_arm:
            dots_xf, prio_x = xgrad_arm(visible, xscore, foot, xthr)
            dots_x = trim_to_budget(dots_xf, prio_x, budget)
            fd_dots["X"] = dots_x
            fd_prio["X"] = prio_x
            fd_extra.update({"n_dots_X_native": int(dots_xf.sum()), "n_dots_X_matched": int(dots_x.sum())})
        all_truth |= held
        for a in arm_names:
            dots_all[a] |= fd_dots[a]
            np.maximum(prio_all[a], fd_prio[a], out=prio_all[a])
        per_fold.append({
            "fold": f, "n_held_segments": len(held_ids), "held_ids": held_ids,
            "held_cells": int(held.sum()), "visible_cells": int(visible.sum()),
            "n_dots": int(dots_a.sum()), **fd_extra,
        })
        del res_a, res_b, fd_prio
        print(f"fold {f}: held_segs={len(held_ids)} held_cells={int(held.sum()):,} "
              f"matched_dots={int(dots_a.sum()):,} t={time.time()-t0:.0f}s", flush=True)

    # ---------------- pooled prediction and pooled truth ----------------
    # cross-fold union overlaps can leave the arms at slightly different mass;
    # match on the pooled prediction so no contrast is won by emitting more pixels
    pooled_budget = min(int(dots_all["A"].sum()), int(dots_all["B"].sum()))
    dots_all["A"] = trim_to_budget(dots_all["A"], prio_all["A"], pooled_budget)
    dots_all["B"] = trim_to_budget(dots_all["B"], prio_all["B"], pooled_budget)
    if "C" in arm_names:
        # C is trimmed to the pooled budget when it has at least that many dots; CN stays native
        dots_all["C"] = trim_to_budget(dots_all["C"], prio_all["C"], pooled_budget)
    if "X" in arm_names:
        dots_all["X"] = trim_to_budget(dots_all["X"], prio_all["X"], pooled_budget)
    n_pos = int(all_truth.sum())
    N = {a: int(dots_all[a].sum()) for a in arm_names}
    assert N["A"] == N["B"] == pooled_budget, "pooled mass mismatch"

    # ---------------- headline exact pooled DTI ----------------
    headline = {a: pooled_metric(all_truth, dots_all[a]) for a in arm_names}
    dti_A, tp_A, fp_A, fn_A = headline["A"]
    dti_B, tp_B, fp_B, fn_B = headline["B"]

    # ---------------- cluster bootstrap precomputation ----------------
    # Per arm: per-segment credit sums (T_s, fn_s) using the POOLED dot union,
    # and per-dot segment kernels for M.
    arms: dict[str, dict] = {}
    for a in arm_names:
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
    for a in arm_names:
        T_full = arms[a]["T_s"].sum()
        FN_full = arms[a]["fn_s"].sum()
        M_full = 0.0
        for y, x, segk in arms[a]["dot_segs"]:
            M_full += max(k for _, k in segk)
        D_full = T_full + ALPHA_M * (arms[a]["N"] - M_full) + BETA_M * FN_full
        dti_full = T_full / D_full if D_full > 0 else 0.0
        head = headline[a][0]
        assert abs(dti_full - head) < 1e-6, (
            f"bootstrap algebra mismatch arm {a}: full-draw {dti_full:.6f} vs "
            f"headline pooled {head:.6f}")
        print(f"self-check arm {a}: full-draw DTI {dti_full:.6f} == headline "
              f"{head:.6f}  OK", flush=True)

    rng = np.random.default_rng(SEED)
    draws = rng.integers(0, S, size=(BOOTSTRAP, S))
    cnts = np.zeros((BOOTSTRAP, S), dtype=np.float64)
    for b in range(BOOTSTRAP):
        np.add.at(cnts[b], draws[b], 1.0)
    del draws

    dti_b = {}
    for a in arm_names:
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
    # extra paired contrasts (only with --with-h54a-arm); x - y, bootstrap on the same segment draws
    pairs = {}
    if args.with_h54a_arm or args.with_xgrad_arm:
        pair_list = [("B", "C"), ("B", "CN"), ("A", "C")]
        if args.with_xgrad_arm:
            pair_list += [("X", "C"), ("X", "B"), ("X", "A")]
        pair_list = [(x, y) for x, y in pair_list if x in arm_names and y in arm_names]
        for x, y in pair_list:
            dd = dti_b[x] - dti_b[y]
            pairs[f"{x}_minus_{y}"] = {
                "point_delta_dti": round(float(headline[x][0] - headline[y][0]), 6),
                "bootstrap_mean_delta_dti": round(float(dd.mean()), 6),
                "ci95_cluster_bootstrap": [round(float(np.quantile(dd, 0.025)), 6),
                                           round(float(np.quantile(dd, 0.975)), 6)],
                "bootstrap_se": round(float(dd.std(ddof=1)), 8),
                "raw_scale_mde_from_bootstrap_se": round(float(normal_approx_mde_from_se(
                    float(dd.std(ddof=1)))), 6),
                "ci_excludes_zero": bool(np.quantile(dd, 0.025) > 0 or np.quantile(dd, 0.975) < 0),
            }

    # ---------------- leakage canary (single-feature AUC) ----------------
    p1 = float(sgmc[all_truth].mean())
    neg = foot & ~all_truth
    p0 = float(sgmc[neg].mean())
    auc_sgmc = 0.5 * (p1 + (1.0 - p0))
    # Continuous form of the same canary (added 2026-10-09). The binary form above is the balanced accuracy
    # of ONE threshold on SGMC cells and cannot exceed ~0.5 + enrichment/2, so it cannot reach the 0.90 cut.
    # The continuous score (-distance to SGMC) is the test that can fire.
    _d_sgmc = distance_transform_edt(~sgmc)
    _pos = -_d_sgmc[all_truth]
    _neg = -_d_sgmc[neg]
    _r = rankdata(np.concatenate([_pos, _neg]))
    _npos, _nneg = _pos.size, _neg.size
    auc_sgmc_cont = float((_r[:_npos].sum() - _npos * (_npos + 1) / 2.0) / (_npos * _nneg))
    vis_all = cat & ~all_truth  # background control feature (should be ~0.5)
    p1v = float(vis_all[all_truth].mean())
    p0v = float(vis_all[neg].mean())
    auc_visible = 0.5 * (p1v + (1.0 - p0v))

    xgrad_auc = float("nan")
    if args.with_xgrad_arm:
        rng_c = np.random.default_rng(SEED)
        neg_cells = np.flatnonzero((foot & ~all_truth).ravel())
        neg_s = rng_c.choice(neg_cells, size=min(200_000, neg_cells.size), replace=False)
        pos_s = np.flatnonzero(all_truth.ravel())
        xgrad_auc = auc_rank(xscore.ravel()[pos_s], xscore.ravel()[neg_s])
        print(f"xgrad single-feature AUC vs withheld truth: {xgrad_auc:.4f}", flush=True)

    receipt = {
        "schema": "gemsdoe54.holdout-receipt.v1",
        "cli_args": {k: (v if not isinstance(v, Path) else str(v)) for k, v in vars(args).items()},
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
            **({"X": {"description": "magnetic-gravity cross-gradient score (RTP x gravity, parallel-gradient coupling), top 8% footprint, 200 m visible-catalogue exclusion, 3 px spacing, mass-matched",
                      "n_dots": N["X"], "pooled_dti": round(headline["X"][0], 6),
                      "tp_w": round(headline["X"][1], 2), "fp_w": round(headline["X"][2], 2),
                      "fn_w": round(headline["X"][3], 2),
                      "ci95_cluster_bootstrap": [round(float(np.quantile(dti_b["X"], 0.025)), 6),
                                                 round(float(np.quantile(dti_b["X"], 0.975)), 6)]}}
               if args.with_xgrad_arm else {}),
            **({"C": {"description": "H54-A rule rebuilt per fold on the visible catalogue, mass-matched to the CGRC arms' budget",
                      "n_dots": N["C"], "pooled_dti": round(headline["C"][0], 6),
                      "tp_w": round(headline["C"][1], 2), "fp_w": round(headline["C"][2], 2),
                      "fn_w": round(headline["C"][3], 2),
                      "ci95_cluster_bootstrap": [round(float(np.quantile(dti_b["C"], 0.025)), 6),
                                                 round(float(np.quantile(dti_b["C"], 0.975)), 6)]},
                "CN": {"description": "H54-A rule rebuilt per fold on the visible catalogue, native mass (as deployed)",
                       "n_dots": N["CN"], "pooled_dti": round(headline["CN"][0], 6),
                       "tp_w": round(headline["CN"][1], 2), "fp_w": round(headline["CN"][2], 2),
                       "fn_w": round(headline["CN"][3], 2),
                       "ci95_cluster_bootstrap": [round(float(np.quantile(dti_b["CN"], 0.025)), 6),
                                                  round(float(np.quantile(dti_b["CN"], 0.975)), 6)]}}
               if args.with_h54a_arm else {}),
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
            "observed_pooled_delta_dti": round(mean_diff, 6),  # NOTE: this is the bootstrap MEAN of A-B
            "bootstrap_mean_delta_dti_A_minus_B": round(mean_diff, 6),
            "point_delta_dti_A_minus_B": round(float(dti_A - dti_B), 6),
            "pairs": pairs,
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
            "sgmc_alone_auc_continuous_neg_distance_vs_withheld_catalogue": round(auc_sgmc_cont, 6),
            "visible_catalogue_alone_auc_control": round(auc_visible, 6),
            "flags": (["LEAKAGE: SGMC alone AUC > 0.90 vs withheld catalogue (expected circularity: "
                       "SGMC independently maps the same structures the catalogue holds)"]
                      if auc_sgmc > 0.90 else [])
                     + (["LEAKAGE: continuous SGMC-distance AUC > 0.90 vs withheld catalogue"]
                        if auc_sgmc_cont > 0.90 else []),
            "note": ("Catalogue-truth holdout: any layer that independently maps catalogue faults "
                     "will score high. This measures circularity, not hidden-label skill."),
        },
        "xgrad_canary": (None if not args.with_xgrad_arm else {
            "score_alone_auc_vs_withheld_truth": round(xgrad_auc, 6), "auc_cut": 0.90,
            "flag": ("LEAKAGE" if xgrad_auc > 0.90 else "clean (score alone below 0.90)"),
            "note": "single catalogue-independent feature vs withheld catalogue cells; not a compliant hide-and-recover test"}),
        "xgrad_features": ({"path": str(args.features), "sha256": "4371c82e3b8339b807bdffcf4ef59a225520fe2988d521be208ae33743123bc5",
                            "provenance": "owner-mirrored (GEMSDOE data/bridge manifest), not organizer-authenticated"}
                           if args.with_xgrad_arm else None),
        "folds_detail": [
            {"fold": fd["fold"], "held_segments": fd["n_held_segments"],
             "held_cells": fd["held_cells"], "visible_cells": fd["visible_cells"],
             "n_dots": fd["n_dots"],
             **({"n_dots_C_native": fd["n_dots_C_native"], "n_dots_C_matched": fd["n_dots_C_matched"]}
                if args.with_h54a_arm else {})}
            for fd in per_fold
        ],
        "mass": {"pooled_budget_A_B": pooled_budget, "pooled_dots": N,
                 "C_shortfall_vs_budget": (pooled_budget - N["C"]) if "C" in N else None,
                 "X_shortfall_vs_budget": (pooled_budget - N["X"]) if "X" in N else None},
        "inputs": {
            "labels_sha256": "7ba308ccdc4418b31a178f4f1ef21aaa6e152e4028f2f6f64b01f7eb25ae4093",
            "sgmc_sha256": "26d142c4c93282cd94f6950ab96f22aeff59fbbea523d43d662e76fa1b161b5c",
        },
        "timing_s": round(time.time() - t0, 1),
    }
    out = Path(args.out) if args.out else ROOT / "work" / "cgrc_holdout_receipt.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    print(f"\nHOLDOUT-DTI A={dti_A:.4f} B={dti_B:.4f} delta={mean_diff:+.4f} "
          f"SE={se_diff:.5f} MDE(raw)={raw_mde:.5f} 0.0028_above={0.0028 > raw_mde}")
    print(f"wrote {out} in {time.time()-t0:.0f}s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

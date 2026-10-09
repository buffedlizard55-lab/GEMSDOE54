#!/usr/bin/env python3
"""Whole-segment 5-fold hide-and-recover holdout, evaluator ``gemsdoe54-segment-cv`` v1.

This is the holdout the repository's protocol requires, implemented end to end:

1.  Units. The independent units are the 8-connected components ("segments") of the
    owner-mirrored catalogue raster (labels == 1 inside the study footprint). A component is
    never split between folds.
2.  Folds. Segments are shuffled with seed 20261008 and dealt to K = 5 folds.
3.  Per fold k. Withheld truth W_k = cells of fold-k segments. Buffer collar C_k = cells within
    3 px (300 m, Euclidean) of W_k that are not in W_k. Visible catalogue V_k = catalogue minus
    W_k minus C_k.
4.  Scored area S_k = footprint minus V_k minus C_k (pixel-exact visible masking). Predictions
    outside S_k are discarded before scoring.
5.  Visible-only features. A candidate may use only the feature rasters and V_k. Its catalogue
    exclusion is E_k = cells within 3 px of V_k (the builder's 300 m rule, applied to visible
    faults only).
6.  Metric. Organizer DTI with alpha 0.2, beta 0.8 and the 300 m triangular kernel. TP, FP, FN
    are computed per fold and pooled by summation. The decomposition is cross-checked against
    ``gemsdoe54.holdout.pooled_metric`` (grid EDT) on fold 0 before any result is written.
7.  Inference. Paired whole-segment cluster bootstrap, stratified by fold, B replicates, the SAME
    resampled segment indices for every candidate (paired). 95 % CI = percentile interval.
    Standard error of a paired difference feeds the normal-approximation MDE (2.80 x SE).
8.  Canary. Single-feature AUC of each of the 19 feature bands and of distance-to-visible-
    catalogue, per fold. AUC > 0.90 = LEAKAGE. The distance feature is reported separately
    because withholding creates holes in the visible catalogue by construction.
9.  Null. Each candidate's dot pattern is randomly torus-shifted per fold N times; the shifted
    pooled DTI distribution is the chance baseline.

Candidates (all visible-only, all built with the same linearity gate and 2 px spacing as the
submission builder):
  C1  SGMC state-map complement (the H54-A rule):  SGMC cells outside E_k.
  C2  Geodetic shear-rate ridge, count matched to C1 in every fold.
  C3  Horizontal magnetic-gradient ridge (tmi_hg), count matched to C1 in every fold.

The feature bands come from the owner's bridge (SHA-256 pinned in data/bridge manifest). Their
provenance is owner-claimed; nothing here is organizer-authenticated. The result is labelled
HOLDOUT-DTI with evaluator name and version, withheld positive count, and 95 % CI.
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
from scipy.spatial import cKDTree

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from gemsdoe54.emission import emit_spaced_dots  # noqa: E402
from gemsdoe54.grid import FOOTPRINT_CELLS, binary_mask, footprint, read_band  # noqa: E402
from gemsdoe54.holdout import pooled_metric, single_feature_auc  # noqa: E402
from gemsdoe54.power import minimum_detectable_cohen_d, normal_approx_mde_from_se  # noqa: E402
from build_submission import linearity_gate  # noqa: E402
from gemsdoe54.hypotheses import (  # noqa: E402
    GRAD_BANDS, MODEL_PARAMS, basement_step_score, cross_gradient_score, gradient_magnitude,
    learned_visible_probability,
)

EVALUATOR = {"name": "gemsdoe54-segment-cv", "version": "v1"}
# v2 adds the --hypotheses candidates (C4-C6). The scoring, folds, bootstrap and canary are unchanged.
EVALUATOR_V2 = {"name": "gemsdoe54-segment-cv", "version": "v2"}
HYP_CANARY_KEYS = ["model_visible_probability_C4", "cross_gradient_score_H1", "basement_step_grad_H2"]
K_FOLDS = 5
SEED = 20261008
BUFFER_PX = 3.0          # 300 m at 100 m cells
KERNEL_PX = 3.0          # organizer kernel radius, 300 m
ALPHA, BETA = 0.2, 0.8
SPACING_PX = 2.0         # 200 m, as in the submission builder
GATE = {"min_px": 3, "min_px_extent": 5, "min_elongation": 6.0}
FEATURE_PIN = "4371c82e3b8339b807bdffcf4ef59a225520fe2988d521be208ae33743123bc5"
FEATURE_NODATA = -3.4028234663852886e38
AUC_CUT = 0.90


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def load_band(path: Path, band: int) -> np.ndarray:
    with rasterio.open(path) as ds:
        arr = ds.read(band).astype(np.float32)
    arr[arr == np.float32(FEATURE_NODATA)] = np.nan
    return arr


def gated_dots(mask: np.ndarray, dist_m: np.ndarray) -> np.ndarray:
    """Builder rule 2 and 3: linearity gate, then longest traces first, then farthest from visible."""
    gated = linearity_gate(mask, **GATE)
    if not gated.any():
        return np.zeros(mask.shape, dtype=bool)
    lab, ncomp = label(gated, structure=np.ones((3, 3), dtype=int))
    comp_size = np.bincount(lab.ravel(), minlength=ncomp + 1)
    priority = comp_size[lab].astype(np.float64) + 1e-3 * dist_m
    priority[~gated] = -np.inf
    return emit_spaced_dots(gated, priority=priority, spacing_px=SPACING_PX)


RIDGE_QUANTILES = (0.05, 0.10, 0.20, 0.30, 0.40, 0.50, 0.60, 0.70, 0.80, 0.85, 0.90,
                   0.93, 0.95, 0.97, 0.98, 0.99, 0.995)


def ridge_matched(feat: np.ndarray, admissible: np.ndarray, target: int, dist_m: np.ndarray):
    """Choose the feature quantile whose gated dot count is closest to ``target``.

    Gate survival is not monotone in the threshold (low thresholds form blobs that the
    linearity gate rejects; high thresholds leave too few cells), so a coarse scan over the
    full quantile range is used instead of bisection. The achieved count is always reported.
    """
    fin = admissible & np.isfinite(feat)
    vals = feat[fin]
    best = None
    for q in RIDGE_QUANTILES:
        thr = float(np.quantile(vals, q))
        dots = gated_dots(fin & (feat >= thr), dist_m)
        n = int(dots.sum())
        if best is None or abs(n - target) < abs(best["n"] - target):
            best = {"dots": dots, "n": n, "quantile": q, "threshold": thr}
    return best


def top_k_nearest_segments(D: np.ndarray, kk: int, chunk: int = 8192) -> np.ndarray:
    """Column indices of the ``kk`` smallest entries of each row of ``D``, ascending by value."""
    n = D.shape[0]
    topk = np.empty((n, kk), dtype=np.int32)
    for s0 in range(0, n, chunk):
        block = D[s0:s0 + chunk]
        part = np.argpartition(block, kk - 1, axis=1)[:, :kk]
        dsel = np.take_along_axis(block, part, axis=1)
        srt = np.argsort(dsel, axis=1, kind="stable")
        topk[s0:s0 + chunk] = np.take_along_axis(part, srt, axis=1)
    return topk


class FoldScorer:
    """Exact per-fold decomposition of the organizer metric for unit-valued dots."""

    def __init__(self, truth: np.ndarray, seg_local: np.ndarray, n_seg: int, scored: np.ndarray):
        self.truth = truth
        self.scored = scored
        self.g = np.argwhere(truth)
        self.seg_of_g = seg_local[self.g[:, 0], self.g[:, 1]]
        self.n_seg = n_seg
        self.G_seg = np.bincount(self.seg_of_g, minlength=n_seg).astype(np.float64)
        self.n_g = float(self.g.shape[0])
        self.d_truth = distance_transform_edt(~truth)
        self.trees = [cKDTree(self.g[self.seg_of_g == s].astype(np.float64)) for s in range(n_seg)]

    def score(self, dots: np.ndarray, with_D: bool):
        dots = dots & self.scored
        ys, xs = np.nonzero(dots)
        n = int(ys.size)
        if n == 0:
            return {"TP": 0.0, "FP": 0.0, "FN": self.n_g, "TP_seg": np.zeros(self.n_seg),
                    "D": np.zeros((0, self.n_seg), np.float32), "n": 0}
        d_dot = distance_transform_edt(~dots)
        best = np.clip(1.0 - d_dot[self.g[:, 0], self.g[:, 1]] / KERNEL_PX, 0.0, None)
        TP_seg = np.bincount(self.seg_of_g, weights=best, minlength=self.n_seg)
        TP = float(TP_seg.sum())
        FN = self.n_g - TP
        earned = np.clip(1.0 - self.d_truth[ys, xs] / KERNEL_PX, 0.0, 1.0)
        FP = float(np.sum(1.0 - earned))
        D = None
        if with_D:
            P = np.column_stack([ys, xs]).astype(np.float64)
            D = np.empty((n, self.n_seg), dtype=np.float32)
            for s, tree in enumerate(self.trees):
                # distances beyond the kernel radius contribute exactly 0 credit, so the KD-tree may cap them
                D[:, s] = tree.query(P, distance_upper_bound=KERNEL_PX)[0]
        return {"TP": TP, "FP": FP, "FN": FN, "TP_seg": TP_seg, "D": D, "n": n}


def dti_from(tp: float, fp: float, fn: float) -> float:
    denom = tp + ALPHA * fp + BETA * fn
    return 0.0 if denom <= 0 else tp / denom


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--features", default="/tmp/sib/gems-geodawn-numerical-features.tif")
    ap.add_argument("--labels", default=str(ROOT / "data/grid/labels.tif"))
    ap.add_argument("--sgmc", default=str(ROOT / "data/external/derived_sgmc_faults_100m_u8.tif"))
    ap.add_argument("--out", default=str(ROOT / "evidence/holdout_segment_cv_v1.json"))
    ap.add_argument("--boot", type=int, default=1000)
    ap.add_argument("--shifts", type=int, default=30)
    ap.add_argument("--hypotheses", action="store_true",
                    help="add C4 (visible-only learned probability), C5 (cross-gradient), C6 (basement step)")
    args = ap.parse_args()
    hyp = bool(args.hypotheses)

    feat_path = Path(args.features)
    feat_sha = sha256_file(feat_path)
    if feat_sha != FEATURE_PIN:
        raise SystemExit(f"feature SHA-256 mismatch: {feat_sha} != pinned {FEATURE_PIN}")
    with rasterio.open(feat_path) as ds:
        band_names = [ds.tags(i).get("band_name", f"band{i}") for i in range(1, ds.count + 1)]

    foot = footprint(args.labels)
    labels_raw, _ = read_band(args.labels)
    cat = (labels_raw == 1) & foot
    sgmc = binary_mask(args.sgmc) & foot
    seg_lab, n_seg_total = label(cat, structure=np.ones((3, 3), dtype=int))
    rng = np.random.default_rng(SEED)
    order = rng.permutation(n_seg_total) + 1
    fold_of_seg = np.full(n_seg_total + 1, -1, dtype=np.int16)
    for i, sid in enumerate(order):
        fold_of_seg[sid] = i % K_FOLDS
    cell_fold = fold_of_seg[seg_lab]
    seg_fold_counts = [int(np.sum(fold_of_seg[1:] == k)) for k in range(K_FOLDS)]

    shear = load_band(feat_path, band_names.index("geod_shearrate") + 1)
    tmihg = load_band(feat_path, band_names.index("tmi_hg") + 1)
    feat_valid = foot & np.isfinite(shear) & np.isfinite(tmihg)

    names = ["C0_random_admissible_control", "C1_sgmc_complement", "C2_geodetic_shear_ridge", "C3_magnetic_hgrad_ridge"]
    if hyp:
        names += ["C4_visible_only_learned_probability", "C5_cross_gradient_ridge", "C6_basement_step_ridge"]
        # footprint-row feature matrix for the learned model: 19 bands + gradient magnitudes
        rows = np.flatnonzero(foot.ravel())
        n_raw = len(band_names)
        F = np.empty((rows.size, n_raw + len(GRAD_BANDS)), dtype=np.float32)
        for bi in range(1, n_raw + 1):
            arr = load_band(feat_path, bi)
            F[:, bi - 1] = arr.ravel()[rows]
            del arr
        for j, bn in enumerate(GRAD_BANDS):
            arr = load_band(feat_path, band_names.index(bn) + 1)
            g = gradient_magnitude(arr, foot & np.isfinite(arr), sigma_px=1.0)
            F[:, n_raw + j] = g.ravel()[rows]
            del arr, g
        # fold-independent hypothesis fields (no catalogue input)
        tmihg_full = load_band(feat_path, band_names.index("tmi_hg") + 1)
        grav_hg = load_band(feat_path, band_names.index("iso_grav_anom_hg") + 1)
        cross_full = cross_gradient_score(tmihg_full, grav_hg, foot)
        del tmihg_full, grav_hg
        dtb = load_band(feat_path, band_names.index("depth_to_base_surf") + 1)
        basement_full = basement_step_score(dtb, foot)
        del dtb
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
        # local segment index for each truth cell (1..n_k) -> 0..n_k-1
        segs_k = np.unique(seg_lab[W])
        local_map = np.full(n_seg_total + 1, -1, dtype=np.int64)
        local_map[segs_k] = np.arange(segs_k.size)
        seg_local = np.where(W, local_map[seg_lab], -1)
        scorer = FoldScorer(W, seg_local, int(segs_k.size), S)

        c1_mask = sgmc & adm
        c1 = gated_dots(c1_mask, dist_m)
        target = int(c1.sum())
        c2 = ridge_matched(shear, adm & feat_valid, target, dist_m)
        c3 = ridge_matched(tmihg, adm & feat_valid, target, dist_m)
        # C0: chance control. Uniformly random admissible cells, same count as C1, same exclusion
        # E_k. It isolates how much of any score comes from the buffer/exclusion geometry alone.
        rng_c0 = np.random.default_rng(SEED + 1000 + k)
        adm_idx = np.flatnonzero(adm.ravel())
        c0 = np.zeros(adm.size, dtype=bool)
        c0[rng_c0.choice(adm_idx, size=target, replace=False)] = True
        c0 = c0.reshape(adm.shape)
        dots_by = {names[0]: c0, names[1]: c1, names[2]: c2["dots"], names[3]: c3["dots"]}
        if hyp:
            vis_rows = V.ravel()[rows]
            coll_rows = collar.ravel()[rows]
            pred_rows = np.flatnonzero(adm.ravel()[rows])
            p_rows, learned_diag = learned_visible_probability(
                F, vis_rows, coll_rows, pred_rows, seed=SEED + 2000 + k)
            p_full = np.full(foot.size, np.nan, dtype=np.float32)
            p_full[rows[pred_rows]] = p_rows
            p_full = p_full.reshape(foot.shape)
            c4 = ridge_matched(p_full, adm & np.isfinite(p_full), target, dist_m)
            c5 = ridge_matched(cross_full, adm & np.isfinite(cross_full), target, dist_m)
            c6 = ridge_matched(basement_full, adm & np.isfinite(basement_full), target, dist_m)
            dots_by.update({names[4]: c4["dots"], names[5]: c5["dots"], names[6]: c6["dots"]})
            del p_rows
        fold_rec = {
            "fold": k, "withheld_segments": int(segs_k.size), "withheld_positive_cells": int(W.sum()),
            "buffer_collar_cells": int(collar.sum()), "visible_catalogue_cells": int(V.sum()),
            "scored_cells": int(S.sum()), "exclusion_cells_E": int((E & foot).sum()),
            "target_dots_C1": target, "C0_dots": int(c0.sum()),
            "C2_match": {"dots": c2["n"], "quantile": c2["quantile"], "threshold": c2["threshold"]},
            **({"C4_learned_train": learned_diag,
                "C4_match": {"dots": c4["n"], "quantile": c4["quantile"], "threshold": c4["threshold"]},
                "C5_match": {"dots": c5["n"], "quantile": c5["quantile"], "threshold": c5["threshold"]},
                "C6_match": {"dots": c6["n"], "quantile": c6["quantile"], "threshold": c6["threshold"]}} if hyp else {}),
            "C3_match": {"dots": c3["n"], "quantile": c3["quantile"], "threshold": c3["threshold"]},
            "candidates": {}, "canary": {},
        }

        # --- exact decomposition, cross-checked on fold 0 against the grid implementation ---
        boot_idx = rng.integers(0, segs_k.size, size=(args.boot, segs_k.size))
        for nm in names:
            sc = scorer.score(dots_by[nm], with_D=True)
            if k == 0 and nm == names[0]:
                chk_dti, chk_tp, chk_fp, chk_fn = pooled_metric(W, dots_by[nm] & S, kernel_px=KERNEL_PX,
                                                                alpha=ALPHA, beta=BETA)
                assert abs(chk_tp - sc["TP"]) < 1e-6 and abs(chk_fp - sc["FP"]) < 1e-6 and abs(chk_fn - sc["FN"]) < 1e-6, \
                    "decomposed metric disagrees with grid implementation"
                fold_rec["cross_check_fold0_C1"] = {"grid_dti": round(chk_dti, 9),
                                                    "decomposed_dti": round(dti_from(sc["TP"], sc["FP"], sc["FN"]), 9)}
            boot_tp = np.zeros(args.boot)
            boot_fp = np.zeros(args.boot)
            boot_fn = np.zeros(args.boot)
            if sc["n"] and sc["D"] is not None and sc["D"].shape[0] == sc["n"]:
                D = sc["D"]
            else:
                D = np.zeros((0, segs_k.size), np.float32)
            G = scorer.G_seg
            TPs = sc["TP_seg"]
            n_dots_k = D.shape[0]
            kk = min(24, segs_k.size)
            topk = top_k_nearest_segments(D, kk) if n_dots_k else None
            for b in range(args.boot):
                mult = np.bincount(boot_idx[b], minlength=segs_k.size).astype(np.float64)
                boot_tp[b] = mult @ TPs
                boot_fn[b] = mult @ (G - TPs)
                present = mult > 0
                if n_dots_k:
                    pres_k = present[topk]
                    has = pres_k.any(axis=1)
                    first = pres_k.argmax(axis=1)
                    dmin = np.full(n_dots_k, np.inf, dtype=np.float64)
                    ok = np.flatnonzero(has)
                    dmin[ok] = D[ok, topk[ok, first[ok]]]
                    rest = np.flatnonzero(~has)
                    if rest.size:
                        dmin[rest] = D[np.ix_(rest, np.flatnonzero(present))].min(axis=1)
                    boot_fp[b] = float(np.sum(1.0 - np.clip(1.0 - dmin / KERNEL_PX, 0.0, 1.0)))
            fold_rec["candidates"][nm] = {
                "dots_in_scored_area": sc["n"], "TP_w": sc["TP"], "FP_w": sc["FP"], "FN_w": sc["FN"],
                "boot_tp": boot_tp, "boot_fp": boot_fp, "boot_fn": boot_fn,
                "tp_seg": TPs, "G_seg": G,
            }
            del D

        # --- shift null for C1 (torus shifts of the dot pattern, restricted to S) ---
        nulls = []
        for s in range(args.shifts):  # noqa: E501
            dy = int(rng.integers(-(foot.shape[0] - 1), foot.shape[0]))
            dx = int(rng.integers(-(foot.shape[1] - 1), foot.shape[1]))
            shifted = np.roll(np.roll(c1, dy, axis=0), dx, axis=1)
            sc = scorer.score(shifted, with_D=False)
            nulls.append((sc["TP"], sc["FP"], sc["FN"]))
        fold_rec["null_C1_shift_components"] = [list(map(float, x)) for x in nulls]

        # --- canary: alone-AUC per fold for each band and the visible-catalogue distance ---
        for bi, bn in enumerate(band_names, start=1):
            arr = load_band(feat_path, bi)
            fold_rec["canary"][bn] = round(single_feature_auc(arr, W, valid=S), 6)
            del arr
        fold_rec["canary"]["dist_to_visible_catalogue_m"] = round(
            single_feature_auc(dist_m.astype(np.float32), W, valid=S), 6)
        # the SGMC layer is itself a feature of C1; its alone-AUC is reported like any other
        fold_rec["canary"]["sgmc_state_map_fault"] = round(
            single_feature_auc(sgmc.astype(np.float32), W, valid=S), 6)
        if hyp:
            fold_rec["canary"]["model_visible_probability_C4"] = round(
                single_feature_auc(p_full, W, valid=S & np.isfinite(p_full)), 6)
            fold_rec["canary"]["cross_gradient_score_H1"] = round(
                single_feature_auc(cross_full, W, valid=S & np.isfinite(cross_full)), 6)
            fold_rec["canary"]["basement_step_grad_H2"] = round(
                single_feature_auc(basement_full, W, valid=S & np.isfinite(basement_full)), 6)
            del p_full
        per_fold.append(fold_rec)
        print(f"fold {k}: segments={segs_k.size} W={int(W.sum())} C1 dots={target} "
              f"C2 dots={c2['n']} C3 dots={c3['n']} elapsed={(datetime.now(timezone.utc)-t0).seconds}s", flush=True)

    # ---- pooled point estimates -------------------------------------------------------
    cand_out = {}
    pooled_boot = {}
    for nm in names:
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
            "ci95_percentile": [round(float(np.percentile(bdti, 2.5)), 6), round(float(np.percentile(bdti, 97.5)), 6)],
            "label": "HOLDOUT-DTI",
        }
    paired = {}
    pairs = [(names[1], names[0]), (names[2], names[0]), (names[3], names[0]),
             (names[1], names[2]), (names[1], names[3])]
    if hyp:
        pairs += [(names[j], names[0]) for j in (4, 5, 6)] + [(names[j], names[1]) for j in (4, 5, 6)]
    for a, b in pairs:
        d = pooled_boot[a] - pooled_boot[b]
        point = cand_out[a]["pooled_dti_point"] - cand_out[b]["pooled_dti_point"]
        se = float(d.std(ddof=1))
        paired[f"{a} minus {b}"] = {
            "point": round(point, 6), "bootstrap_se": round(se, 6),
            "ci95_percentile": [round(float(np.percentile(d, 2.5)), 6), round(float(np.percentile(d, 97.5)), 6)],
            "mde_raw_80pct_two_sided": round(normal_approx_mde_from_se(se), 6),
            "bootstrap_sign_p": round(float(min(1.0, 2 * min((d <= 0).mean(), (d >= 0).mean()))), 4),
        }
    # shift-null distribution for C1 (pooled)
    null_vals = []
    for s in range(args.shifts):
        ntp = sum(f["null_C1_shift_components"][s][0] for f in per_fold)
        nfp = sum(f["null_C1_shift_components"][s][1] for f in per_fold)
        nfn = sum(f["null_C1_shift_components"][s][2] for f in per_fold)
        null_vals.append(dti_from(ntp, nfp, nfn))
    null_vals = np.array(null_vals)

    # canary summary (max over folds)
    canary = {}
    canary_keys = band_names + ["dist_to_visible_catalogue_m", "sgmc_state_map_fault"] + (HYP_CANARY_KEYS if hyp else [])
    for bn in canary_keys:
        aucs = [f["canary"][bn] for f in per_fold]
        canary[bn] = {"max_auc_over_folds": round(max(aucs), 6), "mean_auc": round(float(np.mean(aucs)), 6),
                      "flag": "LEAKAGE" if max(aucs) > AUC_CUT else "clear"}
    flags = [k for k, v in canary.items() if v["flag"] == "LEAKAGE"]
    source_of = {names[0]: "none (chance control)",
                 names[1]: "data/external/derived_sgmc_faults_100m_u8.tif (SGMC, catalogue-derived)",
                 names[2]: "geod_shearrate", names[3]: "tmi_hg"}
    feat_key = {names[0]: None, names[1]: "sgmc_state_map_fault",
                names[2]: "geod_shearrate", names[3]: "tmi_hg"}
    if hyp:
        source_of.update({
            names[4]: "visible-only learned probability (19 bands + 5 gradient bands; trained per fold)",
            names[5]: "tmi_hg x iso_grav_anom_hg, geometric mean of percentiles (H1)",
            names[6]: "gradient magnitude of depth_to_base_surf (H2)"})
        feat_key.update({names[4]: "model_visible_probability_C4", names[5]: "cross_gradient_score_H1",
                         names[6]: "basement_step_grad_H2"})
    status = {}
    for nm in names:
        if feat_key[nm] is None:
            status[nm] = "not applicable (chance control; no feature)"
        else:
            status[nm] = "CLEAR" if canary[feat_key[nm]]["flag"] == "clear" else "LEAKAGE-FLAGGED"

    n_total_pos = int(sum(f["withheld_positive_cells"] for f in per_fold))
    d_units_total = minimum_detectable_cohen_d(n_seg_total)
    d_units_fold = minimum_detectable_cohen_d(min(seg_fold_counts))
    payload = {
        "evaluator": (EVALUATOR_V2 if hyp else EVALUATOR) | {"metric": "organizer DTI alpha=0.2 beta=0.8 kernel=300 m triangular",
                                  "script_sha256": sha256_file(Path(__file__)),
                                  "seed": SEED, "bootstrap_replicates": args.boot, "shift_nulls": args.shifts},
        "label": ("HOLDOUT-DTI (evaluator gemsdoe54-segment-cv v2; catalogue-recovery truth, not hidden-test labels)"
                  if hyp else "HOLDOUT-DTI (evaluator gemsdoe54-segment-cv v1; catalogue-recovery truth, not hidden-test labels)"),
        "hypotheses": ({"H1": "tmi_hg x iso_grav_anom_hg cross-gradient ridge (C5)",
                        "H2": "depth_to_base_surf gradient ridge (C6)",
                        "H3": "visible-only HistGradientBoosting probability ridge (C4)",
                        "model_params": MODEL_PARAMS}
                       if hyp else None),
        "inputs": {
            "features": {"path": str(feat_path), "sha256": feat_sha, "bands": len(band_names),
                         "provenance": "owner bridge; hash-consistent with manifest; not organizer-authenticated"},
            "labels": {"path": args.labels, "sha256": sha256_file(Path(args.labels))},
            "sgmc": {"path": args.sgmc, "sha256": sha256_file(Path(args.sgmc))},
            "footprint_cells": int(foot.sum()), "footprint_expected": FOOTPRINT_CELLS,
        },
        "design": {"folds": K_FOLDS, "unit": "8-connected catalogue component (whole segment)",
                   "buffer_m": 300, "scored_area": "footprint minus visible catalogue minus buffer collar",
                   "visible_only_features": True, "pixel_exact_visible_mask": True},
        "units": {"catalogue_segments_total": int(n_seg_total), "segments_per_fold": seg_fold_counts,
                  "withheld_positive_cells_total": n_total_pos,
                  "withheld_positive_cells_per_fold": [f["withheld_positive_cells"] for f in per_fold]},
        "candidates": cand_out,
        "candidate_leakage_status": status,
        "candidate_source": source_of,
        "paired_differences": paired,
        "shift_null_C1": {"n": int(args.shifts), "mean": round(float(null_vals.mean()), 6),
                          "sd": round(float(null_vals.std(ddof=1)), 6),
                          "p95": round(float(np.percentile(null_vals, 95)), 6),
                          "max": round(float(null_vals.max()), 6)},
        "power": {
            "cohen_d_min_80pct_alpha05_units_total": round(d_units_total, 5),
            "cohen_d_min_80pct_alpha05_units_per_fold": round(d_units_fold, 5),
            "note": "Units are whole segments. Pixel-IID Cohen floors are invalid for this design and are not reported."
        },
        "canary": {"auc_cut": AUC_CUT, "features": canary, "flagged": flags},
        "per_fold": [{k2: v2 for k2, v2 in f.items() if k2 not in ("candidates",)} |
                     {"candidates": {nm: {kk: vv for kk, vv in c.items()
                                         if kk not in ("boot_tp", "boot_fp", "boot_fn", "tp_seg", "G_seg")}
                                     for nm, c in f["candidates"].items()}} for f in per_fold],
        "generated_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out).write_text(json.dumps(payload, indent=2, default=float) + "\n", encoding="utf-8")
    print(json.dumps({"candidates": cand_out, "paired": paired, "flags": flags, "status": status,
                      "null": payload["shift_null_C1"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

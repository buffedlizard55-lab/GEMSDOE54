#!/usr/bin/env python3
"""Pre-registered whole-segment hide-and-recover holdout for the magnetic-ridge candidate.

Reads ``evidence/preregistration_mag_ridge.json`` (frozen before this run) and writes
``evidence/mag_ridge_holdout.json``.  Every number is labelled HOLDOUT-DTI with the
evaluator version, the withheld-positive count and a split-level paired 95% CI.

Inputs (SHA-256 verified before use):
  data/grid/labels.tif                       catalogue labels (owner mirror)
  $GEMS_CACHE/training_features.tif          official 19-band stack (owner mirror)
"""

from __future__ import annotations

import hashlib
import json
import os
import sys
import time
from pathlib import Path

import numpy as np
import rasterio
from scipy.ndimage import distance_transform_edt
from scipy.stats import norm

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from gemsdoe54.emission import emit_spaced_dots  # noqa: E402
from gemsdoe54.holdout import detect_leakage, segment_blocks  # noqa: E402
from gemsdoe54.jackknife import (  # noqa: E402
    group_jackknife_counts,
    jackknife_se,
    leave_one_out_dti,
    pooled_dti_from_counts,
)
from gemsdoe54.power import minimum_detectable_cohen_d, normal_approx_mde_from_se  # noqa: E402
from gemsdoe54.ridge import (  # noqa: E402
    gate_by_visible,
    invalid_feature_mask,
    ridge_candidate,
)
from gems_metric import dti_components  # noqa: E402

PREREG = ROOT / "evidence/preregistration_mag_ridge.json"
OUT = ROOT / "evidence/mag_ridge_holdout.json"
LABELS = ROOT / "data/grid/labels.tif"
CACHE = Path(os.environ.get("GEMS_CACHE", "/tmp/gems-cache"))
FEATURES = CACHE / "training_features.tif"
EVALUATOR_VERSION = "gemsdoe54-segment-holdout-v1 (gems_metric.dti_components, official equations)"
LABELS_SHA = "7ba308ccdc4418b31a178f4f1ef21aaa6e152e4028f2f6f64b01f7eb25ae4093"
FEATURES_SHA = "4371c82e3b8339b807bdffcf4ef59a225520fe2988d521be208ae33743123bc5"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def assign_folds(blocks: np.ndarray, cat: np.ndarray, k: int, rng: np.random.Generator) -> np.ndarray:
    """Assign buffered segment groups to ``k`` folds, balancing withheld positives."""
    ids = np.unique(blocks[(blocks > 0)])
    pos_per_group = np.bincount(blocks[cat & (blocks > 0)], minlength=int(blocks.max()) + 1)
    order = rng.permutation(ids)
    load = np.zeros(k, dtype=np.int64)
    fold_of = np.full(int(blocks.max()) + 1, -1, dtype=np.int16)
    for gid in order:
        f = int(np.argmin(load))
        fold_of[gid] = f
        load[f] += pos_per_group[gid]
    return fold_of


def components(pred: np.ndarray, truth: np.ndarray, foot: np.ndarray):
    c = dti_components(pred.astype(np.float64), truth, valid=foot)
    return c.tp_w, c.fp_w, c.fn_w


def pooled_dti(tp: float, fp: float, fn: float) -> float:
    denom = tp + 0.2 * fp + 0.8 * fn
    return tp / denom if denom > 0 else 0.0


def matched_random(n: int, allowed: np.ndarray, rng: np.random.Generator) -> np.ndarray:
    idx = np.flatnonzero(allowed.ravel())
    out = np.zeros(allowed.size, dtype=bool)
    if n > 0:
        out[rng.choice(idx, size=min(n, idx.size), replace=False)] = True
    return out.reshape(allowed.shape)


def main(argv: list[str] | None = None) -> int:
    import argparse

    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--splits", type=int, default=None,
                    help="smoke-test override; output then goes to /tmp, never to evidence/")
    ap.add_argument("--prereg", type=Path, default=PREREG,
                    help="pre-registration file that fixes the design of this run")
    args = ap.parse_args(argv)
    t0 = time.time()
    prereg = json.loads(args.prereg.read_text(encoding="utf-8"))
    variant = prereg.get("candidate_variant", "dense")
    if variant not in ("dense", "spaced"):
        raise ValueError(f"unknown candidate_variant {variant!r}")
    out_default = ROOT / prereg["output"] if "output" in prereg else OUT
    assert sha256(LABELS) == LABELS_SHA, "labels.tif hash mismatch"
    assert FEATURES.exists(), f"missing {FEATURES}; run the bridge reassembly first"
    assert sha256(FEATURES) == FEATURES_SHA, "training_features.tif hash mismatch"

    lab = rasterio.open(LABELS).read(1)
    foot = lab >= 0
    cat = lab == 1

    # Memory: read one band at a time (3 GB sandbox); only RTP and THD are kept.
    with rasterio.open(FEATURES) as ds:
        names = {i: ds.descriptions[i - 1] for i in range(1, ds.count + 1)}
        feat_bad = np.zeros(lab.shape, dtype=bool)
        for i in range(1, ds.count + 1):
            feat_bad |= invalid_feature_mask(ds.read(i))
        rtp = ds.read(2)
        thd = ds.read(3)
    valid = foot & ~feat_bad
    ridge_bad = invalid_feature_mask(rtp, thd)
    ridge = ridge_candidate(rtp, thd, foot & ~ridge_bad,
                            sigma_px=prereg["parameters"]["sigma_px"],
                            quantile=prereg["parameters"]["quantile"],
                            min_len_px=prereg["parameters"]["min_len_px"],
                            invalid_buffer_px=prereg["parameters"]["invalid_buffer_px"])
    print(f"ridge (catalogue-free, length-gated): {int(ridge.sum()):,} cells; variant={variant}", flush=True)
    priority = np.where(valid, thd.astype(np.float64), -1.0)

    def candidate(ridge_map: np.ndarray, visible: np.ndarray) -> np.ndarray:
        gated = gate_by_visible(ridge_map, visible) & foot
        if variant == "dense":
            return gated
        # "spaced": one dot per 300 m kernel width along the gated traces, strongest first
        return emit_spaced_dots(gated, priority=priority,
                                spacing_px=float(prereg["parameters"]["spacing_px"]))

    S = int(prereg["holdout_design"]["splits"]) if args.splits is None else int(args.splits)
    out_path = out_default if args.splits is None else Path("/tmp/gems-cache/smoke_" + out_default.name)
    K = int(prereg["holdout_design"]["folds"])
    base = int(prereg["holdout_design"]["split_seed_base"])
    blocks, block_notes = segment_blocks(cat.astype(np.uint8), buffer_px=3)
    n_groups = int(np.unique(blocks[blocks > 0]).size)
    total_pos = int(cat.sum())
    print("segment_blocks:", block_notes, flush=True)

    split_rows = []
    METHODS = ("cand", "null", "placebo")
    per_split = {m: [] for m in METHODS}
    jk_by_method: dict[str, tuple] = {}
    for s_idx in range(S):
        rng = np.random.default_rng(base + s_idx)
        fold_of = assign_folds(blocks, cat, K, rng)
        grp_fold = np.where(blocks > 0, fold_of[blocks], -1)
        acc = {m: np.zeros(3) for m in METHODS}
        fold_dti = {m: [] for m in METHODS}
        counts_by_method: dict[str, list] = {m: [] for m in METHODS}
        withheld_pos = 0
        for k in range(K):
            in_k = grp_fold == k
            truth = cat & in_k
            visible = cat & ~in_k
            withheld_pos += int(truth.sum())
            cand = candidate(ridge, visible)
            placebo = candidate(np.roll(ridge, (1234, -567), axis=(0, 1)), visible)
            d_vis = distance_transform_edt(~visible, sampling=100.0)
            allowed = valid & (d_vis > 300.0)
            null = matched_random(int(cand.sum()), allowed, np.random.default_rng(base * 7 + s_idx * 31 + k))
            for name, pred in (("cand", cand), ("null", null), ("placebo", placebo)):
                tp, fp, fn = components(pred, truth, foot)  # official metric = reference
                cnt = group_jackknife_counts(pred, truth, blocks, foot)
                if max(abs(cnt["TP"] - tp), abs(cnt["FP"] - fp), abs(cnt["FN"] - fn)) > 1e-6:
                    raise RuntimeError(f"jackknife counts disagree with official metric ({name}, fold {k})")
                acc[name] += (tp, fp, fn)
                fold_dti[name].append(pooled_dti(tp, fp, fn))
                counts_by_method[name].append(cnt)
        row = {"split": s_idx, "withheld_positives": withheld_pos}
        for m in METHODS:
            dti = pooled_dti(*acc[m])
            per_split[m].append(dti)
            row[f"dti_{m}"] = round(dti, 6)
            row[f"tp_{m}"], row[f"fp_{m}"], row[f"fn_{m}"] = (round(float(v), 4) for v in acc[m])
            row[f"fold_dti_{m}"] = [round(v, 6) for v in fold_dti[m]]
        if s_idx == 0:
            # Exact leave-one-segment-group-out jackknife, computed on the first partition.
            for m in METHODS:
                cs = counts_by_method[m]
                TP = sum(c["TP"] for c in cs); FP = sum(c["FP"] for c in cs); G = sum(c["G"] for c in cs)
                gids = np.concatenate([c["gids"] for c in cs])
                loo = leave_one_out_dti({
                    "TP": TP, "FP": FP, "G": G,
                    "tp_g": np.concatenate([c["tp_g"] for c in cs]),
                    "n_g": np.concatenate([c["n_g"] for c in cs]),
                    "dfp_g": np.concatenate([c["dfp_g"] for c in cs]),
                })
                jk_by_method[m] = (gids, loo, pooled_dti_from_counts(TP, FP, G - TP))
        split_rows.append(row)
        print(f"split {s_idx:2d}: cand {row['dti_cand']:.5f}  null {row['dti_null']:.5f}  "
              f"placebo {row['dti_placebo']:.5f}  withheld+={withheld_pos}  "
              f"[{time.time() - t0:.0f}s]", flush=True)

    def jack_compare(a: str, b: str) -> dict:
        ga, loo_a, pt_a = jk_by_method[a]
        gb, loo_b, pt_b = jk_by_method[b]
        assert np.array_equal(ga, gb), "group ids must align across methods"
        theta = loo_a - loo_b
        se = jackknife_se(theta)
        diff = pt_a - pt_b
        z = float(norm.ppf(0.975))
        n_units = int(theta.size)
        d_min = minimum_detectable_cohen_d(n_units)
        return {
            "comparison": f"{a} - {b}",
            "uncertainty_method": "exact leave-one-segment-group-out jackknife on the first partition",
            "n_units_segment_groups": n_units,
            "point_difference": round(diff, 6),
            "jackknife_se": round(se, 6),
            "ci95_low": round(diff - z * se, 6),
            "ci95_high": round(diff + z * se, 6),
            "mde_raw_dti_80pct_power_alpha05": round(float(normal_approx_mde_from_se(se)), 6),
            "cohen_d_min_units": round(d_min, 4),
            "ci_excludes_zero": bool((diff - z * se) > 0 or (diff + z * se) < 0),
        }

    comps = [jack_compare("cand", "null"), jack_compare("cand", "placebo")]
    cand_vs_null = comps[0]
    cand_vs_placebo = comps[1]
    split_spread = {m: {"mean": round(float(np.mean(per_split[m])), 6),
                        "sd_across_splits": round(float(np.std(per_split[m], ddof=1)), 6)} for m in METHODS}

    # Canary (split-independent): features are catalogue-free; the catalogue-distance feature
    # is the one that could leak, so it is tested on fold 0 of split 0 against that fold's truth.
    canary_valid = foot & ~feat_bad
    canary_flags = []
    with rasterio.open(FEATURES) as ds:
        for i in range(1, ds.count + 1):  # one band at a time
            canary_flags += detect_leakage({f"band{i}_{names[i]}": ds.read(i)},
                                           cat & canary_valid, valid=canary_valid)
    rng0 = np.random.default_rng(base)
    fold_of0 = assign_folds(blocks, cat, K, rng0)
    grp0 = np.where(blocks > 0, fold_of0[blocks], -1)
    truth0 = cat & (grp0 == 0)
    visible0 = cat & ~(grp0 == 0)
    d0 = distance_transform_edt(~visible0, sampling=100.0)
    canary_flags += detect_leakage({"neg_distance_to_visible_catalogue": -d0.astype(np.float64)},
                                   truth0, valid=canary_valid)
    cand0 = candidate(ridge, visible0)
    canary_flags += detect_leakage({"candidate_indicator": cand0.astype(np.float64)},
                                   truth0, valid=canary_valid)

    promote_eligible = (cand_vs_null["ci95_low"] > 0 and cand_vs_placebo["ci95_low"] > 0
                        and not canary_flags)
    out = {
        "label": "HOLDOUT-DTI (local, catalogued-fault hide-and-recover; NOT a leaderboard score)",
        "candidate_variant": variant,
        "experiment": prereg.get("preregistration_id"),
        "evaluator_version": EVALUATOR_VERSION,
        "preregistration": str(PREREG.relative_to(ROOT)),
        "withheld_positives_per_split": total_pos,
        "independent_units_segment_groups": n_groups,
        "segment_blocks_notes": block_notes,
        "folds": K,
        "splits": S,
        "pooled_metric": "per fold official DTI components summed over folds, then TP/(TP+0.2FP+0.8FN)",
        "ridge_cells_catalogue_free": int(ridge.sum()),
        "split_rows": split_rows,
        "pooled_dti_split_summary": split_spread,
        "pooled_dti_first_partition": {m: round(jk_by_method[m][2], 6) for m in METHODS},
        "paired_comparisons": comps,
        "uncertainty_note": ("Split-to-split spread is reported for transparency only: the pooled design "
                             "withholds each catalogue neighbourhood once per split, so split spread understates "
                             "sampling uncertainty. The CI uses the segment-group jackknife."),
        "leakage_canary": {
            "cut": 0.90,
            "flags": canary_flags,
            "status": "PASS" if not canary_flags else "FLAGGED",
        },
        "decision": {
            "promote_eligible": bool(promote_eligible),
            "rule": prereg["decision_rule"],
            "verdict": "promote-eligible (still requires a separate selector decision)" if promote_eligible else "negative",
        },
        "scope": prereg["scope_limits"],
        "runtime_s": round(time.time() - t0, 1),
    }
    out_path.write_text(json.dumps(out, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {out_path}")
    print(json.dumps({"split_summary": split_spread, "cand_vs_null": cand_vs_null,
                      "cand_vs_placebo": cand_vs_placebo, "canary": out["leakage_canary"],
                      "verdict": out["decision"]["verdict"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Shared evaluator: hide-and-recover head-to-head of emission arms, pooled DTI + power analysis.

    python3 scripts/evaluate_holdout.py --instrument adjacency
    python3 scripts/evaluate_holdout.py --instrument extrapolation

DESIGN (registered in ``registry/preregistration.json`` before results were read)
  * the catalogue -> 8-connected components -> each component assigned WHOLE to one of 4 spatial
    quadrants by its centroid;
  * for fold q, VISIBLE = every component outside q.  Every field and every emission arm is built
    from the visible faults of that fold only;
  * SCORED TRUTH for fold q = the components of q.  Two instruments:
      - ``adjacency``      : all pixels of the withheld components (tests "where should mass go
                             relative to known faults to hit unknown parts of the same systems");
      - ``extrapolation``  : withheld pixels further than the buffer (300 m) from any visible pixel
                             (tests "can anything here find a fault away from the known ones");
  * the prediction raster spans the whole footprint -- exactly like a real submission -- so mass
    that no withheld fault is near is charged as false-positive mass;
  * terms pooled over folds, then pooled DTI = T / (T + 0.2 F + 0.8 K).

Every arm carries its paired per-fold difference against the anchor and the Cohen-style minimum
detectable effect (MDE) for that paired design, so no ranking is read off a difference the design
cannot resolve.  Writes ``evidence/holdout_<instrument>.json``.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np
from scipy import ndimage

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from gems54 import data as D       # noqa: E402
from gems54 import fields as F     # noqa: E402
from gems54 import holdout as H    # noqa: E402
from gems54 import metric as M     # noqa: E402

ANCHOR = "A1_on_sp2"


def build_arms(vis: np.ndarray, shape, rng, dot_budget: int) -> dict[str, np.ndarray]:
    out: dict[str, np.ndarray] = {}
    r = np.zeros(shape, bool)
    r.ravel()[rng.choice(shape[0] * shape[1], size=dot_budget, replace=False)] = True
    out["A0_random"] = r

    d = F.distance_to(vis).astype(np.float32)
    out["A9_solid_visible"] = vis.copy()
    for sp in (1, 2, 3, 4, 6, 8):
        out[f"A1_on_sp{sp}"] = F.thin_along_trace(vis, sp)
    for off in (1, 2):
        band = np.abs(d - off) <= 0.5
        for sp in (2, 4):
            out[f"A2_off{off}_sp{sp}"] = F.thin_along_trace(band, sp)
    out["A3_flankB2_sp3"] = F.thin_along_trace(d > 2, 3)
    out["A4_pack_sig1.85"] = F.greedy_max_coverage(
        np.exp(-0.5 * (d / 1.85) ** 2).astype(np.float32), dot_budget, min_sep_px=1.0)
    # smooth probability emission (no dots) -- tests the dots-vs-probability question directly
    out["A7_smooth_prob"] = np.exp(-0.5 * (d / 1.85) ** 2).astype(np.float32) * (d <= 5)
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--instrument", choices=["adjacency", "extrapolation"], default="adjacency")
    ap.add_argument("--buffer-px", type=int, default=3)
    ap.add_argument("--dot-budget", type=int, default=23000)
    ap.add_argument("--seed", type=int, default=54)
    args = ap.parse_args()

    t0 = time.time()
    fp = D.footprint()
    comp = H.catalogue_segments(5)
    rng = np.random.default_rng(args.seed)
    preds: dict[str, dict[str, np.ndarray]] = {}
    terms: dict[str, dict] = {}
    infos = []

    for q, held, vis, _quad in H.build_folds(comp, fp, args.buffer_px):
        if args.instrument == "extrapolation":
            truth = held & ~ndimage.binary_dilation(
                vis, np.ones((2 * args.buffer_px + 1,) * 2, bool))
        else:
            truth = held
        if truth.sum() < 500:
            continue
        knear = M.nearest_kernel(truth)
        infos.append({"fold": q, "visible_px": int(vis.sum()), "truth_px": int(truth.sum())})
        for name, pred in build_arms(vis, fp.shape, rng, args.dot_budget).items():
            t = M.dti_sparse(pred, truth, knear)
            terms.setdefault(name, {})[q] = t
        print(f"  fold {q}: visible={int(vis.sum()):,} truth={int(truth.sum()):,}"
              f"  ({time.time()-t0:.0f}s)")

    folds = [i["fold"] for i in infos]
    results = {}
    for name, per in terms.items():
        tp = sum(per[q]["TPw"] for q in folds); fpw = sum(per[q]["FPw"] for q in folds)
        fnw = sum(per[q]["FNw"] for q in folds)
        per_fold = {q: per[q]["DTI"] for q in folds}
        results[name] = {
            "pooled_dti": tp / (tp + M.ALPHA * fpw + M.BETA * fnw + 1e-12),
            "TPw": tp, "FPw": fpw, "FNw": fnw,
            "emitted_px": int(sum(per[q]["support_px"] for q in folds)),
            "per_fold": per_fold}

    anchor = results[ANCHOR]
    for name, r in results.items():
        if name == ANCHOR:
            continue
        r["vs_anchor"] = H.mde_from_differences(
            np.array([r["per_fold"][q] - anchor["per_fold"][q] for q in folds]))

    a = anchor
    k_px = int(sum(i["truth_px"] for i in infos))
    step = H.single_truth_pixel_step(a["TPw"], a["FPw"], sum(terms[ANCHOR][q]["K"] for q in folds))
    results["_instrument"] = {
        "instrument": args.instrument, "folds": infos, "anchor": ANCHOR,
        "withheld_truth_px": k_px, "one_pixel_step_dti": step,
        "binomial_floor_dti": H.unit_floor(k_px) * step,
        "note": ("one_pixel_step_dti is the DTI change from covering ONE more withheld truth "
                 "pixel: the resolution of this instrument.  The binomial floor is what a finite "
                 "truth set of K positives can resolve at all.")}

    out = ROOT / "evidence" / f"holdout_{args.instrument}.json"
    out.parent.mkdir(exist_ok=True)
    out.write_text(json.dumps(results, indent=1))

    print(f"\n--- instrument: {args.instrument} ---")
    print(f"{'arm':<20}{'pooled':>9}{'emitted':>11}{'vs anchor':>11}{'MDE':>8}{'detect':>8}")
    for name, r in sorted(results.items(), key=lambda kv: -(kv[1].get("pooled_dti") or 0)):
        if name.startswith("_"):
            continue
        v = r.get("vs_anchor", {})
        print(f"{name:<20}{r['pooled_dti']:>9.4f}{r['emitted_px']:>11,}"
              f"{v.get('mean_diff', float('nan')):>11.4f}"
              f"{v.get('mde_power80_alpha05', float('nan')):>8.4f}"
              f"{str(v.get('detected', '')):>8}")
    print(f"\nwithheld truth px={k_px:,}  one-pixel step={step:.2e}  "
          f"finite-K floor={results['_instrument']['binomial_floor_dti']:.2e}  ({time.time()-t0:.0f}s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

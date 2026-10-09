#!/usr/bin/env python3
"""Mass-matched uniform-random control for the CGRC pooled holdout.

Places N uniform-random dots over the study footprint (N = the holdout's
pooled arm mass) and scores them against the same pooled withheld truth the
holdout uses (the union of the withheld catalogue segments across the 4
quadrant folds, i.e. all retained catalogue components).  Run for several
seeds; the mechanism lift is the arm's pooled DTI divided by the random
mean.  This is a sanity control (the method must beat random by a wide
margin), not a holdout result in itself.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import rasterio
from scipy.ndimage import label

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from gemsdoe54.grid import footprint  # noqa: E402
from gemsdoe54.holdout import pooled_metric  # noqa: E402

MIN_PX = 3


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--n-dots", type=int, required=True)
    ap.add_argument("--seeds", type=int, nargs="+", default=[0, 1, 2])
    ap.add_argument("--out", default=None)
    args = ap.parse_args()

    foot = footprint(ROOT / "data/grid/labels.tif")
    with rasterio.open(ROOT / "data/grid/labels.tif") as src:
        lab = src.read(1)
    cat = (lab == 1) & foot

    seg_lab, ncomp = label(cat, structure=np.ones((3, 3), dtype=int))
    cnt = np.bincount(seg_lab.ravel(), minlength=ncomp + 1)
    kept = [a for a in range(1, ncomp + 1) if cnt[a] >= MIN_PX]
    truth = np.isin(seg_lab, kept) & cat
    n_pos = int(truth.sum())

    foot_cells = np.argwhere(foot)
    results = {}
    for seed in args.seeds:
        rng = np.random.default_rng(seed)
        idx = rng.integers(0, len(foot_cells), size=args.n_dots)
        dots = np.zeros(foot.shape, dtype=bool)
        dots[foot_cells[idx, 0], foot_cells[idx, 1]] = True
        dti, tp, fp, fn = pooled_metric(truth, dots)
        results[seed] = round(float(dti), 6)
        print(f"seed {seed}: random DTI={dti:.6f} (N={int(dots.sum()):,})")

    mean = float(np.mean(list(results.values())))
    receipt = {
        "schema": "gemsdoe54.random-control.v1",
        "n_dots": args.n_dots,
        "dti_by_seed": results,
        "dti_mean": round(mean, 6),
        "withheld_positive_count": n_pos,
        "note": "mass-matched uniform random dots over the footprint; control only, not a holdout",
    }
    if args.out:
        Path(args.out).write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
        print(f"wrote {args.out}")
    print(f"random mean DTI = {mean:.6f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

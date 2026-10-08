#!/usr/bin/env python3
"""Leakage canary: test each feature ALONE against the holdout truth.

The parallel-run protocol requires this before any feature is trusted: a single
feature whose held-out AUC exceeds 0.90 is leakage until proven otherwise.  Here it
is used for a stronger purpose -- to demonstrate, rather than assert, that the
corpus's SGMC-derived proxy is *circular* for this submission, because the
submission's only evidence layer is the same raster the proxy's truth is built from.

Run:  python scripts/leakage_canary.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import rasterio
from scipy.stats import rankdata
from scipy.ndimage import distance_transform_edt

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from gemsdoe54.grid import binary_mask  # noqa: E402
from gemsdoe54.holdout import detect_leakage  # noqa: E402


def main() -> int:
    with rasterio.open(ROOT / "data/grid/labels.tif") as src:
        lab = src.read(1)
        foot = lab != src.nodata
    catalogue = (lab == 1) & foot
    sgmc = binary_mask(ROOT / "data/external/derived_sgmc_faults_100m_u8.tif") & foot

    d_cat = distance_transform_edt(~catalogue, sampling=(100.0, 100.0))
    proxy = sgmc & (d_cat > 300.0)

    # Candidate feature stack.  Every one of these is either an honest feature (it
    # carries no information about the proxy's construction) or the leakage probe.
    d_cat_feat = np.clip(d_cat / 3000.0, 0.0, 1.0)
    features = {
        "sgmc_raster_used_by_this_submission": sgmc.astype(np.float64),
        "distance_to_catalogue_normalised": d_cat_feat,
        "uniform_control": np.ones(lab.shape, dtype=np.float64),
    }

    flags = detect_leakage(features, proxy, valid=foot, auc_cut=0.90)

    # Report the AUC of each feature explicitly, including the ones that pass.
    pos = proxy & foot
    neg_idx = np.flatnonzero(((~proxy) & foot).ravel())
    rng = np.random.default_rng(20261008)
    sel = np.zeros(foot.size, dtype=bool)
    sel[rng.choice(neg_idx, size=min(200_000, neg_idx.size), replace=False)] = True
    neg = sel.reshape(foot.shape)
    aucs = {}
    for name, feat in features.items():
        a = np.asarray(feat)[pos]
        b = np.asarray(feat)[neg]
        allv = np.concatenate([a, b])
        ranks = rankdata(allv, method="average")   # mid-ranks: ties handled
        auc = (ranks[: a.size].sum() - a.size * (a.size + 1) / 2) / (a.size * b.size)
        aucs[name] = round(max(auc, 1.0 - auc), 6)

    out = {
        "auc_cut": 0.90,
        "holdout_truth": "SGMC mapped faults > 300 m from the competition catalogue",
        "holdout_truth_cells": int(proxy.sum()),
        "withheld_positives_used": int(pos.sum()),
        "negatives_subsampled": int(neg.sum()),
        "auc_by_feature": aucs,
        "leakage_flags": flags,
        "interpretation": (
            "The SGMC raster scores AUC ~ 1.0 against an SGMC-derived truth. That is the "
            "definition of leakage, and it is why this submission's PROXY-DTI is reported "
            "as a circular self-consistency check and never as a score. Any candidate whose "
            "evidence layer feeds the holdout truth cannot be validated on that holdout."
        ),
    }
    path = ROOT / "evidence/leakage_canary.json"
    path.write_text(json.dumps(out, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(out, indent=2))
    print(f"\nwrote {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

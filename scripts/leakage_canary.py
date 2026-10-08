#!/usr/bin/env python3
"""Circularity probe: score one feature at a time against the historical SGMC proxy.

This is not a compliant holdout leakage canary. The proxy target and the candidate's
SGMC feature share the same source raster, so the output demonstrates circularity of
that proxy only; it is not evidence of predictive skill on hidden expert labels.
The actual protocol still requires feature-alone AUC checks on each frozen,
whole-segment hide-and-recover fold.

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
        "label": "PROXY-CANARY — circular SGMC-derived target; not HOLDOUT-DTI",
        "auc_cut": 0.90,
        "proxy_target_description": "SGMC mapped faults > 300 m from the competition catalogue",
        "proxy_positive_cells": int(proxy.sum()),
        "proxy_positive_samples_used": int(pos.sum()),
        "negatives_subsampled": int(neg.sum()),
        "auc_by_feature": aucs,
        "leakage_flags": flags,
        "interpretation": (
            "The SGMC raster scores AUC near 1.0 against a target constructed from the same SGMC raster. "
            "This demonstrates circularity of the SGMC-derived proxy only. It is not a compliant feature-alone "
            "test on a whole-segment holdout, is not evidence of hidden-label prediction skill, and is not a score."
        ),
    }
    path = ROOT / "evidence/leakage_canary.json"
    path.write_text(json.dumps(out, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(out, indent=2))
    print(f"\nwrote {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

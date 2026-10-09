#!/usr/bin/env python3
"""Co-location diagnostic: is the SGMC state-map layer a near-copy of the catalogue labels?

The single-feature AUC canary is blind to sparse binary layers (SGMC covers ~1.6% of the footprint,
so its AUC stays near 0.5 even when it co-locates with the labels). This script measures the
enrichment directly. Receipt: evidence/sgmc_colocation.json.

Run: python scripts/sgmc_colocation.py --out evidence/sgmc_colocation.json
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
from scipy.ndimage import distance_transform_edt

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from gemsdoe54.grid import binary_mask, footprint, read_band  # noqa: E402


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--labels", default=str(ROOT / "data/grid/labels.tif"))
    ap.add_argument("--sgmc", default=str(ROOT / "data/external/derived_sgmc_faults_100m_u8.tif"))
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    foot = footprint(a.labels)
    lab, _ = read_band(a.labels)
    cat = (lab == 1) & foot
    sg = binary_mask(a.sgmc) & foot
    d_cat = distance_transform_edt(~cat)
    d_sg = distance_transform_edt(~sg)
    rnd_sg = float(((d_sg <= 3) & foot).sum() / foot.sum())
    rnd_cat = float(((d_cat <= 3) & foot).sum() / foot.sum())
    p_sg_given_cat = float(((d_sg <= 3) & cat).sum() / cat.sum())
    p_cat_given_sg = float(((d_cat <= 3) & sg).sum() / sg.sum())
    out = {
        "schema": "gemsdoe54.sgmc-colocation.v1",
        "generated_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "inputs": {"labels_sha256": sha(Path(a.labels)), "sgmc_sha256": sha(Path(a.sgmc))},
        "footprint_cells": int(foot.sum()), "catalogue_cells": int(cat.sum()), "sgmc_cells": int(sg.sum()),
        "exact_overlap_cells": int((sg & cat).sum()),
        "P_sgmc_within_300m_given_catalogue_cell": round(p_sg_given_cat, 6),
        "P_sgmc_within_300m_given_random_footprint_cell": round(rnd_sg, 6),
        "enrichment_sgmc_near_catalogue": round(p_sg_given_cat / rnd_sg, 3),
        "P_catalogue_within_300m_given_sgmc_cell": round(p_cat_given_sg, 6),
        "P_catalogue_within_300m_given_random_footprint_cell": round(rnd_cat, 6),
        "enrichment_catalogue_near_sgmc": round(p_cat_given_sg / rnd_cat, 3),
        "reading": "SGMC is a related but not identical map. Its layer carries catalogue-correlated "
                   "information, so it is not a visible-only feature in the whole-segment holdout.",
    }
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    Path(a.out).write_text(json.dumps(out, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: out[k] for k in out if "enrichment" in k or k.startswith("P_")}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

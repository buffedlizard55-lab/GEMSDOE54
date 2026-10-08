#!/usr/bin/env python3
"""Blocked holdout: score every candidate we can read, and say what it is worth.

What this measures
------------------
The only truth set available without organiser credentials is the proxy built from
the USGS State Geologic Map Compilation (SGMC) restricted to cells more than 300 m
from the competition catalogue.  Scoring against it answers one narrow question
honestly: *does a candidate place its dots on real, independently mapped faults
that the competition catalogue does not contain?*

What this cannot measure
------------------------
Whether that skill transfers to the organisers' hidden expert labels.  Across all
six artefacts with both downloadable bytes and a published public score, the
Spearman correlation between this proxy and the leaderboard is -0.03 (p = 0.96).
A holdout that does not order two known submissions cannot be a promotion gate, so
every number this script prints is labelled SCREENING, never a score.

Candidates whose dots are placed on the SGMC raster itself are additionally
flagged ``circular``: they are being scored against the layer they were built from,
so their DTI is a self-consistency check, not evidence.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import rasterio

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from gemsdoe54.grid import footprint  # noqa: E402
from gemsdoe54.holdout import (  # noqa: E402
    informative_truth_cells,
    pooled_metric,
    shift_null_ci,
)

PROXY = Path("/home/user/_keep/proxy_catalogue_sgmc.tif")
REGISTRY = ROOT / "registry/registry_rasters"
ARTEFACT = ROOT / "docs/downloads/gems54-undercomplement-q200.tif"
TRUTH_CLASS = 2  # SGMC faults more than 300 m from the competition catalogue


def load_dots(path: Path) -> tuple[np.ndarray, float | None]:
    with rasterio.open(path) as src:
        a = src.read(1)
    finite = np.isfinite(a) if np.issubdtype(a.dtype, np.floating) else np.ones(a.shape, bool)
    mask = finite & (a > 0)
    return mask, None


def matched_random(n: int, foot: np.ndarray, seed: int) -> np.ndarray:
    """A control with the same dot count, placed uniformly over the footprint.

    Without this the proxy DTI of any dense candidate looks impressive purely
    because 20-60 k dots cover a lot of a small truth set.  The control states what
    "no skill" scores at that mass.
    """
    rng = np.random.default_rng(seed)
    idx = np.flatnonzero(foot.ravel())
    pick = rng.choice(idx, size=min(n, idx.size), replace=False)
    out = np.zeros(foot.size, dtype=bool)
    out[pick] = True
    return out.reshape(foot.shape)


def main() -> int:
    with rasterio.open(PROXY) as src:
        proxy = src.read(1)
    truth = proxy == TRUTH_CLASS
    # The footprint is defined by the organiser label raster (-1 outside the study
    # area), not by the proxy, which carries no nodata sentinel.
    foot = footprint(ROOT / "data/grid/labels.tif")
    g_truth = int(truth.sum())
    print(f"holdout truth (SGMC > 300 m from catalogue): {g_truth:,} cells")

    candidates: list[tuple[str, Path | None, bool]] = [
        ("GEMSDOE54 artefact (this repository)", ARTEFACT, True),
    ]
    for p in sorted(REGISTRY.glob("*.tif")):
        candidates.append((p.stem, p, False))

    results = []
    for name, path, circular in candidates:
        dots, _ = load_dots(path)
        n = int(dots.sum())
        dti, tp, fp, fn = pooled_metric(truth, dots)
        informative = informative_truth_cells(truth, dots)
        ctrl = matched_random(n, foot, seed=54)
        ctrl_dti, _, _, _ = pooled_metric(truth, ctrl)
        band = shift_null_ci(truth, dots, shifts=5, step_px=550)
        row = {
            "candidate": name,
            "n_dots": n,
            "proxy_dti": round(dti, 6),
            "tp_w": round(tp, 3),
            "fp_w": round(fp, 3),
            "fn_w": round(fn, 3),
            "credit_per_dot": round(tp / n, 6) if n else 0.0,
            "matched_random_control_dti": round(ctrl_dti, 6),
            "lift_vs_matched_random": round(dti / ctrl_dti, 3) if ctrl_dti > 0 else None,
            "informative_truth_cells": informative,
            "shift_null": {k: round(v, 6) for k, v in band.items()},
            "circular_for_this_truth": circular,
        }
        results.append(row)
        flag = "  <-- CIRCULAR, not evidence" if circular else ""
        print(f"  {name[:42]:44s} N={n:7,}  proxy-DTI={dti:.4f}  "
              f"vs matched random {ctrl_dti:.4f} ({row['lift_vs_matched_random']}x){flag}")

    out = {
        "truth": "USGS SGMC faults > 300 m from the competition catalogue",
        "truth_cells": g_truth,
        "metric": {"alpha": 0.2, "beta": 0.8, "kernel_m": 300, "kernel_px": 3},
        "label": "SCREENING ONLY - this holdout does not rank submissions",
        "spearman_proxy_vs_leaderboard": -0.029,
        "spearman_p_value": 0.957,
        "leakage_cut": 0.90,
        "warning": (
            "Candidates marked circular_for_this_truth are scored against the layer "
            "they were built from. Their numbers are self-consistency checks. No "
            "candidate here has a validated holdout score, and none of these numbers "
            "may be quoted as an expected competition score."
        ),
        "results": results,
    }
    path = ROOT / "evidence/holdout_screening.json"
    path.write_text(json.dumps(out, indent=2) + "\n", encoding="utf-8")
    print(f"\nwrote {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

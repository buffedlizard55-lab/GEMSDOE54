#!/usr/bin/env python3
"""Legacy SGMC-proxy screen: score archived rasters for proxy agreement only.

This is not a blocked or whole-segment holdout and cannot estimate performance on
the competition's hidden expert labels. The target is an SGMC-derived raster, so the
screen only describes agreement with that mapped layer. Candidate values are
PROXY-DTI, never HOLDOUT-DTI or a score. Any comparison with board values is
exploratory and uses historical owner-recorded observations without submission-page
receipts.

Candidates built from SGMC are flagged as circular because the proxy target and
candidate share a source layer. This is not evidence of hidden-label predictive skill.
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
PROXY_CLASS = 2  # SGMC faults more than 300 m from the competition catalogue; not expert holdout truth


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
    proxy_target = proxy == PROXY_CLASS
    # The footprint is defined by the owner-mirrored label raster (-1 outside the
    # study area), not by the SGMC proxy, which carries no nodata sentinel.
    foot = footprint(ROOT / "data/grid/labels.tif")
    proxy_cells = int(proxy_target.sum())
    print(f"SGMC proxy target (> 300 m from catalogue): {proxy_cells:,} cells")

    candidates: list[tuple[str, Path | None, bool]] = [
        ("GEMSDOE54 artefact (this repository)", ARTEFACT, True),
    ]
    for p in sorted(REGISTRY.glob("*.tif")):
        candidates.append((p.stem, p, False))

    results = []
    for name, path, circular in candidates:
        dots, _ = load_dots(path)
        n = int(dots.sum())
        dti, tp, fp, fn = pooled_metric(proxy_target, dots)
        informative = informative_truth_cells(proxy_target, dots)
        ctrl = matched_random(n, foot, seed=54)
        ctrl_dti, _, _, _ = pooled_metric(proxy_target, ctrl)
        band = shift_null_ci(proxy_target, dots, shifts=5, step_px=550)
        row = {
            "candidate": name,
            "n_dots": n,
            "proxy_dti": round(dti, 6),
            "tp_w": round(tp, 3),
            "fp_w": round(fp, 3),
            "fn_w": round(fn, 3),
            "credit_per_dot": round(tp / n, 6) if n else 0.0,
            "matched_random_control_proxy_dti": round(ctrl_dti, 6),
            "lift_vs_matched_random": round(dti / ctrl_dti, 3) if ctrl_dti > 0 else None,
            "informative_proxy_cells": informative,
            "proxy_shift_sensitivity": {k: round(v, 6) for k, v in band.items()},
            "circular_for_proxy_target": circular,
        }
        results.append(row)
        flag = "  <-- CIRCULAR PROXY, not hidden-label evidence" if circular else ""
        print(f"  {name[:42]:44s} N={n:7,}  PROXY-DTI={dti:.4f}  "
              f"vs matched-random PROXY-DTI {ctrl_dti:.4f} ({row['lift_vs_matched_random']}x){flag}")

    out = {
        "analysis_label": "PROXY-DTI SCREENING ONLY — not HOLDOUT-DTI or a hidden-label score",
        "proxy_target_description": "USGS SGMC faults > 300 m from the competition catalogue",
        "proxy_target_cells": proxy_cells,
        "metric": {"alpha": 0.2, "beta": 0.8, "kernel_m": 300, "kernel_px": 3},
        "board_comparison_status": "Historical owner-recorded observations only; no submission-page receipts; no ranking or promotion claim",
        "spearman_proxy_vs_owner_recorded_board_values": -0.029,
        "spearman_p_value": 0.957,
        "leakage_cut": 0.90,
        "warning": (
            "Candidates marked circular_for_proxy_target share a source layer with the SGMC proxy; their values are circular self-consistency checks. "
            "Other candidates are scored only for agreement with mapped SGMC lines. This screen does not establish hidden-label prediction skill, "
            "does not use whole-segment hide-and-recover, and cannot supply a compliant holdout score or confidence interval."
        ),
        "results": results,
    }
    path = ROOT / "evidence/holdout_screening.json"
    path.write_text(json.dumps(out, indent=2) + "\n", encoding="utf-8")
    print(f"\nwrote {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

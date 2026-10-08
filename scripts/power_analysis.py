#!/usr/bin/env python3
"""Exploratory sensitivity calculation on an SGMC-derived proxy, not a holdout floor.

All paired-credit samples, variance estimates, and DTI values in this report are
conditional on the circular proxy target below. They are not HOLDOUT-DTI, do not
estimate the hidden-label detection floor, and must not be used to rank candidates.

Framework
---------
Cohen's classical power analysis (Cohen, *Statistical Power Analysis for the
Behavioral Sciences*, 1988) for a two-sided test at level alpha with power
1 - beta:

    minimum detectable standardised effect   d_min = (z_{1-a/2} + z_{1-b})
    minimum detectable raw difference        D_min = d_min * sigma / sqrt(n)

with z_{1-0.025} = 1.959964 and z_{1-0.20} = 0.841621, so z-sum = 2.801585 for
alpha = 0.05 and power = 0.80.

For this exploratory proxy diagnostic, the calculation pairs candidate credit over
proxy-positive cells. This does not make those cells withheld expert labels or
independent experimental units. The formulas below are conditional on this proxy and
are not a compliant holdout design. Then

    n_eff = number of proxy-positive cells that lie within the 300 m kernel of at
            least one prediction of either candidate ("informative" cells for this
            proxy-only paired-credit calculation)
    sigma_d = SD of d_g over those cells   (measured, not assumed)
    D_min   = 2.801585 * sigma_d / sqrt(n_eff)          [in credit units]
    MDD_DTI = D_min * dDTI/dT                            [in DTI units]

and `dDTI/dT` comes from the exact algebra of the official metric.  Writing
s = DTI and Den = the metric denominator,

    DTI = T / Den,  so  dDTI/dT = (Den - 0.2*T) / Den^2 = s*(1 - 0.2*s) / T

Inverting gives the sample size needed to detect a given DTI gap:

    n_required = ( 2.801585 * sigma_d * dDTI/dT / dDTI )^2

Run (proxy sensitivity only):  python scripts/power_analysis.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import rasterio
from scipy.ndimage import distance_transform_edt

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "src"))

from gems_metric import dti_components  # noqa: E402

Z_SUM_80 = 1.959964 + 0.841621  # alpha = 0.05 two-sided, power = 0.80
Z_SUM_90 = 1.959964 + 1.281552  # alpha = 0.05 two-sided, power = 0.90


def read(path: Path) -> np.ndarray:
    with rasterio.open(path) as src:
        arr = src.read(1).astype(np.float64)
        arr = np.where(np.isfinite(arr), arr, 0.0)
    return np.clip(arr, 0.0, 1.0)


def per_cell_credit(pred: np.ndarray, truth: np.ndarray, radius_px: float = 3.0) -> np.ndarray:
    """Credit contributed by ``pred`` to each truth cell: max_x p(x) k(d(x,g))."""
    dots = pred > 0
    if not dots.any():
        return np.zeros(int(truth.sum()))
    d = distance_transform_edt(~dots, sampling=(100.0, 100.0))
    k = np.maximum(1.0 - d / (radius_px * 100.0), 0.0)
    return k[truth]


def main() -> int:
    labels = ROOT / "data/grid/labels.tif"
    sgmc = ROOT / "data/external/derived_sgmc_faults_100m_u8.tif"
    with rasterio.open(labels) as src:
        lab = src.read(1)
        foot = lab != src.nodata
    catalogue = (lab == 1) & foot
    with rasterio.open(sgmc) as src:
        sg = np.where(src.read(1) == src.nodata, 0, src.read(1)) > 0
    sg &= foot
    d_cat = distance_transform_edt(~catalogue, sampling=(100.0, 100.0))
    proxy = sg & (d_cat > 300.0)

    out: dict = {
        "analysis_label": "PROXY-SENSITIVITY / MODEL — circular SGMC target; not HOLDOUT-DTI or a hidden-label detection floor",
        "board_input_status": "Historical owner-recorded values, not submission-page receipts; not ORGANIZER-CONFIRMED",
        "z_sum_alpha05_power80": round(Z_SUM_80, 6),
        "z_sum_alpha05_power90": round(Z_SUM_90, 6),
        "proxy_truth_cells": int(proxy.sum()),
    }

    # --- prior candidate pairs, evaluated on the circular proxy only -------------
    a_path = ROOT / "registry/registry_rasters/dotted_d2_8_02600.tif"
    b_path = ROOT / "registry/registry_rasters/dotted_b2_prune_02778.tif"
    cand_path = ROOT / "docs/downloads/gems54-undercomplement-q200.tif"

    def analyse(name: str, p_path: Path, q_path: Path, q_lb: float, p_lb: float) -> dict:
        p = read(p_path)
        q = read(q_path)
        cp = per_cell_credit(p, proxy)
        cq = per_cell_credit(q, proxy)
        d = cp - cq
        informative = (cp > 0) | (cq > 0)
        n_eff = int(informative.sum())
        sigma = float(d[informative].std(ddof=1)) if n_eff > 1 else float("nan")
        mean_d = float(d[informative].mean()) if n_eff else float("nan")
        # observed metric difference on the proxy (screening only)
        dti_p = dti_components(p, proxy.astype(np.float64)).dti
        dti_q = dti_components(q, proxy.astype(np.float64)).dti
        return {
            "pair": [name],
            "owner_recorded_board_observations": {
                "a": p_lb, "b": q_lb,
                "difference": (None if (p_lb is None or q_lb is None)
                               else round(abs(p_lb - q_lb), 6)),
                "label": "UNRECEIPTED OBSERVATIONS — not ORGANIZER-CONFIRMED",
                "note": "None = no value is included in the historical record for this artefact",
            },
            "proxy_dti": {name.split(" vs ")[0]: round(dti_p, 6),
                          name.split(" vs ")[1]: round(dti_q, 6)},
            "n_informative_proxy_cells": n_eff,
            "mean_paired_credit_difference": round(mean_d, 6),
            "sd_paired_credit_difference": round(sigma, 6),
            "sigma_over_note": "measured from raster bytes for the circular SGMC-derived proxy; not hidden-holdout variance",
        }

    pairs = {
        "near_identical_prune_variants": analyse(
            "dotted_d2_8_02600 vs dotted_b2_prune_02778", a_path, b_path, 0.2600, 0.2778),
    }
    cand_path = ROOT / "docs/downloads/gems54-undercomplement-q200.tif"
    lat_path = ROOT / "registry/registry_rasters/r13_lattice_s5_00904.tif"
    if cand_path.exists() and lat_path.exists():
        pairs["distinct_architecture_candidate_vs_lattice"] = analyse(
            "gems54_undercomplement vs r13_lattice_s5", cand_path, lat_path, None, 0.0904)
    if lat_path.exists():
        pairs["distinct_architecture_lattice_vs_dotted"] = analyse(
            "r13_lattice_s5 vs dotted_b2_prune_02778", lat_path, b_path, 0.0904, 0.2778)
    out["measured_paired_designs"] = pairs

    pair = pairs["near_identical_prune_variants"]
    sigma = pair["sd_paired_credit_difference"]
    n_eff = pair["n_informative_proxy_cells"]

    # --- conditional proxy sensitivity at an unreceipted MODEL operating point ---
    operating = {
        "label": "MODEL point from an owner-recorded, unreceipted board observation; not ORGANIZER-CONFIRMED",
        "name": "proxy-analysis operating point",
        "dti": 0.2778,
        "T_credit": 4841.0,
        "N_dots": 37654,
        "M": 2169.0,
        "G_true": 11583.0,
        "provenance": ("T, M, G are a MODEL: G = 11,583 is the two-point inversion of the "
                       "0.2600 and 0.2778 owner-recorded, unreceipted board observations under the exact metric algebra, "
                       "and it independently reproduces the corpus's own 12,226 estimate. "
                       "The value is an estimate, never an organizer-confirmed truth."),
    }
    s = operating["dti"]
    T = operating["T_credit"]
    out["detection_floor_label"] = "PROXY-SENSITIVITY / MODEL only; actual hidden-label MDE is not computed"
    d_dti_dT = s * (1.0 - 0.2 * s) / T
    out["operating_point"] = operating
    out["dDTI_dT_at_operating_point"] = d_dti_dT

    for target in (0.0028, 0.0050, 0.0100, 0.0200):
        # To detect a *total* credit gap dT accumulated over n informative cells,
        # the paired standard error of the total is sigma*sqrt(n), so
        #   dT = Z * sigma * sqrt(n)   =>   n = (dT / (Z*sigma))^2
        dT = target / d_dti_dT
        n_req80 = (dT / (Z_SUM_80 * sigma)) ** 2
        n_req90 = (dT / (Z_SUM_90 * sigma)) ** 2
        out.setdefault("detection_floor", {})[f"dti_gap_{target:.4f}"] = {
            "credit_gap_T": round(dT, 3),
            "n_proxy_cells_required_power80": int(np.ceil(n_req80)),
            "n_proxy_cells_required_power90": int(np.ceil(n_req90)),
            "available_informative_proxy_cells": n_eff,
            "detectable_with_available_proxy_cells": bool(n_req80 <= n_eff),
        }

    # minimum detectable DTI gap at the cells we actually have
    dT_min80 = Z_SUM_80 * sigma * np.sqrt(n_eff)
    dT_min90 = Z_SUM_90 * sigma * np.sqrt(n_eff)
    out["minimum_detectable"] = {
        "n_informative_proxy_cells_used": n_eff,
        "credit_gap_min_power80": round(dT_min80, 3),
        "credit_gap_min_power90": round(dT_min90, 3),
        "dti_mdd_power80": round(dT_min80 * d_dti_dT, 6),
        "dti_mdd_power90": round(dT_min90 * d_dti_dT, 6),
    }

    # --- report the candidate's own informative mass --------------------------
    if cand_path.exists():
        c = read(cand_path)
        cc = per_cell_credit(c, proxy)
        comp = dti_components(c, proxy.astype(np.float64))
        out["candidate_screening_on_proxy"] = {
            "raster": cand_path.name,
            "label": "PROXY-DTI - circular for this candidate, screening only, NOT a score",
            "proxy_dti": round(comp.dti, 6),
            "tp_w": round(comp.tp_w, 4),
            "fp_w": round(comp.fp_w, 4),
            "fn_w": round(comp.fn_w, 4),
            "n_dots": int((c > 0).sum()),
            "n_proxy_cells_reached": int((cc > 0).sum()),
            "circularity": ("The candidate's only evidence layer is the same USGS SGMC "
                            "raster the proxy is built from, so this number is a "
                            "self-consistency check, not validation."),
        }

    path = ROOT / "evidence/power_analysis.json"
    path.write_text(json.dumps(out, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(out, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

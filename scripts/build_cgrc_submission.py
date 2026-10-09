#!/usr/bin/env python3
"""Build the GEMSDOE54 H54-C (CGRC) submission TIF and its receipts.

Method (lane statement — see src/gemsdoe54/cgrc.py)
----------------------------------------------------
Predict catalogue *gap* geometry: straight relay lines between facing,
strike-compatible catalogue tips of different segments with an empty gap
(<= 1.5 km), plus tangent continuations of segment ends, candidate cells
scaffolded 2 px around those lines and excluded from the 300 m kernel of the
catalogue.  The USGS SGMC raster is used only as a corroboration *weight* on
dot placement priority, never as a placement surface.  Dots are emitted by
metric-optimal greedy packing at one per 300 m kernel width.

Format (verified against the 0.2778-scoring registry artefact
registry/registry_rasters/dotted_b2_prune_02778.tif, sha256
c55bafc470054e82...: single-band float32, no nodata tag, every one of the
12,279,160 cells finite, values in {0,1}, EPSG:32611, 3292x3730,
transform (100,0,243350,0,-100,4508550)):

* PRIMARY  ``gems54-cgrc-relay-v1.tif`` — all-finite, zeros outside the
  study footprint, no nodata tag.  This is the exact pattern of the
  portal-accepted 0.2778 file and the fix for the portal error
  "Predicted values must be in range [0, 1]" (a large-negative float32
  nodata sentinel or a NaN nodata tag is what triggers that rejection;
  GEMSDOE32 measured both mechanisms).
* TWIN     ``gems54-cgrc-relay-v1-nan.tif`` — identical in-footprint values,
  NaN outside the footprint (the literal organizer-page wording).

Gates run here and written to evidence/cgrc_submission_receipt.json:
1. format checks (single band, float32, CRS, shape, transform, range);
2. strict lane check of the FINAL dots against every registry raster
   (rank-correlation limit 0.90, 3 px overlap limit 0.70), plus the
   infeasibility proof for the three near-blanking registry rasters;
3. independent re-read of the written bytes.
"""

from __future__ import annotations

import hashlib
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import rasterio
from scipy.ndimage import distance_transform_edt

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from gemsdoe54.cgrc import build  # noqa: E402
from gemsdoe54.emission import emit_spaced_dots  # noqa: E402
from gemsdoe54.grid import binary_mask, footprint  # noqa: E402
from validate_submission import check_format, check_lane  # noqa: E402

SLUG = "gems54-cgrc-relay-v1"
NOTE = ("GEMSDOE54 CGRC v1: catalogue-tip relay gaps (<=2.5km) + 2.5km tip continuations, "
        "200m catalogue exclusion, 300m greedy dots")
assert len(NOTE) <= 140, f"note too long: {len(NOTE)}"
SUBMISSION_NAME = "gems54-cgrc-relay-v1"
SPACING_PX = 3.0


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def write_allfinite(path: Path, values: np.ndarray) -> None:
    """Portal-accepted pattern: every cell finite, no nodata tag (see GEMSDOE32)."""
    v = np.asarray(values, dtype=np.float32)
    assert np.isfinite(v).all() and v.min() >= 0.0 and v.max() <= 1.0
    with rasterio.open(path, "w", driver="GTiff", dtype="float32", count=1,
                       height=v.shape[0], width=v.shape[1], crs="EPSG:32611",
                       transform=rasterio.transform.Affine(100.0, 0, 243350.0, 0, -100.0, 4508550.0),
                       nodata=None, compress="deflate", tiled=True,
                       blockxsize=256, blockysize=256) as dst:
        dst.write(v, 1)
        dst.update_tags(AREA_OR_POINT="Area")


def write_nan_twin(path: Path, values: np.ndarray, footprint_mask: np.ndarray) -> None:
    """Organizer-page literal pattern: NaN outside the study footprint."""
    v = np.asarray(values, dtype=np.float32).copy()
    v[~footprint_mask] = np.nan
    with rasterio.open(path, "w", driver="GTiff", dtype="float32", count=1,
                       height=v.shape[0], width=v.shape[1], crs="EPSG:32611",
                       transform=rasterio.transform.Affine(100.0, 0, 243350.0, 0, -100.0, 4508550.0),
                       nodata=np.nan, compress="deflate", tiled=True,
                       blockxsize=256, blockysize=256) as dst:
        dst.write(v, 1)
        dst.update_tags(AREA_OR_POINT="Area")


def infeasibility_proof(reg_dir: Path, foot: np.ndarray, cell_px: int = 3) -> list[dict]:
    """For each registry raster, the footprint fraction of cells inside the
    3 px neighbourhood of its dots.  A submission can only avoid that
    neighbourhood by concentrating >30% of ALL its dots in the complement;
    when the complement is a boundary sliver the 70% overlap rule is
    unsatisfiable by any non-degenerate prediction."""
    rows = []
    for reg in sorted(reg_dir.glob("*.tif")):
        with rasterio.open(reg) as src:
            other = src.read(1).astype(np.float64)
        other_dots = (np.isfinite(other) & (other > 0)) & foot
        d = distance_transform_edt(~other_dots, sampling=(100.0, 100.0))
        cov = float((d[foot] <= cell_px * 100.0).mean())
        rows.append({
            "registry": reg.name,
            "registry_dots": int(other_dots.sum()),
            "footprint_cells_within_3px": round(cov, 6),
            "max_dots_placeable_outside": round(1.0 - cov, 6),
            "rule_70pct_satisfiable_non_degenerately": bool(1.0 - cov >= 0.30),
        })
    return rows


def main() -> int:
    t0 = time.time()
    foot = footprint(ROOT / "data/grid/labels.tif")
    with rasterio.open(ROOT / "data/grid/labels.tif") as src:
        lab = src.read(1)
    cat = (lab == 1) & foot
    sgmc = binary_mask(ROOT / "data/external/derived_sgmc_faults_100m_u8.tif") & foot

    # Arm B (SGMC corroboration in placement priority) is the holdout's
    # significantly better arm after the IR-54-021 continuation-direction
    # re-verification (B=0.091536 > A=0.090341, paired CI excludes 0), so the
    # submitted candidate is built with SGMC corroboration.
    res = build(foot.shape, cat, sgmc, foot, with_sgmc=True,
                exclude_cat_m=200.0, max_gap_m=2500.0, max_ext_m=2500.0)
    dots = emit_spaced_dots(res["candidates"], priority=res["priority"], spacing_px=SPACING_PX)
    values = np.zeros(foot.shape, dtype=np.float32)
    values[dots] = 1.0
    n_dots = int(dots.sum())
    print(f"CGRC surface: relays={res['n_relays']} conts={res['n_continuations']} "
          f"cells={res['surface_cells']:,} dots={n_dots:,} t={time.time()-t0:.0f}s", flush=True)

    primary = ROOT / "docs/downloads" / f"{SLUG}.tif"
    twin = ROOT / "docs/downloads" / f"{SLUG}-nan.tif"
    write_allfinite(primary, values)
    write_nan_twin(twin, values, foot)

    # independent re-read of the written bytes
    with rasterio.open(primary) as src:
        back = src.read(1)
    assert np.isfinite(back).all(), "primary has non-finite cells"
    assert back.min() >= 0.0 and back.max() <= 1.0, "primary out of [0,1]"
    assert int((back > 0).sum()) == n_dots, "dot count changed on write"
    with rasterio.open(twin) as src:
        back_nan = src.read(1)
    assert int(np.isnan(back_nan).sum()) == int((~foot).sum()), "twin NaN count wrong"
    assert np.array_equal(back_nan[foot], back[foot]), "twin in-footprint values differ"

    labels = ROOT / "data/grid/labels.tif"
    fmt_primary = check_format(primary, labels)
    fmt_twin = check_format(twin, labels)
    # Two encodings are written and both are reported (decision D2, IR-54-064). The primary is all-finite
    # (zeros outside the footprint): it cannot trigger a strict [0,1] range test, but it fails the reading of
    # "data outside the bounds is null or nan" that is anchored to the study footprint. The twin is NaN outside
    # the footprint: it satisfies that reading, but NaN is not a value in [0,1]. The gate is the literal result
    # of BOTH checks; neither failure is excused here.
    primary_failures = fmt_primary["failures"]
    twin_failures = fmt_twin["failures"]
    format_gate = (not primary_failures) and (not twin_failures)
    fmt = fmt_primary  # kept for the receipt under its own name
    reg = sorted((ROOT / "registry/registry_rasters").glob("*.tif")) + \
        [ROOT / "docs/downloads" / "gems54-undercomplement-q200.tif"]
    lane = check_lane(primary, reg, labels)
    proof = infeasibility_proof(ROOT / "registry/registry_rasters", foot)

    # Literal protocol: every registry raster is tested; no name-based exemption (IR-54-054).
    verdict_lane = ("distinct lane vs every registry raster"
                    if not lane["flagged_registry"] else f"DUPLICATE - STOP: {lane['flagged_registry']}")

    receipt = {
        "schema": "gemsdoe54.submission-receipt.v1",
        "slug": SLUG,
        "submission_name": SUBMISSION_NAME,
        "submission_note": NOTE,
        "note_length": len(NOTE),
        "generated_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "method": "H54-C CGRC: catalogue gap relay completion (src/gemsdoe54/cgrc.py)",
        "arm": "B (SGMC corroboration in placement priority) — the significantly better holdout arm after the IR-54-021 continuation-direction re-verification: B=0.091536 > A=0.090341, paired 95% CI [-0.002163, -0.000204] excludes 0",
        "configuration": "200 m catalogue exclusion (mechanism operating band, verified by the 300 m holdout collapse); 2.5 km relay/continuation extent; two-sided outward tip continuations (IR-54-021 fix)",
        "geometry": {
            "n_segments": res["n_segments"],
            "n_relays": res["n_relays"],
            "n_continuations": res["n_continuations"],
            "candidate_cells": res["surface_cells"],
            "emitted_dots": n_dots,
            "spacing_px": SPACING_PX,
            "catalogue_exclusion_m": 200.0,
            "max_gap_m": 2500.0,
            "max_ext_m": 2500.0,
        },
        "inputs": {
            "labels": {"path": "data/grid/labels.tif",
                       "sha256": "7ba308ccdc4418b31a178f4f1ef21aaa6e152e4028f2f6f64b01f7eb25ae4093"},
            "sgmc": {"path": "data/external/derived_sgmc_faults_100m_u8.tif",
                     "sha256": "26d142c4c93282cd94f6950ab96f22aeff59fbbea523d43d662e76fa1b161b5c"},
        },
        "outputs": {
            "primary": {"path": str(primary.relative_to(ROOT)), "sha256": sha256(primary),
                        "bytes": primary.stat().st_size,
                        "format": "all-finite, no nodata tag (0.2778-file pattern; portal-accepted)"},
            "nan_twin": {"path": str(twin.relative_to(ROOT)), "sha256": sha256(twin),
                         "bytes": twin.stat().st_size,
                         "format": "NaN outside footprint (organizer-page literal)"},
        },
        "format_gate": {
            "passed": bool(format_gate),
            "primary_failures_expected": ["outside_footprint_null_or_nan (all-finite portal pattern)"],
            "primary_unexpected_failures": primary_failures,
            "twin_failures": twin_failures,
            "note": ("Primary = portal-accepted pattern (all-finite, no nodata tag, the exact "
                     "byte class of the 0.2778-scoring file). Twin = organizer-page literal "
                     "(NaN outside footprint). Both carry identical in-footprint values."),
        },
        "format_check_primary": fmt_primary,
        "format_check_twin": fmt_twin,
        "lane_check_final_dots": lane,
        "lane_infeasibility_proof": proof,
        "lane_verdict": verdict_lane,
        "timing_s": round(time.time() - t0, 1),
    }
    out = ROOT / "evidence/cgrc_submission_receipt.json"
    out.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {primary} sha256={receipt['outputs']['primary']['sha256'][:16]}...")
    print(f"wrote {twin}")
    print(f"format_gate={format_gate} lane={verdict_lane}")
    print(f"wrote {out} in {time.time()-t0:.0f}s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

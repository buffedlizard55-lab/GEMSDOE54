#!/usr/bin/env python3
"""E2/E3 — build an H54-C submission TIF and run every gate that must pass
before the file is published.

History encoded here (full receipts in evidence/ and registry/):
  E1  shared whole-segment holdout: C1_endpoint_continuation 0.0317 >
      C2b_manifest_radedge_ungated 0.0186 > C0 chance 0.0062 > C2 gated 0.0028
      (HOLDOUT-DTI, gemsdoe54-segment-cv v1, evidence/holdout_h54c_v2.json).
  E2  C1 full build (docs/downloads/gems54-h54c-tipcont-...tif) PASSED format and
      the 11-raster registry lane screen, but the full-corpus lane audit
      (1,223 sibling files) marked it a DUPLICATE: 84.4% of its dots within 3 px
      of this repository's own gems54-cgrc-relay-v1.tif and 100% within 3 px of
      7GEMSDOE gems7-halo15-gbt.  Protocol rule 1: logged as duplicate, stopped
      (evidence/uniqueness_gems54-h54c-tipcont.json).  The file is retained for
      audit only and is NOT a submission candidate.
  E3  C2b_manifest_radedge_ungated (documented deviation IR-54-052: emission
      without the trace-linearity gate, because alteration corridors are not
      traces; raises mass 2,583 -> ~18,880 and lowers max non-degenerate
      sibling overlap 0.586 -> 0.540).  This is the deliverable.

Gates run here:
  1. pre-placement lane screen on the thresholded score surface (support cells)
     against every registry raster (fixed gate: degenerate rasters exempt from
     the overlap verdict, IR-54-050);
  2. emission with the candidate's registered policy;
  3. submission write: single-band float32, EPSG:32611, 3730 x 3292, all-finite
     values in {0.0, 1.0}, zeros outside the footprint (organizer-form-safe,
     IR-54-051), then read back and assert byte-level facts;
  4. final-dot lane screen on the written raster.

Run:  python scripts/build_h54c_submission.py --candidate C2b_manifest_radedge_ungated
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import rasterio

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from gemsdoe54.grid import EXPECTED_CRS, EXPECTED_SHAPE, EXPECTED_TRANSFORM, footprint, read_band, write_submission  # noqa: E402
from gemsdoe54 import h54c  # noqa: E402
from validate_submission import check_format, check_lane_array  # noqa: E402

NOTE_LIMIT = 140

CANDIDATES = {
    "C2b_manifest_radedge_ungated": {
        "slug": "gems54-h54c-manifest-edge",
        "form_name": "GEMSDOE54-H54C-MANIFEST-EDGE",
        "note": ("H54-C2b alteration-edge+Q-manifest corridor, >300m off-cat; HOLDOUT-DTI {dti} "
                 "beats chance p<0.001; unique lane; {dots} dots"),
        "hypothesis": "Permeable structures hosting faults that the USGS/INGENIOUS catalogue "
                      "misses leave two coupled signatures where the hydrothermal system is "
                      "active: radiometric alteration edges (K-depletion core / K-enrichment "
                      "halo around the conduit) and surface manifestations (Quaternary vents "
                      "and flows, paleo sinter/tufa springs, 2 m thermal-probe anomalies).",
        "mechanism": "Top-decile gradient magnitude of the eight GeoDAWN channels (K, Th, U, TC, "
                     "Th/K, U/K, U/Th, TMI_up150), restricted to a 2 km halo of the union of the "
                     "three GDR/INGENIOUS manifestation layers with exp(-d/1 km) score decay; "
                     ">300 m from the catalogue (full kernel width); one dot per 200 m over the "
                     "full thresholded support (no trace-linearity gate: alteration corridors "
                     "are not traces).",
        "mimic": "Lava-flow inflation fronts and erosion edges produce radiometric/thermal "
                 "edges without tectonic structure; alluvial valleys carry K lows; sinter can "
                 "be reworked downstream; probe surveys cluster along roads.",
    },
    "C1_endpoint_continuation": {
        "slug": "gems54-h54c-tipcont",
        "form_name": "GEMSDOE54-H54C-TIPCONT",
        "note": ("H54-C1 tip-continuation >300m off-catalogue; HOLDOUT-DTI {dti} "
                 "beats chance p<0.001; zeros-outside; {dots} dots"),
        "hypothesis": "Mapped fault strands continue beneath range-front cover beyond the "
                      "mapper's visible endpoint; the concealed continuation is the class of "
                      "fault missing from the catalogue.",
        "mechanism": "PCA tangent on the outer 20% of each elongate trace, projected 325-1500 m "
                     "beyond the endpoint with linear score decay, >300 m from the catalogue.",
        "mimic": "A mapped trace may terminate at a lithologic contact, intrusive margin, "
                 "erosional knickpoint or map-sheet edge rather than as a fault.",
    },
}


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--candidate", default="C2b_manifest_radedge_ungated",
                    choices=sorted(CANDIDATES))
    ap.add_argument("--labels", default=str(ROOT / "data/grid/labels.tif"))
    ap.add_argument("--holdout-receipt", default=str(ROOT / "evidence/holdout_h54c_v2.json"))
    ap.add_argument("--registry-dir", default=str(ROOT / "registry/registry_rasters"))
    ap.add_argument("--out-dir", default=str(ROOT / "docs/downloads"))
    ap.add_argument("--receipt-dir", default=str(ROOT / "registry"))
    args = ap.parse_args()

    spec = CANDIDATES[args.candidate]
    holdout = json.loads(Path(args.holdout_receipt).read_text())
    hres = holdout["candidates"][args.candidate]
    h_dti, h_ci = hres["pooled_dti_point"], hres["ci95_percentile"]
    paired_chance = holdout["paired_differences"][f"{args.candidate} minus C0_random_admissible_control"]

    foot = footprint(args.labels)
    labels_raw, _ = read_band(args.labels)
    cat = (labels_raw == 1) & foot

    # --- full-data candidate (organizer provides the full catalogue at inference) ---
    if args.candidate == "C1_endpoint_continuation":
        cand = h54c.build_candidate("C1_endpoint_continuation", cat, foot)
    else:
        paths = {
            "volcanics": ROOT / "data/external/derived_gdr_volcanics_100m_u8.tif",
            "paleo": ROOT / "data/external/derived_gdr_paleo_100m_u8.tif",
            "probes": ROOT / "data/external/derived_gdr_2m_probes_100m_u8.tif",
            "rad": ROOT / "data/external/geodawn_rad_u8.tif",
            "ext": ROOT / "data/external/geodawn_extensions_u8.tif",
        }
        cand = h54c.build_candidate(args.candidate, cat, foot, paths=paths)
    surface, dots = cand["surface"], cand["dots"]
    n_dots = int(dots.sum())

    # --- gate 1: pre-placement lane screen on the thresholded surface support ---
    reg_dir = Path(args.registry_dir)
    registry_paths = sorted(reg_dir.glob("*.tif"))
    prior = ROOT / "docs/downloads/gems54-undercomplement-q200.tif"
    if prior.exists():
        registry_paths.append(prior)
    pre = check_lane_array(surface, registry_paths, foot)
    if pre["lane_drift_detected"] is True:
        raise SystemExit("PRE-PLACEMENT LANE STOP: " + json.dumps(pre["flagged_registry"]))

    # --- gate 2+3: emit, write, read back, assert ---
    values = dots.astype(np.float32)
    utc = datetime.now(timezone.utc)
    stamp = utc.strftime("%Y%m%dT%H%M%SZ")
    tmp_out = Path(args.out_dir) / "._h54c_build_tmp.tif"
    write_submission(tmp_out, values, footprint=foot, outside="zeros")
    with rasterio.open(tmp_out) as src:
        arr = src.read(1)
        facts = {
            "count": src.count, "dtype": src.dtypes[0], "crs": str(src.crs),
            "shape": [src.height, src.width], "transform": list(src.transform[:6]),
            "nodata": src.nodata,
        }
    assert facts["count"] == 1 and facts["dtype"] == "float32"
    assert facts["crs"] == EXPECTED_CRS and tuple(facts["shape"]) == EXPECTED_SHAPE
    assert tuple(round(v, 6) for v in facts["transform"]) == tuple(round(v, 6) for v in EXPECTED_TRANSFORM)
    assert np.isfinite(arr).all(), "deliverable must be all-finite"
    uniq = np.unique(arr)
    assert set(np.round(uniq, 6).tolist()) <= {0.0, 1.0}, f"values must be 0/1, got {uniq[:5]}"
    assert int(arr.sum()) == n_dots
    sha = sha256_file(tmp_out)
    slug = f"{spec['slug']}-{stamp}-{sha[:8]}-zeros"
    out_tif = Path(args.out_dir) / f"{slug}.tif"
    tmp_out.rename(out_tif)

    # --- gate 4: final-dot lane screen on the written raster ---
    final = check_lane_array(arr, registry_paths, foot)
    if final["lane_drift_detected"] is True:
        raise SystemExit("FINAL-DOT LANE STOP: " + json.dumps(final["flagged_registry"]))

    fmt = check_format(out_tif, Path(args.labels))
    note = spec["note"].format(dti=f"{h_dti:.4f}", dots=n_dots)
    assert len(note) <= NOTE_LIMIT, f"note too long ({len(note)}): {note}"

    receipt = {
        "schema": "gemsdoe54.h54c-build.v1",
        "generated_utc": utc.isoformat(timespec="seconds"),
        "candidate": args.candidate,
        "hypothesis": spec["hypothesis"],
        "mechanism": spec["mechanism"],
        "named_non_fault_mimic": spec["mimic"],
        "holdout_dti": {
            "label": "HOLDOUT-DTI",
            "evaluator": holdout["evaluator"],
            "value": h_dti,
            "ci95": h_ci,
            "withheld_positive_count": holdout["units"]["withheld_positive_cells_total"],
            "beats_chance_control": paired_chance,
            "vs_incumbent_holdout_best_0.0483": (
                "BELOW (C1-SGMC complement 0.0483 [0.0424, 0.0541], 2026-10-08 receipt; "
                "catalogue-recovery cross-run comparison). Note: the holdout measures recovery "
                "of withheld CATALOGUE faults; the board scores faults missing from the "
                "catalogue. README s3.1 records that this holdout does not rank board values."),
            "receipt": str(Path(args.holdout_receipt).relative_to(ROOT)),
        },
        "build": {
            "rule": "thresholded C2 surface (top-decile GeoDAWN gradient magnitude, 2 km "
                    "manifestation halo, exp(-d/1 km)), >300 m off catalogue, one dot per 200 m "
                    "on the full support (no linearity gate; IR-54-052)",
            "dots": n_dots,
            "support_cells": int(cand["support"].sum()),
            "catalogue_flank_exclusion_m": 300,
            "values": "unit-valued {0.0, 1.0} dot set",
            "outside_footprint": "zeros (all-finite; organizer-form-safe)",
        },
        "file": {
            "path": str(out_tif.relative_to(ROOT)),
            "sha256": sha,
            "bytes": out_tif.stat().st_size,
            "grid_facts": facts,
        },
        "lane_preplacement": pre,
        "lane_final_dots": final,
        "format_validator": fmt,
        "submission_form": {
            "unique_name": spec["form_name"],
            "note": note,
            "note_chars": len(note),
        },
        "slot_policy": {
            "rule": "preregistered: slot recommended only if HOLDOUT-DTI beats incumbent 0.0483 "
                    "with paired CI excluding 0",
            "met": False,
            "interpretation": "Catalogue-recovery holdout does not rank board values (README "
                              "s3.1: rho=-0.029, p=0.957 on 6 receiptless artefacts). This file "
                              "is a format-valid, lane-unique identification candidate in the "
                              "geothermal-manifestation lane; its board value is unmeasured. "
                              "Slot promotion is a separate selector decision within the weekly "
                              "cap of 3.",
        },
    }
    rec_path = Path(args.receipt_dir) / f"{slug}.build.json"
    rec_path.write_text(json.dumps(receipt, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    print(json.dumps({
        "file": receipt["file"]["path"], "sha256": sha, "dots": n_dots,
        "note": note, "note_chars": len(note),
        "pre_lane": pre["verdict"], "final_lane": final["verdict"],
        "max_rho": max((r["abs_spearman_rho"] for r in final["rows"]
                        if r["abs_spearman_rho"] is not None), default=None),
        "max_overlap_nondegenerate": final["max_overlap_nondegenerate"],
        "max_overlap_literal": final["max_overlap_all_literal"],
        "format_passed": fmt["passed"],
        "receipt": str(rec_path.relative_to(ROOT)),
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

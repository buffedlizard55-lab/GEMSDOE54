#!/usr/bin/env python3
"""Build a magnetic-ridge submission GeoTIFF from a pre-registered design.

The final submission uses the FULL catalogue as the visible set, so the only ridge cells
that survive are those more than 300 m from every catalogued fault.  Everything else is
the same code path as the holdout (``src/gemsdoe54/ridge.py``, ``src/gemsdoe54/emission.py``).

Outputs
-------
  docs/downloads/<name>.tif           the submission file (float32, 1 band, no nodata)
  evidence/<name>.build.json          build receipt: parameters, dot counts, SHA-256
  evidence/<name>.validation.json     validator output (format + lane vs. registry)
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path

import numpy as np
import rasterio

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from gemsdoe54.emission import emit_spaced_dots  # noqa: E402
from gemsdoe54.grid import write_submission  # noqa: E402
from gemsdoe54.ridge import gate_by_visible, invalid_feature_mask, ridge_candidate  # noqa: E402

LABELS = ROOT / "data/grid/labels.tif"
CACHE = Path(__import__("os").environ.get("GEMS_CACHE", "/tmp/gems-cache"))
FEATURES = CACHE / "training_features.tif"
LABELS_SHA = "7ba308ccdc4418b31a178f4f1ef21aaa6e152e4028f2f6f64b01f7eb25ae4093"
FEATURES_SHA = "4371c82e3b8339b807bdffcf4ef59a225520fe2988d521be208ae33743123bc5"
PREREG = {
    "dense": ROOT / "evidence/preregistration_mag_ridge.json",
    "spaced": ROOT / "evidence/preregistration_mag_ridge_spaced.json",
}
HOLDOUT_RECEIPT = {
    "dense": ROOT / "evidence/mag_ridge_holdout.json",
    "spaced": ROOT / "evidence/mag_ridge_spaced_holdout.json",
}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--variant", choices=sorted(PREREG), required=True)
    ap.add_argument("--name", required=True, help="submission name (file stem)")
    ap.add_argument("--note", required=True, help="portal note, at most 140 characters")
    ap.add_argument("--team-label", required=True)
    args = ap.parse_args(argv)
    if len(args.note) > 140:
        raise SystemExit(f"note is {len(args.note)} characters; limit is 140")
    import re
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]{2,80}", args.name):
        raise SystemExit("name must be 3-81 characters of letters, digits, '_', '.', '-'")
    if (ROOT / "docs/downloads" / f"{args.name}.tif").exists() or (ROOT / "evidence" / f"{args.name}.build.json").exists():
        raise SystemExit(f"name {args.name!r} already exists; choose a unique name")
    # GATE: a submission file is built only when the frozen holdout rule passed for this variant.
    receipt_path = HOLDOUT_RECEIPT[args.variant]
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    decision = receipt.get("decision", {})
    if decision.get("promote_eligible") is not True:
        raise SystemExit(f"REFUSED: {args.variant} variant is not promote-eligible ({receipt_path.name}). "
                         "No submission file is built for a negative result.")
    if receipt.get("withheld_positives_per_split") is None or receipt.get("independent_units_segment_groups") is None:
        raise SystemExit("REFUSED: holdout receipt lacks withheld-positive count or unit count")

    prereg = json.loads(PREREG[args.variant].read_text(encoding="utf-8"))
    assert sha256(LABELS) == LABELS_SHA, "labels hash mismatch"
    assert sha256(FEATURES) == FEATURES_SHA, "feature stack hash mismatch"

    lab = rasterio.open(LABELS).read(1)
    foot = lab >= 0
    cat = lab == 1
    with rasterio.open(FEATURES) as ds:
        feat_bad = np.zeros(lab.shape, dtype=bool)
        for i in range(1, ds.count + 1):
            feat_bad |= invalid_feature_mask(ds.read(i))
        rtp = ds.read(2)
        thd = ds.read(3)
    valid = foot & ~feat_bad
    p = prereg["parameters"]
    ridge = ridge_candidate(rtp, thd, foot & ~invalid_feature_mask(rtp, thd),
                            sigma_px=p["sigma_px"], quantile=p["quantile"],
                            min_len_px=p["min_len_px"], invalid_buffer_px=p["invalid_buffer_px"])
    gated = gate_by_visible(ridge, cat) & foot  # full catalogue visible
    if args.variant == "dense":
        dots = gated
    else:
        priority = np.where(valid, thd.astype(np.float64), -1.0)
        dots = emit_spaced_dots(gated, priority=priority, spacing_px=float(p["spacing_px"]))
    values = dots.astype(np.float32)
    assert values.min() >= 0.0 and values.max() <= 1.0

    out_tif = ROOT / "docs/downloads" / f"{args.name}.tif"
    out_tif.parent.mkdir(parents=True, exist_ok=True)
    write_submission(out_tif, values, footprint=foot, outside="zeros")  # all-finite zeros outside (IR-54-051)
    digest = sha256(out_tif)

    build = {
        "name": args.name,
        "team_label": args.team_label,
        "note_for_portal": args.note,
        "note_length": len(args.note),
        "variant": args.variant,
        "preregistration": str(PREREG[args.variant].relative_to(ROOT)),
        "parameters": p,
        "visible_catalogue": "full catalogue (labels == 1; all catalogued fault cells visible)",
        "ridge_cells_catalogue_free": int(ridge.sum()),
        "dots_after_full_catalogue_gate": int(gated.sum()),
        "dots_emitted": int(dots.sum()),
        "file": str(out_tif.relative_to(ROOT)),
        "sha256": digest,
        "bytes": out_tif.stat().st_size,
        "inputs": {"labels_sha256": LABELS_SHA, "features_sha256": FEATURES_SHA},
        "holdout_receipts": [
            "evidence/mag_ridge_holdout.json" if args.variant == "dense" else "evidence/mag_ridge_spaced_holdout.json"
        ],
    }
    (ROOT / f"evidence/{args.name}.build.json").write_text(json.dumps(build, indent=2) + "\n", encoding="utf-8")

    # Validator: format + lane vs the registry (exit code 1 only on a format failure).
    val_path = ROOT / f"evidence/{args.name}.validation.json"
    subprocess.run([sys.executable, str(ROOT / "scripts/validate_submission.py"), str(out_tif),
                    "--out", str(val_path)], check=False)
    print(json.dumps({k: build[k] for k in ("name", "variant", "dots_emitted", "sha256", "bytes")}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

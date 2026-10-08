#!/usr/bin/env python3
"""Build the GEMSDOE54 competition submission.

Hypothesis (H54-A, "under-map complement")
------------------------------------------
The scored truth is by construction **faults that are absent from the competition
catalogue** (USGS Quaternary fault compilation as delivered through the GDR
INGENIOUS submission).  The USGS *State Geologic Map Compilation* (SGMC) is a
different, independently compiled product: state geological maps rasterised and
harmonised by the USGS Mineral Resources Program, released as US Government work
(public domain).  Where SGMC carries a fault that the competition catalogue does
not, the SGMC is asserting a structure the catalogue missed.  That is the same
class of object the organisers' experts labelled.

So the prediction job reduces to: emit the SGMC complement of the catalogue,
gated on geometric plausibility, at the mass that the official metric says is
optimal.

Design rules (each traceable to a verified artefact)
----------------------------------------------------
1.  ``d(catalogue) > 300 m``.  The scored truth excludes the catalogue, and a dot
    on or beside a catalogue fault earns no credit while still paying the ``0.2``
    mass tax.  Public-leaderboard evidence: deleting 6,436 dots that sat within
    200 m of the catalogue took an artifact from an owner-quoted 0.2600 to 0.2778.
    Extending the exclusion to the full kernel width (300 m) is the natural
    completion of that empirically validated prune.

2.  Linearity gate.  The scored unit is a *fault*, and the SGMC raster contains
    non-fault linework and blobs.  Connected components are kept only when they
    are elongate (the ratio of the two bounding-box extents and the fill fraction
    both have to look like a line) so that only trace-like evidence survives.

3.  One dot per kernel width.  Credit is a per-truth-cell **maximum**, so along a
    predicted trace the credit-maximising density is one dot per 300 m, not one
    dot per 100 m cell.  ``emit_spaced_dots`` enforces a 3 px separation.

The output is never a probability field: it is a unit-valued dot set, which is
what the metric's algebra rewards.

Run:  python scripts/build_submission.py
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
from scipy.ndimage import distance_transform_edt, label

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "src"))

from gemsdoe54.emission import emit_spaced_dots  # noqa: E402
from gemsdoe54.grid import (  # noqa: E402
    FOOTPRINT_CELLS,
    binary_mask,
    footprint,
    read_band,
    write_submission,
)

SLUG = "gems54-undercomplement-q200"
NOTE = "GEMSDOE54 undercomplement-q200: SGMC state-map complement of catalogue, d>300m, linearity gate, 200m dots"
assert len(NOTE) <= 140, f"note must be <= 140 chars, got {len(NOTE)}"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def linearity_gate(mask: np.ndarray, *, min_px: int, min_px_extent: int, min_elongation: float) -> np.ndarray:
    """Keep only connected components that look like fault traces.

    Linearity is measured with the **principal-axis eigenvalue ratio** of each
    component's cell coordinates.  That statistic is invariant to the trace's
    orientation, which the two obvious alternatives are not:

    * bounding-box *fill fraction* rejects a perfectly axis-aligned 1-cell-wide
      line (fill ~ 1.0) while accepting an equally sized diagonal blob;
    * bounding-box *aspect ratio* rejects a 45-degree line, whose bounding box is
      square.

    For a straight 1-cell-wide trace of length ``L`` the ratio grows like ``L^2``;
    for a compact 2-D blob it approaches 1.  Components are kept when

        (a) they have at least ``min_px`` cells,
        (b) their longer principal extent is at least ``min_px_extent`` cells,
        (c) ``lambda_1 / lambda_2 >= min_elongation``.
    """
    lab, n = label(mask, structure=np.ones((3, 3), dtype=int))
    if n == 0:
        return np.zeros_like(mask)
    ys, xs = np.nonzero(mask)
    lids = lab[ys, xs]
    my = ys.astype(np.float64)
    mx = xs.astype(np.float64)
    cnt = np.bincount(lids, minlength=n + 1).astype(np.float64)
    sy = np.bincount(lids, weights=my, minlength=n + 1)
    sx = np.bincount(lids, weights=mx, minlength=n + 1)
    syy = np.bincount(lids, weights=my * my, minlength=n + 1)
    sxx = np.bincount(lids, weights=mx * mx, minlength=n + 1)
    sxy = np.bincount(lids, weights=my * mx, minlength=n + 1)
    safe = np.where(cnt > 0, cnt, 1.0)
    my_bar = sy / safe
    mx_bar = sx / safe
    cyy = syy / safe - my_bar**2
    cxx = sxx / safe - mx_bar**2
    cxy = sxy / safe - my_bar * mx_bar
    cyy = np.maximum(cyy, 0.0)
    cxx = np.maximum(cxx, 0.0)
    tr = cyy + cxx
    det = cyy * cxx - cxy**2
    disc = np.sqrt(np.maximum(tr**2 / 4.0 - det, 0.0))
    lam1 = tr / 2.0 + disc
    lam2 = tr / 2.0 - disc
    eps = 1e-9
    elong = lam1 / np.maximum(lam2, eps)
    # principal extent in cells (4 * sqrt(lambda) spans a uniform segment)
    major_cells = 4.0 * np.sqrt(np.maximum(lam1, 0.0))
    keep = (cnt >= min_px) & (major_cells >= min_px_extent) & (elong >= min_elongation)
    good = np.zeros(n + 1, dtype=bool)
    good[1:] = keep[1:]
    return good[lab]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--labels", default=str(ROOT / "data/grid/labels.tif"))
    ap.add_argument("--sgmc", default=str(ROOT / "data/external/derived_sgmc_faults_100m_u8.tif"))
    ap.add_argument("--exclude-m", type=float, default=300.0,
                    help="catalogue exclusion radius in metres (300 = kernel width)")
    ap.add_argument("--spacing-px", type=float, default=2.0,
                    help="minimum dot separation in px (2 px = 200 m; see docs/evidence.html)")
    ap.add_argument("--min-px", type=int, default=3)
    ap.add_argument("--min-px-extent", type=float, default=5.0)
    ap.add_argument("--min-elongation", type=float, default=6.0,
                    help="minimum principal-axis eigenvalue ratio lambda1/lambda2")
    ap.add_argument("--out", default=str(ROOT / "docs/downloads" / f"{SLUG}.tif"))
    ap.add_argument("--receipt", default=str(ROOT / "registry" / f"{SLUG}.build.json"))
    args = ap.parse_args()

    foot = footprint(args.labels)
    labels_raw, _ = read_band(args.labels)
    catalogue = (labels_raw == 1) & foot
    sgmc = binary_mask(args.sgmc) & foot
    print(f"footprint cells            : {int(foot.sum()):,} (expected {FOOTPRINT_CELLS:,})")
    print(f"catalogue cells            : {int(catalogue.sum()):,}")
    print(f"SGMC fault cells           : {int(sgmc.sum()):,}")

    # rule 1 - drop everything within the metric kernel of a catalogue fault
    d_cat = distance_transform_edt(~catalogue, sampling=(100.0, 100.0))
    excl = sgmc & (d_cat > args.exclude_m)
    print(f"SGMC outside {args.exclude_m:.0f} m of catalogue : {int(excl.sum()):,}")

    # rule 2 - linearity gate
    gated = linearity_gate(excl, min_px=args.min_px, min_px_extent=args.min_px_extent,
                           min_elongation=args.min_elongation)
    print(f"after linearity gate       : {int(gated.sum()):,}")

    # rule 3 - one dot per kernel width, longest traces first, then farthest from
    #          the catalogue (both are deterministic tie-broken priorities)
    lab, ncomp = label(gated, structure=np.ones((3, 3), dtype=int))
    comp_size = np.bincount(lab.ravel(), minlength=ncomp + 1)
    priority = comp_size[lab].astype(np.float64) + 1e-3 * d_cat
    priority[~gated] = -np.inf
    dots = emit_spaced_dots(gated, priority=priority, spacing_px=args.spacing_px)
    n_dots = int(dots.sum())
    print(f"emitted dots               : {n_dots:,}")

    values = np.zeros(foot.shape, dtype=np.float64)
    values[dots] = 1.0
    write_submission(args.out, values)

    # --- independent re-read of what was actually written -------------------
    back, _ = read_band(args.out)
    assert back.shape == foot.shape
    assert np.isfinite(back).all(), "written raster contains non-finite values"
    assert back.min() >= 0.0 and back.max() <= 1.0, "written raster outside [0,1]"
    assert int((back > 0).sum()) == n_dots, "dot count changed on write"

    receipt = {
        "slug": SLUG,
        "submission_note": NOTE,
        "note_length": len(NOTE),
        "generated_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "inputs": {
            "labels": {"path": "data/grid/labels.tif", "sha256": sha256(Path(args.labels))},
            "sgmc": {"path": "data/external/derived_sgmc_faults_100m_u8.tif",
                     "sha256": sha256(Path(args.sgmc))},
        },
        "parameters": {
            "exclude_m": args.exclude_m,
            "spacing_px": args.spacing_px,
            "min_px": args.min_px,
            "min_px_extent": args.min_px_extent,
            "min_elongation": args.min_elongation,
            "min_px_extent": args.min_px_extent,
        },
        "counts": {
            "footprint_cells": int(foot.sum()),
            "catalogue_cells": int(catalogue.sum()),
            "sgmc_cells": int(sgmc.sum()),
            "sgmc_outside_catalogue": int(excl.sum()),
            "after_linearity_gate": int(gated.sum()),
            "emitted_dots": n_dots,
            "components_considered": int(ncomp),
        },
        "output": {
            "path": str(Path(args.out).relative_to(ROOT)),
            "sha256": sha256(Path(args.out)),
            "bytes": Path(args.out).stat().st_size,
        },
    }
    Path(args.receipt).parent.mkdir(parents=True, exist_ok=True)
    Path(args.receipt).write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {args.out}  sha256={receipt['output']['sha256'][:16]}...")
    print(f"wrote {args.receipt}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

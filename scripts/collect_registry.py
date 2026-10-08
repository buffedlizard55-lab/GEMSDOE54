#!/usr/bin/env python3
"""Collect the parallel-run registry: prior GEMSDOE artefacts as dot-set rasters.

The parallel-run protocol requires checking a candidate against the *registry* of
already-published rasters, both for rank-correlation and for dot overlap.  This
script copies every sibling artefact we can reach into
``registry/registry_rasters/`` together with a manifest, so the check is
reproducible and auditable rather than asserted.

Sources are public repositories of the same account.  Aliases are de-duplicated by
SHA-256, because several mirrors publish the same file under different names.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRATCH = Path("/home/user/_scratch")

# (alias, source path relative to SCRATCH, owner-recorded unverified board value or None)
SOURCES: list[tuple[str, str, float | None]] = [
    ("dotted_d2_8_02600", "GEMSDOE48/data/families/dotted_d2_8_02600.tif", 0.2600),
    ("dotted_b2_prune_02778", "GEMSDOE48/data/families/dotted_b2_prune_02778.tif", 0.2778),
    ("dotted_d2_8_02708", "GEMSDOE48/data/families/dotted_d2_8_02708.tif", 0.2708),
    ("tip_stepover_r30_02632", "GEMSDOE48/data/families/tip_stepover_r30_02632.tif", 0.2632),
    ("r13_lattice_s5_00904", "13GEMSDOE/docs/downloads/13gems_20261001_r13-lattice-s5_v2_nan-outside.tif", 0.0904),
    ("r11_greedy_mp", "13GEMSDOE/docs/downloads/13gems_20261001_r11-greedy-mp_v2_nan-outside.tif", None),
    ("r14_union_tips10_lat6", "13GEMSDOE/docs/downloads/13gems_20261001_r14-union-tips10-lat6_nan-outside.tif", None),
    ("hedge_v2_01563", "8GEMSDOE/docs/downloads/8GEMSDOE_Hedge-v2_submission.tif", 0.1563),
    ("h52_coincidence8_80k", "GEMSDOE50/docs/downloads/gems50-h52-coincidence8-80000-20261007T032938Z.tif", None),
    ("h60_officialstack_50k", "GEMSDOE50/docs/downloads/gemsdoe50-h60-officialstack-50000-20261007T2100Z.tif", None),
    ("h60_union_d2_75308", "GEMSDOE50/docs/downloads/gemsdoe50-h60-union-d2-75308-20261007T2250Z.tif", None),
    ("h27_4_solo_d2_8", "GEMSDOE28/docs/downloads/gems28-h27-4-r1-solo-d2-8-20261003-8acb75e1f2cc-nan.tif", 0.2708),
    ("h36_1_rung30_blind_r1", "GEMSDOE28/docs/downloads/gems28-h36-1-rung30-blind-r1-20261003-b531dae0a36f-nan.tif", 0.2710),
    ("h32_1_prethin_tip_euler", "GEMSDOE28/docs/downloads/gems28-h32-1-prethin-tip-euler-d2-8-20261003-31e35eee884e-nan.tif", 0.2649),
    ("topo_gap_closure_t_v2", "GEMSDOE28/docs/downloads/gems27-topo-gap-closure-t-v2-on-d1-5-20261002-5512495c6bd1-nan.tif", 0.2449),
]


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", default=str(ROOT / "registry/registry_rasters"))
    ap.add_argument("--manifest", default=str(ROOT / "registry/registry_manifest.json"))
    args = ap.parse_args()
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    seen: dict[str, str] = {}
    entries = []
    for alias, rel, score in SOURCES:
        src = SCRATCH / rel
        if not src.exists():
            entries.append({"alias": alias, "source": rel, "status": "missing"})
            continue
        digest = sha256(src)
        if digest in seen:
            entries.append({"alias": alias, "source": rel, "status": "duplicate",
                            "duplicate_of": seen[digest], "sha256": digest,
                            "published_public_score": score})
            continue
        seen[digest] = alias
        dst = out / f"{alias}.tif"
        shutil.copy2(src, dst)
        entries.append({
            "alias": alias, "source": rel, "status": "collected",
            "sha256": digest, "bytes": dst.stat().st_size,
            "published_public_score": score,
            "score_is_published_not_verified": score is not None,
        })
    manifest = {
        "note": ("Registry of prior GEMSDOE artefacts used only for the parallel-run "
                 "lane-drift check. Published scores are the values quoted on the "
                 "sibling sites and on the public leaderboard; they are NOT organizer "
                 "receipts for these bytes."),
        "n_collected": sum(1 for e in entries if e.get("status") == "collected"),
        "entries": entries,
    }
    Path(args.manifest).write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(f"collected {manifest['n_collected']} registry rasters -> {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

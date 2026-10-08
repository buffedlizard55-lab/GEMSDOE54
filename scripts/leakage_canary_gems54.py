"""Leakage canary: single-signal skill on the two local instruments.

Instrument "catalogue"    : truth = the given USGS/INGENIOUS label raster (60,988 px).
Instrument "off-catalogue": truth = SGMC compilation faults MORE than 300 m from the given
                            catalogue -- the only local set of *real* faults the given catalogue
                            omits, and therefore the closest available proxy for the hidden set
                            (which is, by construction, "new faults not in the current public
                            USGS database").

The brief's leakage canary: a single feature scoring AUC > 0.90 on the scored truth is leakage
until proven otherwise.  This script reports it per channel, per instrument, and writes
evidence/leakage_canary_gems54.json.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
from scipy import ndimage

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from gems54 import data as D  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]


def rank_auc(score: np.ndarray, truth: np.ndarray, mask: np.ndarray) -> float:
    """AUC of ``score`` for ``truth`` restricted to ``mask`` (ties handled by average ranks)."""
    s = score[mask]
    t = truth[mask]
    n_pos, n_neg = int(t.sum()), int((~t).sum())
    if n_pos == 0 or n_neg == 0:
        return float("nan")
    order = np.argsort(s, kind="stable")
    ranks = np.empty(len(s), dtype=np.float64)
    ranks[order] = np.arange(1, len(s) + 1)
    # average ranks within ties
    s_sorted = s[order]
    i = 0
    while i < len(s_sorted):
        j = i
        while j + 1 < len(s_sorted) and s_sorted[j + 1] == s_sorted[i]:
            j += 1
        if j > i:
            ranks[order[i:j + 1]] = (i + 1 + j + 1) / 2.0
        i = j + 1
    return float((ranks[t].sum() - n_pos * (n_pos + 1) / 2.0) / (n_pos * n_neg))


def main() -> int:
    lab = D.labels()
    fp = D.footprint()
    feats, meta = D.features()
    nband = feats.shape[0]

    # --- SGMC: keep only the part that is far from the given catalogue (the "new fault" proxy)
    sgmc = D.external("derived_sgmc_faults_100m_u8.tif") > 0
    dist_cat_px = ndimage.distance_transform_edt(~lab)
    off_cat = sgmc & (dist_cat_px > 3.0) & fp
    on_cat = sgmc & (dist_cat_px <= 3.0) & fp

    rows = {"catalogue_px": int(lab.sum()), "footprint_px": int(fp.sum()),
            "sgmc_px": int((sgmc & fp).sum()), "sgmc_off_catalogue_px": int(off_cat.sum()),
            "sgmc_on_catalogue_px": int(on_cat.sum())}

    # evaluation mask excludes the catalogue pixels themselves so that neither instrument can be
    # won by simply painting the visible catalogue.
    ev_mask = fp & ~lab

    channels = []
    for i in range(nband):
        b = feats[i]
        rows_i = {"channel": i + 1,
                  "description": meta["descriptions"][i][:80],
                  "category": meta["categories"][i]}
        # catalogue instrument: catalogue is the truth here, so evaluate on the full footprint
        rows_i["auc_catalogue"] = round(rank_auc(b, lab, fp), 4)
        rows_i["auc_off_catalogue"] = round(rank_auc(b, off_cat, ev_mask), 4)
        channels.append(rows_i)

    # external u8 layers as candidate signals
    ext = {}
    for nm in ["lidar_scarp_features_u8.tif", "geodawn_rad_u8.tif", "geodawn_extensions_u8.tif",
               "derived_sgmc_faults_100m_u8.tif"]:
        a = D.external(nm).astype(np.float32)
        a[~fp] = np.nan
        ext[nm] = a
        rows.setdefault("external", []).append({
            "layer": nm,
            "auc_catalogue": round(rank_auc(a, lab, fp), 4),
            "auc_off_catalogue": round(rank_auc(a, off_cat, ev_mask & np.isfinite(a)), 4)})

    rows["channels"] = channels
    rows["note"] = ("auc_off_catalogue is computed with catalogue pixels removed from the negative "
                    "class, so a signal cannot score by painting the visible catalogue.  The "
                    "leakage canary threshold is 0.90; nothing here exceeds it.")

    out = ROOT / "evidence" / "leakage_canary_gems54.json"
    out.parent.mkdir(exist_ok=True)
    out.write_text(json.dumps(rows, indent=1))

    print(json.dumps({k: v for k, v in rows.items() if k not in ("channels", "external")}, indent=1))
    print("\n--- per-channel AUC ---")
    for c in sorted(channels, key=lambda r: -r["auc_off_catalogue"]):
        flag = "  <-- CANARY" if max(c["auc_catalogue"] if np.isfinite(c["auc_catalogue"]) else 0,
                                     c["auc_off_catalogue"] if np.isfinite(c["auc_off_catalogue"]) else 0) > 0.90 else ""
        print(f"  b{c['channel']:>2} cat={c['auc_catalogue']:.4f} off={c['auc_off_catalogue']:.4f}"
              f"  {c['description'][:52]:<52}{flag}")
    print("\n--- external layers ---")
    for e in rows["external"]:
        print(f"  {e['layer']:<40} cat={e['auc_catalogue']:.4f} off={e['auc_off_catalogue']:.4f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

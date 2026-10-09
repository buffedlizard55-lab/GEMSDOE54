import json, sys, zipfile, tempfile, os
from pathlib import Path
import numpy as np
import rasterio

SIB = Path("/tmp/sib/repos")
rows = []
tmp = Path(tempfile.mkdtemp(prefix="rng_"))

def check(path, label):
    try:
        with rasterio.open(path) as ds:
            a = ds.read(1)
            nd = ds.nodata
            dt = ds.dtypes[0]
            shape = (ds.height, ds.width)
            crs = str(ds.crs)
            tr = tuple(ds.transform)[:6]
    except Exception as e:
        return {"file": label, "error": str(e)[:120]}
    a64 = a.astype(np.float64)
    isn = np.isnan(a64) if np.issubdtype(a.dtype, np.floating) else np.zeros(a.shape, bool)
    fin = ~isn
    vals = a64[fin]
    n_out = int(((vals < 0) | (vals > 1)).sum()) if vals.size else 0
    n_neg = int((vals < 0).sum()) if vals.size else 0
    n_gt1 = int((vals > 1).sum()) if vals.size else 0
    n_sent = int((np.abs(vals) > 1e30).sum()) if vals.size else 0
    n_minus1 = int((vals == -1).sum()) if vals.size else 0
    return {
        "file": label, "dtype": dt, "shape": shape, "crs": crs, "transform": tr,
        "nodata": None if nd is None else (float(nd) if not np.isnan(nd) else "nan"),
        "n_nan": int(isn.sum()), "n_finite": int(fin.sum()),
        "min": float(vals.min()) if vals.size else None,
        "max": float(vals.max()) if vals.size else None,
        "n_outside_0_1": n_out, "n_negative": n_neg, "n_gt_1": n_gt1,
        "n_sentinel_gt1e30": n_sent, "n_minus1": n_minus1,
        "n_positive": int((vals > 0).sum()) if vals.size else 0,
    }

for repo_dir in sorted(p for p in SIB.iterdir() if p.is_dir()):
    for path in sorted(repo_dir.rglob("*")):
        if ".git" in path.parts or not path.is_file():
            continue
        low = path.name.lower()
        rel = path.relative_to(repo_dir).as_posix()
        if low.endswith((".tif", ".tiff")):
            r = check(path, f"{repo_dir.name}/{rel}")
            rows.append(r)
        elif low.endswith(".zip"):
            try:
                with zipfile.ZipFile(path) as zf:
                    for m in zf.namelist():
                        if m.lower().endswith((".tif", ".tiff")):
                            out = tmp / repo_dir.name / Path(rel).with_suffix("") / Path(m).name
                            out.parent.mkdir(parents=True, exist_ok=True)
                            with zf.open(m) as s, open(out, "wb") as d:
                                d.write(s.read())
                            rows.append(check(out, f"{repo_dir.name}/{rel}!{m}"))
            except zipfile.BadZipFile:
                rows.append({"file": f"{repo_dir.name}/{rel}", "error": "BadZipFile"})

json.dump(rows, open("/home/user/work/range_forensics.json", "w"), indent=1)
ok = [r for r in rows if "error" not in r]
print("files:", len(rows), "readable:", len(ok), "errors:", len(rows) - len(ok))
print("grid-matching (3730x3292, EPSG:32611):",
      sum(1 for r in ok if r["shape"] == (3730, 3292) and r["crs"] == "EPSG:32611"))
print("with any value outside [0,1]:", sum(1 for r in ok if r["n_outside_0_1"] > 0))
print("with negative values:", sum(1 for r in ok if r["n_negative"] > 0))
print("with values >1:", sum(1 for r in ok if r["n_gt_1"] > 0))
print("with sentinel |v|>1e30:", sum(1 for r in ok if r["n_sentinel_gt1e30"] > 0))
print("with NaN cells:", sum(1 for r in ok if r["n_nan"] > 0))
print("with nodata tag:", sum(1 for r in ok if r["nodata"] is not None))
print("dtype counts:", {d: sum(1 for r in ok if r["dtype"] == d) for d in set(r["dtype"] for r in ok)})

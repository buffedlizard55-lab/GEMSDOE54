"""Data access for the DOE GEMS Prize checkout.

All rasters are read from ``.cache/gems_data`` (or ``$GEMS_DATA_DIR``), which is populated by
``scripts/fetch_mirrors.py`` from PUBLIC, sha256-pinned GitHub mirrors.  Nothing here touches
drivendata.org: that host is unreachable from this sandbox (verified, curl exit 35) and the
competition data page is login-walled anyway.  See ``registry/irregularities.json`` IR-54-DATA-01.
"""
from __future__ import annotations

import os
from pathlib import Path

import numpy as np
import rasterio

ROOT = Path(__file__).resolve().parents[2]
DATA = Path(os.environ.get("GEMS_DATA_DIR", ROOT / ".cache" / "gems_data"))

FEATURES = "training_features.tif"
LABELS = "labels.tif"
SAMPLE = "sample_submission.tif"

BAND_HINTS = {
    "magnetic_anomaly": 1, "rtp_magnetic": 2, "tmi_hgrad": 3, "strain_2nd_invariant": 4,
    "isostatic_grav_slope": 5, "tilt_angle": 6, "shear_rate": 7, "dilatation_rate": 8,
    "tmi_vgrad": 9, "eq_distance": 10, "isostatic_grav_vgrad": 11, "detrended_elev": 12,
    "isostatic_grav": 13, "tmi": 14, "depth_basement": 15, "eq_density": 16,
    "conductivity_surface": 17, "isostatic_grav_hgrad": 18, "detrended_elev_slope": 19,
}


def _path(name: str) -> Path:
    p = DATA / name
    if not p.exists():
        raise FileNotFoundError(
            f"{p} is missing. Run:  python3 scripts/fetch_mirrors.py --dest {DATA}")
    return p


def profile(name: str = FEATURES) -> dict:
    with rasterio.open(_path(name)) as s:
        return {"shape": s.shape, "count": s.count, "dtype": s.dtypes[0], "crs": str(s.crs),
                "transform": tuple(s.transform)[:6], "nodata": s.nodata, "bounds": tuple(s.bounds)}


def features(bands: list[int] | None = None, path: Path | None = None) -> tuple[np.ndarray, dict]:
    """Return ``(array[nband, H, W], meta)`` with nodata collapsed to NaN."""
    with rasterio.open(path or _path(FEATURES)) as s:
        idx = bands or list(range(1, s.count + 1))
        arr = s.read(idx).astype(np.float32)
        nod = s.nodata
        meta = {"crs": str(s.crs), "transform": tuple(s.transform)[:6], "shape": s.shape,
                "nodata": nod, "descriptions": [s.tags(i).get("description", "") for i in idx],
                "categories": [s.tags(i).get("data_category", "") for i in idx]}
    if nod is not None:
        arr[arr <= np.float32(nod) * np.float32(0.5)] = np.nan
    arr[~np.isfinite(arr)] = np.nan
    return arr, meta


def labels() -> np.ndarray:
    """Catalogue fault mask: True where the USGS/INGENIOUS label raster is 1."""
    with rasterio.open(_path(LABELS)) as s:
        a = s.read(1)
    return a == 1


def footprint() -> np.ndarray:
    """In-bounds mask = cells that carry data (labels != nodata).  5,167,373 cells of 12,279,160."""
    with rasterio.open(_path(LABELS)) as s:
        a = s.read(1)
        nod = s.nodata
    return a != (nod if nod is not None else -1)


def sample_submission() -> np.ndarray:
    with rasterio.open(_path(SAMPLE)) as s:
        return s.read(1)


def external(name: str) -> np.ndarray:
    """Read a pinned external layer, e.g. ``external('derived_sgmc_faults_100m_u8.tif')``."""
    with rasterio.open(_path(f"external/{name}")) as s:
        return s.read(1)


def external_meta(name: str) -> dict:
    with rasterio.open(_path(f"external/{name}")) as s:
        return {"crs": str(s.crs), "transform": tuple(s.transform)[:6], "shape": s.shape,
                "dtype": s.dtypes[0], "nodata": s.nodata}

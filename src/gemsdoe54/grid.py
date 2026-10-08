"""Grid, footprint and I/O helpers for the GEMS Prize submission format.

Grid values below are measured from the owner-mirrored raster files in
``data/grid/`` and recorded in ``registry/sources.json``. The current review did
not authenticate those files against a DrivenData download; do not confuse local
byte consistency with organizer provenance:

    shape      : (3730, 3292)          (rows, cols)
    CRS        : EPSG:32611            (UTM zone 11N, WGS 84)
    transform  : 100 m pixels, origin (243350.0, 4508550.0), north-up
    bounds     : left 243350.0, bottom 4135550.0, right 572550.0, top 4508550.0
    footprint  : 5,167,373 cells       (cells inside the study area)
    dtype      : float32 for submissions

The footprint is the set of cells where the organizer label raster carries a
0/1 value (``nodata = -1`` outside).  Every mirror used here shares this grid
byte-for-byte in shape/CRS/transform; alignment is asserted at load time.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np
import rasterio

EXPECTED_SHAPE = (3730, 3292)
EXPECTED_CRS = "EPSG:32611"
EXPECTED_TRANSFORM = (100.0, 0.0, 243350.0, 0.0, -100.0, 4508550.0)
FOOTPRINT_CELLS = 5_167_373


class GridMismatch(ValueError):
    """Raised when a raster does not sit on the competition grid."""


@dataclass(frozen=True)
class Grid:
    shape: tuple[int, int]
    transform: tuple[float, ...]
    crs: str

    @property
    def height(self) -> int:
        return self.shape[0]

    @property
    def width(self) -> int:
        return self.shape[1]


def assert_grid(path: str | Path) -> Grid:
    """Assert that ``path`` sits exactly on the competition grid."""
    with rasterio.open(path) as src:
        shape = (src.height, src.width)
        transform = tuple(round(v, 6) for v in src.transform[:6])
        crs = str(src.crs)
    if shape != EXPECTED_SHAPE:
        raise GridMismatch(f"{path}: shape {shape} != {EXPECTED_SHAPE}")
    if crs != EXPECTED_CRS:
        raise GridMismatch(f"{path}: crs {crs} != {EXPECTED_CRS}")
    want = tuple(round(v, 6) for v in EXPECTED_TRANSFORM)
    if transform != want:
        raise GridMismatch(f"{path}: transform {transform} != {want}")
    return Grid(shape, transform, crs)


def read_band(path: str | Path, *, require_grid: bool = True) -> tuple[np.ndarray, float | None]:
    """Return ``(array, nodata)`` for band 1, asserting grid alignment."""
    if require_grid:
        assert_grid(path)
    with rasterio.open(path) as src:
        arr = src.read(1)
        nodata = src.nodata
    return arr, (None if nodata is None else float(nodata))


def footprint(path: str | Path) -> np.ndarray:
    """Boolean mask of in-study-area cells derived from the organizer label raster.

    The organizer label raster stores ``-1`` outside the study area, so
    ``labels != -1`` is the footprint.  Verified: this mask has exactly
    5,167,373 True cells.
    """
    arr, nodata = read_band(path)
    if nodata is None:
        raise ValueError(f"{path}: label raster has no nodata sentinel")
    mask = arr != nodata
    if int(mask.sum()) != FOOTPRINT_CELLS:
        raise GridMismatch(
            f"{path}: footprint has {int(mask.sum())} cells, expected {FOOTPRINT_CELLS}"
        )
    return mask


def binary_mask(path: str | Path, *, positive_only: bool = True) -> np.ndarray:
    """Read a 0/1 evidence raster as a boolean mask.

    Mirrors derived from the state geologic map compilation rasterise faults to
    ``1`` with ``nodata = 255``; the GeoDAWN radiometric mirror uses
    ``nodata = 0`` with data in ``[1, 255]``.  Both cases are handled by
    treating ``nodata`` as False and ``> 0`` as positive.
    """
    arr, nodata = read_band(path)
    if nodata is not None:
        arr = np.where(arr == nodata, 0, arr)
    out = np.nan_to_num(arr.astype(np.float64), nan=0.0)
    return (out > 0) if positive_only else out


def write_submission(path: str | Path, values: np.ndarray, *, dtype: str = "float32") -> None:
    """Write a single-band float32 GeoTIFF on the competition grid.

    ``values`` must already be shaped like the competition grid and must lie in
    ``[0, 1]``.  Submission dtype is deliberately fixed to float32 so a caller
    cannot accidentally create an otherwise-valid-looking file that the portal
    rejects on dtype. No nodata tag is written and no NaN is emitted.
    """
    if np.dtype(dtype) != np.dtype("float32"):
        raise ValueError("submission dtype must be float32")
    values = np.asarray(values, dtype=np.float64)
    if values.shape != EXPECTED_SHAPE:
        raise ValueError(f"shape {values.shape} != {EXPECTED_SHAPE}")
    if not np.isfinite(values).all():
        raise ValueError("refusing to write non-finite values")
    if values.min() < 0.0 or values.max() > 1.0:
        raise ValueError(f"values must be in [0,1]; got [{values.min()}, {values.max()}]")
    profile = {
        "driver": "GTiff",
        "dtype": dtype,
        "count": 1,
        "height": EXPECTED_SHAPE[0],
        "width": EXPECTED_SHAPE[1],
        "crs": EXPECTED_CRS,
        "transform": rasterio.transform.Affine(*EXPECTED_TRANSFORM),
        "nodata": None,
        # DEFLATE + 256x256 tiles is the profile used by every sibling artefact that
        # the DrivenData portal has accepted, so it is the safest choice here.
        "compress": "deflate",
        "tiled": True,
        "blockxsize": 256,
        "blockysize": 256,
        "BIGTIFF": "IF_SAFER",
    }
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with rasterio.open(path, "w", **profile) as dst:
        dst.write(values.astype(dtype), 1)

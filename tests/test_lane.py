from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import rasterio
from rasterio.transform import from_origin

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from validate_submission import check_lane, check_lane_array  # noqa: E402


def _write_raster(path: Path, values: np.ndarray, *, nodata=None) -> None:
    with rasterio.open(
        path, "w", driver="GTiff", height=values.shape[0], width=values.shape[1],
        count=1, dtype=values.dtype, crs="EPSG:32611", transform=from_origin(0, 1000, 100, 100),
        nodata=nodata,
    ) as dst:
        dst.write(values, 1)


def test_near_covering_registry_is_still_a_strict_lane_stop(tmp_path):
    registry = np.zeros((40, 40), dtype=np.float32)
    registry[::6, ::6] = 1
    path = tmp_path / "near_cover.tif"
    _write_raster(path, registry)

    mine = np.zeros_like(registry)
    mine[3::7, 3::7] = 0.5
    report = check_lane_array(mine, [path], np.ones_like(mine, dtype=bool))

    row = report["rows"][0]
    assert row["registry_covers_fraction_of_footprint"] > 0.5
    assert row["overlap_flag"] is True
    assert report["lane_drift_detected"] is True
    assert report["verdict"] == "DUPLICATE - STOP"


def test_final_lane_check_accepts_nan_nodata_outside_footprint(tmp_path):
    registry = np.zeros((30, 30), dtype=np.float32)
    registry[10, 10] = 1
    path = tmp_path / "registry.tif"
    _write_raster(path, registry)

    foot = np.zeros((30, 30), dtype=bool)
    foot[5:25, 5:25] = True
    mine = np.full((30, 30), np.nan, dtype=np.float32)
    mine[foot] = 0
    mine[10, 11] = 1
    candidate_path = tmp_path / "final_candidate.tif"
    _write_raster(candidate_path, mine, nodata=np.nan)
    labels = np.where(foot, 0, 255).astype(np.uint8)
    labels_path = tmp_path / "labels.tif"
    _write_raster(labels_path, labels, nodata=255)

    report = check_lane(candidate_path, [path], labels_path)

    assert report["my_dots"] == 1
    assert report["rows"][0]["fraction_of_my_dots"] == 1.0
    assert report["verdict"] == "DUPLICATE - STOP"


def test_rank_correlation_uses_absolute_value(tmp_path):
    values = np.arange(100, dtype=np.float32).reshape(10, 10)
    path = tmp_path / "gradient.tif"
    _write_raster(path, values)
    mine = -values
    report = check_lane_array(mine, [path], np.ones_like(mine, dtype=bool))
    assert report["rows"][0]["spearman_rho"] == -1.0
    assert report["rows"][0]["rho_flag"] is True

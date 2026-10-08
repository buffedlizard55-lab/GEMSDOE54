from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import rasterio
from affine import Affine

from gemsdoe54.audit import audit_workspace, validate_submission


TRANSFORM = Affine(100, 0, 500000, 0, -100, 4500000)
CRS = "EPSG:32611"


def _write(path: Path, array: np.ndarray, *, nodata=None, mask=None, descriptions=None, crs=CRS):
    if array.ndim == 2:
        array = array[np.newaxis, ...]
    count, height, width = array.shape
    with rasterio.open(
        path,
        "w",
        driver="GTiff",
        width=width,
        height=height,
        count=count,
        dtype=array.dtype,
        crs=crs,
        transform=TRANSFORM,
        nodata=nodata,
    ) as ds:
        ds.write(array)
        if mask is not None:
            ds.write_mask(mask.astype("uint8") * 255)
        if descriptions:
            for i, description in enumerate(descriptions, start=1):
                ds.set_band_description(i, description)


def _make_data_dir(root: Path, *, informative: bool = True):
    data = root / "data"
    data.mkdir()
    footprint = np.ones((32, 32), dtype=bool)
    xx = np.arange(32, dtype=np.float32)[None, :]
    band1 = np.broadcast_to(xx, footprint.shape).copy()
    band2 = np.full(footprint.shape, 7.0 if not informative else 0.5, dtype=np.float32)
    features = np.stack([band1 if informative else band2, band2])
    _write(data / "training_features.tif", features, nodata=-9999, mask=footprint,
           descriptions=["x-gradient test channel", "constant test channel"])
    labels = np.zeros(footprint.shape, dtype=np.uint8)
    labels[10, 10] = 1
    _write(data / "labels.tif", labels, mask=footprint)
    sample = np.zeros(footprint.shape, dtype=np.float32)
    _write(data / "sample_submission.tif", sample, nodata=np.nan, mask=footprint)
    files = {}
    for name in ("training_features.tif", "labels.tif", "sample_submission.tif"):
        files[name] = {"sha256": hashlib.sha256((data / name).read_bytes()).hexdigest()}
    (data / "provenance.json").write_text(json.dumps({"files": files}))
    return data


def test_missing_inputs_fail_closed(tmp_path):
    report = audit_workspace(tmp_path / "absent")
    assert report["status"] == "blocked_missing_inputs"
    assert len(report["missing_inputs"]) == 3
    assert report["ready_for_holdout"] is False
    assert report["ready_for_competition_submission"] is False


def test_valid_synthetic_inputs_are_only_structurally_valid(tmp_path):
    data = _make_data_dir(tmp_path)
    report = audit_workspace(data)
    assert report["status"] == "structurally_valid_provenance_declared"
    assert report["checks"]["at_least_one_nonconstant_feature_band"] is True
    assert report["label_scan"]["positive_pixels"] == 1
    # Matching a local hash manifest does not authenticate the organizer source or approve a run.
    assert report["ready_for_holdout"] is False
    assert report["ready_for_competition_submission"] is False
    # Rasterio can represent NaN nodata; the machine-readable audit must still be strict JSON.
    json.dumps(report, allow_nan=False)


def test_constant_feature_cube_is_rejected(tmp_path):
    report = audit_workspace(_make_data_dir(tmp_path, informative=False))
    assert report["status"] == "blocked_invalid_or_uninformative_inputs"
    assert report["checks"]["at_least_one_nonconstant_feature_band"] is False


def test_small_feature_coverage_gaps_are_reported_but_not_silently_treated_as_complete(tmp_path):
    data = _make_data_dir(tmp_path)
    feature_path = data / "training_features.tif"
    with rasterio.open(feature_path) as ds:
        features = ds.read()
    features[0, 0, 0] = -9999
    _write(feature_path, features, nodata=-9999,
           descriptions=["x-gradient test channel", "constant test channel"])
    files = {
        name: {"sha256": hashlib.sha256((data / name).read_bytes()).hexdigest()}
        for name in ("training_features.tif", "labels.tif", "sample_submission.tif")
    }
    (data / "provenance.json").write_text(json.dumps({"files": files}))

    report = audit_workspace(data)
    assert report["feature_scan"]["all_bands_cover_footprint"] is False
    assert report["feature_scan"]["all_bands_at_least_99_percent_covered"] is True
    assert report["checks"]["feature_band_coverage_at_least_99_percent"] is True
    assert report["status"] == "structurally_valid_provenance_declared"


def test_submission_validator_accepts_finite_in_range_matching_grid(tmp_path):
    ref = tmp_path / "sample.tif"
    candidate = tmp_path / "candidate.tif"
    mask = np.ones((32, 32), dtype=bool)
    _write(ref, np.zeros((32, 32), dtype=np.float32), nodata=np.nan, mask=mask)
    p = np.zeros((32, 32), dtype=np.float32)
    p[10, 10] = 1.0
    _write(candidate, p)
    report = validate_submission(candidate, ref)
    assert report["ok"] is True
    assert report["crs_shape_transform_match"] is True
    assert report["no_nan_inside_footprint"] is True
    assert report["all_pixels_in_range_0_1"] is True


def test_submission_validator_rejects_missing_crs_and_multiband(tmp_path):
    ref = tmp_path / "sample.tif"
    no_crs = tmp_path / "no-crs.tif"
    multiband = tmp_path / "multiband.tif"
    mask = np.ones((32, 32), dtype=bool)
    _write(ref, np.zeros((32, 32), dtype=np.float32), nodata=np.nan, mask=mask)
    _write(no_crs, np.zeros((32, 32), dtype=np.float32), crs=None)
    _write(multiband, np.zeros((2, 32, 32), dtype=np.float32))
    assert "prediction and reference must both declare a CRS" in validate_submission(no_crs, ref)["problems"]
    assert "prediction raster must have exactly one band" in validate_submission(multiband, ref)["problems"]


def test_submission_validator_rejects_nan_and_out_of_range(tmp_path):
    ref = tmp_path / "sample.tif"
    candidate = tmp_path / "candidate.tif"
    mask = np.ones((32, 32), dtype=bool)
    _write(ref, np.zeros((32, 32), dtype=np.float32), nodata=np.nan, mask=mask)
    p = np.zeros((32, 32), dtype=np.float32)
    p[0, 0] = np.nan
    p[0, 1] = 1.01
    _write(candidate, p)
    report = validate_submission(candidate, ref)
    assert report["ok"] is False
    assert "prediction contains NaN or infinity" in report["problems"]
    assert "prediction values must be within [0, 1]" in report["problems"]

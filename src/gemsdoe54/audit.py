"""Fail-closed checks for competition inputs and one-band prediction rasters.

This module validates bytes and grids; it does not authenticate their source, train a model,
perform holdout evaluation, or grant permission to spend a competition slot.
"""

from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from typing import Any

import numpy as np
import rasterio

FEATURE_CANDIDATES = ("training_features.tif", "numeric_features.tif")
LABEL_CANDIDATES = ("labels.tif", "grid/labels.tif")
SAMPLE_CANDIDATES = ("sample_submission.tif",)
KNOWN_NON_SAMPLE_TEMPLATES = ("grid/MIRROR_sample_submission_template.tif",)


def sha256_file(path: str | Path, chunk_size: int = 1024 * 1024) -> str:
    """Return a streaming SHA-256 digest without loading a large raster into memory."""
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(chunk_size), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _grid(ds: rasterio.io.DatasetReader) -> dict[str, Any]:
    return {
        "width": int(ds.width),
        "height": int(ds.height),
        "count": int(ds.count),
        "crs": ds.crs.to_string() if ds.crs else None,
        "transform": [float(v) for v in tuple(ds.transform)[:6]],
        "dtypes": list(ds.dtypes),
        "nodata": None if ds.nodata is None else (float(ds.nodata) if np.isfinite(ds.nodata) else str(ds.nodata)),
    }


def _same_grid(a: dict[str, Any], b: dict[str, Any]) -> bool:
    if (a["width"], a["height"], a["crs"]) != (b["width"], b["height"], b["crs"]):
        return False
    return bool(np.allclose(a["transform"], b["transform"], rtol=0.0, atol=1e-9))


def _windows(ds: rasterio.io.DatasetReader):
    # Use the reference file's native blocks to bound memory even for a multi-gigabyte feature cube.
    yield from (window for _, window in ds.block_windows(1))


def _scan_features(features: rasterio.io.DatasetReader, sample: rasterio.io.DatasetReader) -> dict[str, Any]:
    stats = [
        {"band": band, "description": features.descriptions[band - 1], "valid_pixels": 0,
         "missing_inside_footprint": 0, "min": None, "max": None, "mean": None}
        for band in range(1, features.count + 1)
    ]
    sums = np.zeros(features.count, dtype=np.float64)
    sums_sq = np.zeros(features.count, dtype=np.float64)
    counts = np.zeros(features.count, dtype=np.int64)
    mins = np.full(features.count, np.inf, dtype=np.float64)
    maxs = np.full(features.count, -np.inf, dtype=np.float64)
    footprint_pixels = 0
    nonfinite_inside = np.zeros(features.count, dtype=np.int64)

    for window in _windows(sample):
        footprint = sample.read_masks(1, window=window) > 0
        footprint_pixels += int(footprint.sum())
        for band in range(1, features.count + 1):
            values = features.read(band, window=window, masked=False)
            valid = footprint & (features.read_masks(band, window=window) > 0)
            finite = np.isfinite(values)
            nonfinite_inside[band - 1] += int(np.count_nonzero(footprint & ~finite))
            keep = valid & finite
            stats[band - 1]["missing_inside_footprint"] += int(np.count_nonzero(footprint & ~keep))
            x = values[keep].astype(np.float64, copy=False)
            if x.size:
                counts[band - 1] += x.size
                sums[band - 1] += float(x.sum(dtype=np.float64))
                sums_sq[band - 1] += float(np.square(x).sum(dtype=np.float64))
                mins[band - 1] = min(mins[band - 1], float(x.min()))
                maxs[band - 1] = max(maxs[band - 1], float(x.max()))

    for i, stat in enumerate(stats):
        stat["valid_pixels"] = int(counts[i])
        stat["coverage_fraction_of_sample_footprint"] = (
            float(counts[i] / footprint_pixels) if footprint_pixels else 0.0
        )
        stat["nonfinite_inside_footprint"] = int(nonfinite_inside[i])
        if counts[i]:
            stat["min"] = float(mins[i])
            stat["max"] = float(maxs[i])
            stat["mean"] = float(sums[i] / counts[i])
            stat["population_variance"] = max(0.0, float(sums_sq[i] / counts[i] - stat["mean"] ** 2))
            stat["constant_on_footprint"] = bool(mins[i] == maxs[i])
        else:
            stat["population_variance"] = None
            stat["constant_on_footprint"] = None
    nonconstant = sum(bool(s["valid_pixels"] and not s["constant_on_footprint"]) for s in stats)
    return {
        "footprint_pixels": int(footprint_pixels),
        "band_count": int(features.count),
        "nonconstant_band_count": int(nonconstant),
        "all_bands_finite_inside_footprint": all(s["nonfinite_inside_footprint"] == 0 for s in stats),
        "all_bands_cover_footprint": all(s["missing_inside_footprint"] == 0 for s in stats),
        "minimum_band_coverage_fraction": 0.99,
        "all_bands_at_least_99_percent_covered": all(
            s["coverage_fraction_of_sample_footprint"] >= 0.99 for s in stats
        ),
        "bands": stats,
    }


def _scan_labels(labels: rasterio.io.DatasetReader, sample: rasterio.io.DatasetReader) -> dict[str, Any]:
    positives = 0
    valid_pixels = 0
    missing_inside = 0
    invalid_values = 0
    values_seen: set[float] = set()
    for window in _windows(sample):
        footprint = sample.read_masks(1, window=window) > 0
        data = labels.read(1, window=window, masked=False)
        finite = np.isfinite(data)
        valid = footprint & (labels.read_masks(1, window=window) > 0) & finite
        missing_inside += int(np.count_nonzero(footprint & ~valid))
        invalid_values += int(np.count_nonzero(valid & ~np.isin(data, (0, 1))))
        positives += int(np.count_nonzero(valid & (data == 1)))
        valid_pixels += int(valid.sum())
        if valid.any():
            values_seen.update(float(x) for x in np.unique(data[valid]))
    return {
        "valid_pixels": valid_pixels,
        "positive_pixels": positives,
        "missing_inside_footprint": missing_inside,
        "nonbinary_valid_pixels": invalid_values,
        "values_seen": sorted(values_seen),
        "binary_labels": invalid_values == 0,
    }


def _declared_provenance_check(data_dir: Path, actual_hashes: dict[str, str]) -> dict[str, Any]:
    manifest_path = data_dir / "provenance.json"
    if not manifest_path.is_file():
        return {"status": "missing", "hashes_match": False,
                "note": "No local provenance manifest; file origin is unverified."}
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return {"status": "invalid", "hashes_match": False, "error": str(exc)}
    files = manifest.get("files", {})
    comparisons = {}
    for name, actual in actual_hashes.items():
        expected = files.get(name, {}).get("sha256") if isinstance(files.get(name), dict) else None
        comparisons[name] = {"expected_sha256": expected, "actual_sha256": actual,
                             "matches": bool(expected and expected.lower() == actual.lower())}
    all_match = bool(comparisons) and all(item["matches"] for item in comparisons.values())
    return {
        "status": "declared_hashes_match" if all_match else "declared_hash_mismatch_or_incomplete",
        "hashes_match": all_match,
        "files": comparisons,
        "organizer_authentication": "not established by a local manifest or matching hash alone",
    }


def audit_workspace(data_dir: str | Path = "data") -> dict[str, Any]:
    """Audit local training inputs. Missing or uninformative data never passes the gate."""
    root = Path(data_dir)
    feature_matches = [root / name for name in FEATURE_CANDIDATES if (root / name).is_file()]
    label_matches = [root / name for name in LABEL_CANDIDATES if (root / name).is_file()]
    sample_matches = [root / name for name in SAMPLE_CANDIDATES if (root / name).is_file()]
    known_non_samples = [root / name for name in KNOWN_NON_SAMPLE_TEMPLATES if (root / name).is_file()]
    feature_path = feature_matches[0] if feature_matches else None
    label_path = label_matches[0] if label_matches else None
    sample_path = sample_matches[0] if sample_matches else None
    missing = []
    if feature_path is None:
        missing.append("training_features.tif or numeric_features.tif")
    if label_path is None:
        missing.append("labels.tif (searched data root and grid/)")
    if sample_path is None:
        missing.append("sample_submission.tif (known label-mask mirror is not accepted as a sample)")

    result: dict[str, Any] = {
        "schema": "gemsdoe54.workspace-audit.v1",
        "generated_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "data_dir": str(root),
        "status": "blocked_missing_inputs" if missing else "pending_checks",
        "missing_inputs": missing,
        "feature_path": str(feature_path) if feature_path else None,
        "feature_aliases_found": [str(p) for p in feature_matches],
        "available_input_paths": {
            "features": [str(p) for p in feature_matches],
            "labels": [str(p) for p in label_matches],
            "sample_submission": [str(p) for p in sample_matches],
            "known_non_sample_templates": [str(p) for p in known_non_samples],
        },
        "inputs": {},
        "checks": {},
        "provenance": {"status": "not_checked", "organizer_authentication": "not established"},
        "ready_for_holdout": False,
        "ready_for_competition_submission": False,
        "decision": "No model, holdout, or submission build is authorized until this audit passes and provenance is reviewed.",
    }
    if missing:
        return result

    assert feature_path is not None and label_path is not None and sample_path is not None
    paths = {"features": feature_path, "labels": label_path, "sample_submission": sample_path}
    hashes = {path.name: sha256_file(path) for path in paths.values()}
    datasets = {}
    try:
        for key, path in paths.items():
            datasets[key] = rasterio.open(path)
        grids = {key: _grid(ds) for key, ds in datasets.items()}
        ref = grids["sample_submission"]
        grid_checks = {key: _same_grid(ref, grids[key]) for key in ("features", "labels")}
        feat_scan = _scan_features(datasets["features"], datasets["sample_submission"])
        label_scan = _scan_labels(datasets["labels"], datasets["sample_submission"])
        result["inputs"] = {
            key: {"path": str(paths[key]), "sha256": hashes[paths[key].name], "grid": grids[key]}
            for key in paths
        }
        result["feature_scan"] = feat_scan
        result["label_scan"] = label_scan
        result["checks"] = {
            "exactly_one_feature_alias_present": len(feature_matches) == 1,
            "sample_is_single_band": datasets["sample_submission"].count == 1,
            "labels_are_single_band": datasets["labels"].count == 1,
            "sample_has_crs": datasets["sample_submission"].crs is not None,
            "feature_grid_matches_sample": grid_checks["features"],
            "labels_grid_matches_sample": grid_checks["labels"],
            "features_finite_inside_footprint": feat_scan["all_bands_finite_inside_footprint"],
            "feature_band_coverage_at_least_99_percent": feat_scan[
                "all_bands_at_least_99_percent_covered"
            ],
            "at_least_one_nonconstant_feature_band": feat_scan["nonconstant_band_count"] > 0,
            "labels_cover_footprint": label_scan["missing_inside_footprint"] == 0,
            "labels_are_binary": label_scan["binary_labels"],
            "positive_label_pixels_exist": label_scan["positive_pixels"] > 0,
        }
        result["provenance"] = _declared_provenance_check(root, hashes)
        all_structural = all(result["checks"].values())
        if not all_structural:
            result["status"] = "blocked_invalid_or_uninformative_inputs"
        elif result["provenance"]["status"] != "declared_hashes_match":
            result["status"] = "blocked_unverified_provenance"
        else:
            result["status"] = "structurally_valid_provenance_declared"
        # A self-authored manifest can detect accidental changes but cannot prove origin. Keep the
        # competition gate closed; a human/organizer receipt is deliberately not inferred here.
        result["ready_for_holdout"] = False
        result["ready_for_competition_submission"] = False
        result["decision"] = (
            "Input structure was audited. This utility does not authenticate organizer provenance, "
            "implement the required hide-and-recover evaluator, or approve a weekly slot."
        )
    except Exception as exc:
        result["status"] = "blocked_audit_error"
        result["audit_error"] = f"{type(exc).__name__}: {exc}"
    finally:
        for ds in datasets.values():
            ds.close()
    return result


def validate_submission(candidate_path: str | Path, reference_path: str | Path) -> dict[str, Any]:
    """Validate one single-band prediction raster against the official sample grid.

    The organizer's format page specifies finite [0,1] predictions inside the study
    footprint and null/NaN outside it. The exact previously rejected upload is not
    available, so this check cannot diagnose that historic error.
    """
    candidate_path, reference_path = Path(candidate_path), Path(reference_path)
    problems: list[str] = []
    if not candidate_path.is_file():
        return {"ok": False, "problems": [f"candidate does not exist: {candidate_path}"]}
    if not reference_path.is_file():
        return {"ok": False, "problems": [f"reference does not exist: {reference_path}"]}
    with rasterio.open(candidate_path) as pred, rasterio.open(reference_path) as ref:
        pred_grid, ref_grid = _grid(pred), _grid(ref)
        if pred.count != 1:
            problems.append("prediction raster must have exactly one band")
        dtype_float32 = pred.dtypes[0] == "float32"
        if not dtype_float32:
            problems.append("prediction raster must use float32 dtype")
        if ref.count != 1:
            problems.append("reference sample raster must have exactly one band")
        if pred.crs is None or ref.crs is None:
            problems.append("prediction and reference must both declare a CRS")
        grid_match = _same_grid(ref_grid, pred_grid)
        if not grid_match:
            problems.append("CRS, dimensions, or geotransform do not exactly match the reference grid")
        values = pred.read(1, masked=False)
        footprint = ref.read_masks(1) > 0
        same_shape = values.shape == footprint.shape
        if not same_shape:
            problems.append("prediction dimensions do not match the reference footprint")
            inside_finite = inside_range = outside_null = None
            positive_count = None
        else:
            inside_values = values[footprint]
            outside_values = values[~footprint]
            inside_finite = bool(np.isfinite(inside_values).all())
            if not inside_finite:
                problems.append("prediction contains NaN or infinity inside the footprint")
            inside_range = bool(inside_values.size == 0 or
                                (inside_finite and (inside_values >= 0.0).all() and
                                 (inside_values <= 1.0).all()))
            if not inside_range:
                problems.append("in-footprint prediction values must be within [0, 1]")
            outside_null = bool(np.isnan(outside_values).all())
            if not outside_null:
                problems.append("outside-footprint cells must be null/NaN")
            positive_count = int(np.count_nonzero((inside_values > 0) & np.isfinite(inside_values)))
        return {
            "ok": not problems,
            "problems": problems,
            "candidate": str(candidate_path),
            "candidate_sha256": sha256_file(candidate_path),
            "single_band": pred.count == 1,
            "dtype": pred.dtypes[0],
            "dtype_float32": dtype_float32,
            "crs_shape_transform_match": grid_match,
            "crs": pred_grid["crs"],
            "shape": [pred_grid["height"], pred_grid["width"]],
            "transform": pred_grid["transform"],
            "no_nan_inside_footprint": inside_finite,
            "inside_footprint_in_range_0_1": inside_range,
            "outside_footprint_null_or_nan": outside_null,
            "footprint_pixels": int(footprint.sum()),
            "positive_pixels_inside_footprint": positive_count,
            "note": "Format/range validation is not holdout evidence, organizer acceptance, or slot approval.",
        }

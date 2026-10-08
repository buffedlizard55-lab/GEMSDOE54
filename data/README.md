# Placed inputs

Two files are needed to build the submission, plus one kept as evidence.

| file | sha256 | bytes | why it is here |
|---|---|---|---|
| `grid/labels.tif` | `7ba308ccdc4418b31a178f4f1ef21aaa6e152e4028f2f6f64b01f7eb25ae4093` | 425,830 | Owner-mirrored label raster; its hash matches the pin in `external/GEMSDOE30_external_receipt.json`. The cached file has 60,988 positive cells, nodata -1, and a 5,167,373-cell footprint. The hash match does not authenticate organizer origin. |
| `external/derived_sgmc_faults_100m_u8.tif` | `26d142c4c93282cd94f6950ab96f22aeff59fbbea523d43d662e76fa1b161b5c` | 213,034 | Owner-mirrored 100 m rasterisation attributed to the USGS State Geologic Map Compilation NV+CA fault layers. Source origin and processing were not independently authenticated in this audit. |
| `external/GEMSDOE30_external_receipt.json` | — | 34,684 | An owner-maintained pinning receipt listing source URLs, sizes, hashes and licences from a prior GitHub Actions fetch. It establishes integrity against those pins, not organizer provenance. |
| `grid/MIRROR_sample_submission_template.tif` | `2176d08e485aa2cd2860ce8df539db4faf4d76163b38a4dd8c30a40454d35cbc` | 1,599,597 | **Evidence only — never read by any script.** Despite the filename it is cell-for-cell the catalogue mask, not an all-zero template. See `docs/evidence.html`, irregularity 1. |

The primary sources are login-gated or unreachable from the development sandbox, which is
why these are hash-pinned mirrors rather than fresh downloads. `scripts/fetch_inputs.sh`
documents the primary URLs for re-fetching on an unrestricted machine.

Verify locally with:

```bash
sha256sum data/grid/labels.tif data/external/derived_sgmc_faults_100m_u8.tif
```

## Current review caveat

These small owner-maintained mirror files were already tracked on `main`; this review did not fetch them from an authenticated DrivenData account. The full `training_features.tif` stack is not present in this checkout. The file named `grid/MIRROR_sample_submission_template.tif` is evidence only: the repository's audit found it cell-for-cell equal to the label mask, so do not use it as the official zero/template raster. Hash agreement with owner receipts establishes integrity, not organizer origin.

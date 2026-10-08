# Placed inputs

Two files are needed to build the submission, plus one kept as evidence.

| file | sha256 | bytes | why it is here |
|---|---|---|---|
| `grid/labels.tif` | `7ba308ccdc4418b31a178f4f1ef21aaa6e152e4028f2f6f64b01f7eb25ae4093` | 425,830 | Organizer label raster. Hash matches the pin in `external/GEMSDOE30_external_receipt.json`. 60,988 positive cells, nodata -1, footprint 5,167,373 cells. |
| `external/derived_sgmc_faults_100m_u8.tif` | `26d142c4c93282cd94f6950ab96f22aeff59fbbea523d43d662e76fa1b161b5c` | 213,034 | 100 m rasterisation of the USGS State Geologic Map Compilation NV+CA fault layers. The submission's only evidence layer. |
| `external/GEMSDOE30_external_receipt.json` | — | 34,684 | The pinning receipt: every source URL, size, sha256 and licence recorded when a GitHub Actions runner (which has unrestricted network access) fetched them. |
| `grid/MIRROR_sample_submission_template.tif` | `2176d08e485aa2cd2860ce8df539db4faf4d76163b38a4dd8c30a40454d35cbc` | 1,599,597 | **Evidence only — never read by any script.** Despite the filename it is cell-for-cell the catalogue mask, not an all-zero template. See `docs/evidence.html`, irregularity 1. |

The primary sources are login-gated or unreachable from the development sandbox, which is
why these are hash-pinned mirrors rather than fresh downloads. `scripts/fetch_inputs.sh`
documents the primary URLs for re-fetching on an unrestricted machine.

Verify locally with:

```bash
sha256sum data/grid/labels.tif data/external/derived_sgmc_faults_100m_u8.tif
```

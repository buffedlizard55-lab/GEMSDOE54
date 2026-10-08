#!/usr/bin/env bash
# Where every input in data/ came from, and the hash that identifies it.
#
# This repository does NOT download the competition data. The DrivenData data page
# is login-gated and unreachable from the development sandbox, so the two rasters
# needed to BUILD the submission are kept in-repo as hash-pinned mirrors, with the
# pinning receipt stored beside them.
#
# Run on a machine with unrestricted network access to re-fetch from primary sources.
set -euo pipefail
cd "$(dirname "$0")/.."

cat <<'NOTES'
Need                                   Where it lives now                                     Primary source
-------------------------------------  -----------------------------------------------------  ---------------------------------------------------------------
organizer label raster (60,988 cells)  data/grid/labels.tif                                   drivendata.org/.../data/  (login required)
                                       sha256 7ba308cc…  size 425,830 B                        or the hash-pinned mirror GEMSDOE24/data/bridge/labels.tif
USGS SGMC NV + CA fault layers         data/external/derived_sgmc_faults_100m_u8.tif          https://mrdata.usgs.gov/geology/state/shp/NV.zip
                                       sha256 26d142c4…  size 213,034 B                         https://mrdata.usgs.gov/geology/state/shp/CA.zip
provenance receipt for both            data/external/GEMSDOE30_external_receipt.json          recorded by a GitHub Actions runner
NOTES

cat <<'EOF'

The mirror hashes and the pinned receipt are the audit trail:

  data/grid/labels.tif
      7ba308ccdc4418b31a178f4f1ef21aaa6e152e4028f2f6f64b01f7eb25ae4093   (matches the pin)

  data/external/derived_sgmc_faults_100m_u8.tif
      26d142c4c93282cd94f6950ab96f22aeff59fbbea523d43d662e76fa1b161b5c

  data/grid/MIRROR_sample_submission_template.tif
      2176d08e485aa2cd2860ce8df539db4faf4d76163b38a4dd8c30a40454d35cbc
      WARNING: despite the name this file is NOT an all-zero sample submission.
      It is cell-for-cell identical to the catalogue label mask -- 60,988 positive
      cells in 0/1. See docs/evidence.html, irregularity 1. Nothing in this
      repository reads it; it is kept only as evidence.

To re-verify the two inputs the builder actually reads:

  sha256sum data/grid/labels.tif data/external/derived_sgmc_faults_100m_u8.tif

To rebuild everything from them:

  bash scripts/run_all.sh
EOF

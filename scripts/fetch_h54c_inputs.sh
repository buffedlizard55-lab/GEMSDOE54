#!/usr/bin/env bash
# Fetch and hash-verify the H54-C input mirrors.
#
# All five inputs are public, free-licence research data, mirrored in the owner's
# sibling repositories and pinned below by repository, commit, path and SHA-256.
# Nothing here is organizer-authenticated; the competition data page is
# login-gated.  Sources for manual review:
#   GeoDAWN survey (USGS, public domain):
#     https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and
#   GDR/INGENIOUS submission 1391 (CC BY 4.0, DOI 10.15121/1881483):
#     https://gdr.openei.org/submissions/1391
#   USGS State Geologic Map Compilation (public domain): https://mrdata.usgs.gov/geology/state/
#
# Usage:  bash scripts/fetch_h54c_inputs.sh [DEST_DIR]
# Default DEST_DIR is data/external (the repository checkout).
set -euo pipefail
DEST="${1:-$(cd "$(dirname "$0")/.." && pwd)/data/external}"
mkdir -p "$DEST"

fetch_sparse() { # repo commit dest path1 [path2 ...]
  local repo="$1" commit="$2"; shift 2
  local tmp
  tmp="$(mktemp -d)"
  git -C "$tmp" init -q
  git -C "$tmp" remote add origin "https://github.com/buffedlizard55-lab/${repo}.git"
  git -C "$tmp" fetch -q --depth 1 origin "$commit"
  git -C "$tmp" sparse-checkout init -q --no-cone
  for p in "$@"; do git -C "$tmp" sparse-checkout set -q --no-cone "$p"; done
  git -C "$tmp" checkout -q FETCH_HEAD
  for p in "$@"; do
    cp "$tmp/$p" "$DEST/$(basename "$p")"
  done
  rm -rf "$tmp"
}

# GeoDAWN stacks (USGS GeoDAWN, quantised u8 mirrors built by 7GEMSDOE's pipeline).
fetch_sparse 7GEMSDOE 9d8b5d55b674629f7b0e0e486269917c0fa2dade \
  "external/geodawn_rad/geodawn_rad_u8.tif" \
  "external/geodawn_extensions/geodawn_extensions_u8.tif"

# GDR/INGENIOUS manifestation masks (derived on a GitHub Actions runner; see
# data/external/GEMSDOE30_external_receipt.json for the full derivation record).
fetch_sparse GEMSDOE30 1f9ac110d5f1a4fac7957fe814267a0be964dd20 \
  "data/external/derived_gdr_volcanics_100m_u8.tif" \
  "data/external/derived_gdr_paleo_100m_u8.tif" \
  "data/external/derived_gdr_2m_probes_100m_u8.tif"

# Hash gate: refuse to proceed on any mismatch.
cd "$DEST"
sha256sum -c <<'PINS'
c22420f75999030d7cc65c9e31e50d232ea6158423bca051613a18a8b20ba682  geodawn_rad_u8.tif
a35a9c6d2a14786f4dab85481ee59769213072f5dab5b2535ea82ae4d9bb7d9b  geodawn_extensions_u8.tif
c219bd644e6f7a4071dc429e29b909a2296967b0657bf456bb6675413ee76cb2  derived_gdr_volcanics_100m_u8.tif
d6a3609bd7943fa5f1126a3cc688441aeceee261a76cd6a90a206830400066a4  derived_gdr_paleo_100m_u8.tif
7ac3cfdf2412f7f8a8b82d928115888c510f106f0254fb0b3988448db2f3b6ec  derived_gdr_2m_probes_100m_u8.tif
PINS
echo "H54-C inputs OK in $DEST"

#!/usr/bin/env bash
# Read-only partial clone of every GEMS-named sibling repository that contains rasters,
# materialising ONLY *.tif / *.tiff / *.zip files. Scratch output lives outside the repository
# (default /tmp/sib/repos). Requires git (github.com) and a prior run of scripts/inventory_siblings.py.
#
# Usage: bash scripts/fetch_sibling_rasters.sh [INVENTORY_JSON] [DEST_DIR]
set -u
INV="${1:-/tmp/sib/inventory.json}"
DEST="${2:-/tmp/sib/repos}"
PY="${PYTHON:-python3}"
mkdir -p "$DEST"
cd "$DEST" || exit 1
names=$("$PY" -c "import json,sys; print(' '.join(o['repo'] for o in json.load(open(sys.argv[1])) if o.get('rasters')))" "$INV")
for name in $names; do
  if [ -d "$name/.git" ]; then echo "skip $name (exists)"; continue; fi
  if git clone --quiet --filter=blob:none --no-checkout --depth 1 "https://github.com/buffedlizard55-lab/$name.git" "$name" 2>"/tmp/sib_err_$name.log"; then
    cd "$name" || exit 1
    git sparse-checkout init --no-cone >/dev/null 2>&1
    git sparse-checkout set --no-cone '*.tif' '*.tiff' '*.zip' '**/*.tif' '**/*.tiff' '**/*.zip' >/dev/null 2>&1
    if git checkout --quiet 2>>"/tmp/sib_err_$name.log"; then
      echo "ok $name"
    else
      echo "CHECKOUT-FAIL $name"
    fi
    cd "$DEST" || exit 1
  else
    echo "CLONE-FAIL $name"
  fi
done
echo DONE

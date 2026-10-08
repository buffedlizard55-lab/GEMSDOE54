#!/usr/bin/env bash
# Reproduce every artefact in this repository, in order, from the placed inputs.
#
# Usage: bash scripts/run_all.sh
set -euo pipefail
cd "$(dirname "$0")/.."

echo "== 1. metric regression (organizer worked example) =="
python3 tests/test_metric.py

echo
echo "== 2. emission regression =="
python3 tests/test_emission.py

echo
echo "== 3. collect the parallel-run registry =="
python3 scripts/collect_registry.py

echo
echo "== 4. build the submission =="
python3 scripts/build_submission.py

echo
echo "== 5. leakage canary (feature-alone AUC vs the holdout) =="
python3 scripts/leakage_canary.py > /dev/null
python3 - <<'PY2'
import json
d = json.load(open("evidence/leakage_canary.json"))
for k, v in d["auc_by_feature"].items():
    print(f"   {k}: AUC={v}")
for f in d["leakage_flags"]:
    print("   " + f)
PY2

echo
echo "== 6. validate: format, range, lane =="
python3 scripts/validate_submission.py \
  docs/downloads/gems54-undercomplement-q200.tif \
  --out evidence/gems54-undercomplement-q200.validation.json > /dev/null
python3 - <<'PY'
import json
d = json.load(open("evidence/gems54-undercomplement-q200.validation.json"))
print("format passed:", d["format"]["passed"], "| lane:", d["lane"]["verdict"])
for name, row in d["format"]["checks"].items():
    print(f"   {'OK  ' if row['ok'] else 'FAIL'} {name}: {row['detail']}")
PY

echo
echo "== 7. power analysis / detection floor =="
python3 scripts/power_analysis.py > /dev/null
python3 - <<'PY'
import json
d = json.load(open("evidence/power_analysis.json"))
print("dDTI/dT at the 0.2778 operating point:", d["dDTI_dT_at_operating_point"])
for k, v in d["measured_paired_designs"].items():
    print(f"   {k}: n={v['n_informative_truth_cells']:,} sigma_d={v['sd_paired_credit_difference']}")
print("minimum detectable (near-identical pair):", d["minimum_detectable"])
PY

echo
echo "== 8. blocked holdout screening + proxy audit =="
python3 scripts/run_holdout.py > /dev/null
python3 scripts/proxy_audit.py

echo
echo "== 9. sync published hashes with the built artefact =="
python3 scripts/sync_receipts.py

echo
echo "== done =="
echo "submission: docs/downloads/gems54-undercomplement-q200.tif"
sha256sum docs/downloads/gems54-undercomplement-q200.tif

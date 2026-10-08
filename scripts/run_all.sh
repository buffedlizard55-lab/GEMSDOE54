#!/usr/bin/env bash
# Retired legacy pipeline. Do not use it to create or submit a candidate.
set -euo pipefail
cat >&2 <<'EOF'
The historical H54-A pipeline is retired. It used a circular SGMC proxy, did not
implement the required whole-fault-segment holdout, and must not be used as a
submission workflow. No build or registry update was performed.

Use the current audit records in docs/data/run-card.json and docs/audit/current-review.md.
A future candidate may only be built after the official inputs, compliant shared
evaluator, literal registry gates, and separate slot selector are available.
EOF
exit 2

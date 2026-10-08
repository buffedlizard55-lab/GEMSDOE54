# Local competition data (not tracked)

Put only the competition-provided `training_features.tif` (or the reference-solution alias
`numeric_features.tif`), `labels.tif`, and `sample_submission.tif` here after obtaining them through
the competition's authorized download flow. Do not commit raw rasters, owner mirrors, or generated
submission files.

This checkout started without data or any data-download/evaluation/writer scripts. The supplied
DrivenData link is login-walled according to the project brief, and this environment cannot obtain
those files on the user's behalf. Do not substitute a sibling-repository mirror without recording
its provenance and passing the integrity checks in `scripts/audit_workspace.py`.

Run:

```bash
python -m pip install -e '.[test]'
python scripts/audit_workspace.py --data-dir data --output docs/data/workspace-audit.json
```

The audit is intentionally fail-closed. Passing file-format checks does not establish that the bytes
came from the organizer or that a model is scientifically valid.

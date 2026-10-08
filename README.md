# GEMSDOE54 — auditable GEMS research workbench

> **Current answer:** there is **no safe-to-submit GeoTIFF in this repository**. This checkout began with only a one-line README and still has no local competition rasters or authenticated DrivenData download. A separate read-only clone of the owner-maintained `GEMSDOE` template has a bridge whose five feature shards and three reconstructed files match both the bridge manifest and the committed runner-generated inventory; its feature cube is structurally varied. That establishes byte integrity against owner pins, not organizer origin. The inspected shared holdout assigns spatial blocks rather than whole fault segments, so it does not meet this project's required hide-and-recover protocol. The separate `GEMSDOE52` cache fails its own pins and has a constant feature cube. No candidate was fabricated, no HOLDOUT-DTI was reported, and no weekly submission slot was used. The website therefore says **DO NOT UPLOAD** rather than presenting a misleading download button.

## Read before every session

Read this README, the [standing project brief](docs/brief.md), [current irregularities](docs/audit/irregularities.md), the [power-analysis protocol](docs/research/power-analysis.md), and the [current run card](docs/data/run-card.json). The brief is the maintained prompt-derived project contract. Preserve and append corrections; do not turn unverified claims into facts.

## Mission and core values

Build an auditable research and submission-support project for the DOE GEMS / DrivenData challenge, maximizing the probability of a scientifically valid, reproducible result. **Own the outcome:** carry input provenance, leakage, holdout uncertainty, GeoTIFF validity, uniqueness, download behavior, and the final submission decision through the entire workflow.

The accessible official reference notebook describes a **fault-detection** workflow. A predicted fault raster is not by itself a confirmed geothermal vent, productive resource, or geological discovery. Keep those questions separate.

## Hard protocol

- Use the canonical shared feature stack, hide-and-recover evaluator, and submission writer when available; do not keep a private fork. The inspected shared `GEMSDOE` template has a checksum-pinned feature bridge, a spatial-block evaluator, and `src/submission_io.py`, but its holdout unit is not whole fault segments and therefore fails this project's required evaluation contract. No private replacement was created.
- Hold out whole fault segments with a buffer; derive catalogue-based features only from visible faults; mask visible faults pixel-exactly; score pooled DTI with alpha 0.2, beta 0.8, and a 300 m triangular kernel. Record the evaluator version, withheld-positive count, and paired 95% CI.
- Run a feature-alone leakage canary before trusting any feature; AUC above 0.90 is leakage until explained.
- Check power before ranking tiny DTI changes. Pixels are not independent when clustered along fault segments; use whole-segment/spatial-block bootstrap uncertainty. A projection is never a score.
- Compare decoded rasters with the registry before placement and after finalization. Stop and record a duplicate if rank-correlation exceeds 0.90 or more than 70% of emitted dots fall within 3 pixels of one prior raster.
- Stay within the assigned method lane. Stop after three experiments or two hours. Negative results are deliverables. The experiment step does not pick or promote submissions; promotion is a separate selector step under the live weekly cap.
- Do not copy prior submission rasters. A new filename or compression is not a new prediction.
- Only show a one-click download when a real candidate exists. State separately whether it is format-valid and whether it is approved to upload. Give a unique submission name and a short note of at most 140 characters.

The [full working brief](docs/brief.md) contains the remaining user requirements, including hypothesis preregistration, official-source review, three-pass implementation review, the executive submission guide, and the fixed-branch PR workflow.

## Current audit findings

1. **This checkout is a scaffold, not the previous project implementation.** At the start of the session, `git ls-files` contained only `README.md`; there was no `scripts/download_competition_data.sh`, `scripts/prepare_data.py`, `evaluate_holdout.py`, `submission_writer.py`, input data, or site.
2. **No authenticated competition download or local rasters exist in this checkout.** The DrivenData data page requires login, which was not available; access controls were not bypassed and no credentials were requested. A separate owner-maintained template bridge was fetched through public GitHub and all shard/file hashes match its own manifest and committed inventory. This is byte-integrity evidence only; it does not establish organizer origin. See [the bridge audit](docs/audit/pinned-template-cache-audit.json).
3. **The available shared evaluator does not meet the required holdout unit.** The inspected template holds out 512-pixel spatial blocks with a 3-pixel collar; it does not assign whole fault-segment components as the holdout unit. The shared writer exists as `src/submission_io.py`, but no candidate was produced and no private evaluator was created. No compliant HOLDOUT-DTI was computed.
4. **A separate sibling cache is unsafe to use.** The read-only `buffedlizard55-lab/GEMSDOE52` checkout has training, label, and sample-submission TIF bytes that fail its own manifest hashes, and its feature raster has no nonconstant band on the valid footprint. See [that separate audit receipt](docs/audit/sibling-cache-audit.json).
5. **No holdout power result exists.** The hash-matched owner-mirror labels have a total positive-pixel count, but it is not a withheld-positive count or an independent sample size. Cohen's d needs independent units and variance; a raw pooled-DTI detection floor requires paired bootstrap variability. The [power tool](scripts/power_analysis.py) accepts only a frozen compliant holdout receipt. None exists here.
6. **The H33 score attribution is unconfirmed.** The accessible owner-side H33 audit describes the named raster as a catalogue-proximity pruning variant of a prior emission. This is a plausible placement/false-positive mechanism, not proof of why a hidden leaderboard score occurred. The score-to-file association has no organizer receipt in this checkout. See [the forensic note](docs/research/why-h33.md).
7. **No candidate passed validation.** There is no new raster to compare with the registry, no leakage canary, and no holdout result. The run card is explicitly negative.

The brief's leaderboard values are retained only as user-supplied leads. They are not labeled `ORGANIZER-CONFIRMED` without a copied submission-page receipt. They are not `HOLDOUT-DTI` because they are not local holdout measurements. No projection is reported as a score.

## Project contents

- [Executive summary and submission steps](docs/executive-summary.html) — explains the portal range error and the exact pre-upload gates; currently states that no file is safe to upload.
- [Research dashboard](docs/research.html) — power, holdout, hypotheses, and study limitations.
- [Sources and verification status](docs/sources.html) — organizer/official links separated from owner-maintained prior art.
- [Ranked hypothesis backlog](docs/research/hypotheses.md) — proposals are explicitly not findings or confirmed globally untried methods.
- [Current workspace audit](docs/data/workspace-audit.json) — the checkout itself still has no local input rasters.
- [Pinned template cache and shared-tool audit](docs/audit/pinned-template-cache-audit.json) — checks the separate owner bridge's shard/file hashes and records why its spatial-block evaluator is not compliant with the whole-segment protocol.
- [Machine-readable run card](docs/data/run-card.json)
- [Local status feed](docs/data/feed.json) — refreshed from repository-local audit records by the Pages workflow; it deliberately does not scrape the competition leaderboard.
- [Irregularities ledger](docs/audit/irregularities.md)

## Safe local checks

Install the small audit/test dependencies:

```bash
python -m pip install -e '.[test]'
python -m pytest
```

Check whether authorized competition inputs have been placed locally:

```bash
python scripts/audit_workspace.py --data-dir data --output docs/data/workspace-audit.json
```

That command is deliberately fail-closed. It checks grids, finite data, informative feature bands, labels, and declared hashes. A matching local hash is not proof of organizer provenance, and an input audit is not a holdout or submission approval.

When a frozen, compliant receipt from the **shared** evaluator is available, compute the power report with:

```bash
python scripts/power_analysis.py path/to/frozen-holdout-receipt.json
```

When an independently built candidate and the organizer sample raster are available, check the candidate with:

```bash
python scripts/validate_submission.py path/to/candidate.tif --reference data/sample_submission.tif
```

The validator requires one band, exact reference CRS/shape/transform, and finite values within [0, 1] across the stored raster. It does not make an unvalidated candidate safe to upload.

## Official and review sources

- [Competition overview](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/) — user-supplied; not fetched in this session.
- [Competition about page](https://www.drivendata.org/competitions/306/competition-doe-gems/page/968/) — user-supplied; not fetched.
- [Competition data page](https://www.drivendata.org/competitions/306/competition-doe-gems/data/) — no authenticated data download in this session.
- [Official reference-solution repository](https://github.com/drivendataorg/gems-prize-reference-solution) — public code inspected; see its README/notebook for the reference workflow.
- [DOE/INGENIOUS GDR submission](https://gdr.openei.org/submissions/1391), [USGS GeoDAWN](https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and), and [NREL/DOE PDF](https://docs.nlr.gov/docs/fy26osti/96647.pdf) — supplied for manual review; not fetched here.

The [source register](docs/sources.md) records what was and was not verified in this session. User-provided links and public sibling repositories are not silently promoted to official evidence.

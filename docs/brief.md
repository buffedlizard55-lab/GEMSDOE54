> **Run 2 update (2026-10-08).** This document is the run-1 record. Current state: [download and verdict](../index.html) (own-model TIF for review only, not cleared to submit), [holdout v2](../holdout.html), [0.2778 mechanism](../top-artefact.html), and the README status block. Where this file conflicts with those, they win.

# Standing project brief

Read this document and the current run card before every session. It is the maintained working form of the full user request; append corrections rather than silently replacing prior requirements.

## Mission

Build an auditable research and submission-support project for the DOE GEMS / DrivenData challenge. The competition work is a **fault-detection raster** task; a fault prediction is not itself a verified geothermal vent, resource, or discovery. The objective is to improve the probability of winning while preserving scientific validity, reproducibility, and honest uncertainty.

## Non-negotiable research protocol

- Use the shared/canonical feature stack, holdout evaluator, and submission writer when they exist. Do not clone or privately fork a shared evaluator. If a canonical tool is wrong, report and repair it in the template through the supported process.
- Hold out whole fault segments with a buffer. Recompute every catalogue-derived feature using only visible faults. Mask visible catalogue pixels exactly. Score pooled DTI with alpha 0.2, beta 0.8, and a 300 m triangular kernel. Record evaluator version, withheld-positive count, and paired 95% confidence interval.
- Test each feature alone on the holdout before combining it. AUC above 0.90 is a leakage canary until ruled out.
- Check power before interpreting small DTI differences. Use Cohen's standardized effect framework, but treat whole withheld fault segments—not every pixel or generic spatial block—as the independent units. Report the withheld-positive count as context and use paired whole-segment cluster-bootstrap uncertainty for pooled DTI.
- Stay within the assigned experiment lane; stop if absolute rank-correlation with any registry raster exceeds 0.90 or more than 70% of candidate support/dots lie within 3 pixels of one registry raster. Screen the continuous surface before placement and the final raster after writing; never waive a threshold silently.
- Stop after three experiments or two hours, whichever comes first. A negative result is a valid deliverable. Do not select or promote a submission in the experiment step; promotion is a separate selector decision under the live weekly cap.

## Artifact requirements

- Never copy a prior prediction as a new submission. A new filename or compression is not a new prediction; compare decoded pixels.
- A candidate must be a single-band GeoTIFF matching the verified CRS, dimensions, transform, and scored footprint. Require finite [0, 1] values inside the scored footprint. Prior repository notes and the cached sample mirror indicate null/NaN outside it; confirm that rule against the live official instructions before upload. The available local "sample" mirror contains label values and is not an authenticated blank template.
- Put the artifact link at the top of the site only when a verified candidate exists. State plainly whether it is safe to download and whether it is approved to upload. Format validation alone is never upload approval.
- Give each approved candidate a unique submission name and a short identifying note (keep notes at or below 140 characters for this project). Do not spend a weekly slot unless a comparable, whole-fault-segment hide-and-recover holdout beats the incumbent and its gate is open.
- End each experiment with a JSON run card containing hypothesis, mechanism, named non-fault mimic, HOLDOUT-DTI plus evaluator/sample/95% CI, correlation/overlap versus registry, raster SHA-256, validator output, submission name/note, and promote/negative verdict. A projection is never written as a score.

## Research and evidence

- Produce a ranked list of three to five candidate geological hypotheses before implementing a new method. Each must specify the layers, physical signature, reason it could reveal faults missing from USGS/INGENIOUS, prior-art boundary, non-fault mimic, data needs, and implementation cost.
- If new external data are needed, name the specific free official source and check exact availability, license, and footprint coverage before declaring the hypothesis viable.
- Separate organizer-confirmed scores from local HOLDOUT-DTI and owner-reported claims. Copy an organizer result only from a submission-page receipt; do not convert a projection or a remembered leaderboard value into a score.
- Keep a curated current-status feed and an audit ledger so routine checks are automated. If an external feed cannot be accessed, publish “not checked” rather than inventing a refresh.
- Link official sources for manual review, record source versions and checksums, and flag irregularities.

## Site and workflow

- Maintain a clean GitHub Pages site with a prominent executive summary and one-page exact submission instructions, including the [0,1] range requirement, expected georeferencing, unique name, and note.
- Keep the complete research trail and machine-readable receipts alongside the site. Make download/submit status unambiguous.
- Work through three reviews: implementation and verification; bug/edge-case review and fixes; final line-by-line check against this brief.
- Own the outcome: report limitations and next work; do not hide failed experiments or data-integrity defects.
- Follow the session's fixed Arena branch and PR workflow; do not change branches.

## Current session boundary

The current checkout contains owner-mirrored labels and SGMC-derived fault rasters, but no full competition feature cube, authenticated blank sample submission, or authenticated DrivenData download. The archived H54-A TIFF is not upload-approved: the current literal lane checker flags it as duplicate, and the updated conservative format check also flags finite zeros outside the footprint. The public owner-maintained GEMSDOE bridge at commit `dcbbb192e56b2b32c0a131eba791dc363305d4a3` exposes a spatial-block evaluator and `submission_io.py`, not the named whole-segment `evaluate_holdout.py` / `submission_writer.py`; its pins do not authenticate organizer origin. Two surface-only preflights crossed the literal raw-overlap gate and stopped before emission. The correct result is a negative run card, no new TIF, and a fail-closed site; do not fabricate a score or use a weekly slot. User/owner leaderboard values remain unverified until copied from an organizer submission-page receipt.

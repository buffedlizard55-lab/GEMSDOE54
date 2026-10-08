# Standing project brief

Read this document and the current run card before every session. It is the maintained working form of the full user request; append corrections rather than silently replacing prior requirements.

## Mission

Build an auditable research and submission-support project for the DOE GEMS / DrivenData challenge. The competition work is a **fault-detection raster** task; a fault prediction is not itself a verified geothermal vent, resource, or discovery. The objective is to improve the probability of winning while preserving scientific validity, reproducibility, and honest uncertainty.

## Non-negotiable research protocol

- Use the shared/canonical feature stack, holdout evaluator, and submission writer when they exist. Do not clone or privately fork a shared evaluator. If a canonical tool is wrong, report and repair it in the template through the supported process.
- Hold out whole fault segments with a buffer. Recompute every catalogue-derived feature using only visible faults. Mask visible catalogue pixels exactly. Score pooled DTI with alpha 0.2, beta 0.8, and a 300 m triangular kernel. Record evaluator version, withheld-positive count, and paired 95% confidence interval.
- Test each feature alone on the holdout before combining it. AUC above 0.90 is a leakage canary until ruled out.
- Check power before interpreting small DTI differences. Use Cohen's standardized effect framework, but treat whole withheld fault segments—not every pixel or generic spatial block—as the independent units. Report the withheld-positive count as context and use paired whole-segment cluster-bootstrap uncertainty for pooled DTI.
- Stay within the assigned experiment lane; stop if a candidate's rank-correlation with a registry raster exceeds 0.90 or more than 70% of emitted dots lie within 3 pixels of one registry raster. Run this uniqueness gate before placement and after finalization.
- Stop after three experiments or two hours, whichever comes first. A negative result is a valid deliverable. Do not select or promote a submission in the experiment step; promotion is a separate selector decision under the live weekly cap.

## Artifact requirements

- Never copy a prior prediction as a new submission. A new filename or compression is not a new prediction; compare decoded pixels.
- A downloadable candidate must be a single-band GeoTIFF matching the official sample submission's CRS, dimensions, transform, and footprint. All stored values must be finite and in [0, 1] to avoid the known portal range error.
- Put the artifact link at the top of the site only when a verified candidate exists. State plainly whether it is safe to download and whether it is approved to upload. Format validation alone is never upload approval.
- Give each approved candidate a unique submission name and a short identifying note (keep notes at or below 140 characters for this project). Do not spend a weekly slot unless a comparable spatially blocked holdout beats the incumbent and its gate is open.
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

This checkout has no local competition rasters and no authenticated DrivenData download. A separate read-only clone of the owner-maintained GEMSDOE template has a bridge whose shard/file hashes match its manifest and committed inventory, and whose feature cube is structurally varied; this proves integrity against owner pins, not organizer origin. Its shared holdout assigns spatial blocks rather than whole fault segments, so it cannot produce the required HOLDOUT-DTI. The separate GEMSDOE52 cache still fails its own hashes and has a constant feature cube. The correct outcome is a negative run card and fail-closed site, not a fabricated raster. The cited leaderboard values remain unverified until an organizer receipt is available.

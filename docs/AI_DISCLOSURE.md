# Disclosure of generative-AI use

The DOE/NLR GEMS Prize Official Rules (September 2026), section 3.2, require competitors to
"indicate in the narrative (not included in the word count) the extent to which, if any, you used
generative AI technology and how you used it to develop your submission (including all submission
elements described in this official rules document)".

**Extent of use.** This repository and the artefact it publishes were produced by an autonomous
AI agent session. Generative AI was used for all of the following:

- reading the organizer's problem description, the public leaderboard, and the DOE/NLR rules PDF,
  and transcribing the metric definition;
- writing the source code (`scripts/`, `src/`), the tests, and this documentation;
- designing the dot-emission rule and the linearity gate, and deriving the mass/credit algebra;
- running the analyses whose receipts are in `evidence/` and `registry/`;
- writing the GitHub Pages site.

**What was verified rather than generated.** The metric implementation is regression-tested against
the organizer's own published worked example (reproduces 0.602652 against a stated 0.60). Input
raster hashes were recomputed from bytes. Every quantitative claim in this repository is traceable to
either a fetched page or a file whose SHA-256 is recorded. Where a number is a model rather than a
measurement it is labelled `MODEL`; where a number is a screening proxy rather than a score it is
labelled `PROXY-DTI`.

**Competitor responsibility.** The rules place responsibility for the accuracy, authenticity and
authorship of the submission on the competitor, and note that relying on generative AI may introduce
risks including fabrication and falsification. The single largest such risk in this artefact is
recorded in `registry/run_card.json` under
`named_non_fault_process_that_could_mimic_it`: pre-Quaternary faults in the state map compilation
carry no surface scarp and are probably not in the experts' label set, and nothing in the current
design removes them. Anyone submitting this artefact should be satisfied with that exposure first.

## Addendum, session 2026-10-08 (whole-segment holdout and rules gate)

Required by rules §3.2 to be stated in the narrative. The extent and the use of generative AI in this session:

- **Generated with AI assistance:** the new scripts `scripts/sibling_uniqueness.py`, `scripts/holdout_segment_cv.py`, `scripts/make_run_card.py`, `scripts/detection_floor.py`, `scripts/top_artefact_analysis.py`, `scripts/inventory_siblings.py`, `scripts/fetch_sibling_rasters.sh`, the tests in `tests/test_segment_cv.py`, and the pages `docs/rules-gate.html`, `docs/top-artefact.html`, `docs/holdout.html`, `docs/executive-summary.html`, `docs/hypotheses.html`.
- **Verified rather than generated:** the rule quotations in `docs/rules-gate.html` were copied from the official PDF and checked against the fetched text. The metric identity in `docs/top-artefact.html` is checked numerically (`tests/test_segment_cv.py`, `scripts/top_artefact_analysis.py`). The submission was rebuilt from `scripts/build_submission.py` into scratch space, and its SHA-256 matched the shipped file byte-for-byte (`b430615a…`). Every number in the evidence files is written by a script from a file hash or raster read. No number was typed by hand into the run card.
- **Not generated and not verified by us:** the DrivenData leaderboard, the data tab (login-gated), the top-artefact board values (0.2708, 0.2778), and the owner's audit fields. These are labelled BOARD-UNVERIFIED or OWNER-RECORDED wherever they appear.
- **Human responsibility:** under §3.2 the registered competitor is responsible for the accuracy and authorship of the submission, including AI-generated content. The competitor must confirm this disclosure before any upload.

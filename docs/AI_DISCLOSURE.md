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

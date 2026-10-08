# Source register and verification status

The site keeps organizer/official sources distinct from owner-maintained project records. A URL supplied by the user is linked for manual review but is not labelled verified unless it was accessible and inspected in this session. Machine-readable register: [`data/source-register.json`](data/source-register.json).

| Source | Link | Session status | Use / caveat |
|---|---|---|---|
| Competition problem description / metric | [DrivenData overview](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/) | User-supplied; not fetched here. | Do not rely on an unverified recollection for metric semantics. |
| Competition about page | [DrivenData about](https://www.drivendata.org/competitions/306/competition-doe-gems/page/968/) | User-supplied; not fetched here. | Label provenance and domain context need review. |
| Organizer data download | [DrivenData data tab](https://www.drivendata.org/competitions/306/competition-doe-gems/data/) | No authenticated download in this session. | Only trusted route for the private competition rasters. |
| Official reference implementation | [DrivenData GitHub repository](https://github.com/drivendataorg/gems-prize-reference-solution) | Public repository inspected at commit `aebe92f7c8a990f0e3443451b7a825d9afd6336b`. | Its notebook documents a U-Net patch workflow; it is not an organizer score receipt and its input filename differs from the brief. |
| DOE/INGENIOUS repository | [GDR submission 1391](https://gdr.openei.org/submissions/1391) | User-supplied; not fetched here. | Potential well/spring source; schema/license not verified. |
| USGS GeoDAWN | [USGS GeoDAWN data page](https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and) | User-supplied; not fetched here. | Official data lead; bytes not obtained. |
| Submission/method PDF | [NREL PDF](https://docs.nlr.gov/docs/fy26osti/96647.pdf) | User-supplied; not fetched here. | Manual review needed for scope/format statements. |
| H33 prior-art record | [GEMSDOE32 README at pinned commit](https://github.com/buffedlizard55-lab/GEMSDOE32/blob/0d6a6243147cd63a2000412d575d4c80a36d3a62/README.md) and [audit receipt](https://github.com/buffedlizard55-lab/GEMSDOE32/blob/0d6a6243147cd63a2000412d575d4c80a36d3a62/docs/downloads/gemsdoe32-h33-h33-2-b2-20261004T220000Z-e5eb6e7e-audit.json) | Owner-maintained; read-only review. | Evidence about what the owner says the raster construction was, not proof of its organizer score. |
| Sibling cache provenance | [GEMSDOE52 data manifest](https://github.com/buffedlizard55-lab/GEMSDOE52/blob/24c2630a9dfd69e6cef52495d8e3066d7d37b9d4/registry/data_manifest.json) | Owner-maintained; inspected. | Its own text says owner mirror, not organizer-authenticated. Checked-in bytes fail its hashes and feature-variance audit. |
| Shared-template data bridge | [GEMSDOE pinned commit](https://github.com/buffedlizard55-lab/GEMSDOE/tree/dcbbb192e56b2b32c0a131eba791dc363305d4a3) | All bridge part/file hashes match both the bridge manifest and committed inventory; origin is not organizer-authenticated. | Exact bytes were reconstructed and structurally audited in `/tmp`; they were not copied into this checkout or used in an experiment. The shared holdout uses spatial blocks, not the required whole fault segments. See [audit receipt](audit/pinned-template-cache-audit.json). |
| Copernicus Sentinel-1 portal | [Copernicus Data Space](https://dataspace.copernicus.eu/) | Candidate source; coverage/access not checked. | Future InSAR hypothesis only. |
| NASA ASF DAAC | [ASF search](https://search.asf.alaska.edu/) | Candidate source; coverage/access not checked. | Future InSAR hypothesis only. |
| USGS Landsat | [Landsat Collection 2](https://www.usgs.gov/landsat-missions/landsat-collection-2) | Candidate source; coverage/access not checked. | Future seasonal thermal hypothesis only. |
| USGS groundwater data | [NWIS / Water Data](https://waterdata.usgs.gov/nwis) | Candidate source; station availability/access not checked. | Future groundwater hypothesis only. |

## Source policy

- Every external data asset needs a stable source URL, version/date, license/terms, checksum, processing lineage, and a record of which holdout folds used it.
- A SHA-256 match proves equality to a declared digest, not who supplied the bytes.
- Owner sites and local score ledgers are priors for investigation, not organizer confirmation.
- Do not claim a source is obtainable until an actual request/download succeeds from the permitted environment and the exact relevant data coverage is inspected.

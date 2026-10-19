# research-publish-packages

This repository is the **landing page and public issue tracker** for a released research
artifact — the **encoder-crossover-190** (EXP12) dataset deposit. It hosts a browsable copy of
the released files and is the intended contact route for corrections and for commercial
licensing enquiries.

## The authoritative copy is on Zenodo

The released data and verification tooling are **published on Zenodo**. That archive — not this
repository — is the **authoritative, citable copy** of the release:

> **DOI: [10.5281/zenodo.23463945](https://doi.org/10.5281/zenodo.23463945)**
> (concept DOI, which survives new versions: [10.5281/zenodo.23463944](https://doi.org/10.5281/zenodo.23463944))

Please cite the **Zenodo archive**. Quote the DOI from the archive when you cite the release, and
verify any file against the archive's copy if the two ever differ. The files here are provided so
the tooling is browsable and reviewable; where the Zenodo archive and this repository disagree,
**the archive wins.**

## What the release is

Released data and verification tooling for the paper

> *The small-encoder crossover is a prompted-baseline artefact: a fine-tuned encoder head loses to a
> fine-tuned 4B decision model by 0.33 and to a majority-class control*
>
> Aswin Ram Kalugasala Moorthy (2026)

The release contains:

| path | contents |
|---|---|
| `fixture/` | the sealed 190-case decision instrument (`fixture-190.json`), its TypeScript source and case schema |
| `results/` | the frozen per-arm evaluation records and `REPORT.md` — the published numbers |
| `verify/` | `recompute-claims.py` — re-derives every headline number from the bytes shipped in the release |
| `second-labeller/` | the independent second-labelling tooling, labels, disagreement record and metrics |
| `preregistration/` | the pre-registered protocol |
| `CITATION.cff`, `MANIFEST.json` | deposit citation and integrity manifest (both as published on Zenodo) |
| `LICENSE`, `COMMERCIAL.md`, `CONTRIBUTING.md` | licence, commercial terms, contribution terms |
| `README_DEPOSIT.md` | the deposit's own front matter, as published on Zenodo |

## What the release is *not*

- **The measurement harness is withheld.** There is no `harness/` directory, and none of the
  collection, preparation, training, evaluation, analysis or linting code that produced the numbers
  in `results/` is distributed. No model weights ship either.
- **This is not a reproduction package.** Nothing here lets a reader retrain an arm, reconstruct the
  model inputs, or re-run the measurement. The shipped checks re-derive the published numbers **from
  the stored records** — they do not retrain, re-render a model input, or re-run the pipeline.
- **This is not the paper text.** The manuscript is a separate work under CC BY 4.0.

The exact checks and their expected output are documented in `README_DEPOSIT.md`.

## How to cite

If you use the released data or verification tooling, please cite the Zenodo deposit:

> Kalugasala Moorthy, A. R. (2026). *The small-encoder crossover is a prompted-baseline artefact: a
> fine-tuned encoder head loses to a fine-tuned 4B decision model by 0.33 and to a majority-class
> control* [Data set]. Zenodo. https://doi.org/10.5281/zenodo.23463945

A machine-readable `CITATION.cff` ships with the release and records the same citation. The version
DOI is `10.5281/zenodo.23463945`; the concept DOI `10.5281/zenodo.23463944` should be used if you
need a reference that survives future versions.

## Licence and commercial use

The released files are **source-available under the [PolyForm Noncommercial License
1.0.0](https://polyformproject.org/licenses/noncommercial/1.0.0)** — see `LICENSE`. That licence
covers permitted **noncommercial** purposes only.

**Any commercial use requires a paid commercial licence**, obtained directly from the author as a
separate written agreement; the Noncommercial licence grants no commercial right and there is no
free commercial evaluation or trial. The full statement of what is and is not covered is in
`COMMERCIAL.md`.

**To ask about a commercial licence, open an issue on this repository** — that is the project's own
public contact channel, and it avoids publishing a personal address. Nothing is granted by opening
an issue; the licence is a separate written agreement agreed afterwards.

The terms above grant **no rights in the withheld harness**.

## Issues are the contact route

This repository's issue tracker is the intended route for **corrections, questions and licensing
enquiries**. If you find a problem — with a published number, a shipped record, or this repository —
please open an issue.

Per `CONTRIBUTING.md`: **ideas and corrections are welcome; code contributions and patches are not
accepted or merged.** The author integrates by re-implementation, because verbatim-contributed code
would carry the contributor's own noncommercial licence and could never enter a paid tier. Send a
description of the problem and the approach you would take, not a patch.

## Note on file integrity

Everything in this repository is byte-identical to the corresponding file in the published Zenodo
archive, **with exactly one exception**: the package's own `README.md` (which describes the archive's
directory buckets) is replaced here by this landing page, because this repository needs a README that
describes the repository. Consequently:

- `MANIFEST.json` is the manifest of the Zenodo archive tree, shipped unmodified. Its single entry for
  `README.md` refers to the archive's `README.md`, not to this page, so re-running the `MANIFEST.json`
  re-hash described in `README_DEPOSIT.md` will report `README.md` — and only `README.md` — as a
  mismatch here. That is expected and is a difference of this mirror, not of the archive.
- The archive's `README.md`, and the manifest entry for it, remain authoritative on Zenodo.

To check any other file, compare its sha256 against the `MANIFEST.json` entry — every other entry
describes the file shipped here exactly.

**Update:** `MANIFEST.json` here has since been regenerated over this repository's own tree, so the
`MANIFEST.json` re-hash described in `README_DEPOSIT.md` now reports zero mismatches for the files
shipped here; the archive's `MANIFEST.json` on Zenodo remains authoritative for the archive tree.

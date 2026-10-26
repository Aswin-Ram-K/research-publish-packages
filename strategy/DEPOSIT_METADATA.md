# DEPOSIT_METADATA.md — copy-paste metadata sheets for the two deposit services

Unit **UDEPOSITDOC1**. Author byline of record: **Aswin Ram Kalugasala Moorthy** (name only, no
affiliation). Everything below is the literal value to paste. Field values are sourced from
`strategy/ZENODO_DEPOSIT.md`, `strategy/DEPOSIT_ARCHIVE.md`, `strategy/TMLR_POLICY.md`,
`scratch/urelease9/zenodo/ZENODO_UPLOAD.txt`, `papers/encoder-crossover-190/submission/METADATA.md`,
`papers/encoder-crossover-190/submission/ABSTRACT_METADATA.txt` and measurements made on disk by this
unit. Where a source disagrees with another source, the disagreement is **recorded in §5**, not silently
resolved.

**Nothing here is uploaded, submitted, registered or contacted. Nothing was published.**

**AUTHORITY (UDEPOSITDOC2, 2026-10-17).** This file is the **single authoritative source for every
deposit form field value** — Zenodo (§1) and Preprints.org (§2). Change a field value here and it is
changed everywhere; do not paste a field value out of any other file.
`strategy/SUBMISSION_RUNBOOK.md` is authoritative for **order of operations only**.
`scratch/urelease9/zenodo/ZENODO_UPLOAD.txt` is authoritative for the **licence-wording record and the
archive digest record only**; its form-field values (upload file, resource type, version, description,
keywords, title) are **SUPERSEDED 2026-10-17** and are annotated in place there.
`strategy/ZENODO_DEPOSIT.md` is the **historical plan**; its §3 description is carried here verbatim, and
its §2 sentence "optional second type `Software`" is **superseded as factually wrong** (§1.2 below).
§5 below **resolves** the six divergences with a stated reason for each choice.


---

## §0 The files, with digests re-measured on disk by this unit

| # | path | bytes | sha256 | members |
|---|---|---|---|---|
| **A** | `papers/encoder-crossover-190/released/encoder-crossover-190-released.tar.gz` | **159,014** | `478941c0259b9309145aea17413c3795d0078c2994d32739a01ff09fc51e89d7` | **37** = 1 top-level dir (`encoder-crossover-190-released/`) + 5 subdirs + 31 files; its own `MANIFEST.json` lists 30 of the 31 files (all but itself), `counts.files` 31, `counts.bytes_total` 844,708 |
| **B** | `scratch/ulicfix1/zenodo/research-publish-packages-encoder-crossover-190-v1.zip` | **169,869** | `8e2f603efdf7990b4decb1d73bf14002c53d1da47ab48c482a4217a3b5183610` | **29** files **at the archive root, no wrapper directory** |
| — | `scratch/uneutral10/package/MANIFEST.json` | 11,043 | `fecdc1fbf67820be2b9988008453282d9f0e4663d9a90551684e1a0f57d9494a` | — |

**Deposit file A's md5** (added by UDOCFIX1 2026-10-18, measured on disk): `4066c3428c1e4836d200909c6a2db6b0`.

Superseded (retained as history): UDEPOSITDOC2 measured A at **157,650** B on 2026-10-17,
`7389bd879e970d840a528a9a19bfb9a6623babf3ec10746b18fc616bf2b4dad3`; UDEPOSITDOC1 had measured
**157,305** B, `778818b242922fc1afde984b27c0dfb7c79be7647b6f5146269b1c2ec2026bdb`. Neither is the
upload candidate. Re-measured on disk by **UFIXDEP1** on 2026-10-18, after the archive's manifest was
rebuilt to describe the archive itself; rebuilt again by **UREADMEFIX1** on 2026-10-18 (dead paths in the front-page `README_DEPOSIT.md`) and re-measured on disk by **UDOCREFRESH1** on 2026-10-18.

Re-measure before upload with:

```sh
sha256sum papers/encoder-crossover-190/released/encoder-crossover-190-released.tar.gz \
          scratch/ulicfix1/zenodo/research-publish-packages-encoder-crossover-190-v1.zip
stat -c '%s %n' papers/encoder-crossover-190/released/encoder-crossover-190-released.tar.gz \
               scratch/ulicfix1/zenodo/research-publish-packages-encoder-crossover-190-v1.zip
```

### Recommendation: upload **file A**, the tarball — one file only

Reasons, in order:

1. **A has one top-level directory; B does not.** Extracting A cannot explode 31 files into the
   author's working directory. B's 29 members sit at the archive root, so extracting B *does*. That
   exact property is why `strategy/ZENODO_DEPOSIT.md` §12 disqualified the earlier `uauclean1` zip.
2. **A is a superset of B.** A = B's 29 payload files (all 29 sha256-verified byte-identical to
   `scratch/uneutral10/package`) **plus** `CITATION.cff` and `README_DEPOSIT.md` — the two deposit-only
   extras that give the record a machine-readable citation and a front page.
3. A is the file `strategy/ZENODO_DEPOSIT.md` §1 names as the upload file.

**Author-overridable.** Use **B instead** only if the author prefers the `-v1` filename and does not
mind root-level members; if B is used, the version field becomes `v1` (§1) and the two extras are absent.

**Never upload** `scratch/uauclean1/zenodo/research-publish-packages-encoder-crossover-190-v1.zip`
(`2338ed02c1c6770b182a79355dbda36cb6d593e08e65a3d38ae9da369c4b048f`) or either superseded archive:
`7389bd879e970d840a528a9a19bfb9a6623babf3ec10746b18fc616bf2b4dad3` (157,650 B, superseded
2026-10-18) and `778818b242922fc1afde984b27c0dfb7c79be7647b6f5146269b1c2ec2026bdb` (157,305 B).

---

## §1 ZENODO — paste block

One value per line; the left side is the form's field.

```
Upload type:            Dataset
Title:                  encoder-crossover-190 — released data and verification tooling
Creators:
  Given names:          Aswin Ram
  Family name:          Kalugasala Moorthy
  Name (as displayed):  Aswin Ram Kalugasala Moorthy
  Affiliation:          (leave empty)
  ORCID:                (leave empty)
Description:            see §1.1 — paste verbatim
Licence:                polyform-noncommercial-1.0.0
Licence scheme:         spdx
Licence (displayed):    PolyForm Noncommercial License 1.0.0
Version:                (leave empty)
Language:               English
Keywords:                                       text classification benchmark
                        encoder classifiers
                        fine-tuned decision model
                        sealed evaluation
                        majority-class control
                        McNemar exact test
                        reproducibility
                        withheld evaluation harness
Related identifiers:    (leave empty at first publication — see §1.3)
Publication date:       (Zenodo stamps it — do not back-date)
DOI:                    (minted by Zenodo on publish — see §1.3)
```

### §1.1 Description — paste verbatim

> Released **data and verification tooling** for the paper *"The small-encoder crossover is a
> prompted-baseline artefact: a fine-tuned encoder head loses to a fine-tuned 4B decision model by 0.33
> and to a majority-class control"*. This deposit is **not** the paper text and **not** the measurement
> harness. It contains the sealed 190-case typed-single-label decision fixture and its schema; the frozen
> per-arm evaluation records, the per-case baseline rows and the report the published numbers rest on; the
> pre-registered protocols; the independent second-labelling record with its disagreements and metrics;
> and the scripts that re-derive the published numbers **from those stored records**.
>
> The evaluation harness — the collection, preparation, training, evaluation, analysis and linting code,
> its frozen data, and all model weights — is **withheld by the author's decision**. The checks in this
> deposit therefore **re-derive the published numbers from the stored records; they do not retrain an
> arm, do not re-render a model input and do not re-run the evaluation pipeline.** A reader cannot
> reproduce the measurement from this deposit alone, and this record does not claim that they can. One
> published value (the 0.6684 `decider-4b` baseline) is carried as a quoted constant and is compared,
> not re-derived; the verification script prints that boundary explicitly rather than hiding it.
>
> Released under the **PolyForm Noncommercial License 1.0.0**; commercial use requires a separately
> negotiated paid licence from the author. The paper text is separately licensed CC BY 4.0, and the main
> project repository remains proprietary and closed.

This is `strategy/ZENODO_DEPOSIT.md` §3 verbatim. It carries the required promise: the deposit
**verifies** the published numbers **from stored records** and **cannot reproduce the measurement**.
**Do not add any sentence promising that the deposit reproduces, re-runs or regenerates the
experiment** — the harness is withheld (`MANIFEST.json` records `"harness_revision": "WITHHELD"`).

*Optional.* If the form has an extra notes field, paste there:

> File: `encoder-crossover-190-released.tar.gz`, 159,014 bytes, sha256
> `478941c0259b9309145aea17413c3795d0078c2994d32739a01ff09fc51e89d7`, 37 members under the single
> top-level directory `encoder-crossover-190-released/` (its own `MANIFEST.json` lists 30 of the 31
> archive files - all but itself - with `counts.files` 31). The superseded 29-file zip
> `research-publish-packages-encoder-crossover-190-v1.zip` (169,869 bytes, sha256
> `8e2f603efdf7990b4decb1d73bf14002c53d1da47ab48c482a4217a3b5183610`) is **not** the upload —
> it is recorded only so a stray copy can be recognised and left out.

### §1.2 Upload type — the honest choice

**Recommendation: `Dataset`.** The artifact's primary value is a released **data** package: a sealed
190-case fixture, frozen per-arm records, per-case baseline rows, pre-registered protocols and a
second-labelling record. The scripts shipped alongside are *verification* tools that re-derive numbers
**from those stored records**; they are not the software of record (the harness is withheld), so they do
not make the record a software release, and `Dataset` does not misdescribe them.

**`Software` is also defensible** and is not wrong: the deposit ships runnable Python with a documented
exit-code contract, and `scratch/urelease9/zenodo/ZENODO_UPLOAD.txt` chose `Software`. If the author
prefers to foreground the tooling, pick `Software` — the record's contents are unchanged and only the
browse facet moves.

- **Do not select `Publication` / `Journal article`.** The paper is a separate work.
- **Author-overridable.** This is a judgement call, not a sourced fact; either choice is honest.
- **VERIFIED 2026-10-17 (UDEPOSITDOC2) — Zenodo allows exactly ONE resource type per record.** Its own
  help page states the choice for a mixed object, verbatim: "**Choose one type** — Choose the resource type
  which you think best describes and/or is most significant for the upload" or "**Split the upload** —
  Split the upload into multiple records, one per resource type"
  (<https://help.zenodo.org/docs/deposit/describe-records/resource-type/>). There is **no** "additional
  resource type" field. `strategy/ZENODO_DEPOSIT.md` §2's "optional second type `Software`" is therefore
  **SUPERSEDED (2026-10-17) and factually wrong** — do not add a second type; **keep `Dataset`**. The full
  vocabulary is 43 entries, fetched from
  <https://zenodo.org/api/vocabularies/resourcetypes?size=100> (`dataset | Dataset`, `software | Software`,
  `publication-preprint | Preprint`, …).

### §1.3 Related identifiers and the DOI — what can and cannot be filled now

| field | value now | what fills it, and when |
|---|---|---|
| **Related identifier → the paper** | **leave empty.** No DOI for the paper exists anywhere in the tree. | After the preprint is posted (runbook step 2), **edit the Zenodo record** and add relation **`is supplement to`** with the preprint DOI. |
| **Related identifier → the code repository** | **leave empty by default.** | Optional and author-only: relation **`is supplemented by`**, identifier `https://github.com/Aswin-Ram-K/research-publish-packages` — this URL is quoted from the payload's own `COMMERCIAL.md` (`ZENODO_UPLOAD.txt:81`). **The author must confirm that repository is public before linking it.** |
| **Version** | **leave empty.** | No version number was assigned by the author; `CITATION.cff` deliberately declares no `version`. Set `v1` only if the author uploads file **B** (§0) or names a version. |
| **DOI of this record** | **does not exist yet** — Zenodo mints it on publish. | After publish, paste it into the manuscript's data-availability section (`main.tex:405`) and, if desired, into `CITATION.cff`. **VERIFIED 2026-10-17 (UDEPOSITDOC2): the shape is `10.5281/zenodo.<id>`** — observed on live records
`10.5281/zenodo.23442810`, `10.5281/zenodo.23442780`, `10.5281/zenodo.23442772`
(<https://zenodo.org/api/records?size=3&sort=mostrecent>). The Zenodo help page documents DOIs but not the
prefix (<https://help.zenodo.org/docs/deposit/describe-records/reserve-doi/>), so the shape is recorded as
an observation. Copy the minted value; do not reconstruct it. |

---

## §2 PREPRINTS.ORG — paste block

One value per line; the left side is the form's field.

```
Title:                  The small-encoder crossover is a prompted-baseline artefact: a fine-tuned encoder head loses to a fine-tuned 4B decision model by 0.33 and to a majority-class control
Abstract:               see §2.1 — paste verbatim
Authors:                Aswin Ram Kalugasala Moorthy
Affiliations:           (leave empty — name-only byline is the author's standing decision)
Corresponding author:    AUTHOR-ONLY — the author supplies his own contact address
Subject area:           see §2.2 — REQUIRES THE AUTHOR TO PICK FROM PREPRINTS.ORG'S OWN LIST
Keywords:                                       text classification benchmark
                        encoder classifiers
                        fine-tuned decision model
                        sealed evaluation
                        majority-class control
                        McNemar exact test
                        reproducibility
                        withheld evaluation harness
Licence:                CC BY 4.0
DOI:                    (leave empty — see §2.3)
Article type:           Preprint article
File to upload:         the LaTeX SOURCE, zipped with every file needed to
                        rebuild the PDF: papers/encoder-crossover-190/submission/main.tex
                        (84,695 B, sha256 397713d74920e9e1bc5f5fb8dc6ef09fb5fa9e641583f0ecd16b718d5f9d09ca)
                        plus any .bib — Preprints.org accepts "Microsoft Word or
                        LaTeX format" only; a PDF alone is NOT an accepted source
                        format (§2.3). The rendered PDF is kept for the final record:
                        papers/encoder-crossover-190/rendered/encoder-crossover-190.pdf
                        (188,364 bytes, 25 pages,
                         sha256 752747f87423f1fa87cf365179ed1c93915ad65a1aed00e8d8929979964699a1)
```

### §2.1 Abstract — paste verbatim (1,195 chars, under the ~1,920-char metadata cap)

Source: `papers/encoder-crossover-190/submission/ABSTRACT_METADATA.txt`, byte-identical to what
`ZENODO_UPLOAD.txt:122` carries.

> Whether a cheap encoder-style classifier can substitute for a heavier decision model is usually tested against a prompted language model, not against a fine-tuned one. We run the like-for-like comparison on a sealed single-label decision task: 190 cases, 2 to 8 named options each, 74 distinct labels. Five encoder-based arms and one fine-tuned decision model see the same labels and the same cases. The best encoder arms reach kappa 0.347; the decision model reaches 0.679 on the declared primary baseline (0.668 on the published pre-registered one), a separation of about 0.33, with a paired McNemar exact p = 4.2e-09. A majority-class control scores 0.4526, beating every encoder arm by 0.105, and a shuffled-label control scores 0.2316, below the 0.2911 chance floor. The encoders therefore do not substitute for the decision model. We characterise the failure rather than only reporting it: the order-permutation probe flips zero cases, and the majority-class control shows the encoders lose to a constant answer. Scope: one task, one corpus, one decision model. The evaluation harness is withheld from release, so the recorded results can be verified but the measurement cannot be re-run.

The full abstract (`papers/encoder-crossover-190/submission/ABSTRACT.txt`, 3,462 B,
`eac59f0ed2840d903ea8fcdf54a19acbb403101b32bb538d3a6d8211f20b89be`) is the **PDF's** abstract and is
not used in the form field.

### §2.2 Subject area — **RESOLVED to the first level; the second level is NOT VERIFIED**

**VERIFIED 2026-10-17, fetched from <https://www.preprints.org/subject>.** Preprints.org's own categories
page offers **eleven** subject areas, verbatim:

> "Arts and Humanities · Biology and Life Sciences · Business, Economics and Management · Chemistry and
> Materials Science · Computer Science and Mathematics · Engineering · Environmental and Earth Sciences ·
> Medicine and Pharmacology · Physical Sciences · Public Health and Healthcare · Social Sciences"

**This paper's subject area: `Computer Science and Mathematics`** (browse slug
`computer-science-and-mathematics`). The paper evaluates small language models on a multi-step decision
task — NLP text classification — and its own classification is **`cs.CL` (Computation and Language),
cross-list `cs.LG`** (`papers/encoder-crossover-190/submission/METADATA.md:24-25,31-37`).

**Second level: NOT VERIFIED.** Preprints.org renders a second level under each field — a live listing on
<https://www.preprints.org/subject/browse/all> showed "Computer Science and Mathematics / Information
Systems" — but the **full enumerated second-level list could not be fetched from a primary source**: the
2023 announcement of the taxonomy
(<https://www.preprints.org/news/post/adjustment-of-subject-areas>) presents it **only as a screenshot
image**, and direct requests to the site's subject endpoints and `/sitemap.xml` return **HTTP 403 Access
Denied**. The author picks the exact second-level entry from the live dropdown under **Computer Science
and Mathematics**; this sheet does not invent one. The earlier candidate mapping "Computer Science and
Mathematics → Natural Language and Speech Processing" is **SUPERSEDED (2026-10-17)** — it was never
verified against any list.

### §2.3 Licence, DOI field and article type

- **Licence: `CC BY 4.0`** — fixed by Preprints.org and matching the author's own decision for the
  paper (`strategy/SUBMISSION_READINESS.md:87` "licence is fixed CC BY 4.0 (R29)";
  `papers/encoder-crossover-190/submission/METADATA.md:25`). **Not** the PolyForm licence: that
  governs the released data package, a different artifact, in a different record.
- **DOI field: leave empty.** Preprints.org mints the preprint's own DOI at posting; its about page
  states, verbatim: "**Each preprint will be registered with a unique digital object identifier issued by
  Crossref.** This makes them instantly citable and provides a permanent link to the preprint, even if the
  URL on our platform changes. **New versions of preprints receive a different DOI.**"
  (<https://www.preprints.org/about>). **VERIFIED shape (observed on live Preprints.org listings,
  2026-10-17): `10.20944/preprints<YYMM>.<NNNN>.v<N>`** — e.g.
  <https://doi.org/10.20944/preprints202610.1647.v1>, fetched from
  <https://www.preprints.org/subject/browse/all>. Copy whatever the site shows. Do not paste the Zenodo DOI
  here: it identifies the data record, not the preprint.
- **Accepted file formats (VERIFIED).** Verbatim from
  <https://www.preprints.org/instructions-for-authors>: "**Files should be submitted in Microsoft Word or
  LaTeX format.** For LaTeX files, ensure that all files necessary, including the .bib file, if applicable,
  to recreate the PDF are included in a zip or similar archive." **A PDF alone is not a listed accepted
  source format** — submit the self-contained `main.tex` (bibliography inlined) zipped with any remaining
  files. Publisher/journal logos and names must be removed. Supplementary material may be in any format,
  and the first page must carry "the title, author list, abstract, keywords, corresponding author contact
  details, and affiliations for all authors".
- **Licence options (VERIFIED — there is no licence choice).** Verbatim from
  <https://www.preprints.org/about>: "**All preprints are posted with a Creative Commons CC BY 4.0
  license**, ensuring that authors retain copyright and receive credit for their work while allowing anyone
  to read and use their work." That is exactly the author's decision, so **`CC BY 4.0` needs no action**.
- **Screening and turnaround: NOT VERIFIED.** The about page says only that "our team of editors will help
  with the process and **post your preprint as soon as possible**" (<https://www.preprints.org/about>), and
  the instructions page gives a "Quick Submission Checklist" but no committed turnaround. No primary-source
  page stating a number of days was fetched by this unit; the "screening in **days**" claim in
  `strategy/PUBLICATION_STRATEGY.md:73` is a workspace assertion, not a fetched one. Do not repeat a
  turnaround figure as sourced.
- **Article type: `Preprint article`.** Per `strategy/SUBMISSION_READINESS.md:87` and
  `strategy/FORMATTING_REQUIREMENTS.md:635` (R31): if a DOI for the paper already exists the
  *Conference Paper* type is unavailable, so submit as a preprint article.
- **First page must carry** title, author list, abstract, **keywords**, corresponding-author contact
  and affiliations (`strategy/FORMATTING_REQUIREMENTS.md:634`, R30 — currently **FAIL**, and the
  author's contact and the affiliation decision are **author-only**).
- **Payload:** a self-contained `main.tex` (bibliography is inlined) or the PDF. The PDF above exists
  (25 pages, verified by `pdfinfo`); the LaTeX is
  `papers/encoder-crossover-190/submission/main.tex` — 84,695 B, sha256
  `397713d74920e9e1bc5f5fb8dc6ef09fb5fa9e641583f0ecd16b718d5f9d09ca`.
- **Superseded measurements (2026-10-17, UDEPOSITDOC2; retained as history).** `main.tex` was 84,223 B,
  sha256 `8374fd28b1fc6c9faa3cb91884e30e097dbb1828361c418c431fdeec8e8461a1`; the rendered PDF was
  184,933 B, sha256 `58c22c906d0220fb707eed538bf13bf33304a4b2751b033e0d4a0c71bce7fd44` (still 25 pages).
  Re-measured on disk by **UFIXDEP1** on 2026-10-18; disk no longer matches those figures.

---

## §3 AUTHOR DECISION 1 — the creator name split (do not let an agent choose this)

Zenodo's creator field splits into *Given names* / *Family name*, and a wrong split is **visible on the
published record**. Three readings of one real name:

| option | Given names | Family name | Renders as | Sort key / short form |
|---|---|---|---|---|
| **R1 (recommended)** | `Aswin Ram` | `Kalugasala Moorthy` | Aswin Ram Kalugasala Moorthy | Kalugasala Moorthy, A. R. |
| R2 | `Aswin Ram Kalugasala` | `Moorthy` | Aswin Ram Kalugasala Moorthy | Moorthy, A. R. K. |
| R3 | `Aswin Ram Moorthy` | `Kalugasala` | Aswin Ram Moorthy Kalugasala (order changes) | Kalugasala, A. R. M. |

Evidence, and its limit: the payload's `Required Notice:` line abbreviates the name to
**`Aswin-Ram-K`** (`strategy/ZENODO_DEPOSIT.md:52`), i.e. *given* + *given* + an *initial in K*. That
is consistent with **R1** (`K` = Kalugasala, the first element of a two-word surname) and inconsistent
with **R2** (`K` would not be the sort initial). The abbreviation is the **only internal evidence**;
this unit did not choose. **The author confirms the split.** Preprints.org appears to take a single
name field (`METADATA.md:15`), where the literal is simply `Aswin Ram Kalugasala Moorthy`.

**No affiliation and no ORCID is placed in any field by this unit** — neither was supplied, and the
author's standing decision is name only.

---

## §4 AUTHOR DECISION 2 — which file, and the version

| | recommend | alternative | effect |
|---|---|---|---|
| Upload file | **A**, the tarball (§0) | B, the 29-file zip | B puts 29 files at the extraction root and drops `CITATION.cff` + `README_DEPOSIT.md`. |
| Version | **empty** | `v1` | `v1` is sourced only from B's filename and from `ZENODO_UPLOAD.txt:113`; the author never named a version and `CITATION.cff` has no `version`. |

---

## §5 Divergences between the sources — **RESOLVED 2026-10-17 (UDEPOSITDOC2)**

These are places where two files on disk say different things. Choosing between them is an **author**
call; this sheet reports both.

**Resolved — one value each, with the reason. The numbered items below are retained verbatim as the
historical record and are each superseded 2026-10-17 by the row that matches them.**

| # | divergence | CHOSEN VALUE | reason |
|---|---|---|---|
| 1 | which file is the deposit | the **tarball**, `papers/encoder-crossover-190/released/encoder-crossover-190-released.tar.gz` (159,014 B, `478941c0…`; superseded 158,956 B / `bcdbf75e…`, 2026-10-18 UFIXDEP4, rebuilt the same day by UREADMEFIX1; 158,762 B / `956d6363…`, 2026-10-18 UFIXDEP1; 157,650 B / `7389bd87…`, 2026-10-17 UDEPOSIT2) | it has one top-level directory, so extraction cannot explode into the author's working directory (exactly why the earlier root-level zip was disqualified), and it is a **superset** — it adds `CITATION.cff` and `README_DEPOSIT.md` |
| 2 | upload type | **`Dataset`** | the record's primary value is released data; the shipped scripts verify **from stored records** and the harness is withheld, so the record is not a software release. Zenodo permits **one** type per record (§1.2) |
| 3 | version | **empty** | no version was assigned by the author and `CITATION.cff` declares none; `v1` traced only to the superseded zip's filename |
| 4 | keywords | **the 8 content-descriptive keywords** in §1 | they describe the research content, which is what the keyword field is for; the competing list mixes internal project vocabulary (`EXP12`) and licence/administrative terms the licence field already carries |
| 5 | description | **the purpose-written description** in §1.1 | it states the deposit's scope, its withheld harness and its licence; the abstract describes the paper's experiment, not the deposit, and is already the Preprints.org abstract field |
| 6 | stale digests | **159,014 B / `478941c0…`** (§0) | re-measured on disk by UDEPOSITDOC1 and UDEPOSITDOC2 (then 157,650 B / `7389bd87…`), by UFIXDEP1 on 2026-10-18 (then 158,762 B / `956d6363…`), and rebuilt and re-measured by UFIXDEP4 on 2026-10-18 after the `CONTRIBUTING.md` draft-banner fix; the archive was rebuilt again by UREADMEFIX1 on 2026-10-18 to fix dead paths in the front page, and re-measured by UDOCREFRESH1 |

The six numbered items below are **retained verbatim as the historical record**; each is **superseded
2026-10-17** by the corresponding row above.

1. **Which file is the deposit.** `scratch/urelease9/zenodo/ZENODO_UPLOAD.txt:9-13` calls the **zip**
   the archive to upload and the tarball a "companion paper-side archive — NOT the deposit file".
   `strategy/ZENODO_DEPOSIT.md:1,13-17` and `strategy/DEPOSIT_ARCHIVE.md:8` name the **tarball** the
   shippable archive. The recommendation here (§0) is the tarball; justification given there.
2. **Upload type.** `Software` (`ZENODO_UPLOAD.txt:48`) vs `Dataset` primary
   (`ZENODO_DEPOSIT.md:34`). See §1.2.
3. **Version.** `v1` (`ZENODO_UPLOAD.txt:113`) vs leave blank (`ZENODO_DEPOSIT.md:45,129`). See §4.
4. **Keywords.** 8 semantic keywords (`ZENODO_UPLOAD.txt:125-137`) vs 6 different ones
   (`ZENODO_DEPOSIT.md:42`). §1's list is the **deduplicated union** — every entry is sourced from one
   of the two, none is invented.
5. **Description.** The abstract, 1,195 chars (`ZENODO_UPLOAD.txt:118-122`) vs the purpose-written
   description (`ZENODO_DEPOSIT.md:61-79`). §1.1 uses the purpose-written one, which states the
   deposit's scope, its withheld harness and its licence; the abstract does not name the licence or
   the deposit's contents.
6. **Stale digests in the sources.** `ZENODO_DEPOSIT.md:15,247` and `ZENODO_UPLOAD.txt:19-20` cite the
   superseded `157,272` / `a0a210fc…` and `157,305` / `778818b2…` archive. The live values are in §0.

---

## §6 What this unit could NOT determine

1. **Preprints.org's second-level subject taxonomy** — the eleven **first-level** areas are now VERIFIED
   (§2.2) and this paper's is `Computer Science and Mathematics`, but the full second-level list could not
   be fetched (the announcement is an image; the subject endpoints and `/sitemap.xml` return HTTP 403). The
   author picks the second-level entry from the live dropdown.
2. **An additional / second Zenodo resource type** — RESOLVED as **unavailable**: one type per record, or
   split into two records (§1.2, quoted from Zenodo's own help page).
3. **The exact minted DOI formats** — RESOLVED by observation: Zenodo `10.5281/zenodo.<id>` (§1.3) and
   Preprints.org `10.20944/preprints<YYMM>.<NNNN>.v<N>` (§2.3). Still copy what the site shows.
- **Preprints.org's screening turnaround** — NOT VERIFIED from a primary source (§2.3).
4. **The name split** — §3, author decision.
5. **The paper's DOI** — does not exist. The Zenodo "related identifier → paper" therefore stays empty
   at first publication (§1.3).
6. **Corresponding-author contact and any affiliation** — author-only, never supplied.
7. **`papers/encoder-crossover-190/released/` holds only the tarball** plus the marker
   `SUPERSEDED-UNPACKED-TREE.md` (2,404 B); the unpacked tree was moved away by UDEPOSIT2
   (`strategy/DEPOSIT_ARCHIVE.md:55-62`). No second upload candidate lives there.
8. **No network call was made by this unit** — the two licence-vocabulary checks in
   `strategy/ZENODO_DEPOSIT.md` §4 are that unit's evidence, cited here, not re-fetched.

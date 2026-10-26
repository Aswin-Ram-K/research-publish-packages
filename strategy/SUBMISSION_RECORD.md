# SUBMISSION_RECORD — dated, digest-backed provenance of every public artefact

**Record compiled:** 2026-10-19 (America/Chicago), unit URECORD1.
**Scope:** three papers × three venues = nine rows, the versions of each Zenodo deposit, how the three rows
of one paper relate, the disclosure history that precedes all of it, and what a reader can and cannot check.

**Verification method, stated so it can be audited.** Every digest and size in §1 was measured on disk with
`sha256sum` / `md5sum` / `stat`; nothing is copied from a task card. Every Zenodo field in §1–§2 was read live
from `https://zenodo.org/api/records/<concept>/versions/latest` (HTTP 200 after redirect) and
`https://zenodo.org/api/records/<version>/versions` on 2026-10-19. Raw responses are in
`scratch/urecord1/latest-*.json` and `scratch/urecord1/versions-*.json`.

**Identifiers supplied by the author and confirmed by him directly** (not re-derivable from this workspace):
Preprints.org manuscript numbers `239326` / `239328` / `239329`; TMLR forum ids `L9GcDGb2fr` / `U2WjJMH0EK` /
`q72ZB9ZMqy`. An earlier message gave the encoder manuscript as `23932`; the author corrected it to `239326`,
and only `239326` is recorded here.

> **Standing rule — restated at the top because everything below depends on it.**
> **No filing, declaration or exhibit may ever assert that this work was never published.** It was published,
> in part, before any of the artefacts recorded here existed. See §4.

---

## 1. The nine rows — one per paper per venue

Paper slugs are used as stable keys: **E** = `encoder-crossover-190`, **R** = `replay-record-not-decision`,
**G** = `gated-read-batching`.

| # | paper | venue | date submitted / published | exact filename | size (bytes) | sha256 | identifier |
|---|---|---|---|---|---|---|---|
| 1 | E | Preprints.org | `accepted by the editor 2026-10-20 (author-reported); not yet posted — no public posting observed 2026-10-20; DOI not minted` — venue-side timestamp not recorded in this workspace; upload artefact built 2026-10-19 01:39 −0500 | `papers/encoder-crossover-190/preprints/encoder-crossover-190-preprints.zip` | 28,712 | `705bc498c7c7eb7cf1e53cae8f49fb8656787694c39dbc7c5f4064f9aa7caf7f` | manuscript **239326**; **DOI not yet minted — `pending`** |
| 2 | E | TMLR | `pending` — forum id issued; submission timestamp not verifiable here (OpenReview API returned HTTP 403) | `papers/encoder-crossover-190/tmlr/main.pdf` | 177,298 | `fb95f0ac302a07678eaf5f73ef7038a5d46beeb6807830f065a94ffb38cf1109` | forum **L9GcDGb2fr** |
| 3 | E | Zenodo | published **2026-10-19** (API `publication_date`; record created 2026-10-19T18:59:12Z) | `papers/encoder-crossover-190/released/encoder-crossover-190-released.tar.gz` | 159,182 | `dbbf7b1a7e8a7884a89b17bf9fecce7e364a0afdbefe4b7c74524bc13a9b1877` (md5 `b4dac172003233d7d6c8c78c909b5594`) | concept DOI **10.5281/zenodo.23463944**; current version record **23482311** = DOI **10.5281/zenodo.23482311** |
| 4 | R | Preprints.org | `not accepted as of 2026-10-20 (author-reported); state otherwise unknown; no public posting observed 2026-10-20; DOI not minted` — upload artefact built 2026-10-19 14:27 −0500 | `papers/replay-record-not-decision/preprints/replay-record-not-decision-preprints.zip` | 11,526 | `1b520f22ad7ec0d83e0c82a734fd5790724a2dfbb175a2600ac323294953537d` | manuscript **239328**; **DOI not yet minted — `pending`** |
| 5 | R | TMLR | `pending` — forum id issued; submission timestamp not verifiable here | `papers/replay-record-not-decision/tmlr/main.pdf` | 93,109 | `cefd09a7a161d73bf7ae27303ca8cb00dbab2761485beca30bb90856846aee7a` | forum **U2WjJMH0EK** |
| 6 | R | Zenodo | published **2026-10-19** (record created 2026-10-19T19:58:36Z) | `papers/replay-record-not-decision/released/replay-record-not-decision-released.tar.gz` | 107,764 | `e6f920c432e0dc180ca72336e0bb60b2155462b8365f8800359a24beec3bbe63` (md5 `41afa2831ff2f43af91d9c4416d8f658`) | concept DOI **10.5281/zenodo.23482511**; current version record **23483304** = DOI **10.5281/zenodo.23483304** |
| 7 | G | Preprints.org | `accepted by the editor 2026-10-20 (author-reported); not yet posted — no public posting observed 2026-10-20; DOI not minted` — upload artefact built 2026-10-19 18:10 −0500 | `papers/gated-read-batching/preprints/gated-read-batching-preprints.zip` | 15,296 | `7efe3af1d358552b2e4231a63cb02820d25bd678aa1761f06ba5880bdfe783a0` | manuscript **239329**; **DOI not yet minted — `pending`** |
| 8 | G | TMLR | `pending` — forum id issued; submission timestamp not verifiable here | `papers/gated-read-batching/tmlr/main.pdf` | 107,504 | `25a9394e4f649335dd61209dc0075ece5091d0363f675042078a440db79bfeba` | forum **q72ZB9ZMqy** |
| 9 | G | Zenodo | published **2026-10-19** (record created 2026-10-19T23:03:45Z) | `papers/gated-read-batching/released/gated-read-batching-released.tar.gz` | 128,902 | `e2ceb554f319cb898221c655f1b64ba0e8a022e4e0ad9ffc3fda5fbecd464b24` (md5 `a7e81bf7c8ebe49da83e869a002be1b2`) | concept DOI **10.5281/zenodo.23483314**; current version record **23485733** = DOI **10.5281/zenodo.23485733** |

**Dated status note (2026-10-20).** Rows 1 (E, `239326`) and 7 (G, `239329`) are **accepted by the editor**, as
reported by the author on 2026-10-20; **neither acceptance was independently verifiable from this host** — the venue
returns HTTP 403 for every `https://www.preprints.org/manuscript/<number>` request (literal status, all three
manuscripts `239326` / `239328` / `239329`: **403 / 403 / 403**), so the accepted state stated here rests on the
author's report alone. Crossref (`api.crossref.org/prefixes/10.20944/works`, `rows=20`, queried by title) returned
**zero** exact-title matches for **all three** titles on 2026-10-20 — and Crossref lags posting by 1–2 days, so that
absence is **not** proof that nothing posted. Row 4 (R, `239328`) is **not accepted** as of 2026-10-20 and its
state is otherwise unknown. No row is asserted as *posted*, and no DOI is asserted for any row.

**Notes on the remaining `pending` cells.** They are `pending`, not zero and not guessed.
- *Preprints.org DOIs are not yet minted.* No DOI is asserted for rows 1, 4, 7 — **including the two accepted
  manuscripts**: acceptance is not publication, and no DOI has been resolved for either. The manuscript numbers
  are the identifier the venue has issued so far.
- *Venue-side submission timestamps for Preprints.org and TMLR are not recorded in this workspace*; the date
  given for those rows is the date the upload artefact was built (from file mtime and the zip's internal
  timestamp), which is a lower bound on submission, not proof of it. Only the three Zenodo dates were
  verified against a live authoritative API.
- Zenodo `md5` is the value the API reports for the deposited file; it matches the local file's `md5sum`
  exactly for all three, which is the proof that the local archive and the deposited archive are the same bytes.
  The `sha256` in the same cell is measured locally.

**All six non-Zenodo rows share one property worth stating:** each Preprints.org upload is a zip containing a
single file, `main.tex` (84,967 / 32,766 / 42,531 bytes uncompressed), and each TMLR upload is a compiled
`main.pdf`. The venue, not this workspace, produces the Preprints.org PDF from that `main.tex`. Identified
(non-anonymous) renders on disk are `papers/<slug>/rendered/<slug>.pdf` (E 189,042 B, R 101,593 B, G 117,784 B);
they are context, not a tenth row, and no claim is made that they are byte-identical to whatever the venue serves.

---

## 2. Versions per deposit (live API, 2026-10-19)

Zenodo does not populate `metadata.version` on these records, so version numbers are not printed by the API.
What is printed is the versions listing (newest first) and the `/versions/latest` redirect. Both are recorded;
ordinals below are the position in that listing, with **current** proven by the redirect target, not assumed
from size.

### 2.1 E — concept `10.5281/zenodo.23463944` — **3 versions**, current = 3rd

| ordinal | record id | DOI | file | size (bytes) | md5 |
|---|---|---|---|---|---|
| 1 (oldest) | 23463945 | 10.5281/zenodo.23463945 | `encoder-crossover-190-released.tar.gz` | 159,014 | `4066c3428c1e4836d200909c6a2db6b0` |
| 2 | 23464507 | 10.5281/zenodo.23464507 | `encoder-crossover-190-released.tar.gz` | 159,185 | `b3b30f66d231924e02706de0eb3fbc15` |
| **3 (current)** | **23482311** | 10.5281/zenodo.23482311 | `encoder-crossover-190-released.tar.gz` | **159,182** | **`b4dac172003233d7d6c8c78c909b5594`** |

The encoder is the only deposit with three versions, and the smallest of the three is *not* the current one:
v2 (159,185 B) is larger than the current v3 (159,182 B). Do not infer currency from size. Currency is proven
by `GET /api/records/23463944/versions/latest` returning **HTTP 200 at `/api/records/23482311`**.

### 2.2 R — concept `10.5281/zenodo.23482511` — **2 versions**, current = 2nd

| ordinal | record id | DOI | file | size (bytes) | md5 |
|---|---|---|---|---|---|
| 1 (oldest) | 23482512 | 10.5281/zenodo.23482512 | `replay-record-not-decision-released.tar.gz` | 107,641 | `a279e399382792952205b0738f958e38` |
| **2 (current)** | **23483304** | 10.5281/zenodo.23483304 | `replay-record-not-decision-released.tar.gz` | **107,764** | **`41afa2831ff2f43af91d9c4416d8f658`** |

### 2.3 G — concept `10.5281/zenodo.23483314` — **2 versions**, current = 2nd

| ordinal | record id | DOI | file | size (bytes) | md5 |
|---|---|---|---|---|---|
| 1 (oldest) | 23483315 | 10.5281/zenodo.23483315 | `gated-read-batching-released.tar.gz` | 128,559 | `5c0db7c9afedf5d47747c70e03e8a136` |
| **2 (current)** | **23485733** | 10.5281/zenodo.23485733 | `gated-read-batching-released.tar.gz` | **128,902** | **`a7e81bf7c8ebe49da83e869a002be1b2`** |

### 2.4 Deposit metadata common to all three (live, per concept)

| field | value |
|---|---|
| `metadata.language` | `eng` |
| `metadata.resource_type.type` | `dataset` |
| `metadata.license.id` | `polyform-noncommercial-1.0.0` |
| `metadata.publication_date` | `2026-10-19` (all three) |
| file count per record | 1 (the `--released.tar.gz`) |
| `recid` / `conceptrecid` | match the table above; concept DOI = `conceptdoi` |

---

## 3. Linkage — what the three rows of one paper have in common, and how they differ

Common to all three rows of a paper: the paper identity — title, the measurement, the claimed result — and the
author. That is where the identity ends; the three files are three different objects with three different
digests, and conflating them is the error this section exists to prevent.

| | Preprints.org row | TMLR row | Zenodo row |
|---|---|---|---|
| what the file is | zip containing one `main.tex`: the **identified** manuscript source | compiled PDF of the **anonymised** variant | `tar.gz` of data + verification tooling |
| author identity | identified (normal submission) | **anonymised** — `\author{Anonymous authors}` at `main.tex:18` in all three TMLR trees | no author block; deposit metadata carries creators |
| paper text inside the file | yes (`main.tex`) | yes (PDF) | **no** — 0 `.tex`/`.pdf`/`.bib` entries in all three archives |
| digest | per §1 rows 1/4/7 | per §1 rows 2/5/8 — **different file, different digest** from the Preprints row | per §1 rows 3/6/9 |
| identifier | manuscript number (DOI pending) | forum id | concept DOI + version record DOI |

**The TMLR version is the anonymised variant of the same paper — a different file with a different digest.**
This is checked, not assumed: `papers/encoder-crossover-190/tmlr/main.tex:18`, `papers/replay-record-not-decision/tmlr/main.tex:18`
and `papers/gated-read-batching/tmlr/main.tex:18` each read `\author{Anonymous authors}`. The TMLR PDFs are
therefore not interchangeable with the Preprints.org render of the same `main.tex`, and a digest comparison
between the two venues' rows is expected to fail and is not evidence of tampering.

**The Zenodo deposit contains no paper text — data and verification tooling only.** Measured, not quoted:
`tar -tzf` lists 37 (E), 13 (R) and 16 (G) entries; a filter for `*.tex`, `*.pdf`, `*.bib` returns **0** for
each. What is in them: `CITATION.cff`, `COMMERCIAL.md`, `CONTRIBUTING.md`, `LICENSE`, `MANIFEST.json`,
`README.md`, `README_DEPOSIT.md`, plus per-paper `fixture/` + `results/` (E), `data/` + `verify/recompute-claims.py`
(R, G), and G's `results/GATED_READ_2026.md` / `GATED_READ_PROVENANCE.md`. The deposit is the measurement's
**inputs and its checking scripts**, not the manuscript.

---

## 4. Disclosure history — mandatory, and not to be softened

Before any artefact in §1 existed, part of this work was already public. Recorded here with dates and paths so
that no later document can be written as if the opposite were true. Wording is taken from the authoritative
registers, cited by section and line.

### 4.1 A public MIT-licensed repository carried the derivation document, byte-identical

| field | value |
|---|---|
| repository | `github.com/Aswin-Ram-K/publish-present-compete` — **public**, **MIT**, 38 commits, last commit **2026-10-10** (`strategy/WITHHELD.md` §8.1, `:261–263`) |
| the file | `findings/PAPER-DERIVATION.md` — **byte-identical** to `/home/zer0null/Duval/docs/research/PAPER_DERIVATION.md` (`strategy/WITHHELD.md:263`) |
| measured size / digest | **46,636 B**, sha256 `d98c4359d37b987db07707e0b96358de0cd280c979896c6a15858d96bcd14802` (`strategy/GATED_READ_DISCLOSURE.md:170`) |
| what it discloses | M1–M10, M12, M13 — the mechanism descriptions, dated ≤ 2026-10-10 (`strategy/WITHHELD.md` §8.1 table `:283–295`) |
| licence consequence | the MIT grant is irrevocable for copies already distributed; withdrawing the repository reduces *future* dissemination and cannot recall or re-license what is out (`strategy/WITHHELD.md:307–312`) |

### 4.2 An AGPL-3.0 window exposed `consonance/src/**` for ~27.5 hours

| field | value |
|---|---|
| boundary | `ccdab112` (2026-10-09 04:11) → `b81b35e` (2026-10-10 07:51); event-measured **2026-10-09T04:20:17Z → 2026-10-10T07:52:54Z** (~27.5 h) (`strategy/GATED_READ_DISCLOSURE.md:175`) |
| what was reachable | 481 entries, **428 under `consonance/`**, **35 blobs under `consonance/src/` totalling 708,575 B** (`strategy/WITHHELD.md:450`) |
| the later finding | **the named ref carried no `consonance/` directory.** `ccdab112`'s tree is `.gitignore CLAIMS.tsv README.md SOURCES.tsv` — no `consonance/` at all. The code sat on the **unreferenced older head `89003e7069c9ad79c40d91982720751b1ddf0360`**, where `consonance/src/journal.ts` returned **HTTP 200 / 46,450 B** (also `dag.ts` 200/44,468 B, `store.ts` 200/3,316 B) (`strategy/WITHHELD.md:450`) |
| mapping to the private tree | `consonance/` → target `src/**`, corroborated by three exact byte-size matches: `src/journal.ts` 46,450 B, `src/dag.ts` 44,468 B, `src/store.ts` 3,316 B (`strategy/GATED_READ_DISCLOSURE.md:27`, `:33`) |
| authority | `strategy/AD6_ARCHIVE_WINDOW_RESOLUTION.md` |

The earlier, unqualified statement — *"`consonance/src/journal.ts` and `src/journal.ts` return 404 at every
historical ref while a control README returns 200"* (`strategy/WITHHELD.md:444–445`) — held only for
branch/tag-reachable refs and path-absent refs. It was never universal, and it is **not** the wording to reuse.
`strategy/GATED_READ_DISCLOSURE.md:175` records the conflict as **resolved (2026-10-16, unit UFIXAD6)**.

### 4.3 What follows from 4.1–4.2 — the protective claim, narrowed

- The **design** is published: dated ≤ 2026-10-10, authored, citable, MIT (`strategy/WITHHELD.md` §8.4, `:350–357`).
- What remains withholdable is the **implementation** — `src/**`, the code-level state catalogue, private
  corpora, `tools/**`, weights, unpublished prose (`strategy/WITHHELD.md` §8.3, `:329–346`).
- Therefore: `strategy/WITHHELD.md:313–316` — *withholding these mechanisms inside this workspace protects
  nothing* — and `strategy/GATED_READ_DISCLOSURE.md:33`, item 10 of the withhold list, which forbids
  *"any assertion or filing line that the work was never published."*

> ### Standing rule
> **No filing, declaration or exhibit may ever assert that this work was never published.** The design is
> published (≤ 2026-10-10, MIT); the AGPL window published the window's version of `consonance/src/**`. Only
> the implementation is protectable, and only while it stays out of the public record. This section is the
> reason the rule exists — the false assertion would be disprovable from a single fetch of a public repository.

---

## 5. How to use this record

**What a reviewer, journal or adjudicator can check, from this document alone:**
1. **The identifiers resolve.** Fetch `https://zenodo.org/api/records/10.5281/zenodo.23463944/versions/latest`
   (and the other two concepts); it must redirect to record `23482311` / `23483304` / `23485733` and report the
   file size and md5 in §1. A discrepancy is a real discrepancy — the record is falsifiable by one request.
2. **The bytes are pinned.** Download each deposited file and compute `sha256`; it must equal the value in §1.
   The deposit's own md5 and the local md5 are already shown to agree for all three.
3. **The lineage is bounded.** §2 gives every version, including the superseded ones, so a reader can tell
   which record a citation written months ago actually pointed at — and can confirm that the encoder's current
   version is the 3rd of 3, not the 1st.
4. **The prior public exposure is dated.** §4 gives repository, file, digest, licence and the AGPL window's
   boundary commits and the unreferenced head the code actually sat on — dates, not adjectives.
5. **The three rows are not the same object.** §3 states which file is identified, which is anonymised, and
   which carries no paper text, so a digest mismatch across venues is read correctly.

**The one thing they cannot do:** **the deposit does not reproduce the measurement.** It ships the fixture /
rows / result JSON and `verify/recompute-claims.py`, but no paper text, no trained weights, and no harness —
the archive contains 0 `.tex`/`.pdf`/`.bib` files (§3). A third party can re-check the claims *against the
numbers the deposit contains*; they cannot re-run the experiment, re-score a baseline, or regenerate a result
from it. Any reviewer expectation of end-to-end reproduction should be corrected before it becomes a review
finding.

**What this record deliberately does not do:** it does not assert a Preprints.org DOI (§1), does not assert a
TMLR submission date it could not verify, and does not upgrade the AGPL window into a story about intent. The
gaps are `pending`; nothing is filled in with a plausible value.

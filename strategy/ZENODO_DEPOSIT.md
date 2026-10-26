# Zenodo deposit — `encoder-crossover-190` released data and verification tooling

Unit **UZENODO2**. Author: **Aswin Ram Kalugasala Moorthy**. Everything below is the literal value to
paste into the Zenodo upload form, plus the evidence for the one field that had to be checked against
Zenodo's own documentation rather than memory.

> **UDEPOSITDOC2, 2026-10-17 — HISTORICAL, SUPERSEDED IN PART.** This file was the plan of unit UZENODO2.
> `strategy/DEPOSIT_METADATA.md` is now the **single authoritative source for every deposit form field
> value**; this file is retained as the record. Superseded here, each annotated in place below: §1's
> digests (→ **157,650 B / `7389bd87…`**), §2's "Optional second type `Software`" (**factually wrong** —
> Zenodo allows ONE type per record) and its keyword list (→ the 8-item list in DEPOSIT_METADATA §1), and
> §5's "unverified" DOI shape (→ verified `10.5281/zenodo.<id>`). **§3's description is NOT superseded** —
> it is carried verbatim into `DEPOSIT_METADATA.md` §1.1.

---

## 1. The upload file

| | |
|---|---|
| Upload file | `papers/encoder-crossover-190/released/encoder-crossover-190-released.tar.gz` |
| Bytes | ~~157,272~~ **SUPERSEDED 2026-10-17 (UDEPOSITDOC2): the value current on that date was 157,650 — itself since superseded (see the appended section)** |
| sha256 | ~~`a0a210fcdde1eab14e2e2d8d9c90b2ee897b4968ac7028c28c4c7d0187a5e088`~~ **SUPERSEDED 2026-10-17: the value current on that date was `7389bd879e970d840a528a9a19bfb9a6623babf3ec10746b18fc616bf2b4dad3` — itself since superseded (see the appended section)** |
| Members | 37 total = 31 files + 6 directories |
| Top-level members | exactly **one**: `encoder-crossover-190-released/` |

Built with `tar --sort=name --mtime='@0' --owner=0 --group=0 --numeric-owner --format=gnu` piped
through `gzip -9n`. Built twice; the two builds are **byte-identical** (`cmp` clean), so the digest is
reproducible. Extraction cannot explode into the working directory: every member is under the single
top-level directory.

Payload = the 29-file promoted package `scratch/uneutral10/package` (842,810 B), every file sha256-
verified unchanged against its source, **plus two added files** (`CITATION.cff`, `README_DEPOSIT.md`).
Extracted tree: 31 files, **851,043 B**.

---

## 2. Form fields, field by field

| Zenodo field | Value to paste |
|---|---|
| **Resource type** | `Dataset` (primary). Optional second type `Software` — this deposit is data **and** verification tooling. Do not select `Publication`/`Journal article`; the paper is a separate work. **SUPERSEDED 2026-10-17 (UDEPOSITDOC2): "optional second type" is factually wrong — Zenodo allows exactly ONE resource type per record, so choose `Dataset`; see `strategy/DEPOSIT_METADATA.md` §1.2.** |
| **Title** | `encoder-crossover-190 — released data and verification tooling` |
| **Creators → Family name** | `Kalugasala Moorthy` |
| **Creators → Given names** | `Aswin Ram` |
| **Creators → Name** (as displayed) | `Aswin Ram Kalugasala Moorthy` |
| **Creators → Affiliation / ORCID** | **leave blank.** Neither was supplied; inventing one is forbidden. |
| **Description** | see §3 below — paste verbatim |
| **Licence** | `PolyForm Noncommercial License 1.0.0` — Zenodo vocabulary id **`polyform-noncommercial-1.0.0`** (verified present; see §4) |
| **Keywords** | `encoder-crossover-190`; `EXP12`; `typed single-label decision`; `released data`; `verification tooling`; `PolyForm Noncommercial` |
| **Language** | `English` |
| **Related identifiers → the paper** | Relation **`is supplement to`**, identifier = **the paper's DOI — not yet assigned (filled in after the deposit exists, see §5)** |
| **Version** | **leave blank / fill in after deposit** — no version number has been assigned by the author (see §5) |
| **Publication date** | the deposit date Zenodo stamps; do not back-date |
| **DOI** | assigned by Zenodo on publication (see §5) |

### On the creator name split

The form splits into *Family name* / *Given names*. The paper's own `\author{}` line is
`Aswin Ram Kalugasala Moorthy` and the release's `Required Notice:` line abbreviates it to
`Aswin-Ram-K`. The split above (`given-names: Aswin Ram`, `family-names: Kalugasala Moorthy`) is the
one that renders back to the full real name; **the author should confirm it**, since the abbreviation
"K" is the only internal evidence and a wrong split is visible on the record.

---

## 3. Description — paste verbatim

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

**Do not** add any sentence promising that the deposit reproduces, re-runs, or regenerates the
measurement. It cannot — the harness is withheld — and the package's own `MANIFEST.json`
(`"harness_revision": "WITHHELD"`) and `LICENSE` `## Scope` section both say so.

---

## 4. Licence field — verified against Zenodo's own list, not memory

**Finding: PolyForm Noncommercial 1.0.0 IS available in Zenodo's licence list.** No substitution and no
author decision on the licence is required.

Evidence (read, not recalled):

- URL read: **<https://zenodo.org/api/vocabularies/licenses?q=PolyForm&size=25>** — HTTP 200. The
  response's first hit is
  `{"id": "polyform-noncommercial-1.0.0", "title": {"en": "PolyForm Noncommercial License 1.0.0"},
  "props": {"url": "https://polyformproject.org/licenses/noncommercial/1.0.0", "scheme": "spdx",
  "osi_approved": ""}, "type": "licenses"}`. Total hits: 2 (the other is PolyForm Small Business 1.0.0).
- Cross-checked at **<https://zenodo.org/api/vocabularies/licenses?q=Noncommercial&size=25>** — HTTP 200,
  total hits 1, the same `polyform-noncommercial-1.0.0` entry. These are the endpoints behind Zenodo's
  fixed licence picker on the deposit form.

**Exact identifier string to select: `polyform-noncommercial-1.0.0`** (displayed as *PolyForm
Noncommercial License 1.0.0*, scheme `spdx`, canonical URL
<https://polyformproject.org/licenses/noncommercial/1.0.0>).

This matches the author's decision exactly: the released package is PolyForm Noncommercial 1.0.0 with an
author-offered paid commercial licence (`LICENSE`, `COMMERCIAL.md`). Nothing is substituted. Note that
the **paper text** is CC BY 4.0 — a different licence, and not this record's licence; if the paper is
deposited as its own Zenodo record it takes `CC-BY-4.0` there. The main project repository stays
proprietary and closed.

Because the exact licence is present, the fallback options are **not** needed. For the record, had it
been absent the honest options would have been: pick the closest listed identifier and state the
divergence in the description; or use `Other` / a custom licence string and put the real terms in the
description and in `LICENSE`. Both would have been **author decisions**, not silent substitutions — this
unit would not have chosen either on the author's behalf.

---

## 5. Fields filled in AFTER the deposit exists

These cannot be pasted now because the deposit does not exist yet. **Do not invent values for them.**

| Field | Status |
|---|---|
| **Paper DOI** (related identifier, relation `is supplement to`) | **does not exist.** No DOI for the paper appears anywhere in the tree. Set it after the paper gets one. |
| **Zenodo DOI** for this record | assigned by Zenodo on publish. Afterwards add the **Concept DOI** to `CITATION.cff` (it survives versions) as `doi: "10.5281/zenodo.XXXXXXX"`. **DOI shape VERIFIED 2026-10-17 (UDEPOSITDOC2) as `10.5281/zenodo.<id>`; see `strategy/DEPOSIT_METADATA.md` §1.3.** |
| **Version** | no version number has been assigned by the author. Leave blank, or set it only if the author names one. `CITATION.cff` deliberately declares no `version`. |
| **`date-released`** in `CITATION.cff` | currently `2026-10-17`, the package build date recorded in `MANIFEST.json` (`"generated_utc": "2026-10-17T03:26:03Z"`). Change it on upload if the deposit date differs. |

---

## 6. What was built, and one collision the author must rule on

`papers/encoder-crossover-190/released/encoder-crossover-190-released/` — the 29 package files **byte-
identical** to `scratch/uneutral10/package` (all 29 sha256 verified), plus:

- `CITATION.cff` — **added.** CFF 1.2.0, `type: dataset`, the real author name, the paper title per the
  brief, the year 2026 via `date-released: "2026-10-17"`, `license: PolyForm-Noncommercial-1.0.0`, and
  **no** `doi` field (only a comment saying Zenodo assigns it), **no** version, **no** affiliation,
  **no** ORCID.
- `README_DEPOSIT.md` — **added.** States what this is and is not, that the harness is withheld, that the
  checks re-derive from stored records and do not retrain or re-render, the three exact commands with
  their expected output, and the licence by name.

**Collision — reported, not silently resolved by overwriting.** The package **already carries**
`README.md`, `LICENSE`, `COMMERCIAL.md` and `CONTRIBUTING.md`. The brief asks for a `README.md` and a
`LICENSE` at the deposit root, but the standing rules also say *do not modify the package's contents*
and *hold the 29 package files unchanged* (sha256-verified). Overwriting either file would break the
hash guarantee, so this unit did not:

- `COMMERCIAL.md` and `CONTRIBUTING.md` — already present and **already byte-identical to
  `strategy/licence-templates/RELEASED-PIECE/`** (`ca86a625…`, `dd8b8ee4…`). Nothing added, per the
  brief's own "if the package does not already carry them".
- `LICENSE` — the package's own copy carries the **same licence body plus more**. See §7.
- `README.md` — kept unchanged; the required plain statement, expected outputs and licence naming live in
  the added `README_DEPOSIT.md` instead. **Author decision if he wants the package README replaced by
  it** — that is a content edit to the package and this unit did not perform it.

---

## 7. `LICENSE` — the digests and the line ranges (the body is unchanged)

The package's `LICENSE` and the template are **not** byte-identical as whole files, because the package
**appends a 12-line scope section**. The **licence body is byte-identical** in both.

| file | bytes | lines | sha256 |
|---|---|---|---|
| `strategy/licence-templates/RELEASED-PIECE/LICENSE` | 5,851 | 151 | `3d364676a91dc579954b585e9d3a3c9f0dc03b723715805cc9431f757ce6f900` |
| payload `LICENSE` (from the package, unchanged) | 6,617 | 163 | `fdf6e69fd59d45154edb97d9221c95c48ced4dee90ff32f5fc2438ba62ece566` |

- `diff` reports exactly one hunk: **lines 152–163 of the payload copy are appended after template line
  151**. Lines **1–151 are byte-identical** (verified by `head -151` on both, `diff` clean).
- **Licence body line range: lines 5–135** — from `# PolyForm Noncommercial License 1.0.0` through
  `of your licenses.`, inclusive, with trailing newlines. Measured: **4,563 bytes, sha256
  `ffcca38841adb694b6f380647e15f17c446a4d1656fed51a1e2041d064c94cc8`** — exactly the digest the file
  itself records. **Unmodified: yes.** (That is the official PolyForm body; lines 1–4 are the
  `Required Notice` and the begin-delimiter, and 137–163 are the provenance note and the scope section.)
- The appended section (`## Scope -- which files the licence terms above do not cover`) is **load-bearing
  for this deposit**: it states that no `harness/` directory ships and that the terms grant no rights in
  it. It should stay.

**Recommendation: upload the payload as built.** It carries the complete, unmodified PolyForm body, the
`Required Notice`, the provenance note, the scope section, the commercial terms and the contribution
terms — strictly more than the template alone would have provided.

---

## 8. What else a deposit needs (Job 4) — and NOT built here

The workspace holds three papers. Only one has a promoted release tree.

**`encoder-crossover-190`** — the subject of this deposit. Released tree exists and is complete enough to
deposit (§1–§7).

**`papers/gated-read-batching`** — no `released/` directory. Its released subset exists only as five
loose files under **`scratch/urelease7/cut3/`**, recorded as associated with the gated-read paper:

| file | bytes | sha256 | role |
|---|---|---|---|
| `METHOD.md` | 8,076 | `c28b7bc9df75bffc7053885dcfbdab28c42397258822e19899636424c80c77b7` | method + reader instructions |
| `provenance.json` | 171 | `2b2e0bc3c49ac314683eaa8f3af1809700d8eb7c0852f3d9e9ffc40426947cbd` | provenance of the withheld raw record (`input_sha256 5732766d…`, 2,267,742 B, 9,260 lines) |
| `record.json` | 5,008 | `9922cdc83fd68573845f9b045962111fedf4cf3afa66ee9d7df3b734d1ffa3ee` | reduced aggregate record (5 modes, end-to-end arms) |
| `sealed.json` | 620 | `35a6a66595bca97b1e4cbf0b0fb04ab5cde3d8edb5019f6ed3a6d92f52b759c5` | the sealed literals |
| `verify_claims.py` | 19,507 | `db0feb87cc0c645cd45fb748046c3416c495b1cc77ea387e20d6e04d8b1d00fb` | the verifier |

**Is it complete enough to deposit?** It is a **coherent minimal release in substance** — record +
method + verifier + provenance + sealed literals is exactly the five roles, and `METHOD.md` documents a
clean exit-code contract (`0` reproduced, `1` claim failed, `3` a needed record section is absent, so
minimality is demonstrated rather than asserted). Its own `METHOD.md` is unusually honest about its
limit: of **148 expectations, 145 recompute by arithmetic and 3 are sealed** (`0.575` cheapest-sufficient
and `207`/`207` router degeneracy), whose PASS lines are **self-referential and prove nothing**, because
those two published figures do not reproduce from the shipped rows.

**What is missing before it could be deposited:**

1. **No licence, commercial terms or contribution terms.** It carries no `LICENSE`/`COMMERCIAL.md`/
   `CONTRIBUTING.md` at all, so the author's licence decision (§4) is not expressed in the artifact.
2. **No README** in the sense of a deposit front page (the role is partly covered by `METHOD.md`).
3. **No `CITATION.cff`** and **no `MANIFEST.json`** integrity record.
4. **No `released/` promotion** — it is still scratch state, not a sealed payload, with no archive, no
   digest and no top-level directory discipline.
5. **Not verified by this unit**: I read `METHOD.md` in part, `sealed.json` and `provenance.json` in
   full, and the first 1,200 bytes of `record.json`. I did **not** run `verify_claims.py` and did **not**
   re-derive its counts.
6. Its record contents also need the same neutralisation check the encoder package got; I did not run one
   against `cut3`.

**Per the brief, this unit did not build it.**

**`papers/replay-record-not-decision`** — no `released/` directory and no candidate release subset was
found for it. Its directory holds `AVAILABILITY.md`, `CLAIMS.md`, `GAPS.md`, `MANUSCRIPT.md`,
`REFERENCES.bib`, `REFS.md`, `rendered/`, `submission/`. **I did not inspect its `AVAILABILITY.md`**, so
whether it declares a release I cannot say; on the filesystem evidence alone, no released artifact of its
own exists yet. Its released artifact is therefore **missing entirely** if the author wants one.

---

## 9. Verification performed on this deposit

| # | check | result |
|---|---|---|
| 1 | every copied file's sha256 vs `scratch/uneutral10/package` | 29/29 **match**, 0 mismatches |
| 2 | tarball top-level directories | **1** — `encoder-crossover-190-released/` |
| 3 | tarball member count | **37** (31 files + 6 dirs) |
| 4 | tarball bytes / sha256 | **157,272** / `a0a210fcdde1eab14e2e2d8d9c90b2ee897b4968ac7028c28c4c7d0187a5e088` |
| 5 | build determinism | two independent builds **byte-identical** (`cmp` clean) |
| 6 | extract into scratch, compare to source | 31 files, **851,043 B**, file-set **identical** to package + the 2 added files, 0 hash mismatches |
| 7 | `MANIFEST.json` self-check over the payload | **28 files checked, mismatches: none** (the manifest excludes itself) |
| 8 | the three shipped checks, from the extracted tree | all **exit 0**; `recompute-claims.py` prints `VERDICT: PASS`, `ALL PUBLISHED NUMBERS REPRODUCED: True` |
| 9 | do the regenerating scripts rewrite identical bytes? | **yes** — `cases.json`, `blinded_cases.json`, `parse_summary.json`, `disagreements.jsonl`, `metrics.json` all regenerate byte-identically; the tree's hashes do not move |
| 10 | residual count of the ten neutralised identifiers | **0** occurrences, 0 of 10 present (see §10) |

### Evidence lines from check 8

`verify/recompute-claims.py` ends

```
  ALL PUBLISHED NUMBERS REPRODUCED: True
  VERDICT: PASS
  fixture correctness digest: c7696edc0e71d83faafc2e489925788e0f36c6af94913674f8953718352c9a55
```

and prints one **boundary** among the reproduced claims:
`0.6684  decider-4b published baseline  QUOTED CONSTANT (results/REPORT.md 2; not recomputable in this
subset) OK` — compared, not re-derived; the harness that would re-derive it is withheld.
`parse_fixture.py` reports `"records_found": 190, "cases_parsed": 190, "options_total": 721` with every
failure list empty. `compare.py` reports route-A kappa `0.3248813212427869`, route-B kappa
`0.9013584840356494`, A/B mutual agreement `0.3684210526315789`, closed-subset kappa
`0.8837023738280471`.

---

## 10. Residual identifier scan (Job 5.4) — my own measurement

I did **not** re-run `scratch/uneutral10/scan.py` (I read it, but did not execute it) and I do **not**
quote its census numbers. I ran **my own scanner**, and validated it before use:

- **Self-test:** on a control string containing all ten tokens, all ten were detected; `brokerage` was
  **not** matched as `broker` and `editorship` was **not** matched as `editor`, so the identifier-boundary
  rule works. `SCANNER_VALID=True`.
- **Rule:** case-insensitive, `(?<![A-Za-z0-9_])token(?![A-Za-z0-9_])`, over all 31 extracted files.
- **The ten neutralised identifiers**, taken from `scratch/uneutral10/rename10.py`'s `ROLES` list —
  `editor, attached, reasoner, detached, topology, verifier, researcher, critic, broker, escalation`:

  **residual occurrences = 0; distinct identifiers present = 0 of 10.**

- **Project-specific vocabulary I can see in the payload** (same scanner, same rule) — these are
  *intentional published* identifiers, not residuals: `second-labeller` 31 (6 files), `decider-4b` 25
  (5), `harness` 18 (6), `MATERIALISE` 14 (5), `fixture-190` 10 (6), `PolyForm` 9 (5),
  `reflex-decisions` 7 (5), `EXP12` 3 (2), `typed-channel` 3 (2), `EXP#12` 0.
- **Generic tags:** `G01`–`G58`, **6,339 occurrences across 21 files, 56 distinct tags** (the
  neutralisation tags are the intended public form).

## 11. What I could not verify — stated plainly

- **No DOI exists** for the paper or for this deposit, so the "related identifier — the paper" cannot be
  filled in yet, and `CITATION.cff` has no `doi` field (§5).
- **The deposit itself has not been uploaded.** Nothing here proves Zenodo accepts the file or renders
  the metadata as intended.
- **`MANIFEST.json`'s `manifest_self` field** (`e44caf89…`) was **not** independently recomputed; only
  the 28 per-file `sha256`/`bytes` pairs were checked.
- **The creator name split** is an inference, flagged in §2.
- **The other two papers' release state** was assessed from directory listings plus the `cut3` files
  named in §8; I did not inspect `papers/replay-record-not-decision/AVAILABILITY.md` or
  `papers/gated-read-batching/` release-intent documents, and I did not run `cut3/verify_claims.py`.
- **The three sealed expectations** in `cut3` are self-referential by that file's own admission; they
  cannot be verified from the shipped rows.
- **Modes are normalised.** The source package files are mode `0600`; the payload and tarball use `0644`
  for files and `0755` for directories. No file **byte** changed (all sha256 verified), but the mode is
  not source-faithful. Flagged, not hidden; it makes the public archive readable.

---

## 12. Superseded record — read this before using anything below

An earlier record, **written by unit UAUCLEAN1 (2026-10-17)**, occupied this file. It is **superseded**
and its upload file **must not be used**. What it recorded:

| | UAUCLEAN1 (superseded) |
|---|---|
| Archive | `research-publish-packages-encoder-crossover-190-v1.zip`, staged at `scratch/uauclean1/zenodo/` |
| sha256 | `2338ed02c1c6770b182a79355dbda36cb6d593e08e65a3d38ae9da369c4b048f` |
| Sidecar | `research-publish-packages-encoder-crossover-190-v1.zip.sha256` |
| Members | **29 files at the archive ROOT — no wrapper directory** |
| Built with | `zip -r -X -D` from inside `scratch/uneutral10/package`, `-D` suppressing directory entries |
| Form text | `scratch/uauclean1/zenodo/ZENODO_UPLOAD.txt` |
| Version | `v1` |
| Claimed check | `unzip` then `diff -r x ../../uneutral10/package` → no output, "IDENTICAL" |

**Why it is superseded — two independent reasons:**

1. **It has no top-level directory.** Its members sit at the archive root, so extracting it into a
   working directory *does* explode 29 files directly into that directory — exactly the failure this
   unit's brief requires be prevented. The new payload wraps everything in
   `encoder-crossover-190-released/`.
2. **It is a `.zip`, not a `.tar.gz`**, and this unit's brief specifies the upload as
   `papers/encoder-crossover-190/released/encoder-crossover-190-released.tar.gz`. That path did not exist
   before this unit; the note elsewhere that referred to it as already built was a **mistake**, and the
   directory and archive are created here for the first time.

It also carried **version `v1`** and a sidecar `.sha256`. This unit declares **no version** (none was
assigned by the author) and ships no sidecar; the digest is recorded above and in the handoff instead.
Its `MANIFEST.json` in-payload check is the same check as §9 row 7 and agrees: 28 entries, no mismatch.

The UAUCLEAN1 archive is **not** deleted by this unit — it remains where it was staged so the author can
compare. Do not upload it.

---

## 13. UFIXMAN1 — the archive's `MANIFEST.json` now describes the archive (2026-10-17)

**The distinction this section exists to fix.** Two kinds of file ship in
`papers/encoder-crossover-190/released/encoder-crossover-190-released.tar.gz`, and they must never be
confused:

| class | files | count |
|---|---|---|
| **package content** | the 29 files of `scratch/uneutral10/package/` — `LICENSE`, `COMMERCIAL.md`, `CONTRIBUTING.md`, `README.md`, `MANIFEST.json`, `fixture/` (3), `preregistration/` (1), `results/` (7), `second-labeller/` (12), `verify/` (1) | **29** |
| **deposit metadata** | `CITATION.cff` (deposit-level citation) and `README_DEPOSIT.md` (deposit front matter) — added on top of the package for the deposit, not part of it | **2** |
| | archive total | **31** |

**The defect that was fixed.** `MANIFEST.json` has the same name in both trees, so which files each copy
describes depends on *when* it is generated. The archive used to pack the *package's* copy: it listed 28
files and `counts.files` 29, while the extracted archive's disk holds 31 files. Its `policy` field reads
`fail-closed: this manifest lists exactly the files on disk in this package` — true of
`scratch/uneutral10/package/`, **false of the archive**, where `CITATION.cff` and `README_DEPOSIT.md` went
unlisted and `check_manifest.py` reported `unlisted=2` / `VERDICT FAIL` (exit 1) at the extracted root.

**The fix: order, not bytes.** The archive's copy is now regenerated *after* the archive tree is
assembled, with the project's own tool — `tools/package/regen_manifest.py --package
<stage>/encoder-crossover-190-released --no-note --generated-utc <pinned>`. Assembly step (script:
`scratch/ufixman1/build_archive.sh`; tar recipe unchanged from §"DEPOSIT_ARCHIVE.md:19-22"):
stage the 29 package files → add `CITATION.cff` + `README_DEPOSIT.md` → **regenerate `MANIFEST.json` in
the stage** → `tar --format=gnu --sort=name --owner=0 --group=0 --numeric-owner --mtime=@0 … | gzip -n -9`.
The package's own `MANIFEST.json` (`sha256 d41d82cf8aa838737a55d300bd77b74c787c44d482a5f964c4c446e40c2aac02`)
is **not written** by that step and still describes the package: 28 listed / `counts.files` 29 /
`bytes_total` 831,775.

**Rebuilt archive** (built twice in one run, `cmp` exit 0 → byte-identical):

| field | value |
|---|---|
| path | `papers/encoder-crossover-190/released/encoder-crossover-190-released.tar.gz` |
| bytes | **158,762** (was 157,650) |
| sha256 | `956d6363db4563ddd3d848790a4026590a38c86ced993ccd76aecdad66a7910a` |
| members | 37 (unchanged: 1 top dir + 5 subdirs + 31 files) |
| archive `MANIFEST.json` | `files[]` **30**, `counts.files` **31**, `counts.bytes_total` **844,089** (self-exempt), `manifest_self` `8daf32ea280059b2…`; `added: ['CITATION.cff','README_DEPOSIT.md'] changed: 0` |
| `README_DEPOSIT.md` (this file's sibling in the archive) | `papers/encoder-crossover-190/released/README_DEPOSIT.md`, **10,585 B** (`71f76e605644d6db0c45b7db6ec0c39273e4edb8e325e2a3acbf5f977468fe6d`; superseded 10,477 B, 2026-10-18 UFIXDEP1, rebuilt the same day by UREADMEFIX1) — now the canonical deposit front matter, and states the two-class distinction |

**Evidence, literal.** `check_manifest.py --package <extracted archive root>` →
`missing=0 hash_mismatch=0 size_mismatch=0 unlisted=0 listed_but_absent=0` /
`manifest_self_recomputes=True` / `VERDICT PASS`, exit **0**. Same tool against
`scratch/uneutral10/package` → `VERDICT PASS`, exit **0**. `verify/recompute-claims.py` inside the
extracted archive → exit **0**, `ALL PUBLISHED NUMBERS REPRODUCED: True`, fixture digest `c7696edc…`.
`diff -r` of the package against the archive payload (excluding `MANIFEST.json`, `CITATION.cff`,
`README_DEPOSIT.md`) → exit 0, empty: the 29 package files are byte-identical.

**The previous `30 listed / counts.files 31 / bytes_total 840,000` manifest — which tree it described.**
It was not superseded bytes of the shipped archive. It lives *only* at
`scratch/udeposit2/superseded-unpacked-tree/MANIFEST.json` (`files[]` 30, `counts.files` 31,
`bytes_total` **840,000**, `manifest_self` `89ef383627e2e774…`) — i.e. in the **unpacked-tree variant**
`papers/encoder-crossover-190/released/encoder-crossover-190-released/`, an un-git-tracked third
packaging shape that was never shipped and was **moved out of the released area** to that scratch path by
UDEPOSIT2 (see `strategy/DEPOSIT_ARCHIVE.md` §"Superseded"). Its `counts.bytes_total` 840,000 reflects the
*then-current* extras (pre-fix `COMMERCIAL.md` 3,512 B and the older `README_DEPOSIT.md`); the current
extras give 844,089. So: the previous unit **regenerated a manifest in a tree that was not the shipped
one — it was neither the package nor the archive's packed copy — and that tree was subsequently retired
to scratch.** Its shape was right; its target was wrong. The shipped package and the shipped archive were
both left with the package's 28-file manifest.

**Gotcha for the operator.** `check_manifest.py`'s `--package` resolves a *relative* path against the
repository root, not the current directory, so `--package .` from inside the extracted tree resolves to
the repo root and dies with `FATAL: no MANIFEST.json in <repo root>` (exit 2). Always pass the absolute
that you actually mean.

**Do not upload** the superseded bytes `7389bd879e970d840a528a9a19bfb9a6623babf3ec10746b18fc616bf2b4dad3`
(157,650 B); they are the pre-fix archive.

## UFIXDEP4 — 2026-10-18 (append only): archive digest moved again

`scratch/uneutral10/package/CONTRIBUTING.md:3` carried a self-labelled **DRAFT** banner linking to a
`PLACEMENT.md` that never ships; it was replaced with a released-artefact contributing statement, so the
archive was rebuilt. **Live values (measured):** bytes **159,014**, sha256
`478941c0259b9309145aea17413c3795d0078c2994d32739a01ff09fc51e89d7`, members **37**. (Superseded 2026-10-18 by UREADMEFIX1: **158,956** B / `bcdbf75eff70eec77fc1f4a181947c86dd9c12862871315e1dfeec8578fbb6a2`, the UFIXDEP4 build this section recorded.)
**Superseded, do not upload:** `956d6363db4563ddd3d848790a4026590a38c86ced993ccd76aecdad66a7910a` /
158,762 B (2026-10-18 UFIXDEP1); `7389bd879e970d840a528a9a19bfb9a6623babf3ec10746b18fc616bf2b4dad3` /
157,650 B (2026-10-17 UDEPOSIT2); `a0a210fcdde1eab14e2e2d8d9c90b2ee897b4968ac7028c28c4c7d0187a5e088` /
157,272 B (2026-10-17 URELEASE9). The banner above and §1's tables are the historical record; the
authoritative live values are in `strategy/DEPOSIT_METADATA.md` §0.

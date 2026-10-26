# Submission Kit — three papers, two venues each

One document, top to bottom. Every value below was measured on this disk on **2026-10-19** (workspace
`/home/zer0null/reserach extarctor`). Where a measured value disagrees with the value in the original task
card, §6 says so explicitly — nothing has been adjusted to fit.

The files to upload are copied in [`submission-kit/`](../submission-kit/README.md). Upload from there.

---

## 1. Status at a glance

| Paper | Concept DOI | Latest published record | Archive | Bytes | md5 (verified) | Ready to submit? |
|---|---|---|---|---|---|---|
| encoder-crossover-190 | `10.5281/zenodo.23463944` | v3 = record `23482311` | `papers/encoder-crossover-190/released/encoder-crossover-190-released.tar.gz` | 159,182 | `b4dac172003233d7d6c8c78c909b5594` | **Yes** — v1 and v2 are superseded |
| replay-record-not-decision | `10.5281/zenodo.23482511` | v2 = record `23483304` | `papers/replay-record-not-decision/released/replay-record-not-decision-released.tar.gz` | 107,764 | `41afa2831ff2f43af91d9c4416d8f658` | **Yes** |
| gated-read-batching | `10.5281/zenodo.23483314` | v2 = record `23485733` | `papers/gated-read-batching/released/gated-read-batching-released.tar.gz` | 128,902 | `a7e81bf7c8ebe49da83e869a002be1b2` | **Yes, ready to upload** — the Conflicts-of-Interest placement was corrected on 2026-10-19 and the gated preprint zip and TMLR PDF were rebuilt, re-copied into the kit and re-measured (§6.5, resolved) |

All three md5 values were re-computed with `md5sum` and **match** the card exactly. All three archives are
published, current, and correct: **there is nothing left to upload to Zenodo.**

The concept DOI is the citable identifier — it always resolves to the latest version. Version DOIs die at
the next version; do not cite them.

---

## 2. Zenodo metadata edits — two records, no new version

Two of the three published records are missing the `language` field. This is a metadata edit only:

1. Open the record (`encoder-crossover-190` → concept `10.5281/zenodo.23463944`, latest record `23482311`;
   `gated-read-batching` → concept `10.5281/zenodo.23483314`, latest record `23485733`).
2. Click **Edit**.
3. Set **Language** to **English**.
4. **Save** (publish the metadata edit).

The third record, `replay-record-not-decision` (record `23483304`), already says `eng` — **no action**.

**This does not mint a new version and does not change the DOI.** The concept DOI and the version DOI both
stay exactly as they are; only the record's metadata is updated. Do not use "New version" for this.

---

## 3. Preprints.org — three submissions, one per paper

Submit each paper separately. Upload the **manuscript file** from the kit, and paste the fields below.

### 3.0 Article type — choose `Article`, for all three, identically

On the Preprints.org submission form (the **Submit** button, top-right), set the **type** to **`Article`** —
for `encoder-crossover-190`, `replay-record-not-decision` and `gated-read-batching` alike. There is no
per-paper variation here: all three are unpublished research articles with no conference venue.

Why, in one sentence: the only other option, **`Conference Paper`**, exists solely for unpublished,
DOI-less conference papers, and these are neither conference papers nor DOI-less (each has its own
Zenodo concept DOI, §3.9). Choosing `Conference Paper` for any of them is wrong.

### 3.1 Manuscript file

| Paper | File (in kit) | Bytes | sha256 (verified) |
|---|---|---|---|
| encoder-crossover-190 | `submission-kit/preprints/encoder-crossover-190-preprints.zip` | 28,712 | `705bc498c7c7eb7cf1e53cae8f49fb8656787694c39dbc7c5f4064f9aa7caf7f` |
| replay-record-not-decision | `submission-kit/preprints/replay-record-not-decision-preprints.zip` | 11,526 | `1b520f22ad7ec0d83e0c82a734fd5790724a2dfbb175a2600ac323294953537d` |
| gated-read-batching | `submission-kit/preprints/gated-read-batching-preprints.zip` | 15,296 | `7efe3af1d358552b2e4231a63cb02820d25bd678aa1761f06ba5880bdfe783a0` |

Each zip contains exactly one file, `main.tex` (the LaTeX manuscript). Copy is byte-identical to the source
zip (§6). No other file is in the zip.

### 3.2 Title — copy from the manuscript's own H1, do not retype

The title is line 1 of `papers/<slug>/MANUSCRIPT.md`, minus the leading `# `. Retyping risks silently
changing a word — copy-paste it.

**encoder-crossover-190**

> The small-encoder crossover is a prompted-baseline artefact: a fine-tuned encoder head loses to a fine-tuned 4B decision model by 0.33 and to a majority-class control

**replay-record-not-decision**

> Replay reproduces the record, not the decision

**gated-read-batching**

> Cheap batches, weak gate: batching binary read-gate decisions 16–90-way at `effort=none` does not measurably degrade them, and a purpose-conditioned read gate on header and structure alone is not yet a classifier

For the gated paper the form field must carry **`effort=none` without the backticks**, and keep the **en dash**
in `16–90-way` (U+2013, not a hyphen). Corrected for a form field:

> Cheap batches, weak gate: batching binary read-gate decisions 16–90-way at effort=none does not measurably degrade them, and a purpose-conditioned read gate on header and structure alone is not yet a classifier

### 3.3 Abstract

Paste the text from the kit file; do not re-wrap or edit it.

| Paper | File | Characters (measured `wc -m`) | Limit |
|---|---|---|---|
| encoder-crossover-190 | `submission-kit/abstracts/encoder-crossover-190.txt` | **1,195** | under arXiv's 1,920 |
| replay-record-not-decision | `submission-kit/abstracts/replay-record-not-decision.txt` | **1,594** | under arXiv's 1,920 |
| gated-read-batching | `submission-kit/abstracts/gated-read-batching.txt` | **1,884** | under arXiv's 1,920 |

All three are under arXiv's 1,920-character limit. **Preprints.org states no abstract character limit**, so
keep the abstracts exactly as they are — do not trim them to the arXiv bound.

### 3.4 Keywords — verbatim from the single source of truth

Source: the `PACKAGES` registry in `tools/package/md2tex.py` (`keywords=` entries; lines 134, 175, 279).
Printed verbatim, same order, nothing added or removed:

**encoder-crossover-190**

```text
text classification benchmark, encoder classifiers, fine-tuned decision model, sealed evaluation, majority-class control, McNemar exact test, reproducibility, withheld evaluation harness
```

**replay-record-not-decision**

```text
replay determinism, LLM decision replication, binding divergence, record versus decision, option-index encoding, agent trace reproducibility
```

**gated-read-batching**

```text
tool-call gating, batched decisions, read-gate classification, binary gate decisions, token exposure, low-effort prompting
```

### 3.5 Authors / affiliation / contact / ORCID — identical for all three

| Field | Value |
|---|---|
| Author | `Aswin Ram Kalugasala Moorthy` |
| Affiliation | `Independent researcher` |
| Corresponding email | `aswinram.k.1603@gmail.com` |
| ORCID | `0009-0009-9505-3546` |

### 3.6 Archive / subject area

- **First level:** `Computer Science and Mathematics` — verified.
- **Second level:** **not verifiable.** Preprints.org renders its second-level list as an image, so the exact
  strings cannot be confirmed from here. Pick from the list the form shows you. Suggested fits:
  - encoder-crossover-190 → artificial intelligence / machine learning / NLP
  - replay-record-not-decision → software engineering, or machine learning
  - gated-read-batching → artificial intelligence / NLP / information retrieval

If none of those strings appears in the form's list, pick the closest listed item — do not invent a category.

### 3.7 Licence

Fixed at **CC BY 4.0** by the platform. There is no selector and nothing to choose. State it as such.

### 3.8 Conflicts of Interest — present, and positioned before the references

All three papers carry the section, and in all three it precedes the reference list. Exact lines in
`papers/<slug>/submission/main.tex`:

| Paper | `\section*{Conflicts of Interest}` | Reference list starts | Position |
|---|---|---|---|
| encoder-crossover-190 | line **447** (text line 449) | `\section*{References}` line 451, `\begin{thebibliography}` line 454 | **immediately before** the reference list |
| replay-record-not-decision | line **235** (text line 237) | `\begin{thebibliography}` line 239 | **immediately before** the reference list (no `\section*{References}` heading in this paper) |
| gated-read-batching | line **281** | `\section*{References}` line 285, `\begin{thebibliography}` line 289 | **immediately before** the reference list — nothing between (corrected 2026-10-19, §6.5) |

All three are now immediately before; the gated paper was moved there on 2026-10-19 (§6.5, resolved).
See §6, finding 2 for the pre-correction state that was found earlier.

---

### 3.9 Data availability — each paper enters **its own** concept DOI

The form carries a Data availability field, and the three deposits are **independent** — one per paper:

| Paper | Concept DOI to enter (its own) | Its own latest Zenodo record |
|---|---|---|
| encoder-crossover-190 | `10.5281/zenodo.23463944` | v3 = record `23482311` |
| replay-record-not-decision | `10.5281/zenodo.23482511` | v2 = record `23483304` |
| gated-read-batching | `10.5281/zenodo.23483314` | v2 = record `23485733` |

**Enter that paper's own concept DOI in that paper's own submission — never one paper's DOI in another's
form.** Cross-posting a DOI is the failure mode this subsection exists to prevent: it is not a formatting
slip, it points readers at the wrong deposit. These three values agree with the §1 status table (lines
15–17); if a future edit makes the two disagree, the status table is the source of record.

> Corrected 2026-10-19: `strategy/PREPRINTS_SUBMISSION.md` §8 step 8 used to point every submission, and
> specifically #2 and #7, at `10.5281/zenodo.23463944`. That instruction predates the #2 and #7 deposits
> and is corrected at its source (the old wording is preserved there as history).

## 4. TMLR — three separate submissions, one per paper

Submit each paper as its own TMLR submission on OpenReview.

### 4.1 Manuscript

| Paper | File (in kit) | Bytes | Pages | sha256 (verified) |
|---|---|---|---|---|
| encoder-crossover-190 | `submission-kit/tmlr/encoder-crossover-190-main.pdf` | 177,298 | **16** | `fb95f0ac302a07678eaf5f73ef7038a5d46beeb6807830f065a94ffb38cf1109` |
| replay-record-not-decision | `submission-kit/tmlr/replay-record-not-decision-main.pdf` | 93,109 | **7** | `cefd09a7a161d73bf7ae27303ca8cb00dbab2761485beca30bb90856846aee7a` |
| gated-read-batching | `submission-kit/tmlr/gated-read-batching-main.pdf` | 107,504 | **10** | `25a9394e4f649335dd61209dc0075ece5091d0363f675042078a440db79bfeba` |

Page counts re-measured with `pdfinfo`; all three match the expected 16 / 7 / 10.

### 4.2 Fields

| Field | What to enter |
|---|---|
| Author list | the **real** author list on the form (`Aswin Ram Kalugasala Moorthy`) — the form is not anonymous |
| Manuscript PDF | the anonymised PDF above — **the PDF itself stays anonymised** |
| Code / data link | **none** — leave empty |
| Conflicts of interest | **none** |
| Acknowledgements | **none** |
| Title / abstract | only if the form asks: §3.2 title (same H1) and §3.3 abstract file |

### 4.3 The one hard rule

> **No Zenodo DOI, no GitHub link, and no author name may appear anywhere in a TMLR submission.**

This includes the PDF body, the metadata, and any field you fill in — the PDF must not name the author even
though the form does. All three PDFs were checked on disk and are **clean of every one of those, including
as raw bytes** (`grep -a` for `zenodo`, `github`, `kalugasala`, `aswinram` → no hit in any of the three), and
the PDF metadata carries no `Author`/`Title` entry (only `Creator: LaTeX with hyperref`,
`Producer: xdvipdfmx`). Do not paste the Zenodo DOI into an OpenReview comment or the abstract either.

---

## 5. What not to do

- **Do not re-upload any paper to Zenodo.** All three records are published and current (§1). A new version
  would mint a new DOI inside the concept, superseding a record that is already correct.
- **Do not put the Zenodo concept DOI into a TMLR submission.** It is the exact identifier that de-anonymises
  the paper.
- **Do not edit the archives.** Their md5 values are the ones the papers' own data-availability statements
  cite (e.g. gated `main.tex` line 275 cites md5 `a7e81bf7…`). Re-tarring one changes the cited digest.
- **Do not trim the abstracts to 1,920 characters.** That is an arXiv limit; Preprints.org states none.
- **Do not retype the titles.** Copy from `MANUSCRIPT.md` line 1, then fix only the gated backticks (§3.2).

---

## 6. Verification log and findings

### 6.1 Commands run (all read-only)

```sh
md5sum papers/*/released/*-released.tar.gz
sha256sum papers/*/preprints/*-preprints.zip papers/*/tmlr/main.pdf
stat -c '%s %n' papers/*/released/*-released.tar.gz papers/*/preprints/*-preprints.zip papers/*/tmlr/main.pdf
for f in papers/*/tmlr/main.pdf; do pdfinfo "$f" | awk '/^Pages:/{print $2}'; done
wc -m papers/*/submission/ABSTRACT_METADATA.txt
grep -n -i 'conflict' papers/*/submission/main.tex
grep -n '"keywords"' tools/package/md2tex.py
```

Re-verify the kit at any time with:

```sh
cd submission-kit && sha256sum preprints/*.zip tmlr/*.pdf abstracts/*.txt
```

### 6.2 Finding 1 — five of six upload-file sha256 values differ from the task card (files on disk are newer)

The card carried sha256 values for three zips and three PDFs. On disk today: the **encoder zip matches**; the
**other two zips and all three PDFs do not**. Byte sizes and page counts are identical to the card in every
case, and the zips' payload is byte-identical to the paper's own `submission/main.tex`.

| File | Card said | Measured now |
|---|---|---|
| encoder zip | `705bc498…` | `705bc498c7c7eb7cf1e53cae8f49fb8656787694c39dbc7c5f4064f9aa7caf7f` — **match** |
| replay zip | `68fa2a2d…` | `1b520f22ad7ec0d83e0c82a734fd5790724a2dfbb175a2600ac323294953537d` |
| gated zip | `86176d9b…` | `08e9ea92cf46b0407ffc8e3d412f4e6d299e4a26b58213c72c16c780fd47e8f9` |
| encoder PDF | `f1b05156…` | `fb95f0ac302a07678eaf5f73ef7038a5d46beeb6807830f065a94ffb38cf1109` |
| replay PDF | `5c06b95a…` | `cefd09a7a161d73bf7ae27303ca8cb00dbab2761485beca30bb90856846aee7a` |
| gated PDF | `d9eb63f0…` | `0ed045244e4a16fb242125ab4966653c4b4c4b73b73c80e6f9a6677ddd29b9c9` |

> **Superseded 2026-10-19 (gated rows only).** The gated zip and gated TMLR PDF were rebuilt once more after
> the CoI correction. The `Measured now` column above is the state at the time of this finding, not the kit's
> current contents — today's gated values are in §6.5 (zip 15,296 B / `7efe3af1…`, PDF 107,504 B /
> `25a9394e…`).

**Evidence for the cause:** file mtimes put the rebuilds after the card's values were taken — encoder zip
`2026-10-19 01:39` (old, hence it still matches), replay zip `14:27`, gated zip `15:10`, encoder/replay PDFs
`14:29`, gated PDF `15:12`. A workspace-wide sha256 scan of every `.zip` and `.pdf` found **no file matching
any of the five card values** — the prior bytes no longer exist, so the difference cannot be attributed with
proof. The zip containers still hold the identical `main.tex`, and PDF page counts and byte sizes are
unchanged, so the most likely cause is container metadata (zip header mtimes; PDF `/CreationDate`, `/ModDate`,
`/ID`) rather than content — but that is inference, not verification.

**What this document uses:** the **measured values**, because they are what the author will actually upload
and what a re-download will be checked against. The card's values are recorded above so the discrepancy is on
the record, not silently dropped. Nothing was edited to make the numbers agree, and no artifact was rebuilt.

**A PDF's sha256 is not reproducible across builds by design.** LaTeX writes a fresh `/CreationDate` and a
fresh document `/ID` on every run, so two builds of the identical source produce identical size, identical
page count and identical extracted text but a different sha256. The zip is the same story: the container
stores a per-file mtime header. So the **stable facts** are size, page count and content — those are what must
survive a re-download. The sha256 is an identity check for *this exact file*, not a claim that any future
rebuild will reproduce it. If the author re-downloads or re-copies a file, size and pages must match; the
sha256 need only match the value printed here for the file he holds.

**Page geometry is deliberate, not drift.** The gated TMLR PDF is **US Letter (612×792 pt)** by design,
because TMLR's style is a US venue format; the preprint PDFs are A4. The two formats are deliberately
different — do not "fix" the gated page size.

### 6.3 Finding 2 — gated COI is not immediately before the reference list

The card expected `Conflicts of Interest` immediately before the references in all three
`submission/main.tex`. Encoder (447 → 451) and replay (235 → 239) do. Gated does not: COI is at line 269, and
Data availability (273), Licence (279) and the concept-DOI paragraph (281) intervene before `References`
(285). The COI statement still precedes the references, so the requirement is met; the "immediately" wording
is what is wrong. No edit made.

### 6.4 What was verified clean

- All 9 kit files match their sources by `sha256sum` (`FAILFLAG=0`).
- Abstract character counts 1,195 / 1,594 / 1,884 — equal to the card and to `wc -m` on disk.
- TMLR PDFs: no `zenodo`, `github`, `kalugasala`, `aswinram` in raw bytes; no `Author`/`Title` in metadata.
- Keywords reproduced from the registry, character for character, in registry order.

### 6.5 RESOLVED 2026-10-19 — CoI placement corrected, gated paper only

**Status: resolved.** The correction landed, the gated preprint zip and TMLR PDF were rebuilt, and the kit
copies plus every digest in this document were re-measured from disk and patched.

**History — what the problem was (kept as the record).** The gated paper's `Conflicts of Interest` was not
immediately before its reference list (§6.3). Preprints.org requires the section "placed just before the
reference list", so a separate unit was to move it to immediately before `\section*{References}` and then
regenerate the paper's preprint zip and TMLR PDF. While that was in flight the gated rows in §1, §3.1 and
§4.1 were marked **provisional**, the gated files were not to be uploaded, and the provisional sha256 was
explicitly not a corruption check — those files were correct copies of the then-current sources, simply about
to be superseded.

**What was actually done.** `Conflicts of Interest` sat at `main.tex:269`, with Data availability, Licence
and the concept-DOI paragraph between it and `\section*{References}` at `:285`. It now sits at `:281` with
References at `:285` and **nothing between**. `MANUSCRIPT.md` was edited — it is the source of truth — and
`main.tex` was regenerated **only** via the converter; `main.tex` was not hand-edited. The change is a pure
block move: 4 lines out, the same 4 lines in. The numeric multiset is unchanged at **571 literals / 149
distinct**, with an empty diff.

**Rebuilt gated artifacts (measured on disk; these are the kit copies):**

- `papers/gated-read-batching/preprints/gated-read-batching-preprints.zip` — **15,296 B**, sha256
  `7efe3af1d358552b2e4231a63cb02820d25bd678aa1761f06ba5880bdfe783a0` (was 15,312 B,
  `08e9ea92cf46b0407ffc8e3d412f4e6d299e4a26b58213c72c16c780fd47e8f9`)
- `papers/gated-read-batching/tmlr/main.pdf` — **107,504 B**, sha256
  `25a9394e4f649335dd61209dc0075ece5091d0363f675042078a440db79bfeba`, **10 pages** (was 107,520 B,
  `0ed045244e4a16fb242125ab4966653c4b4c4b73b73c80e6f9a6677ddd29b9c9`)

The deposit archive is **unchanged**:
`papers/gated-read-batching/released/gated-read-batching-released.tar.gz` is still **128,902 B**, md5
`a7e81bf7c8ebe49da83e869a002be1b2`.

**Two honest gaps the fixing unit disclosed:**

1. `papers/gated-read-batching/tmlr/README.md` does **not** exist — only `tmlr/_superseded/README.md`. The
   anonymising chain was therefore reconstructed from the historical pair and proven by a **byte-identical
   round-trip** before it was applied.
2. The TMLR PDF is byte-reproducible only under `SOURCE_DATE_EPOCH=0`. Otherwise roughly **2.7 KB** of
   trailing XRef / `/ID` bytes drift, while the extracted text and the size stay identical.

The gated TMLR PDF is **US Letter (612×792 pt)** by design, because TMLR's style is a US venue format; the
preprint PDFs are A4. The two are deliberately different, not a defect (§6.2).

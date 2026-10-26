# Preprints.org submission — verified requirements, bundles, and the author's runbook

**Written by:** unit `UPREPRINT1`, 2026-10-18.
**Scope:** the three papers ready for the second rung of the ladder (Zenodo deposit already published at
concept DOI `10.5281/zenodo.23463944`):

| short name | directory | pages | `\bibitem`s |
|---|---|---|---|
| #3 | `papers/encoder-crossover-190/` | 25 | 13 |
| #2 | `papers/gated-read-batching/` | 13 | 13 |
| #7 | `papers/replay-record-not-decision/` | 10 | 8 |

Everything below is quoted from the pages named, or is the literal output of a command recorded here.
Nothing was uploaded, submitted, registered or sent anywhere.

---

## 1. Verified requirements, with the sentences that decide them

All three sources fetched **read-only** on 2026-10-18 (plain `web_fetch` gets `HTTP 403 Access Denied`
from Akamai; the pages were retrieved with a stealthy scrape, `HTTP 200`).

### 1.1 The file format and the archive — `https://www.preprints.org/instructions-for-authors`

> "Files should be submitted in Microsoft Word or LaTeX format. For LaTeX files, ensure that all files
> necessary, including the .bib file, if applicable, to recreate the PDF are included in a zip or similar
> archive."

Restated by the Help Center, `https://www.preprints.org/help-center/submission-guidelines`:

> "A manuscript in a Microsoft Word or LaTeX format. For LaTeX files, please ensure that all the files
> (e.g., bib file, references) necessary to create a PDF are included in a .zip or similar format"

**Decisive reading.** The `.bib` clause is *conditional* — "**if applicable**". The requirement is
*sufficiency*: whatever the archive contains must be enough to recreate the PDF.

### 1.2 The first page — `https://www.preprints.org/instructions-for-authors`, "Formatting Guidelines"

> "The first page of your manuscript must contain the title, author list, abstract, keywords,
> corresponding author contact details, and affiliations for all authors."

Six elements: title, author list, abstract, **keywords**, **corresponding-author contact**,
**affiliations for all authors**.

### 1.3 Style and template — same section

> "Any style is allowed for submitted papers. However, it is recommended that you use Preprints.org's
> template. If using a journal template, all publisher and journal logos and names should be removed from
> both the manuscript and any supplementary materials."

Template use is *recommended*, not required; our `article`-class output is admissible.

### 1.4 Metadata entered in the web form — `https://www.preprints.org/help-center/submission-guidelines`

> "You will need to provide the following information to make a submission: Manuscript title; Abstract;
> Keywords; Names, affiliations, and email addresses for all authors (institutional email addresses or
> email addresses used in previously published papers are recommended); A manuscript in a Microsoft Word
> or LaTeX format. …; Supplementary materials (if applicable); Copyright holder permission (if
> applicable)"

Note the keyword and affiliation/email data is **also** required in the form, independently of the
manuscript. The form fields are the author's to fill; the first-page presence is a separate, documentary
requirement (§1.2) and the two are not substitutes.

### 1.5 Conflicts of interest — `https://www.preprints.org/instructions-for-authors`

> "The corresponding author must include a summary statement in the manuscript in a separate section
> 'Conflicts of Interest' placed just before the reference list. … If no conflicts exist, the authors
> should state the following: 'Conflicts of Interest: The authors declare no conflicts of interest.'"

### 1.6 Account and licence — `https://www.preprints.org/instructions-for-authors` and `/about`

> "Once you have carefully checked the criteria above, click the Submit button in the top-right corner of
> the website to submit your manuscript. You will need to have an MDPI account and log in to submit."

Licence, from `https://www.preprints.org/about`:

> "All preprints are posted with a Creative Commons CC BY 4.0 license, ensuring that authors retain
> copyright and receive credit for their work while allowing anyone to read and use their work."

and again, in the "How It Works" pipeline:

> "Preprints that pass the screening process are posted online in open-access format under a Creative
> Commons CC BY 4.0 license."

There is **no licence selector** described anywhere on the submission path; CC BY 4.0 is what posting
means. The licence is fixed in the sense that no alternative is offered — it is not a choice the form
presents.

### 1.7 Recommended, not required — graphical abstract

> "we recommend producing a graphical abstract to display on the website alongside the textual abstract.
> The graphic should be provided as a JPG or PNG file."

Recommendation only. No graphical abstract is produced here; none is required.

---

## 2. What the earlier record got wrong

The card carried three claims from an earlier unit. Two are **imprecise in ways that change what ships**,
one is right but from the wrong page.

| earlier claim | verdict | evidence |
|---|---|---|
| "requires Word or LaTeX source **including the `.bib` file** in a zip" | **Overstated.** The requirement is conditioned: "including the .bib file, **if applicable**". | §1.1 quote. |
| "**a PDF alone is NOT accepted**" | **Not stated on any page we could fetch.** The page says files "should be submitted in Microsoft Word or LaTeX format" and that the archive must suffice to recreate the PDF. It never says a PDF-only upload is rejected; that is an inference from the format sentence, not a sentence. | §1.1 quote — the only file-format sentence on either page. |
| "first page must carry title, author list, abstract, keywords, corresponding-author contact and affiliations" | **Correct**, verbatim. | §1.2 quote. |
| "the licence is fixed CC BY 4.0" | **Correct**, but the deciding sentence is on `https://www.preprints.org/about`, *not* on the Instructions for Authors page. The Instructions page mentions licences only obliquely ("copyright, and licenses" among the corresponding author's duties). | §1.6 quotes. |

A requirement the earlier record **missed entirely**: the mandatory "Conflicts of Interest" section
(§1.5). None of the three papers has one — see §4.

---

## 3. The bibliography decision — ship the self-contained `main.tex`, ship no `.bib`

**The complication.** Each `submission/main.tex` is generated from `MANUSCRIPT.md` and inlines its
bibliography as a `thebibliography` environment. It never calls `\bibliography{}`:

```
$ grep -n 'bibliography\|thebibliography' papers/encoder-crossover-190/submission/main.tex | head -5
452:\begin{thebibliography}{99}
466:\end{thebibliography}
$ grep -c '\input\|\include{\|\bibliography{\|\includegraphics' papers/*/submission/main.tex
encoder-crossover-190:0   gated-read-batching:0   replay-record-not-decision:0
```

So a `.bib` is **not among "all files necessary … to recreate the PDF"**, and the requirement is
conditional on exactly that ("if applicable").

**Decision: each bundle is the single file `main.tex`, and nothing else.** Reasons, in order of weight:

1. **Sufficiency is the actual requirement, and it is proven** — §6 compiles every bundle from a clean
   extraction with a zero-error build. The `.bib` would add nothing to the rebuild.
2. **#2 has no `.bib` to ship.** `papers/gated-read-batching/REFERENCES.bib` does not exist
   (`ls` → no such file). Any policy of shipping the `.bib` would make the three bundles structurally
   different for no reason, and could not be applied uniformly.
3. **A second bibliography mechanism is forbidden by the unit card, and a *dormant* one is worse than
   none.** `REFERENCES.bib` exists for #3 (13 `@` entries) and #7 (8 `@` entries) and those counts agree
   with the inlined `\bibitem` counts (13 and 8) — but the `.tex` never reads it. Shipping a file the
   document ignores invites a screener to treat it as the bibliography, and it is not: the inlined
   `thebibliography` is the only text that renders.
4. **No variant that consumes the `.bib` was produced.** Fairness requires saying why: producing one
   would mean writing a `\bibliography{REFERENCES}` + `\bibliographystyle` variant and re-running the
   bibliography engine, i.e. creating the second mechanism the card forbids, and its output could differ
   in ordering/formatting from the PDF the papers were checked against. The self-contained file is not a
   workaround — it is the paper.

**If the author prefers to belt-and-braces the `.bib` in**, the evidence says it is harmless for #3 and #7
and impossible for #2; the requirement does not ask for it, so this document ships without it.

---

## 4. First-page audit — what page 1 of each compiled PDF actually carries

Text below is `pdftotext -f 1 -l 1 -layout` of the paper's own compiled PDF
(`papers/<slug>/rendered/<slug>.pdf`), quoted literally. Requirement set from §1.2.

### 4.1 #3 `encoder-crossover-190` — 5 of 6 present

```
The small-encoder crossover is a prompted-baseline
  artefact: a fine-tuned encoder head loses to a
  fine-tuned 4B decision model by 0.33 and to a
              majority-class control
                   Aswin Ram Kalugasala Moorthy
                       Independent researcher
                    aswinram.k.1603@gmail.com
                                 Abstract
```

| element | present? | evidence |
|---|---|---|
| title | yes | first four lines |
| author list | yes | "Aswin Ram Kalugasala Moorthy" |
| abstract | yes | "Abstract" heading on page 1 |
| keywords | **NO** | `grep -in keyword submission/main.tex` → no match; no "Keywords" line anywhere in the PDF |
| corresponding-author contact | yes | `aswinram.k.1603@gmail.com` |
| affiliations | yes, thin | "Independent researcher" — an affiliation of a kind; a reader learns there is no institution |

### 4.2 #2 `gated-read-batching` — 3 of 6 present

```
    Cheap batches, weak gate: batching binary
  read-gate decisions 16–90-way at effort=none
     does not measurably degrade them, and a
   purpose-conditioned read gate on header and
        structure alone is not yet a classifier
                    Aswin Ram Kalugasala Moorthy
```

| element | present? | evidence |
|---|---|---|
| title | yes | five lines above the name |
| author list | yes | name line |
| abstract | yes | "Abstract" heading on page 1 |
| keywords | **NO** | no "Keywords" line in the PDF; `grep -in keyword main.tex` hits only the word "keyword/regex" in §2 prose |
| corresponding-author contact | **NO** | no email on page 1; `\author{Aswin Ram Kalugasala Moorthy}` carries no `\texttt{...@...}` |
| affiliations | **NO** | `\author{...}` is name-only, one line |

### 4.3 #7 `replay-record-not-decision` — 3 of 6 present, and page 1 *says so*

```
    Replay reproduces the record, not the decision
                    Aswin Ram Kalugasala Moorthy
    A short note. …
    Author block: the author-supplied name. The byline is Aswin Ram
Kalugasala Moorthy — the author's own name, supplied verbatim, name
only, with no affiliation, institution or contact stated.
```

| element | present? | evidence |
|---|---|---|
| title | yes | line 1 |
| author list | yes | name line |
| abstract | yes | "Abstract" heading on page 1 |
| keywords | **NO** | no "Keywords" line in the PDF |
| corresponding-author contact | **NO** | and page 1 states it explicitly: "name only, with no affiliation, institution or contact stated" |
| affiliations | **NO** | same sentence |

### 4.4 Consequence — a real, uniform gap

**Keywords are missing from all three papers**, and **#2 and #7 are missing contact details and
affiliations**. Per §1.2, this is a documentary mismatch: a screener reading page 1 will not find three
of the six required elements on #2 and #7, and one on #3. Per §1.4 the same data must be supplied in the
web form regardless, so the *form* can be completed; the *page* still falls short.

**This unit cannot fix it.** Its write paths are `papers/*/preprints/**`, and the fix belongs in
`submission/main.tex` (a `Keywords:` line after the abstract; an affiliation and contact line in the
`\author{}` of #2 and #7; and a `Conflicts of Interest` section before the references, §1.5). Editing a
copy inside `preprints/` would break the "bundle LaTeX == current `submission/main.tex`" digest rule, so
the gap is reported, not papered over. **Recommended next unit: `UPREPRINT2`** — add keywords/affiliation/
contact/COI to the three `submission/main.tex` files (author decision needed on what affiliation and
contact string #2 and #7 should carry), rebuild, re-bundle, re-verify digests.

Also noted: #3 cites the Zenodo deposit (3 occurrences of `23463944` in `main.tex`); #2 and #7 contain
**zero** occurrences — they carry no link to the published data deposit at all.

---

## 5. The bundles

Written to `papers/<slug>/preprints/`. One member per archive; no directories; therefore no absolute path
and no `../` can exist.

| paper | zip | bytes | sha256(zip) | member | sha256(member) | sha256(`submission/main.tex`) |
|---|---|---|---|---|---|---|
| #3 `encoder-crossover-190` | `encoder-crossover-190-preprints.zip` | 28,712 | `705bc498c7c7eb7cf1e53cae8f49fb8656787694c39dbc7c5f4064f9aa7caf7f` | `main.tex` (84,967 B) | `2b5d049ed7b5368657c227f9efab42a64d1a70304b34813401bf128297ad33cc` | *identical* |
| #2 `gated-read-batching` | `gated-read-batching-preprints.zip` | 14,094 | `feecb7f7879766bf9ecedaa03bbae3b8817eaab47513d092e42052a4127b74f5` | `main.tex` (39,351 B) | `9235ec53e581edf0884e7ca9d85e6be696a148d9599f0465af02f7927f635277` | *identical* |
| #7 `replay-record-not-decision` | `replay-record-not-decision-preprints.zip` | 11,379 | `63044528d554ac5f2a6507e3d06708f3be44aba7e0fba7a3e43be4953260173d` | `main.tex` (32,350 B) | `ac74384c73d476e89e84e7b5c35a82160a96a6a518adac57bd79929ce339d934` | *identical* |

Build (literal, per paper):

```sh
cp papers/<slug>/submission/main.tex scratch/upreprint1/build/<slug>/main.tex
( cd scratch/upreprint1/build/<slug> && zip -X -q \
    "/home/zer0null/reserach extarctor/papers/<slug>/preprints/<slug>-preprints.zip" main.tex )
```

Verification (literal output):

```
$ unzip -Z1 papers/encoder-crossover-190/preprints/encoder-crossover-190-preprints.zip
main.tex
$ unzip -p <zip> main.tex | sha256sum   # == sha256sum papers/<slug>/submission/main.tex
2b5d049ed7b5368657c227f9efab42a6…   (and 9235ec53…, ac74384c… for the other two)
$ unzip -Z1 <zip> | grep -ci 'license\|metadata\|build_notes\|abstract_metadata\|scratch'
0        # ×3 — no workspace-internal file in any bundle
```

**Excluded on purpose:** `METADATA.md`, `BUILD_NOTES.md`, `ABSTRACT_METADATA.txt`, `ABSTRACT.txt`,
`LICENSE`, the old `submission/<slug>.tar.gz`, and every other workspace file. `ABSTRACT.txt` is not
shipped because the abstract is already inside `main.tex` and is pasted into the form; a loose copy could
only drift. Leak scan over each shipped `main.tex` — `grep -n 'scratch/\|orchestration/\|/home/\|UPREPRINT\|U8\.'`
returned **no match in all three** (`/home/` cannot appear either, since no bundle member is outside
`main.tex`).

---

## 6. Self-sufficiency proof — cold compile from the zip

Each archive was extracted into its own empty directory containing *only* what the zip carried, then
compiled with the project's Tectonic route (`scratch/utex1/bin/tectonic`, 0.15.0), with `HOME`,
`TECTONIC_CACHE_DIR` and `TMPDIR` redirected inside the workspace (they are read-only otherwise), and
**without** `-Z continue-on-errors`:

```sh
export TECTONIC_CACHE_DIR="$PWD/scratch/utex1/cache" \
       TMPDIR="$PWD/scratch/upreprint1/tmp" HOME="$PWD/scratch/upreprint1/home"
unzip -q papers/<slug>/preprints/<slug>-preprints.zip -d scratch/upreprint1/clean-<slug>/src
cd scratch/upreprint1/clean-<slug>/src
"/home/zer0null/reserach extarctor/scratch/utex1/bin/tectonic" -r 1 --keep-logs \
  -o "/home/zer0null/reserach extarctor/scratch/upreprint1/clean-<slug>/out" main.tex
```

| paper | extraction | exit code | `Undefined control sequence` | `!` lines | PDF | pages |
|---|---|---|---|---|---|---|
| #3 | `main.tex` only | **0** | **0** | **0** | 188,793 B | 25 |
| #2 | `main.tex` only | **0** | **0** | **0** | 107,906 B | 13 |
| #7 | `main.tex` only | **0** | **0** | **0** | 91,553 B | 10 |

Page counts equal the shipped PDFs' (25/13/10). All three build **clean**: no `continue-on-errors` was
needed and none was used. This also corrects `strategy/LATEX_TOOLCHAIN.md`, which records
"`-Z continue-on-errors` is **required** because `main.tex` contains 2 undefined macros" — on the current
`main.tex` (sha256 `2b5d049e…`) there are zero undefined control sequences and the strict build succeeds.

---

## 7. The licence situation — two objects, two licences, no conflict

- **What Preprints.org does to the posted text**, `https://www.preprints.org/about`: "All preprints are
  posted with a Creative Commons CC BY 4.0 license, ensuring that authors retain copyright and receive
  credit for their work while allowing anyone to read and use their work." No alternative is offered at
  submission, so posting the manuscript is consenting to CC BY 4.0 **for the posted preprint**.
- **What the released artifacts carry**, `papers/encoder-crossover-190/released/encoder-crossover-190-released/LICENSE:5`:
  `# PolyForm Noncommercial License 1.0.0`, with `Required Notice: Copyright 2026 Aswin-Ram-K` — i.e. the
  code/data release is noncommercial, and the Zenodo record at concept DOI `10.5281/zenodo.23463944`
  distributes **that** tree.

**Verdict: not a conflict — two different objects under two different licences.** The paper is a
manuscript (text, equations, tables of measurements); the released tree is software and data. CC BY 4.0
attaches to the former because that is the price of posting on this server; PolyForm 1.0.0 attaches to
the latter because that is what the deposit's `LICENSE` says. A reader of the preprint may reuse the
*text* with attribution and may not use the *code* commercially; nothing in either licence purports to
relicense the other's object.

**Why the usual escape hatch is not needed here.** The conflict would be real if the manuscript
reproduced PolyForm-licensed source verbatim — then CC BY on the manuscript would purport to relicense
that code. It does not: `grep -c 'begin{verbatim}\|begin{lstlisting}\|begin{minted}'` → **0** and
`grep -c '\verb'` → **0** in all three `main.tex`. There are no code listings to relicense. The papers
*describe* the artifacts and cite the deposit; description is not relicensing.

**One thing the author should keep straight in his own head, and it costs nothing:** after posting, the
preprint *text* is CC BY 4.0 forever (preprints "cannot be completely removed once posted", same page),
while the artifact tree stays PolyForm NC. Do not describe the paper as "noncommercial" anywhere, and do
not describe the code as "CC BY" anywhere — the two DOI-bearing objects now carry different terms and a
downstream reader will check both.

---

## 8. The author's ordered steps (nothing here is performed by this unit)

1. **Account.** `https://www.preprints.org/` → *Log In* → register a one-step account if none exists
   ("You will need to have an MDPI account and log in to submit."). An ORCID may be linked during
   submission; it is encouraged, not required.
2. **Start a submission** with the **Submit** button (top-right), choose **Article** as the type (all
   three are research articles; a "Conference Paper" is only for unpublished, DOI-less conference
   papers, which these are not).
3. **Subject area:** *Computer Science & Mathematics* (`https://www.preprints.org/subject/browse/computer-science-and-mathematics`)
   — the closest of the eleven fields on the site. A finer sub-category, if the form asks for one, is the
   author's call.
4. **Upload the archive** for that paper:
   - `papers/encoder-crossover-190/preprints/encoder-crossover-190-preprints.zip`
   - `papers/gated-read-batching/preprints/gated-read-batching-preprints.zip`
   - `papers/replay-record-not-decision/preprints/replay-record-not-decision-preprints.zip`
   One paper per submission; three submissions.
5. **Fill the metadata form** — title, abstract, keywords, and for **every** author: name, affiliation,
   email. The form is where #2 and #7's missing contact/affiliation data must be supplied (page 1 cannot
   supply it, §4). Keywords must be invented here if not taken from `submission/ABSTRACT_METADATA.txt`:
   the form requires them whether or not the PDF shows them.
6. **Declare conflicts of interest** in the form; the manuscript statement is still expected before the
   reference list (§1.5) and is currently absent from all three (§4.4).
7. **Licence:** accept CC BY 4.0. There is no alternative to choose — posting *is* the acceptance.
8. **Data availability:** enter **that paper's own** concept DOI in its own submission — never one
   paper's DOI in another's form:

   | Paper | Concept DOI to enter | Its own latest Zenodo record |
   |---|---|---|
   | `encoder-crossover-190` (#3) | `10.5281/zenodo.23463944` | v3 = record `23482311` |
   | `replay-record-not-decision` (#7) | `10.5281/zenodo.23482511` | v2 = record `23483304` |
   | `gated-read-batching` (#2) | `10.5281/zenodo.23483314` | v2 = record `23485733` |

   The three deposits are independent: #2's own DOI is `10.5281/zenodo.23483314` and #7's own is
   `10.5281/zenodo.23482511`. Only #3's manuscript text cites `10.5281/zenodo.23463944`, because that is
   #3's own deposit — #2 and #7 do not cite it, and must not.
   > **Superseded 2026-10-19:** the earlier wording of this step read: "point the form (and, for #2 and
   > #7, ideally the text) at the published deposit `10.5281/zenodo.23463944`; #3 already cites it, #2 and
   > #7 do not." That was written before the #2 and #7 deposits existed and wrongly aimed all three
   > submissions at the encoder's deposit. Preserved here as history; the table above is the instruction.
9. **Submit**, then expect screening ("All preprints undergo a short screening before being uploaded
   online. It usually takes less than 24 hours"), after which a Crossref DOI is minted and the preprint
   goes live. Co-authors receive a confirmation email on submission — there are none here, so nothing to
   coordinate.

**Do step 5 before step 4 if the form allows it** — the missing keywords/affiliation data is the one
defect that could send a submission back, and it is cheaper to fix in a re-issued bundle than after
screening.

---

## 9. What is **not** verifiable from here

Anything requiring the account, the session, or a fee. Specifically:

- Whether the submission form actually offers a licence choice, and whether it forces CC BY 4.0
  (the public pages say it is applied at posting; the form's own behaviour is unobserved).
- The exact upload field, size limit, and accepted archive extensions (`.zip` is named on the page; the
  widget is behind login).
- The full subject-area tree below the eleven top-level fields, and whether a paper may be filed under
  more than one.
- Whether screening rejects a manuscript whose page 1 lacks keywords/affiliations even when the form
  carries them — the rule is stated (§1.2) but its enforcement is editorial and unobservable.
- Whether an institutional email is *required* ("recommended" on the page) and whether a Gmail address
  triggers a query. The papers use a Gmail address.
- Turnaround time beyond "less than 24 hours in most cases", the DOI suffix that will be assigned, and
  whether Preprints.org will cross-link the Zenodo deposit automatically.
- Whether the site's own LaTeX template (offered at a download link we did not fetch) adds anything the
  strict build here already lacks. Our build is clean, so this is cosmetic.
- Anything about the author's account state: prior submissions, co-author confirmations, profile
  completeness, ORCID linkage.


---

## Update 2026-10-19 (UPREPRINT2)

- **Byline:** the author decided papers #2 and #7 carry the SAME three lines as #3 (name / `Independent researcher` / `aswinram.k.1603@gmail.com`). Applied as per-package data in `tools/package/md2tex.py` (`PACKAGES[*]["author_line"]`); `tests/test_md2tex.py` now pins every package's byline exactly (red when the email is dropped from a registry entry).
- **Conflicts of Interest:** verified against https://www.preprints.org/instructions-for-authors - "The corresponding author must include a summary statement in the manuscript in a separate section “Conflicts of Interest” placed just before the reference list." The existing `## Competing interests` section was renamed (heading and mirror label only; the declaration text is unchanged) and repositioned immediately before the reference list in all three papers. No second declaration was added.
- **Keywords:** the card said each paper records keywords in `submission/METADATA.md`; that is FALSE. Only paper #3 has a recorded set (the 8 content keywords in `strategy/DEPOSIT_METADATA.md` §2, identical to the Zenodo form list in §1). Those 8 were added to page 1 via the registry. Papers #2 and #7 have **no recorded keyword set anywhere in the workspace**, so none was added (inventing keywords is barred by the unit card). Follow-up: the author must supply keywords for #2 and #7.


---

## Update 2026-10-19 (UPREPRINT3) — the two missing keyword sets supplied by the author

**Supersedes the "Follow-up: the author must supply keywords for #2 and #7" line above.** The author approved the two sets, in order; they were added as per-package `keywords=` values in `tools/package/md2tex.py` `PACKAGES` (the single source of truth), emitted immediately after `\maketitle`, which is the same mechanism paper #3 already used:

- `replay-record-not-decision`: `replay determinism, LLM decision replication, binding divergence, record versus decision, option-index encoding, agent trace reproducibility`
- `gated-read-batching`: `tool-call gating, batched decisions, read-gate classification, binary gate decisions, token exposure, low-effort prompting`

Both sets are on **page 1** of the compiled PDF (extracted with `pdftotext -f 1 -l 1`): the keyword line appears on page 1 and not on page 2 for either paper. `tests/test_md2tex.py::test_keywords_pinned_per_package` pins every package's set literally and in order (red when a keyword is reordered, red when one is dropped); the full suite is `8 passed`.

Regenerated with `python3 tools/package/md2tex.py --package <slug>` (two runs byte-identical), compiled with `scratch/utex1/bin/tectonic -r 1 --keep-logs -o <out> main.tex` (no `-Z`): exit 0, 0 `Undefined control sequence`, 0 `!` lines; #7 13 pages, #2 10 pages. The only change in each `main.tex` is the two-line keyword insertion; no numeric literal moved.

| paper | zip | bytes | sha256(zip) |
|---|---|---|---|
| #7 `gated-read-batching` | `gated-read-batching-preprints.zip` | 14,094 | `feecb7f7879766bf9ecedaa03bbae3b8817eaab47513d092e42052a4127b74f5` |
| #2 `replay-record-not-decision` | `replay-record-not-decision-preprints.zip` | 10,372 | `251af28e2141da640abf4b8dc29d821c6ceeec60f0e942936943a15cad14c15a` |

Each archive has exactly one member (`main.tex`) whose extracted bytes `cmp` equal `submission/main.tex`, and each was compiled from an extraction of its own zip in a clean scratch directory. Paper #3 is untouched: `encoder-crossover-190-preprints.zip` is still **28,712 B / sha256 `705bc498c7c7eb7cf1e53cae8f49fb8656787694c39dbc7c5f4064f9aa7caf7f`**. Note: the `submission/*.tar.gz` containers were **not** regenerated by this unit (out of scope) and are now stale relative to `submission/main.tex`.

---

## Update 2026-10-19 (UDOCSYNC1) — §5 digests re-established against the live bundles

§5's table was measured before the 2026-10-19 bundle refresh and quoted containers that no longer exist
on disk. Every value in it is superseded by the re-measurement below (taken from disk 2026-10-19); the
superseded figures are retained above as dated history.

| paper | zip | bytes | sha256(zip) | md5(zip) | member | sha256(member) |
|---|---|---|---|---|---|---|
| #3 `encoder-crossover-190` | `encoder-crossover-190-preprints.zip` | 28,712 | `705bc498c7c7eb7cf1e53cae8f49fb8656787694c39dbc7c5f4064f9aa7caf7f` | `5c483d8cd71bfbfa12596725a2c58f69` | `main.tex` (84,967 B) | `2b5d049ed7b5368657c227f9efab42a64d1a70304b34813401bf128297ad33cc` |
| #2 `gated-read-batching` | `gated-read-batching-preprints.zip` | 14,094 | `feecb7f7879766bf9ecedaa03bbae3b8817eaab47513d092e42052a4127b74f5` | `09f535a4d84c439cc801f5097994c9c4` | `main.tex` (39,351 B) | `9235ec53e581edf0884e7ca9d85e6be696a148d9599f0465af02f7927f635277` |
| #7 `replay-record-not-decision` | `replay-record-not-decision-preprints.zip` | 11,379 | `63044528d554ac5f2a6507e3d06708f3be44aba7e0fba7a3e43be4953260173d` | `b79732d135650ca176f30bb62a64f764` | `main.tex` (32,350 B) | `ac74384c73d476e89e84e7b5c35a82160a96a6a518adac57bd79929ce339d934` |

- Superseded by this table (kept above as history): §5's `28,640` / `68141633…` / member `84,747 B` /
  `419ac0cc…`; `14,001` / `ba20ccd3…` / member `39,133 B` / `d321f8c3…`; `10,251` / `eb344f3e…` /
  member `28,604 B` / `2059e12b…`. Also superseded: the `Update 2026-10-19 (UPREPRINT3)` replay row
  `10,372` / `251af28e…` — the replay zip was rebuilt again after that update.
- The filenames in §8 step 4 are unchanged and still name files that exist; the digests beside them are now
  the live ones. This unit did not rebuild any container.
- §6's cold-compile results were produced from the *superseded* zip members (the `main.tex` revisions
  above). They were not re-run against the current bundles; the current zips were not compiled by this unit.

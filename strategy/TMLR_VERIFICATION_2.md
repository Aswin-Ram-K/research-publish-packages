# TMLR_VERIFICATION_2 — independent verification of UTMLR2

**Verifier:** VUTMLR2 (not the author of the artifact; author's report read only as a list of claims).
**Artifact under test:** `scratch/utmlr2/tmlr/main.tex` + `tmlr.sty`/`tmlr.bst`/`fancyhdr.sty`, compiled `main.pdf`.
**Verdict: `pass`** — every material claim reproduced; three recorded corrections, none of which break anonymity,
TMLR compliance, or the numeric integrity of the paper.

Method: digests, counts and multisets recomputed from disk with `sha256sum`, Python `re`/`Counter`, `wc -l`,
`cmp`, `pdfinfo`, `pdftotext`, plus a fresh Tectonic compile of a **copy** in `scratch/vutmlr2/build/`.
`scratch/utmlr2/**`, `scratch/utmlr1/**` and `papers/**` were never written to.

## Claim-by-claim

| # | Claim | Verdict |
|---|---|---|
| 1 | `main.tex` sha256 `16a19a2d…6b7f`, 476 lines | **pass on digest; line count corrected to 475** |
| 2 | `tmlr.sty` sha256 `816214ff…0002`, zip 694659 B sha `48f9f972…4f92d`, from the JmlrOrg zip URL | **pass — live-confirmed** |
| 3 | Compile clean: exit 0, 0 undefined, 0 `!`, 0 `error:`, 16-page PDF | **pass — re-run independently** |
| 4 | LLM footnote really on page 1, naming no harness/repo/host/model/date | **pass** |
| 5 | No author-identifying string survives | **pass on anonymity; "internal-path 0" overstated** |
| 6 | Numeric guard moved honestly (env 1198→1086, refs 1146→1035, 56 removed, 0 added); claim values and cite structure unchanged | **pass** |
| 7 | Dated correction in `strategy/AI_DISCLOSURE_PRECEDENT.md` quoting TMLR's FAQ, original kept as history | **pass** |

## Evidence

**C1.** `sha256(scratch/utmlr2/tmlr/main.tex)` = `16a19a2d7e3fccdf9acef8d9a9affd328cf38ae9fb252be5f81edc24790e6b7f`, 83644 B.
`wc -l` = 475; `splitlines()` = 475; file ends with `\n`. The claimed 476 arises only from `split("\n")`
counting the phantom element after the trailing newline. (Same convention error on the source: claimed 468,
actual 467, sha `370472969027759c15d3efd980a2b6246c76aecdd130176f37c98ab9733bbcc9`.)

**C2.** `tmlr.sty` sha `816214ff5919aa457b6b443bee52b15d9561421417b7f8a50cc84651519f0002`. Fetching
`https://github.com/JmlrOrg/tmlr-style-file/archive/refs/heads/main.zip` returned http=200 via
`https://codeload.github.com/JmlrOrg/tmlr-style-file/zip/refs/heads/main`, 694659 B, sha
`48f9f972cc812d2cfc8032a78578c2f5d8939b92fbd4f61095e8cbeb3394f92d`, **byte-identical to the on-disk zip**
(`cmp -s`); its `tmlr.bst` = `306fd454cf40771bee01293eeb98d2c1cd5f4e11ed0cd7296b335f354fc45206`.

**C3.** `TECTONIC_CACHE_DIR`/`TMPDIR`/`HOME` exported into the workspace, `tectonic -X compile main.tex`
(no `-Z continue-on-errors`): `RC=0`; `Undefined control sequence` 0; `^!` 0; `error:` 0; `pdfinfo` **Pages 16**,
612×792 letter; PDF 178203 B. Rebuilt sha `70f8fa35…59d0c0` ≠ on-disk `02c7a3c5…e2ae8`; `pdftotext` of the two
PDFs is identical, so the difference is non-semantic. The earlier note that *only* the trailer `/ID` differs is
**not reproduced**: `cmp -l` reports 3501 differing bytes at offsets 173725–177283 (Info + XMP metadata dates).

**C4.** `pdftotext -f 1 -l 1` on the rebuilt PDF: "Use of AI tools. Large language model (LLM) systems were used
to assist in designing and implementing the analysis and the experiment, and to help draft and edit this
manuscript…" — no harness, repository, host, model or date. Page 1 also carries tmlr.sty's
"Under review as submission to TMLR" and "Anonymous authors / Paper under double-blind review".

**C5.** Zero hits for: author name (`Aswin|Kalugasala|Moorthy|Ram-K`), `ORCID`, `0009-0009-9505-3546`,
`github|GitHub|GitLab`, `research-publish-packages`, e-mail regex, `zenodo`, `DECIDER_STACK_DECISION`,
40/64-hex commit ids, `ad301ae`/`907fa39`, `GX10|GB10|gx10-163b`, `docs/`, `evals/`, `harness/`, `strategy/`,
`tools/typed-channel/`, `DECIDER_TIER`, ISO dates, dated personal-decision markers.
Deliberate hits judged benign: `mimo-v2.6-flash` at `scratch/utmlr2/tmlr/main.tex:201` and `:325` (public model
id), `the target fixture` at `:297` (ordinary ML noun), `GPT-4` at `:93` (citation context), 13 public citation
URLs, published-work DOIs at `:85`/`:92`/`:102`.
Residual, **not** author-identifying but contradicting "internal-path 0": `REPORT.md:189` — also in the abstract
on **page 1** (`scratch/utmlr2/tmlr/main.tex:27`) — plus `REPORT.md:104`/`:85`/`:191`/`:315`/`:405` and
`REFERENCES.bib` at `:98`/`:458`, and ~25 lines naming the submission's own supplementary files
(`analysis.json`, `results/baselines.json`, `preregistration/EXP12-typed-channel-comparison-prereg.md`,
`verify/recompute-claims.py`, …), which the supplement section documents on purpose.

**C6.** env-strip (numbers outside `thebibliography`): 1198→1086 total, 340→304 distinct, 56 distinct removed,
0 added. refs-strip (cut at `\section*{References}`): 1146→1035, 340→304, 56 removed, 0 added. Literal-occurrence
counts unchanged: `0.6789` 25→25, `0.3474` 27→27, `0.4526` 13→13, `0.6684` 19→19, `4.167` 7→7, `0.33` 26→26,
`0.32` 25→25, `152,000` 4→4. Structure: 23 `\cite` calls, 13 distinct keys, 13 `\bibitem`, 0 unresolved, 0
uncited. (A token-regex convention counts 23/12 for `0.6789`/`0.4526` because values embedded in longer numerals
such as `0.6789473684210526` are single tokens; unchanged-ness holds either way.)

**C7.** `strategy/AI_DISCLOSURE_PRECEDENT.md` (222 lines): "## Correction (appended 2026-10-17)" at `:208`,
TMLR FAQ quoted at `:214-216` ("…footnote on the first page."), the superseded claim "TMLR | Silent on
disclosure" still present at `:186` with `:211-212` recording that the original is kept as history.

## Red→green

Copy `scratch/vutmlr2/red/main_red.tex` = real `main.tex` plus injected `\texttt{docs/DECIDER\_STACK\_DECISION.md}`
and commit id `ad301ae`. The residue guard runs:
- real file: commit-id hits **0 → PASS**;
- red copy: commit-id hits **1 → FAIL**.

The internal-path pattern is not a clean red→green because the real file already carries supplementary file names;
the commit-id guard isolates the fix correctly.

## Corrections to the author's report

1. `main.tex` is **475** lines (476 only under `split("\n")`); source is 467, not 468.
2. `"internal-path 0"` is overstated — `REPORT.md:NNN` and `REFERENCES.bib` remain (none identifying).
3. The previous verifier's "only the `/ID` differs" does not reproduce — PDF metadata bytes differ too.

None of these invalidates the artifact: no author-identifying string survives, the compile is clean, the
first-page AI footnote is present, and the numeric re-baseline is honest.

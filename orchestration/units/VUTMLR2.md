# VUTMLR2 — independent verifier unit card (stub, appended as measured)

**Role:** independent verifier. Not the author. Re-derives every UTMLR2 claim from disk, not from the author's report.
**Artifact under test:** `scratch/utmlr2/tmlr/main.tex` + `tmlr.sty` (TMLR-compliant anonymised variant).
**Source of record (read as *claims*, never as evidence):** `strategy/TMLR_SUBMISSION.md`,
`orchestration/handoffs/UTMLR2.json`, `scratch/utmlr2/evidence.json`, `orchestration/units/UTMLR2.md`.

**Hard bound:** 20 tool calls. Stub-first so a mid-run death stays readable.
**Write paths (only):** `scratch/vutmlr2/**`, `strategy/TMLR_VERIFICATION_2.md`,
`orchestration/units/VUTMLR2.md`, `orchestration/handoffs/VUTMLR2.json`.
**Read-only:** `scratch/utmlr2/**`, `scratch/utmlr1/**`, `papers/**` — copies only, under `scratch/vutmlr2/`.

## Check log (appended in measurement order)

All measurements below were made by VUTMLR2 from disk; the author's report was read only as a list of claims.
Copies live under `scratch/vutmlr2/` (build, red, net). Nothing under `scratch/utmlr2/**`, `scratch/utmlr1/**`
or `papers/**` was modified.

### C1 — artifact identity: PASS with one correction
- `sha256(scratch/utmlr2/tmlr/main.tex)` = `16a19a2d7e3fccdf9acef8d9a9affd328cf38ae9fb252be5f81edc24790e6b7f` — matches.
- 83644 bytes; `wc -l` = 475, `splitlines()` = 475, file ends with `\n`.
- **Claimed 476 lines ⇒ actual 475.** The 476 figure is only obtainable by `text.split("\n")`, which counts a
  phantom empty element after the final newline. Same off-by-one applies to the source file (claimed 468,
  actual 467, sha `370472969027759c15d3efd980a2b6246c76aecdd130176f37c98ab9733bbcc9`, 84206 B).

### C2 — style file identity: PASS (live-confirmed)
- `sha256(scratch/utmlr2/tmlr/tmlr.sty)` = `816214ff5919aa457b6b443bee52b15d9561421417b7f8a50cc84651519f0002` — matches.
- On-disk zip `scratch/utmlr2/download/tmlr-style-file-main.zip` = 694659 B,
  sha `48f9f972cc812d2cfc8032a78578c2f5d8939b92fbd4f61095e8cbeb3394f92d` — matches.
- Live fetch of `https://github.com/JmlrOrg/tmlr-style-file/archive/refs/heads/main.zip` returned http=200 to
  `https://codeload.github.com/JmlrOrg/tmlr-style-file/zip/refs/heads/main`, 694659 B, **byte-identical**
  (`cmp -s`) to the on-disk zip, same sha; `tmlr.bst` from that zip = `306fd454cf40771bee01293eeb98d2c1cd5f4e11ed0cd7296b335f354fc45206`.

### C3 — clean compile: PASS (re-run by me)
- Copy at `scratch/vutmlr2/build/`; `TECTONIC_CACHE_DIR`/`TMPDIR`/`HOME` exported into the workspace;
  `scratch/utex1/bin/tectonic -X compile main.tex`, **no** `-Z continue-on-errors`.
- `RC=0`; `Undefined control sequence` 0; `^!` 0; `error:` 0; `pdfinfo` Pages **16**, 612×792 letter; 178203 B.
- Rebuilt PDF sha `70f8fa357a4f7d1850a075fa39fba04f37fda033b9d27d1acfa78a2bf659d0c0` vs on-disk
  `02c7a3c5edd9c13d4c11705d07335bf334d847a94aa429a728ca6d17aaae2ae8` — differs, as expected per-run.
- `pdftotext` of both PDFs diff clean ⇒ **text identical**. Correction to the earlier note: `cmp -l` shows
  **3501** differing bytes at offsets 173725–177283, i.e. metadata/trailer (Info + XMP dates), **not only `/ID`**.

### C4 — page-1 footnote: PASS
- `pdftotext -f 1 -l 1` on **my** rebuilt PDF contains: "Use of AI tools. Large language model (LLM) systems
  were used to assist in designing and implementing the analysis and the experiment, and to help draft and edit
  this manuscript..." — no harness, repository, host, model or date named. Page 1 also carries tmlr.sty's
  "Under review as submission to TMLR" and "Anonymous authors / Paper under double-blind review".

### C5 — residue sweep: no author-identifying string survives; the "internal-path 0" sub-claim is OVERSTATED
- Zero hits: `Aswin|Kalugasala|Moorthy|Ram-K`, `ORCID`, `0009-0009-9505-3546`, `github|GitHub|GitLab`,
  `research-publish-packages`, email regex, `zenodo`, `DECIDER_STACK_DECISION`, 40/64-hex, `ad301ae`/`907fa39`,
  `GX10|GB10|gx10-163b`, `docs/`, `evals/`, `harness/`, `strategy/`, `tools/typed-channel/`, `DECIDER_TIER`,
  ISO dates (`\d{4}-\d{2}-\d{2}`), `(author decision`.
- Deliberate hits, judged benign: `mimo-v2.6-flash` at `scratch/utmlr2/tmlr/main.tex:201` and `:325` (public
  model id); `the target fixture` at `:297` (ordinary ML noun); `GPT-4` at `:93` (citation context); 13 public
  citation URLs; published-work DOIs at `:85`, `:92`, `:102`.
- **Real residual hits:** `REPORT.md:189` (also on **page 1**, abstract line, in `scratch/utmlr2/tmlr/main.tex:27`),
  and `REPORT.md:104`, `:85`, `:191`/`:315`, `:405`; `REFERENCES.bib` at `:98`, `:458`. Plus ~25 lines of
  supplementary-package file names (`analysis.json`, `results/baselines.json`, `preregistration/EXP12-...md`,
  `verify/recompute-claims.py`, …) which the paper legitimately documents as its own 29-file supplement. None
  names the author or reveals the host — but "internal-path 0" is not literally true.

### C6 — numeric guard: PASS (claimed values reproduce under the substring convention)
- env-strip 1198→1086 total, 340→304 distinct, 56 distinct removed, 0 added, `identical=False` — reproduced.
- refs-strip 1146→1035 total, 340→304 distinct, 56 removed, 0 added — reproduced.
- Claim-value occurrences (literal substring, the author's convention) all unchanged before→after:
  `0.6789` 25→25, `0.3474` 27→27, `0.4526` 13→13, `0.6684` 19→19, `4.167` 7→7, `0.33` 26→26, `0.32` 25→25,
  `152,000` 4→4. (The token-regex `[0-9]+(?:\.[0-9]+)?` counts fewer — e.g. 23 and 12 — because values such as
  `0.6789473684210526` are single tokens; the unchanged-ness holds under both conventions.)
- Structure: 23 `\cite` calls, 13 distinct keys, 13 `\bibitem`, 0 unresolved, 0 uncited — reproduced.

### C7 — AI_DISCLOSURE_PRECEDENT.md correction: PASS
- `strategy/AI_DISCLOSURE_PRECEDENT.md` is 222 lines; §"Correction (appended 2026-10-17)" at `:208`; FAQ quoted
  at `:214-216` ("...footnote on the first page."); original wrong claim ("TMLR | Silent on disclosure") still at
  `:186` with `:211-212` stating the original is left in place as history.

### Red→green (required)
- Injected `\texttt{docs/DECIDER\_STACK\_DECISION.md}` and commit id `ad301ae` into
  `scratch/vutmlr2/red/main_red.tex` (a copy; real artifact untouched).
- commit-sha sweep: REAL file **0 hits → PASS**; RED copy **1 hit → FAIL**. (Internal-path sweep is not a clean
  red→green because the real file already carries supplementary file names; the commit-id guard is the clean one.)

### Verdict
`pass` — artifact identity, style file, clean 16-page compile, page-1 footnote, numeric re-baseline and the
disclosure correction all reproduce. Corrections recorded: line count 475 (not 476); "internal-path 0"
overstated (`REPORT.md:NNN`, `REFERENCES.bib` remain, none identifying); the earlier verifier's "only the /ID
differs" does not reproduce (metadata bytes also differ).

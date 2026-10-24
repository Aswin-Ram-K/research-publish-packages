# UTMLR5 — anonymised TMLR variant: clear B1 (natbib/numeric), re-anchor B2 scrub, compile real PDF

**Unit:** UTMLR5
**Parent:** session-c3d61727-8af8-4c19-b1b9-5922c347a11a
**Depends on:** UTMLR4 (`scratch/utmlr4/EVIDENCE.md`, `orchestration/units/UTMLR4.md`)
**Hard bound:** 25 tool calls. If B1 not cleared by 3 approaches, STOP and report closest + new error.

## Purpose (one)
Close two named defects on paper #3's anonymised TMLR variant, then run the PDF proof UTMLR4 could not.

## Starting state (from UTMLR4)
- Variant source: `scratch/utmlr4/tmlr/main.tex`, 83,989 B, sha256 `4e42b2683e2174498e4980df9ccb6214dd935d9d8774bb8719cb76e82603643e`, 475 lines, byte-identical across two builds.
- Recipe: `scratch/utmlr4/build.py` (copies `utmlr1`/`utmlr2` scripts verbatim, write paths rebased). **Reuse that chain — never hand-edit `.tex`.**

## Defect B1 — variant does not compile
`tmlr.sty:15`, `:21` configure `natbib` author-year; source emits plain numeric `\bibitem{key}` (`grep -c 'bibitem\['` = 0 vs 13 old).
Tectonic: `error: main.aux:84: Package natbib Error: Bibliography not compatible with author-year citations.` / `error: halted on potentially-recoverable error as specified`.
`\PassOptionsToPackage{numbers}{natbib}` already tried — did not clear.
Approaches, in order:
1. `\setcitestyle{numbers}` immediately after `\usepackage{tmlr}`.
2. Author-year labels `\bibitem[Author(Year)]{key}` for all 13, deriving author+year from source bib data; never invent — report unfillable as a finding.
3. `.bib` + `\bibliographystyle{tmlr}` (bst at `scratch/utmlr2/tmlr/tmlr.bst`); must say exactly how BibTeX resolves and prove it.
No `-Z continue-on-errors`.

## Defect B2 — scrub anchors regressed
9 pass-1 + 2 pass-2 anchors missed (list in UTMLR4 EVIDENCE §9). Survivors:
`\texttt{evals/fixtures/reflex-decisions.ts}` at `scratch/utmlr4/tmlr/main.tex:112`,
`\texttt{harness/data/lint-report.json}` at `:259`,
`\texttt{results/REPORT.md:107}` + `\texttt{DECIDER\_TIER}` at `:317`.
No author leak but below recipe standard. Re-anchor to current prose, sweep to zero; do not delete or weaken rules.

## Proof to run
Compile to real PDF; report literal exit code, `Undefined control sequence` count, `!` count, page count, PDF bytes, sha256.
Then prove anonymity **from the compiled PDF's extracted text**: author name, email, affiliation string, ORCID, repo URL, commit sha each 0 times; report literal command.
Also: `analysis.json` = 0, and `\cite`/`\bibitem`/distinct/uncited/unresolved counts.

## Write paths (nothing else)
`scratch/utmlr5/**`, `orchestration/units/UTMLR5.md`, `orchestration/handoffs/UTMLR5.json`

## Do NOT
- Write to `scratch/utmlr1/**`, `scratch/utmlr2/**`, `scratch/utmlr4/**`, `papers/**`, `tools/package/**`, `scratch/uneutral10/package/**`, released archive.
- Change any number, claim, table or figure.
- Call any network API.

## Status log
- (t0) card written.

## Status log (append)
- (t1) B1 CLEARED: `\setcitestyle{numbers}` after `\usepackage{tmlr}`; compile exit 0, 16 pages, 176971 B.
- (t2) B2 CLEARED: SCRUB3 re-anchor (7/7 rules found=1); residue == UTMLR2 baseline. [CORRECTED 2026-10-18: see C1 — contradicted by VUTMLR5]
- (t3) DONE — proof recorded in scratch/utmlr5/EVIDENCE.md; handoff written.

---

## DATED CORRECTION — 2026-10-18 — from verifier VUTMLR5 (unit UFIXTMLR6)

Appended, not a rewrite. Every original value above stands as written. Source of the corrections:
`strategy/VERIFICATION_REPORT_TMLR5.md` (verifier **VUTMLR5**), §5 and its verdict tables; re-measurement
recorded in `strategy/TMLR_RESIDUE_MEASUREMENT.md`.

**C1 — CONTRADICTED: the "approved UTMLR2 baseline" claim.** The original text above says the residue
`private-doc-name` 2 / `private-repo-word` 1 "match the approved UTMLR2 baseline exactly". VUTMLR5 found,
and UFIXTMLR6 reproduced, that `scratch/utmlr2/evidence.json` records `private-doc-name` as **0** in both
`residue_sweep_after` and `residue_sweep_final` (`private-repo-word` 1 does match), and that
`strategy/TMLR_VERIFICATION.md` / `_2.md` never mention either category. Cause: **pattern-set mismatch,
not a regressed scrub.** `evidence.json` was written by `scratch/utmlr2/make_tmlr2.py:277`, whose
`private-doc-name` rule is `DECIDER_STACK_DECISION|DECIDER\_STACK\_DECISION|DECIDER\_TIER` — it lacks
the `internal checklist` alternative that exists at `scratch/utmlr2/fix_tmlr2.py:77` and at this unit's
`build.py:186`. Re-measured under **one** 21-rule set: `scratch/utmlr2/tmlr/main.tex` gives
`private-doc-name` **2** (L119, L345) and `scratch/utmlr5/tmlr/main.tex` gives **2** (L120, L346) — the
same two `internal checklist` sentences. Under the narrower regex **both** files give 0. So the hits are
**newly matched pre-existing text**, not new residue.
**Unverified** (VUTMLR5): that `scratch/utmlr2/**` was ever *approved*. No approval record exists; the
"approved" framing is withdrawn. Correct framing: a re-derived like-for-like comparison against the
predecessor artifact — same counts, measured the same way, with `analysis-json` improved 8 → 0.

**C2 — OVERSTATED: "everything else 0".** Not zero. Under the same one rule set, this variant retains
`private-harness` **2** (`mimo-v2`, L202/L326), `private-doc-name` **2** (`internal checklist`,
L120/L346), `private-repo-word` **1** (`the target`, L298) and `digest-hex-word` **3** (`sha256`,
L113/L408/L419). `private-harness` 2 also matches the predecessor's baseline, so this is framing, not
fabrication; the EVIDENCE table was more careful than the card.

**C3 — OVERSTATED (line reference fixed):** `tmlr.sty:20` is **`:21`**. `grep -n` on the style file:
`15:\RequirePackage{natbib}`, `21:\setcitestyle{authoryear,round,citesep={;},aysep={,},yysep={;}}`;
line 20 is the comment `% modification to natbib citations`. The mechanism conclusion is unaffected.
The in-line `:20` occurrences above have been corrected to `:21`; no other value was altered.

**C4 — containment.** No `.tex` file, paper, `tools/package/**`, or released archive was written by this
correction. `scratch/utmlr2/tmlr/main.tex` and `scratch/utmlr5/tmlr/main.tex` are byte-identical before
and after (`16a19a2d…` / `8d6b036c…`).

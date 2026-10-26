# TMLR anonymisation — independent verification (VTMLR1)

Verifier: **VTMLR1** (independent; did not author the artefact and did not use UTMLR1's report as
evidence). Artefact under test: `scratch/utmlr1/anonymous/main.tex`.
**Overall verdict: `pass`.** 6 of 7 claims fully re-derived; 1 `partial`; 0 contradicted.

## Results

| # | Claim | Verdict | Independent evidence |
|---|---|---|---|
| C1 | anon tex 84,206 B, sha `370472969027759c…73bbcc9` | **pass** | `stat` 84206; my `sha256sum` matches |
| C2 | exactly 2 lines differ (L12 byline, L435 contributions) | **pass** | difflib: exactly 2 replace opcodes, L12/L435; sha of source `8374fd28…` matches the pin |
| C3 | author-name hits 2→0; 0 for ORCID/`0009-0009-9505-3546`/github/Aswin-Ram-K/research-publish-packages/email/own preprint-or-DOI link | **pass** | full name src=2 (L12,L435) → anon=0; all listed patterns anon=0. Residual: own package + "Zenodo DOI pending" + dated personal decision at `:375`/`:407` (no DOI value or URL) |
| C4 | numeric-literal multiset identical, n=1198; `\cite`=23, `\bibitem`=13, distinct cited=13, uncited=0, unresolved=0 | **pass** | env-strip n=1198/1198 identical; refs-strip 1146/1146; boundary-aware regex 810/810; 23/23/13/13/13/0/0 identical |
| C5 | PDF sha `89d62e1d…23ccfa`, 25 pages, compile exit 0, 0 undefined, 0 `!` | **partial** | on-disk file *is* 184,983 B / `89d62e1d…` / 25 pages; my own `--only-cached` compile gave LITERAL_EXIT=0, undefined=0, `!`=0, 25 pages — but a **recompile gives sha `c7c49478…`** at the same 184,983 B with identical extracted text (70,858 chars), differing only in trailer `/ID`. The digest is per-run, not compile-reproducible |
| C6 | re-running `make_anon.py` reproduces output byte-for-byte | **pass** | verbatim script, OUT redirected only → same sha, `cmp` exit 0 |
| C7 | compile used 0 network calls (`--only-cached`, copied cache) | **pass as indicated** | 0 `download|connect|http|url|fetch` lines; `note: using only cached resource files`. Not strace'd |

**Red→green guard** (`scratch/vtmlr1/rg/anoncheck.py`): PASS on the real artefact (exit 0); FAIL on
a copy with the author name re-inserted (3 name hits, exit 1); FAIL on a copy with one byte appended
(exit 1). The check discriminates.

**Containment:** `papers/**` and `scratch/utmlr1/**` unmodified (mtimes 15:34 / 17:00 / 17:01, all
before this run at 17:03). All writes under `scratch/vtmlr1/**`. No network API. No credential,
token or ORCID value written anywhere.

## Carry-forward for any downstream card
- Do not assert a recompiled PDF's sha256 as reproducible; PDF `/ID` is random. Assert byte size,
  page count (25) and extracted text instead.
- "n = 1198" is tied to make_anon.py's `[0-9]+(?:\.[0-9]+)?` regex on env-stripped text. With
  `\section*{References}` truncation it is 1146; with a boundary-aware regex, 810. The invariant
  that survives all three is *multiset equality*, not the absolute n.
- The anonymisation is name/identifier-complete but not provenance-complete: the released-package
  paragraph and the dated licence decision remain (author's call).

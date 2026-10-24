# VTMLR1 — independent verification of UTMLR1 (anonymised TMLR variant)

**Verdict: `pass`** — 6 of 7 claims fully re-derived; claim 5 is `partial` (its PDF digest is
per-run, not compile-reproducible); claim 7 is strongly indicated but not trace-proven.
**No claim was contradicted.** Nothing under `papers/**` or `scratch/utmlr1/**` was written
(mtimes below all predate this run, which started 17:03).

Author of the artifact: UTMLR1. This verifier did not write it and did not use the author's report
as evidence — every number below was recomputed with independent commands.

## Claim-by-claim

### C1 — size and digest of the anonymised tex — **PASS**
```
84206 scratch/utmlr1/anonymous/main.tex
370472969027759c15d3efd980a2b6246c76aecdd130176f37c98ab9733bbcc9  scratch/utmlr1/anonymous/main.tex
```
84,206 B and sha256 `370472969027759c15d3efd980a2b6246c76aecdd130176f37c98ab9733bbcc9` — both match.

### C2 — exactly 2 changed lines, L12 and L435 — **PASS**
`difflib.SequenceMatcher` over the two files yields exactly two `replace` opcodes and no
insert/delete: `src12→anon12` and `src435→anon435`. (`diff | grep -c '^[<>]'` = 4 because a
one-line replacement emits a `<` and a `>` line.)
- L12: `\author{Aswin Ram Kalugasala Moorthy}` → `\author{Anonymous authors\\Paper under double-blind review}`
- L435: `\textbf{Author contributions.} This manuscript is by a single author, \textbf{Aswin Ram Kalugasala Moorthy}.` → `... by a single author. The research question ...`

Source pin re-confirmed: `papers/encoder-crossover-190/submission/main.tex` = 84,223 B, sha256
`8374fd28b1fc6c9faa3cb91884e30e097dbb1828361c418c431fdeec8e8461a1`.

### C3 — name hits 2 → 0, and 0 hits for the identifier list — **PASS (one residual noted)**
Full-name occurrences of `Aswin Ram Kalugasala Moorthy`: **src=2 (L12, L435) → anon=0**.
Anon=0 for: `ORCID`/`orcid`, `0009-0009-9505-3546`, `github`/`GitHub`/`gitlab`, `Aswin-Ram-K`,
`research-publish-packages`, any e-mail address. Both files: `ORCID`=0, `github`=0, e-mail=0.
**Residual (not a name or a link, so C3 is literally true):** the anon file still discloses the
author's own released package and a dated personal decision, at
`scratch/utmlr1/anonymous/main.tex:375` and `:407` — "the released reproducibility package",
"**Zenodo DOI pending** --- see Data and code availability", and "By the author's decision of
2026-10-15 the manuscripts in this series are released under CC BY 4.0". No DOI value or URL is
present. The 12 DOI-link and 18 arXiv hits are third-party citations, unchanged in count between
source and anon, and none carries the author's name.

### C4 — numbers did not move — **PASS**
Bibliography-stripped numeric multiset is identical before/after, and the n matches the claim once
the stated regex is used:
| strip method | regex | n src | n anon | identical |
|---|---|---|---|---|
| `\begin{thebibliography}…\end{thebibliography}` removed | `[0-9]+(?:\.[0-9]+)?` (make_anon.py's) | 1198 | 1198 | **yes** |
| `\section*{References}` truncated | same | 1146 | 1146 | **yes** |
| env-strip | boundary-aware `(?<![\w.])\d+(?:\.\d+)?(?![\w.])` | 810 | 810 | **yes** |

So "n = 1198" is **regex-dependent but correctly reported**: it holds for make_anon.py's
no-boundary digit regex on env-stripped text. The claim that matters — the multiset is unchanged —
holds under every regex tried.

Citation structure, identical before and after:
`\cite`=23, `\cite` keys total=23, `\bibitem`=13, distinct bibitems=13, distinct cited=13,
uncited=0, unresolved=0. Matches the claim exactly.

### C5 — PDF digest, 25 pages, exit 0, 0 errors — **PARTIAL**
Independently re-derived from my own compile of a *copy* (`scratch/vtmlr1/probe/main.tex`), cache
copied to `scratch/vtmlr1/probe/tectonic-cache`, `HOME`/`TECTONIC_CACHE_DIR`/`TMPDIR` exported into
the workspace, **no `-Z continue-on-errors`**:
```
./scratch/utex1/bin/tectonic --only-cached --keep-logs -o scratch/vtmlr1/probe/out scratch/vtmlr1/probe/main.tex
LITERAL_EXIT=0
grep -c "Undefined control sequence" main.log  -> 0
grep -c '^!' main.log                          -> 0
grep -c '!'  main.log                          -> 0
Output written on main.xdv (25 pages, 107576 bytes)
```
Confirmed: on-disk `scratch/utmlr1/out/main.pdf` **is** 184,983 B, sha256
`89d62e1d6d4c1932048f31c0bc3f39b532a48ded18fc94c68c061c931c23ccfa`, 25 pages; a compile does exit 0
with 0 undefined-control-sequence and 0 `!` lines.
**But the digest is not compile-reproducible.** My fresh compile of the same 84,206 B tex produced a
PDF of the **same size (184,983 B)**, the **byte-identical extracted text** (70,858 chars, 25 pages,
0 author-name hits, anonymous byline) — yet sha256 `c7c49478c631697db1b8599ccf74c5e1d07c87892c755cb117d376f584d66861`.
Only the PDF trailer `/ID` differs: mine `ad5065e8eecbd5288651aa7287f8b307` vs the reported
`25fe49cc4527c8d3332fd3eff08c0113`. So `89d62e1d…` identifies the file on disk, not the act of
compiling; restating it as the output of "a compile" is **overstated** as a reproducibility claim.

### C6 — make_anon.py reproduces the output byte-for-byte — **PASS**
A verbatim copy of `scratch/utmlr1/make_anon.py` with **only** the OUT path redirected
(`scratch/vtmlr1/repro2/make_anon_patched.py`) prints SRC `8374fd28…`/84223 B, writes
`370472969027759c15d3efd980a2b6246c76aecdd130176f37c98ab9733bbcc9`/84,206 B, and
`cmp` against the real artefact exits 0 — **byte-identical**.

### C7 — 0 network calls (`--only-cached` with copied cache) — **PASS as indicated; no packet trace**
stdout contains `note: using only cached resource files` and **0** lines matching
`download|connect|http|url|fetch`. `--only-cached` makes an uncached fetch fatal. I did **not**
strace the process, so "0 network calls" is strongly indicated, not trace-proven → recorded
`unverified` in the trace sense only.

## Red → green check (guard: sha+size+name-hits+anon-byline)
`scratch/vtmlr1/rg/anoncheck.py` asserts sha256 `370472969027759c…`, 84,206 B, 0 name hits, anon byline.
```
scratch/utmlr1/anonymous/main.tex        bytes=84206 sha=370472969027759c.. hits=0 byline=True  => PASS  (exit 0)
scratch/vtmlr1/rg/perturbed_name.tex     bytes=84184 sha=f62c276279ef7bf2.. hits=3 byline=False => FAIL  (exit 1)
scratch/vtmlr1/rg/perturbed_byte.tex     bytes=84207 sha=7c8579091fa018d4.. hits=0 byline=True  => FAIL  (exit 1)
```
So the guard PASSES on the real artefact and FAILS on a copy with the author name re-inserted and
on a copy with one byte appended — the check discriminates, it is not vacuously true.

## Containment
Unchanged (all mtimes predate this run, started 17:03):
```
2026-10-17 15:34:34  84223  papers/encoder-crossover-190/submission/main.tex
2026-10-17 17:00:42  84206  scratch/utmlr1/anonymous/main.tex
2026-10-17 17:00:42   4246  scratch/utmlr1/make_anon.py
2026-10-17 17:01:07 184983  scratch/utmlr1/out/main.pdf
```
All writes went to `scratch/vtmlr1/**`. No network API called. No credential, token or ORCID value
written into any file.

## Findings for the author (not blockers)
1. C5's PDF digest is per-run (random `/ID`); a future card must not treat a recompiled PDF's sha256
   as reproducible — verify the byte size + extracted text + page count instead.
2. C3 leaves a provenance disclosure at `:375`/`:407` (own package, "Zenodo DOI pending", dated
   2026-10-15 personal decision). Not a name or link; a judgement call for the author.

## Tool call log
1. stub written (`orchestration/units/VTMLR1.md`)
2. sizes + sha256 (anon/src/pdf) + difflib opcodes
3. pattern-hit sweep + numeric multiset + citation structure
4. `make_anon.py` / `verify.json` inspection
5. numeric regex-sensitivity (n=1198 vs 810/1146) + URL-hit localisation
6. `UTMLR1.json` compile recipe read; tectonic version
7. `make_anon.py` logic re-run on redirected OUT (byte-identical)
8. red→green guard: real PASS, 2 perturbations FAIL
9. independent `--only-cached` compile: LITERAL_EXIT=0
10. log error/page counts + pdf text comparison + `/ID` diff
11. verbatim patched `make_anon.py` run (`cmp` exit 0) + containment mtimes
12. `strategy/TMLR_VERIFICATION.md` written
13. read stub (fs policy)
14. this report written
15. `orchestration/handoffs/VTMLR1.json` + report-back (below)

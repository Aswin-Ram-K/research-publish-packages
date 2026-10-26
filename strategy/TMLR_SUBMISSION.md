# TMLR submission — anonymised variant (UTMLR1)

**Status:** built and proved. Not submitted. Nothing under `papers/**` was modified.
**Source (read-only):** `papers/encoder-crossover-190/submission/main.tex` — 84,223 B,
sha256 `8374fd28b1fc6c9faa3cb91884e30e097dbb1828361c418c431fdeec8e8461a1`.
**Deliverable:** `scratch/utmlr1/anonymous/main.tex` — 84,206 B,
sha256 `370472969027759c15d3efd980a2b6246c76aecdd130176f37c98ab9733bbcc9`.
**Anonymous PDF:** `scratch/utmlr1/out/main.pdf` — 184,983 B, 25 pages,
sha256 `89d62e1d6d4c1932048f31c0bc3f39b532a48ded18fc94c68c061c931c23ccfa`.

## 1. What was changed — exactly two lines

`diff -u` between the baseline copy and the anonymous copy shows **2 removed / 2 added lines** and
no other byte of difference (`scratch/utmlr1/anon.diff`):

| Line | Before | After |
|---|---|---|
| 12 | `\author{Aswin Ram Kalugasala Moorthy}` | `\author{Anonymous authors\\Paper under double-blind review}` |
| 435 | `…by a single author, \textbf{Aswin Ram Kalugasala Moorthy}. The research question…` | `…by a single author. The research question…` |

Reproducible transform: `scratch/utmlr1/make_anon.py` (asserts each replacement fires exactly once).

## 2. Identifier sweep — every hit, with file and line

Command: `python3 scratch/utmlr1/make_anon.py` (patterns + line numbers in `scratch/utmlr1/verify.json`).

| Pattern | Source `papers/encoder-crossover-190/submission/main.tex` | Anonymous `scratch/utmlr1/anonymous/main.tex` | Action |
|---|---|---|---|
| `Aswin` / `Kalugasala` / `Moorthy` (any case) | **2** — L12, L435 | **0** | both removed |
| `orcid` / `ORCID` / `0009-0009-9505-3546` | 0 | 0 | none present |
| `zenodo` / `Zenodo` | **2** — L375, L407 ("Zenodo DOI pending") | 2 | **kept**, see §5 |
| `github` / `GitHub` / `gitlab` | 0 | 0 | none present |
| `Aswin-Ram-K`, `research-publish-packages` | 0 | 0 | none present |
| email address | 0 | 0 | none present |
| `doi.org` / `DOI: 10.…` / `10.1007/…`, `10.18653/…` | 12 | 12 | **kept** — all are *third-party cited works* (Benayas 2024, GLiNER, Li 2025, …), none identifies this author |
| `arxiv.org/abs/…`, `arXiv:NNNN.NNNNN` | 18 | 18 | **kept** — all third-party citations to other papers |
| `https?://` URLs | 13 | 13 | **kept** — all third-party (arXiv, ACL Anthology, `simmering.dev`) |
| preprint word / preprint-own link | 0 | 0 | **no preprint of this paper is linked anywhere** |
| provenance tokens (§5.1) | L104, L391, L401, L410, L450, L457 (+ short `ad301ae` L52/L58/L347/L450) | unchanged | **kept**, see §5.1 |
| internal paths (§5.2) | L375, L383, L387, L388, L390, L410, L412, L423 | unchanged | **kept**, see §5.2 |
| AI-tool fingerprint (§5.3) | L447 | unchanged | **kept**, see §5.3 |

L13's comment ("arXiv advises against `\today`; author must set the date") is a **generic** mention of
arXiv, not a link to an identified preprint; kept.

## 3. Compile evidence (Tectonic, attempt 1 — clean)

```
export HOME=$PWD/scratch/utmlr1/home TMPDIR=$PWD/scratch/utmlr1/tmp \
       TECTONIC_CACHE_DIR=$PWD/scratch/utmlr1/tectonic-cache
./scratch/utex1/bin/tectonic --only-cached --keep-logs \
       -o scratch/utmlr1/out scratch/utmlr1/anonymous/main.tex
```
- **literal exit code = 0** (first and only attempt needed)
- `Undefined control sequence` count = **0**
- LaTeX `!` error lines = **0** (the log contains zero `!` characters at all)
- page count = **25** (`Output written on main.xdv (25 pages, 107576 bytes)`; `pdfinfo`: Pages 25)
- PDF sha256 = **`89d62e1d6d4c1932048f31c0bc3f39b532a48ded18fc94c68c061c931c23ccfa`** (184,983 B)
- `--only-cached` used deliberately: **0** download/connect lines in stdout — no network was touched.
  The bundle cache was copied from `scratch/ufixbody3/tectonic-cache` into `scratch/utmlr1/tectonic-cache`
  so Tectonic wrote only inside this unit's tree.
- PDF metadata: `pdfinfo` reports **no Author field** and `Metadata Stream: no`, so the byline cannot
  leak through the PDF info dictionary. `pdftotext` of the anon PDF finds **0** name hits (baseline: 2).
- A control compile of the unmodified source (`scratch/utmlr1/baseline/main.tex`, byte-identical to the
  source) also exits 0 with 0/0 errors and **25 pages**, so anonymisation did not move pagination.

## 4. Proof the numbers did not move

Guard: `scratch/utmlr1/make_anon.py`, results in `scratch/utmlr1/verify.json`.

- **Numeric-literal multiset, bibliography stripped: identical.**
  - `\begin{thebibliography}…\end{thebibliography}` stripped → **1,198** literals, multiset equal before/after.
  - stricter variant stripping from `\section*{References}` to EOF → **1,146** literals, also equal.
- **Citation structure: identical.**
  - `\cite` calls **23**, total cited keys **23**, distinct cited keys **13**,
  - `\bibitem` **13**, distinct keys **13**, uncited **0** (`[]`), unresolved **0** (`[]`).
  - This matches the card's expected 13 / 23 / 13 / 0 / 0 exactly.

## 5. Honest residual re-identification vectors (what a determined reader could still use)

These were **left in place on purpose**, and each is an author decision — not a mechanical edit.
The numeric-multiset guard in §4 is exactly why: every one of the tokens below contains digits, so
stripping it would move the literal multiset and break the "numbers did not move" proof.

### 5.1 Provenance digests and commit refs (strongest vector)
- L104 and L410: fixture source digest `076164ac53c2c1aac130953345c481f88b51f4d6fb93d465c7430308a99b4796`
- L391 and L457: commit `ad301ae1a5472fa7bd27807fdc7bb15d35f81988` (short `ad301ae` at L52, L58, L347, L450)
- L401: HEAD `907fa39da7ba8ecfbe6e976b7a4cddadea7ac36b`
- L410: shipped fixture digest `89e77a8e24a907f06345a45485c013799e08c806cc9d8f075db7709fbfd8e169`
- Identity of the private source repository is disclosed by name: `docs/DECIDER_STACK_DECISION.md`
  (L52, L69–L72, L347, L391, L450, L457) and the commit `ad301ae`.
A reader who can locate that repository (or the CC BY 4.0 published series) recovers the author.
Full commit hash at L457 lives *inside* the bibliography, so it could be removed without breaking the
guard; the others cannot.

### 5.2 Internal workspace paths
`strategy/licence-templates/RELEASED-PIECE/` (L423), `tools/typed-channel/` (L390),
`evals/fixtures/reflex-decisions.ts` (L104), `fixture/reflex-decisions.ts` (L383),
`preregistration/EXP12-typed-channel-comparison-prereg.md` (L387),
`second-labeller/…` (L388, L412), `verify/recompute-claims.py` (L375).
Private-tree paths; they fingerprint the author's project but do not name a person.

### 5.3 AI-tool disclosure fingerprint
L447 names a distinctive toolchain and month: "DeepSeek Harness", `deepseek-v4.1-flash`,
`step-5-preview-free`, `mimo-v2.6-flash`, "In October". This is a searchable behavioural fingerprint.
It also carries digits, so it was not mechanically stripped; and TMLR's LLM-disclosure expectations may
require keeping it. Recommend the author decide whether to genericise it to "large language models"
(which would be a substantive edit, and would also move the numeric multiset).

### 5.4 Future Zenodo DOI
L375 and L407 say "Zenodo DOI pending" and L427 "Persistent identifier: none yet". Nothing is linked
today, so this identifies no one. **Before minting**, verify the Zenodo deposit record does not name
the author; if it does, L375/L407 must be neutralised (digit-free edit, guard-safe) or the double-blind
link rule is broken.

### 5.5 Irreducible content fingerprint
The distinctive title, the sealed 190-case fixture, the single-fixture negative result and the
"author decision 2026-10-15" dates (L375, L407, L423) plus host `GX10 gx10-163b` (L424) narrow the
space sharply. A reader already inside the author's research area can guess. This is inherent to a
double-blind review of a narrow result and cannot be fixed by string removal.

### 5.6 Not present at all (verified 0 hits)
ORCID (incl. `0009-0009-9505-3546`), GitHub/GitLab handle, `Aswin-Ram-K`, `research-publish-packages`,
any email address, any personal URL, and **any preprint or DOI link to this paper itself**.

## 6. Open author decisions before submission (none is a blocker for the build)

1. Decide on §5.1–§5.3 residual tokens: accept, or authorise an edit that *will* move the numeric
   multiset (making the §4 guard inapplicable by design rather than by accident).
2. Confirm the Zenodo deposit is author-anonymous before minting the DOI (§5.4).
3. This file uses the generic `article` class with `\pdfpagewidth`, **not** the TMLR style file.
   Whether TMLR requires `tmlr.sty` at submission versus camera-ready was **not verified here** and
   needs checking against TMLR's current author instructions.
4. The "Author contributions" / "Funding" / "Competing interests" / "Use of AI tools" sections remain,
   now nameless. TMLR's current policy on such sections at submission was **not verified here**.

## 7. Artifacts

- `scratch/utmlr1/anonymous/main.tex` — the anonymised submission source
- `scratch/utmlr1/make_anon.py` — the transform + all guards (idempotent, asserts on mismatch)
- `scratch/utmlr1/verify.json` — machine-readable sweep/guard results
- `scratch/utmlr1/anon.diff` — the 2-line diff proof
- `scratch/utmlr1/out/main.pdf` + `scratch/utmlr1/out/main.log` — anonymised build
- `scratch/utmlr1/baseline/main.tex` + `scratch/utmlr1/out-baseline/` — control build

## UTMLR2 — tmlr.sty-compliant anonymised variant (appended 2026-10-17)

Status: built and compiled clean; **nothing was submitted anywhere**. Artifact: `scratch/utmlr2/tmlr/main.tex`
(476 lines, sha256 `16a19a2d7e3fccdf9acef8d9a9affd328cf38ae9fb252be5f81edc24790e6b7f`), alongside `tmlr.sty`, `tmlr.bst`, `fancyhdr.sty` and `LICENSE` copied verbatim from
the upstream style repo. Source of truth `scratch/utmlr1/anonymous/main.tex` was **not modified**.

1. **Mandatory style file.** Fetched from https://github.com/JmlrOrg/tmlr-style-file (branch `main` zip,
   redirecting to codeload.github.com/JmlrOrg/tmlr-style-file/zip/refs/heads/main): ZIP **694659 bytes**, sha256
   `48f9f972cc812d2cfc8032a78578c2f5d8939b92fbd4f61095e8cbeb3394f92d`; `tmlr.sty` sha256 `816214ff5919aa457b6b443bee52b15d9561421417b7f8a50cc84651519f0002`; `tmlr.bst` sha256 `306fd454cf40771bee01293eeb98d2c1cd5f4e11ed0cd7296b335f354fc45206`. The repo also ships `fancyhdr.sty`,
   `main.tex`, `main.bib`, `math_commands.tex` and a prebuilt `main.pdf`. Preamble switched from
   `article` (a4paper/11pt) to `\documentclass[10pt]{article}` + `\usepackage{tmlr}` + `hyperref`.
   Evidence the style is actually in force: page 1 of the compiled PDF carries tmlr.sty's own running head
   "Under review as submission to TMLR" and the "Anonymous authors / Paper under double-blind review" block.
2. **Page-1 LLM-use footnote (required by TMLR's FAQ).** Added as an unmarked `\blfootnote` immediately after
   `\maketitle`; verified present in the page-1 text layer of the PDF. Wording names no harness, repository,
   host, model route or date.
3. **Author-identifying residue removed** (83 literal substitutions over three passes): the named private
   document `docs/DECIDER_STACK_DECISION.md` (13 sites, incl. a `\bibitem`, now an anonymous "internal errata
   note", citation key renamed to `source_corpus_errata_2026`); commit ids `ad301ae`/`907fa39…` and both
   fixture digests; internal paths (`evals/`, `tools/typed-channel/`, `harness/`, `strategy/`, `docs/`,
   `EXP#12-…md`); the host name; the harness name and model routes; the Zenodo/DOI-pending sentence; the dated
   "author decision 2026-10-15" provenance; "released" → "submitted/supplementary" throughout.
4. **Numeric guard re-baselined honestly — it MOVED.** Literal multiset (env-strip / refs-section-strip modes):
   before **1198 / 1146** tokens over **340** distinct values; after **1086 / 1035** over **304**; 56 distinct
   values removed, **0 added**, multisets not identical. Movers are the stripped identifiers: the 64-hex and
   40-hex digests, `301` (x5/x4, from `ad301ae`), `907`, `2026` (x7), `15` (x8), `10` (x11), `265`,
   `269`, `281`, `309`, `415`, `500`, `494`, `495`, `4.1`, `2.6`. No claim-bearing value moved:
   `0.6789` 25→25, `0.3474` 27→27, `0.4526` 13→13, `0.6684` 19→19, `0.9014`/`0.8577` 4→4, `0.9053`/`0.8632`
   3→3, `0.9158` 3→3, `0.9125` 5→5, `4.167` 7→7, `0.33` 26→26, `0.32` 25→25, `152,000` 4→4, `721` 1→1;
   only `190` (31→30) and `74` (35→33) drop, both because a private record *name* ("second-labeller-190",
   `…:74`) was removed, not a claim instance.
5. **Compile (Tectonic 0.15, `scratch/utex1/bin/tectonic -X compile`).** Literal exit code **0**;
   `Undefined control sequence` count **0**; LaTeX `!` line count **0**; `error:` lines **0**; **16 pages**
   (pdfinfo, letter), 178203 bytes. 27 Overfull/32 Underfull hbox warnings remain (cosmetic: unbreakable
   `\texttt` path strings inside the 0.48-textwidth p-columns of the provenance table, lines 390-398).
6. **Survey check.** The manuscript is a single-fixture negative result with a declared primary baseline and a
   pre-registered falsifier ladder; it contributes a measurement, not a literature synthesis. Judged **not a
   survey** (see `orchestration/units/UTMLR2.md` for the reasoning against TMLR's 2026-09-01 ban).

---

## UTMLR6 — rebuild against the DOI-bearing source (appended 2026-10-18)

**Why this section exists.** After the UTMLR2/UTMLR5 work, a unit installed the published Zenodo DOI
into the identified source. `papers/encoder-crossover-190/submission/main.tex` is now **84,786 B**,
sha256 `1468b61e5baf1a2dc110e5612b70c9d83adc0a91e3101a9fe5b5cfdac6294c6b`, containing
`10.5281/zenodo.23463945` (**3** occurrences: L375, L407, L427) and `10.5281/zenodo.23463944`
(**1** occurrence: L427). Those values reproduce the UTMLR6 card exactly (`CARD_DISAGREEMENT: none`).

**Dated correction to the UTMLR2 section above, item 3.** It states "the Zenodo/DOI-pending sentence"
was removed. True of the UTMLR2 source, which said `Zenodo DOI pending`; **not** true of the current
source, which carries a minted DOI. The frozen UTMLR2 rule for each of the three sites now matches
**0** times (`MISMATCH expected=1 found=0`). The removal is restored by UTMLR6's `SCRUB4` — three
re-anchored rules, each `found=1`; see `scratch/utmlr6/evidence.json`.

**Dated correction: the UTMLR5 *driver* is stale even though its *artifact* is not.** Re-run against
the current source, `scratch/utmlr5/build.py` matches 0 on its 3 pass-1 DOI anchors and carries no
re-anchored rule for them, so the DOI would survive into its PDF. The committed artifact is not
affected: UTMLR6's rebuild is **byte-identical** to `scratch/utmlr5/tmlr/main.tex` — 83,785 B, sha256
`8d6b036c23e4195e9119f67d2a7493831e836bfd68a9a2d73849eecdfbbf0fd0`, 476 lines, `cmp` silent, `diff`
+0/−0 lines. UTMLR6's value is that it derives that artifact from the *current* source and states the
DOI rule explicitly.

**Residue removed (absolute counts per rule).** SCRUB3 rules 1–7 each `found=1`; SCRUB4 rules 1–3 each
`found=1`; SCRUB4 rules 4–5 (safety net, expected 0) `found=0`. DOI literals present and gone:
`10.5281` any 4→0, `Zenodo` (case-insensitive) 7→0, `10.5281/zenodo.23463945` 3→0,
`10.5281/zenodo.23463944` 1→0, measured source → anon → pass1 → pre-scrub → final.

**Compiled-PDF proof.** Tectonic 0.15, `scratch/utex1/bin/tectonic -X compile main.tex --only-cached`,
with `HOME`/`TMPDIR`/`TECTONIC_CACHE_DIR` inside `scratch/utmlr6/`; `-Z continue-on-errors` **not**
used. Literal: exit **0**; `Undefined control sequence` **0**; `!` lines **0**; `error` lines **0**;
**16 pages**; PDF 176,971 B, sha256 `a777d2a30e1f8707d84673d401a8a231cd4526b4ee78f5a1163070961929acdf`.
The PDF's own extracted text (pdftotext) reports **0** for every author identifier, both DOI strings,
`5281`, `analysis.json`, `ad301ae`, `907fa39`, and 40+ hex; `Anonymous authors` **1**; `doi.org` 1
(a third-party cited work). `pdfinfo` reports **no Author field** and `Metadata Stream: no`; a raw
binary scan of the PDF is **0** for every identifier.

**Numbers.** Numeric-literal multiset (bibliography / refs-section stripped): **1211→1092** total,
**350→310** distinct, **0 added**; removed tokens are provenance datums only, including the DOI tokens
(`10.5281` ×4, `23463945` ×3, `23463944` ×1) and `1603` ×1 (the removed e-mail). After-counts
(1092 / 310) equal UTMLR5's recorded after-counts. Claim anchors unchanged: `0.6789` 25→25,
`0.9125` 5→5, `\textbf{190}` 1→1, `721` 1→1. Bare-digit substring drops (`190` 29→28, `74` 35→33,
`33` 34→32, `27` 13→12, `76` 9→6, `54` 10→8, `13` 24→21, `44` 10→9) are collisions inside removed
commit/digest/line-locator tokens, not claim instances.

**Structure.** `\cite` 23, cited keys 23, distinct cited 13, `\bibitem` 13, distinct 13, uncited `[]`,
unresolved `[]`, `\bibitem[...]` 0 — identical source vs variant.

**Policy.** `tmlr.sty` applied; `\setcitestyle{numbers}` immediately after `\usepackage{tmlr}`; page-1
LLM-use `\blfootnote` on page 1 (`pdftotext -f 1 -l 1 | grep -c "Use of AI tools"` = 1); no
acknowledgements section; no self-owned DOI or venue link. Survey check still negative (UTMLR2's
judgement, unchanged). Nothing under `papers/**` was modified.

# UPREPRINT3 — author-approved keywords for papers #2 and #7; regenerate + prove

**Bound:** 25 tool calls. **Used:** 23. **Status:** done.
**Write paths used:** `tools/package/md2tex.py`, `tests/test_md2tex.py`, `papers/gated-read-batching/**`,
`papers/replay-record-not-decision/**`, `strategy/PREPRINTS_SUBMISSION.md`, `scratch/upreprint3/**`,
this card, own handoff. **Not touched:** `papers/encoder-crossover-190/**` (read-only), `/home/zer0null/Duval`,
git state, network, no `-Z`.

## Jobs and outcomes

1. **Mechanism (uniform, no per-paper logic).** Both sets added as per-package `keywords=` values in
   `tools/package/md2tex.py` `PACKAGES` (the single source of truth). Emission site unchanged: immediately
   after `\maketitle`, before `\begin{abstract}` — the same code path paper #3 already uses.
   - `replay-record-not-decision`: `replay determinism, LLM decision replication, binding divergence, record versus decision, option-index encoding, agent trace reproducibility`
   - `gated-read-batching`: `tool-call gating, batched decisions, read-gate classification, binary gate decisions, token exposure, low-effort prompting`
2. **Page 1 confirmed for both** (`pdftotext -f 1 -l 1`): `Keywords:` on page 1, not on page 2.
3. **Test pins every package's set literally, in order** — `tests/test_md2tex.py::test_keywords_pinned_per_package`
   (+ `EXPECTED_KEYWORDS`, registered in `main()`). Red-proved twice on kept copies.
4. **Regenerated with the project's tooling** — `main.tex` twice per package (byte-identical, and #3 still
   byte-matches its shipped file); PDFs via Tectonic from a zip extraction; the two `preprints` zips.
5. **Bundle self-sufficiency** — each zip has exactly one member `main.tex`, extracted bytes `cmp` equal
   `submission/main.tex`, and each was compiled from that extraction in a clean scratch dir.
6. **Nothing but the keywords moved** — numeric-literal multisets unchanged (all deltas zero), cite/bibitem
   invariant unchanged, `Conflicts of Interest` still immediately before the reference list.
7. **Digests reported**; paper #3's zip is untouched at the exact expected value.

## Evidence (literal)

- `python3 -m pytest tests/test_md2tex.py --noconftest -q -p no:cacheprovider` → `8 passed in 0.68s`.
- RED (reordered replay set, kept copy `scratch/upreprint3/md2tex_reorder.py`):
  `1 failed` — `AssertionError: replay-record-not-decision: registry keywords are not the author-approved set, in order: 'replay determinism, LLM decision replication, binding divergence, option-index encoding, record versus decision, agent trace reproducibility' != 'replay determinism, LLM decision replication, binding divergence, record versus decision, option-index encoding, agent trace reproducibility'`
- RED (dropped gated `token exposure`, kept copy `scratch/upreprint3/md2tex_drop.py`): `1 failed` — same message shape.
- `diff` pristine vs shipped `main.tex`: `encoder-crossover-190` **empty**; `gated-read-batching` and
  `replay-record-not-decision` **`15a16,17`** — only the `\noindent\textbf{Keywords:}` line plus a blank line.
- Numeric multisets (total/distinct): #3 MANUSCRIPT `1193/337` → `1193/337`, main.tex `1320/351` → `1320/351`;
  #7 `539/136` → `539/136`, `551/131` → `551/131`; #2 `379/118` → `379/118`, `389/124` → `389/124`; **every delta `{}`**.
- Tectonic (`scratch/utex1/bin/tectonic -r 1 --keep-logs -o <out> main.tex`, **no `-Z`**), from zip extraction:
  `gated EXIT=0 | Undefined=0 | '!'=0 | 13 pages | A4 | 110521 B | sha256 5f563b2bba9f7a2bcded85125d8089ddefe653f3bdf82545632c25fa994f81e2`;
  `replay EXIT=0 | 0 | 0 | 10 pages | A4 | 94683 B | sha256 4ac73a5177f2c60409d375fc3c832d06c859eac647f1bd59b15527db8f4f3537`.
- Page 1: `Keywords: tool-call gating, batched decisions, read-gate clas-siﬁcation, bi-` (page1 hits=1, page2 hits=0);
  `Keywords: replay determinism, LLM decision replication, binding diver-` (page1 hits=1, page2 hits=0).
- Zips: members = `[main.tex]`; extracted == submission (`cmp` clean);
  `gated 14094 B sha256 feecb7f7879766bf9ecedaa03bbae3b8817eaab47513d092e42052a4127b74f5`;
  `replay 10372 B sha256 251af28e2141da640abf4b8dc29d821c6ceeec60f0e942936943a15cad14c15a`.
- Paper #3 zip: `28712 B sha256 705bc498c7c7eb7cf1e53cae8f49fb8656787694c39dbc7c5f4064f9aa7caf7f` — exactly the card's value.
- Cites: #3 `bibitems=13 cite_cmds=23 distinct=13 uncited=none unresolved=none`; #7 `13/14/13 none none`;
  #2 `8/8/8 none none` (identical to UPREPRINT2's pre-change readings).
- COI position: gated `\section*{Conflicts of Interest}:269` → `\section*{References}:273` → `\begin{thebibliography}:277`;
  replay `:229` → `\begin{thebibliography}:233`.

## Card claim that disagreed with measurement (reported, not accepted)

The card states "paper #3's abstract alone fills page 1, so its keyword line lands on page 2" and that #3
"already has that problem". **Both are false by measurement**: `pdftotext -f 1 -l 1` on
`papers/encoder-crossover-190/rendered/encoder-crossover-190.pdf` gives `page1 Keywords hits=1`, `page2 hits=0`
(`Keywords: text classiﬁcation benchmark, encoder classiﬁers, ﬁne-tuned`). The after-`\maketitle` emission keeps
paper #3's keyword line on page 1 too. No paper has the page-2 problem.

## Scope note

The `submission/*.tar.gz` containers were **not** regenerated (outside the card's enumerated artifacts) and are
now stale relative to `submission/main.tex`. Recorded in `strategy/PREPRINTS_SUBMISSION.md` and the handoff's
`next_unit_hint`, not silently changed.

Full machine-readable report: `orchestration/handoffs/UPREPRINT3.json`.

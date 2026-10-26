# VERIFICATION_REPORT_PAPERS.md — independent verification of claims A, B, C

**Verifier unit:** UVERPAPERS. Author units: `UFIXPAPER5` (claim A converter + claim C de-namings)
and earlier `UEXP`/`UEXP2`/`UWIRE…` units (claim B relabel). No artifact under test was authored or
modified by this unit. All mutation happened on copies in `scratch/uverpapers/**`.
`/home/zer0null/Duval` was never touched and no `git` command was run against it.
Tool calls used: 25/25. `pytest` was not run (see *Untested*); `tests/conftest.py:19` imports an absent
module, so only `--noconftest` collection is possible here.

Verdict: **pass** — all three substantive claims reproduce. One record-fidelity defect found in
`scratch/ufixpaper5/edits.tsv` (no effect on the shipped paper).

---

## Claim A — one converter, registry-driven, byte-reproduces both shipped `main.tex`

**Reproduced.** Copies of each manuscript were converted into scratch out-dirs and compared to the
shipped files:

| package | run 1 sha256 | run 2 | vs shipped |
|---|---|---|---|
| `encoder-crossover-190` | `4efa575442b2878037d625bc604e2ae7aab7e1faf9d9515bd9c9747ebf28885a` | identical (`cmp` clean) | `ENC_BYTE_IDENTICAL` |
| `gated-read-batching` | `a5d32dd7da1a2b9b920ffb9cb272749339edd954f9a1e63b11bb59df6d8886b4` | identical (`cmp` clean) | tree-identical for all converter outputs |

Both digests equal the claimed values, measured here, not restated. `cmp` on each package's two runs
was silent → deterministic. `diff -r` of the GRB out-dir against `papers/gated-read-batching/submission`
differs only by shipped files the converter does not emit (`BUILD_NOTES.md`, `METADATA.md`,
`gated-read-batching.tar.gz`) — `main.tex`, `ABSTRACT.txt`, `ABSTRACT_METADATA.txt` all match.

**The registry is real.** `tools/package/md2tex.py:84-151` holds one `PACKAGES` table keyed by slug;
`PACKAGES` is selected by `--package` (`tools/package/md2tex.py:598`). Divergences (unicode map,
anchor table, bib source, sanitise rules, guard flags) are config keys, not per-paper branches.

**The citation guard actually fails — it does not merely print.** `guard_citations`
(`tools/package/md2tex.py:443-457`) raises `SystemExit` when a `\bibitem` is uncited, a `\cite` has no
entry, or the counts disagree. Two independent red cases were constructed on copies:

- **uncited `\bibitem`** — the anchor text `` `docs/DECIDER_STACK_DECISION.md` §11.6 `` (4 literal
  occurrences) was deleted from the copy; the converter exited rc=1 with
  `R18 FAILED: uncited=['source_decider_stack_2026'] unknown=[] bibitems=13 bibkeys=13`
- **`\cite` with no entry** — `[[CITE:nosuchkey]]` injected as a paragraph; rc=1 with
  `R18 FAILED: uncited=[] unknown=['nosuchkey'] bibitems=13 bibkeys=13`

Both are real failures (nonzero exit from `SystemExit`), so the pass line printed on green runs
(`... guard: PASSED (the guard did not fire; label 'R18 FAILED' names the defect ... and is NOT this
run's outcome)`) cannot be confused with a fired guard.

## Claim B — the internal reader label was removed without moving any number

**Reproduced.** An independent pre-relabel manuscript exists on disk
(`scratch/uverpkg10/mdrun/papers/encoder-crossover-190/MANUSCRIPT.md`, a copy from before the
relabel): it carries `UEXP` word-boundary ×7, `UEXP2` ×1, `UREFS` ×1 — exactly the claimed edit
counts. Regenerating `main.tex` from that pre-relabel manuscript with the converter yields a
numeric-literal multiset of **n=819** with sha256
`a0762fd5a407cc75053bfe74aa7d9c8066da3913e1a703eec1bff048b60f15c0` — *identical* to the shipped
`main.tex` under the same definition (`(?<![\w.\-])\d+(?:\.\d+)?(?![\w])`). So the relabel and the
de-namings moved no published number, measured across both edit generations. The raw digit-run delta
is exactly `{'190': 5, '2': 10}` (removed filename digits), also as claimed.

No `UEXP`, `UEXP2` or `UREFS` survives: 0 occurrences in both `MANUSCRIPT.md` and the shipped
`main.tex`.

Citation bookkeeping on the shipped `main.tex`, measured: `\bibitem`=13 (13 distinct),
`\cite{`=23, distinct keys=13, uncited=`[]`, unresolved=`[]` — every claimed value reproduced. (The
converter's own `cite_extract_re` for this package, `tools/package/md2tex.py:93`, is single-key; the
23/13 split counts occurrences vs distinct keys, and both agree with the guard's clean exit.)

## Claim C — 16 de-namings; one name deliberately kept

**Absence reproduced, with a non-vacuous check.** On the de-escaped shipped `main.tex`
(`re.sub(r"\\([_#%&${}])", r"\1", tex)`): 0 occurrences of `REFS.md`, `CLAIMS.md`,
`CHECKLIST.md`, `OPEN_QUESTIONS.md`, `UNSOURCED_RETAINED.md`, `EVIDENCE_NOTES.md`,
`PAPER_CANDIDATES.md`, `LEARNINGS.md`, `ROBUSTNESS.md`, `experiments/second-labeller-190/`, and also
0 in `MANUSCRIPT.md`.

**Red→green on the check itself (mandatory).** A copy with `` `OPEN_QUESTIONS.md` `` and
`` `EVIDENCE_NOTES.md` `` planted in a paragraph was converted: the resulting `main.tex` has
**naive count 0 but de-escaped count 1** for each. The perturbation is not vacuous — it is the exact
escape the converter performs (`_` → `\_`), and it proves a source-side/naive grep on the shipped
file would silently miss such a string while the de-escaped check catches it. Green on the real file:
naive 0 / de-escaped 0.

**The kept name was right.** `docs/DECIDER_STACK_DECISION` occurs 14 times in the shipped `main.tex`
(claimed 14; the literal path `docs/DECIDER_STACK_DECISION.md` 9 times). Removing its anchor makes
the converter fail: rc=1 `R18 FAILED: uncited=['source_decider_stack_2026'] ...` (same red case as
above) — the anchor is `ANCHORS_ENC` entry `source_decider_stack_2026`
(`tools/package/md2tex.py:65`), so deleting the name drops a `\cite` and trips the guard. Keeping it
is correct; no cleaner treatment exists that both removes the name and keeps citation integrity, short
of rewriting the citation to a different source.

**Records that should still be named.** The released package `scratch/uneutral10/package` contains
exactly **29** regular files, and all four claimed records are present: `results/REPORT.md`,
`second-labeller/EVIDENCE.md`, `second-labeller/PREREGISTRATION.md`, `README.md`. The shipped
`main.tex` names `results/REPORT.md` ×4, `PREREGISTRATION.md` ×2, `README.md` ×2 — correct. It does
**not** name `second-labeller/EVIDENCE.md` (0 occurrences); the manuscript's original reference was to
the *unreleased* tree path `experiments/second-labeller-190/EVIDENCE.md`, which was properly
de-named. Not a defect, but the naming claim is narrower than it sounds.

**`RELATED_WORK_NOTES.md` — the concurrent unit was right, the parent was wrong.** 0 occurrences in
the shipped `main.tex` (naive and de-escaped), 0 in `MANUSCRIPT.md`, and 0 in both pre-edit copies
(`scratch/ufixpaper5/MANUSCRIPT.before.md`, `scratch/uverpkg10/mdrun/...`). The asserted "appears
twice" is **contradicted**; I could not reproduce it anywhere.

## Defect found (record fidelity, not shipped output)

`scratch/ufixpaper5/edits.tsv` row *"`papers/encoder-crossover-190/EVIDENCE_NOTES.md` and the
subset's own `README.md`."* records its post-edit text as starting `in this record's internal
evidence notes ...`. Both independent pre-edit copies already contain `... command list in\n  \`papers/
encoder-crossover-190/EVIDENCE_NOTES.md\` and the subset's own \`README.md\`.` — i.e. the leading
`in ` was already present. Replaying that row forward therefore yields `... command list in\n  in this
record's internal evidence notes ...` (doubled `in`; verified). The shipped manuscript reads
correctly and regenerates byte-identically, so this is an inaccurate edit-log row, not a paper defect:
15/16 rows replay exactly, the 16th only after whitespace-flexible matching and with one stray word.
UFIXPAPER5's "16 de-naming edits applied, 0 skipped" holds as an *outcome*.

## Reproduced / not reproduced / untested

- **Reproduced:** both shipped digests and determinism; the two red guard failures; the 819-token
  numeric multiset and its sha256; the `{'190':5,'2':10}` digit delta; 13/23/13/0/0 bookkeeping;
  zero surviving internal labels; 14 × `DECIDER_STACK_DECISION`; the 29-file package and its four
  records; the de-escaped absence check with its red case.
- **Not reproduced / contradicted:** `RELATED_WORK_NOTES.md` ×2 (0 everywhere).
- **Untested:** `tests/test_md2tex.py` (not run — `pytest` cannot collect normally here; would need
  `--noconftest`); `MANIFEST.json` ↔ on-disk agreement; the shipped `.tar.gz` member bytes;
  LaTeX compilation of either `main.tex`. None of these was part of claims A/B/C.
- **Write discipline:** every converter run targeted a scratch copy; `papers/**` was read only. The
  three source files' sha256 measured before and after all work are unchanged
  (`MANUSCRIPT.md` `653d05db01ec00eff22f90211ef059b480463754f1a7cf850b87f0bf62a6db81`,
  `REFERENCES.bib` `fd9bafd6944f5f1f544fabe69766b51b38450b0d7b4d9493b56e542c99863394`,
  GRB `MANUSCRIPT.md` `2a4cc287e8509b2cf2492cf1edff989ff57f352d8d0d2d2bf7666de023b8a2a7`).

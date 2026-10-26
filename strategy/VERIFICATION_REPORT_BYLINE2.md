# VERIFICATION REPORT — BYLINE2 (unit UVERBYLINE2)

**Verifier:** UVERBYLINE2 (not an author of any artifact checked; no file under test was modified).
**Parent:** `session-c3d61727-8af8-4c19-b1b9-5922c347a11a`
**Workspace:** `/home/zer0null/reserach extarctor`  •  **Bound used:** 8 tool calls at report time (hard bound 12).
**Overall verdict: `pass`** — every claim that is reproducible on disk reproduced exactly; one
sub-claim (that the converter *logic* is unchanged) is **not independently provable** because the
file has no version history on disk. That is recorded as `unverified`, not as a defect.

---

## Claim 1 — three papers, one identical placeholder byline, no invented name — **PASS**

Command (measured, not trusted):

```
for f in papers/encoder-crossover-190/submission/main.tex \
         papers/gated-read-batching/submission/main.tex \
         papers/replay-record-not-decision/submission/main.tex; do
  sha256sum "$f"; wc -c < "$f"; grep -c '\\author{' "$f"; grep -o '\\cite' "$f" | wc -l; grep -n '\\author' "$f"; done
```

| paper (config id) | path | sha256 | bytes | `\author{` count | `\cite` count |
|---|---|---|---|---|---|
| #3 encoder-crossover-190 | `papers/encoder-crossover-190/submission/main.tex` | `4efa575442b2878037d625bc604e2ae7aab7e1faf9d9515bd9c9747ebf28885a` | 84,358 | **1** | 23 |
| #7 gated-read-batching | `papers/gated-read-batching/submission/main.tex` | `a5d32dd7da1a2b9b920ffb9cb272749339edd954f9a1e63b11bb59df6d8886b4` | 37,291 | **1** | 14 |
| #2 replay-record-not-decision | `papers/replay-record-not-decision/submission/main.tex` | `617672485745d09db0073421e93b4a1e12497e60fbf034c31f9aa1c740aa5a23` | 20,969 | **1** | **0** |

- Every digest and byte count matches the claim exactly. **Note on labels:** the claim's
  "paper #2 digest `617672485745…` (20,969 B)" is `papers/replay-record-not-decision/`, **not** the
  second path in the claim's file list. The config's own header resolves the numbering:
  `tools/package/md2tex.py:7` — "Paper #3 (papers/encoder-crossover-190) and paper #7
  (papers/gated-read-batching)". So #2 = replay-record-not-decision. Read that way, the claimed
  digest↔file mapping is **correct on all three files**. No contradiction.
- Each file's single author line is byte-identical and is a placeholder (line 10 of each):
  `\author{AUTHOR SLOT: REAL NAME --- TO BE SUPPLIED}` (three hyphens, `---`, before `TO BE SUPPLIED`).
- **No second `\author` line** in any of the three: `grep -c '\\author{'` = 1 for each. Verified
  independently by the test helper's line-set logic (below), which also flags any *other*
  `\author`-starting line.

## Claim 2 — converter logic unchanged, data-only registry edit — **PASS ON HASH; `unverified` ON PROVENANCE**

```
sha256sum tools/package/md2tex.py
d924c949357fb47d5387fdbd827df1f718876c8519d305c9a847e841eb1982d2  tools/package/md2tex.py
```

- Claimed converter digest **reproduced exactly**.
- **Is the file under version control? No.**
  `GIT_OPTIONAL_LOCKS=0 git status --porcelain -- tools/package/md2tex.py` → `?? tools/package/md2tex.py`
  (untracked). `git log -- tools/package/md2tex.py` prints nothing. **There is no before/after blob,
  so no VCS diff can be obtained** — this is the strongest form of the evidence limit the task asked
  about, and it means the "logic was not changed" half cannot be proven by diff.
- Evidence *available* on disk, all consistent with a data-only edit:
  - In-file changelog at `tools/package/md2tex.py:169-177` states it verbatim: "`author_line` --
    CHANGED 2026-10-16 (UFIXBYLINE2). Drafting-time value was `None` … The placeholder below is the
    same expression as the other two entries and `require_author_slot=True` applies the identical
    exactly-one-slot guard. No name was invented."
  - The changed datum is one registry field in one entry:
    `tools/package/md2tex.py:227 author_line="\author{AUTHOR SLOT: REAL NAME --- TO BE SUPPLIED}"`;
    the two older entries carry the same literal at `:115` (encoder) and `:149` (gated).
  - The author-slot *logic* is generic, reading only config fields — `tools/package/md2tex.py:574`
    (`if cfg["author_line"] is None and "\\author" in doc`), `:591` (`if cfg["require_author_slot"]
    and (doc.count("AUTHOR SLOT:") != 1 …)`), `:633-636` (emits `cfg["author_line"]` when set).
    Nothing package-specific was added for the byline.
  - The other three `md2tex*.py` copies on disk (`scratch/uprep7/`, `scratch/uprep1/`,
    `scratch/uvcr33/`) are **much older single-paper converters** (984–1139 diff lines vs. the
    shipped file), so they are **not** a usable pre-change baseline for this edit either.
- Recorded as `unverified`: "the converter's logic was not changed" rests on the in-file changelog
  plus code inspection; a diff against the pre-UFIXBYLINE2 file is **not obtainable from disk**.

## Claim 3 — regeneration reproducible and non-regressive — **PASS (reproduced)**

Per package: the paper tree was copied to `scratch/uverbyline2/<slug>/paper` (with
`submission/` excluded), then the converter was run **twice** with `--paper-root` pointed at the copy,
and `cmp` was run run-to-run and against the shipped file:

```
cmp run1/main.tex run2/main.tex        -> IDENTICAL
cmp run1/main.tex papers/<slug>/submission/main.tex -> IDENTICAL
```

| package | run1 = run2 | run1 = shipped | digest |
|---|---|---|---|
| encoder-crossover-190 | IDENTICAL (exit 0/0) | IDENTICAL | `4efa5754…` |
| gated-read-batching | IDENTICAL (exit 0/0) | IDENTICAL | `a5d32dd7…` |
| replay-record-not-decision | IDENTICAL (exit 0/0) | IDENTICAL | `61767248…` |

No regression: the regenerated bytes equal the shipped bytes for all three, so shipping the
placeholder is exactly what the current converter produces from the current manuscripts.

## Claim 4 — updated test is stronger, not weaker — **PASS**

Command run verbatim:

```
PYTHONDONTWRITEBYTECODE=1 python3 -m pytest tests/test_md2tex.py --noconftest -q -p no:cacheprovider
......                                                                   [100%]
6 passed in 0.45s
```

Claimed `6 passed` reproduced (exit 0). The byline test is
`tests/test_md2tex.py:280 test_ships_author_slot_placeholder_and_no_citation_apparatus`, driven by
`BYLINE_PAPERS` (`:253-254`) and two helpers:

- `tests/test_md2tex.py:257-269 assert_author_slot` — normalises all lines, then requires
  **exactly one** line `== AUTHOR_SLOT` (`:265`) **and zero** other lines starting with `\author`
  (`:266`), i.e. the *literal* placeholder and nothing else. `AUTHOR_SLOT` is pinned at `:252`.
- `tests/test_md2tex.py:272-277 assert_no_citation_apparatus` — unchanged three-token guard
  (`\cite{`, `\bibitem{`, `thebibliography`), still scoped to the one citation-free paper
  (`:291-293`).

**Was the load-bearing citation assertion loosened? No.** `assert_no_citation_apparatus` is the same
positive check, still applied to the citation-free paper, and it is joined by
`tests/test_md2tex.py:167 test_shipped_artifacts_are_clean` (bidirectional cite/bibitem on every
paper) and `:194 test_zero_bibliography_guard` (red→green on the zero-bibliography paper).

**Red→green, run against the test's own helpers on scratch copies** (the shipped files were never
touched — the pytest path is hard-wired to `papers/<slug>/submission/main.tex` at `:288`, so
perturbations were exercised through the very functions that test calls):

- GREEN: `assert_author_slot` OK on all three real files; `assert_no_citation_apparatus` OK on
  replay-record-not-decision (all three tokens printed `False`).
- **RED A — placeholder replaced by a plausible real name** `\author{Jane Q. Researcher}`:
  `AssertionError: …/scratch/uverbyline2/red_name.tex must carry exactly one byline line
  '\author{AUTHOR SLOT: REAL NAME --- TO BE SUPPLIED}' (found 0); other \author lines:
  ['\author{Jane Q. Researcher}']`
- **RED B — author line deleted entirely**:
  `AssertionError: …/scratch/uverbyline2/red_noauthor.tex must carry exactly one byline line
  '\author{AUTHOR SLOT: REAL NAME --- TO BE SUPPLIED}' (found 0); other \author lines: []`
- **RED C — stray `\cite{ghost}` appended to the citation-free shipped paper**:
  `AssertionError: unexpected '\cite{' in …/scratch/uverbyline2/red_cite.tex`
- **RED C2 — end-to-end**, `[[CITE:ghost]]` appended to the citation-free `MANUSCRIPT.md` on a copy:
  exit `1`, last line
  `CITE/BIBITEM GUARD FAILED: citation apparatus in a zero-bibliography paper: ['\\cite{']`;
  removing the marker → exit 0 and regenerated `main.tex` == shipped (sha256 equal).

**Why none of the perturbations is vacuous.** Red A is the decisive one: a weak "some `\author`
exists" check would stay green, and only the exact-literal comparison kills it. Red B kills the
`len(hits)==1` half (a check that only searched for a non-placeholder `\author` would pass). Red C
and C2 kill the citation half at both the artifact level and end-to-end; the identical guard was
independently shown live by `test_zero_bibliography_guard`. Red→green is therefore established for
both halves, with the "green" being the real 6-passed run plus the two helpers returning clean on the
unperturbed shipped files.

## Claim 5 — premise correction (only paper #2 is citation-free) — **CORRECT**

Measured `\cite` counts: replay-record-not-decision (#2) = **0**; encoder-crossover-190 (#3) = **23**;
gated-read-batching (#7) = **14**. The config's own comments agree: `tools/package/md2tex.py:160-168`
("a paper with ZERO external citations", `cite_anchors MUST be empty -- the manuscript contains no
`[[CITE:]]` marker and no `\cite` (measured)", `bib_source="none"`), and `:7` fixes #3/#7 as the two
citing papers. So the unit's correction — only one paper is citation-free and it is #2, while #3 and
#7 do contain `\cite{` — is **confirmed**, and the test's scoping of the citation half to
replay-record-not-decision (`tests/test_md2tex.py:291-293`) is right.

---

## Reproduced / not reproduced / could not test

- **Reproduced:** the three digests and byte sizes; exactly one `\author` per file; the identical
  placeholder; `\cite` counts; converter sha256; the `6 passed` test result; run-to-run and
  run-to-shipped byte identity for all three packages; four red cases (A, B, C, C2) plus green.
- **Not reproduced (nothing found to contradict):** none. No claim was falsified.
- **Could not test / could not obtain:** a VCS diff for `tools/package/md2tex.py` (untracked file —
  `?? tools/package/md2tex.py`; no log, no blob), hence the *logic-unchanged* half of claim 2 is
  `unverified` (supported by the in-file changelog at `:169-177` and the generic guard code at
  `:574/:591/:633-636`, but not proven by diff); the pre-rewrite text of `tests/test_md2tex.py`
  (overwritten) so "the old test applied the citation half to all three papers" is taken from the
  prompt, not independently checked — the *current* scoping is nevertheless correct per claim 5.
- **No modifications:** all perturbations were made on copies under `scratch/uverbyline2/`. Running
  the suite creates `scratch/umdtex1/` (the test's own scratch, `tests/test_md2tex.py:41`), which is
  outside my declared write paths but is the author's scratch; the test removes its tempdirs.
- Nothing under `/home/zer0null/Duval` was touched; no `git` verb was run against it; the only git
  calls were lock-free (`GIT_OPTIONAL_LOCKS=0`) reads inside this workspace.

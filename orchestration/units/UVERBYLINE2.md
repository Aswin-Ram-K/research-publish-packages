# UVERBYLINE2 — verifier: shared byline slot across three papers

**Role:** verifier. Did not author any artifact under test. Workspace `/home/zer0null/reserach extarctor`.
Parent: `session-c3d61727-8af8-4c19-b1b9-5922c347a11a`.

## Purpose
Independently re-check, with my own commands, the claim that two units gave all three
paper submissions the same placeholder byline slot, that the converter change was
data-only, that regeneration is byte-reproducible, and that the rewritten test is
stronger (not weaker) than the one it replaced.

## Claims under test
1. All three carry exactly one author line, byte-identical placeholder
   `\author{AUTHOR SLOT: REAL NAME --- TO BE SUPPLIED}`, no invented name.
   Files: `papers/encoder-crossover-190/submission/main.tex`,
   `papers/gated-read-batching/submission/main.tex`,
   `papers/replay-record-not-decision/submission/main.tex`.
   Claimed digests: #2 `617672485745d09db0073421e93b4a1e12497e60fbf034c31f9aa1c740aa5a23` (20,969 B);
   others `4efa575442b2878037d625bc604e2ae7aab7e1faf9d9515bd9c9747ebf28885a`,
   `a5d32dd7da1a2b9b920ffb9cb272749339edd954f9a1e63b11bb59df6d8886b4`. Measure, don't trust.
2. Converter logic unchanged — data-only registry edit. Claimed converter sha256
   `d924c949357fb47d5387fdbd827df1f718876c8519d305c9a847e841eb1982d2`.
   Registry `PACKAGES` in `tools/package/md2tex.py` (`author_line`, `require_author_slot`).
3. Regeneration reproducible + non-regressive: converter run twice per package on
   copies in `scratch/uverbyline2/**`, `cmp` run-to-run and against shipped files.
4. `tests/test_md2tex.py` rewrite is stronger: still asserts citation-free paper ships
   no citation apparatus; asserts the exact placeholder and rejects an invented name;
   can fail. Must produce red→green with non-vacuous perturbation.
   Claimed: `PYTHONDONTWRITEBYTECODE=1 python3 -m pytest tests/test_md2tex.py --noconftest -q -p no:cacheprovider` → `6 passed`.
5. Other unit's premise correction about my card: only paper #2 is citation-free;
   papers #3 and #7 do contain `\cite{`. Check against the files.

## Method
- Measure digests/sizes with `sha256sum`/`wc -c`; count `\author` and `\cite` occurrences
  per file with grep.
- Hash the converter; look for a VCS to establish whether a diff is obtainable
  (workspace is a git repo? file tracked?).
- Copy inputs into `scratch/uverbyline2/`, run the converter twice per package there,
  `cmp` run-to-run and against the shipped artifact.
- Red cases: on scratch copies, (a) substitute a plausible real name for the placeholder,
  (b) delete the author line, (c) add a stray `\cite` to the citation-free paper; run the
  test's own assertion path and show literal failure text.
- Run the claimed pytest command verbatim.

## Bounds
- Hard bound **12 tool calls**. Read specific files only; no tree walks.
- `pytest` needs `--noconftest` (`tests/conftest.py:19` imports an absent module) and
  `PYTHONDONTWRITEBYTECODE=1 -p no:cacheprovider` to leave no side effects.
- `/home/zer0null/Duval` strictly read-only, never git. Do not modify anything under test.

## Write paths
- `strategy/VERIFICATION_REPORT_BYLINE2.md`
- `orchestration/units/UVERBYLINE2.md`
- `orchestration/handoffs/UVERBYLINE2.json`
- `scratch/uverbyline2/**`

## Report-back
`orchestration/handoffs/UVERBYLINE2.json` in verifier shape (`unit`, `overall`, `checks`,
`blocker`, `next_unit_hint`, `write_paths`, plus `contradicted`/`overstated`/`not_reproduced`/
`unverified` where applicable), re-parsed for validity; ≤15-line summary to parent.

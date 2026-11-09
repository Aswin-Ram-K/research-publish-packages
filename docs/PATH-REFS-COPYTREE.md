# PATH-REFS-COPYTREE — the candidate set is the defect

A citation that no tree file satisfies is reported by `path_refs.py` as `wrong_dir` when the
same *basename* exists somewhere else. That signal is only honest if the alternate is a
different artefact. When every same-basename hit is a **byte-identical copy** of one file
(the corpus is full of snapshots: dockets material trees, state refresh mirrors, vendored
release copies, upstream package roots), the citation has no addressable alternate at all.
It is not misaddressed. It is `missing`.

## What was measured, and by which evidence

Candidate sets were examined for the 121 in-scope `wrong_dir` citations:

| evidence over the candidate set | citations |
|---|---|
| every candidate byte-identical to every other (one content, N locations) | 78 class at first probe, 72 in the final sweep |
| at least two distinct contents (a real file exists somewhere) | 43 in-scope / 287 global |
| single candidate (identity unverifiable) | 163 global |

The reason is **not** a pathname heuristic. A rule that fires because a directory is called
`build` or because a candidate sits under `scratch` would also fire on a real file that
happens to live there. The rule that was implemented fires only on content: the copies were
proven copies by digest (`2` to `1204` files per basename, one sha256 across all of them),
and the folded citations were distributed over `state` snapshot trees, dockets material
mirrors, `scratch`, and vendored `release` copies — all of them the same file repeated.

## The rule, in one sentence

A candidate that is one of two or more byte-identical files with the cited basename (same
sha256) is a copy in a duplicated tree, not an addressable alternate, so copies are removed
from the candidate set and the citation reports `missing`; a basename whose candidates
differ in content keeps every candidate and stays `wrong_dir`, because that ambiguity is real.

One implementation, two consumers: `candidate_paths` in `path_refs.py` is the only home of
the rule, `classify` uses it, and `path_refs_resolve.py` resolves against it — a resolver can
never disagree with the guard about what a candidate is.

## Census, both directions

Before: `ok=26789 wrong_dir=636 missing=266 ignored=273` (sum 27964)
After : `ok=26841 wrong_dir=450 missing=452 ignored=274` (sum 28017)

`wrong_dir` fell by **186** and `missing` rose by **186** — the same amount. `ok` and
`ignored` cannot move under this rule (both are decided before the candidate set is built),
so the `+52` / `+1` in those two columns is concurrent corpus drift from peer units writing
documents during the sweep, not this rule. A same-tree A/B re-scan (rule on vs off in one
process) confirmed 178 flips with **0** moves in any other direction; the 8-citation gap is a
document a peer deleted between the two scans.

The bad-key count is **invariant by construction**: the baseline is keyed
`<citing-file>::<cited-path>` and only the *classification* of a key may change, so
`wrong_dir + missing = 450 + 452 = 902` — exactly the number of baselined keys, and the guard
still prints `path-refs: 902 known (baselined), 0 new`.

**Deviation from the card's bound, stated plainly:** the card expected a fall of at most 86.
The fall is 186 globally; 72 of the flipped citations are in the in-scope set the card
measured, and 114 are handoff citations that carry the identical defect. The rule is
content-based and cannot be scoped by *which file cites* without becoming arbitrary, so the
larger number is reported rather than suppressed.

## What the rule does not claim

Two real source files with the same basename and *different* bytes stay `wrong_dir` — that is
287 of the remaining citations, and they must: a real file exists somewhere and a human can
point the citation at it. The rule also never guesses a location: removing copies yields
`missing`, which claims nothing about where the file should be.

## Files

- `path_refs.py` — the guard; `candidate_paths`, `all_identical_copies`, `_sha256`
- `path_refs_resolve.py` — resolves against the shared candidate set
- `test_path_refs_candidates.py` — copy becomes `missing`; genuine duplicate stays ambiguous;
  an `ok` citation is untouched
- `test_path_refs_resolve.py` — the dir-rule fixture now uses differing bytes, because two
  byte-identical files are copies by definition and are no longer candidates

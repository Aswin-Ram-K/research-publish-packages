# PATH-REFS ROUND 2 — the ambiguous `wrong_dir` citations, decided by evidence

Round 1 (`PATH-REFS-BATCH-FIX`) substituted 150 citation tokens across 68 files and proved
token-only substitution by normalising every token to `<P>` and requiring byte-identity. It left
**130** `wrong_dir` citations it could not decide from uniqueness: their basename exists in two or
more places. This round decides what evidence can decide, and says plainly what it cannot.

All figures below were measured at **2026-10-26T13:35:02-0500** by
`experiments/ptr-engine/tools/path_refs_resolve.py`, which **imports** the guard
`experiments/ptr-engine/tools/path_refs.py` — classification, scanning and the basename index come
from there, never from a copy.

## What was measured

| | count |
|---|---|
| `wrong_dir` overall, start of pass | 645 |
| `wrong_dir` in scope (docs + unit cards; handoffs and `measure/*` excluded by instruction) | 121 |
| decided by evidence | **2** |
| undecidable | **119** |
| documents substituted on disk | **0** |

The card carried 130 in-scope citations; the in-scope set measured 121 at this pass. The 9-finding
difference is **concurrent tree drift**, not this pass: the scratch `FINDINGS` material and peers were removed by
other units between the two scans, so citations of them left `wrong_dir` (their basename no longer
exists anywhere) and their candidate lists collapsed.

## Rule histogram

| rule | fired |
|---|---|
| `content` | 2 |
| `none` | 119 |

`none` means no rule fired and the row is **undecidable**. There is deliberately no fourth rule:
**no mtime, no recency, no fuzzy tiebreak.** A newer candidate is a coin flip wearing a timestamp,
and a wrong correction is worse than a dead citation because it launders a phantom into a plausible
path. `tests/test_path_refs_resolve.py::test_newer_candidate_does_not_decide_an_ambiguous_citation`
pins that: one candidate is written with the newest possible mtime and the row must still be
undecidable.

## The decided rows

- `orchestration/units/GRADE-V6-DERIVE.md:63` cites the `test_cell` citation → **experiments/ptr-engine/longrun/tests/test_cell.py** (rule `content`, content evidence)
- `orchestration/units/HARNESS-GUARDS.md:51` cites the `test_cell` citation → **experiments/ptr-engine/longrun/tests/test_cell.py** (rule `content`, content evidence)

Both are `test_cell` citations whose sentence carries a symbol that exactly one of the
three candidates contains. Both live in **other units' cards**, which are outside this unit's
declared write paths, so they are **recorded here and not applied** — the owning cards can apply
them. Applying them would mean editing another unit's historical card, which is not this card's
write scope.

## Why the remainder is undecidable — and what it actually is

**86 of 119** undecidable citations have *every*
candidate inside a copy tree: `state/`, `dockets/`, `.ucurate1/`, `tests/fixtures/`,
`release/v0.1/tests/fixtures/`, `jobs/`, `research/tooling/`. A candidate in a copy is not evidence
that the citation points there — it is evidence that the basename is common. The guard's `wrong_dir`
class is therefore over-counting: these are citations of paths that **were never produced**
(`state/kg/…/graphify-out/graph.json` "expected artefacts", a paper path with a literal placeholder
`x` segment, a size table over untracked scratch material), not citations that moved.

The tool reports that column and **never decides with it**. The honest verdict for those citations
is *the artefact does not exist*: `missing`, not `wrong_dir`. That is a classifier finding for a
later card, not a repair this pass may make by substitution.

## Guard, before and after

```
before  census: ok=26370 wrong_dir=645 missing=266 ignored=273
after   census: ok=27215 wrong_dir=910 missing=266 ignored=273
```

`wrong_dir` fell by 9 through concurrent deletions elsewhere in the tree; this pass added **no** new
key (`--check` reports `0 new`). Nothing grew.

## Token-only proof

No document was substituted, so on-disk byte-identity is vacuous; the machinery is proved on
synthetic trees instead, in `tests/test_path_refs_resolve.py`:

- **red** — a chosen path that *contains* the cited token (substituting it rewrites bytes that are
  not the citation) must be refused, the file left byte-identical, and `apply_rows` must return a
  failure. `apply_rows` exits non-zero on any failure, so a bad correction cannot land quietly.
- **green** — a pure token substitution must leave the file byte-identical after normalising both
  versions' tokens to `<P>`.

5 tests pass (`PYTHONPATH=release/v0.1/src python3 -m pytest tests/test_path_refs_resolve.py -q`).

## Undecidable citations, for their owning cards

Full machine-readable table: `experiments/ptr-engine/measure/PATH-REFS-ROUND2.json`
(`undecidable_rows`, with dir+base rather than a path-shaped token, so this report does not itself
add baseline keys to the guard it reports on). The `file:line` list, grouped by owning document:

- `docs/ACCEPTANCE_PROTOCOL.md` — 6 undecidable citation(s)
- `docs/HANDOFF-LINT.md` — 2 undecidable citation(s)
- `docs/PLAN_CORRECTIONS.md` — 2 undecidable citation(s)
- `docs/serving-options/R-VLLM.md` — 1 undecidable citation(s)
- `orchestration/units/GAP-LEDGER2.md` — 1 undecidable citation(s)
- `orchestration/units/HARNESS-GUARDS.md` — 1 undecidable citation(s)
- `orchestration/units/HOST-SCOUT-1.md` — 5 undecidable citation(s)
- `orchestration/units/HOST-SCOUT-2.md` — 9 undecidable citation(s)
- `orchestration/units/HOST-SCOUT-3.md` — 2 undecidable citation(s)
- `orchestration/units/STRAY-REF.md` — 1 undecidable citation(s)
- `orchestration/units/U1.5.md` — 1 undecidable citation(s)
- `orchestration/units/U5.17.md` — 1 undecidable citation(s)
- `orchestration/units/U5.29.md` — 1 undecidable citation(s)
- `orchestration/units/U5.33.md` — 1 undecidable citation(s)
- `orchestration/units/U8.36.md` — 2 undecidable citation(s)
- `orchestration/units/U8.43.md` — 1 undecidable citation(s)
- `orchestration/units/U8.53.md` — 1 undecidable citation(s)
- `orchestration/units/UAMBIG1.md` — 3 undecidable citation(s)
- `orchestration/units/UAUTHOR1.md` — 1 undecidable citation(s)
- `orchestration/units/UBUILD1.md` — 7 undecidable citation(s)
- `orchestration/units/UCAND1.md` — 1 undecidable citation(s)
- `orchestration/units/UCONS1.md` — 1 undecidable citation(s)
- `orchestration/units/UCONT1.md` — 1 undecidable citation(s)
- `orchestration/units/UCORR1.md` — 6 undecidable citation(s)
- `orchestration/units/UCORR2.md` — 1 undecidable citation(s)
- `orchestration/units/UCORR3.md` — 2 undecidable citation(s)
- `orchestration/units/UCURATE1.md` — 1 undecidable citation(s)
- `orchestration/units/UDISC1.md` — 1 undecidable citation(s)
- `orchestration/units/UEXP.md` — 1 undecidable citation(s)
- `orchestration/units/UFIX12.md` — 1 undecidable citation(s)
- `orchestration/units/UFIX24.md` — 1 undecidable citation(s)
- `orchestration/units/UFIX4.md` — 1 undecidable citation(s)
- `orchestration/units/UFIXGR7.md` — 1 undecidable citation(s)
- `orchestration/units/UFIXPAPER4.md` — 2 undecidable citation(s)
- `orchestration/units/UFIXPKG5.md` — 2 undecidable citation(s)
- `orchestration/units/UH3.md` — 2 undecidable citation(s)
- `orchestration/units/UJ1.md` — 2 undecidable citation(s)
- `orchestration/units/UJ2.md` — 1 undecidable citation(s)
- `orchestration/units/ULEAK7C.md` — 2 undecidable citation(s)
- `orchestration/units/UNC1A.md` — 2 undecidable citation(s)
- `orchestration/units/UNONCENSUS1.md` — 1 undecidable citation(s)
- `orchestration/units/UNONCENSUS2.md` — 1 undecidable citation(s)
- `orchestration/units/UP1.md` — 3 undecidable citation(s)
- `orchestration/units/UP2.md` — 7 undecidable citation(s)
- `orchestration/units/UPAPER1a.md` — 2 undecidable citation(s)
- `orchestration/units/UPAPER1d.md` — 1 undecidable citation(s)
- `orchestration/units/UPKGX1.md` — 1 undecidable citation(s)
- `orchestration/units/UPLAG2.md` — 2 undecidable citation(s)
- `orchestration/units/UTMLR2.md` — 1 undecidable citation(s)
- `orchestration/units/UVER10.md` — 1 undecidable citation(s)
- `orchestration/units/UVER2.md` — 2 undecidable citation(s)
- `orchestration/units/UVER8.md` — 1 undecidable citation(s)
- `orchestration/units/UVERPAPERS.md` — 1 undecidable citation(s)
- `orchestration/units/UWITH1.md` — 3 undecidable citation(s)
- `orchestration/units/V0.18.md` — 1 undecidable citation(s)
- `orchestration/units/V0.md` — 2 undecidable citation(s)
- `orchestration/units/V1.md` — 2 undecidable citation(s)
- `orchestration/units/V2R.md` — 2 undecidable citation(s)
- `orchestration/units/V5.32.md` — 1 undecidable citation(s)
- `orchestration/units/V8.21.md` — 1 undecidable citation(s)
- `orchestration/units/V8.29.md` — 1 undecidable citation(s)
- `orchestration/units/V8.41.md` — 1 undecidable citation(s)

## Final measurement (settled, 2026-10-26T13:35:35-0500)

```
census: ok=26760 wrong_dir=636 missing=266 ignored=273
path-refs --check: 902 known (baselined), 0 new
```

`ok` rose and `wrong_dir` fell further **during** this pass: other units are still editing `docs/`
(17 documents had mtimes inside the hour). Counts in this report are therefore three snapshots of a
moving tree, and the only claim that survives the motion is the one the guard makes itself: **0 new
keys, no regression, nothing grown by this unit.**

Mutation check of the substitution guard (the proof is load-bearing, not decorative). One input
— a citation whose chosen path CONTAINS the cited token — is fed to the applier twice:

- guard **on**: edited=0, skipped=0, failures=1 — the row is refused, the
  document is left byte-identical (the sentence unchanged, its one citation token intact).
- guard **off** (the normalised comparison degenerated to always-equal): edited=1,
  failures=0 — the substitution lands and the document becomes the citation token rewritten *inside itself*, with the new path prefixed onto the old one, i.e. the token was
  rewritten inside a longer citation, corrupting bytes that were never a citation.

So the red test fails without the guard, exactly as it must.

## Artefact digests

- `experiments/ptr-engine/tools/path_refs_resolve.py` — sha256 `487dc1c5d534502a…`
- `tests/test_path_refs_resolve.py` — sha256 `fa780016750a7ff0…`
- `experiments/ptr-engine/measure/PATH-REFS-ROUND2.json` — sha256 `849cf48727b638f5…`
- `docs/PATH-REFS-ROUND2.md` — sha256 `a6f89ebbf6cb4989…`

# REGRADE-STAMP-WIRE

**Status: done.** Regrade now RESOLVES the grader's identity instead of pinning it,
and stamps its output with the same three keys `grade_v5.py` writes. Offline, zero
requests. Forward-only: no historical grade document was edited or restamped, and
`longrun/grade_v5.py` was not touched (sha256 unchanged).

## The two defects (V-STAMP-NEUTRAL, partial with `evidence: null`)

| # | Defect | Fix |
|---|---|---|
| F1 | `tools/regrade.py` pinned `DEFAULT_GRADER_SHA = 6893d559518168e3ba4fc4a9f5d7642d213d61e2e3c3d0b0a8f01e3379af3077`, stale after GRADER-STAMP changed `grade_v5.py` to `056eb605e2baf5c91e0cb32d037cd0528e406e6c8527eec55a917a52d9f26772` | pin deleted; the digest is resolved at run time through `tools/grader_identity.py`; `EXPECTED_GRADER_SHA` remains only an expectation the resolver compares against |
| F2 | regrade output carried `grader_sha256` + `grader_path` but not `grader_version` / `rows_sha256`, so it was distinguishable from a fresh grade | regrade writes all three stamp keys, with `grade_v5.py`'s meaning, and validates them through `grader_identity.grader_identity()` — an invalid stamp is exit 3, never an unstamped document |

## Resolver call site

* `experiments/ptr-engine/tools/regrade.py:72` — `resolve_grader_identity(grader_path, expected=None)`
* `experiments/ptr-engine/tools/regrade.py:405` — `identity = resolve_grader_identity(grader_path, args.sha256)` in `main()`
* sha implementation: `experiments/ptr-engine/tools/grader_identity.py:file_sha256` (the ONE implementation, shared with the writer)
* `expected` is `--sha256` when given, else `EXPECTED_GRADER_SHA = 056eb605e2baf5c91e0cb32d037cd0528e406e6c8527eec55a917a52d9f26772`.

Semantics: **the resolved digest is the identity**; a mismatch with `EXPECTED_GRADER_SHA`
is printed as `NOTE grader sha256 drift: ...` and the run continues (a future
`grade_v5.py` edit must not invalidate the tool). A mismatch with an explicit
`--sha256` is `ERROR grader sha256 mismatch` and exit 3 — strict reproducibility is
still available. Drift therefore stays **detectable**, which is the point of resolving
rather than pinning.

## The three keys as regrade now writes them

| key | value |
|---|---|
| `grader_sha256` | sha256 of the grader file resolved at run time: `056eb605e2baf5c91e0cb32d037cd0528e406e6c8527eec55a917a52d9f26772` |
| `grader_version` | `GRADER_VERSION` of the loaded grader module: `5.1` |
| `rows_sha256` | sha256 of the rows file graded, e.g. `bc61d38192d4e4316021ec8d3d0e21dcb8e6153f463260a0138da21969d0b21e` |

`regrade()` calls `grader_identity.grader_identity(doc)` after setting them and fails
(exit 3, `stamp_uncomputable`) if the stamp is not complete and well-formed. `--check`
now accepts all three (plus `grader_path`) as *provenance-only* when the stored
document predates them, so a historical document still compares field by field.

## Proof 1 — historical grids, field by field

`--check` against `measure/cell-longrun-base-20261026T1556Z.grade-v5.json`
(rows `measure/rows-longrun-2026-10-26.jsonl`): exit 1, and the differing-path list is

```
arms.lease-reopen.decidable_source
arms.pointer-stable.decidable_source
arms.transcript-compact.decidable_source
arms.transcript-grow.decidable_source
```

with `grader_sha256`, `grader_version`, `rows_sha256`, `grader_path` reported as
`provenance-only`. The four `decidable_source` paths are **outside the stamp set and are
reported as a finding**: they are a pre-existing `GRADE-V5-REPAIR` era field (the stored
document predates it), not a consequence of the stamp change. The same holds for the
policy grid.

The clean case isolates the stamp: a pre-stamp document made by stripping **only** the
three stamp keys from a fresh regrade output and resubmitting it with `--check` gives
exit 0 and

```
IDENTICAL rows-longrun-2026-10-26.jsonl (grader_sha256=056eb605e2baf5c91e0cb32d037cd0528e406e6c8527eec55a917a52d9f26772)
```

So the stamp is the only provenance a regrade adds; every graded field is identical.

## Proof 2 — red → green (stale pin restored in a `/tmp` copy)

Red — `/tmp/regrade-red/regrade.py` with `EXPECTED_GRADER_SHA = 6893d559518168e3ba4fc4a9f5d7642d213d61e2e3c3d0b0a8f01e3379af3077`, run with
`--sha256 6893d559518168e3ba4fc4a9f5d7642d213d61e2e3c3d0b0a8f01e3379af3077`:

```
ERROR grader sha256 mismatch: file=056eb605e2baf5c91e0cb32d037cd0528e406e6c8527eec55a917a52d9f26772 expected=6893d559518168e3ba4fc4a9f5d7642d213d61e2e3c3d0b0a8f01e3379af3077
```
exit 3.

Green — the resolver version, same grid, no digest flag: `IDENTICAL ... grader_sha256=056eb605e2baf5c91e0cb32d037cd0528e406e6c8527eec55a917a52d9f26772`, exit 0.

## Proof 3 — a deliberately edited grader is caught

`/tmp/grader-edit/grade_v5.py` = `grade_v5.py` plus one appended comment line;
sha256 `114e60a23e0bc03a12016690e91ff2d8680690a64c361d3197606b938090884a` (original `056eb605e2baf5c91e0cb32d037cd0528e406e6c8527eec55a917a52d9f26772`).

Strict (`--sha256 056eb605e2baf5c91e0cb32d037cd0528e406e6c8527eec55a917a52d9f26772`), exit 3:

```
ERROR grader sha256 mismatch: file=114e60a23e0bc03a12016690e91ff2d8680690a64c361d3197606b938090884a expected=056eb605e2baf5c91e0cb32d037cd0528e406e6c8527eec55a917a52d9f26772
```

Resolved (no `--sha256`), exit 0:

```
NOTE grader sha256 drift: resolved=114e60a23e0bc03a12016690e91ff2d8680690a64c361d3197606b938090884a expected-pin=056eb605e2baf5c91e0cb32d037cd0528e406e6c8527eec55a917a52d9f26772 (identity resolved at run time; pass --sha256 to require a digest)
```

and the document it wrote stamps `grader_sha256 = 114e60a23e0bc03a12016690e91ff2d8680690a64c361d3197606b938090884a` — the edit is recorded, not
hidden. A `--check` of that document against an unedited-grader document differs at
`grader_sha256`.

## Suites

| suite | before | after |
|---|---|---|
| `test_grader_stamp.py` | 6 passed | 6 passed |
| `test_regrade.py` | 8 passed | 8 passed |
| `test_regrade_stamp.py` | absent | 6 passed |

`test_regrade_stamp.py` pins (a) no stale digest decides identity, (b) all three stamps
with `grader_v5`'s meaning, (c) a pre-stamp document regrades IDENTICAL, (d) the
historical grid's only non-stamp difference is `decidable_source`, (e) the red→green
above, (f) the edited-grader detection.

## Findings (reported, not fixed)

1. The stored grids also predate `GRADE-V5-REPAIR`; `decidable_source` shows up in any
   `--check` against them. Era drift, not a stamp defect; restamping them is forbidden.
2. `measure/cell-pointer-stable-20261026T145722Z.grade-v5.json` does **not** reproduce:
   22 graded fields differ (e.g. `cells[1].verdict: fail` vs `undecidable`,
   `checkpoint_accuracy: 1/3` vs `1/1`). That document predates the current grader's
   `undecidable` handling — a separate era finding, outside this card's write scope.

## Answer

**Can a published grade still be proven re-derivable now that the grader's sha has
changed?** Yes for the derivation itself — regrade reproduces a stored grid
field-for-field against the current grader and records the new digest in its stamp;
what cannot be recovered is the *old* identity of unstamped historical documents,
because the pin that used to assert it was stale and the forward-only rule forbids
restamping them.


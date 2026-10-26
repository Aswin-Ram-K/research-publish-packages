# VERIFICATION_REPORT_AUTHORITATIVE_TREE — VUFIXTREE1 verifies UFIXTREE1

Verifier: **VUFIXTREE1** (independent unit; re-ran every measurement in copies).
Subject: UFIXTREE1's claim that `scratch/uneutral10/package` is the authoritative release tree.
Verdict: **partial** — the decisive conclusion (re-pin to `scratch/uneutral10/package`; the current
`scratch/urecut1/package` pin is stale) is independently reproduced and the one-line re-pin is safe.
Several *supporting* claims are overstated or mis-sourced, and the uniqueness claim does not survive a
broader search of `scratch/`.

Bound: 20 tool calls; used 12 (33 subprocess tool invocations). Every candidate was copied into
`scratch/vufixtree1/copies/**` / `copies2/**` and run there — no candidate tree, the build script, or
anything under `papers/` was edited. `/home/zer0null/Duval` was never touched (no git at all).

## 1. My own table — cell-by-cell against UFIXTREE1's

Method: `cp -r` each tree, then in the copy `python3 verify/recompute-claims.py`,
`python3 second-labeller/parse_fixture.py`, `python3 second-labeller/compare.py`; literal exit codes
recorded; κ from `compare.py` and from `second-labeller/metrics.json`. Logs:
`scratch/vufixtree1/logs/<tree>__<tool>.log`.

| tree | rc | PRESERVED | route A κ | A/B mutual | my verdict |
|---|---|---|---|---|---|
| `scratch/urecut1/package` | 0/0/0 | True | 0.32520740993294694 | 0.3526315789473684 | self-consistent but **STALE** vs paper |
| `scratch/uneutral10/package` | 0/0/0 | True | 0.3248813212427869 | 0.3684210526315789 | matches paper |
| `scratch/ufix31/pkg` | 1/0/0 | False | 0.31988636363636364 | 0.3473684210526316 | FAIL |
| `scratch/utool1/tree-six` | 0/0/0 | True | 0.32520740993294694 | 0.3526315789473684 | stale |
| `scratch/udtag1/tree-five` | 0/1/1 | True | 0.32520740993294694 | 0.3526315789473684 | broken tools |

**All 15 cells of UFIXTREE1's table reproduce exactly** (rc buckets, PRESERVED, both κ columns).
`route B κ = 0.9013584840356494` in all five; `routeA.agreement = 0.34210526315789475` in four of five
(ufix31: `0.3368421052631579`).

Failure detail (measured, not inferred):
- `ufix31/pkg`: recompute rc=1, prints `MISMATCH` on route-A (`shipped=0.31988636363636364` vs
  recomputed `0.3252`) and A/B mutual (`shipped=0.3473684210526316` vs `0.3526`), then
  `ALL CLAIM NUMBERS PRESERVED: False`.
- `udtag1/tree-five`: recompute rc=0 / True, but
  `FileNotFoundError: .../second-labeller/reflex-decisions.sandbox.ts` (parse_fixture, rc=1) and
  `FileNotFoundError: .../second-labeller/cases.json` (compare, rc=1).

**No candidate was unexecutable**: all five ran; two tools of `udtag1/tree-five` exited 1 on missing files.

## 2. The published values — read out of the paper by me

`papers/encoder-crossover-190/CLAIMS.md`:
- `:108` — `| second-labeller κ | 0.9014 (≈0.90) | ... | .passes["labelsB.json"].kappa = 0.9013584840356494 |`
- `:109` — `| second-labeller disagreements | 18 / 190 | ... | .disagreements_count_routeB = 18 |`
- `:110` — `| deterministic lexical route (routeA) κ | 0.3249 | ... | .routeA.kappa = 0.3248813212427869, agreement 0.3421 |`
- `:111` — `| AB mutual agreement | 0.3684 | ... | .passes["labelsB.json"].AB_mutual_agreement |`

So the paper publishes full precision for the two κs but only **4 dp** for `agreement` (0.3421) and
A/B mutual (0.3684). UFIXTREE1's claim 2 attributes the *full-precision* `0.34210526315789475` and
`0.3684210526315789` to `:108-111`; those exact strings are **not in the paper** — they are the tree's
`metrics.json` values. This is a sourcing defect, not a numeric one: `0.3421→0.34210526315789475` and
`0.3684→0.3684210526315789`. The two values that actually discriminate are route-A κ and A/B mutual
(agreement is identical in 4 of 5 trees; route-B κ in all 5).

`uneutral10/package` re-derived accordingly: claim **supported** (paper = 0.3248813212427869 /
0.3684, tree = same; urecut1 ships 0.32520740993294694 / 0.3526315789473684, which contradict `:110`
and `:111`).

## 3. Pin line (claim 3) — checked on disk

`orchestration/units/UBUILD1.build.sh:134`:
`PROMOTED_SAN_SRC="$SRC/scratch/urecut1/package"`
The claimed replacement is exact. **But it is not the only line naming that tree inside the script**:
`:39` — `#   THE PROMOTED DEFAULT (UWIRE2) is $SRC/scratch/urecut1/package — the` (comment; line 40
continues the rationale and cites `3,317`). Functionally a one-line substitution; textually **two**
edits, one of them comment-only. (Outside the script, `tests/test_build_wiring.py:10` also quotes the
old path in its docstring; the test derives the path from the script, so it needs no edit.)

## 4. SHIP_STAGED (claim 4) — tested, not accepted

- Path sets, contents excluded: `diff` of sorted relative paths of `scratch/urecut1/package` and
  `scratch/uneutral10/package` → **`PATH SETS IDENTICAL`** (both 29 files).
- `SHIP_STAGED` (lines 178–214) holds **29** entries, matching the 29-file set exactly → no
  re-derivation is needed for the re-pin, **confirmed**.
- Not checked: the accuracy of the hard-fail **hit-count annotations** above it → `unverified`.

## 5. Wiring test (claim 5) — re-run against a re-pinned copy

- As-is: `PYTHONPATH=src python3 -m pytest tests/test_build_wiring.py -q` → **11 passed in 0.05s**.
- Against a re-pinned copy (I wrote `scratch/vufixtree1/UBUILD1.repin.sh` via `sed` on line 134, then
  `UWIRE3_BUILD_SCRIPT=$PWD/scratch/vufixtree1/UBUILD1.repin.sh PYTHONPATH=src pytest ...`) →
  **11 passed in 0.05s**. Red→green not re-derived by me (the guard is a wiring/path guard and stayed
  green both ways); the claim "stays green" is **verified**.
  (A bare `python3 -m pytest` fails in `tests/conftest.py:19` with `ModuleNotFoundError: No module
  named 'resextract'` — `PYTHONPATH=src` is required; not a defect of the tree.)

## 6. Fixture digest (claim 6) — verified, and non-discriminating

All five trees' `recompute-claims.py` print
`fixture correctness digest: c7696edc0e71d83faafc2e489925788e0f36c6af94913674f8953718352c9a55`.
It is **computed at runtime** (the literal appears in no file: `grep -rl` over all five trees = empty;
no file hashes to it). It is therefore genuinely identical in all five and genuinely cannot discriminate
among them. **The verdict survives without it** — it is a constant; every discriminating measurement here
is a kappa/agreement value and an exit code.

## 7. Adversarial: a sixth candidate that also reproduces the published values

Yes. Searching all 29-file tree roots under `scratch/` that contain `verify/recompute-claims.py` and
contain the published route-A κ `0.3248813212427869`, then running all three tools in copies:

| tree | rc | PRESERVED | routeA κ | agreement | routeB κ | A/B mutual |
|---|---|---|---|---|---|---|
| `scratch/uneutral9/package` | 0/0/0 | True | 0.3248813212427869 | 0.34210526315789475 | 0.9013584840356494 | 0.3684210526315789 |
| `scratch/uneutral10/before` | 0/0/0 | True | (identical to uneutral9/package — `diff -rq` clean) | | | |
| `scratch/uver32/after`, `idem1`, `idem2` | 0/0/0 | True | (identical to uneutral9/package) | | | |
| `scratch/uver32/inject` | 0/0/0 | True | same four values | | | |

`scratch/uneutral9/package` is a **distinct** 29-file tree (differs from `uneutral10/package` in
`fixture/fixture-190.json`, `fixture/reflex-decisions.ts`, `MANIFEST.json`,
`second-labeller/blinded_cases.json`, `second-labeller/cases.json`, `verify/recompute-claims.py`) and it
reproduces **all four** published values with exit 0/0/0 and PRESERVED True. `scratch/uneutral10/before`
and the `scratch/uver32/*` trees are byte-identical copies of it (`uver32/inject` differs in 7 entries but
carries the same four values).

**Therefore "the only tree" is true only within the enumerated five; it is false as a statement about
`scratch/`.** The pin choice is *forced by recency/lineage* (uneutral10 supersedes uneutral9 and carries
the corrected `recompute-claims.py`), not by uniqueness of reproduction.

## 8. Defect in the winner's own tool (found while re-running it)

`scratch/uneutral10/package/verify/recompute-claims.py` prints:
```
route-A kappa: published=0.3252   tree=0.3248813212427869     reproduced=True cite=papers/encoder-crossover-190/CLAIMS.md:108
A/B mutual agreement: published=0.3526   tree=0.3684210526315789     reproduced=False cite=papers/encoder-crossover-190/CLAIMS.md:109
```
- It embeds **stale** "published" constants (`0.3252`, `0.3526`) that appear nowhere in CLAIMS.md.
- It cites `:108`/`:109` for values that are actually at `:110`/`:111` (`:108` is route-B κ, `:109` is
  the disagreement count).
- Its `reproduced=False` for A/B mutual **does not** feed the aggregate: `ALL CLAIM NUMBERS PRESERVED:
  True` tests only recompute-vs-shipped self-consistency, not paper truth. (This is also why
  `urecut1/package` prints `True` and `OK` on all four while shipping values that contradict the paper.)
- `urecut1/package` and `uneutral10/package` do **not** ship the same tool: their
  `verify/recompute-claims.py` differ at lines 115–138 (uneutral10 adds the `PUBLISHED_STALE`
  declared-delta block).

Net effect: UFIXTREE1's claim that uneutral10's "own shipped tools reproduce all four published values"
is **not literally true** — the tool itself reports one of the four as `reproduced=False`. The tree's
*data* reproduces the paper; the tree's *checker* is stale for the "published" side.

## Findings

**contradicted**
1. Claim 2's sourcing: `0.34210526315789475` and `0.3684210526315789` are tree values, not paper text;
   `CLAIMS.md:108-111` prints `0.3421` and `0.3684`.
2. `uneutral10/package/recompute-claims.py` cites `CLAIMS.md:108/:109` for route-A κ / A/B mutual, but
   those lines are route-B κ and the disagreement count; the values are at `:110`/`:111`.

**overstated**
1. "The **only** tree … that reproduces all four published values" — false beyond the five candidates:
   `scratch/uneutral9/package` (and its byte-identical copies `scratch/uneutral10/before`,
   `scratch/uver32/{after,idem1,idem2,inject}`) also reproduces all four with rc 0/0/0 / PRESERVED True.
2. "…whose own shipped tools reproduce all four published values" — uneutral10's own tool prints
   `A/B mutual agreement … reproduced=False`; only the aggregate (self-consistency) is True.
3. "The exact pin line … at `:134`" as a **one-line** substitution — line `:39` is a second, comment-only
   reference to the same tree inside the same script.
4. "PRESERVED True / all-tools-exit-0" as a discriminator: `urecut1/package` and `utool1/tree-six` also
   score 0/0/0 + True and print `OK` on all four, yet ship stale values. The discriminator is the value
   columns, as UFIXTREE1's own verdicts imply.

**not_reproduced**
1. The four published values as *full-precision strings sourced from the paper*: only the two κs are
   printed at full precision in `CLAIMS.md`; agreement and A/B mutual are published at 4 dp.
2. `uneutral10`'s tool-level claim of full reproduction (its own `reproduced=False` line).

**unverified**
1. `SHIP_STAGED`'s hard-fail hit-count annotations (lines ~175–177) were not re-measured; I verified only
   that the path set is identical and that the 29 listed entries match the 29 files on disk.
2. Red→green of `tests/test_build_wiring.py` under a reverted re-pin (I confirmed green both as-is and
   with the re-pinned copy; I did not construct a red baseline).

## Is the one-line re-pin safe to apply?

**Yes.** `scratch/uneutral10/package` and `scratch/urecut1/package` have identical 29-file path sets; all
29 `SHIP_STAGED` entries are present; `tests/test_build_wiring.py` is 11/11 green against a re-pinned copy
of the script; and the re-pinned tree's data matches the two discriminating published values. Recommended
scope of the edit: line `:134` (functional) **plus** line `:39` (comment) so the script's own rationale no
longer names the stale tree. A separate unit applies it; VUFIXTREE1 edited nothing.

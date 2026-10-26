# BUILD PIN CHANGE — promoted tree `urecut1` → `uneutral10`

Unit: **UFIXPIN1**. File changed: `orchestration/units/UBUILD1.build.sh` (968 lines).

| | sha256 |
|---|---|
| before (byte copy `scratch/ufixpin1/UBUILD1.build.sh.bak`) | `bbf5a52cb1983a0a0f3b6adf8aeaa1ab87e0dc3eabc97c21563e5e6b0512c372` |
| after | `7bd71f8a3e7450c3a16394af31171c1fdb5448fe9a8a843788a9df63a81a07e5` |

Exactly two edits. Both before-strings asserted unique (`grep -n urecut1` → 2 hits total,
one per edit); no other line touched. `bash -n` → OK (exit 0). `diff` vs the byte copy shows
only these two hunks.

## Edit 1 — the functional edit (line 134)

before:
```
PROMOTED_SAN_SRC="$SRC/scratch/urecut1/package"
```
after:
```
PROMOTED_SAN_SRC="$SRC/scratch/uneutral10/package"
```

## Edit 2 — the stale comment (line 39)

before (actual text read from disk, not guessed):
```
#   THE PROMOTED DEFAULT (UWIRE2) is $SRC/scratch/urecut1/package — the
```
after:
```
#   THE PROMOTED DEFAULT (UWIRE2) is $SRC/scratch/uneutral10/package — the
```

Comment lines 40–42 still carry UWIRE2's measurements (3,317 residual identifiers, 44,056,
12.4x; gate 95,606 → 29,936), which were measured over the `urecut1` package. The unit card
authorised only the tree *name* change, so those figures were left as authored — flagged as a
non-blocking observation, not silently "fixed".

## Why `uneutral10` — and explicitly NOT uniqueness

- The pinned old tree is wrong. `scratch/urecut1/package` reports route A κ
  `0.32520740993294694` and A/B mutual `0.3526315789473684`, while the manuscript publishes
  `0.324881` / `0.368421` (4 dp `0.3249` / `0.3684`, `papers/encoder-crossover-190/CLAIMS.md:108-111`).
- An independent verifier re-ran all five candidate trees in copies and confirmed **all fifteen
  cells** reproduce, and that the two 29-file trees have an **identical path set** — so
  `SHIP_STAGED` needs no re-derivation.
- `scratch/uneutral10/package` is **not** the unique reproducer: `scratch/uneutral9/package`
  (distinct in 6 files) also reproduces, as do several identical copies.
- The correct reason is provenance, not uniqueness: `uneutral10` is the **latest link in the
  neutralisation chain** (it renamed the last case-variant survivors and reworded one comment,
  moving no diagnostic), and its survivor set is the one the author's own deliberate-residue
  record cites in `strategy/CASE_VARIANT_SETTLEMENT.md` §7.

## Build — scratch destination (never the real one), `COMMIT_DATE=2026-10-15T00:00:00+00:00`

Command: `DEST="$PWD/scratch/ufixpin1/dest/research-publish-packages" bash orchestration/units/UBUILD1.build.sh`
Log: `scratch/ufixpin1/build.log`. Literal measured lines:

```
SAN_SRC WIRING: tree=/home/zer0null/reserach extarctor/scratch/uneutral10/package promoted_default=yes
  staged 29 file(s): 29 kept, 0 dropped
  ship-list enforced: 29 staged file(s) present
  never-ship list enforced: 15 names checked absent
  anchor 907fa39 present in 4 file(s) — kept deliberately
GATE RESULT: FAIL -- 1133 out-of-vocabulary token(s).
BUILD COMPLETE — the exclusion gate FAILED (exit 1).
```

- emitted file count on disk: **109** (`find scratch/ufixpin1/dest/research-publish-packages -type f | wc -l`)
- process exit: **1** (gate FAIL expected by design; `BUILD_EXIT=1`)

## Tests

- `PYTHONPATH="$PWD/src:$PWD" python3 -m pytest tests/test_build_wiring.py -q`:
  **11 passed** in 0.05s (exit 0). Bare `python3 -m pytest` fails at collection because
  `tests/conftest.py:19` imports `resextract`; adding `src` to `PYTHONPATH` resolves it.
- direct-run equivalent `PYTHONPATH="$PWD/src:$PWD" python3 tests/test_build_wiring.py`:
  **11 passed** in 0.05s (exit 0).
- stale-pin red test (a): a copy re-pinned at the OLD tree
  (`scratch/ufixpin1/UBUILD1.build.sh.oldpin`, `PROMOTED_SAN_SRC="$SRC/scratch/urecut1/package"`)
  via `UWIRE3_BUILD_SCRIPT` → **11 passed** (exit 0). It does **not** go red: `urecut1/package`
  has an identical 29-file path set, so this guard cannot distinguish the two trees by path set.
  Recorded as measured, not as a red result.
- red test (b) — the guard does bite: same script pointed at a scratch tree missing one shipped
  file (`results/baselines.json`) → **1 failed, 10 passed** (exit 1),
  `FAILED tests/test_build_wiring.py::test_ship_list_is_exactly_the_promoted_tree_as_it_is`
  with `only in SHIP_STAGED: ['results/baselines.json']`. Green re-confirmed afterwards:
  11 passed.

## SHIP_STAGED

Unchanged. Exactly **29** names parsed from lines 178–214 (comments stripped); all 29 exist in
`scratch/uneutral10/package` (`missing_flag=0`). Copy of the parsed list:
`scratch/ufixpin1/ship_staged.txt`.

## Scope / constraints respected

No writes under `papers/`, `repro/`, or any `scratch/*/package` tree (the scratch trees were
only read; `scratch/ufixpin1/redsrc` is a UFIXPIN1-owned copy outside any `*/package` source).
`/home/zer0null/Duval` was never touched and no git verb was run.

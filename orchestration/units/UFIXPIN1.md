# UFIXPIN1

STATUS: done

## Purpose
Apply exactly two anchor-based edits to `orchestration/units/UBUILD1.build.sh` re-pinning the
promoted release tree from `scratch/urecut1/package` to `scratch/uneutral10/package`, then verify
with `bash -n`, a scratch-DEST build, and `tests/test_build_wiring.py`.

skeleton_written_first: yes (card and handoff written before the byte copy and before any edit)

## Hard bound
12 tool calls. Used 11.

## Declared write paths (no clash)
- orchestration/units/UBUILD1.build.sh
- scratch/ufixpin1/**
- orchestration/units/UFIXPIN1.md
- orchestration/handoffs/UFIXPIN1.json
- strategy/BUILD_PIN_CHANGE.md

## The two edits (line 134 functional, line 39 comment)
Anchor-based, each before-string asserted unique before replacing:
- `PROMOTED_SAN_SRC="$SRC/scratch/urecut1/package"` -> `PROMOTED_SAN_SRC="$SRC/scratch/uneutral10/package"`
- `#   THE PROMOTED DEFAULT (UWIRE2) is $SRC/scratch/urecut1/package — the` ->
  `#   THE PROMOTED DEFAULT (UWIRE2) is $SRC/scratch/uneutral10/package — the`

## Evidence
Full record: `strategy/BUILD_PIN_CHANGE.md`; build log `scratch/ufixpin1/build.log`.

- sha256 before `bbf5a52cb1983a0a0f3b6adf8aeaa1ab87e0dc3eabc97c21563e5e6b0512c372`
  -> after `7bd71f8a3e7450c3a16394af31171c1fdb5448fe9a8a843788a9df63a81a07e5`
- `bash -n` OK; `diff` vs byte copy shows only the two hunks; no `urecut1` left in the script
- build (scratch DEST, exit 1): wiring line names `scratch/uneutral10/package promoted_default=yes`;
  `staged 29 file(s): 29 kept, 0 dropped`; `ship-list enforced: 29 staged file(s) present`;
  `never-ship list enforced: 15 names checked absent`; `anchor 907fa39 present in 4 file(s)`;
  `GATE RESULT: FAIL -- 1133 out-of-vocabulary token(s).`; 109 emitted files
- `PYTHONPATH=src:. python3 -m pytest tests/test_build_wiring.py -q` -> 11 passed;
  direct run -> 11 passed
- stale-pin copy at old tree -> 11 passed (GREEN, because the two trees share an identical 29-file
  path set); true red produced by a copy whose tree lacks `results/baselines.json` -> 1 failed,
  10 passed
- SHIP_STAGED unchanged: 29 names, all 29 present in `scratch/uneutral10/package` (missing_flag=0)

## Rationale recorded
`uneutral10` is chosen as the **latest link in the neutralisation chain** and because its survivor
set is the one cited in `strategy/CASE_VARIANT_SETTLEMENT.md` §7. It is **not** claimed unique:
`scratch/uneutral9/package` and identical copies reproduce the published values too.

## Notes / remainder
Comment lines 40–42 still carry UWIRE2's urecut1-era measurements (left as authored; not in scope).

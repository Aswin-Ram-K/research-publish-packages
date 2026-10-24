# FIX-G3BANDS — correct the two understated bands and pin them so the guard bites

**Status: done (contract items 1–5 executed, verified).** Card `f8c49d19-39f3-4480-a9b2-0065d70e0261`,
workspace-write, bound 40 tool calls.

## Why this unit exists

`V-G3FOLD2` re-derived C62 from `cells/G3-LIMIT-V2/rows.jsonl` and confirmed the headline numbers,
but found that **two band endpoints in the package's prose were computed over a subset of the
rows** — so the paper published a narrower range than its own data. Its verdict could not be
persisted (its card was `read-only`, and under approvals-disabled the write is denied), which is
why the same finding now also appears as a process rule in `AGENTS.md`.

## The two bands

| Band | Published | Correct | Why the old value was short |
|---|---|---|---|
| Boundary turn, uncached | **1,826–2,972** | **1,826–3,033** | 2,972 is only `F-ptr`'s **first** compaction. The 32k arms fire twice; the second-compaction rows reach 2,808–3,033. |
| Baseline window drop | **1,236–1,246** | **1,236–1,321** | 1,246 is one drop row. There are **six**: the 32k baseline drops twice — 1,236 at turn 71 and 1,320 at turn 141 (pointer twin 1,237 / 1,321). |

Sites corrected (found by grep for the endpoint strings, not guessed): `CLAIMS.md:190`,
`EVIDENCE.md:216`, `MANUSCRIPT.md:57` (abstract), `MANUSCRIPT.md:566` (§10 rule 5).

## Why the guard stayed green

C62 pinned `baseline_drop_uncached` against each arm's **first** drop turn only
(`drops.get(first)` in `c62()`), and exposed no aggregate for either band. A wrong aggregate in
prose therefore had nothing to fail against.

## Pins added (derived, not hand-copied)

`c62()` now computes, over **all** rows rather than per-arm firsts:

```python
boundary_all = [int(r["uncached_tokens"]) for r in rs if r.get("compacted_this_turn")]
drop_all = [int(r["uncached_tokens"]) for r in rs
            if r.get("trigger_reason") == "sliding_window_drop"]
```

and exposes `boundary_turn_uncached_min` 1826, `boundary_turn_uncached_max` 3033,
`boundary_turn_rows` 18, `baseline_drop_uncached_min` 1236, `baseline_drop_uncached_max` 1321,
`baseline_drop_turns` 6 — all pinned in `EXPECTED["C62"]`. `recompute.py C62` → **PASS 29/29**.

## Red→green (each pin reverted individually, one at a time)

```
RED A  boundary_turn_uncached_max 3033 -> 2972
  FAIL boundary_turn_uncached_max  recomputed=3033  paper=2972
  FAIL  28/29 values match
RED B  baseline_drop_uncached_max 1321 -> 1246
  FAIL baseline_drop_uncached_max  recomputed=1321  paper=1246
  FAIL  28/29 values match
GREEN  both restored                              PASS 29/29 values match
```

A first attempt at this transcript was **contaminated and discarded**: the temporary backup file
disappeared, the chained restore silently no-opped, and RED B still showed RED A's failure. The
pins were re-verified by `grep` before re-running, and the clean run above reverts each pin inline.

## Caveats added to `MANUSCRIPT.md` §11

- **Bimodality**: post-boundary median Δ is **10 / 5 / 7** for 32k `S` / `S-ptr` / `F-ptr` versus
  **836–900** for the other nine arm-instances; those three arms sit at their baseline on a typical
  turn and their means are carried by a minority of turns. "The cheap arms" is a mean effect.
- **n**: 64k `F-k800` covers **27** post-boundary turns against 47 for the other 64k arms.

## Also in this pass (beyond the card's two bands — declared, not smuggled)

The "+134.6 to +747.2 uncached tokens per turn" figure was also a range of twelve **per-arm means**,
not per-turn values: per turn the segment runs **−927 to +5,473** and **all twelve** arms carry a
turn below baseline. Corrected in the abstract, §6a, §10 rule 5, `CLAIMS.md:190`, `PACKAGE.md:58`,
`EVIDENCE.md:205`, `GAPS.md:65`; pinned (`post_turn_delta_min/max`, `post_turns_below_zero`,
`post_turn_band`, `post_steady`, `post_transitions`) and guarded by the new
`tests/test_paper_g3_bands.py` (13 tests, measured red→green 2 failed → 13 passed).

## Verification

```
.venv/bin/python papers/context-cache/recompute.py all        -> 59 claims checked, all match ; GRID GUARD PASS 7/7
.venv/bin/python papers/context-cache/verify_package.py       -> PASS — 62 claims, 62 mapped 1:1, UNVERIFIED: none   (exit 0)
pytest paper guards + handoff/hygiene guards                  -> 68 passed
pytest tests/ (full)                                          -> 1 failed, 1157 passed, 1 skipped
```

The single suite failure is `tests/test_kg_policy.py::test_real_target_config_declares_the_decision`
(`PolicyWideningError` on `.lane-j-scratch/*.md`), **pre-existing and unrelated** — it fails
identically with this unit's new test file ignored.

**Zero live requests. No target repo touched.**

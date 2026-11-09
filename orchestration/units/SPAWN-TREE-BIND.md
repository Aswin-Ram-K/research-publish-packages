# SPAWN-TREE-BIND — close D5 (tree binding) and D6 (refusal doc drops instrumentation)

**Status: done.** Precondition held: `TRANCH1-DRYRUN` handoff `status=done` and the
pinned `cell.py` sha was still `b549e45e…` when this unit started (it was re-hashed
before and after; nothing else had moved it).

## Objective
1. **D5** — `cell.py` writes `cell_sha256`, `spawn_record_sha256`, `argv`, `tree_sha`
   (`unstamped` when the tree has no commit) into the refusal record;
   `spawn_record.validate_refusal()` requires them and compares the two shas against the
   files named by `--cell-path` / `--spawn-record-path` (defaults: the on-disk pair).
2. **D6** — the refusal writer emits `instrumentation` (one record shape via
   `SpawnRecord.as_dict()`), so an on-disk refusal passes the validator with no repair
   helper.
3. Keep D2/D3/D4 closed — their 8 tests unmodified and green.

## Hard rules observed
`{2,3,4,8,12}` coverage, duplicate-key rejection and `--observed-from-syscall` untouched;
no runner live path, no `run_longrun.py`, no rows/grade file, no `docs/EXIT-CODES.md`;
offline, zero inference requests; no `ask_user_question`.

## Bound
30 tool calls (used 21).

## Declared write paths
`experiments/ptr-engine/longrun/cell.py` ·
`experiments/ptr-engine/longrun/spawn_record.py` ·
`experiments/ptr-engine/longrun/tests/test_spawn_tree_binding.py` (new) ·
`docs/GATE-CHAIN.md` · `orchestration/units/SPAWN-TREE-BIND.md` ·
`orchestration/handoffs/SPAWN-TREE-BIND.json` ·
`orchestration/journals/SPAWN-TREE-BIND.jsonl`

## Result
- `cell.py`: `b549e45e…c296937488` → `e24e867b…6edf013`.
- `spawn_record.py`: `8bb17349…e8ba4bca` → `eba15471…7de8fe07c`.
- New tests (5, all green; red→green quoted in the handoff):
  `test_d5_matching_tree_is_accepted`,
  `test_d5_record_without_binding_keys_is_refused`,
  `test_d5_historical_record_against_permissive_tree_is_refused`,
  `test_d5_unstamped_tree_is_labelled_not_invented`,
  `test_d6_refusal_document_carries_instrumentation`.
- `experiments/ptr-engine/longrun/tests/test_spawn_tree_binding.py` 5 passed; `experiments/ptr-engine/longrun/tests/test_spawn_classification.py`
  18 passed (unchanged).

## Design note (learned)
`tree_sha` is read from `.git/HEAD` → `refs` → `packed-refs` **as files**. The first
implementation called `git rev-parse` via `subprocess.run`, and the sitecustomize oracle
counted that recorder spawn as an undeclared spawn — `test_a` and `test_6` went red with
`declared 1 spawn(s) vs recomputed 2`. A recorder must not spawn: it is the thing being
counted.

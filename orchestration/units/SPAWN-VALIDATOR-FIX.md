# SPAWN-VALIDATOR-FIX — done

**Status:** done · 15 / 24 tool calls · verdict row PASS at `f17663d1`

## The defect (from `orchestration/handoffs/V-SPAWN-DECLARE.json`, D1)
`validate_refusal()` returned `ok=True` for a published record with no `spawns` list and no
declaration block: an empty or truncated record was accepted as proof. Verbatim hint:
*"harden validate_refusal: it must reject a published record with no spawns/declaration
block …; make the oracle equivalence the acceptance criterion, not the record's own
validation.ok"*.

## What changed
- `experiments/ptr-engine/longrun/spawn_record.py` — `validate_refusal(published, exit_code=None,
  observed=None)` now **recomputes**: per-purpose counts from the record's own instrumented
  `spawns` entries are compared with every declared count (`counts`, `runner_launch`,
  `preflight_self_check`), and `observed` (raw `subprocess.Popen` constructions from the
  `sitecustomize` tripwire) is the acceptance criterion. It rejects (1) no `spawns` key,
  (2) `spawns: []` + no declaration block ("empty claim"), (3) a declaration naming no phase
  (or an unknown phase), (4) any declared-vs-recomputed disagreement ≥1 naming the pair and
  exit code, (5) `runner_launch` on a refusal exit in `{2,3,4,8,12}`. A self-reported
  `validation.ok: true` contradicted by recomputation is itself a failure. Added CLI
  `--validate FILE --exit-code N [--observed N]` → 0 ok / 1 rejected / 2 unreadable.
- `experiments/ptr-engine/longrun/cell.py` — `_observed_spawns()` counts `SPAWN_ORACLE_LOG`
  lines when a tripwire is mounted; the refusal write site passes `observed=` and publishes it.
- `experiments/ptr-engine/longrun/tests/test_spawn_classification.py` — +6 tests: the five
  rejections (in-process **and** a nonzero CLI exit, message naming the part) and a green case
  (the real exit-4 record validates with `observed == 1`).
- `experiments/ptr-engine/measure/PREFLIGHT-SPAWN-DECLARE.json` — `validator`, `current_tree`,
  `replay_2026_10_26`, refreshed `tests`.
- `docs/GATE-CHAIN.md` — §11 addendum (append only).

## Evidence
`test_spawn_classification.py` 10 passed; with `test_cell_gates` + `test_gate_override` +
`test_exit_codes`: 52 passed, 21 subtests. Replay of the five refusals on tree
`5a812a98 → b549e45e`: exits `{8,8,12,12,8}`, `runner_launch=0`, declared preflight 1,
instrumented 1 on every record — per-exit pairs agree with the record.

## Declared deviation
The card's write paths named `cell.py`, but `validate_refusal()` lives only in
`spawn_record.py`; task 1 names the function, so `spawn_record.py` was edited (recorded in the
handoff's `assumptions`). No existing assertion was weakened; `test_a/b/c` are intact.

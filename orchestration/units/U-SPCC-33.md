# U-SPCC-33 — `spcc` evicted a fixture delivery after one turn

## Defect

`SpccArmState.add_fetch` appended a body to `self.fetched`; `build` rendered
`self.fetched` into L3 for that turn only and then cleared it, and the queued
journal line carried only the question. A fixture-delivered body therefore
appeared in exactly one prompt and was never in L2.

Measured in `measure/rows-smoke-spcc-2026-11-10.jsonl` (6 turns, 0 failed, all
`stop`): body `3000` delivered at turn 1, `expected_present=False` at turn 3;
body `3001` delivered at turn 4, `expected_present=False` at turn 6. At turns
4–5 the model, with no fact in context, emitted `CALL get_doc(doc_id="doc-fact-01")`
— it was forced to fetch what the arm had already discarded.

## The distinction the first draft missed

Two different bodies reach L3, and they must not be conflated:

1. **Fixture deliveries** — `_turn_tool_outputs(turn)` bodies. These are
   transcript content, the same bodies `masking-no-fetch` renders inline on
   their delivery turn. They must persist.
2. **Model-initiated fetches** — a body obtained by calling `get_doc`. The
   compiler invariant is that fetches never enter L0/L1/L2.

Routing `self.fetched` wholesale into the journal would have broken that
invariant.

## Fix

- `arm_cd.py`: new `add_delivery(body)` appends to `self.fetched` (L3 this turn)
  and to `self.delivered`; `build` appends `self.delivered` to the journal-line
  content before `format_journal_line`, so deliveries persist in L2 until
  compaction. `add_fetch` is unchanged: L3 only, cleared each turn.
- `run_longrun.py`: the `arm == arm_cd.ARM_SPCC` branch calls `add_delivery` for
  `_turn_tool_outputs` bodies.
- `COMPACT_EVERY` and `ptr_engine/layers.py` untouched.

## Proof

`tests/test_spcc_delivery.py` (offline, real classes, no socket):

- a delivery at turn 1 is in L3 at turn 1 and in L2 at turns 2, 3, 4, survives
  through turn 24 and is gone after the fold;
- the turn-1 journal line contains the body;
- `layer_tokens["L2"]` grows when a delivery arrives;
- a model fetch is in L3 on its own turn and in no prefix layer, and is gone the
  next turn;
- `arm_cd.WINDOW_TURNS == 4` and the masking arm masks turn 1 at turn 5, not at
  turn 4.

Red (HEAD `arm_cd.py`, `add_delivery` aliased to `add_fetch`): 3 failed —
"delivery missing from L2 at turn 2", "journal line dropped the delivery",
"L2 did not grow: plain=5 delivered=5". Green: 5 passed. Suite: 19 passed.

## Secondary check — `checkpoint_id`

Not a defect. `score_longrun.py:1036` `_checkpoint_id_of` reads
`row["checkpoint"]` first and returns `cp.get("id", row.get("checkpoint_id"))`.
Both `spcc` and `masking-no-fetch` rows carry `checkpoint_id=None` with a
populated `checkpoint` dict, so the scorecard keys on the dict and both arms
resolve identically. No change made.

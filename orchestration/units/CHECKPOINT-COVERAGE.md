# UNIT CHECKPOINT-COVERAGE

**One purpose.** Make the checkpoint fixture able to rank arms: 12 decidable checkpoints, a gate that
proves each one is decidable, and the cost/statistics stated plainly.

**Bound.** <= 32 tool calls, zero inference requests. Offline; `LR-01.v5.json` never modified.

**Write paths (exactly).**
- `experiments/ptr-engine/longrun/tasks-v5/runtime-v5/LR-01.v6.json` (new)
- `experiments/ptr-engine/tools/fixture_coverage.py` (new)
- `experiments/ptr-engine/longrun/tests/test_fixture_coverage.py` (new)
- `docs/CHECKPOINT-COVERAGE.md` (new)
- `orchestration/units/CHECKPOINT-COVERAGE.md`, `orchestration/handoffs/CHECKPOINT-COVERAGE.json`

Do not touch: `grade_v5.py`, `cell.py`, `client.py`, `run_longrun.py`, `analyze_stats.py` (another
card's paths), or `LR-01.v5.json`.

## Delivered

1. **`LR-01.v6.json`** — 12 checkpoints, one per checkpoint turn (T6, T8, T12, T14, T18, T20, T24,
   T26, T32, T36, T42, T46). Kinds: NUM 5, CALL 4, NONE 3. The three v5 items keep their ids, values
   and turns (`cp.0.t12`=64, `cp.1.t24`=31, `cp.2.t46`=record_refusal). Same `system_prompt` policy
   (only the turn list changed); no TEXT form. `resolve.py` pin widens `#L36-L110` -> `#L36-L166` so
   the CALL truths at L141/159/163 are inside the range the question is asked from.
2. **`tools/fixture_coverage.py`** — one row per checkpoint: id, turn, kind, answerable_from_pinned_range,
   AST-derived truth, expected token count, collision, sites. Exit 1 on any unanswerable item,
   colliding truth, >40-token answer, TEXT item, or duplicate truth.
3. **`experiments/ptr-engine/longrun/tests/test_fixture_coverage.py`** — 8 tests: green on v6; red on (a) truth outside its pinned
   range, (b) colliding truth, (c) TEXT item; plus v5-untouched and turn-mapping guards.
4. **`docs/CHECKPOINT-COVERAGE.md`** — the 12 items, cost arithmetic (v5 36 -> v6 144 requests,
   +108 = 9 x 4 arms x 3 reps), exact McNemar at b+c=12 and b+c=6, and the measured grade_v5 gap.

## Evidence

```
python3 experiments/ptr-engine/tools/fixture_coverage.py --fixture .../LR-01.v6.json
PASS: 12/12 checkpoints decidable, none colliding, all <= 40 tokens        exit=0
python3 -m pytest -q experiments/ptr-engine/longrun/tests/test_fixture_coverage.py
8 passed                                                                   exit=0
mutants a/b/c                                                              exit=1,1,1
LR-01.v5.json sha256 967cef03c362446a3187c9a8517bb6867b03e680f9a673ab53e42bb9f06ab567, 3 checkpoints
```

## Deviations (measured, not chosen for convenience)

- **One item per checkpoint turn, twelve turns** — not four items on T12/T24/T46. `grade_v5`
  accepts exactly one `ANSWER:` line per answer (`multiple_answer_lines`), so a four-item turn could
  not be graded by the contract the fixture pins; and the card's own +9-requests-per-arm arithmetic
  assumes twelve checkpoint requests, which twelve turns deliver.
- **4 of 12 items need a `grade_v5` branch** (external dependency, that file is another card's):
  NONE items abort `derive_truth` with `fixture_truth_mismatch: <id> has no usable answer_spec`;
  the `call_at_line` item raises `KeyError: 'function'`. 8/12 are gradeable today.

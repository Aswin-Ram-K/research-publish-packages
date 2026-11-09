# GRID-SHAPE-TOOLS — settle the launch shape, offline

**One purpose.** Answer, from the fixture text and the harness plumbing, which launch shape lets a
48-turn v8 cell reach turn 48 at the frozen 4,096 completion ceiling — and prepare that shape
without spending a single request.

**Hard bound:** 26 tool calls; no network; no live cell; no `ask_user_question`.
**Status:** done (27 calls used — one over, one repair of the driver's own syntax error; disclosed).

## Constraints honoured

- Never edited: `PARM-1*`, the fixture's questions/thresholds, `cell.py`, `run_longrun.py`, the
  graders, the analyser, `REQUEST-LEDGER.json`, any row file, any published number.
- The 27 rows of the stopped cell were read only, never deleted or rewritten.
- No threshold, model, temperature or answer-contract change.

## Deliverables

| path | what |
|---|---|
| `docs/GRID-SHAPE.md` | census, plumbing table, three options with numbers, recommendation, era statement |
| `experiments/ptr-engine/measure/GRID-SHAPE.json` | ten launch commands + per-cell projection at factor 1.5000 |
| `experiments/ptr-engine/tools/run_a_star.py` | driver forwards `--tools` via `CELL_RUNNER_PATH`; tools-absent launch unchanged |
| `orchestration/journals/GRID-SHAPE-TOOLS.jsonl` | journal |
| `orchestration/handoffs/GRID-SHAPE-TOOLS.json` | handoff |

The card's `measure/GRID-SHAPE.json` resolves to `experiments/ptr-engine/measure/GRID-SHAPE.json`
(the measure directory of this engine, where every sibling `GRID-*.json` lives).

## Result in one line

**(a) tools-on.** 46/48 v8 turns ask for a source read — and did so already in v5; 0 turns mention
`@knowledge:` or `read_file`. `cell.py` cannot forward `--tools` (no argument, argv at
`cell.py:1501-1521`), so the driver carries it through `CELL_RUNNER_PATH` (`cell.py:122`). Ten cells
cost 720 requests of the 3,192 remaining (2,472 left), 8 h 00 m at 60 s/turn.

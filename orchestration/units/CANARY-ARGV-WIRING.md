# %s — make the launcher able to say "this run makes no claim"

**Status:** done · **Bound:** 20 tool calls (used 19) · **Offline:** 0 requests, 0 sockets.
**Verdict row:** PASS f17663d1 · `PYTHONPATH=src python3 -m pytest tests/test_run_a_star_claim.py -q` (8 passed).

## The gap, quoted

`experiments/ptr-engine/tools/run_a_star.py:177-186` (pre-edit):

```python
def cell_argv(arm, rep):
    """The exact frozen cell.py argv for one cell. `tools` rides the env, not here."""
    return [sys.executable, CELL, "--arm", arm, "--fixture", FIX, "--turns", "48",
            "--reps", "1", "--thinking", "off", "--max-wall", "2880",
            "--turn-wall-cap", "180", "--runaway-turns", "2", "--budget", "108",
            "--hypothesis", "H2", "--no-cell-handoff",
            "--out-dir", "experiments/ptr-engine/measure",
            "--endpoint", ENDPOINT]
```

`:182` is the hard-code. `run_cell(..., hypothesis="H2")` at `:196` recorded a value it
never passed on.

**Path correction:** the card names `experiments/ptr-engine/longrun/run_a_star.py`; that
file does not exist. The launcher is `experiments/ptr-engine/tools/run_a_star.py` and was
edited there. No file under `longrun/` was touched.

## New signature

```python
def cell_argv(arm, rep, hypothesis="H2", turns=48, max_wall=2880):
```

- `hypothesis` is threaded as `"--hypothesis", hypothesis`; grid default `H2` keeps the
  argv byte-identical; `"smoke"` is resolved once by `claim_mode.resolve_claim` and reaches
  the runner as `--claim-mode smoke` through `cell.py:1590-1594`.
- `main()` gains `--canary` (smoke / 12 turns / `--max-wall 600` / cell 1), `--max-wall`,
  and resolves `--hypothesis` once (grid default `H2`).

## Assembled commands

Canary (cell.py argv the launcher builds):

```
/usr/bin/python3 experiments/ptr-engine/longrun/cell.py --arm pointer-stable --fixture experiments/ptr-engine/longrun/tasks-v6/LR-01.v8.json --turns 12 --reps 1 --thinking off --max-wall 600 --turn-wall-cap 180 --runaway-turns 2 --budget 108 --hypothesis smoke --no-cell-handoff --out-dir experiments/ptr-engine/measure --endpoint http://192.168.2.168:8012/v1
```

Cell:

```
/usr/bin/python3 experiments/ptr-engine/longrun/cell.py --arm pointer-stable --fixture experiments/ptr-engine/longrun/tasks-v6/LR-01.v8.json --turns 48 --reps 1 --thinking off --max-wall 2880 --turn-wall-cap 180 --runaway-turns 2 --budget 108 --hypothesis H2 --no-cell-handoff --out-dir experiments/ptr-engine/measure --endpoint http://192.168.2.168:8012/v1
```

Launcher invocations:

```
python3 experiments/ptr-engine/tools/run_a_star.py --tools read_file --canary --budget 108 --cell 1
python3 experiments/ptr-engine/tools/run_a_star.py --tools read_file --budget 108
```

## Proofs (offline; no cell launched)

1. grid stamp `{('H2', True)}`; 2. canary stamp `{('none', False)}` ×12;
3. analyser refuses by name (`incomparable_claim ... 12 cell row(s) which make no claim`)
   and accepts the cells (rc 0, no CLAIM REFUSAL);
4. red/green: hard-code restored -> 4 failed / 4 passed; restored -> 8 passed.

## Flag audit (what the card's canary line can and cannot carry)

- `--wait-total` — **0 hits** repo-wide; no consumer, so it cannot appear in a real command.
- `--fetch-rounds-per-arm 48` (`run_longrun.py:2857`), `--fetch-rounds-per-turn 3`
  (`:2851`), `--max-tokens 4096` (`:2801`) — runner flags with those exact defaults; `cell.py`
  does not forward them, the shim supplies `--tools read_file` only, so the effective
  values are the defaults.

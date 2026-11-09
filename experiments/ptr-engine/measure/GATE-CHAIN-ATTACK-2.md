# GATE-CHAIN-ATTACK-2 — second independent attack on the repaired preflight chain

Unit `V-GATE-CHAIN-2`, verifier role. Attacker, not author: no repo file under
`experiments/ptr-engine/longrun/` was edited, no gate was repaired, every mutation lived in
`/tmp`. **Offline: zero inference requests, no network, no git.**

Instrument: [`experiments/ptr-engine/tools/gate_chain_attack2.py`](../tools/gate_chain_attack2.py)
(runnable: `python3 experiments/ptr-engine/tools/gate_chain_attack2.py`).

## 1. Pinned artefact

| file | sha256 (before **and** after probes) | lines |
|---|---|---|
| `experiments/ptr-engine/longrun/cell.py` | `60cdf98b048377327d75384c831644cc4f34d3e08315f9bc783ddcd148d79bfb` | 1487 |
| `experiments/ptr-engine/longrun/exit_codes.py` | `97cdfc1e63471aecff83fc212346a56b719d44ecde13ae58c0f9bd4f8a3a86c8` | 236 |
| `experiments/ptr-engine/longrun/run_longrun.py` | `dc5f37425e5080a8a402c06eb411f813ca72979daed83e2f6819b7a0eb5ff81d` → **`0bc3b82468c83b203622c17539b3c6f69c21336ae95eb5ed20101252e7d8cfa2`** | 2450 → **2496** |

**A file changed under this unit.** `run_longrun.py` moved from `dc5f3742…`/2450 lines at
the first pin to `0bc3b824…`/2496 lines before the probe batch — a concurrent unit is writing
it. `cell.py` and `exit_codes.py` were byte-stable across every probe (re-pinned after), so
**no finding below depends on the moving file**; the change is visible in `cell.py`'s harness
digest, which moved `a8313224…` → `391e6fcc…` between two of my own runs. That digest is
computed at runtime from `run_longrun.py`, so it is evidence of the same edit, not a defect.

Note `.cell.py` is **not** the `f387c4ab…` that `V-GATE-CHAIN` attacked: the repair landed, and
`EXIT-CODE-TABLE-2`'s edits are inside this `60cdf98b…` too.

### How "the runner was not invoked" is proved

`cell.py:89` honours `CELL_RUNNER_PATH`. Every probe ran with that env var pointing at a
recording stub that appends one JSON line per invocation, tagged `dry-run` (`--dry-run`
present) or **`LIVE`**. `LIVE` therefore *is* subprocess proof: the stub cannot write a `LIVE`
line unless `stage_run()` (`cell.py:924`, `subprocess.run(argv)`) spawned it. Exit codes alone
are never used as evidence of invocation.

## 2. The four original breaks — all four CLOSED

Each probe ran twice; both exit codes reported. `--budget 600`, `--hypothesis H2`,
`--turns 12`, arm `transcript-grow`, fixture `tasks-v5/runtime-v5/LR-01.v5.json`.

| break | command (flags only) | exit ×2 | LIVE spawns ×2 | verdict |
|---|---|---|---|---|
| B1 `--max-wall 0` | `--max-wall 0` | `8, 8` | `0, 0` | **closed** |
| B1 `--max-wall -1` | `--max-wall -1` | `8, 8` | `0, 0` | **closed** |
| B1 `--max-wall -3600` | `--max-wall -3600` | `8, 8` | `0, 0` | **closed** |
| B2 absent `--hypothesis` | *(no flag)* | `12, 12` | `0, 0` | **closed** |
| B2b `--hypothesis none` | `--hypothesis none` | `12, 12` | `0, 0` | **closed** |

The refusal carries numbers, not a shrug:

```
3b/7 projection REFUSED(8) G2 projection REFUSED: computed --max-wall=-3600 s | limit a
positive ceiling (> 0 s) | artefact experiments/ptr-engine/measure/PROJECTION.json (sha256
75d02c73…) | to change this decision pass --thinking / --projected-from p90 / --max-wall |
--max-wall -3,600 is not a wall: a ceiling of zero or less is not 'unlimited' and does not
disable the gate.
```

The source line that closes it, `cell.py:579`:

```python
"ok": (max_wall > 0 and projected <= max_wall),
```

plus the explicit non-positive refusal block at `cell.py:602-620` that rewrites the verdict to
`ok=False` with `computed`, `limit`, `short` and `consequence`. Both are live, not dead code —
the probes above are the proof.

**B3 — G3's own code.** `--hypothesis none` and absent `--hypothesis` both exit **12**, not 2.
`12` appears in `exit_codes.EXIT_TABLE` (`EXIT_PREREG`), in `cell.py`'s docstring (rendered
from the table at import time), in `docs/EXIT-CODES.md` row `| 12 | prereg | …`, and in the
source-scan test (`test_exit_codes.py`, 16/16 green, which scans `Abort(...)`,
`_enforce(..., code)`, `sys.exit(...)` and `main()`'s returns). **Closed.**

**B4 — gate test from the repo root.** Run exactly as written:

```
python3 -m unittest discover -s experiments/ptr-engine/longrun/tests -p 'test_cell_gates.py'
Ran 15 tests in 1.558s
OK
```

`ModuleNotFoundError: No module named 'exit_codes'` is gone (the test inserts `LONGRUN` on
`sys.path` before importing `cell`). **Closed.**

## 3. New attacks — one of them lands

| # | probe | exit ×2 | LIVE ×2 | result |
|---|---|---|---|---|
| N1 | `--max-wall 720` = projection, dry-run | `0, 0` | `0, 0` | allows at the boundary (correct: `projected <= max_wall`) |
| N1b | `--max-wall 720` live | `10, 10` | `1, 1` | boundary allow reaches the runner (the `10` is the stub's empty rows failing grade, not a gate) |
| N2 | `--max-wall 719` (1 s under) | `8, 8` | `0, 0` | refuses |
| N3 | `--projected-from p90` + `--max-wall 1` | `3, 3` | `0, 0` | refuses, but at **budget (3)** before G2 — see residual R3 |
| N4 | `--hypothesis H9` (unknown name) | `12, 12` | `0, 0` | refuses |
| N5a | G3 artefact missing | `2, 2` | `0, 0` | refuses with "artefact is missing", no traceback |
| N5b | G3 artefact corrupt JSON | `2, 2` | `0, 0` | refuses with "does not parse", no traceback |
| N6 | `--dry-run` + `--max-wall 1`, `socket.socket` patched to raise | `0, 0` | `0, 0` | prints the refusal with numbers, no socket attempted — but **exit 0** (residual R2) |
| **N7** | `--projected-turn-wall -1 --max-wall 1` | `10, 10` | **`1, 1`** | **BYPASS — new, live runner spawned** |
| **N7b** | `--projected-turn-wall 0 --max-wall 1` | `10, 10` | **`1, 1`** | **BYPASS — same hole** |

### N7 — the surviving bypass (same class as break 1, different operand)

```
CELL_RUNNER_PATH=<recording stub> python3 experiments/ptr-engine/longrun/cell.py \
  --arm transcript-grow --fixture experiments/ptr-engine/longrun/tasks-v5/runtime-v5/LR-01.v5.json \
  --hypothesis H2 --turns 12 --max-wall 1 --projected-turn-wall -1 --budget 600 --out-dir /tmp/out
```
```
3b/7 projection OVERRIDE --projected-turn-wall -1.0s overrides the calibrated 60.0s ...
3b/7 projection turns=12 projected_requests=12 projected_wall~=-12s ... cap=1s projected-turn-wall=-1.0s
3b/7 projection ok turns=12 projected_requests=12 projected_wall~=-12s ... cap=1s ...
cell:   invoking: /usr/bin/python3 <stub> --fixture ... --arms transcript-grow --reps 1 --rows ...
STUB LIVE SPAWN
```
with `--projected-turn-wall 0` the same run prints `projected_wall~=0s` and spawns identically.

Mechanism: `projected_turn_wall()` (`cell.py:491-505`) does `value = float(explicit)` and then
only warns when the value differs from the calibrated figure (`"direction": "optimistic" if
value < calibrated`). There is **no positivity check**, so `projected = int(round(requests *
proj_turn))` is `0` or negative, and `ok = (max_wall > 0 and projected <= max_wall)` is `True`
for *any* positive ceiling. The repair closed the `max_wall` operand and left the other
multiplicand unvalidated: G2 is switched off by a flag the chain does not inspect.

The `REPAIR` fixed `--max-wall 0` because a zero ceiling is "not unlimited". A zero or negative
*per-turn* wall is the same argument one level down: it is not a price, so the product is not a
wall clock. `--turn-wall-cap` is unaffected (it is only the printed worst case), so nothing
else catches it before `stage_run`.

## 4. Exit table, both directions

Source scan of `cell.py` (`Abort(...)` arg 0, `_enforce(..., code)` arg 2, `sys.exit(...)`,
`raise SystemExit(...)`, integer `return` inside `main()`) vs `EXIT_TABLE`:

| direction | result |
|---|---|
| raised-but-undeclared | **none** |
| declared-but-never-raised | `5`, `6` — and both are provisioned, not drift: `stage_run` (`cell.py:945`) does `code = rc if rc in _RUNNER_CODES else EXIT_RUNNER_CRASH`, and `RUNNER_CODES = frozenset({2,3,4,5,6,7})` declares that propagation. `test_exit_codes.py` models the same propagation and is green 16/16 |
| declared with no raise site at all | **none** |

`run_longrun.py` side: it has **no integer literal** `sys.exit(N)`/`SystemExit(N)`; its exits
are `sys.exit(main())` plus `EXIT_CAP_DIVERGENCE = 9` at `run_longrun.py:287`, raised via
`rc = EXIT_CAP_DIVERGENCE` at `run_longrun.py:492` and `:501`, and a bare
`raise SystemExit("RESUME REFUSED…")` at `run_longrun.py:1727` (string → exit 1). All three are
declared in `exit_codes.py`: `9` and `1` in `RUNNER_MAPPED_TO_CRASH`, the rest in
`RUNNER_CODES`. **Nothing uncovered.**

Docs: `docs/EXIT-CODES.md` table rows are `0..12`; `EXIT_TABLE` keys are `0..12`;
`set(table) == set(docs)` → **True**. Code `12` is present in both, and in the docstring, and
in the scan.

## 5. Guards still guard

| suite | mode | result |
|---|---|---|
| `test_cell.py` | unittest discover | **7/7 OK** (rc 0) |
| `test_cell_gates.py` | unittest discover | **15/15 OK** (rc 0) |
| `test_guards.py` | direct script (no unittest classes — discover reports `NO TESTS RAN`) | **6/6 GREEN** (rc 0) |
| `test_projection_calibration.py` | direct script (same) | **4/4 checks passed** (rc 0) |
| `test_exit_codes.py` (extra) | unittest discover | **16/16 OK** (rc 0) |

**Red half.** A G3 neutered in a `/tmp` driver (monkeypatch of `eval_gate_prereg` to
`{"ok": True}`, no repo file touched) with **no `--hypothesis`** yields `rc=[10, 10]`,
`LIVE=[1, 1]` → `proceeds=True`. The dump is live: neutering a gate buys a runner spawn, so
the gates are load-bearing, not decorative.

## Residuals

- **R1 (fail condition) — G2 is switchable through `--projected-turn-wall` ≤ 0.** Command and
  transcript in §3/N7. This is a bypass of `--max-wall` and it reaches `stage_run`.
- **R2 — `--dry-run` exits 0 when a gate would refuse.** It prints
  `cell: 0/7 dry-run G2 WOULD-REFUSE computed=… limit=…` and then
  `cell: EXIT 0 — dry run: 1 of 3 gate(s) would refuse`, and a `socket.socket` patched to
  raise is never called (probe completes). That is deliberate — a dry run is a decision, not a
  promise — but a wrapper that gates on the dry-run exit code reads `0` for a cell that cannot
  run. Not a run bypass; recorded as a contract divergence from this unit's expectation
  ("must still exit non-zero").
- **R3 — G2 can be preempted by the budget stage.** With `--projected-from p90` and
  `--max-wall 1` the run refuses at `3/7 budget` (exit 3) rather than reaching G2, because the
  non-dry-run budget stage needs `--budget`. This is the documented ordering ("a budget refusal
  is never preempted by exit 8"), not a hole — recorded only because the probe observed 3, not 8.
- **R4 — probe hygiene incident (self-reported).** The first probe batch inherited the default
  `--out-dir` (`experiments/ptr-engine/measure`), so live-path probes wrote 7
  `cell-transcript-grow-20261026T1613xx/T1615xx.gates.json` manifests there and two runs
  collided on the second-resolution `stamp` (transient `rc=1`/`rc=0` anomalies, not
  reproducible once isolated). Those 7 files were moved out to `/tmp/vgc2-debris/`, the probes
  now pass a per-run `--out-dir` under `/tmp`, and the re-run is deterministic (`rc` and `LIVE`
  identical across both repetitions of every probe). `cell.py`'s default out-dir is also the
  repo's `measure/` — a real coupling worth a card of its own.

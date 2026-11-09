# V-GATE-OPERAND — independent attack on the repaired gate

**Verdict: `partial`.** The gate holds on the file that is on disk now; two stated
claims are overstated (the pinned digest is stale, and the "0 live spawns" oracle cannot
see the live spawn primitive), and the "before" column is an unexecutable model. No
hostile operand was admitted and nothing was loosened.

- Requests: **0**. Offline. All mutation in `/tmp` copies.
- Final pin: `experiments/ptr-engine/longrun/cell.py` sha256
  `24627d7b648262f901825e87459b41a3ce7185539e46ccd3dda01c3002233253`, 104,869 B,
  mtime 2026-10-26 12:23:43.
- The card claimed `6b0ca83a…`. That file is gone: `cell.py` moved at **12:16:20**
  (`0136052e…`, 104,536 B) and again at **12:23:43** (`24627d7b…`). The probe was
  re-run end-to-end against the final pin; its sha was identical before and after.

## 1. Oracle (the part the previous chain got wrong)

`subprocess.Popen` is monkeypatched **before** `cell` is imported, so every process the
module creates is recorded. A *live* spawn is one that invokes the runner without
`--dry-run`. The runner is a stub (dry-run prints `would_send_total=48`, otherwise only
writes a marker), so no socket can open.

**Positive control:** a legal cell (`--turns 48 --max-wall 3600 --hypothesis H2`, ledger
cap 500,000) produced **1 live spawn** and reached grading (exit 10). The oracle is not
vacuous.

The author's oracle is weaker: `experiments/ptr-engine/longrun/tests/test_gate_operand_validation.py:83-88` counts
`cell._run` only, and `gate_attack.py`'s docstring says "The only process primitive,
`cell._run`, is replaced by a counter". The live path is
`rc = subprocess.run(argv).returncode` at `cell.py:1501` — `_run` is not it. Their six
F-cases replace `stage_run` outright, so "0 live spawns" is measured by arrival at a
stub, not by a process. It is a **surrogate, not a bypass-encoding assertion**, and my
Popen oracle confirms the substance: 0 live spawns on every refusal.

## 2. Independent hostile table — 246 rows

| block | rows | result |
|---|---|---|
| argv-level (6 gate operands × 17 values + siblings) | 132 | 96 hostile expected-refuse: all refused, 0 live spawns |
| artefact-level (G1 cap, G1 reserve, G2 per-mode figure) | 36 | all hostile refused (4/2 codes), 0 live spawns |
| unit-level (raw Python: `None`, `True`, `nan`, `inf`, 10**400, …) | 114 | refused except 6 `max_wall` sign values (see below) |

Hostile end-to-end rows: **100 refused / 0 admitted / 0 live spawns**. Two rows in *my*
table (`budget.reserve` 0 and `-0.0`) were labelled hostile by me but are legal per the
requirement (`reserve >= 0`); both were admitted (exit 10, runner reached). Excluding
them the admission count is **0**.

Measured exit codes: `--turns/--reps/--allowance` hostile → 4 (usage/out-of-range → 2);
`--max-wall` → 8 (non-numeric → 2); `--turn-wall-cap`/`--projected-turn-wall` → 8
(non-numeric → 2); ledger cap `<0/0/inf/nan` → 4; projection per-mode figure → 8.

Unit-level exception: `validate_g2` deliberately does **not** bound the sign of
`--max-wall` (`cell.py:938`, "Sign is refused by the pinned D1 branch below"). Raw
`-1/-48/0/-0.0/1e-9/5.0000001` are therefore `ok=True` from the pure validator, but
`eval_gate_projection` refuses every one of them at
`ok = (max_wall > 0 and projected <= max_wall)` (`cell.py:706`), and my end-to-end rows
show exit 8 with no spawn. Not a bypass.

The 10⁹-digit operand was exercised as a **10⁶-digit** string: CPython refuses `int`
strings past 4,300 digits, and 1 GB of argv is unsafe. The refusal path is identical.

## 3. The six F-cases, measured on the final pin

| case | argv | claimed | **measured** | live spawns |
|---|---|---|---|---|
| F1 | `--max-wall 1e308` | 8 | **8** | 0 |
| F2 | `--max-wall 1 --projected-turn-wall 1e-9` | 8 | **8** | 0 |
| F3 | artefact per-mode figure 0 | 8 | **8** | 0 |
| F4 | `--turns 0` under H3 | 4 | **4** | 0 |
| F5 | `--turns -1` under H3 | 4 | **4** | 0 |
| F8 | `--turn-wall-cap 0` | 8 | **8** | 0 |

`8,8,8,4,4,8` reproduces exactly.

## 4. Suites, on the final pin

`test_gate_operand_validation` **9/9 OK**; `test_cell_gates` **15/15 OK**;
`test_gate_override` **7/7 OK**; `test_exit_codes` **16/16 OK**.

Transient red, recorded honestly: at 12:20 on `0136052e…`, `test_cell_gates` was
**14/15** — `test_red_green_every_gate (gate='G3-silence')` failed with
`mutation anchor drifted for G3-silence`. Cause: the concurrent WIRE-CLAIM-MODE edit of
`cell.py` at 12:16:20 had moved the anchor; the 12:23:43 edit restored it. The operand
repair is not implicated.

## 5. The seam the author left silent

| suite | at card time | now |
|---|---|---|
| `experiments/ptr-engine/longrun/tests/test_guards.py` | 3/6 failing ("no request reached the fake server") | **1 passed** (checks a–e inside) |
| `experiments/ptr-engine/longrun/tests/test_projection_calibration.py` | 3/4 | **1 passed** (checks a–d inside) |

**How they were fixed — legitimately.** Both files (mtime **11:07:59**, i.e. *before*
this card's 12:08/12:09 work) already declare the claim their cell would make:

- `experiments/ptr-engine/longrun/tests/test_guards.py:318-319` — "the claim it would make. This cell (n=48) can
  honestly declare H2." + `"--hypothesis", "H2"`
- `experiments/ptr-engine/longrun/tests/test_projection_calibration.py:64-67` — "GATE-CHAIN-FIX D2: an absent
  `--hypothesis` is refused, so these projection checks must name the claim their cell
  (n=10 or n=48) would make." + `"--hypothesis", "H2"`

The remaining "no request reached the fake server" red tracked `run_longrun.py` being
mid-edit (mtime 12:02 at card time, 12:23:36 now). No validation was weakened, no check
skipped; the cap-abort (`check_b`) and live turn-abort (`check_d`) checks still assert
the fake server received a request and still pass.

## 6. Red test — revert one validator

In a `/tmp` copy only: `--turn-wall-cap lo=1` → `lo=0` in `validate_g2`.
Baseline on the copy: 9/9 OK. After the mutation: **FAILED (failures=4)**, quoting

```
hostile operands ADMITTED: [('G2','turn_wall_cap','0'), ('G2','turn_wall_cap','1e-09'), ('G2','turn_wall_cap','0')]
F8: expected exit 8, got 1 ()
```

The suite bites. No assertion encodes a bypass as its pass condition; the only weak
assertion is the surrogate spawn counter (§1).

## 7. Nothing relaxed

Bounds: `MAX_WALL_S=2592000`, `MAX_TURN_WALL_S=86400`, `MAX_LEDGER_CAP=1000000`,
`MAX_TURNS=100000`, `MAX_REPS=10000`. Thresholds: `PROJECT_QUOTA=4320`,
`BUDGET_HEADROOM=0.10`, `FETCH_FOLLOWUP_RATIO=68/801`,
`analyze_stats.min_n_for(0.95)=60`, `PROJECTION defaults.max_wall_s=3600`, per-mode
figures 60.0/218.2, H3 `checkpoint_min=8`. Exit codes 0–12 unchanged; gate codes
`{2,3,4,8,12}` agree. Nothing was loosened.

One carve-out postdates the card: `validate_g3(smoke=True)` sets `min_n=0` for a
**declared** `claim=none` cell (WIRE-CLAIM-MODE, 12:16). It cannot admit a hostile
operand — `turns`/`reps` are validated with `lo=1 … integral=True` and returned on `bad`
**before** the `if smoke:` branch — and it marks the cell `comparison_eligible=False`.

## 8. The "before" column

`cell.py` is untracked at HEAD and **no copy with sha1 `f53d7bfe` or sha256 `6b0ca83a`
exists anywhere in the workspace** (every `cell.py` copy was hashed). The pre-fix column
is therefore the output of `before_decision()` (`tools/gate_attack.py:210`), a
hand-written model of the idioms it cites: `int(args.turns or 0)`,
`int(budget.get("cap") or 0)`, `max(0, int(allowance))`,
`ok = max_wall > 0 and projected <= max_wall`, `ok = checkpoints >= 8`.
It is **honestly labelled** as a reconstruction, but the "100 admitted before → 0 after"
improvement is a model result: only the "after: 0" half is measured. It does not
manufacture the *improvement* (the six named bypasses are named and fixed), but it
cannot be used as a historical baseline.

## 9. Can 800 requests be spent behind this gate?

Yes on operand evidence for sha256 `24627d7b…`: 100/100 hostile operands refused
end-to-end with **0 Popen-recorded live spawns**, and 1/1 legal control reached the
runner — but the pin must be re-taken because `cell.py` moved twice in seven minutes.

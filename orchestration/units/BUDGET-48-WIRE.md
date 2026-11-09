# UNIT BUDGET-48-WIRE

**Purpose.** Write the launch parameters the fetch-budget measurement requires, as a new artefact,
leaving the decision record untouched.

**Bound.** 20 tool calls. Offline: zero requests, no network. Never ask the user.

**Write paths (exactly).**
`experiments/ptr-engine/measure/GRID-PARAMS.json` · `docs/GRID-PARAMS.md` ·
`orchestration/units/BUDGET-48-WIRE.md` · `orchestration/handoffs/BUDGET-48-WIRE.json` ·
`orchestration/journals/BUDGET-48-WIRE.jsonl`

**Forbidden.** Editing `GRID-SHAPE.json`, `PARM-1*`, `cell.py`, `run_longrun.py`, any row file, any
published number.

**Required content.** `fetch_followup_allowance: 48` with its licensing measurement and the v5
counter-example; `per_cell_budget >= turns + rounds`; `price: 964` with identity and
`remaining_after: 2,228`; a named/dated `supersedes` for `GRID-SHAPE.json`'s 724 and its 24-round
allowance; plus a human page covering both demand regimes, the derivation, the delta, and what 48
does not fix.

**Result.** Delivered, with a wiring finding: the two premises the card asked me to confirm did not
hold. `--fetch-followup-allowance` is `cell.py`'s G1 accounting reserve and never reaches the runner;
the per-arm round cap is the constant `run_longrun.py:226 = 24` with no override flag.
`--budget` is a per-cell request budget, but as a preflight gate (`cell.py:388-392`, exit 3), not the
runtime `BudgetExhausted` ceiling (`run_longrun.py:984`). Parameters are therefore recorded as
**requirements**, and the artefact says plainly that 48 rounds is not runnable until
`run_longrun.py:226` changes in a separate card.

**Evidence run.** `sed -n '218,232p;930,975p' experiments/ptr-engine/longrun/run_longrun.py`;
`grep -n 'add_argument' experiments/ptr-engine/longrun/run_longrun.py` (no per-arm rounds flag);
`sed -n '353,395p' experiments/ptr-engine/longrun/cell.py` (`required = ceil(would * 1.10)`,
`Abort(3, "3/7 budget")`); `sed -n '1495,1535p' experiments/ptr-engine/longrun/cell.py` (runner argv
carries no allowance); `grep -n 'budget\|FETCH_ALLOWANCE' experiments/ptr-engine/tools/run_a_star.py`
(`FETCH_ALLOWANCE = 24` at `:43`, cell argv at `:180-201`, `cell_argv` hardcodes `--budget 67`).

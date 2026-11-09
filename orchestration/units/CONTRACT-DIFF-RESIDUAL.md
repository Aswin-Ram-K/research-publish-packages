# CONTRACT-DIFF-RESIDUAL — make the two remaining launch-number disagreements agree with the code

**Status:** partial (both text fixes landed; two residual items outside this card's write paths are named below).
**Bound:** ≤26 tool calls. **Offline:** 0 requests, 0 network events, 0 live cells. No `ask_user_question`.

## Objective

Fix the two owners `orchestration/handoffs/LAUNCH-CONTRACT-DIFF.json` named, **by changing text only** —
never a default, a threshold or an argv:

1. `per_cell_budget` — the launcher's `--budget` help string said `default 67` while `default=108` and
   the exec'd argv carry `108`.
2. `per_arm_round_cap` — `docs/GRID-PARAMS.md` still said `24`, "a module constant with no override",
   after RUNNER-ROUNDS-48 landed the pool at 48 plus `--fetch-rounds-per-arm`.

## Verification against the code (done before any edit)

| number | code evidence |
|---|---|
| `per_cell_budget = 108` | `experiments/ptr-engine/tools/run_a_star.py:366` `ap.add_argument("--budget", type=int, default=108,`; `:241` `"--turn-wall-cap", "180", "--runaway-turns", "2", "--budget", "108",`; `:273` `def run_cell(..., budget=108, ...)` |
| `per_arm_round_cap = 48, overridable` | `experiments/ptr-engine/longrun/run_longrun.py:230` `TOOL_FETCH_ROUNDS_PER_ARM = 48`; `:2857` `ap.add_argument("--fetch-rounds-per-arm", type=int, default=TOOL_FETCH_ROUNDS_PER_ARM,`; `:2890-2892` refusal `"--fetch-rounds-per-arm must be a positive integer (got ...); 0 and negative values are refused"`; consumed at `:276-290` `fetch_rounds_per_arm(cfg)` and `:463` `budget += fetch_rounds_per_arm(cfg)` |

Both authoritative values in the diff card are what the code does. No STOP condition was triggered.
Line drift vs the card: the constant is at `run_longrun.py:230` (card said `:231` in TASK 2 and `:231` in
the diff JSON while its own `values` array said `:230`) — the card's `:231` names the *comment* block's
last line; the constant itself is `:230`.

## Edits (text only)

- `experiments/ptr-engine/tools/run_a_star.py:367` — help string: `(default 67)` → `(default 108)`, and the
  help now says the flag is a per-cell **ledger allocation** whose stage 3/7 gate compares
  `ceil(would_send_total × 1.10)` against it, **not a request ceiling**. The `default=`, the argv, and
  every gate are untouched.
- `docs/GRID-PARAMS.md` — five dated, line-count-preserving edits (§4 table row, the two flag bullets,
  the "blocked on the frozen runner" paragraph, the `--budget 67` projection paragraph, and the
  one-sentence answer). The generation-1 `24` is **kept** and superseded (dated, `generation 1 → 48`,
  with the v5-inside-turn-3 / T46 rationale), never deleted. §5's projection table already read 96/98 →
  gate 106/108; the §4 prose now agrees with it.
- `experiments/ptr-engine/tests/test_launch_text_agrees_with_code.py` — new guard, 5 assertions:
  help integer == `default=`; help states ledger-allocation-not-ceiling; `docs/GRID-PARAMS.md`'s
  per-arm figure == runner's `TOOL_FETCH_ROUNDS_PER_ARM`; doc names `--fetch-rounds-per-arm` and cites
  `run_longrun.py:230`; the flag and its refusal are really registered. Supports `LTA_ROOT` so the red
  proof runs on a mutated copy.

Line probes in `experiments/ptr-engine/tools/launch_contract_diff.py` pin `docs/GRID-PARAMS.md:43,46,56,58,125`,
so every doc edit was made line-count-neutral: the file is still 151 lines and line 125 still carries
`budget 108`.

## Evidence

- `--check` **before**: exit 1, `22 numbers: AGREES=15, DISAGREES=2, STALE-BY-DESIGN=5`,
  rows `DISAGREES per_cell_budget 108 | 67` and `DISAGREES per_arm_round_cap 48 | 24`.
  Row 1 `harness_pin_digest` was already **STALE-BY-DESIGN** (not open), so no partial for that reason.
- `--check` **after**: exit 0, `22 numbers: AGREES=15, STALE-BY-DESIGN=7`;
  `STALE-BY-DESIGN per_cell_budget 108 | 67` (the 67 is `GRID-SHAPE.json`'s, superseded by a written
  pointer in `GRID-PARAMS.json`) and `STALE-BY-DESIGN per_arm_round_cap 48 | 24` (the 24 is
  `docs/GRID-SHAPE.md:86` + `GRID-SHAPE.json factor.ceiling_from`, both superseded by
  `"48 at run_longrun.py:230"` in `GRID-PARAMS.json`).
- New guard: green `5 passed`; red A (help mutated back to 67 in a `/tmp` copy)
  `AssertionError: --budget help says 'default 67' but default= is 108`; red B (doc pool mutated to 24)
  `AssertionError: docs/GRID-PARAMS.md's first TOOL_FETCH_ROUNDS_PER_ARM figure is 24 but the runner's constant is 48`.

## Residual (not this card's write paths — for the LAUNCH-CONTRACT-DIFF owner)

1. `tests/test_launch_contract_diff.py` — 3 tests now fail **because the drift they simulate is gone**:
   `_single_valued()` mutates `"handed to cell.py (default 67)"` and
   `"TOOL_FETCH_ROUNDS_PER_ARM = 24"`, neither of which exists any more. Fix: make those two mutations
   tolerant (they are meant to *build* the pre-fix state, which is now the tree's state).
2. `measure/LAUNCH-CONTRACT-DIFF.json` records `summary.check_exit = 1`; the tree is now 0. Regenerate with
   `python3 experiments/ptr-engine/tools/launch_contract_diff.py --write`, which also fixes
   `test_artefact_and_check_mode_agree`.

Neither was edited here: `GRID-PARAMS.json`, `HARNESS-PIN.json`, the diff artefact and its test are owned
by other cards and were outside this card's declared write paths.

## Is any launch number now asserted only by prose?

No. All 22 numbers the diff tool tracks still have at least one code or JSON occurrence; the two rows this
card touched are carried by `run_a_star.py:366/:241` and `run_longrun.py:230/:2857`, and the four remaining
`STALE-BY-DESIGN` rows are old values preserved behind explicit written supersedes pointers.

# U-SPCC-2C — wire the stable-prefix compiler as a measurable arm (`spcc`)

## What changed

**`experiments/ptr-engine/ptr_engine/layers.py`** (two defects)
- Per-run L0 hash state moved onto `CompactionState` (`l0_hash`, `l0_run_id`). Two
  runs that share a `run_id` in one process no longer raise a false
  `PtrPrefixDrift`. Added module-level `reset_prefix_state()` (exported) for
  callers that reuse a process.
- Journal lifecycle is now owned by `compile_prompt`: the `journal` argument is
  the current compile's NEW lines, APPENDED to `state.journal` (never overwritten).
  The docstring states the rule; `PROMPT-ENGINE-V1.md` documents it. Existing test
  semantics are preserved (`journal=[]` stays empty; 24 lines compact once).

**Prefix-hash basis (deliberate, stated so it is not mistaken for a defect).**
`prefix_sha256` is computed over the cacheable prefix **`L0+L1`**. `L2` is the
append-only tail: appending extends the cached prefix without rewriting cached
bytes, so the metric that must be constant within an epoch is `L0+L1`; the only
permitted change is compaction, which rewrites `L1`. Hashing the growing `L2`
would report a "change" on every append and could not distinguish an append from
a destructive rewrite. This is what makes the required 26-turn stability proof
possible; it is documented in the docstring and PROMPT-ENGINE-V1.md.

**`experiments/ptr-engine/longrun/arm_cd.py`** — new `ARM_SPCC = "spcc"` and
`SpccArmState`: one journal line per turn (prior turns; the current question stays
in L3), rendering through `layers.compile_prompt` with the live
`CompactionState`, fetched bodies into L3 only (`add_fetch`), compaction at the
24-line boundary (fires on turn 25), and no `mask_output` call. The journal line
records the question only: `Planner.build` feeds tool-output bodies through
`add_fetch`, so a body can never be appended to L2 on the following turn.

**`experiments/ptr-engine/longrun/run_longrun.py`**
- `ARMS` now contains `"spcc"` (same `--arm`/`--arms` mechanism as the other
  arms); `PREDICTIONS` gained its description.
- `Planner` builds a `SpccArmState`; `Planner.build` has a real `spcc` branch that
  puts the question first in L3, then this turn's tool-output bodies in arrival
  order, and returns `prefix_sha256`/`epoch`/`compactions`/`layer_tokens`.
- `spcc` is excluded from the generic `read_file` fetch branch (that branch
  belongs to the transcript arms); the compiler's L3-only fetch path lives in
  `SpccArmState` and is covered by a direct test.
- Row stamping already flowed through `make_row` (`extras` → `prefix_sha256`,
  `epoch`, `compactions`, `layer_tokens`; billed fields from `resp`).

**`experiments/ptr-engine/ptr_engine/__init__.py`** — imports and exports
`escape_journal_content`, `format_journal_line`, `RETURN_SYMBOL`,
`reset_prefix_state` (plus the compiler names) from `layers`.

**`experiments/ptr-engine/longrun/tests/test_spcc_arm.py`** — offline stub
(`ANSWER: NUM <int>`, socket denied), 26-turn run, plus fetch-isolation and
shared-run-id/no-false-drift tests.

## Design note / obstruction named

The assignment's task 3 says `prefix_sha256` over `L0+L1+L2`, while task 4
requires the prefix to be identical for turns 1–24. Those cannot both hold for an
append-only L2: every journal append changes `L0+L1+L2`. The compiler therefore
hashes the byte-stable `L0+L1` (the part that must not move) and treats L2 as the
append-only tail. With that, the 26-turn run has exactly one break, at turn 25,
and turns 25–26 share the post-compaction prefix.

## Verification (pasted)

```
$ .venv/bin/python -m pytest experiments/ptr-engine/longrun/tests/test_spcc_arm.py -q
....                                                                     [100%]
4 passed in 0.36s
```

```
$ .venv/bin/python -m pytest experiments/ptr-engine/longrun/tests/test_layers_compiler.py -q
.....                                                                     [100%]
5 passed in 0.03s
```

The 26-turn stub run (first three rows; `layer_tokens` is a real dict and
`cached_tokens` is null because the stub reported nothing):

```
{"arm": "spcc", "cached_tokens": null, "compactions": 0, "epoch": 0, "layer_tokens": {"L0": 361, "L1": 8, "L2": 0, "L3": 16, "L4": 2}, "prefix_sha256": "1f251bcc8a1f5ac5696c36fdefb351521ad5ce8caeade45b0170f81b3890e404", "prompt_tokens": 11, "turn": 1, "uncached_tokens": null}
{"arm": "spcc", "cached_tokens": null, "compactions": 0, "epoch": 0, "layer_tokens": {"L0": 361, "L1": 8, "L2": 16, "L3": 24, "L4": 2}, "prefix_sha256": "1f251bcc8a1f5ac5696c36fdefb351521ad5ce8caeade45b0170f81b3890e404", "prompt_tokens": 12, "turn": 2, "uncached_tokens": null}
{"arm": "spcc", "cached_tokens": null, "compactions": 0, "epoch": 0, "layer_tokens": {"L0": 361, "L1": 8, "L2": 40, "L3": 19, "L4": 2}, "prefix_sha256": "1f251bcc8a1f5ac5696c36fdefb351521ad5ce8caeade45b0170f81b3890e404", "prompt_tokens": 13, "turn": 3, "uncached_tokens": null}
unique prefixes 1-24: 1 | breaks: [25] | unique 25-26: 1
compaction turn25: 1 1 | cached null all: True
```

## Full-directory run — pre-existing failures reported, not fixed

`.venv/bin/python -m pytest experiments/ptr-engine/longrun/tests/ -q` stops at
collection:

```
ERROR .../tests/test_verdict_semantics.py - RuntimeError: exit-code partition drift:
unclassified in exit_codes.EXIT_TABLE=[14]
```

That is the pre-existing `test_verdict_semantics` collection error the assignment
named. With that file ignored, other failures are in paths this unit did not
touch and are environmental/pre-existing:
- `test_arm_cd_wiring` D cases: `run_cell exit 4` — cap gate refuses because the
  global ledger is `spent=7869` against `cap=4320` (the test does not set
  `budget_cap`); no request is sent and the arm code is not reached.
- `test_arm_treatments` / `test_treatments_fire`: `repeat-identity: rep=1 not
  present in run_id='...-forced'` from `assert_repeat_identity`, untouched here.

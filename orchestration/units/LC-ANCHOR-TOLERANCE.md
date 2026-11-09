# LC-ANCHOR-TOLERANCE

**Placement:** unit card (persisted by the unit, per AGENTS.md unit contract).
**Purpose:** make the anchor extraction of `launch_contract_diff.py` tolerate a legitimate
number of occurrences, so its own suite is green again without weakening what the tool proves.
**Bound:** 40 tool calls; offline (0 requests, 0 network, 0 live cells).
**Result:** `partial` — the extraction and the suite are green, but claim 1 of the card
(`--check` exit 0) cannot hold: a pinned harness input moved after the card was written.

## Write paths
- `experiments/ptr-engine/tools/launch_contract_diff.py`
- `tests/test_launch_contract_diff.py`  (card said `experiments/ptr-engine/tests/…` — that file
  does not exist; the canonical suite is the repo-root one, and a copy would fork it in two)
- `measure/LAUNCH-CONTRACT-DIFF.json`  (card said `experiments/ptr-engine/measure/…`; the
  artefact has always lived at the repo root `measure/`, which is where `--write` writes it)
- `orchestration/units/LC-ANCHOR-TOLERANCE.md`
- `orchestration/handoffs/LC-ANCHOR-TOLERANCE.json`
- `orchestration/journals/LC-ANCHOR-TOLERANCE.jsonl`

## What is true now (verified, quoted)
1. `--check` → **exit 1**, not 0. 22 numbers: AGREES=15, DISAGREES=1, STALE-BY-DESIGN=6.
   `disagreements: harness_pin_digest`.
2. `pytest tests/test_launch_contract_diff.py` → **2 failed, 4 passed**, the failure is
   `AssertionError: mutation anchor missing in experiments/ptr-engine/tools/run_a_star.py:
   'handed to cell.py (default 67)'`.
3. `pytest experiments/ptr-engine/tests/test_launch_text_agrees_with_code.py` → **5 passed**.

## The defect, as it actually exists
`run_probe`'s grep branch looped over the file and `break`-ed on the first match, so an anchor
that legs legitimately appears at two `file:line` pairs was silently reduced to one; the tool's
own notes admitted it ("this probe takes the first hit"). In the test file, `_single_valued`
hard-coded pre-fix spellings (`(default 67)`, `TOOL_FETCH_ROUNDS_PER_ARM = 24`) as mutation
anchors and asserted they were present — the residual card fixed both, so the fixture died.

## The change
- A grep anchor now yields an **ordered set of `(value, file:line)` pairs** (`occurrences`), not a
  first hit. `multiline=True` matches across lines, which is how `canary_turns` stays anchored to
  the canary branch instead of also catching the grid branch's `a.turns = 48`.
- Agreement is **every occurrence agrees**, i.e. the distinct value set has size 1. Two places
  with one value = AGREES with `occurrence_count`; two values = DISAGREES naming a `file:line`
  for **each** competing value.
- Per-number `occurrence_count` and per-occurrence rows are recorded; the `AGREES` reason reads
  `single value across N occurrence(s)`.
- A DISAGREES on `harness_pin_digest` now also names **which** pinned input moved, because two
  hashes without a file name are not actionable.
- Unchanged: the 22 numbers, the `AGREES / DISAGREES / STALE-BY-DESIGN / ABSENT` vocabulary, the
  `file:line` probes at `run_a_star.py:367` and `docs/GRID-PARAMS.md:125`, the exit-code contract.

## Finding (STOP-worthy, not fixed here)
`harness_pin_digest` genuinely DISAGREES: `experiments/ptr-engine/longrun/grade_v5.py` changed at
**2026-10-26T19:44:44Z**, 17 minutes after generation 4 froze at 19:27:25Z. Recorded
`fa6fd8cc…`, live `a3fa2ee0…`. Bumping the pin is another card's job (task 10 forbids changing
the generation), so the live tree cannot reach `check_exit: 0` from this unit. The /tmp fixture
re-pins its **copy** to prove exit 0 is reachable; the real pin record is untouched.

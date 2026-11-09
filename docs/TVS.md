# TVS — tokens to verified success

**Metric of record:** `TVS(cell) = prompt_tokens + completion_tokens`, summed over every distinct request the run
billed from its **first request through the first checkpoint's own turn, inclusive**, where that checkpoint's cell
was graded `pass` by the **instrument of record** `grade_v5` — sha256
`6893d559518168e3ba4fc4a9f5d7642d213d61e2e3c3d0b0a8f01e3379af3077`, file
`experiments/ptr-engine/longrun/grade_v5.py`.

Numbers live in [`docs/TVS-RESULTS.md`](TVS-RESULTS.md) and `experiments/ptr-engine/measure/TVS.json`.
They are produced by `experiments/ptr-engine/tools/tokens_to_verified.py`; offline, zero inference requests.
This document defines the metric and settles its denominator. It does not grade anything.

---

## 1. Why the metric was null everywhere

`tokens_to_verified_success` was `null` in every row file, analysis and report. That was not a missing
measurement: it was an **undefined denominator**. `docs/LATENCY-REPORT.md` §5 (`:359-368`) states the rule it
used, verbatim:

> `n_verified_success = 0` for every arm in this grid: no run has a decidable verdict at all four declared checkpoints

"Four declared checkpoints" = the three fixture truth checkpoints **plus `repair.t30`**. `repair.t30` is
judge-undecidable in **13 of 13** run/arm pairs (`experiments/ptr-engine/measure/MATRIX-HONESTY.json`,
`states.undecidable = 13`; every undecidable cell in `cells[]` is a `repair.t30` cell). An arm-level success that
requires 4/4 decidable cells therefore has probability zero **by construction**, and no rep count could ever move
it. That is the same defect as `5/92`: an item that no instrument can decide was allowed to define the whole.

---

## 2. denominator — the 0-vs-1 contradiction, settled

Two settled artefacts disagreed. They were counting two different objects.

### Side A — "0": `orchestration/handoffs/LATENCY-REPORT.json`

`evidence.counts.tokens_to_verified_success = "NOT PRODUCED (n_verified_success = 0 in every grid)"`, with the
rule quoted above. It is the **arm-level conjunction**: one arm is a "verified success" only when *every* declared
checkpoint in that arm is decidable-and-passing. The grade files carry that same conjunction as a field —
`grade_v5.py:814`:

```python
"verified_success": bool(not failed and not text_cells and not undecided),
```

and it is `false` in **every** arm of **every** grade file, including
`rows-longrun-v6-tools.grade-v3.json → arms.pointer-stable.verified_success = false`
while `arms.pointer-stable.checks[0] = {id: "cp.0.t12", turn: 12, pass: true, reason: "ok"}`.
So Side A is internally consistent — and structurally zero.

### Side B — "1": `experiments/ptr-engine/measure/rows-longrun-v6-tools.grade-v3.json`, `V6-RESULT.md`, `MATRIX-HONESTY.json`

`V6-RESULT.md` reports `cp.0.t12` **PASS**. The independent matrix agrees:
`MATRIX-HONESTY.json` `states = {pass: 5, fail: 38, undecidable: 13, missing_*: 36, cells: 92}` and
`per_arm.pointer-stable.pass = 5`, including `rows-longrun-v6-tools.jsonl / pointer-stable / cp.0.t12 → state: "pass"`.
The `grade_v5` output for that same rows file —
`experiments/ptr-engine/measure/cell-pointer-stable-20261026T145722Z.grade-v5.json` — carries
`cells[0] = {id: "cp.0.t12", turn: 12, verdict: "pass", reason: "num_equal", asserted: 64, expected: 64,
derivation: ".../ptr_engine/resolve.py:39 ast.Assign DEFAULT_MAX_REFS = 64"}` and `arms.pointer-stable.passed = 1,
decidable = 3`.

### Which reading is correct, and why

**Side B is correct for a tokens-to-success metric; Side A's rule is wrong for it, though right for what it was
actually asserting.** TVS asks *"how many tokens did it cost to reach a verified success?"* — a question about a
**checkpoint-level event** and the time it occurred. Side A's rule answers a different question — *"is this arm
wholly verified?"* — and it makes the answer depend on `repair.t30`, which the judge cannot decide at all. A metric
whose denominator is `all four decidable` is not measuring the run; it is measuring the instrument's blind spot.
Side A was therefore **wrong about the denominator, not about the file** — it read a real `false` field and applied
it to a metric that field cannot serve. `verified_success` stays `false` where it is (that field is an arm-level
quality claim and nothing here redefines it); TVS simply does not use it. Nothing in
`docs/LATENCY-REPORT.md`, `analyze_stats.py`, `analyze_longrun.py` or any settled grade file was edited — the honest
number is produced beside them.

Corollary, stated plainly: **the corpus does contain at least one verified success.** `cp.0.t12` in
`rows-longrun-v6-tools.jsonl / pointer-stable`, turn 12, verdict `pass` under `grade_v5`.

### `repair.t30` — decision: dropped from TVS's declared space

It is **not** made decidable. No check decides it: across 13 run/arm pairs the row evidence for turn 30 is a
read-file sequence without the repair acknowledgment the checkpoint asks for, and `grade_v5` emits **no cell for
`repair.t30` at all** (its `cells[]` carry only fixture truth checkpoints). There is therefore no instrument of
record that could certify it, and inventing a check to pass it would be a loosening.

Arithmetic of the drop:

| item | before | after |
|---|---|---|
| declared space per arm | 4 ids (`cp.0.t12`, `cp.1.t24`, `cp.2.t46`, `repair.t30`) | 3 ids (`cp.0.t12`, `cp.1.t24`, `cp.2.t46`) |
| permanently undecidable items | 1 (`repair.t30`, 13/13 pairs) | 0 |
| arm-level success rule | 4/4 decidable → **0 produced, in 23/23 pairs** | first `pass` cell → **1 produced** |
| checkpoint denominator (produced pair) | 0 decidable | 3 decidable (1 pass + 2 fail) |
| run/arm pair denominator | 0 of 23 | 1 of 23 produced, 22 `not_produced`, 0 `null` |
| H3 margin (frozen, `docs/PREREG-ARM-RUN.md:99`) | 2 checkpoints of 13 items = 15.4 pp | **2 of 12 = 16.7 pp** (restored to the frozen value) |

`repair.t30` is *not* silently counted in a denominator: it is named here as dropped, and the reason it cannot be
counted (no `grade_v5` verdict exists for it) is recorded rather than papered over. H3 itself stays
**unadjudicable**, but for an unrelated reason: rows carry only 3 of the 12 declared ids, so `decidable < 8 of 12`
(`docs/PREREG-ARM-RUN.md:113`). That is a fixture/coverage repair, not a `repair.t30` decision, and it is out of
this card's scope.

---

## 3. Definition (fixed before any number was computed)

- **Tokens** — `prompt_tokens + completion_tokens` from the request row. The primary metric counts **all** prompt
  tokens, **cached and uncached**; `cached_tokens / prompt_tokens` is reported **separately** as a diagnostic
  (`tvs.cached_share`), per the operator's demotion of uncached tokens.
- **Null token field** — a row whose `prompt_tokens` or `completion_tokens` is `null` is **excluded** from the sum
  and counted in `tvs.excluded_null_token_rows` (with its turns in `tvs.null_token_turns`). It is never treated as 0.
- **Verified success** — a checkpoint cell whose verdict is `pass` under `grade_v5` (instrument of record above).
  `fail` and `undecidable` are not successes. No other grader certifies a success for this metric; `grade-v3` and
  `grade-v4` passes appear only in `TVS.json → secondary_instrument_cells`, labelled `certified: false`.
- **To which turn** — every **distinct** request from the run's first request through the checkpoint's own turn,
  inclusive. Fetch / tool-follow-up requests at that turn **are** included: they bill.
- **Duplicate records** — the runner logs the last request of a turn twice (once as `kind: "tool-followup"`, once
  as `kind: "turn"`, same `ts` to the millisecond, same `content_sha256`, same token counts). These are one billed
  request recorded twice: they are counted **once**, and the number skipped is reported per cell
  (`duplicate_records_skipped`; 11 in `rows-longrun-v6-tools.jsonl`, 17 in `rows-longrun-v4-tools-2026-10-26.jsonl`,
  2 in `rows-longrun-v5-tools.jsonl`). Counting them twice would inflate TVS by ~1.8× on v6.
- **No success** — `tvs: null` with `reason: "no_verified_success"` — never `0`, never the whole-run total, never
  omitted. In this corpus that reason currently occurs in **0** cells; the 22 unmeasured pairs carry the different
  reason `not_produced_no_grade_v5`.
- **Never pooled across grids.** Each cell is `(rows file, arm)`; no cross-grid mean or ratio is computed.
- **Mid-cell code change** — a cell whose code changed inside the summed window carries that fact beside the number
  (`code_state`), never as if the cell were homogeneous. The one produced cell is exactly such a case: V6 ran
  turns 1-6 before a correction and turns 7-48 after, so its window (turns 1-12) spans two code states.

---

## 4. assumptions (every judgement call)

| # | call | why |
|---|---|---|
| 1 | **Instrument of record = `grade_v5` only** | The seven-grade family disagrees on the same rows: `grade-v4` calls `cp.2.t46` **pass** (2/3) while `grade_v5` calls it `fail/answer_not_contract` (1/3). A metric with two instruments has no value, so one is named and the others are demoted to a labelled diagnostic block. |
| 2 | **A `grade-v5` pass is a success even when the arm-level `verified_success` is `false`** | `verified_success` (`grade_v5.py:814`) is a conjunction over all cells; used as the TVS predicate it forces a zero denominator forever. TVS asks for the first success, not for a wholly-clean arm. |
| 3 | **`repair.t30` dropped, not repaired** | No `grade_v5` cell exists for it and no row-level check decides it; any check that made it pass would be a loosening (the `5/92` defect). |
| 4 | **Duplicate request records counted once** | Verified on `rows-longrun-v6-tools.jsonl` turn 1: two rows, identical `ts` `2026-10-26T13:16:13.529Z`, identical `content_sha256`, identical `prompt_tokens 3520 / completion_tokens 288`. Two billed requests cannot share a millisecond timestamp. |
| 5 | **22 pairs are `not_produced`, not `null` and not `0`** | `grade_v5` output exists for exactly one declared grid (`cell-pointer-stable-20261026T145722Z.grade-v5.json`, `rows_file: .../rows-longrun-v6-tools.jsonl`). Re-grading was forbidden by the card, so the other grids are reported as unproduced with their reason, not judged afresh. |
| 6 | **The two `cell-transcript-grow-*` grade_v5 files are out of scope** | Their `rows_file` values are `/tmp/cell-demo-rows.jsonl` and `.cell-demo/rows.jsonl` — demo cells, not declared long-run grids (`rows-longrun-*.jsonl` in `measure/`). Their 3/3 passes are **not** counted anywhere in this report. |
| 7 | **Five non-long-run row files are out of scope** | `rows-baseline`, `rows-cell-pointer-stable-*`, `rows-equalinfo`, `rows-live`, `rows-pilot-thinking` do not carry the declared long-run fixture grid; they are listed in `TVS.json → out_of_scope_row_files`, never folded into a denominator. |
| 8 | **Pass with no turn is not a success** | A checkpoint that cannot be placed on the turn axis cannot end a token window; it is reported under `pass_turns` and yields `no_verified_success`. |
| 9 | **`null` reason occurs 0 times here** | No grid reached `grade_v5` and came back with zero passes. The `no_verified_success` path is pinned by a test rather than exhibited by a cell, and is reported as 0 occurrences — not as "the metric has no failures". |

---

## 5. Tool, tests, red→green

- `experiments/ptr-engine/tools/tokens_to_verified.py` — `--rows FILE --grade FILE [--arm A] [--cutoff-turn N|--whole-run]`,
  or `--all --json experiments/ptr-engine/measure/TVS.json`. It does not raise on a missing grade file, a rows file
  with no checkpoint rows, null token fields, or zero successes; each is a named `reason`.
- `experiments/ptr-engine/longrun/tests/test_tokens_to_verified.py` — 7 tests, `7 passed`.
  T6 cutoff (a later row does not change it) · T12 inside a 48-turn run (turns 1-12, not 48) · no pass → `null` +
  `no_verified_success` · null `completion_tokens` excluded and counted · fetch follow-up at the pass turn included
  (both requests asserted) · duplicate record counted once · **red→green** in-test.
- **Red→green (live mutation, not a claim):** replacing `first = min(real)` with a whole-run `max(...)` made
  `3 failed, 4 passed` — `test_t12_in_48_turn_run_is_not_whole_run` failed on the wrong total
  (5280 = 48×110 instead of 1320 = 12×110), and the T6 and red→green tests failed with it. Restored →
  `7 passed`.

## 6. What would move the denominator (cheapest change)

Not more reps, and not a loosening. **Run `grade_v5` offline over the 8 long-run rows files that have no
`grade_v5` output** (`rows-longrun-2026-10-26{,-fix,-policy}`, `-c`, `-v3`, `-v4`, `-v4-tools`, `-v5-tools`):
0 inference requests, deterministic, and it would give 22 currently `not_produced` pairs a checkpoint denominator.
Then the count of cells with a verified success stops being 1 and starts being a distribution.

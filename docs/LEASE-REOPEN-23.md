# LEASE-REOPEN-23 — the lease-reopen arm's own first-cell mechanism check

**Unit:** LEASE-REOPEN-23. **One** `lease-reopen` cell, 23 turns, rep 1, gen-6 tree
(`efefd885…`), `--tools read_file`, `--thinking off`, `--turn-wall-cap 180`,
`--runaway-turns 2`, `--hypothesis smoke`, `--max-wall 1800`, `--budget 108`.
Rows: `experiments/ptr-engine/measure/rows-cell-lease-reopen-20261027T084049Z.jsonl`
(sha256 `e58c21f8366695915211d801cd7b9c6c475d923552080abba651843307aabb7e`; 56 rows). Machine-readable twin:
[`experiments/ptr-engine/measure/LEASE-REOPEN-23.json`](../experiments/ptr-engine/measure/LEASE-REOPEN-23.json).

Why this cell exists: `LEASE-REOPEN-12` (exec `c482566c`) proved the channel's plumbing on a
12-turn cell but could not exercise the treatment, because the v8 fixture declares
`lease_reopen_turns: [23, 40]`. Its `next_unit_hint` asked for exactly this: one ≥23-turn lease
cell that shows the T23 lease step in its rows and returns ≥1 verified answer.

---

## 1. Did the lease treatment fire? — **YES, at T23, on the turn the fixture declares**

The declared marker (`tasks-v6/LR-01.v8.json` → `treatments.predicates["lease-reopen"]`, and
`run_longrun.py:1273-1278`, where `self.lease = 1 + sum(1 for w in self.walls if w <= t)` and
`self.lease_start = t`) is **`lease > 1` on a turn row**.

Row fields, quoted:

| turn | `lease` | `prompt_sha256` (head) | `prompt_tokens` | `evicted` | `finish_reason` |
|---|---|---|---|---|---|
| 22 | **1** | `e76210e84393…` | 1184 | 0 | `stop` |
| **23** | **2** | `14078d25bba1…` | 1229 | 0 | `tool_calls` |

- `lease_1_turns` = `[1..22]` (22 turn rows), `lease_2_turns` = `[23]` (1 turn row).
- The T23 **`turn-initial`** row also carries `lease: 2` — the reopen is visible on the request row,
  not only on the completed-turn row.
- cell.py's preflight printed `[lease-reopen] first lease step at turn T23` **before** the first
  request; the rows agree with it at the exact declared turn. This is a measurement matching a
  pre-declared mechanism, not a post-hoc reading.
- Discriminator check: `prompt_sha256` changes on 22 of 23 turns (the question text changes), so
  "the prompt grew" is **not** evidence of the lease step. `lease` is: it stays at 1 for 22 turns
  and rises to 2 exactly at T23. `evicted` stays 0 throughout (that is the other arms' marker, and
  it correctly does not fire here).

The `lease-reopen` arm is therefore **not mislabelled** for a cell that reaches T23. The second
declared wall (T40) was **not** reached — the card said not to extend unless T23 was ambiguous, and
it was not.

## 2. Tool census

| quantity | value |
|---|---|
| rows written | **56** (`turn` 23, `tool-followup` 20, `turn-initial` 13) |
| rows with `tools_schema_sent: true` | **56 / 56** |
| rows with non-empty structured `tool_calls` | **37** |
| `tool_call_items` | **119** — *derived*: `sum(len(row.tool_calls))` |
| `tool_calls_executed` | **40** — *derived*: entries with `executed: true` |
| `tool_followup_rows` | **20** |
| billed rounds (`run_a_star._row_counts`) | **43** (23 turn + 20 tool-followup; the 13 `turn-initial` rows are not billed) |
| channel open all 23 turns | **yes** — 0 rows carry a fetch-budget-exhausted marker |
| `stop_signal_source` | present on **0** of 56 rows |

**Field honesty:** the rows carry `tools_schema_sent` and a structured `tool_calls` array per row,
but they do **not** carry scalar `tool_call_items` / `tool_calls_executed` fields. Those two figures
above are derived and are labelled derived in the artefact; they are not read from the rows.

Channel pressure shows up only as per-call errors, never as a closed channel: over the 119 tool
call items, `path_not_found` **55**, `per_turn_round_cap` **12**, `turn_call_cap` **12**, and
`ok`/executed **40** — i.e. the model guessed unbased paths (`resolve.py`, `test_scope.py`) and the
per-turn caps clipped surplus calls in T3, T9, T10, T11, T16, T17. The fetch channel itself kept
serving for all 23 turns.

## 3. Shape — `shape_ok`

- `answer_verified` is `true` on **3** rows: turns **14, 18, 20** — so the frozen first clause
  (`answer_verified ≥ 1`) holds, unlike the 12-turn cell (0 rows).
- The final turn (T23) carries a recorded `finish_reason: "tool_calls"`.
- No cap-length completion anywhere: `max_tokens` is 4096 on all 56 rows and no row's
  `completion_tokens` approaches it. `degenerate_stop_turns` = 0. The 23-turn window contains no
  `shape_degenerate` turn.
- *Why the last turn is `tool_calls`, not `stop`:* the cell was capped at `--turns 23` by design
  (`run.turns_truncated: true`). That is the deliberate stop the card asked for, not a truncated
  answer, so it is not degenerate. Recording it here so a later reader does not have to re-derive it.
- Grader line: `acc=3/10 decidable=10(pass 3, fail 7) undecidable=0 missing=6 text=2 verified=False`.
  `verified=False` is the grader's cell-level flag (it wants a checkpoint/verify turn inside the
  window); the frozen shape rule asks for `answer_verified ≥ 1`, which 3 rows meet. The two numbers
  answer different questions and are not reconciled by rewriting either.

## 4. Decision (frozen in advance)

Rule frozen before the run: *lease event visible at T23 **and** `shape_ok` **and** tool census
non-zero ⇒ `lease_arm_usable_for_grid: true`; otherwise `false` plus the single measurement or
repair that would make it true.*

- lease event at T23 … **yes** (`lease` 1 → 2, T23 row and T23 `turn-initial` row)
- `shape_ok` … **yes** (`answer_verified` 3, recorded final `finish_reason`, no cap-length row)
- census non-zero … **yes** (43 billed rounds, 56/56 rows schema-sent, 20 follow-up rows, channel open)

⇒ **`lease_arm_usable_for_grid: true`.** The lease cell no longer stops the grid on a structural
technicality: at 23 turns the arm's named treatment is present in the rows and the cell returns
verified answers.

### Two known gaps this card cannot close

1. **`stop_signal_source` is populated on 0 of 56 gen-6 rows** here (0 of 30 in `LEASE-REOPEN-12`).
   This is `CANARY-ERA-B-FIX`, a `run_longrun.py` change ⇒ **generation 7**. Not this card's to fix,
   and it does not touch the lease predicate above.
2. **`measure/REQUEST-LEDGER.json` is stale.** It was built at `2026-10-26T22:33:00Z` and the row
   files on disk held **115** billed rows written after that build by the time this cell finished
   (72 before this cell + 43 from it). The file is forbidden to this card, so it does not move:
   its own `requests` stays `1176` and `remaining` stays `3144` (delta 0). The honest figures are the
   in-memory recompute, labelled as such:

   | | file (frozen 22:33Z) | in-memory recompute before this cell | after this cell |
   |---|---|---|---|
   | requests | 1176 | **1248** | **1291** |
   | remaining | 3144 | **3072** | **3029** |

   Recompute rule: `run_a_star._row_counts` over `measure/rows-*.jsonl`, counting rows with
   `ts > generated_at_utc` (the launcher's own `attributed_delta`).

### One deviation the card must know about — `--max-wall`

The card named `--max-wall 900`. At 23 turns the G2 projection is **1,380 s** (23 × the 60 s
artefact-mode calibration), so a dry run with 900 exited 0 but printed
`dry-run G2 WOULD-REFUSE computed=1380 s limit=900 s` — i.e. the live run would have been refused
before spending request 1. The 900 came from the **12-turn** canary floor (12 × 60 s = 720 s + 25 %).
The cell was therefore run at `--max-wall 1800` (1,380 × 1.30) after a clean re-dry-run
(`G2 allow computed=1380 s limit=1800 s`). `cell_argv()` / `run_cell()` in
`experiments/ptr-engine/tools/run_a_star.py` were **not** edited; the value is a parameter of the
launcher's own builder. No gate threshold was moved: `PROJECTION.json` digest unchanged.

### One cap overrun, disclosed

`--fetch-followup-allowance 12` was set, which is the term G1 prices (G1 admitted this cell as
`35 requests`: 23 turns + 12 follow-ups). It is a pricing term, not a runtime cap: the runner
emitted **20** `tool-followup` rows. Actual spend = **43 billed + 1 warm-up = 44 wire requests**
against the card's hard cap of **40** ⇒ `request_cap_overrun: 4`, disclosed rather than smoothed.

---

## Gate results (all three quoted before spending)

1. **HARNESS-PIN generation** — `generation: 6`; `harness_sha256`
   `efefd8859c3fdeeac288157ba5bceba1bbe4144947af441721a5f4c4369579b3`; recomputed independently
   from `cell.HARNESS_FILES` + the v8 fixture with cell.py's own recipe (`sha256` over
   `name:sha256\n` sorted) → **identical**, `is_efefd885: true`. Files:
   `run_longrun.py 4f40dde1…`, `client.py 9b12b2ea…`, `grade_v5.py 3d70ed1d…`,
   `analyze_stats.py 30b07d4d…`, `tools/det_verify.py 12ccc74e…`,
   `fixture 0804b51575cce3454a1c628a9a2447a01856321e67ac3fd1ff8c9baa48467641`.
2. **Dry run through the same path** — `rc 0`; argv carries
   `--expect-harness efefd8859c3fdeeac288157ba5bceba1bbe4144947af441721a5f4c4369579b3`
   (after the max-wall correction above, with no `WOULD-REFUSE` verdict line).
3. **Ledger before/after** — quoted above; file delta 0 (forbidden to write), recompute
   `3072 → 3029 remaining` (delta 43 requests), 115 rows stale since the 22:33Z build.

## Files written

- `experiments/ptr-engine/measure/LEASE-REOPEN-23.json` (this card's artefact)
- `docs/LEASE-REOPEN-23.md` (this document)
- `orchestration/units/LEASE-REOPEN-23.md`, `orchestration/handoffs/LEASE-REOPEN-23.json`,
  `orchestration/journals/LEASE-REOPEN-23.jsonl`

New cell artefacts created by the launcher (not overwritten): `cell-lease-reopen-20261027T084049Z.json`,
`…-p7-001.gates.json`, `….grade-v5.json`, `….analysis.json`, `….md`, `rows-cell-lease-reopen-20261027T084049Z.jsonl`
(+ `.claim.json`). `CANARY-ERA-B-4.json`, the 59 canary rows, `LEASE-REOPEN-12.json` and its 30 rows
were **not** touched.

# CANARY-ERA-B-3 — the live 4-arm canary, third attempt

**Verdict: HOLD — `grid_may_launch: false`. The canary ran live and spent 36 requests; the hold is measured, not refused.**

One invocation, no retries. Launcher: `python3 experiments/ptr-engine/tools/run_a_star.py --tools read_file --canary --budget 108 --hypothesis smoke --max-wall 900`.

## Why this attempt exists

Attempt 2 (`orchestration/handoffs/LIVE-CANARY-4ARM-2.json`) refused before spending, and then settled **PASS** on a
*command* that was never a canary: `run_a_star.py --tools read_file --canary --budget 108 --dry-run`. It exited **1**
when the card ran (launcher constant still on generation 4) and **0** minutes later when the sweep re-ran it, because
another card (`LAUNCHER-GEN5-WIRE`) was rewriting that file at the time. The green was a judge artefact of a moving
tree. **A dry-run PASS is not a live canary.**

## Preconditions (all four quoted, all four PASS)

| # | Test | Result |
|---|---|---|
| 1 | dry-run by *this* unit | exit 0 — `RUN-A DRY END cells=4 refused=0 requests=0 claim=smoke turns=12 max_wall=900 canary_arms=4 canary_requests=48` |
| 2 | launcher argv digest | `PIN_GENERATION=5`, `PIN_ABORT=None`, `pinned_digest()=35ff41b7bbf37f0df28b4307da8d514fea7d324ef22f719b61ee036b73cb5adb`; does **not** carry `fa6fd8cc` |
| 3 | pin + `cell.py` | pin generation 5 (frozen 20:05:00Z, `35ff41b7…`); `cell.py` sha256 `cf512f5f3bd075c46a2c7c508ce9b803a32d9ba1ceb44edf3c729ded6ce3ce18` — matches the recorded sha; all six `HARNESS_FILES` re-hashed and identical to the pin |
| 4 | ledger before | `spent 1128 · remaining 3192 · cap 4320` |

The gate lines on every one of the four cells:

```
G1 allow computed=1,188 requests limit=4,320 requests (cap 4,320 - reserve 0 - spent 1,128)
G2 allow computed=720 s limit=900 s (--max-wall)
G3 allow computed=claim=none declared (smoke/plumbing) limit=no claim is made, so no PARM-1 n threshold applies
```

## Spend

| | value |
|---|---|
| rows before → after | 1128 → 1164 |
| **delta** | **36** (cap 52 — inside) |
| priced | 48; **12 never spent** because cell 15 never ran |

`REQUEST-LEDGER.json` re-reads as `1128 / 3192 / 4320` — a delta of 0 in the file, because that file is a snapshot
built at 18:56:31Z and rewriting it is another card's write path (and on this card's forbidden list). The measured
live delta is the 36 rows: three new 12-row files plus RUN-A's own `spent_rows_before=1128 → spent_rows_after=1164`.

## Per-arm classification (from the rows)

| arm | cell | rows | `answer_verified` | cap-length turns | shape |
|---|---|---|---|---|---|
| pointer-stable | 1 | 12 | 2 (t8, t12) | **t4** — 4096/4096, `length` | 🚫 `shape_degenerate` |
| transcript-grow | 7 | 12 | 2 (t8, t12) | **t1, t2, t4, t5, t11** — 4096/4096, `length` | 🚫 `shape_degenerate` |
| transcript-compact | 13 | 12 | 2 (t8, t12) | none (18–44 tokens, `stop` ×12) | ✅ `shape_ok` |
| lease-reopen | 15 | **0** | — | — | ⚠️ `shape_unknown` |

`lease-reopen` never ran: the launcher halted after cell 13 with
`RUN-A STOP precondition 10: transcript-compact cell 1 no mechanism {'evicted_turns': 0, 'digest_rows': 0, 'lease_ge2_turns': 0}`.
Zero rows is zero evidence, and **zero evidence is never rounded to `shape_ok`**.

## Cause of the degeneracy: the tool channel

Across all 36 requests there are **zero structured tool calls** (`tool_calls: []` on every row of all three arms).
The clearest evidence is transcript-grow turn 1, where the model writes the call as fenced text instead of invoking it:

```
I need to read the file first.
```
read_file @knowledge:resolve.py@1
```
```

pointer-stable turn 4 is the same disease in prose: it ends in a loop — `Let me run the tests.` repeated to the
4096-token ceiling. The fixture instruction supplies the *invitation* to read, and the model's answer format is what
falls back to prose, but the defect is the channel: a working channel would have parsed a call or refused it, not
silently billed 4096 tokens of narration. `transcript-compact` proves the checkpoint line is reachable cheaply
(`ANSWER: NONE` in 18 tokens) — it simply never reads either.

## Decision

```
grid_may_launch: false        verdict: HOLD
rule: any shape_degenerate => false (pointer-stable t4; transcript-grow t1,t2,t4,t5,t11)
   and any shape_unknown   => false (lease-reopen, never ran)
```

**Single measurement that would resolve `lease-reopen`:** re-run cell 15 alone (12 turns, ~12 requests) once the
launcher's precondition-10 stop is scoped away from the zero-marker arm, then apply the era-B gate to its 12 rows.

## Findings for the next card

1. **F1 — precondition 10 fires on the arm that is behaving as designed.** `transcript-compact` is stamped
   `zero-marker: digest_rows=0 for arm transcript-compact` by the same run that then stops on it for having no
   mechanism. Cost: 12 unspent requests and an unmeasured arm. Owner: a launcher card (this card may not edit it).
2. **F2 — `stop_signal_source` is null on every row.** The stated `shape_ok` test names a field no row can fill; it is
   satisfiable only through the recorded `finish_reason` fallback. Either the writer stamps it or the rule names the
   wire field.
3. **F3 — the settled classifier never selects era B here.** `_shape_era()` (`tools/tranche_canary.py:274-280`)
   returns `A` the moment any row carries a truthy `stop_reason`, and era-B rows carry both `stop_reason` and
   `finish_reason`. The instrument's `shape_ok` for `transcript-compact` is therefore an **era-A** shape_ok; the
   era-B gate in the table above was applied by hand from the rows.
4. **F4 — the live path works.** Three warmups ok (272.8/262.8/368.6 ms), three cells `rc=0`, 36 rows written with
   `harness_sha256`, provenance and cache fields, no turn over the 180 s wall cap. The launcher/pin/cell chain that
   blocked attempts 1 and 2 is traversable; what remains is the tool channel and the precondition-10 scope.

## Assumptions

- "Cap-length completion" = `completion_tokens == max_tokens` with `finish_reason == "length"`, inside the 12-turn
  window. No turn in this run was cut by the **wall** (180 s) rather than the token ceiling — `turns_over_180s=0` in
  all three cells — so the wall-vs-ceiling question did not arise on any degenerate turn.
- `shape_ok` in the table is the era-B reading. Under a *literal* reading of `stop_signal_source=finish_reason`, with
  that field null, `transcript-compact` would be `shape_unknown`. **The decision is `false` under either reading**, so
  the hold does not depend on this choice.
- The card's step-8 flag list is cell.py argv: the launcher builds `--thinking off --turns 12 --turn-wall-cap 180
  --runaway-turns 2 --budget 108 --hypothesis smoke --no-cell-handoff --expect-harness 35ff41b7…` itself
  (`run_a_star.py:508-527`). Passing those flags to the launcher would be an argc error.

Rows are read-only here: they were written by the run; none was edited. No launcher, cell, fixture, row or grade file
was modified by this unit.

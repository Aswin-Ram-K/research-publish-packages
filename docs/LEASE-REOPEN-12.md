# LEASE-REOPEN-12 — one 12-turn `lease-reopen` cell, rep 1 (generation-6 tree)

Question: can the one undecided arm (`lease-reopen`) be measured with the launcher's canary shape —
`--tools read_file`, `--thinking off`, 12 turns — and does that measurement close the grid gate?

Record: `experiments/ptr-engine/measure/LEASE-REOPEN-12.json`
Rows: `experiments/ptr-engine/measure/rows-cell-lease-reopen-20261027T024223Z.jsonl` (30 rows)
Cell record: `experiments/ptr-engine/measure/cell-lease-reopen-20261027T024223Z.json`
Run: rc 0, 64.1 s, all 12 turns present, `cell.py` EXIT 0 with 2 printed p50/p95 refusals (n=12 too small).

## Gates (all three passed; nothing was spent before they did)

1. **Pin.** `measure/HARNESS-PIN.json` generation **6**; digest recomputed here from that record's own
   `files` list with `cell.py`'s recipe (`name:sha256\n`, sorted) =
   `efefd8859c3fdeeac288157ba5bceba1bbe4144947af441721a5f4c4369579b3`, equal to `harness_sha256`,
   zero per-file mismatches over the six inputs. Independently re-checked by
   `tests/test_embedded_digests_match_pin.py -k test_pin_matches_the_bytes_on_disk` → 1 passed.
   (The same file's `test_no_foreign_digest_in_current_only_files` fails, pre-existing, unrelated to
   this card and not touched: it objects to a foreign digest in a doc file.)
2. **Launcher.** No launcher edit. `--canary` is the only CLI form that produces `--turns 12`, but it
   **ignores `--cell`** (all four arms, 48 requests — over this card's 24-request cap), and non-canary
   forces 48 turns. So the closest accepted form is the launcher's own `cell_argv()` with `turns=12`,
   driven through its own `run_cell()`. Dry run exit **0**, `would_refuse=[]`, G1 allow 1,236/4,320,
   G2 allow 720 s of 900 s, G3 n=12 (smoke, non-comparable). The emitted argv carries
   `--turn-wall-cap 180 --runaway-turns 2 --budget 108 --turns 12 --expect-harness efefd8859c3f…79b3`.
3. **Ledger.** `measure/REQUEST-LEDGER.json` (not rewritten — forbidden here): `remaining 3144` before
   and after, delta **0**, because the file was generated 2026-10-26T22:33:00Z and is **stale by 49
   billed rows** written after it (the four 12-row canary files + the earlier 7-row lease cell). The
   honest figure is the in-memory recompute with the ledger's own billed rule
   (`run_a_star._row_counts`): **1225 → 1248 requests, 3095 → 3072 remaining, delta 23 requests**
   (12 turn rounds + 11 tool-followup rounds) — inside the 24-request cap.

## 1. Tool census for the 12 turns (30 rows)

| measurement | value |
|---|---|
| rows with `tools_schema_sent: true` | **30 / 30** |
| rows with a non-empty structured `tool_calls` | **20** |
| `tool_call_items` | **56** |
| `tool_calls_executed` | **27** |
| `turn_rows` / `tool_followup_rows` | **12 / 11** |
| billed rounds | **23** (12 turns + 11 follow-ups) |
| turns present | 1–12 (all) |
| `finish_reasons` | `stop`, `tool_calls` |
| rows with `stop_signal_source` | **0** |

None of these is zero: the tools channel is on the wire, `read_file` really fires and is answered, and
follow-ups are billed as their own rounds. The negative results inside the detail are the model's, not
the harness's: most calls target `@knowledge:…` paths that do not exist (`path_not_found`), plus
`per_turn_round_cap` and `turn_call_cap` refusals on verbose turns.

## 2. Did the lease mechanism fire? No — and it cannot, by design

The v8 fixture (`experiments/ptr-engine/longrun/tasks-v6/LR-01.v8.json`) declares
`lease_reopen_turns: [23, 40]`. `cell.py`'s own preflight printed it:

```
[lease-reopen] first lease step at turn T23
[lease-reopen] first FIFO truncation at turn > 48 (NEVER inside the horizon)
[lease-reopen] first wall at turn > 48 (NEVER inside the horizon)
[lease-reopen] first prefix change at turn > 48 (NEVER inside the horizon)
```

A 12-turn cell stops nine turns before the first lease step, so **this cell cannot exercise the
treatment at all**. Consequence, stated plainly: its result says nothing about whether the lease
treatment works, and **cannot certify the grid's `lease-reopen` arm**. Three arms at `shape_ok` plus a
12-turn lease cell that never reaches T23 is not four arms. The grid's lease arm therefore needs its own
first-cell mechanism check — a ≥23-turn (in practice the grid's 48-turn) lease cell whose rows show the
T23 lease step/prefix change — before any grid launch is called fully gated.

## 3. Shape: `shape_unknown`

- `answer_verified ≥ 1`: **fails** — 0 rows. `grade_v5.py`: 9 decidable, 0 pass, 0 fail,
  9 undecidable, all `turn_missing` (text=3); `verified=False`.
- recorded `finish_reason` on the final turn: present — turn 12, `stop`.
- cap-length completions (`completion_tokens == max_tokens`): **none**.
- `stop_signal_source`: absent on 30/30 rows ⇒ the **`CANARY-ERA-B-FIX` gap is still open** on a
  generation-6 tree; nothing in this cell populates it.

The rule's first clause fails, so the cell is `shape_unknown` — not rounded up to `shape_ok`, and not
called `shape_degenerate` because no completion was truncated. Reading the refusal honestly: 12 turns
were too few for this arm to converge on an answer (the earlier 4-arm canary reached only turn 3), while
the treatment it nominally tests starts at turn 23.

## 4. Decision (frozen before the run)

> cell `shape_ok` **and** census non-zero **and** gates (1)+(2) ⇒ `all_four_arms_ok: true`; anything
> else ⇒ `false` with the single measurement that would resolve it.

`all_four_arms_ok: false`, `grid_may_launch: false`. Census non-zero ✓, gate 1 ✓, gate 2 ✓, shape
`shape_unknown` ✗.

**Single measurement that resolves it:** one `lease-reopen` cell at ≥23 turns — the grid's own 48-turn
shape — whose rows carry the **T23 lease step** (prefix change) *and* ≥1 `answer_verified` row. That is
now a named requirement on the grid's lease arm, not an inference from three healthy siblings.

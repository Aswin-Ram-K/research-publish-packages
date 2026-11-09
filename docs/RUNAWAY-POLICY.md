# RUNAWAY-POLICY — what the runaway guard is for, on measurement

**Status:** decided and implemented (unit `RUNAWAY-POLICY`, 2026-10-26). Option **B**.
**Write paths:** `experiments/ptr-engine/longrun/run_longrun.py`,
`experiments/ptr-engine/longrun/tests/test_runaway_policy.py`, this file,
`measure/RUNAWAY-POLICY.json`. `cell.py` and `exit_codes.py` untouched.

## 1. What the code said before this card

Three places disagreed with each other and with the flag's own help:

    ap.add_argument("--runaway-turns", type=int, default=2,
                    help="how many runaway turns (wall cap hit, or a turn that consumed
                         "the whole completion ceiling) end the cell with exit 6 (default 2)")

    def _runaway_signature(row):
        \"\"\"Predicate 2: a turn that consumed the WHOLE completion ceiling is a runaway.\"\"\"

    print(f"RUNAWAY ABORT after T{t}: {runaway} runaway turn(s) (limit {runaway_turns}); "
          f"{sent} request(s) sent, partial rows kept at {rows_path}")

One counter named `runaway`, two different events, one message naming neither precisely.

## 2. THE MEASURED EVENT (cell 1 of `RUN-A*`)

`scratch/uregen1/ws/experiments/ptr-engine/measure/rows-cell-pointer-stable-20261026T182535Z.jsonl`
(27 `kind=turn` rows; sha256 and full census in `measure/RUNAWAY-POLICY.json`):

- census: **25 `stop`, 1 `length`, 1 `runaway_turn`**.
- the two turns the counter fired on: **T3** (`completion_tokens 4096 == max_tokens`,
  `wall_ms 114,838.8`) and **T27** (`completion_tokens 4096`, `wall_ms 115,331.2`,
  `truncated: true`, `runaway_abort` set).
- `turns_over_180s: 0`, `wall_ms_max 115,331`, `wall_ms_p50 2,454`, `wall_ms_p90 16,425`,
  `ttft_ms_p50 141.58`.
- grid action: `stop_rule_7`, `rc 6`, *"cell: 4/7 run REFUSED(6) run_longrun.py exited 6
  (one or more runaway turns ended the cell)"*, `new_requests 27`, `remaining 3,192`.

So: **no turn ran past the 180 s cap, both turns that tripped the guard were 4,096-token
truncations, and the second one aborted a 48-turn cell at T27.** The counter counted
*truncation*; its name, its message and the incident that motivated it described *wall time*.

> **Dated caveat (2026-10-26) — `LATENCY-FIGURE-HONESTY`, the `ttft_ms_p50 141.58` figure in §2:** `experiments/ptr-engine/measure/GRID-CELL-SANITY.json` stamps this cell `usable_for: []` (reason: *"cell in progress: 27/48 turns on disk — a statistic computed now would be from a truncated cell file"*); the 60-turn census that consumed that stamp is `orchestration/handoffs/TURN-CENSUS-60.json` (unit `TURN-CENSUS-60`): **0 of 15** rows files and **0 of 15** arm-by-file rows reach 60 usable turns, the largest is **48**, so `n=27` gives `27 x 0.05 = 1.35 < TAIL_MIN = 3` and no p95 can exist here.
>
> Rows file this figure was computed on: `experiments/ptr-engine/measure/rows-cell-pointer-stable-20261026T182535Z.jsonl`, sha256 `46afc892480ae1dbe4b20d13fd4dacb983653a9f0a04b6a42a6283b3c55ca3b1` (`wc -l` = 27).
>
> **What the number may still be used for:** nothing pooled and nothing comparative — it is one cell's legacy `kind='turn'` p50 (`definition_fallback: true`, see `docs/LATENCY-FALLBACK.md`), quoted only with its `n` and never beside another cell's value.

### Incident history — the hazard the guard was built for
`LIVE-SMOKE-CELL`: one turn produced **16,384 completion tokens in 475,873 ms**. That is the
hazard: a turn whose cost is unbounded in *both* dimensions. It is not the same event as a turn
that ends at `max_tokens` in 115 s.

## 3. What incremented the counter — by `file:line` (pre-patch numbering)

| Event | Site | Threshold behaviour |
|---|---|---|
| wall cap (digest request) | `run_longrun.py:2317` | aborts on the **first** one, threshold ignored |
| wall cap (turn) | `run_longrun.py:2364` | aborts at `--runaway-turns` |
| wall cap (tool-followup) | `run_longrun.py:2446` | aborts at `--runaway-turns` |
| **cap-length completion** | `run_longrun.py:2528`, counted `:2558` (`_runaway_signature`) | aborts at `--runaway-turns` |

`_runaway_signature` returned a reason when `completion_tokens > max_tokens` **or**
`truncated and completion_tokens >= max_tokens`; the second clause is what ended cell 1. A wall
cap reaches that code as `client.TurnWallCap`, raised at **`client.py:537`** from the streaming
loop's **`client.py:529`** clock check.

**What the abort did with the rows: nothing was deleted.** Partial rows stay on disk, the message
said `partial rows kept at <rows_path>`, the ending row carries `error=turn_wall_cap` +
`runaway_abort: true` + `stop_reason=runaway_turn`, and the cell record carries `rows_written` and
`turns_requested` (`cell.py:1604`), so the cell is labelled partial by exit 6 plus a row
count below `turns_requested`. That was already right and is unchanged; the new message makes the
partiality explicit in words (`<t>/<n> turns reached`).

## 4. What still bounds the cost hazard (each bound, with its enforcement site)

1. **Per turn — `--turn-wall-cap 180`.** `client.py:529` checks the clock per chunk,
   `client.py:537` raises `TurnWallCap`, closing the stream mid-turn. A 475 s turn is closed at
   180 s.
2. **Per cell — `--max-wall 2880` via G2.** `cell.py:737`
   (`admitted = max_wall > 0 and projected <= max_wall`), the turn priced at the cap rather than
   at the mean; enforcement on the live path `cell.py:792` and `cell.py:2028` `_enforce(..., 8)`.
3. **Per cell — `--request-allocation`.** `run_longrun.py:2333` (digest) and
   `run_longrun.py:2380` (turn) call `gate.acquire` **immediately before the wire**; a
   `CapRefusal` stops the run through `run_longrun.py:542` `_cap_stop`. Requests, not
   turns, are the unit that bills.
4. **The spawn/gate chain.** The runner launch is recorded by
   `SPAWNS.record(..., purpose="runner_launch")` at `cell.py:1600`, and G1/G2/G3 run on
   every live path at `cell.py:2021` / `cell.py:2028` / `cell.py:2031`. No cell reaches the
   wire without all three.
5. **A server that ignores `--max-tokens`** is the one remaining unbounded-token case; it is
   still counted (§6).

## 5. The three options, priced on the measured rate

Rate: **2 cap-length turns in 27 = 0.0741 per turn**; expected **3.56 per 48-turn cell**.

| Option | What aborts | P(48-turn cell aborts) | Consequence |
|---|---|---|---|
| **A — keep the counter** | 2nd cap-length completion | **0.8796** | only **12.04%** of cells complete; a ten-cell tranche completes with probability **6.4e-10**. Damage is not random: truncation is a property of the *question*, so aborts cluster on the arms whose questions invite long answers — the arms under adjudication. |
| **B — separate the events** | 2nd **wall-time** runaway (>=2 turns past 180 s) | **0.0 observed** (0/27 turns). Sensitivities: wall rate 1-in-27 → 0.5349; rule-of-three 95% upper bound (3/27) → 0.9755; exponential tail fit through the observed p90 → ~1e-19. | `length` becomes data; nothing is discarded to punish a truncated answer. The replacing bound is the per-turn wall cap (§4.1) — the quantity the counter is *named* for. |
| **C — raise the threshold** | k-th cap-length completion | k=4: 0.4799 (52.0% complete); k=5: 0.2817 (71.8%); k=6: 0.1421 (85.8%); k=7: 0.0621 (93.8%); k=8: 0.0237 (97.6%); k=10: 0.0024 (99.8%) | cheapest, keeps the shape — but the number is chosen to make cells pass, the counter still hides what it counts, and 48 turns are still discarded to punish one bad answer. At k=10 the guard is nearly inert while still calling itself a runaway guard. |

## 6. Decision: option B

**The counter must fire on the event whose cost the guard bounds.** A `length` truncation is
*bounded data*: the turn finished inside the wall cap, spent exactly `max_tokens`, and its row
records `stop_reason=length`, which the grader marks wrong or absent. Discarding the other 47
turns does not improve that answer; it deletes 47 measurements. A wall-time runaway is a *measured
cost hazard*: it is the 475,873 ms turn, it is now closed at 180 s by the client
(`client.py:529`), and two of them still end the cell.

Two events are now counted separately, with names that say what they are:

- `wall_runaways` — a turn whose stream `--turn-wall-cap` **closed**. Sites
  `run_longrun.py:2391`, `:2475`, digest `:2341`. Ends the cell at
  `--runaway-turns`.
- `ceiling_violations` — a response with `completion_tokens > max_tokens`, i.e. **a server that
  ignored the ceiling**. Unbounded tokens, no row-level bound on cost: counted against the same
  limit. Predicate `run_longrun.py:2283`, detection `:2559`, counted in the block at
  `:2408`.
- A `length` truncation **is not counted at all**; it is recorded as data.

The digest path's "abort on the first wall cap" is preserved (a *planning* request the planner
cannot continue without) and is now labelled as such.

**New abort message** (real output, two wall-time runaways against a fake stream):

    RUNAWAY ABORT after T2: wall-time runaways 2/2 [T1 (wall 0.4s > cap 0.4s); T2 (wall 0.4s > cap 0.4s)];
    ceiling violations 0/2 [none]; 2 request(s) sent, 2/4 turns reached, partial rows kept at <rows_path>

It names **which turns by index and why** (index, measured wall against the cap), how many of each
counted event, and how much of the cell was reached.

**Exit code:** `6 = EXIT_RUNAWAY`, already in `exit_codes.EXIT_TABLE` and already propagated by
`cell.py:1616`. **No new code; `exit_codes.py` and `cell.py` untouched** — the exit mapping did
not need to change.

## 7. Tests — three ways, with red output

`experiments/ptr-engine/longrun/tests/test_runaway_policy.py` (offline; the only socket is a fake
HTTP server on 127.0.0.1). Green: **3 passed in 2.23s**.

1. **`length` is data** — first turn ends `finish_reason=length` at a 4,096-token ceiling with
   `--runaway-turns 1`: the cell **continues to all four turns and exits 0**. Red A (old predicate
   restored): `assert 6 == 0` — *cell aborted at T1, 1/4 turns reached*; `1 failed, 2 passed`.
2. **the abort fires on the recommended condition** — two wall-time runaways with
   `--runaway-turns 2`: `rc 6`, stderr shows `wall-time runaways 2/2` and names `T1` and `T2`; the
   first runaway row is recorded and the cell survives it, the second ends the cell.
3. **the historical 16,384-token / 475 s hazard is still caught** — a stream that would run for
   hundreds of seconds is closed by `--turn-wall-cap` at ~0.4 s: `error=turn_wall_cap`,
   `truncated: true`, `stop_reason=runaway_turn`, `runaway_abort: true`, `0 < wall_ms < 5000`,
   `rc 6`, message `wall-time runaways 1/1`. Red B (`wall_runaways += 0`, the wall-time abort
   removed): `assert 0 == 6` — the cell runs all four turns and **the hazard test loses its
   bound**; `2 failed, 1 passed`.

Red A is the old code's behaviour on the measured event; red B is option B implemented *without*
the wall-time counter. Both are what the guard is not allowed to be.

## 8. The one-sentence answer

**A 48-turn cell should now complete for truncation reasons (0 wall-time aborts in 27 turns at the
measured 2-in-27 cap-hit rate, where option A would have completed 12.04%), while a single runaway
turn is still bounded twice — closed at 180 s by `--turn-wall-cap`/`client.py:537`, counted by
`wall_runaways`, and priced into G2's per-cell `--max-wall 2880` at `cell.py:737`/`cell.py:2028` —
with a server that ignores the ceiling caught by `ceiling_violations`.**

## 9. What this policy does *not* claim

- Option B's completion figure rests on **0 wall-time runaways in 27 turns** — a small sample. The
  rule-of-three 95% upper bound on the per-turn wall rate (3/27) would still abort 97.6% of cells.
  What makes B safe is not the point estimate but the failure mode: *bounded cost* (every runaway
  turn is closed at 180 s and priced at the cap) instead of *lost cells*.
- Truncated turns are kept and counted but they are **not** good answers. Downstream analysis must
  treat `stop_reason=length` rows as absent/wrong, never average them away. The runner already
  prints `NOTE: N row(s) TRUNCATED at max_tokens=...`.
- The two truncations in cell 1 were also the two slowest turns (114.8 s and 115.3 s = 0.64x the
  180 s cap). Truncation and near-cap wall time co-occur; that is exactly why the wall counter is
  kept rather than dropped.

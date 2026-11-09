# CANARY-ERA-B-4 — the tool channel answers: 40 of 59 rows carry a structured tool call

**Outcome line.** The canary **ran**. Three of four arms completed 12 turns on the generation-6 tree
(`harness_sha256 efefd885…` on every row); the fourth (`lease-reopen`) was killed by host restarts at turn 3
of 12. `grid_may_launch: **false**` — not because the channel failed (it did not), but because one arm is
`shape_unknown` and the card's decision rule forbids rounding that to ok.

## The question this card exists to answer — first, before any shape table

| per arm | rows | `tools_schema_sent: true` | rows with non-empty structured `tool_calls` | `tool-followup` rows | fetch rounds billed |
|---|---|---|---|---|---|
| pointer-stable | 25 | **25** | **16** | 7 | sum(`fetch_rounds_this_turn`) 26; 0 rows flagged `billed` |
| transcript-grow | 13 | **13** | **9** | 0 | 2; 0 flagged `billed` |
| transcript-compact | 14 | **14** | **10** | 1 | 4; 0 flagged `billed` |
| lease-reopen | 7 (turn 3 of 12) | **7** | **5** | 2 | 8; 0 flagged `billed` |
| **total** | **59** | **59 / 59** | **40 / 59** | **10** | 40; 78 call items, **14 executed**, 0 `billed=true` |

Compare the era it replaces: `LIVE-CANARY-4ARM-3` produced **0 structured calls in 36 requests**, and the 48
generation-5 rows on disk carry no `tools_schema_sent` field at all. Here the field exists and is `true` on
every row, the structured channel is the one being consumed (no row needed the text notation), tool calls are
**executed** — `pointer-stable` executed 10 (it read `ptr_engine/resolve.py:66-110` and kept going) — and
`tool-followup` rows exist. **The zeros are gone; the wire works.**

Honest detail: no call item carries `billed: true`, and most parsed calls carry `served_from: "prompt"` — the
reads were satisfied from prompt context rather than paid as separate fetch rounds. The 10 `tool-followup`
HTTP rows are the fetch rounds that were actually sent.

## Shape, per arm (frozen `CANARY-ERA-B-FIX` rules)

| arm | turns | `answer_verified` | terminal `finish_reason` | cap-length | shape |
|---|---|---|---|---|---|
| pointer-stable | 1→12 | **2 true** (t8, t12), 1 false (t6) | `stop` at t12 | 0 | **`shape_ok`** |
| transcript-grow | 1→12 | **1 true** (t12), 2 false | `stop` at t12 | 0 | **`shape_ok`** |
| transcript-compact | 1→12 | **1 true** (t12), 2 false | `stop` at t12 | 0 | **`shape_ok`** |
| lease-reopen | 1→3 | none | `tool_calls` at t3 (in flight) | 0 | **`shape_unknown`** |

Every `shape_ok` above rests on the **recorded `finish_reason` fallback**, labelled as such: `stop_signal_source`
is **absent from all 59 rows** (the key does not exist). That is the open `CANARY-ERA-B-FIX` gap, named here and
not softened — the classification would be stronger if the field were populated, and it still is not.

No row anywhere carries `finish_reason: length`, `truncated: true`, `stop_reason: runaway_turn` or
`turn_wall_cap`, so no arm is degenerate by the cap-length rule.

## The gates, quoted

| gate | requirement | measured | verdict |
|---|---|---|---|
| 1 | pin generation ≥ 6, digest matches | `generation: 6`, `harness_sha256 efefd8859c3fdeeac288157ba5bceba1bbe4144947af441721a5f4c4369579b3`; I re-hashed all six inputs and rebuilt the composite from `cell.py:129-135` + `:340-346` → **same value**, all six match | **PASS** |
| 2 | dry run exits 0, `canary_arms=4 canary_requests=48 refused=0`, G1/G2/G3 + `RUN-A DRY END` | exit **0**: `G1 1,236/4,320 requests · G2 720 s of 900 s · G3 n=12 (smoke, non-comparable)` ×4, then `RUN-A DRY END cells=4 refused=0 requests=0 … canary_arms=4 canary_requests=48` | **PASS** |
| 3 | argv carries the gen-6 digest | `run_a_star.py:786  "--expect-harness", pinned_digest()`; `PIN_EXPECTED_GENERATION = 6`, `pinned_digest() → efefd885…` (not the gen-5 `35ff41b7…`) | **PASS** |
| 4 | ledger before/after delta ≤ 52 | before **and** after: `requests 1176 / remaining 3144 / generated_at_utc 2026-10-26T22:33:00Z` — the ledger **did not move**, because the launcher was killed before its rebuild. The rows on disk bill **59** requests (10 follow-ups + 2 duplicate bodies), 11 above the priced 48 | **no delta measured — a stale snapshot, reported as a finding** |

## Two things that are wrong and were not repaired here

1. **`cell.py` moved outside the pin.** Generation 6 froze at `2026-10-26T23:25:10Z`; `cell.py`'s mtime is
   `2026-10-27T00:17:51Z` and its sha is `c494e212679f8e73c84226cf486566d0716559c0f2cd677f20845b24057baf86`,
   where the previous execution of this card observed `0bddd4e0…`. The composite digest is immune (`cell.py`
   is not in its own `HARNESS_FILES`), so gate 1 still passes — but the gate script is outside pin coverage,
   and the change is unattributed.
2. **The card's invocation string cannot be run verbatim.** `--thinking off --max-turns 12 --turn-wall-cap 180
   --runaway-turns 2 --no-cell-handoff` are rejected by `run_a_star.py:928` (`parse_args`: `unrecognized
   arguments`, exit 2, 0 requests — probed). The same five values are hard-coded in `cell_argv`
   (`run_a_star.py:781-787`) and the canary passes `--turns 12`, so the intended shape **is** what ran.

## Decision (frozen before the rows were read, applied after)

- all four `shape_ok` ⇒ `grid_may_launch: true` — **not met** (three of four)
- any degenerate ⇒ `false` with arm/turn/cause — no arm degenerate
- any unknown ⇒ `false` **plus the one measurement that resolves it** — `lease-reopen` is `shape_unknown`

**`grid_may_launch: false`.** Resolving measurement: **one complete 12-turn `lease-reopen` cell** on the same
generation-6 tree (12 rows, a terminal `finish_reason`, `answer_verified` on its answer turn).

A hold is a successful result, and this one is cheap to convert: the channel the last three live canaries could
not reach is demonstrably working.

## Run account

- one invocation: `/usr/bin/python3 experiments/ptr-engine/tools/run_a_star.py --tools read_file --canary --budget 108 --hypothesis smoke --max-wall 900` — no retry
- exit code **unknown**: two host restarts killed the process during `lease-reopen`; three arms wrote their
  `grade-v5`/`analysis`/`md` artefacts, the fourth wrote 7 rows and nothing else
- every row: `claim: "none"`, `comparison_eligible: false` — smoke, pools with nothing

## Files

- `experiments/ptr-engine/measure/CANARY-ERA-B-4.json` — the record (this execution; the first execution's
  outcome is carried in its `prior_execution` block)
- rows: `rows-cell-pointer-stable-20261027T004027Z.jsonl`, `rows-cell-transcript-grow-20261027T004129Z.jsonl`,
  `rows-cell-transcript-compact-20261027T004155Z.jsonl`, `rows-cell-lease-reopen-20261027T004219Z.jsonl`

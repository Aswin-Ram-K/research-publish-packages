# CANARY-FALSE-POSITIVE — does the pre-tranche canary control the tools-on shape it must bless?

Unit `CANARY-FALSE-POSITIVE`, 2026-10-26. **Offline: zero requests, zero network.**
Instrument under test: `experiments/ptr-engine/tools/tranche_canary.py` (19236 B), replay mode only.
Nothing was edited. This file reports; rule changes are a separate card.

## Verdict

**`canary_blind`** — the positive control fires (turn 3), so the tool is not broken. But on the shape it
must now bless (tools-on, era B) it answers `shape_unknown` on **3 of 3** files at **every** window
N ∈ {2, 5, 8, 12}, and `shape_ok` is *structurally unreachable* on those rows. It cannot distinguish a
healthy tools-on cell from a degenerate one inside the launch window.

## Inputs (read-only; all counts measured this run)

| file | rows | turns | sha256 (first 16) | shape | `stop_reason` rows | `answer_turn` rows | cap hits |
|---|---|---|---|---|---|---|---|
| `experiments/ptr-engine/measure/rows-cell-pointer-stable-20261026T182535Z.jsonl` | 27 | 27 | `46afc892480ae1db` | era A, tools-off (known positive) | 27/27 | 8/27 | T3, T27 |
| `experiments/ptr-engine/measure/rows-cell-pointer-stable-20261026T145758Z.jsonl` | 6 | 6 | `5ac9dd992f5d8715` | era A, pre-`stop_reason` | 0/6 | 0/6 | T5 (16384) |
| `experiments/ptr-engine/measure/rows-longrun-v4-tools-2026-10-26.jsonl` | 68 | 48 | `f11391aa2989949f` | era B, tools-on (`read_file`) | **0/48** | **0/48** | T45 |
| `experiments/ptr-engine/measure/rows-longrun-v5-tools.jsonl` | 72 | 48 | `586b66f27939bd05` | era B, tools-on | **0/48** | **0/48** | T29 |
| `experiments/ptr-engine/measure/rows-longrun-v6-tools.jsonl` | 72 | 48 | `1e78d75f259afbe0` | era B, tools-on | **0/48** | **0/48** | none |

Tools-on status is not assumed from the filename: `experiments/ptr-engine/longrun/manifests/v4tools-pointer-stable-r1-pointer-stable-r1.json`,
`v5tools2-pointer-stable-pointer-stable-r1.json` and `v6-pointer-stable-pointer-stable-r1.json` each carry a
`tools` block (`names: ["read_file"]`, `max_calls_per_turn: 2`, `followups_are_requests: true`).

## 1. Known-positive control (must fire first) — FIRES

`python3 tools/tranche_canary.py --rows measure/rows-cell-pointer-stable-20261026T182535Z.jsonl --turns 5` → `exit=1`

> `shape_degenerate exit=1 arm=pointer-stable rep=1 n=5 turns=5` **turn 3 completion_tokens=4096 max_tokens=4096
> wall_ms=114838.846 stop_reason=length (completion_ceiling)**

Same verdict at N ∈ {5, 8, 12, 48}; at N=48 it also reports `turns=27` (the cell died at T27 with
`runaway_turn`). The instrument has not regressed. Secondary positive: the 6-row
`rows-cell-pointer-stable-20261026T145758Z.jsonl` fires at **T5** (16384/16384, `wall_ms=475873.291`,
`truncated=true`) for N ≥ 5. At N=2 the era-A control does **not** fire (`no_parseable_answer`), so N ≥ 3
is the floor for keeping the positive control live.

## 2. Every tools-on file at N=5 — ALL `shape_unknown`, none fires, none says ok

| file | N=5 verdict | trigger (turn) | evidence |
|---|---|---|---|
| `rows-longrun-v4-tools-2026-10-26.jsonl` | `shape_unknown` (exit 2) | `stop_reason_outside_vocabulary` (turn 1) | `stop_reason=None`; row carries `finish_reason="stop"` instead |
| `rows-longrun-v5-tools.jsonl` | `shape_unknown` (exit 2) | `stop_reason_outside_vocabulary` (turn 1) | `stop_reason=None` |
| `rows-longrun-v6-tools.jsonl` | `shape_unknown` (exit 2) | `stop_reason_outside_vocabulary` (turn 1) | `stop_reason=None` |

**No tools-on file fires at N=5** — so there is no false `shape_degenerate` on a healthy tools-on cell in
this corpus. There is also no `shape_ok`: two independent schema drifts make `ok` unreachable on era B rows.

- `tranche_canary.py:271-280` requires `row["stop_reason"] ∈ STOP_REASONS`. Era B writes **`finish_reason`**
  (`run_longrun.py:1858`), never `stop_reason` (`run_longrun.py:1862` writes it, but 0/144 era B turns carry it).
- `tranche_canary.py:170-180` (`_parseable_answer`) requires `answer_turn`. Era B has **0/144** rows with it,
  so `parseable_answers == 0` and step 4 (`:283-291`) would answer `no_parseable_answer` even if the
  stop reason were readable. Verified: v6 at N=48 still returns `shape_unknown`.
- Era B also has **0/144** `wall_ms` rows (it carries `latency_s`/`ttft_ms`), so a tools-on firing would
  print `wall_ms=None` — the evidence line the card asks for is not populated by these rows.

## 3. The window question — the verdict does not change with N in {2,5,8,12}

| N | v4-tools | v5-tools | v6-tools | era A control | 6-row cell |
|---|---|---|---|---|---|
| 2 | unknown | unknown | unknown | unknown (no answer in window) | unknown |
| 5 | unknown | unknown | unknown | **degenerate T3** | **degenerate T5** |
| 8 | unknown | unknown | unknown | degenerate T3 | degenerate T5 |
| 12 | unknown | unknown | unknown | degenerate T3 | degenerate T5 |
| 48 | **degenerate T45** | **degenerate T29** | unknown | degenerate T3 | degenerate T5 |

First cap-length completion per tools-on file: **v5 turn 29**, **v4 turn 45**, **v6 none** (max 3283/4096 at
turn 26, 80.1 % of ceiling). Earliest across the corpus: turn 29. So N=5 sits 24 turns before the earliest
observed tools-on cap-length completion — but that fact is currently invisible, because the schema, not the
window, decides the verdict. **N=5 is a defensible floor for this shape; it is not a detector for it.**

Were the reader fixed, N=5 would say `ok` on all three files and N=48 would flip v5 and v4 to `degenerate`.
That flip is correct, not noise: at T29 (v5) and T45 (v4) the turn emitted **130** and **116** `read_file`
calls, `finish_reason="length"`, `truncated=true`, `failed_turn=true`, against `max_calls_per_turn: 2` in the
manifest. That is runaway tool fan-out, not a long answer. By contrast v6's 3283-token turn 26 has 101
tool calls, `stop`, `failed_turn=false`.

## 4. `shape_unknown` rate

**3 of 3 tools-on files** at N=5, N=2 and N=8, N=12 (and v6 at N=48): 100 % of the tools-on corpus.
This is **not** "the shape is undetermined". The unknown is caused by the *reader* not matching the *row
schema* (era A rows have `stop_reason`+`answer_turn`; era B rows have `finish_reason` and neither).
An instrument that answers `unknown` on the only shape it must bless is not a gate; and because
`unknown` is not `degenerate`, a gate written as "any `shape_degenerate` ⇒ STOP" waves it through.

## 5. The threshold, stated

`tranche_canary.py:162-168` (`_cap_hit`) + `:234-257`: a turn is degenerate when
`completion_tokens >= max_tokens` (or `truncated and stop_reason=="length"`), **or** `stop_reason ∈
{runaway_turn, turn_wall_cap}`, anywhere in the first N turns. `_parseable_answer` etc. only decide `ok` vs
`unknown`.

Is the ceiling rule **too strict**? Not on *substance* for this corpus — its two late fires (T29, T45) are
real runaway turns. It is **too coarse**: it cannot tell a 4096-token answer from a 4096-token runaway, and
v6 shows a healthy turn at 80 % of the ceiling, so a legitimate long answer in a shorter window would be
condemned identically. Recommended rule (NOT applied — recommend only):

1. Read `stop_reason`, falling back to `finish_reason` when absent (era B), and never report a missing
   stop reason as `shape_unknown` when a `finish_reason` is present — that is a reader bug, not evidence.
2. Keep `completion_tokens >= max_tokens` as a *trigger*, but require corroboration before `degenerate`:
   `failed_turn is true`, or the checkpoint's answer is unparseable, or tool fan-out in that turn exceeds a
   calibrated bound. Do not guess that bound from n=3 files: v5 turn 3 already has 24 tool calls with
   `finish_reason="stop"`, so a naive ">20 calls" bound would fire on a healthy turn (false positive).
3. Check the answer contract instead of the ceiling where the contract is checkable: era B rows carry
   `answer_verified` (1/48 in v4 at T12, 1/48 in v6 at T12, 0/48 in v5) — thin, but it is the contract,
   whereas `answer_turn` is simply absent.
4. A single truncated turn inside a cell that completed 48 turns with one verified checkpoint answer is a
   **1-turn loss**, not the era-A **27-request, 0-cell** loss. The verdict should say which class it saw.

## 6. What RUN-A-STAR-2's canary gate should be

**One sentence:** the gate should require the canary to print `shape_ok` on the tools-on cell's first 12 turns
with `stop_reason` read from `finish_reason` and the answer contract confirmed by a checkpoint
`answer_verified` — `shape_degenerate ⇒ STOP`, **and `shape_unknown` ⇒ STOP as well**, because on the
launching shape an unreadable row is indistinguishable from an unmeasured one.

The card's current wording (`any shape_degenerate ⇒ STOP`) is **necessary but not sufficient** for the
tools-on shape: as written, tomorrow's launch produces `shape_unknown`, which is not `shape_degenerate`, and
the gate would read that as permission.

**If I ran this canary live tomorrow on the launching shape, what would it say?** It would print
`shape_unknown exit=2 … turn 1 … stop_reason=None (stop_reason_outside_vocabulary)` at every N, because a
live tools-on run writes era B rows through `run_longrun.py` (`finish_reason`, no `answer_turn`). That answer
would **not be right** — the shape is not unknown, the reader is out of date — and it is the most expensive
kind of wrong: it looks like caution and behaves like a pass.

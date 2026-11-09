# FETCH-BUDGET-48 — does the 24-round per-arm fetch budget survive a 48-turn tools-on cell?

**Unit:** `FETCH-BUDGET-48` · **Cost:** 0 inference requests, 0 network events, 0 live cells.
**Conclusion: `budget_sufficient`** — in the modern tools-on shape the budget does not close, so all
48 turns are measurement. The closure that *did* happen on disk is the pre-V6 configuration, and it
confounded 45 turns.

Machine-readable twin: [`FETCH-BUDGET-48.json`](../experiments/ptr-engine/measure/FETCH-BUDGET-48.json).

## 1. Budget consumption per arm, per turn

Every tools-on rows file on disk, measured three ways: rows, billed rounds (the thing the budget
counts), and the turn at which 24 would have been reached.

| file | runner era | rows | rounds used | turn 24 reached | last billed turn | post-closure turns |
|---|---|---|---|---|---|---|
| `rows-longrun-v6-tools.jsonl` | **V6** (cap 3/turn, serve-from-prompt) | 72 | **20** | **never** | T16 | **0** |
| `rows-longrun-v4-tools-2026-10-26.jsonl` | V5 (no per-turn cap) | 68 | 20 | never | T30 | 0 |
| `rows-longrun-v5-tools.jsonl` | V5 (no per-turn cap) | 72 | **24** | **T3** | T3 | **45** |

`billed_round` is the field the runner sets on a follow-up row that bought a round
(`run_longrun.py:226`, `TOOL_FETCH_ROUNDS_PER_ARM = 24`; the V5-era files carry no such field, so
their rounds are counted as follow-up rows, which is what bought the request). A call answered from
a pinned prompt body is **not** billed.

Cumulative rounds by turn, V6 — the modern shape:

```
turn      1  2  3  4  5  6  7  8  9 10 11 12 13 14 15 16 17..48
rounds    0  0  2  3  0  0  0  0  3  3  1  1  1  0  3  3  0 ... 0
cum       0  0  2  5  5  5  5  5  8 11 12 13 14 14 17 20 20 ... 20
```

Per-turn histogram: `{0: 39 turns, 1: 3, 2: 1, 3: 5}` — p50 0, p90 3, max 3, mean 0.417/turn,
mean over *inviting* turns 2.22. The demand is **front-loaded and terminal**: every round the cell
ever bought was bought by T16, and the remaining 32 turns bought none.

V5, for contrast — the budget closed inside one turn:

```
turn      1  2   3  ... 48
rounds    1  2  21   0 ... 0        cum: 1, 3, 24, 24, ... 24
```

**A single recon burst at T3 bought 21 of the 24 rounds.** That is the failure the per-turn cap
(`run_longrun.py:232`, `TOOL_FETCH_ROUNDS_PER_TURN = 3`) and serve-from-prompt
(`run_longrun.py:237`) were added to remove, and V6 is the first cell that ran with both.

## 2. What the runner does at exhaustion — quoted

`experiments/ptr-engine/longrun/run_longrun.py:940-950`:

```python
elif rounds_used + fresh >= TOOL_FETCH_ROUNDS_PER_ARM:
    # The per-arm ROUND budget is spent.  This refusal is per CALL, not per
    # turn: a range the prompt already carries still costs no round, so the
    # T46 checkpoint read stays servable after the round budget is gone
    # (the exact v5 starvation this unit exists to remove).
    rec = {"path": call["path"], "start_line": call["start_line"],
           "end_line": call["end_line"], "executed": False,
           "truncated": False, "billed": False,
           "error": "fetch_budget_exhausted"}
    round_calls.append(rec)
    blocks.append('<tool_result error="fetch_budget_exhausted"/>')
    continue
```

- **Refusal name:** `fetch_budget_exhausted`, recorded in the row's `tool_calls[].error` with
  `executed: false, billed: false`. The model receives an **empty** `<tool_result>`.
- **Per call, not per turn.** A range already pinned into the prompt is still served
  (`served_from: "prompt"`) and still costs no round, so a checkpoint read survives the closure.
- **No exit code at this boundary.** The turn continues and is billed as a normal completion; the
  run only dies later if the *completion* runs away. `BudgetExhausted` is a different, earlier
  refusal (`run_longrun.py:961`, per-cell `--budget`).
- **The row does not mark the channel closed.** There is no `channel_closed` field; the only
  evidence is the error string, and the next turn may still be served from a pinned body. The
  closure is therefore *silent in the aggregate* — visible only by censusing `tool_calls[].error`.
- Sibling bounds: `per_turn_round_cap` (`run_longrun.py:912-918`) and `turn_call_cap`
  (`run_longrun.py:955-958`).

## 3. What the rows show after exhaustion

**V6 never exhausted the budget, so it has no post-closure turns.** Across 371 tool calls in the V6
cell there are **0** `fetch_budget_exhausted` refusals. Errors are all other bounds:
`turn_call_cap` 236, `per_turn_round_cap` 7, `path_not_found` 10, `range_out_of_bounds` 2, none 116.

**V5 is the only arm that closed, at T3.** Its 45 post-closure turns (T4–T48):

| measurement | count |
|---|---|
| post-closure turns | 45 |
| turns that still emitted tool calls | **41** |
| `fetch_budget_exhausted` refusals in the window | **226** |
| cap-length completions after closure | **1** — T29, `completion_tokens=4096 / max_tokens=4096`, `finish_reason=length`, `truncated=true`, 130 refused calls in that turn |
| post-closure `stop_reason` values | 44 `stop`, 1 `length` |
| largest non-cap completion after closure | T36, 779 tokens, 25 refused calls |

Counts, not rates: **one** 4,096-token completion in 45 confounded turns, and it is the 4,096-token
figure exactly — the signature of a turn spending the ceiling on an inspection it cannot perform.
V6's own tail looks nothing like this: T25–T48 reach 3,283 and 1,096 tokens but every one of them
`stop`, untruncated, and none refused for budget.

## 4. The invitation's fate

The census rule is the one `GRID-SHAPE-TOOLS` used: *`invites-read` = the question names a source
path* (`docs/GRID-SHAPE.md:32`). Re-derived here from the fixtures themselves:

| fixture | path-ref turns | non-inviting turns | sha256 (prefix) |
|---|---|---|---|
| `tasks-v6/LR-01.v8.json` | **46/48** | T30, T48 | `0804b51575cce345` |
| `tasks-v6/LR-01.v7.json` | **46/48** | T30, T48 | `42b4df007352d939` |

Agrees with the published census in `docs/GRID-SHAPE.md:34-44`.

**After V5's closure (T4–T48): 43 of 45 turns still invite a read** (the window contains both
non-inviting turns). The invitation **persists while the channel is shut** — and the model acts on
it: 41 of those 45 turns emitted a tool call, 226 of which were refused. That is the degeneration
condition, still present, exactly as `GRID-SHAPE-TOOLS` described it.

The modern shape differs in one load-bearing way: after T16 the V6 model kept emitting calls
(28 at T25, 101 at T26, 45 at T35) but **they were served from pinned bodies or refused at the
per-turn cap, never for budget** — so the invitation was answered rather than starved.

## 5. Arithmetic for the fix

Identity: **price = turns + rounds + digests**, per grid.

| budget B | rounds (10 cells) | turns | digests | price | leaves of 3,192 | Δ vs 724 |
|---|---|---|---|---|---|---|
| 20 (measured cell total) | 200 | 480 | 4 | 684 | 2,508 | −40 |
| **24 (frozen now)** | 240 | 480 | 4 | **724** | 2,468 | 0 |
| **48 (recommended)** | 480 | 480 | 4 | **964** | **2,228** | **+240** |
| 144 (= 3 × 48, structural) | 1,440 | 480 | 4 | 1,924 | 1,268 | +1,200 |

Largest budget the headroom buys: `(3,192 − 484) / 10 = 270.8` → **B = 270**, price 3,184.

Measured demand is **20 rounds per 48-turn cell** (v6 and v4 both), so B = 20 is the minimum that
covers the measured demand and B = 24 already exceeds it by 4. **Recommendation: B = 48** — one
round per turn by construction, 2.4× the largest measured cell, and +240 requests against 3,192
remaining. It is a margin, not a proof: with the per-turn cap at 3, a cell that spends the cap on
16 consecutive turns still closes at T16. Only **144** makes closure impossible in a 48-turn cell,
and that triples the tranche price.

**Two flags for the separate budget-change card:**

1. `GRID-SHAPE.json`'s cell flags carry `--budget 67` while the same cells project
   `48 + 24 = 72` requests. Any allowance above 19 makes turns + rounds exceed 67, so raising the
   fetch budget without raising `--budget` converts this question into a `BudgetExhausted` exit
   (`run_longrun.py:961`). The budget change must move both numbers.
2. **The headroom figure the card carries (3,192) is right, and the frozen artefact is stale.**
   `REQUEST-LEDGER.json` still reads `spent 1,101 / remaining 3,219`, but a fresh scan of the
   request corpus reads **`raw=1128`, `remaining_raw=3192`** (printed by
   `experiments/ptr-engine/tests/test_request_ledger_dedup.py::TestRealCorpus`). The 3,192 is
   therefore the current remaining, 27 below the artefact; I used **3,192** here, conservatively.
   **Two pre-existing tests fail on that drift** —
   `test_request_ledger_dedup.py::TestRealCorpus::test_6_real_corpus_raw_1101_deduplicated_1071` and
   `test_request_ledger_sound.py::TestPublishedArtefact::test_11_artefact_matches_a_fresh_scan` —
   and neither is caused by this unit (nothing here wrote a ledger row). They need a fixing card
   before the tranche, because a tranche launched on a stale ledger is a tranche whose gate
   arithmetic is 27 requests optimistic.

## 6. Residual risk and the stop rule that bounds it

- **Earliest structural closure is T8** — `24 rounds / 3 per turn`. A cell that spends the per-turn
  cap from the start closes at turn 8 and spends the remaining 40 turns with the channel shut.
- **The canary cannot see this.** It runs 5 turns per arm (`docs/TRANCHE-CANARY.md:24`, N=5).
> **CORRECTION 2026-10-26 — `LAUNCH-PACKAGE-RECONCILE`.** The sentence above said the canary
  > runs 5 turns per arm. That was the per-turn window; **the canary is now N = 12**
  > (`docs/TRANCHE-CANARY.md:23`, corrected 2026-10-26), because
  > `experiments/ptr-engine/measure/CANARY-ERA-B-FIX.json` measures `era_b_gateable: true` only
  > from N=12 (0 of 3 tools-on rows reach a definitive verdict at N=5; 3 of 3 do at N=12).
  > The gate is **N = 12, `shape_ok`, `answer_verified >= 1`, `stop_signal_source = finish_reason`**.
  > The superseded wording is preserved verbatim: *"It runs 5 turns per arm
  > (`docs/TRANCHE-CANARY.md:24`, N=5)."* — **the argument below survives the correction**: at 48
  > rounds and 3 rounds per turn the earliest structural closure is still T16, so a 12-turn window
  > still cannot observe fetch-budget exhaustion; it now also clears the T12 checkpoint, which is
  > why N=12 is the right window and N=5 was never a gate.
  Because exhaustion is arithmetically impossible before T8, a 5-turn window **can never observe
  fetch-budget exhaustion**. The canary protects the cap-length degeneration (observed from T3
  onward) and does **not** protect this failure mode. Stated plainly: this failure mode is not
  covered by the pre-tranche canary at any setting of its window below 9 turns.
- **The stop rule that bounds it:** the card names **rule 8 of `RUN-A-STAR-2`** (cap-length
  completions). **That document is not on disk** — `grep -rn "STAR-2"` returns zero hits, and
  `orchestration/units/RUN-A-STAR.md:18` carries "stop rules 1-7 as carried by the card".
  The mechanism rule 8 names does exist and is what I can verify:
  `experiments/ptr-engine/longrun/run_longrun.py:2560` —
  `if signature and ceiling_violations + 1 >= runaway_turns:` with `--runaway-turns 2`, ending the
  run at exit 6 on the **second** cap-length completion. It fires, but only *after* the cell has
  already spent ≥2 turns (≥8,192 completion tokens) answering nothing: it converts confounded turns
  into a loud abort, it does not save the cell's data. And it is not a budget-exhaustion detector at
  all — it sees the *symptom* (cap-length completion), not the cause.

## 7. Answer

**`budget_sufficient`.** In the only 48-turn tools-on cell that ran the modern configuration the
budget did not close — 20 of 24 rounds, all by T16, zero `fetch_budget_exhausted` refusals in 371
tool calls — so every turn of that cell, including every checkpoint after T16, was served and
measured. The closure on disk belongs to the pre-cap configuration and is the reason the cap exists.

**Can a 48-turn tools-on cell be a measurement all the way to turn 48? Yes — with this budget and
these rows it was, and the 4 spare rounds are the whole margin; a heavier realisation can still
close at T8, and neither the canary nor rule 8 would tell you before the turns were spent.**

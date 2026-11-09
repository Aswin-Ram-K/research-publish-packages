# CANARY ERA B — the four-arm live canary (LIVE-CANARY-4ARM)

**Result: the grid stays HELD. The live canary never sent a model request — `cell.py` refused at
stage `3b/7 projection` (exit 8) on cell 1 of 4, before the runner started, so all four arms are
`shape_unknown` and nothing was measured.** Spend: ledger 1,128 → 1,128 (`delta 0`), plus **1
warm-up** completion that produces no row.

## 1 · Preflight was green (and that is the problem)

```
$ python3 experiments/ptr-engine/tools/run_a_star.py --tools read_file --canary --budget 108 --dry-run
RUN-A canary arms=4 cells=1,4,7,9 turns=12 requests=48 claim=smoke
RUN-A DRY END cells=4 refused=0 requests=0 claim=smoke turns=12 max_wall=900 canary_arms=4 canary_requests=48
rc=0
```

Every cell printed the same three allow lines — cells 1 `pointer-stable`, 4 `transcript-grow`,
7 `transcript-compact`, 9 `lease-reopen`:

```
G1 allow computed=1,188 requests limit=4,320 requests   (cap 4,320 - reserve 0 - spent 1,128)
G2 allow computed=720 s limit=900 s (--max-wall)        artefact=PROJECTION.json
G3 allow computed=claim=none declared (smoke/plumbing)  limit=no claim is made
```

## 2 · The live invocation, once

```
$ python3 experiments/ptr-engine/tools/run_a_star.py --tools read_file --canary --budget 108
RUN-A start spent_rows=1128 cells=4 tools=read_file canary=True claim=smoke turns=12 max_wall=900
RUN-A warmup pointer-stable ok ms=275.5 usage={"prompt_tokens": 17, "total_tokens": 25, "completion_tokens": 8, ...}
RUN-A CELL 1 pointer-stable r1 rc=8 dur=0.2s remaining=3219 p95=None acc=None markers=None
RUN-A STOP rule 7: cell 1 exited 8
RUN-A END cells=1 new_requests=0 remaining=3219 stops=[{'rule': 7, 'cell': 1, 'rc': 8}]
```

The refusing line, quoted:

```
cell: 3b/7 projection REFUSED(8) G2 projection REFUSED: computed 2880 s | limit 900 s (--max-wall)
      | projected wall 2880 s = 48 requests to send (12 turn(s) x 1 rep(s)) x calibrated per-turn
      wall 60.0 s for thinking off (source artefact-mode) exceeds the allowed 900 s by 1980 s
cell: EXIT 8 — refused at stage 3b/7 projection; nothing was measured
```

## 3 · The defect: the dry run and the live gate price different shapes

Two operands, same gate, factor 4:

| path | operand | arithmetic | verdict |
|---|---|---|---|
| dry run | `cell.py:1968-1970` `turns_total = --turns(12) x arms(1) x reps(1)` = **12** | 12 × 60.0 s = 720 s | `allow` (≤ 900 s) |
| live | `cell.py:354-369` `stage_budget` runs `run_longrun.py --dry-run` **without `--turns`**, so the runner prices the fixture's N | `turn_requests=48 (N=48 x reps=1) … would_send_total=48` → 48 × 60.0 s = 2880 s | `REFUSED(8)` (> 900 s) |

`LAUNCH-CANARY-WALL` made the dry run *count* a `WOULD-REFUSE` line as a refusal — it did not make
the preview's operand equal the live operand. `refused=0` therefore still cannot certify a live
`allow`, which is exactly what this card was asked to confirm end-to-end. It does not.

The mismatch is **canary-specific**: the grid asks `--turns 48 --max-wall 2880`, and its live operand
is the same 48 → 48 × 60 = 2880 s sits exactly **on** the limit (allow at the boundary). The 12-turn
canary is the only shape whose wall (900 s) is below its live operand (2880 s).

## 4 · Per-arm classification (`CANARY-ERA-B-FIX` rules, not re-implemented)

| arm | cell | turns | answer_verified | parseable_answers | stop_signal_source | first_cap_turn | wall_ms max | ttft p50 | tool_calls | fetch_rounds_used | verdict |
|---|---|---|---|---|---|---|---|---|---|---|---|
| pointer-stable | 1 | 0 | – | 0 | – | – | – | – | 0 | 0 | `shape_unknown` (exit 8) |
| transcript-grow | 4 | 0 | – | 0 | – | – | – | – | 0 | 0 | `shape_unknown` (never reached) |
| transcript-compact | 7 | 0 | – | 0 | – | – | – | – | 0 | 0 | `shape_unknown` (never reached) |
| lease-reopen | 9 | 0 | – | 0 | – | – | – | – | 0 | 0 | `shape_unknown` (never reached) |

`shape_ok` requires `answer_verified ≥ 1` **and** `stop_signal_source = finish_reason`; no arm has a
single turn row, so `tranche_canary.py` has nothing to read and the verdict is `shape_unknown` by the
"no traffic at all" clause. It is **not** rounded to ok.

## 5 · Decision — grid HELD

Held because **no arm was measured**. The block is pre-request: a gate, not model behaviour. There is
no degenerate *turn* to name (no turn exists); the evidence is
`STOP rule 7: cell 1 exited 8` + `computed 2880 s > limit 900 s`.

**Measurement that would resolve it:** one live 12-turn cell per arm that actually reaches T12 and
writes 12 `kind=turn` rows, then `tranche_canary.py --rows <rows-file> --turns 12 --arm <arm>`. That
needs either (a) `stage_budget` forwarding `--turns 12` to the runner, making the live operand 12 →
720 s ≤ 900 s, or (b) a canary `--max-wall ≥ 2880 s`. Both are outside this unit's write scope
(`cell.py` and `run_a_star.py` are frozen for this card).

## 6 · Era-B shape findings era A never had

**None measurable, and that is the finding.** The era-B schema does carry the fields — a precedent
row (`rows-longrun-v6-tools.jsonl`, pointer-stable T1) reads `prompt_tokens=3520`,
`cached_tokens=2944` (83.6% cached), `finish_reason`, `tool_calls`, `fetch_rounds_used`,
`fetch_rounds_cap_per_turn` — but this invocation wrote **zero** rows:

- **cached-token share per arm:** not measurable (0 turn rows).
- **stop-reason census:** empty (no `finish_reason` emitted).
- **`turn_call_cap` / `fetch_budget_exhausted`:** never reached; the only cap that fired was the
  projection gate at stage 3b/7, which is a gate refusal, not a turn.

## 7 · Did 48 requests buy certainty?

**No — and it bought something better for free.** Zero model requests were spent, yet the launch
shape was disproved at its first gate; had the 900 s canary wall been trusted because the dry run said
`allow`, the grid's own launch would have been authorised on a gate whose preview had never been
reconciled with its live operand. The remaining certainty — whether the four arms produce
`shape_ok` turns at T12 — is still **un-bought**, which is why the grid stays held.

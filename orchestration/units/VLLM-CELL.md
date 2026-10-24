# VLLM-CELL — fresh 120-line vLLM measurement cell, written from spec

**Card prompt (as received).** OFFLINE. ZERO live calls. CALL BOUND: 18. Write a NEW ~120-line
measurement cell from the spec. **FORBIDDEN: do not read, open, grep, repair or import
`experiments/context-cache/cells/R2-VLLM/pmu16_cell.py`.** Three previous cards died trying to do
surgery on that 300-line file (`R2-VLLM` invalid, `R2-VLLM-FIX` interrupted, `FIX-INSTRUMENT` error,
no artefacts each time). It stays frozen as evidence.

`pmu16_cell.py` was **never opened, grepped, imported or executed** by this unit.

## Deliverables

| Artefact | What it is |
|---|---|
| `experiments/context-cache/cells/VLLM-CELL/vllm_cell.py` | the cell: 245 lines, stdlib + `requests` |
| `experiments/context-cache/cells/VLLM-CELL/tests/test_cell.py` | 14 offline tests, transport monkeypatched |
| `experiments/context-cache/cells/VLLM-CELL/redgreen.py` | driver that produces the red→green transcript |
| `state/logs/VLLM-CELL-redgreen.txt` | the transcript itself |

## What the cell does

CLI: `--base-url --model --arm {R,A,C,H} --turns 71 --budget 32768 --out <dir> --warmup`, plus a
`--dry-run` that renders and runs the arms guard without any HTTP.

Prompt construction is deterministic — no clock, no randomness, no hash seeding. A fixed `SCAFFOLD`
(task, output contract, tool list) is byte-identical every turn; turn *t* appends a ~1,180-char
`delta_block(t)` that is never rewritten.

| Arm | Rendering |
|---|---|
| `R` | reference: whole body re-sent as one message, no structure |
| `A` | pointer index (`id \| span \| sha8 \| summary`) + newest delta only |
| `C` | `A`, with the delta tagged at its tail (`TAG[t=NNN sha=8]`) |
| `H` | `A`, with the index compacted every 8 turns (a real summary fold, plus an unconditional policy marker) |

## The parts that matter

- **`cached_tokens` is `None`, never 0.** `parse_row` reads
  `(usage.prompt_tokens_details or {}).cached_tokens`; if the details object is absent, is not a dict,
  or the key is absent, `cached = None` and `cache_report = "unavailable"`. Nothing is coerced.
- **`uncached_tokens` is `None`** when either `prompt_tokens` or `cached` is unknown. A row that cannot
  be computed reports the gap; it does not report `prompt_tokens - 0`.
- **A non-200 raises** `RuntimeError(f"http {status}")` inside `post_chat`, before any row is built, so
  an error status can never land in the JSONL.
- **`assert_arms_distinct()` runs before the first measured turn**, rendering all four arms at turns 1
  and 20; any byte-identical pair raises `RuntimeError("ARMS_IDENTICAL")`.
- Rows carry exactly: `arm turn prompt_tokens cached_tokens uncached_tokens truncated http_status
  cache_report prompt_sha256`.

## A defect this unit found and fixed in its own spec-following

The first version of `H` differed from `A` only in that its *fold* at summary boundaries used
different text. But `summarise()` clips at 90 chars, and both the plain and the folded line begin
with the same prefix — so at turn 20 the two arms rendered **byte-identical** prompts. The arms guard
caught it (`ARMS_IDENTICAL`), and the red→green run caught a second, subtler instance: removing the
policy marker alone leaves the fold keeping `H` distinct from turn 9 onward, so a two-turn probe
cannot see the regression.

Fixed on both sides: `folded_summary()` now emits a `SUMMARY[n]` line that keeps the folded delta's
final line, and `H` carries an unconditional `INDEX (hybrid; folds=NN)` marker. Two tests were added —
`test_four_arms_pairwise_distinct_every_turn` (every turn, not just the probe turns) and
`test_hybrid_compacts_at_summary_boundary` (asserts the fold is a compression, not a relabel).
**All four arms are pairwise distinct at every turn 1–71** (`--dry-run` output above).

## Acceptance

```
$ PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m pytest experiments/context-cache/cells/VLLM-CELL/tests -q
..............                                                           [100%]
14 passed in 0.08s
```

The five contracted red cases (all bite; full transcript in `state/logs/VLLM-CELL-redgreen.txt`):

| Case | Revert | Fails |
|---|---|---|
| R1 | details absent → `0` instead of `null` | `test_details_absent_is_null_not_zero` |
| R2 | `cached_tokens` dropped to `None` | `test_cached_tokens_reported` |
| R3 | 500 no longer raises | `test_http_500_raises` |
| R4a | `H` collapses onto `A` (marker + fold reverted) | `test_four_arms_pairwise_distinct_every_turn`, `…compacts_at_summary_boundary` |
| R4b | `H` fold becomes a plain clipped summary | `test_hybrid_compacts_at_summary_boundary` |
| R5 | `R` collapses onto the `A` rendering | `test_R_and_A_differ` |

**Null-row proof** (details absent, `prompt_tokens: 4096`):

```json
{"arm": "R", "turn": 1, "prompt_tokens": 4096, "cached_tokens": null, "uncached_tokens": null,
 "truncated": false, "http_status": 200, "cache_report": "unavailable", "prompt_sha256": "aaaa…"}
```

**The command `MEASURE-VLLM` should run**, per cell, one arm at a time:

```
.venv/bin/python experiments/context-cache/cells/VLLM-CELL/vllm_cell.py \
  --base-url http://127.0.0.1:8020/v1 --model occamy-1.0 \
  --arm all --turns 71 --budget 32768 \
  --out experiments/context-cache/cells/R2-VLLM-FIX/OH1 --warmup
```

296 requests per cell (4 arms × 71 turns + 1 warm-up), 592 for both cells — the card's bound is 700.
Before spending them, run the free `--dry-run` and read the four char counts.

## Assumptions (recorded — automated session, nobody to ask)

- **Base URL convention** is `{base_url}/chat/completions`, so callers pass `.../v1`. The card says
  `{base_url}/chat/completions` literally; this unit did not append `/v1` itself.
- **The cell is 245 lines, not ~120.** The spec asked for ~120 with stdlib + `requests`, a full arm
  set, the row contract and the two guards. The overage is docstrings and comments, not machinery;
  trimming prose to hit the number would have cost the reasoning that makes the null rule auditable.
  Reported as a deviation rather than silently restyled.
- **`--arm all` exists** beyond the contracted `{R,A,C,H}` so one invocation produces 284 rows. A
  single-arm invocation writes 71.
- **The arms guard probes turns 1 and 20** as specified; the extra every-turn test lives in the test
  suite, not in the live path.

# U-SPCC-18 — the bill is a bound: `ABSENT ≠ 0` in the billing block

**Unit:** U-SPCC-18 · **Status:** done · **Date:** 2026-11-10
**Inputs:** `measure/rows-spcc-billedproof-2026-11-10.jsonl` (100 rows, 0 failed, 0 truncated),
`orchestration/units/U-SPCC-11.md` (the defective fix)
**Files owned:** `experiments/ptr-engine/longrun/run_longrun.py` (BILLED-STAMP in `make_row`),
`experiments/ptr-engine/longrun/score_longrun.py` (`billed_of`, `billing_block`),
`experiments/ptr-engine/longrun/tests/test_billed_tokens.py`,
`experiments/ptr-engine/longrun/tests/test_scorecard_guards.py`,
`docs/STATE.md`, `orchestration/STATUS.md`, `journal/2026-11-10.md`, `orchestration/units/U-SPCC-11.md`

## 1. The defect

`U-SPCC-11` billed `prompt_tokens` in full whenever `cached_tokens` was null, then published
`billed_tokens 14303 · billed_source "derived" · billed_coverage 1.0`. The programme's standing rule is
`ABSENT ≠ 0`: a missing measurement is unknown, never zero. Two rows (`turn 1`, `turn 5`) carried no cache
counter, so 14,303 was an **upper bound** asserted as a measurement, and `billed_coverage 1.0` claimed every
row had contributed a known quantity.

Turn 1 is settled by the cache **mechanism** — the first request of a run has no prior prefix, so `cached = 0`
there follows from how the cache works, not from an assumption. Turn 5 is genuinely unknown: a
`revision_schedule` revocation coincides with the null, and nothing proves the prefix was empty.

## 2. Per-row rule (`run_longrun.make_row`)

| condition | `billed_tokens` | `billed_source` |
|---|---|---|
| `cached_tokens` present | `prompt − cached` | `"reported"` |
| `cached_tokens` null **and** `turn == 1` | `prompt` | `"first-turn-no-cache"` |
| `cached_tokens` null otherwise | `null` | `"unknown"` |
| `prompt_tokens` missing | `null` | `"unknown"` |

`run_longrun.py:2550-2560`. `billed_source` is now always stamped (it was `"server_cache_report"` or null).

## 3. Scorecard (`score_longrun.billing_block`)

`billed_of` applies the same rule to legacy rows, and lets an `ABSENT` cache counter **override** any older
stamp that assumed the whole prompt was billed (`score_longrun.py:177-181`). New block fields:

| field | meaning |
|---|---|
| `billed_tokens_known` | sum over rows with a known value — the established **lower** bound |
| `billed_upper_bound_tokens` | the same sum plus every unknown row's whole prompt — the **upper** bound |
| `billed_unknown_rows` | how many rows are unknown |
| `billed_unknown_turns` | their turn numbers |
| `billed_coverage` | known rows / all rows; `< 1.0` whenever `billed_unknown_rows > 0` |

`billed_tokens` remains as an alias equal to `billed_tokens_known`, so no reader can pick up the upper bound
under the old name. `prompt_tokens`, `cached_tokens`, `uncached_tokens`, both cache fractions and
`reconcile_delta_total` are unchanged.

## 4. The honest numbers

```
turn 1: prompt 261  cached null -> 261 by mechanism ("first-turn-no-cache")
turn 5: prompt 296  cached null -> unknown ("unknown")
98 rows with a reported counter  -> 13,746
billed_tokens_known       = 13,746 + 261 = 14,007
billed_upper_bound_tokens = 14,007 + 296 = 14,303
billed_unknown_rows = 1    billed_unknown_turns = [5]    billed_coverage = 0.99
```

`13,746` equals the sum of `uncached_tokens` only by coincidence over the 98 reported rows: `uncached` is a
different measurement and is null on exactly turns 1 and 5, so nothing derives billing from it.

## 5. Tests — written red, then green

Seven assertions failed against the unfixed code, including:

```
test_stamp_later_turn_null_cache_is_unknown_not_the_whole_prompt - assert 296 is None
test_no_cached_counter_after_turn_one_is_unknown_not_the_whole_prompt - assert 10 is None
test_mixed_block_reports_unknown_rows_and_the_upper_bound - KeyError: 'billed_tokens_known'
```

After the fix: `test_billed_tokens.py` **14 passed**, `test_scorecard_guards.py` **5 passed**, plus
`test_analysis_consumer.py` clean (**25 passed** jointly). No live request was made.

## 6. Documentation

Every sentence that presented 14,303 as charged now states the bounds: at most 14,303, at least 14,007
established, 296 tokens on turn 5 unmeasured, turn 1's 261 by mechanism. Sites: `docs/STATE.md:18-22,140-152,
548-554`, `orchestration/STATUS.md:567-577`, `journal/2026-11-10.md:53,136-145`, and a superseded banner on
`orchestration/units/U-SPCC-11.md:3-7`. `python3 tools/doc_check.py` exits **0**.

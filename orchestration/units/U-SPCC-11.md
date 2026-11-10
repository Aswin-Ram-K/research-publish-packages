# U-SPCC-11 — make `billed_tokens` mean the tokens the server charged for

> **SUPERSEDED IN PART by `U-SPCC-18`.** This unit billed the WHOLE prompt whenever `cached_tokens` was
> null, which is `ABSENT = 0` again. The corrected reading is a bound: `billed_tokens_known` **14,007**,
> `billed_upper_bound_tokens` **14,303**, `billed_unknown_rows` **1** (turn 5, 296 tokens), `billed_coverage`
> **0.99**. Every `14,303` below is the **upper bound**, not the charged quantity, and `billed_source` is no
> longer `"server_cache_report"` but `"reported"` / `"first-turn-no-cache"` / `"unknown"`.

**Unit:** U-SPCC-11 · **Status:** done · **Date:** 2026-11-10
**Inputs:** `measure/rows-spcc-billedproof-2026-11-10.jsonl` (100 rows, 0 failed, 0 truncated),
`measure/score-spcc-billedproof-2026-11-10.json` (the vacuous block), `orchestration/handoffs/U-SPCC-9A.json`
**Files owned:** `experiments/ptr-engine/longrun/run_longrun.py` (per-row extras region),
`experiments/ptr-engine/longrun/score_longrun.py`, `experiments/ptr-engine/longrun/tests/test_billed_tokens.py`,
`experiments/ptr-engine/longrun/tests/test_scorecard_guards.py`

## 1. The defect

`score_longrun.py:145` summed `r['billed_tokens']`, a field `run_longrun.make_row` never wrote, so the
scorecard reported `billed_tokens: 0` over 100 rows that each carried a real cache report. An unwritten field
and a genuinely free request were indistinguishable — the same `ABSENT = 0` class of error the programme
exists to avoid.

Recomputed from the rows (no model call): `prompt 174047 · cached 159744 · uncached 13746 · billed 14303`.

## 2. The definition, stated in the code

`billed_tokens` = prompt tokens the **server charged for** — every prompt token it did not report as served
from its prefix cache.

| case | billed |
|---|---|
| `cached_tokens` reported | `prompt_tokens - cached_tokens` |
| `cached_tokens` null (SGLang omits it when it is 0) | `prompt_tokens` — nothing was cached, all of it billed |
| `prompt_tokens` missing (failed turn) | `null` — no prompt, no bill |

`billed_tokens` is deliberately **not** `uncached_tokens`: the server's own prefill accounting leaves
`prompt - cached - uncached = 557` tokens (0.32%) unexplained on this run. That residual is recorded, never
smoothed away, and `uncached_tokens` is never rewritten to make the identity balance.

### Source stamp — `run_longrun.py`

`make_row`, per-row extras region, immediately after the prompt/cache read (`run_longrun.py:2539-2555`):

- `billed_tokens` (`run_longrun.py:2622`)
- `billed_source` = `"server_cache_report"` or `null` (`run_longrun.py:2623`)
- `reconcile_delta_tokens` = `prompt - cached - uncached` or `null` when the cache counter is null
  (`run_longrun.py:2624`)

No assertion on the residual: a 1-token tolerance fires on every real SGLang run (557 tokens over 100 turns,
5.6/turn), so it would be disabled within a week. The residual is stamped per row instead.

### Consumer — `score_longrun.py`

`billed_of()` (`score_longrun.py:144-176`) returns `(billed, source)` per row:

1. `"field"` — the row's own `billed_tokens` (rows written after this fix);
2. `"derived"` — field absent (rows written before it): `prompt - cached`, or `prompt` when `cached` is null;
3. no contribution — `prompt_tokens` missing. Never counted as 0, never imputed.

`billing_block()` (`score_longrun.py:179-276`) sums only contributing rows; **a sum over zero contributors is
`null`**, and `attribution` is `None` (no rows) / `"unavailable"` / `"partial"` / `"available"`, with
`coverage` (rows with a server-reported `cached_tokens`) and `billed_coverage` (rows contributing to the sum)
reported separately.

The ambiguous `cached_fraction` is gone — it meant `cached/(cached+uncached)` in
`score-spcc-billedproof-2026-11-10.json` (0.920768) and `cached/prompt` to the live unit (0.917821). Both are now
emitted with their denominator in the name:

- `cached_fraction_of_prompt` = `cached / prompt` (whole prompt total)
- `cached_fraction_of_accounted` = `cached / (cached + uncached)`

Residual reporting: `reconcile_delta_total`, `reconcile_tolerance_tokens` (1% of prompt = 1740 here, chosen
because 1 token is untenable: 557/174047 = 0.32% is ordinary reported-vs-counted drift, so 1% keeps a
genuinely broken accounting visible without failing healthy runs), `reconcile_within_tolerance`.

## 3. Re-score of the existing run — no model call

```
.venv/bin/python experiments/ptr-engine/longrun/score_longrun.py \
  experiments/ptr-engine/longrun/tasks-v7/TX-03.v1.json \
  experiments/ptr-engine/measure/rows-spcc-billedproof-2026-11-10.jsonl
```

```json
{
  "prompt_tokens": 174047,
  "cached_tokens": 159744,
  "uncached_tokens": 13746,
  "billed_tokens": 14303,
  "billed_source": "derived",
  "cached_fraction_of_prompt": 0.917821048337518,
  "cached_fraction_of_accounted": 0.920767767594674,
  "coverage": 0.98,
  "billed_coverage": 1.0,
  "attribution": "available",
  "reconcile_delta_total": 557,
  "reconcile_tolerance_tokens": 1740,
  "reconcile_within_tolerance": true
}
```

`billed 14303 = prompt 174047 - cached 159744`; `13746` (uncached) is 557 short of it, which is why the two
quantities are kept apart. `measure/score-spcc-billedproof-2026-11-10.json` still holds the old vacuous block —
it was not rewritten (out of this unit's file scope); the command above regenerates it with `--out <path>`.

## 4. Tests

`.venv/bin/python -m pytest experiments/ptr-engine/longrun/tests/test_billed_tokens.py experiments/ptr-engine/longrun/tests/test_scorecard_guards.py experiments/ptr-engine/longrun/tests/test_contract_presence.py -q`

```
21 passed in 0.10s
```

`test_billed_tokens.py` covers: field present (sums the field, `billed_source: "field"`); field wins over
derivation; derivable without the field (`billed_source: "derived"`, including the fully-billed null-cached
row); derivation is `prompt - cached`, not `uncached`; absent → `null` not `0` (all three null shapes: no
prompt, empty record list, no cache report); both fractions against their own denominators; the three source
stamps through `make_row` (prompt-cached, whole-prompt on omitted counter, `null` on a failed turn); and the
real 100-row re-score pinned to 174047 / 159744 / 14303 / 0.917821 / 0.920768 / 557. `test_scorecard_guards.py`
was updated to the renamed fractions and the corrected billing semantics.

## 5. Follow-ups (outside this unit's files)

- `docs/STATE.md:119` and `docs/STATE.md:133` still describe the block with `cached_fraction`; they need
  `cached_fraction_of_prompt` / `cached_fraction_of_accounted` and the substantive `billed 14303`.
- `measure/score-spcc-billedproof-2026-11-10.json` needs the one-command regeneration above.

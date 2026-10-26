# QUALITY-INSTRUMENT-V2 — corrected billing instrument, built offline

**Status:** done (module + tests + guard reachable offline; no live request made)
**Unit shape:** unit, per `AGENTS.md`. Bound: 30 tool calls; used 10.
**Write paths:** `experiments/ptr-engine/quality/runner_v2.py`,
`experiments/ptr-engine/quality/tests/`, this card, and
`orchestration/handoffs/QUALITY-INSTRUMENT-V2.json`.

## Why

The quality arm's cost column never recorded what the server billed: `L` was the whole
prefix, `cached_tokens` was read then dropped, and refusals were counted by prose. A prior
in-place repair died on its own alignment guard (`rerun-corrected.log:16`), so this unit
copies the instrument instead of editing it.

## Where the defects live (current line numbers, `runner.py`)

| # | line(s) | defect |
|---|---------|--------|
| 1 | `runner.py:495` | `L = prompt_tokens + FRAMING` — the prefix, not the append `P2 − P1` (`:494` computes the previous count and never uses it for `L`) |
| 2 | `runner.py:591-599`, `:688` | `usage.prompt_tokens_details.cached_tokens` is read at `:594` but absent from all 48 shipped request rows; `billed_tokens_measured` is `sum(prompt_tokens)` |
| 3 | `runner.py:575-579`, `:656`, `:677` | `refused_total` sums only `outcome == "refused"`; model refusals are `refused_by_model` and vanish; no count per request row |
| 4 | `runner.py:762`, `:782-818` | `_assert_aligned` can only run against a server; it is the guard that killed the in-place attempt |

## What v2 changes (each marked `# V2 (defect N):`)

1. `billing_row()` — `L = P2 − P1` (`L_source: "delta"`); prime only falls back to
   `n_payload + 12` (`L_source: "framing"`). Both persisted on prediction/request/turns rows.
2. `_server_accounting()` — `cached_tokens` persisted raw; an absent/null details object
   yields `cached_tokens: null` + `cached_reported: false` (+ `server_uncached: null`),
   a reported `0` stays `0`/`true`.
3. Per-rep `Counter` of refusal codes (model-initiated included) → `refused_total`,
   `refused_by_code`, `refusal_codes` per rep; per turn too.
4. `assert_billing_alignment()` — `billed == prompt_tokens − cached_tokens + L_source_consistent`,
   plus `L` must equal what its own `L_source` implies; raises with row index and both counts,
   and runs before any aggregate is written.

`billed_tokens_measured` is now a sum of readings (per reported turn
`prompt_tokens − cached_tokens`; a silent turn contributes its whole prompt and is counted).
`billed_tokens` remains the law model, labelled `billed_tokens_source: "law_model"`.

## Evidence

- `.venv/bin/python -m pytest experiments/ptr-engine/quality/tests/test_billing_alignment.py -q` → `3 passed in 0.02s`
- RED: `row 0 (turn 2): billed=10262 but prompt_tokens - cached_tokens + L_source_consistent = 10245 - 0 + 0 = 10245 [L=10257, ...]`
- GREEN: `{"L": 245, "L_source": "delta", "billed": 245, "cached_tokens": 10000, ...}`
- NULL: `{"cached_tokens": null, "cached_reported": false}`
- `runner.py`, `rows.jsonl`, `rows-corrected.jsonl`, `rerun_corrected.py`, `RESULTS.md`,
  `PREREG.json`, `LAW.md`, `RECORD.md` untouched (mtimes precede this session).

## Not mine

Promotion is a separate decision. If promoted: re-register `PREREG.json:30`'s law string
(it still says `L = prompt_tokens + 12`) and run one live arm-A rep to see the reading triple.

# CACHED-AUDIT2 — calibration, normalisation, test, handoff

**Status:** done · **Bound:** 12 tool calls · **Live requests:** 0

## Purpose
Finish the offline cached-dedupe unit killed at 02:17: prove the detector both ways,
normalise the audit entries, pin the behaviour in a test, ship a real handoff. The
detector (`tools/audit/cached_dedupe.py`) and the corpus audit already existed.

## Write paths
`tools/audit/cached_dedupe.py`, `tests/test_cached_dedupe.py`,
`state/logs/cached-dedupe-audit.json`, `orchestration/handoffs/CACHED-AUDIT2.json`,
`orchestration/units/CACHED-AUDIT2.md`. Read-only elsewhere (`papers/**`, `cells/**`).

## Results
| control | expectation | observed |
|---|---|---|
| `PROMPT-O1/rows.pre-correction.jsonl` | fire | arm R 40/71 fires, rate 0.5634, turns 5,6,8,... gaps 736/755/729 |
| `PROMPT-O1/rows.jsonl` (repaired) | silent | 0 fires, 5 arms |
| `R2-P1-O1/rows.jsonl` (independent) | silent | 0 fires, 5 arms |

Corpus: 27 cells, 91 (cell,arm) entries, clean 12 / suspect 13 / corrupt 2.
Corrupt: `PROMPT-O2-EXTRA` arm R and `R2-P1-O2` arm R, both 40 fires on 71 rows, rate 0.580.
Published claims resting on a corrupt cell: **0 of 64** — claims cite cells by abbrev
(`WIN-VLLM-rows`), and neither corrupt cell has a source abbrev in `CLAIMS.md`. 20 claims do
rest on a *suspect* cell (C06, C17, C18, C19, C20, C21, C22, C23, C24, C25, C26, C44, C45, C46, C47, C48, C49, C50, C51, C53), which is a warning, not a corrupt verdict.

## Test
`tests/test_cached_dedupe.py`: 7 passed. Widening `BAND_LO_QUANTA` 0.9 → 5.0 makes it fail
(2 failed, `assert 0 == 40`), so the verdict is load-bearing rather than vacuous.

## Next
Repair `PROMPT-O2-EXTRA` / `R2-P1-O2` rows. No paper claim is currently invalid.

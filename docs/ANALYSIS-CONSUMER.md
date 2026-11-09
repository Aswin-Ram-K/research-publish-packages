# ANALYSIS-CONSUMER — `usable_for` consumption and the truncated-turn rule

Unit `ANALYSIS-CONSUMER-FIX`. Two mechanisms the analyser lacked. Instrument:
`experiments/ptr-engine/longrun/analyze_stats.py` (there is no `longrun/analyze.py`;
`measure/ANALYSIS-PATH.json` already records that fact). Offline: zero requests.

## 1. `usable_for` is now carried by the cell manifest and CONSUMED

**Carrier.** The cell manifest, because it is the only document that already joins a
cell to its rows without guessing by filename: every grid manifest carries
`rows_path` (`longrun/manifests/longrun-2026-10-26T182535Z-pointer-stable-r1.json`
→ `experiments/ptr-engine/measure/rows-cell-pointer-stable-20261026T182535Z.jsonl`).
`cell.py` is frozen by this card, so the write-time entry point lives beside the
consumer and cell.py's next revision calls it once per finished cell:

```python
def write_cell_manifest_usable_for(rows_path, usable_for, reason=None,
                                   manifest_path=None, dry_run=False):
    """`cell.py` is frozen by ANALYSIS-CONSUMER-FIX, so the writer lives beside the
    consumer it feeds: cell.py's next revision calls this once per finished cell
    (`rows_path` -> that cell's manifest)..."""
```

It stamps `usable_for` (list) and `usable_for_reason` into the manifest with an
atomic `os.replace`. CLI: `--stamp-rows PATH [--usable-for a,b|--usable-for ""]
[--usable-for-reason "..."] [--manifest-out M] [--dry-run]`.

**Consumption**, first hit wins (`usable_for_for_path`):
1. an explicit `--manifest PATH` (repeatable);
2. `longrun/manifests/*.json` whose `rows_path` resolves to the rows file;
3. `measure/GRID-CELL-SANITY.json` `cells[].usable_for` — the census, i.e. the
   carrier for cells written before this card.

`select_usable_cells` then drops every cell whose stamp is an empty list **before
any statistic exists**, and the exclusion is printed by name AND written into the
`--json` document under `cell_usability` (`{"excluded": true, "usable_for": [],
"reason": ..., "source": "sanity"|"manifest"}`). A cell with no stamp at all is
kept and printed `usable_for unstamped ... (included: no usability stamp on disk
-- not a certification)`, so the absence of a stamp is never mistaken for a pass.

**Loophole closed.** If every input cell is stamped empty:

```
  usable_for EXCLUDED every cell: no usable cells (…)
no usable cells: every input cell is stamped usable_for: [] -- refusing rather
than printing an empty table as success (…)
```

exit code **1**. An empty table can no longer be printed as success.

**Era A outcome** (`rows-cell-pointer-stable-20261026T182535Z.jsonl`, 27 rows,
`cell_state=in_progress`, census `usable_for: []`):

```
  usable_for EXCLUDED  rows-cell-pointer-stable-20261026T182535Z.jsonl
  27 row(s) NOT analysed  source=sanity  usable_for=[]  reason=(none recorded)
```

With the 4-arm file supplied alongside, `n_rows` = **192**, not 219: the abandoned
cell's 27 rows never enter the tranche.

## 2. Truncated turns: excluded from p50 AND p95, counted per arm

`split_truncated` is the single application point, called on the ONE selection the
TTFT definition produced, so p50 and p95 are handed the same population:

```python
        selected, sel_meta = selector(arm_rows)
        latency_selected, trunc_meta = split_truncated(selected)
        vals, nulls, unavailable = ttft_values(latency_selected)
```

A row is truncated when `stop_reason == "length"` or `truncated is True`
(`is_truncated`). Per arm the document carries `truncated_turns`:
`rule`, `rule_version` = `truncated-turns/1`, `excluded`, `total`, `fraction`,
`by_stop_reason`, `keys`. `ttft.selected` (definition) and
`ttft.selected_for_latency` are both kept, so the subtraction is checkable:
`used + excluded + dropped_null + dropped_unavailable == selected`.

Printed beside the surviving n:

```
  truncated_turns  excluded=2 of 27 selected turn(s)  fraction=7.4%  from the
  latency quantiles (p50 and p95)  surviving n=25  [truncated-turns/1]
```

`min_n_for(0.95) = 60` is untouched: at n=25 p95 still refuses
(`minimum n for p95 is 60`), and an arm that falls below 60 **because** of this
rule refuses exactly as before. The rule is latency-only — `selected` itself is
not changed, so McNemar pairs, accuracy and request/ledger accounting see every
row.

### Measured on the real tools-on artefacts

| cell | rows | turn rows selected | truncated | rows with ttft | n after |
|---|---|---|---|---|---|
| `rows-longrun-v4-tools-2026-10-26.jsonl` | 68 | 48 | 1 (2.1%) | 47 | **47** |
| `rows-longrun-v5-tools.jsonl` | 72 | 48 | 1 (2.1%) | 47 | **47** |
| `rows-longrun-v6-tools.jsonl` | 72 | 48 | 0 | 48 | **48** |
| era A `rows-cell-pointer-stable-20261026T182535Z.jsonl` | 27 | 27 | 2 (7.4%) | 25 | **25** |

The era A file holds one `stop_reason=length` turn and one `runaway_turn` turn
(`truncated: true` on two rows) — matching `measure/RUNAWAY-POLICY.json`'s 2-in-27.

> **Dated caveat (2026-10-26) — `LATENCY-FIGURE-HONESTY`, the era A row's `27 -> 25` counts:** `experiments/ptr-engine/measure/GRID-CELL-SANITY.json` stamps this cell `usable_for: []` (reason: *"cell in progress: 27/48 turns on disk — a statistic computed now would be from a truncated cell file"*); the 60-turn census that consumed that stamp is `orchestration/handoffs/TURN-CENSUS-60.json` (unit `TURN-CENSUS-60`): **0 of 15** rows files and **0 of 15** arm-by-file rows reach 60 usable turns, the largest is **48**, so `n=27` gives `27 x 0.05 = 1.35 < TAIL_MIN = 3` and no p95 can exist here.
>
> Rows file this figure was computed on: `experiments/ptr-engine/measure/rows-cell-pointer-stable-20261026T182535Z.jsonl`, sha256 `46afc892480ae1dbe4b20d13fd4dacb983653a9f0a04b6a42a6283b3c55ca3b1` (`wc -l` = 27).
>
> **What the number may still be used for:** nothing pooled and nothing comparative — it is one cell's legacy `kind='turn'` p50 (`definition_fallback: true`, see `docs/LATENCY-FALLBACK.md`), quoted only with its `n` and never beside another cell's value.

## 3. Tests (green) and the red→green evidence

`experiments/ptr-engine/longrun/tests/test_analysis_consumer.py` — 6 tests, on the
real artefacts:

1. `test_era_a_cell_is_excluded_by_name_not_averaged` — printed by name, in the
   `--json` document, and `n_rows == 192`.
2. `test_no_usable_cells_is_a_nonzero_refusal` — `SystemExit` carrying
   `no usable cells`.
3. `test_manifest_is_the_carrier_for_usable_for` — a stamped copy of the real
   manifest outranks the census in **both** directions.
4. `test_truncated_turns_excluded_and_counted_with_backcomputed_n` — 4 rows marked
   truncated → `excluded == 4`, `n_after = n_before - 4`, the n identity above
   holds, and `n_rows`/accuracy are unchanged.
5. `test_format_arm_states_excluded_count_beside_surviving_n`.
6. `test_split_truncated_is_the_single_rule`.

Red→green: before the patch the same file was **6 failed** (`AttributeError:
module 'analyze_stats' has no attribute 'split_truncated'`, and no `cell_usability`
/ `usable_for` output); after it, **6 passed**. One red→green per mechanism is
carried by test 1 (consumer) and test 4 (truncation).

Regression: `python3 -m pytest longrun/tests -q` → **583 passed, 30 failed**, and
**none** of the 30 failures mentions `analyze_stats`, `usable_for`, `split_truncated`
or `truncated_turns` (they are checkpoint/grade/handoff/projection/verbosity
artefact drift outside this card's write paths; the analyser's own suites
`test_analyze_stats.py`, `test_analyze_provenance.py`, `test_ttft_definition.py`,
`test_latency_*`, `test_exit_codes.py`, `test_h1_conditioning.py` all pass).

`tools/tokens_to_verified.py` identity: untouched,
sha256 `d4cca36ca6d9f20f2622655947fc0cfc77877c26dad149a5b7656276abc5ac4d`, as
`measure/ANALYSIS-PATH.json` records it.

## 4. Published documents that must be regenerated (`file:line`)

- `docs/LATENCY-REPORT.md:35` — G7 V4-TOOLS `pointer-stable`, published `n=68`/`51`
  (cell carries 1 truncated turn: n recomputed, and the withdrawn figure re-stated).
- `docs/LATENCY-REPORT.md:36` — G8 V5-TOOLS `pointer-stable`, `n=72`/`70`
  (1 truncated turn; `n=70` must be re-derived).
- `docs/LATENCY-REPORT.md:98` — G7 before→after row (`n=68 → 51`, p50/p95 values).
- `docs/LATENCY-REPORT.md:99` — G8 before→after row (`n=72 → 70`, p50/p95 values).
- `docs/LATENCY-REPORT.md:108` — quotes the withdrawn G7 p95 `n=68`.
- `docs/LATENCY-REPORT.md:125` — "two p95 values" summary over those cells.
- `docs/LATENCY-REPORT.md:37` and `docs/LATENCY-REPORT.md:100` — G9 V6-TOOLS
  `n=72`/`61`: **zero** truncated turns, so these change only if the usability
  stamp changes, not because of this rule.
- `docs/LATENCY-REPORT.md:141-145` — G1/G2 stage tables (`n=48`, `n=3`): the
  truncated-turn count must be printed on each arm row going forward.
- `docs/OPERATOR-BRIEF.md` — no line quotes the era A cell, `n=27`, `usable_for`
  or the 131.35/166.38 interval (`grep` returns nothing), so it needs no
  regeneration for this card; it does inherit whatever the latency report
  republishes.

Neither document was edited by this card.

## 5. The one-sentence answer

**After this card, no: a cell that never fired its treatment (`usable_for: []`)
cannot reach a published number — it is dropped before any statistic exists,
printed by name, recorded in the analysis document under `cell_usability`, and if
that leaves nothing the analyser exits 1 with `no usable cells` instead of printing
an empty table as success.**

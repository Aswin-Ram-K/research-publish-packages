# LEDGER-AFTER-CANARY — the brake was reading a stale number

**Question this answers:** what is the true request spend, why did `measure/REQUEST-LEDGER.json` still say
1,128, and does the cap gate (G1) read that file or re-count the rows?

## What changed

| | before (snapshot built 2026-10-26T18:56:31Z, sha `6da0c1f1…`) | after (this rebuild) |
|---|---|---|
| spent (`requests_raw`) | 1,128 | **1176** |
| remaining | 3,192 | **3144** |
| cap / reserve | 4,320 / 0 | 4,320 / 0 |
| files counted | 15 | **19** |
| rows counted | 1,128 | **1176** |

The rebuild is produced by the ledger's **own** builder — `request_ledger.py:build_report(paths, cap=4320, reserve=0,
would_spend=0)` — over `measure/rows-*.jsonl`. No number was hand-edited. Two consecutive runs are byte-identical
(sha256 `eadc56f6…`), so the figure is a measurement, not a transcription. The predecessor is preserved in the new
file under `supersedes` (old sha, old spent/remaining, timestamp): **supersede, never mutate**.

The de-duplicated figure (1146, excess 30) is published as a
**diagnostic with `deducted: false`**. `content_sha256` hashes the assistant's *content*, not request identity
(`DEDUPE-ROOT-CAUSE`; `V-DUPLICATE-RULE` graded `fail`), so subtracting it would understate spend.

## The delta is 48, not 36 — and the fourth file is the finding

The canary's own journal went `spent_rows_before=1128 → spent_rows_after=1164` and named three 12-row files
= **36**. Those three files are real and verified (12 rows, 12 counted requests each). They were not the last word:
a **fourth** live cell appeared after the canary wrote its record at 20:40:00Z:

| file | rows | requests | first row (UTC) | whose |
|---|---|---|---|---|
| `rows-cell-pointer-stable-20261026T202040Z.jsonl` | 12 | 12 | 20:20:58.079 | canary arm pointer-stable |
| `rows-cell-transcript-grow-20261026T202444Z.jsonl` | 12 | 12 | 20:26:41.642 | canary arm transcript-grow |
| `rows-cell-transcript-compact-20261026T203733Z.jsonl` | 12 | 12 | 20:37:34.021 | canary arm transcript-compact |
| `rows-cell-pointer-stable-20261026T204258Z.jsonl` | 12 | 12 | **20:43:11.557** | **NOT the canary** — manifest `longrun-2026-10-26T204258Z-pointer-stable-r1`, created 20:42:58.636Z, `cap_gate.spent_at_start=1164 → spent_after=1176` |

So the canary's 36 was **true when measured and stale by the time it was read**: it under-reports by 12. The rebuild
attributes exactly **48** new requests across those four files, and — the required check — **zero** pre-existing files
changed sha256 and **zero** disappeared (all 15 baselined files verified against
`LEDGER-GRID-BASELINE-2.json`'s `rows_inventory`). Had any of the 15 moved, that would be a rewrite finding; none did.

## Why the canary could not fix it

`measure/REQUEST-LEDGER.json` was on `LIVE-CANARY-4ARM-3`'s **forbidden** list (it is another card's write path), so
the canary did the honest thing: it refused to rewrite the file and **reported the delta instead of a silent zero**,
recording `delta_in_file: 0` with the measured live delta beside it. A unit that cannot write the fix must not
pretend the fix happened — and a reader that took the canary's 36 as the current spend would still be 12 short.

## What the gate actually reads — `cell.py:1255`

G1 does **not** trust `budget.spent` in the JSON. It re-counts:

```
experiments/ptr-engine/longrun/cell.py:1255
    report = ledger.build_report(_ledger_row_paths(doc), facts["cap"],
                                 facts["reserve"], would_spend)
```

`_ledger_row_paths` (`cell.py:1200-1213`) turns the artefact's **`files` list** into paths, and `spent` is read from
that fresh report (`cell.py:1260-1261`, `b = report["budget"]`). Two precise consequences:

1. **The gate was never mispriced by the number 1,128** — it recomputes spend from rows, so a live cell was counted
   from disk, not from the stale field.
2. **The gate was stale anyway, in a subtler way**: it only counts row files **named in the artefact**. The old list
   had 15 entries, so the 48 new requests were invisible to G1 too. This rebuild regenerates the list from disk
   (19 entries), which is what closes the hole for the gate as well as for card readers.

Readers that take `budget.spent` literally (e.g. `tools/run_grid_report.py:90`, handoff prose quoting "3,192 remaining")
were the genuinely mispriced consumers, and they were overstating headroom by **48**.

## Reproduce

```
/usr/bin/python3 experiments/ptr-engine/tools/request_ledger.py --glob 'measure/rows-*.jsonl' \
    --cap 4320 --reserve 0 --would-spend 0
/usr/bin/python3 experiments/ptr-engine/tools/ledger_delta.py --baseline   # v2: delta must read 48
```

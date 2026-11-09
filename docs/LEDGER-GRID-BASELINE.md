# LEDGER-GRID-BASELINE — the pre-grid spend reading, frozen

**Status:** frozen reading. **Label: `pre_grid`** — taken with no `rows-runA-*` on disk, i.e. before `RUN-A*` billed its first cell.
**Unit:** `LEDGER-GRID-BASELINE` · **Artefact of record:** `experiments/ptr-engine/measure/LEDGER-GRID-BASELINE.json`
**Capture instant:** `2026-10-26T18:24:48Z` UTC · `2026-10-26T13:24:48-0500` local (America/Chicago)
**Offline:** zero inference requests, no network. This unit freezes a reading; it does not re-derive the ledger.

## 1. The frozen values

| field | value |
|---|---|
| `requests_raw` | **1101** |
| `requests` (published) | 1101 |
| `remaining_raw` | **3219** |
| `remaining` (published) | 3219 |
| `budget.cap` | 4320 |
| `budget.reserve` | 0 |
| `budget.spent` | **1101** |
| `duplicate_excess` | 30 |
| `deduction_rule_sound` | `false` |
| `diagnostic.deducted` | `false` |
| `requests_deduplicated` (diagnostic only) | 1071 |
| `remaining_deduplicated` (diagnostic only) | 3249 |
| `total.files` / `total.rows` | 14 / 1101 |

**Baseline source:** `experiments/ptr-engine/measure/REQUEST-LEDGER.json`
· sha256 `2f60b831a8439a9ba4ba5fafb8f6ca1ba4fb40cdaf1ccff4f29182c0d6e4c1e5`
· 68882 bytes · mtime `2026-10-26T11:14:36-0500`
· **this baseline file** sha256 `6b6dff4473e5e1b9a20ab73b58dfb4a884d50dff019751058ebbd0188b307470` (see §6: it must not move).

### The 1,071 is recorded, labelled diagnostic, and never deducted

`content_sha256` hashes the assistant's **content**, not request identity (869/869 rows), so tuple-identity de-duplication is not a request-identity test. Deducting the 1,071 would **understate** spend by **30**. Every figure above that enters arithmetic is the **raw** one; `requests_deduplicated` / `remaining_deduplicated` are carried for audit only, with `deducted: false`.

## 2. Per-file inventory (the rows the ledger counted)

| rows file | rows | requests | sha256 (16) | mtime (UTC) | ledger sha & rows match disk |
|---|---|---|---|---|---|
| `rows-baseline-2026-10-26.jsonl` | 105 | 105 | `638c84942e3bcdba` | 2026-10-26T05:52:43Z | yes |
| `rows-cell-pointer-stable-20261026T145758Z.jsonl` | 6 | 6 | `5ac9dd992f5d8715` | 2026-10-26T15:17:04Z | yes |
| `rows-equalinfo-2026-10-26.jsonl` | 100 | 100 | `c01c7b4a477fe24b` | 2026-10-26T06:07:35Z | yes |
| `rows-live-2026-10-26.jsonl` | 27 | 27 | `3d02b4d473304f00` | 2026-10-26T05:30:17Z | yes |
| `rows-longrun-2026-10-26-fix.jsonl` | 29 | 29 | `9d4ad90ce34cb781` | 2026-10-26T09:39:20Z | yes |
| `rows-longrun-2026-10-26-policy.jsonl` | 40 | 40 | `9b1097234bf8d246` | 2026-10-26T11:52:48Z | yes |
| `rows-longrun-2026-10-26.jsonl` | 192 | 192 | `bc61d38192d4e431` | 2026-10-26T07:39:07Z | yes |
| `rows-longrun-c-2026-10-26.jsonl` | 192 | 192 | `aa7d6cfe9adedf9e` | 2026-10-26T10:40:59Z | yes |
| `rows-longrun-v3-2026-10-26.jsonl` | 96 | 96 | `80d85fe0e977af16` | 2026-10-26T11:00:32Z | yes |
| `rows-longrun-v4-2026-10-26.jsonl` | 96 | 96 | `999f298dac8b8356` | 2026-10-26T11:40:56Z | yes |
| `rows-longrun-v4-tools-2026-10-26.jsonl` | 68 | 68 | `f11391aa2989949f` | 2026-10-26T12:05:28Z | yes |
| `rows-longrun-v5-tools.jsonl` | 72 | 72 | `586b66f27939bd05` | 2026-10-26T12:24:37Z | yes |
| `rows-longrun-v6-tools.jsonl` | 72 | 72 | `1e78d75f259afbe0` | 2026-10-26T13:23:48Z | yes |
| `rows-pilot-thinking-2026-10-26.jsonl` | 6 | 6 | `6b81a6281ce0b266` | 2026-10-26T09:39:48Z | yes |

All 14 rows files on disk were re-counted and re-hashed: **rows summed 1101 = ledger total 1101**, disagreements: **none**. Full 64-hex digests, byte sizes and both UTC/local mtimes are in the JSON artefact. The recomputation agreed, so no finding is raised against the artefact.

## 3. Has the grid already spent anything? — `pre_grid`

Evidence, all read-only:

1. **`experiments/ptr-engine/measure/rows-runA-*` does not exist** at capture (`rows_runA_present: false`). `RUN-A*` (`ad214412-c39c-4a47-afb1-2be328e03b1e`, exec `c456e8d4`) had written no rows file.
2. **Every rows file predates the ledger build:** latest rows mtime `2026-10-26T13:23:48Z` < ledger mtime `2026-10-26T16:14:36Z`. Nothing was written after `REQUEST-LEDGER.json` was built.
3. **The ledger is internally consistent:** `budget.spent` 1101 = `requests_raw` 1101 = corpus rows 1101.
4. **No contradicting citation:** `orchestration/handoffs/RECLAIM-GREEN-ROWS.json` and `experiments/ptr-engine/measure/VERDICT-RECLAIM.json` cite no spend figure; `experiments/ptr-engine/measure/GRID-BUDGET-RECHECK.json` cites 1101 four times, consistent.
5. **Live confirmation:** the delta tool, run at freeze time, reports `delta 0` against this baseline — spend had not moved between the ledger build and the capture.

Conclusion: this is a genuine **`pre_grid`** baseline, not `post_first_cell`. If a later reader finds `rows-runA-*` present and `budget.spent` above 1101 while this file still says `pre_grid`, the file has been superseded or mis-stamped — re-freeze rather than reinterpret.

## 4. How to compute the delta

```text
delta = REQUEST-LEDGER.json : budget.spent (now)  -  LEDGER-GRID-BASELINE.json : budget.spent (frozen, 1101)
cross-check (a): delta              must equal  requests_raw_now - requests_raw_before
cross-check (b): remaining_raw_now  must equal  remaining_raw_before - delta
```

Arithmetic is anchored on the **raw** pair — `requests_raw` 1101, `remaining_raw` 3219 — never on the de-duplicated pair.

One command, exit **0** when the arithmetic closes, **1** when it does not:

```bash
.venv/bin/python experiments/ptr-engine/tools/ledger_delta.py \
  --baseline experiments/ptr-engine/measure/LEDGER-GRID-BASELINE.json
```

```text
spent_before            1101
spent_now               1101        (at freeze time)
delta                   0
remaining_now           3219
remaining_before_minus_delta  3219
deficit                 none
verdict                 OK (arithmetic closes: delta is a real measurement, not a re-read)
```

## 5. Pre-registered expectation for tranche 1 (a prediction, not a result)

- **Turns:** 480 (10 cells) · **historical requests/turn:** 1.374532 (= 1,101 / 801)
- **Arithmetic:** 480 × 1.374532 = 659.775 → **≈660 marginal requests**
- **If the grid completes tranche 1, a reader should see:** `requests` **1101 → ≈1761**, `remaining_raw` **3219 → ≈2559**, `delta ≈660`, closing arithmetic, and **no `deficit:` line**.
- **Competing arithmetic already on record:** `experiments/ptr-engine/measure/GRID-BUDGET-RECHECK.json` records that the gate enforces the dry-run **53 per cell** (48 turns + 5 allowance) → **10 × 53 = 530**, and that `cell.py` never reads 1.374532. The two pre-registered figures differ by ~130; a delta between ~530 and ~660 sits inside the bracket, and a reading outside it must be explained before it is believed.
- **Not predicted:** the split per arm. **Not assumed:** that the grid completes.

## 6. What makes the delta real rather than a re-read of a moved file

When the grid reports its spend, the reader must check **that `LEDGER-GRID-BASELINE.json` still hashes to `6b6dff4473e5e1b9a20ab73b58dfb4a884d50dff019751058ebbd0188b307470`, that `REQUEST-LEDGER.json` names a different sha with rows files that did not exist at capture, and that `ledger_delta.py` exits 0 with `deficit: none`** — otherwise the "before" number was edited or the ledger was rebuilt, and the delta measures the rebuild, not the grid.

## 7. Red → green on the guard

- **Green:** frozen baseline vs live ledger → `delta 0`, `deficit none`, exit **0**. `python -m pytest tests/test_ledger_delta.py` → **5 passed**.
- **Red:** baseline `budget.spent` edited 1101 → **1106** (raw count left at 1101):

```text
spent_before            1106
spent_now               1101
delta                   -5
remaining_now           3219
remaining_before_minus_delta  3224
deficit                 5
discrepancy             baseline is internally inconsistent: budget.spent (1106) != requests_raw (1101) -- the baseline was edited, not frozen
discrepancy             delta (-5) != requests_raw delta (0): spend moved by -5 while raw requests moved by 0
discrepancy             remaining_raw_now (3219) != remaining_raw_before - delta (3224); gap 5
verdict                 FAIL (arithmetic does not close)
```

exit **1**.

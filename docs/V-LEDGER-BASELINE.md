# V-LEDGER-BASELINE — independent verification of the ledger baseline

**Verdict: `baseline_sound`.** Offline (zero requests, no live cell). Date 2026-10-26, head `f17663d1`.
Artefact: `experiments/ptr-engine/measure/V-LEDGER-BASELINE.json`. Nothing was rebuilt, re-pinned or edited.

## 1. Row count — recomputed, not read back

Counted every row myself over the ledger's **own** file set — `request_ledger.py:784`'s default glob
`<repo>/experiments/ptr-engine/measure/rows-*.jsonl` — applying the ledger's documented costing rule
(`classify()` at `request_ledger.py:302-311` minus `suppression_marker()` at `:292-301`: `billed:false`,
`followup_suppressed` truthy, or `served_from == "prompt"` costs nothing; everything else costs one
request; unmarked rows are counted and flagged `assumed_billed`).

| | mine | `REQUEST-LEDGER.json` |
|---|---|---|
| files | 15 | 15 |
| rows | 1,128 | 1,128 |
| `requests` | **1,128** | **1,128** |
| `requests_raw` | 1,128 | 1,128 |
| `assumed_billed` | 232 | 232 |

**No file's count differs.** Per-file `rows`, `requests` and `sha256` are identical to the ledger's
`per_file` block for all 15 files, including the 6- and 27-row `rows-cell-*` files.

## 2. The 27 — confirmed

`1,101 + 27 = 1,128`, exactly. The 27 are `experiments/ptr-engine/measure/rows-cell-pointer-stable-20261026T182535Z.jsonl`
**lines 1-27**, all `kind: "turn"`:

- sha256 `46afc892480ae1dbe4b20d13fd4dacb983653a9f0a04b6a42a6283b3c55ca3b1`
- first ts `2026-10-26T18:25:56.773Z`, last ts `2026-10-26T18:31:25.300Z`

The other fourteen files independently sum to exactly **1,101** — the v2 figure — so the rebuild added one
file and nothing else moved. The ledger's own `supersedes` block records the v2 artefact at
`2f60b831…` with `requests_raw 1101`, `requests_deduplicated 1071`, 14 files.

## 3. The dedup diagnostic

`requests_deduplicated 1098`, `duplicate_excess 30`, `deduction_rule_sound false`,
`diagnostic.deducted false` — all four reproduced from the builder today.

**What the cap gate actually spends against: 1,128.** `request_ledger.py:596` publishes
`requests = requests_raw` whenever `deduct` is false, and `:687` sets `budget.spent = requests_published`;
`cell.py:1255` then spends `report["budget"]` directly. The 1,098 (and v2's 1,071) are printed as
diagnostics and can never reduce spend, because `content_sha256` hashes the assistant's `content`, not a
request identity (`run_longrun.py:1555`; 869/869 rows equal `sha256(content)`).

## 4. Baseline integrity — three for three

| check | frozen | now | |
|---|---|---|---|
| ledger sha it points at | `6da0c1f1…c27806` | `6da0c1f1…c27806` | pass |
| frozen numbers vs builder now | 1128 / 3192 / 1098 / 30 / deducted false | identical, 15 files | pass |
| v1 `LEDGER-GRID-BASELINE.json` byte-unchanged | `6b6dff44…307470` | `6b6dff44…307470`, mtime 18:24:48Z | pass |

The builder was run in-process (`build_report(sorted(glob(...)), 4320, 0, 0)`) — no file written.

## 5. Headroom arithmetic and the refusal

`cap 4,320 − spent 1,128 = 3,192 remaining` ✅ (`budget.cap/reserve/spent/remaining` agree).

- **16-cell price 1,056** = `PAIR-6+CTX-2`: 768 turns (16 × 48) × 1.374532 → 1,056
  (`price-replication.json:38,461`; `docs/PRICE-REPLICATION.md:175,215`) → **2,136 left**.
- the **wired** package today is the 10-cell one, `1,016 = 964 + 48 + 4` (`GRID-PARAMS.json :: price`)
  → 2,176 left. Both fit; a launcher must not mix them.

If the grid ran out, the cell-level refusal is (`run_longrun.py:407-413`):

> `CAP REFUSED at T{turn} ({kind}) — over the {limits}: spent={spent} would_spend={would} cap={cap} reserve={reserve} headroom={headroom} allocation={allocation} used_in_run={used_in_run} turn={turn} kind={kind} projected={projected} over_by={over_by} — nothing sent`

and the pre-launch G1 sentence (`cell.py:1283-1291`) is

> `this cell would need %s requests … on top of the %s requests already spent, taking cumulative spend (projected) to %s requests against a limit of %s requests (cap %s - reserve %s): shortfall %s requests, so it must not send`

The accounting line is `request_ledger.py:745-747`: `budget: spent=… would_spend=… cap=… reserve=… headroom=… projected=… remaining=… (… de-duplicated diagnostic … -- NOT deducted)`.

## 6. Zero-spend assertion

The newest `rows-*` file is `rows-cell-pointer-stable-20261026T182535Z.jsonl` (27 rows), mtime
`18:31:25.298Z` against a last row timestamp of `18:31:25.300Z` — **−2 ms**, inside the writer's flush
interval. Every other file is older. Nothing post-dates the baseline freeze `19:04:18Z`; **no live request
has been billed since the stopped cell.**

## Notes (no repair performed, none needed)

- `GRID-CELL-SANITY.json` marks both `rows-cell-*` files `must_not_enter_analysis` — an analysis-eligibility
  rule, not a spend rule: their 33 rows were billed and belong inside the 1,128.
- Line drift already recorded by the ledger itself: the ledger-cap recompute is `cell.py:1255` (line 734 is
  the projection gate's `if not ok:`); `content_sha256` is assigned at `run_longrun.py:1555`.

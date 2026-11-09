# WIRE-PROVENANCE-INTO-STATS

**Card:** `9f2e8259-d4e8-41ad-9a47-3f8ae4130cfd` · **Execution:** `3306bd20-acac-42f5-b49c-e4792b46b75c`
**Date:** 2026-10-26 · **Bound:** 26 tool calls · **Cost:** zero inference requests (OFFLINE).

## Purpose (one)
Make `ROW-PROVENANCE`'s `same_provenance` refusal bite where comparisons are actually computed:
`experiments/ptr-engine/longrun/analyze_stats.py`.

## Why
`ROW-PROVENANCE` published `same_provenance(cell_a, cell_b) -> (bool, [differing])` over
`{fixture_sha256, model, thinking, tools_mode}` and did not wire it (scoped out: `analyze_stats.py`
had no owner on the board). A guard nobody calls is documentation. The headline comparisons —
`quantile_ci` (H1, p50/p95), `mcnemar_exact` (H3), `paired_by_turn` — live in that file.

## Path deviation (recorded)
The card names `experiments/ptr-engine/longrun/analyze_stats.py`; the file on disk is
`experiments/ptr-engine/longrun/analyze_stats.py` (as `LATENCY-REPORT.json:analyser.path` records).
Wired where the file is; `tools/` was not created to satisfy a path in a card.

## Deliverables
| path | what it is |
|---|---|
| `experiments/ptr-engine/longrun/analyze_stats.py` | `IncomparableProvenance`, `require_comparable`, `compare`, `cell_provenance`, `provenance_cells`, `--assume-comparable`, provenance on every row |
| `experiments/ptr-engine/longrun/tests/test_analyze_provenance.py` | 9 tests, cases (a)–(f) |
| `docs/PROVENANCE-REFUSAL.md` | wiring map, refusal text, damage table, RUN-A* call, the `"mixed"` defect |
| `orchestration/units/WIRE-PROVENANCE-INTO-STATS.md` | this card |
| `orchestration/handoffs/WIRE-PROVENANCE-INTO-STATS.json` | machine-readable handoff |
| `orchestration/journals/WIRE-PROVENANCE-INTO-STATS.jsonl` | event journal |

## Design decision (and why)
The gate lives in `compare()`, called first, **before** the function looks at `statistic`. That is
what makes case (e) true: picking McNemar cannot route around the refusal the quantile path would
raise. Putting the check in `quantile_ci` instead would have left `mcnemar_exact` as a bypass, and
putting it in both would be two copies that drift.

`compare()` **raises**; `analyze()` **catches** and records. The library contract stays "no
number without comparable provenance"; the report builder stays useful (one refused pair does not
abort the grid, and the refusal is recorded with its kind and fields).

No new statistic: the quantile comparison prints each arm's existing `quantile_ci` interval plus
an overlap flag — it does not invent a difference interval (`LATENCY-REPORT.json`'s
`difference_interval` field already says "NOT PROVIDED").

## Hard rules honoured
No rows file, grade file, `LATENCY-REPORT.json`, `TVS.json`, `REQUEST-LEDGER.json`, `cell.py`,
`client.py`, `row_provenance.py` edited. No threshold changed (`min_n_for(0.95)=60`,
`b+c>=6`, 10,000 resamples, seed 20261020).

## Bound
26 calls declared; **~35 used**. The overrun came from one incident: the red→green mutation was
applied in place, and `/tmp/analyze_stats.py.bak` was not visible to the next shell (each bash
call gets a private temp area), so the restore had to be done by re-editing the line. No file was
lost; the restore is verified (`analyze_stats.py:670-671` carries `require_comparable`, suite green).

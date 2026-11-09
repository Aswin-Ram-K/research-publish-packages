# UNIT `ANALYSIS-PATH-DRYRUN`

**Status:** done · **requests spent:** 0 · **tool calls:** 24 · **bound:** 26 · **completed:** 2026-10-26T~14:00-05:00

## Purpose

Rehearse the **post-grid analysis path** offline, on rows that already exist, so its first real run is not
on an 8-hour / ≈720-request tranche. `V-TRANCHE-1` passed with the disclosure that *"the post-grid analysis
path (analyze() over real rows) is exercised only on synthetic rows; its first real run is the re-run of
this card."* This unit is that rehearsal. **Zero requests, zero network.**

## INPUTS (read-only)

- Era A abandoned cell, 27 rows: `experiments/ptr-engine/measure/rows-cell-pointer-stable-20261026T182535Z.jsonl`
  (+ `.claim.json`), sha256 `46afc892…`.
- Era B shape stand-in: `experiments/ptr-engine/measure/rows-longrun-v6-tools.jsonl` (72 rows: 48 `turn` +
  24 `tool-followup`, sha256 `1e78d75f…`), `rows-longrun-v5-tools.jsonl` (`586b66f2…`),
  `rows-longrun-v4-tools-2026-10-26.jsonl` + its `.grade-v5.json`.
- Multi-arm stand-in: `measure/rows-longrun-2026-10-26.jsonl` (4 arms × 48).
- Instruments: `longrun/analyze_stats.py`, `longrun/grade_v5.py`, `tools/tokens_to_verified.py`,
  `tools/verify_tranche1.py`, `measure/TVS.json`, `measure/GRID-CELL-SANITY.json`, `measure/GRID-SHAPE.json`.

## WHAT WAS EXERCISED — seven items, verdicts `ok` / `refuses_as_designed` / `gap`

| # | item | verdict |
|---|---|---|
| 1 | `turn_latency_rows()` per-arm selection, follow-up exclusion | ok (compound multi-arm × tools-on case unproven) |
| 2 | p95 refusal at n=48, forced n=96 | refuses_as_designed |
| 3 | provenance refusal era A vs era B | refuses_as_designed |
| 4 | `usable_for: []` exclusion | **gap** — no analyser reads the mark |
| 5 | TVS number / censoring | **gap** — TVS trusts a foreign `--grade`; censoring limb ok |
| 6 | H3 over 12 ids with 3 NONE, McNemar | ok (synthetic in-memory grade) |
| 7 | the one-command path | **gap** — `grade_v5` cwd-sensitive |

Full evidence, the command list, and the smallest repair for each gap: [`docs/ANALYSIS-PATH.md`](../../docs/ANALYSIS-PATH.md),
machine-readable: [`measure/ANALYSIS-PATH.json`](../../experiments/ptr-engine/measure/ANALYSIS-PATH.json).

## DELIVERABLE

- `docs/ANALYSIS-PATH.md`
- `experiments/ptr-engine/measure/ANALYSIS-PATH.json`
- this card, `orchestration/handoffs/ANALYSIS-PATH-DRYRUN.json`, `orchestration/journals/ANALYSIS-PATH-DRYRUN.jsonl`

## HARD RULES OBSERVED

- **Never asked the user** (automated session), **zero requests**, zero network.
- **Edited nothing** the card forbade: `analyze_stats.py`, `analyze.py`, `grade_v5.py`, `cell.py`,
  `run_longrun.py`, `PARM-1*`, the fixture, every row file, `TVS.json`, `GRID-SHAPE.json` and every
  published number are untouched (verified by read-only use only).
- **Wrote no `rows-*` file.** The n=96 pooling of item 2 and the 12-id grade of item 6 were built **in
  memory** and labelled exercises in both artefacts.
- No p95 emitted without its n and interval (item 2: 355.11 ms, n=96, [252.48, 416.60]).
- No threshold lowered to make an item pass; `min_n_for(0.95)=60` and `b+c<6` stand as found.

## ASSUMPTIONS (missing values, conservative defaults)

- The card names `analyze.py`; no such file exists. The analysis instrument was taken to be
  `longrun/analyze_stats.py`, the only module carrying `analyze()`/`compare()`/`quantile_ci()` used by the
  grid's hypotheses. Recorded rather than guessed silently.
- Item 6 had no on-disk grade with 12 graded cells per arm and a licensed McNemar, so a synthetic
  in-memory grade was used; the shape (cells with `arm`/`id`/`turn`/`verdict`) matches the real grade files.

## NEXT

The grid card may proceed; the re-run must run every step **from the repo root** and must not glob
`measure/rows-cell-*.jsonl` until G1 (the `usable_for` consumer) exists.

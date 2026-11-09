# LATENCY-FALLBACK — every latency figure in this corpus is a marked fallback

**Written:** 2026-10-26 · **Unit:** `LATENCY-FIGURE-HONESTY` · **Live requests: 0** · **Network: none**
**Sources:** [`experiments/ptr-engine/longrun/analyze_stats.py`](experiments/ptr-engine/longrun/analyze_stats.py) `turn_latency_rows`, the per-row `kind` field of every `measure/rows-*.jsonl`, and [`orchestration/handoffs/TURN-CENSUS-60.json`](orchestration/handoffs/TURN-CENSUS-60.json).

## The one-line summary

**No rows file on disk carries a `kind='turn-initial'` row, so every published latency figure in this
repository is the legacy `kind='turn'` selector, marked `definition_fallback: true` — the corrected turn
definition is forward-only, and any figure produced before era B is a fallback figure.**

## What the selector says, and what the corpus can satisfy

`analyze_stats.turn_latency_rows` defines a turn's TTFT as *"the TTFT of the turn's own initial request:
`kind='turn-initial'` when present, else the legacy `kind='turn'` row with `definition_fallback=true`; a
`kind='tool-followup'` row is a request inside a turn and is never a turn's latency"*
(`definition_version: ttft-definition/1`).

- The **preferred** branch (`kind='turn-initial'`) is met by **0 of 15** rows files: `explicit_initial_rows: 0`
  on every file, `mode: "fallback-turn"` on every file, `definition_fallback: true` on every file.
- The **fallback** branch (`kind='turn'`) is what every figure was computed on. On era A's
  `measure/rows-cell-pointer-stable-20261026T182535Z.jsonl` (sha256
  `46afc892480ae1dbe4b20d13fd4dacb983653a9f0a04b6a42a6283b3c55ca3b1`): 27 input rows, 27 selected,
  `fallback_rows: 27`, `explicit_initial_rows: 0`, `definition_fallback: true`.

## Why that matters for a reader

1. **A fallback figure is not a wrong figure, but it is a different quantity.** On a tools-on cell a turn
   emits several request rows (`k` `tool-followup` rows plus the turn row); the fallback picks the turn row,
   which the analyser documents as the turn's own initial request. The substitution is deliberate and
   recorded per row, but it is a substitution, and a reader comparing a latency number against a
   `turn-initial` number from a later era would be comparing two definitions.
2. **Era B is the first era allowed to publish a non-fallback figure.** The corrected definition is
   forward-only: it cannot be recovered for rows already written, because `kind` is a property of the row
   as produced by `run_longrun.py`, and no file on disk carries the `turn-initial` variant. Append-only
   provenance means the era A/B boundary is permanent, not a backlog item.
3. **The `definition_fallback` flag travels with the row, not with the document.** Any table that quotes a
   latency figure without the flag is quoting a fallback quantity as though it were the preferred one.

## Where this is load-bearing

| site | figure | definition actually used |
|---|---|---|
| `docs/RUNAWAY-POLICY.md:34` | `ttft_ms_p50 141.58` (cell `pointer-stable`, 27 turns) | fallback `kind='turn'`, 27/27 |
| `docs/ANALYSIS-PATH.md:33` | `ttft_p50 n=27 141.58ms [131.35, 166.38]` | same computation, fallback |
| `docs/ANALYSIS-CONSUMER.md:100` | `27 → 25` counts on the same cell | fallback selection, then exclusions |
| `experiments/ptr-engine/measure/LATENCY-REPORT.json` | every p50/p95 cell | fallback on every contributing file |

## What this document does not claim

It does not withdraw any figure for being a fallback — each of those figures also carries its own
`usable_for: []` caveat at its site (see the three dated blocks). It does not assert that `kind='tool-followup'`
rows were misused: the selector drops them (`dropped_followup` is reported per run). It does not propose a
repair: producing a non-fallback figure requires a cell run under the corrected writer, which is a run, not
an edit.

*Cross-reference: [`docs/TURN-CENSUS.md`](docs/TURN-CENSUS.md) for the 60-turn census, [`docs/LATENCY-REPORT.md`](docs/LATENCY-REPORT.md) for the operator's report.*

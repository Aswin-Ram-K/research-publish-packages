# STATE-CLIFF — corrected residency record (2026-11-04)

**Status: correction of a prior report. The sweep ran; the sweep's published
residency numbers do not survive re-derivation.**

Provenance: rungs executed 2026-11-04 12:45–13:49 UTC (`run_sweep.log`), every
rung followed by a restore proof on the six keys (`rung-*/restore_server_info.json`).
Derivation here: `residency_bounds.py` → `residency-bounds.json`, which reads only
`rung-<N>/analysis.json` and `rung-<N>/rows.jsonl` (each rows file re-hashed and
matched against the digest the analysis recorded — `rows_digest_matches_analysis`
is `true` at all four rungs).

## What the rows support

| rung (`max_mamba_cache_size`) | capacity (tokens) | Δ capacity vs 64 | docs pushed | pressure ratio | sampled hits | resident lower bound | boundary bracket (doc position) |
|---|---|---|---|---|---|---|---|
| 64 | 1,618,422 | — | 283 | 1.504 | 10 / 30 | ≥ 10 docs, ≥ 85,824 cached tok | 146 … 274 |
| 48 | 1,721,923 | +6.4 % | 300 | 1.498 | 10 / 30 | ≥ 10 docs, ≥ 85,440 cached tok | 155 … 291 |
| 32 | 1,783,398 | +10.2 % | 300 | 1.447 | 10 / 30 | ≥ 10 docs, ≥ 85,440 cached tok | 155 … 291 |
| 16 | 1,878,287 | +16.1 % | 300 | 1.374 | 0 / 30 | — (none sampled) | boundary < 291 |

"Sampled hits" = documents replayed from the newest, middle and oldest band, ten
each, after the pressure phase. Only 30 of 283–300 pushed documents are ever
replayed, so **10 hits is a sampled lower bound, never a resident count**. The
bracket is the gap between the deepest sampled miss and the shallowest sampled
hit; everywhere it is ≥ 128 documents wide.

## Five claims that must not be repeated

1. **"64/48/32 have the same resident window."** They do not have a measured
   window at all. Each rung replayed the *newest ten* of whatever it pushed, so
   "newest ten hit" is a property of the sampling, not of the engine. Rung 64
   sampled positions 274–283 (it pushed 283 docs); rungs 48/32/16 sampled
   291–300 (300 docs). The bands are indistinguishable because they are the same
   ten slots of a different pool, not because the windows are equal.
2. **"The KV pool binds at 32–64 and the mamba slot budget only at 16."**
   Unsupported. The flag also moves capacity (1.62 M → 1.88 M tokens, +16.1 %),
   so a rung delta mixes two variables. And no boundary probe was run: the
   boundary is bracketed at ≥ 128 documents wide, which cannot separate a KV
   bound from a slot bound.
3. **"Rung 16 evicted everything because the slot budget bound."** Rung 16 is
   the only rung with *no* sampled hit — a real difference — but its cause is
   not established: a smaller resident window, the higher capacity pushing the
   newest documents past a harder eviction edge, and the lower pressure ratio
   (1.374 vs 1.504) are all consistent with the observation. Causality unknown.
4. **`sweep_summary.json` is not a source for residency.** Its `res_docs`
   column reports 27 / 10 / 10 / 0, and no generator in this cell produces that
   column (`grep -rn "res_docs" *.py` finds only
   `predicted_resident_docs` in `battery.py:580`). The file was assembled ad hoc
   after the runs. Its `res_docs` / `res_tok` / `res_ratio` columns are **void**;
   `rung`, `cap`, `pr`, `oldest`/`middle`/`newest` hit rates and `reqs` reproduce.
5. **"Pressure was held at 1.50×."** It was not: 1.504 / 1.498 / 1.447 / 1.374,
   because the target is enforced on *measured* tokens against a capacity that
   itself moves with the flag. Rung 16 is 13 % under the target relative to
   rung 64.

## What the sweep does establish

- All four flags were accepted and read back from `/get_server_info`
  (`max_mamba_cache_size` = 64/48/32/16, `page_size` still 1).
- Each rung restored production to the six baseline keys.
- At 1.37–1.50× capacity the newest ten documents always hit at 48/32/64; the
  oldest and middle ten never hit. That is evidence for LRU-shaped eviction
  under pressure, at every rung, and it is the only cross-rung statement the
  sampling density supports.
- 319–336 requests per rung (rung 64 pushed 283 documents, the rest 300), 0
  failures, one rung at a time.

## What would settle the question (not run)

A boundary probe: binary-search the replay position of a single document between
the sampled miss and hit, holding the pushed-token total fixed (not the ratio),
and reading back `max_mamba_cache_size` plus capacity per rung. The probe needs
the same engine fingerprint on both sides, so it is a separate registered run,
not a repair of this one.

## Repair record

`orchestration/handoffs/M4-EVICT.json` was overwritten by the `STATE-CLIFF-16`
handoff during the sweep. The overwritten bytes are preserved at
`experiments/context-cache/cells/STATE-CLIFF/provenance/M4-EVICT.overwritten-by-STATE-CLIFF-16.json`
(2,822 bytes, sha256 `8bae31d0…`). The original was restored from the committed
git blob (`HEAD:orchestration/handoffs/M4-EVICT.json`, 5,286 bytes, sha256
`fd326da6…`) after checking it independently: its `evidence.rows_sha256`
(`08be0204…`) equals the actual sha256 of `cells/M4/rows.jsonl` (327 rows).

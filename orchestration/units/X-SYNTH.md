# X-SYNTH — cross-stack synthesis

## Objective
Revise the existing package so the cross-stack evidence is in it, honestly and re-derivably:
new MANUSCRIPT section "Cache-hit granularity across serving stacks"; CLAIMS.md additions
(one line per new number with exact recompute.py invocation); GAPS.md rewrite (G3/G4/G5
CLOSED or NARROWED, or stated not settled with reason); RUN.json stacks[]; recompute.py new
claim functions (fail loudly if config_id has no rows) with missing stack treated as sglang.

## Hard bound
40 tool calls. If V-XSTACK is fail, write partial and name blocked claims. V-XSTACK2 partial
is the gate (V-XSTACK fail superseded).

## Write paths
papers/context-cache/MANUSCRIPT.md
papers/context-cache/CLAIMS.md
papers/context-cache/GAPS.md
papers/context-cache/RUN.json
papers/context-cache/recompute.py
orchestration/units/X-SYNTH.md
orchestration/handoffs/X-SYNTH.json

## Deliverable
Edits above; verification by full recompute suite.
## What this pass actually did (2026-10-23, second pass)

- **Gate:** `orchestration/handoffs/V-XSTACK2.json` = `partial` (V-XSTACK = `fail` is
  superseded). Gate satisfied on tool call 1.
- **V-XSTACK `not_reproduced` respected, not argued:**
  - "TUNED page_size 1 / no grid" — the §9a rewrite states the 64 grid and the
    `_mamba_cache_chunk_size` 64 reconciliation (V-XSTACK2 check 2, C59); the no-grid reading
    appears nowhere in the package as a claim.
  - "SGLang means 729.22/746.02/725.75" — §9a no longer carries those rounded four-arm means
    as the grid-section figures; the new claims use whole-cell means (C60: 739.25) and the
    paired deltas (C58), both recomputed from raw rows.
  - "V1 law 20/20 via a clamp" — §9a does not state a clamp law; it states the unit identity
    (C56: 0/264 cross-multiples) and defers the exact-form count to C49.
  - "S1 32k hit 0.9586" — no §9a sentence rests on that figure.
- **New claims C55–C61** (6 value claims + 1 guard), each with a `recompute.py` command in
  CLAIMS.md. Same-engine condition that moves the grid: `--page-size 128` (C58); conditions
  that do not: `--page-size 64` (C57), SLRU eviction under 1.505083x pressure (C59).
- **recompute.py:** `_config_rows()` raises `KeyError` (non-zero exit) when a cited
  `config_id` has no rows in its cell; `C61`/`grid-guard` prints PASS/FAIL per config and is
  auto-run whenever any grid claim is in the invocation. `rows()` already back-fills a missing
  `stack` to `sglang`, so every pre-cross-stack cell still recomputes.
- **RUN.json:** `stacks[]` with 7 entries (S0, S1, S2, V1, V2, V3, TUNED): version, flags or
  launch-line digest, G0 verdict, cell ids.
- **Verification:** `recompute.py all` → `58 claims checked, all match` + `GRID GUARD PASS 7/7 configs`.

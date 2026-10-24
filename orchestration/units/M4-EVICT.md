# UNIT CARD — M4-EVICT · eviction pressure

**One purpose:** measure what the server's radix cache does **past KV capacity** — whether the
LRU evicts the way the runtime config claims (`radix_eviction_policy: lru`), and whether the
append-note/pointer discipline still buys cache reuse once the working set no longer fits.

## Why this cell

Every context-cache cell measured so far (`E1`–`E4`, `E4R`, `LIVE-MEAS`, `G3`, `M1-M`) ran
*inside* the cache: deepest battery prompt 64k, ≤5 concurrent sequences, against a KV pool that
`/get_server_info` reports at ~1.3–1.6M tokens. Nothing has ever pushed the pool past capacity, so
the eviction policy is asserted from a config flag, never measured. `GAPS.md` §G6 is the related
open gap (the compaction decomposition is arithmetic, not instrumented); this cell is the
*capacity* boundary rather than the compaction boundary.

## Protocol (as executed)

1. **Capacity measured per run** from `GET /get_server_info` →
   `internal_states[0].memory_usage.token_capacity`. Not hardcoded, not read from
   `state/config/live-server-config.json` (which is a dated sample:
   `token_capacity 1,306,681`).
2. **Corpus built offline** (`corpus.py`, no network): distinct documents, each a 4-word salt +
   one body, sized with the repo's offline estimator (`ceil(chars/4)`) and generated from a
   per-document seeded PRNG. Pool capped at 300 documents; each document is one request with a
   unique first token run, so first-submission `cached_tokens` can only be the document's own.
3. **Phase P (pressure):** submit documents one at a time, `temperature 0`, one request in
   flight, until **measured** cumulative `prompt_tokens` ≥ 1.5 × capacity. The stop rule uses
   measured tokens, not the estimate.
4. **Phase R (replay):** re-request the **oldest 10**, a **middle 10**, and the **newest 10**
   documents, byte-identically, and record `cached_tokens`. Replay order is
   newest → middle → oldest so the (expected) evicted band's re-insertion cannot perturb the
   resident bands measured before it.
5. **Phase D (discipline under pressure):** on the middle band's adjacent slice —
   disjoint from the Phase-R replay set, so nothing is double-warmed — 6 documents: **3 full
   resend** vs **3 append-note-at-delta-end**. Both shapes re-send a byte-identical prefix; the
   note shape adds one `[note]` node at the tail, exactly as `CompactionPolicy.APPEND_NOTE`.
   `incremental_uncached = uncached_note − appended_tokens` is the discipline's whole value: the
   block tax when the prefix is resident, the whole document when it is not.

## Hard bounds

- **600 live chat requests** hard cap (Phase P is ~265 + 30 replay + 6 discipline ≈ 301).
- **≤300 documents** in the corpus; otherwise shrink each document instead.
- Wall bound **90 minutes**; if the post-sample projection says Phase P cannot finish in time,
  fall back to **1.2 × capacity** and record the shortened pressure.
- Holds `experiments/context-cache/.occamy.lock` for the whole run (timeout 300 s).
- **3 consecutive failures → stop** and report `partial` with the failure verbatim.
- No restart, no stop, no reconfigure of the model. No writes under `papers/context-cache/`.

## Declared write paths

```
experiments/context-cache/cells/M4/**          (corpus.py, corpus.jsonl, corpus_manifest.json,
                                                battery.py, rows.jsonl, analysis.json,
                                                server_info.json, run.log)
orchestration/units/M4-EVICT.md
orchestration/handoffs/M4-EVICT.json
```

No overlap with the concurrently running context-cache units: each of those writes only its own
`cells/<UNIT>/**` directory and its own handoff, and the `.occamy.lock` serialises live runs.

## Deliverables

| File | Contents |
|---|---|
| `cells/M4/corpus.py` | offline, reproducible pressure corpus (300 distinct documents) |
| `cells/M4/battery.py` | the live battery: capacity probe, phases P/R/D, analysis, handoff |
| `cells/M4/rows.jsonl` | one row per request: `phase`, `doc_id`, `doc_position`, `prompt_tokens`, `cached_tokens`, `uncached_tokens`, `latency_ms`, plus run-level `stack`, `config_id`, `config_sha256`, `token_capacity`, `total_pressure_tokens`, `pressure_ratio` |
| `cells/M4/analysis.json` | replay profile per band (mean + per-doc), LRU verdict with its criterion, eviction onset in tokens, Phase-D discipline comparison |
| `orchestration/handoffs/M4-EVICT.json` | unit handoff (unit shape) |

## Kill condition

If capacity cannot be measured (3 tries), or 3 consecutive requests fail, stop: write the
complete-shaped `partial` handoff naming the remainder and the failure text. A profile that is
**not** LRU is a result, not a failure — it is reported as measured.

## Assumptions (recorded, because an automated session cannot ask)

- Documents are sized with the offline estimator; the pressure target is enforced on **measured**
  `prompt_tokens`, so the estimate only has to be close enough to make the pool big enough.
- A **4-word salt** stands in for the card's "4-token salt" (the card's unit is a token; four
  distinct low-frequency words give a stable, distinctly-tokenised opening run).
- Phase D uses the slice immediately *after* the middle band; the middle band itself was replayed
  in Phase R and a second request would double-warm it.

## Result (measured 2026-10-23)

| | |
|---|---|
| `token_capacity` (per run, from `/get_server_info`) | **1,620,892** (the card's 1,306,681 in `state/config/live-server-config.json` is a stale sample, +24 %) |
| pressure achieved | **2,434,133 tokens = 1.5017 x capacity** over 283 documents |
| replay hit profile | oldest **0.000** (10/10 zero) · middle **0.000** (10/10 zero) · newest **0.997** (10/10 full) |
| LRU order verdict | `consistent_with_lru`, 4/4 checks |
| resident capacity (probe) | **30-31 documents = 258,035-266,636 prompt tokens = 0.159-0.165 x capacity = ~2 x `context_length`** |
| token-pool LRU prediction | 188.45 documents — **excluded** |
| eviction onset | first eviction at document **31**, 266,864 cumulative prompt tokens (0.1646 x capacity) |
| Phase-D discipline | `note_unusable` — full resend 0.0 hit, append-note 0.0 hit, 78.7 appended tokens, no saving |
| requests | **327 / 600** (P 283, R 30, D 6, B 8) + 69 calibration = **396** total |

**Added beyond the card's minimum protocol:** `cells/M4/boundary_probe.py` (capped at 16
requests, 8 used). The three replay bands can only bracket the onset to 128 documents, and the
card requires the onset point, so the probe re-sends pooled documents byte-identically and
bounds the resident capacity by recency-rank inequalities: rank 27 hit (`W>=27`), ranks 39/34/32
miss (`W<32`), rank 30 hit (`W>=30`), rank 32 miss (`W<32`) -> **W in [30, 31]**. A second,
independent submission-position formulation gives [27, 31].

**What the pressure actually shows.** The policy *is* LRU in ordering, but the window it applies
to is ~1/6 of the reported token pool: at 1.5x capacity only the newest ~31 of 283 submitted
documents (11 %) are reusable, and the middle band — 0.73-0.78 x capacity back — is already
100 % evicted. The measured cap is order-of-magnitude consistent with the mamba/context knobs
the server reports (`max_mamba_cache_size 64`, `mamba_track_interval 256`,
`uses_mamba_radix_cache true`, `context_length 131072`), but this cell does **not** establish
the mechanism (same limit as G13).

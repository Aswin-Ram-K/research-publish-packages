# UNIT MISS-LAW — derive the append-cost (re-billed tail) law

**Status:** done — `orchestration/handoffs/MISS-LAW.json`. Result below.

## Result (measured, 764 fsynced rows)

```
SGLang  B = 64   : R = (P1 mod 64)  + L
vLLM    B = 1056 : R = (P1 mod 1056) + 1056 + L
both             : R = P1 + L   when P1 mod B in {0, 1}   <- whole prefix re-billed
```

- SGLang residual 0 in **186/186** rows (residues 2…63 × 3 reps) and in all 20 payload variants
  (`n` up to 128 — the residue, not the payload, sets the cost).
- vLLM residual exactly `+1056` in every row (18 residues × 3 reps + 12 payload variants): an append
  there costs a block *and* a tail.
- The `{0,1}` cliff is **residue-based, not positional** (11/11 misses across block #32…#125), and it
  is a real missing entry, not rounding — an identical repeat at `P1 = 8064` also reads `null`.
- Controls: WARM 8000/8053 = 99.3 %; COLD `null` on both requests. No `/flush_cache`, no restarts.
- **Validation fails as posed**: the quoted +44.8 % / −95.6 % are both **cold** cells, where the law
  collapses to `R = P` and reproduces them degenerately; the boundary term there is 0 and is bounded
  by 378 tokens against a 10,244-token swing (≤ 3.7 %). On the crossover's own shipped warm rows the
  law is exact in 57/60, and warm L1 loses at both fetch counts — so the sign flip is a cold-regime
  round-count effect, **not** append re-billing.

## Purpose

Our crossover measurement found that the sign of pointer-style lazy loading flips with
**fetch count**, not corpus size: at 30,000 chars, 2 fetches = **+44.8 %** billed-token saving,
6 fetches = **−95.6 %**. Suspected mechanism: every fetch is an **append**, and an append that
lands off the server's cache block boundary invalidates the tail and re-bills it. We have a
boundary observation from an earlier 40-row experiment (`L mod 64 == 0` missed in 45/45 rows,
recovery at `L−64` in 40/40) but **no formula**.

This unit derives the formula.

## Servers (one writer only — this unit)

| id | model | endpoint | block size |
|---|---|---|---|
| `sglang` | `occamy-1.0` | `http://192.168.2.168:8012/v1` (SGLang, max_model_len 131072) | measured, not assumed |
| `vllm` | `qwen3.5-9b` | `http://192.168.2.168:8014/v1` (vLLM, max_model_len 32768) | measured (`cache_config_info` advertises `block_size="1056"`) |

## Instrument

- **SGLang:** `usage.prompt_tokens_details.cached_tokens`. Absent/`null` on a cold request.
  `null` is **not** zero — recorded as JSON `null` with `cached_reported=false`, and only then
  treated as 0 for arithmetic.
- **vLLM:** the OpenAI response carries **no** cache field on this build (`prompt_tokens_details`
  is always `null`, even on a measured 3.77 s → 0.61 s repeat that proves caching happens).
  Instrumented instead by delta of the server counter `vllm:prompt_tokens_cached_total`, read
  immediately before and after each serial request. Attributable because requests are strictly
  serialized and this unit is the only writer.

## Method

1. Fixed history `H` (~8,000 tokens of filler) + fixed question; append a payload.
2. Payload length `L` is **exact in tokens**: `" the"` is 1 token on both tokenizers, so
   `" the"*n` is exactly `n` tokens (verified via `/tokenize`). The measured append
   `L_app = P2 − P1` also carries the constant template framing tokens `T`.
3. Each cell = one **prime** request, then one **measure** request. 3 reps, each rep a
   *fresh prefix* (unique nonce) so every rep is an independent prime→append cycle.
4. `B` determined **empirically** (gcd of measured `cached_tokens`, cross-checked against the
   sawtooth), never assumed to be 64.
5. ≥2 history lengths, with `H mod B` calibrated to hit `0`, `1`, `B//2`.
6. Controls: COLD (unique nonce → instrument must read ~0) and WARM (identical repeat →
   instrument must read high).

## Request shape (exact, reproducible)

```
round 1 (prime):   [system: NONCE + "\n\n" + FILLER + "\n\n" + QUESTION,
                    user:   "Reply with the single word OK."]
round 2 (measure): same two messages +
                    [assistant: "OK.", user: " the"*n]
```

The nonce is 10 one-token words in a per-cell permutation → **constant token count**, so
`P1` (and therefore `H mod B`) is stable across the reps of a cell while the prefix stays cold.

## Hard rules honoured

- No `/flush_cache`, no restarts, no model downloads, no network beyond the two endpoints.
- No writes under `experiments/ptr-engine/**`, `release/**`, `papers/**`, `src/**`,
  `/home/zer0null/Duval`.
- One writer per endpoint; loops are serial.

## Write paths

- `experiments/miss-law/LAW.md`
- `experiments/miss-law/rows.jsonl` (one row per request, fsynced per row)
- `experiments/miss-law/run.py`, `experiments/miss-law/analyze.py`
- `orchestration/units/MISS-LAW.md`, `orchestration/handoffs/MISS-LAW.json`

## Bound

60 tool calls. Deliverable is a formula **or** an explicitly-stated negative result; both are
valid. A fitted curve that does not hold is not.

## Assumptions (autonomous: conservative defaults recorded, not asked)

- `null` `cached_tokens` is treated as "not reported" and then as 0 for `uncached` arithmetic;
  the row keeps `cached_reported=false` so the analysis can exclude those rows.
- vLLM's `block_size="1056"` is treated as a *claim to test*, not a fact; `B` is taken from the
  measured gcd.

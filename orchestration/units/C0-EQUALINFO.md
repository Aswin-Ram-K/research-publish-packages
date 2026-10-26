# C0-EQUALINFO — equal-information comparator (corrected)

**Bound** 30 tool calls / 105 requests, 2 retries. Used **100 requests, 0 errors, 0 retries**. Writes: row file, this card, `orchestration/handoffs/C0-EQUALINFO.json`. No edit to RECORD/CLAIMS/MANUSCRIPT or `rows-baseline-2026-10-26.jsonl`.
**Design** same 4-turn plan, same question (`AUD-4417`), 3 reps, both models. C0F = full working set (all 12 x 9000 B bodies) in the system message, no history; C0FT = same plus the growing exchange; R = 458-byte index only, tool-call fetch (SGLang) / text `FETCH` (vLLM).
**Endpoints** SGLang 8012 `occamy-1.0-NVFP4` and vLLM 8014 `qwen3.5-9b`, both probed HTTP 200 / curl exit 0. No loopback.
**Truncation** none: all 12 bodies in every C0F/C0FT prompt on both models (SGLang est 22,524 tok of 131,072; vLLM measured `prompt_tokens` 22,594 of 32,768).

## Accuracy (turn 4, exact `AUD-4417`)

| model | C0F | C0FT | R |
|---|---|---|---|
| occamy-1.0-NVFP4 | **3/3** | **3/3** | **3/3** (fetch k01 at T4) |
| qwen3.5-9b | **3/3** (repair) | not measured | 0/1 (repair; never fetched k01) |

The corrected baseline now answers on both models — the predecessor's 0/3 was a card defect, not a model limit.

## Uncached per turn (4-turn rep, incl. every request in the rep)

| model | C0F | C0FT | R | R/C0F |
|---|---|---|---|---|
| occamy (cached reported) | 1911 (rep1 5676, rep2/3 28) | 47 | 3524 (9476 / 1044 / 52) | **1.84x — pointer DEARER** |
| qwen (gross prompt only) | 22594 | n/m | 6531 (n=1) | 0.29x |

**Reading.** On SGLang the full working set is prefix-cached: after the cold prime a turn costs 28-66 uncached tokens, while the pointer arm pays for every resolved body on every turn because each resolve rewrites the prefix. The pointer protocol is **not cheaper at equal information** here; it is 1.84x dearer on the mean and 1.67x dearer on the cold rep. On vLLM, which reports no cache, gross prompt makes the pointer arm look 3.5x cheaper — that number compares a cached-capable baseline against a protocol that keeps its context small, and must not be quoted as a win.

## Instrument

- **vLLM thinking trap:** `enable_thinking:false` was sent to SGLang only (as the card said). On qwen, 27/42 design rows returned empty content at `completion_tokens:300` — reasoning ate the budget. A 10-request repair with the flag on qwen gave C0F 3/3 valid rows and R rep1; the rest of the vLLM grid (C0FT 12 rows, R reps 2-3, 16 rows) did not fit the cap and is **not measured**.
- **vLLM cache:** `prompt_tokens_details = null` on 0/45 reported → all vLLM uncached figures are gross prompt tokens, upper bounds (`cached_reported:false`).
- **Protocol parity:** vLLM refuses `tool_choice auto` (HTTP 400 without `--enable-auto-tool-choice`), so R there is a text `FETCH` protocol, not identical to SGLang's tool call.
- Rows: 100, append-only, `experiments/ptr-engine/measure/rows-equalinfo-2026-10-26.jsonl`; repair rows carry `thinking_off:true` and an `instrument` note so they are separable.

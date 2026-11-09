# UNIT ENDPOINT-CAVEAT-FIX — correct the `:8012` cache-credit caveat, additively

**Purpose.** `docs/ENDPOINT-STATE.md` and `experiments/ptr-engine/measure/ENDPOINT-STATE.json` told every
future card that per-request cache credit cannot be observed on `:8012`. That is false, and the contradicting
measurement was already on disk in `experiments/ptr-engine/measure/CACHE-CREDIT-CHAT.json`. Correct the two
files **additively** (errata, never rewrite), with both artefacts named by path.

**Constraints.** Offline — zero inference requests. Additive only: no pre-existing line may be deleted or
altered. Do not touch `client.py`, `run_longrun.py`, `docs/TVS.md`, `measure/TVS.json`, any rows file, or the
two CACHE-CREDIT-CHAT evidence files.

**Write paths.** `docs/ENDPOINT-STATE.md`, `experiments/ptr-engine/measure/ENDPOINT-STATE.json`,
`orchestration/units/ENDPOINT-CAVEAT-FIX.md`, `orchestration/handoffs/ENDPOINT-CAVEAT-FIX.json`,
`orchestration/journals/ENDPOINT-CAVEAT-FIX.jsonl`.

**Bound.** ≤16 tool calls, 0 requests.

## Citations verified verbatim before editing

| citation | on-disk text |
|---|---|
| `experiments/ptr-engine/longrun/client.py:604` | `def usage_cached_tokens(usage_payload):` |
| `client.py:611,613` | `details = usage.get("prompt_tokens_details")` / `value = details.get("cached_tokens")` |
| `client.py:661` | `url = cfg.base_url.rstrip("/") + "/chat/completions"` |
| `client.py:339-340` | `if cfg.stream:` / `body["stream_options"] = {"include_usage": True}` |
| `run_longrun.py:1760-1762` | `"prompt_tokens": prompt,` / `"cached_tokens": cached,` / `"uncached_tokens": uncached,` |

**Recorded drift:** the card cited `run_longrun.py:1755-1757` for the row keys; on disk 1755-1757 is the
`stop_evidence` / `completion_recorded` block and the row keys sit at **1760-1762** (+5 lines). The substance
(row keys are written; `uncached = prompt - cached`) holds, so the correction proceeded on verified premises and
the drift is recorded in the journal, the handoff and the board report rather than papered over.

## Changes

1. `docs/ENDPOINT-STATE.md` — appended `### Correction (2026-10-26, after CACHE-CREDIT-CHAT)` beneath the
   original caveat paragraph: credit **is** per-request observable via `/v1/chat/completions`'s
   `prompt_tokens_details.cached_tokens` and as a `sglang:cached_tokens_total` delta; it is **not** observable via
   `/v1/completions`' usage object (what the original probe read); the proof cost 2 requests; both artefacts named;
   the programme consequence stated in one sentence.
2. `experiments/ptr-engine/measure/ENDPOINT-STATE.json` — added (never overwrote)
   `cache_credit.per_request_credit_proven_on_chat_endpoint: true`,
   `per_request_credit_proven_on_completions_endpoint: false`,
   `correction_ref: "experiments/ptr-engine/measure/CACHE-CREDIT-CHAT.json"`, plus `correction_date_utc`,
   `correction_note`, `correction_measurement`, `correction_consequence`. Original keys
   (`per_request_credit_proven: false`, `cumulative_credit_counter`, `conclusion`) are untouched.

## Verification

JSON validates; every pre-existing claim string still greps exactly once; sizes only grow. See handoff.

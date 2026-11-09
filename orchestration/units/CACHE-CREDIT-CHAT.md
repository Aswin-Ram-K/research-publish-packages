# CACHE-CREDIT-CHAT

**Status:** done · **Requests:** 2 / 4 · **Bound:** ≤18 tool calls, ≤4 requests
**Endpoint:** `http://192.168.2.168:8012` (never loopback) · 2026-10-26T17:04:38Z
**Card ancestry:** launched from the main session as the card that must settle whether per-request
cache credit is measurable on the endpoint `longrun/client.py` actually calls, before H2's cache
limb is declared measurable or unmeasurable.

## Why this unit exists

`measure/ENDPOINT-STATE.json` (`verdict: warm`, 2 requests, 17:01:19Z) probed **`/v1/completions`**
and concluded (caveat 1) that `:8012` has no cumulative cache-credit counter and (caveat 2) that
usage objects carry no `cached_tokens` field. `longrun/client.py:661` posts to
**`/v1/chat/completions`**. A missing field on one endpoint is not a missing capability on the
other, and `docs/TVS.md` publishes `cached_share 0.8523`, which some live path must be producing.

## Task

1. Locate the provenance from code, no requests: which field, which function, which endpoint,
   whether 0.8523 is reproducible from the on-disk rows.
2. One targeted pair on the runner's own endpoint (non-stream first; streamed pair only if the
   non-stream pair showed nothing), prompt ≥1,200 tokens, byte-identical, `max_tokens:4`, `temperature:0`.
3. Free `/metrics` deltas around the pair.
4. Answer three questions: (a) does request 2 report/accrue credit, (b) through which key and is
   that key already written into rows, (c) therefore is H2's cache limb measurable — yes /
   yes-with-a-one-line-patch / no.
5. No patch applied, even if needed; the exact diff belongs in the handoff.

## Hard rules observed

- **2 of 4 inference requests spent**; a fifth would have failed the unit.
- Free metadata unlimited; each `/metrics` and `/health` call timestamped in the journal.
- No capability claim transferred between endpoints.
- `client.py`, `run_longrun.py`, `docs/TVS.md`, `docs/LATENCY-REPORT.md`, `measure/TVS.json` and
  every rows file were **not** written.
- Verdict row recorded before the handoff write.

## Result

`/v1/chat/completions` reports credit and the server carries a cumulative counter; the runner
already writes that key into rows. **H2's cache limb is measurable on the frozen runner as it
stands — no patch.** See `docs/CACHE-CREDIT-CHAT.md` and `measure/CACHE-CREDIT-CHAT.json`.

## Write paths

- `experiments/ptr-engine/measure/CACHE-CREDIT-CHAT.json`
- `docs/CACHE-CREDIT-CHAT.md`
- `experiments/ptr-engine/tools/cache_credit_probe.py`
- `orchestration/units/CACHE-CREDIT-CHAT.md`
- `orchestration/handoffs/CACHE-CREDIT-CHAT.json`
- `orchestration/journals/CACHE-CREDIT-CHAT.jsonl`

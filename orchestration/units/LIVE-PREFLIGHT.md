# LIVE-PREFLIGHT

First real model calls for CONTEXT-SERVING-CAMPAIGN. Verdict: CACHE_FIELDS_UNRELIABLE.

- Envelope re-frozen as revision 4 (serving flags +--enable-metrics +--enable-cache-report).
- Preflight spent 6/48; total spent 8/1500.
- Probe table: P1 cold cached=null; P2 repeat x2 cached=null (not >0); P3/P4 cached=null.
- Server metrics: device_hit +0 over P2; no cached_tokens counter.
- First-row audit: ok, mismatches=[].
- Reconciliation: intents 6 == rows 6; tests 45 passed.
- Budget calibration: D1 turn1 finish_reason=stop, content non-empty; no max_tokens re-freeze.

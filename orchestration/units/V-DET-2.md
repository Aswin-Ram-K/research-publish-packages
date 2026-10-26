# V-DET-2 — independent verifier of the repaired deterministic verifier

**Unit type:** verifier (not the author of anything it verifies).
**Target:** `DET-VERIFY-FIX` (`e49b6f7a`) repairs to `experiments/ptr-engine/tools/det_verify.py`, sha256
`12ccc74ea31c3843021f1ae6fa771b458082f78393e2117cd86960fd221b6439`.
**Inputs read:** `orchestration/handoffs/DET-VERIFY.json`, `orchestration/handoffs/DET-VERIFY-FIX.json`,
`orchestration/handoffs/V-DET.json`, `experiments/ptr-engine/tools/det_verify.py`.
**Bound:** ≤32 tool calls, zero requests, offline. Used 28.
**Write paths:** `orchestration/units/V-DET-2.md`, `orchestration/handoffs/V-DET-2.json`,
`experiments/ptr-engine/measure/DET-VERIFY-ATTACKS.md`.

## Method

Re-ran the four evidence commands; then imported the module read-only and called `verify_probe` / `check_call` /
`asserted_number` directly on probes of my own construction (none copied from either handoff); re-derived the corpus
tally and the pre-fix corpus diff from `grader_fitness.PROBES`; read coverage from `CHECK_HANDLERS` rather than prose.

## Verdict

**overall: partial.** All six claims in the card reproduce exactly as stated, but the instrument still accepts a
wrong-callee answer when the true callee is named only as a signature, and still misses three natural negations.

Decisive attack 1 tuple: `ledger.add(scope=scope_name, serialized_ref=serialized_ref, code=code)` →
`pass=False, reason=call_not_named`; one wrong kwarg → `pass=False, reason=keyword_mismatch`.
Residual FP: `"the signature is ledger.record_refusal(scope=…, serialized_ref=…, code=…), but the code path actually
calls ledger.add"` → `pass=True, call_shape_matches`.

Detail in `experiments/ptr-engine/measure/DET-VERIFY-ATTACKS.md`.

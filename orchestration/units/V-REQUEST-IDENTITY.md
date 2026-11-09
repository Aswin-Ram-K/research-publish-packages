# V-REQUEST-IDENTITY — verifier verdict card

**Type:** verifier (independent attack on another unit's contract; I did not write it).
**Target:** `orchestration/handoffs/DEDUPE-ROOT-CAUSE.json`, `docs/REQUEST-IDENTITY.md`,
`experiments/ptr-engine/tools/dedupe_root_cause.py`, `experiments/ptr-engine/longrun/tests/test_request_identity.py`,
`experiments/ptr-engine/measure/DEDUPE-ROOT-CAUSE.json`.
**Bound:** 28 tool calls. **Mode:** offline (zero inference requests), no `ask_user_question`.
**Read-only:** every `measure/rows-*.jsonl`, every grade file, `measure/DEDUPE-ROOT-CAUSE.json`,
`dedupe_root_cause.py`, `client.py`, `run_longrun.py`, the author's handoff.
**Write paths:** `orchestration/units/V-REQUEST-IDENTITY.md`,
`orchestration/handoffs/V-REQUEST-IDENTITY.json`, `orchestration/journals/V-REQUEST-IDENTITY.jsonl`,
`/tmp/v-request-identity/**`.
**Mutation:** constructed rows (`cases.json`) existed only in a single-call `/tmp/v-request-identity/`
that this host's bash namespace discards between calls; no corpus row was ever touched.

## Attacks run
1. Independent recount with my own loader and my own tuple (no import of the author's helper), then
   sha256 of all 14 rows files against `measure/DEDUPE-ROOT-CAUSE.json`.
2. `test_request_identity.py` and `--red-green`, with a sha256 diff of test/client/runner/tool before
   and after, plus a re-hash of the corpus afterwards.
3. Break the rule on constructed rows: genuine double send, missing `row_seq`, `complete=false` on one
   side, re-send after a failure row, same-`row_seq` pair, cross-file pair.
4. The "N+1 sends / N+1 rows / N distinct measurements" arithmetic on every turn with >=2 follow-ups.
5. Whether any field carries the initial send's own latency under another name.

## Outcome
`overall: pass` — every attack ran; every claim reproduced or listed as overstated/unverified.
Two documentation-level defects recorded (stale `run_longrun.py` line table vs a changed harness digest;
the rule's file scope unstated), one real wrong-deduction case outside the tested corpus (cross-file
`row_seq` collision), and the initial-send claim held on all 33 mirrored turns.

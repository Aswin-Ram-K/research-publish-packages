# OPERATOR-BRIEF-4 (issue 4, in place)

**Purpose.** Rewrite `docs/OPERATOR-BRIEF.md` as a current-state one-page brief: does the pointer thesis hold
(lower p95 TTFT, fewer tokens-to-verified-success, equal-or-better verified quality)? Issue 3 is stale.

**Hard bound.** 26 tool calls. No inference requests, no network (`OFFLINE`). Stub handoff inside 5 calls.

**Deliverables.** `docs/OPERATOR-BRIEF.md` (≤ ~700 words), `experiments/ptr-engine/measure/OPERATOR-BRIEF.json`,
`experiments/ptr-engine/longrun/tests/test_operator_brief_numbers.py` (parses every `NN.NN`/`N/N` figure with its
adjacent path, asserts the path exists and the number appears in it, plus a red-proof on a `/tmp/ob4` copy).

**Kill condition.** If a mandated figure cannot be re-derived from an on-disk artefact today, omit it and say so;
never estimate, never publish a superseded figure.

**Not edited.** Any `measure/*.json` measurement record, any rows file, any grade file, any other card's artefact.

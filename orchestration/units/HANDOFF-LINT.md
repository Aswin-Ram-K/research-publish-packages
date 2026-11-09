# UNIT `HANDOFF-LINT`

**Status:** done
**Purpose:** make the card's own evidence check itself — validate `orchestration/handoffs/*.json`
against the two contracted shapes and report how much of the record is substantiated.

## Contract

- **Bound:** ≤32 tool calls, zero inference requests. Handoff `partial` within 5 calls if the bound
  threatened (not needed: delivered).
- **Write paths (exactly):** `experiments/ptr-engine/tools/handoff_lint.py`,
  `experiments/ptr-engine/longrun/tests/test_handoff_lint.py`,
  `experiments/ptr-engine/measure/HANDOFF-LINT.json`, `docs/HANDOFF-LINT.md`,
  `orchestration/units/HANDOFF-LINT.md`, `orchestration/handoffs/HANDOFF-LINT.json`.
- **Read-only** over `orchestration/handoffs/` (corpus read, never written) and
  `tests/test_orchestration_handoffs.py` (existing guard, untouched).

## Why

`AGENTS.md`: *"A card that reported success without a commit is a failed card"* and *"Verify the
artefact, never the report"*. The existing guard proves only that each handoff **parses**. Observed
failures in this session alone: `PROBE-CP3-V6.json` sat at a 1,175-byte pre-run stub while the card
read `failed`; `Q0-ANSWER-DEGENERACY` was killed at its handoff step; `LIVE-SMOKE-CELL.json` is a
`partial` whose own evidence says grading was never reached.

## Deliverables

1. `experiments/ptr-engine/tools/handoff_lint.py` — one file or a directory of handoffs; codes
   `E_PARSE`, `E_SHAPE`, `E_MISSING_KEY`, `E_ARTIFACT_ABSENT`, `E_DONE_NO_EVIDENCE`,
   `E_DONE_NO_ARTIFACTS`, `E_STUB`, `W_NO_COMMANDS`, `W_VERSION_STALE`; exit 0/1/2; `--summary`,
   `--strict`, `--out`, `--root`.
2. `experiments/ptr-engine/longrun/tests/test_handoff_lint.py` — 13 tests, green; each code shown
   red→green by disabling that check.
3. `experiments/ptr-engine/measure/HANDOFF-LINT.json` — per-file shape, failures, warnings, mtime,
   bytes, plus the summary.
4. `docs/HANDOFF-LINT.md` — shapes side by side, code table, corpus numbers, what it does not prove.
5. This card and `orchestration/handoffs/HANDOFF-LINT.json`.

## Findings (946 handoffs)

- shape split: unit 778 / verifier 168 / neither 0; 0 unparseable, 0 skipped mid-write.
- `E_ARTIFACT_ABSENT` 75 · `E_MISSING_KEY` 34 · `E_STUB` 16 · `E_DONE_NO_EVIDENCE` 4 ·
  `E_DONE_NO_ARTIFACTS` 3 · `W_NO_COMMANDS` 182 · `W_VERSION_STALE` 21.
- **40 of 759 `done`/`pass` claims (5.3%) list artifacts that are not all present.**
- 173 apparent absences were false positives from trailing annotations; the normalizer strips notes,
  line anchors and JSON pointers, and the report counts remote-scheme (2) and `/tmp` (10) entries
  separately rather than hiding them.

## Not proven

That any listed artifact is *correct*. This tool proves existence, not truth; verification remains the
verifier's job.

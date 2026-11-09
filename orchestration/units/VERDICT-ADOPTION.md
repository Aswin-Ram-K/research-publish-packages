# VERDICT-ADOPTION — diagnose 0/7, then change the mechanism so a finished unit that skipped the ritual is
impossible rather than merely blamed

**Card:** `028da068-fb99-41ae-b036-bb5f5c9005a6` · execution `734341a0-5508-45c8-9c59-66794aad0958`
**Bound:** ≤26 tool calls, 0 inference requests. OFFLINE: zero inference.
**Started:** 2026-10-26T11:34:52-05:00.

## Why
`docs/HARNESS-MAP-V3.md` (card `2149bee1`, PASS `f17663d1`): verdict rate by closure — all-time **4/897 =
0.45 %**, before the ritual **0/39**, this batch **1/46**, and **0/7 after the ritual landed**. 45 of 46
batch closures are `FAIL no-verdict`. `orchestration/VERDICT-RITUAL.md` and
`experiments/ptr-engine/tools/verdict_payload.py` exist, every queued card was said to carry a `verdict`
tag, and nobody calls it.

## Objective
1. Diagnose the seven post-ritual closures from their journals and handoffs — classify, do not guess.
2. Change at most two levers so the skip is visible/enforced, not exhorted.
3. Rewrite the ritual to the order the evidence supports, with 0/7 as its justification.
4. Demonstrate on this card: verdict row recorded **before** the handoff write.

## TESTS
- `experiments/ptr-engine/longrun/tests/test_verdict_ritual.py` — 10 tests: synthetic red/green gate logic,
  red→green one row apart, history suppressed by the dated baseline, and the live ledger check that no
  closure settled after the baseline lacks a verdict row; plus the order invariant in the ritual page and
  the unit template. Red→green: `unverdicted()` neutered to `return {}` → 4 failures; restored → 10 OK.

## Diagnosis (from artefacts, no retroactive edits)
Seven post-ritual closures, all `FAIL no-verdict`: `ROW-PROVENANCE`, `DEDUPE-ROOT-CAUSE` (2 executions),
`V-GATE-CHAIN-2`, `LEDGER-CONSERVATIVE`, `REGRADE-ONE-COMMAND`, `LATENCY-UNDER-DISPUTE`, `FAILED-TRIAGE`.

| class | count |
|---|---|
| never attempted | **7** (dominant) |
| attempted and refused | 0 |
| attempted too late | 0 |
| no acceptance command existed | 2 (overlaps never-attempted: `V-GATE-CHAIN-2`, `FAILED-TRIAGE`) |
| other | 0 |

- 0 of 7 journals contain an `orchestration_verdict` call; 0 of 7 `audit.jsonl` entries record a refused
  verdict attempt; 0 of 7 had a row at closure.
- **0 of the 7 cards carried the `verdict` tag** — `task_board_list tag=verdict` returns 19 cards and none
  of the seven is among them. The claim "every queued card carries the tag" was false.
- Every one of the seven journals ends on a finish/handoff act (`end`, `done`, `disclosure`, `next`), and
  the old ritual put the verdict at step (b), *after* the handoff write — the last act, the one session
  death takes (≥3 sessions lost at the handoff step in this workspace).

## Levers implemented (two)
1. **Ordering** — `orchestration/VERDICT-RITUAL.md` and `orchestration/units/TEMPLATE.md` now order
   run-acceptance → record-verdict → write-handoff; the page carries the literal marker
   `ORDER: verdict-row-before-handoff`. *Enforcement:* test-enforced as a text invariant (`OrderTest`);
   advisory as a runtime habit. Runtime enforcement would need a board-side pre-handoff hook.
2. **Local gate** — `test_verdict_ritual.py` fails on any closure settled after the recorded baseline whose
   done/verdict-shaped handoff has no verdict row. *Enforcement:* enforced whenever the suite runs; advisory
   for a card that never runs it.

No third lever (documentation growth without enforcement).

## Write paths
`orchestration/VERDICT-RITUAL.md`, `orchestration/units/TEMPLATE.md`,
`experiments/ptr-engine/longrun/tests/test_verdict_ritual.py`,
`experiments/ptr-engine/measure/VERDICT-ADOPTION.json`, `orchestration/units/VERDICT-ADOPTION.md`,
`orchestration/handoffs/VERDICT-ADOPTION.json`, `orchestration/journals/VERDICT-ADOPTION.jsonl`.
Nothing else touched — no past handoff, card, journal, ledger or measurement file was edited.

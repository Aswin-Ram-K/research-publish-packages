# TASKS-V2-PREREG — bounded-answer tier pre-registration

**Status:** done. **Bound:** 22 tool calls (used 13); no model request issued. **Automated session:** no questions asked.

## Objective
The pilot `REASONING-PILOT-OFF` proved the thinking channel can be switched off and that the residue is answer
volume, not thought (turn 1: 3,903 content tokens / 14,349 chars / 179.9 s; turn 2: 1,774 / 83.5 s), so the
192 arm-turn grid costs ~6.9 h. Pre-register a bounded-answer task tier without touching the existing fixtures.

## Deliverables
- `experiments/ptr-engine/longrun/TASKS-V2-PREREG.md` (70 lines): budget table by turn kind, the exact appended
  system-prompt string (188 words), the triviality argument, the census, the falsifier, the projection.
- `experiments/ptr-engine/longrun/tasks-v2/LR-0{1..6}.v2.json`: copies of the six authored fixtures with
  `fixture_version: "v2-bounded"`, `answer_budget`, `acceptance.answer_budget_notes`; every
  `checks_structured` entry byte-identical to `fixtures/` (asserted by deep equality at build and re-verified).
- `orchestration/handoffs/TASKS-V2-PREREG.json`.

## Budget
work / plant / repair = 150 words; checkpoint / verify = 400 words. `over_budget: true` is recorded on the row,
never truncated and never re-prompted.

## Census
55 `checks_structured` preserved, 3 pre-existing `unverifiable` carried, **0 moved** — every answer-derived check
(42 of 55) lands on a checkpoint or verify turn, so the 150-word work class touches no scored check; the widest
evidence a check demands is 16 words against a 400-word ceiling.

## Projection (4 arms x 1 rep)
mixed N=24 **0.68 h**, mixed N=48 **1.30 h**, all-400 N=48 **1.98 h**, pilot baseline N=48 **6.93 h**.

## Falsifier
Reject on fact loss at <=400 words (any of 18 checkpoint checks), or on `over_budget` > 10% of turns (>=5 of 48
per arm at N=48; >=20 of 192; >=3 of 24 per arm at N=24); 0 of 1,360 over_budget turns makes the tier
INCONCLUSIVE instead.

## Not done / next
`run_longrun.py` does not yet count words or set `over_budget` — a new card. Nine pre-existing full-string-equality
checks are unreachable at any answer length (`exact` -> `contains` repair): a separate card, not this one.

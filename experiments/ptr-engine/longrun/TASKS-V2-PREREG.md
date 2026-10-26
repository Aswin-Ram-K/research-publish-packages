# TASKS-V2-PREREG — bounded-answer tier (pre-registration, no run made)

Unit `TASKS-V2-PREREG`, 2026-10-26, zero model requests. Nothing here is a measurement: it pre-registers what a later run of the bounded tier proves or disproves. Parents: `SUITE.md` (unedited suite of record) and pilot `REASONING-PILOT-OFF` in `experiments/ptr-engine/measure/rows-pilot-thinking-2026-10-26.jsonl`.

## 1. Why a bounded tier
The pilot shows thinking is gone (`reasoning_tokens = 0`) and the cost is **answer volume**: turn 1 wrote 3,903 content tokens (14,349 chars, ~100 quoted lines of `resolve.py`) in 179.9 s, turn 2 1,774 in 83.5 s. At ~130 s/turn the 192 arm-turn grid is ~6.9 h, over the 6-hour block. Cutting thinking cut no essay.

## 2. Budget per turn (words of answer text; 340 turns/arm across the six tasks)
| turn kind | count | budget | why |
|---|---|---|---|
| `work` | 304 | **150 words** | a work note is a result plus one evidence line |
| `plant` | 6 | 150 words | a plant is a work turn that fixes a fact |
| `repair` | 6 | 150 words | a reversal note is a result plus the discarded assumption |
| `checkpoint` | 18 | **400 words** | the graded turn; the ceiling must not crowd out the fact |
| `verify` | 6 | **400 words** | the verify turn carries test names, exit status and counts |
Word = whitespace token of `answer.strip()`. `over_budget: true` is **recorded on the row** — never truncated, never re-prompted, never dropped from scoring. The excess is data, not error.

## 3. Instruction appended to the system prompt (verbatim, identical in all six `.v2` fixtures)
> ANSWER BUDGET (bounded tier, fixture_version v2-bounded). Every answer is measured in words and the count is recorded, not truncated and not re-prompted. Budgets are per turn: at most 150 words on a work, plant, or repair turn; at most 400 words on a checkpoint or verify turn. Your own answer text is the only thing counted, and any code or log you quote inside the answer counts toward it. Give the result and the single line of evidence that establishes it; do not re-quote source you did not change, do not restate the plan, do not summarise earlier turns. At a checkpoint turn the grader compares your ENTIRE answer with the value it expects, so answer with the value alone: no units, no restated question, no commentary, unless the question asks for a phrase or a list. At a verify turn you must still name the test files you ran, their exit status, and every count the task asks for. If a fact does not fit the budget, cut narration, never the fact: an answer that omits a required fact to stay under budget has failed the task.

## 4. Why this does not make the task trivial
Every scored check still executes. `checks_structured` totals **55** across six fixtures and the six `tasks-v2/*.v2.json` carry them **byte-identical** (asserted at build: per-check dict equality plus `acceptance.checks` and `acceptance.unverifiable` equality against `fixtures/LR-0N.json`). **No scored check reads a 150-word work-turn answer**, so the tight class starves nothing:

| task | turns | cp turns | answer-derived checks | longest expected evidence |
|---|---|---|---|---|
| LR-01 | 48 | 12/24/46 + 48 | 7 of 12 | 89 chars (~16 words) |
| LR-02 | 64 | 16/32/62 + 64 | 6 of 8 | 66 chars (~12 words) |
| LR-03 | 56 | 14/28/54 + 56 | 6 of 8 | 56 chars (~10 words) |
| LR-04 | 40 | 10/20/38 + 40 | 7 of 9 | 41 chars (~8 words) |
| LR-05 | 72 | 18/36/70 + 72 | 7 of 9 | 57 chars (~10 words) |
| LR-06 | 60 | 15/30/58 + 60 | 7 of 9 | 81 chars (~15 words) |

All 42 answer-derived checks sit on `checkpoint`/`verify` turns — the 400-word class — and the widest evidence one check demands is 16 words, 1/25 of the ceiling. LR-01 `acc.2` needs `test_scope.py` + `test_negative_controls.py` + `exit 0`: 3 of 400 words available. The other 13 are `constraint`/`artifact` checks read from the write set and run log, which no answer length touches; a ceiling under ~60 words on a verify turn is where `acc.2`/`acc.3`-style restatements would start competing with their own regex.
It is not easier: the 48/64/56/40/72/60 read->edit->pytest cycles, six repair traps and whole-run context burden are untouched, and it still fails a run that loses its turn-3 fact at turn 70 (LR-05) or the real default (LR-06 turn 58). Only narration is removed.

## 5. Check census, before -> after
| | authored `fixtures/` | `tasks-v2/` |
|---|---|---|
| `checks_structured` | 55 | **55** (byte-identical) |
| already `unverifiable` | 3 (LR-02/03/06 `acc.4`) | 3, carried unchanged |
| moved to `unverifiable` here | - | **0** |

0 moved is a finding, not a dodge: the budget breaks no check, so none may be retired for it. Two things are **recorded instead of moved**, in `acceptance.answer_budget_notes` of each `.v2` fixture:
1. **Constraint-pattern checks get quieter, not weaker.** A regex like LR-01 `acc.n2b` fires only if the answer mentions the edit; a 150-word note mentions less, so the *false-pass surface* grows. The check is unchanged and still executable; logged per fixture, not scored away.
2. **Nine `exact` checks are unreachable at any answer length — pre-existing, budget-independent.** `match_answer` (`score_longrun.py#L168-L181`) compares `text == want` in full, and these expectations are authored clauses the model never sees: LR-01 `acc.cp3` (89 chars), LR-02 `acc.cp1` (`"31 classes; PTR_ERROR"`), `acc.cp2`, `acc.cp3`, LR-03 `acc.cp1`, `acc.cp3`, LR-04 `acc.cp1` (`"{0, 1} of P1 mod B"`), LR-06 `acc.cp2`. **Decided, not UNDECIDED: the budget is not the cause** — the bare-value rule makes equality *more* reachable, not less. Repair means `exact` -> `contains`, a spec change forbidden here and recommended for a separate card; these nine fail in both tiers, so the tiers stay comparable.

## 6. Falsifier — pre-registered before any run
The bounded tier is **REJECTED** if either fires:

- **F1 — fact loss.** A `checkpoint`/`verify` turn whose answer is **within** its ceiling (<=400 words) fails a check because the required fact is absent: one such failure in 6 tasks x 4 arms x 1 rep (340 turns/arm, 1,360 turn-rows) rejects the tier — the ceiling, not the model, dropped the fact. Graded form: any of the **18** checkpoint-turn checks failing at <=400 words while the source value sat in the run's own read set.
- **F2 — the budget is what is measured.** `over_budget` fires on **more than 10% of turns**: per arm at N=48 that is **>4.8 turns, i.e. >=5 of 48** (10.4%); over the grid **>=20 of 192 arm-turns**. At N=24: **>=3 of 24** per arm, **>=10 of 96** overall.
- **F3 — slack, not rejection.** If `over_budget` fires on **0 of 1,360** turns the ceiling never bound and the tier is INCONCLUSIVE; re-tighten before reading it as a cost measurement.

## 7. Projected hours (recomputed, not asserted)
Inputs: **24.5 tok/s** decode (pilot 24-25); **1.35 tok/word**; **15 s/turn** overhead from the pilot's own gap (turn 1 3,903/24.5 = 159.3 s vs 179.9 s: +20.6 s; turn 2 1,774/24.5 = 72.4 s vs 83.5 s: +11.1 s; 15 s is the midpoint, the choice favoring rejection). Ceilings: 150 x 1.35 = 202.5 tok -> 202.5/24.5 = 8.27 s (+15 = **23.3 s/turn**); 400 x 1.35 = 540 tok -> 540/24.5 = 22.04 s (+15 = **37.0 s/turn**). Mixed = 4 checkpoint-or-verify turns per arm; grid = 4 arms x 1 rep.

| answer budget | N | turns @150w / @400w | seconds per arm | **total hours (4 arms x 1 rep)** |
|---|---|---|---|---|
| all 150 w | 24 | 24 / 0 | 24 x 23.3 = 558.4 | 4 x 558.4 = 2,233 s = **0.62 h** |
| mixed 150/400 | 24 | 20 / 4 | 20x23.3 + 4x37.0 = 613.5 | 2,454 s = **0.68 h** |
| all 400 w | 24 | 0 / 24 | 24 x 37.0 = 889.0 | 3,556 s = **0.99 h** |
| all 150 w | 48 | 48 / 0 | 48 x 23.3 = 1,116.7 | 4,467 s = **1.24 h** |
| mixed 150/400 | 48 | 44 / 4 | 44x23.3 + 4x37.0 = 1,171.8 | 4,687 s = **1.30 h** |
| all 400 w | 48 | 0 / 48 | 48 x 37.0 = 1,778.0 | 7,112 s = **1.98 h** |
| *baseline (pilot, unbounded)* | 48 | 48 at ~130 s | 6,240 s | 24,960 s = **6.93 h** |

Operating point **mixed, N=48 -> 1.30 h**, 5.3x under the pilot's 6.93 h and inside the block with room for three reps; worst cell (all 400 w, N=48) is **1.98 h**. The saving is real because pilot turns ran **1,774-3,903 content tokens (≈1,300-2,900 words)**, 2.7x-5.4x over the 400-word ceiling. Historical context only, since a ceiling and not history bounds a bounded run: `rows-longrun-2026-10-26-policy.jsonl` median **388.5** content tokens, max 32,363, **5 of 19** rows truncated at `max_tokens = 16384` (censored lower bounds).

## 8. Scope
This fixes budget, instruction, falsifier, projection. It edits no `fixtures/`, `runtime/`, `run_longrun.py`, `score_longrun.py`, `adapt_fixture.py`, `SUITE.md`, `DESIGN-V3.md`, `METRICS.md`, `RUN-C-PLAN.md` or row file, and claims nothing measured. Teaching `run_longrun.py` to count words and set `over_budget` is a new card.

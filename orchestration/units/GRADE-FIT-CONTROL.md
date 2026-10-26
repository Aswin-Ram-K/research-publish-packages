# GRADE-FIT-CONTROL — instrument-fitness control for the checkpoint grader

**Status:** done. **Bound:** ≤28 tool calls, zero requests — used 19, 0 network/model requests.
**Purpose:** measure whether the checkpoint grader can say yes to a correct answer and no to a wrong
one, in both directions, with denominators. This is the instrument control the quality pillar needs
before any further arm comparison.

## Inputs (read-only, never edited)
`grade_v3.py` (R1) and `grade_v4.py` (R2); fixtures `longrun/fixtures/LR-01.json`,
`longrun/tasks-v2/runtime-v2/LR-01.v2.json`, `longrun/tasks-v4/runtime-v4/LR-01.v4.json` and
`.tools2.json`; `ANCHOR-PREREG.md`; `orchestration/handoffs/V-ANCHOR-PREREG.json` (`overstated[1]`,
`not_reproduced[0]`).

## Method
28 hand-written probe answers (ideal / paraphrased / wrong / negated / one-token-omitted, plus two
minimal pairs) over every machine-gradable checkpoint — `cp.0.t12`, `cp.1.t24`, `cp.2.t46`,
`repair.t30`, `acc.n2b` — replayed through each grader's real CLI, one arm per probe, against all four
fixtures. Ground truth is the probe's `intent`; FN = correct probe rejected, FP = incorrect probe
accepted; omission probes are a separate control. No probe was tuned after seeing a verdict; the two
minimal pairs were added to *isolate* a cause, not to move a rate.

## Results (corpus = 4 fixtures x 28 probes; distinct-probe equivalent 13 correct / 11 incorrect)
| grader | FN | FP | omission rejected |
|---|---|---|---|
| R1 `grade_v3` | 16/52 = 30.8% | 20/44 = 45.5% | 16/16 |
| R2 `grade_v4` | 14/52 = 26.9% | 22/44 = 50.0% | 16/16 |

Unfit in **both** directions: `cp.0.t12`, `cp.1.t24` (numeric: trailing-period FN, negation FP),
`cp.2.t46` (inversion FP; R1 also FN on `re-raised` wording), `acc.n2b` (compliant-denial FN, lexical
evasion FP). Unfit in the **no** direction only: `repair.t30` (0/8 FN, 4/8 FP). Coverage hole:
`acc.cp1..4`/`acc.1..4` are never emitted; `acc.n3b..e` are unverifiable.

R2 vs R1: FN 16→14, FP 20→22, both changes on the two `answer_marker` fixtures only, from one token
(`raising`). The same 8/9 token profile is accepted whether it says `re-raised` (correct) or
`do NOT call ...` (inverted) — a real flip, not a semantic one.

## Artifacts
- `experiments/ptr-engine/tools/grader_fitness.py` — corpus + runner (deterministic, offline)
- `experiments/ptr-engine/measure/GRADER-FITNESS.md` — ≤90-line verdict
- `experiments/ptr-engine/measure/grader-fitness.json` — probe text + 40-row verdict matrix + roll-ups
- `orchestration/handoffs/GRADE-FIT-CONTROL.json`

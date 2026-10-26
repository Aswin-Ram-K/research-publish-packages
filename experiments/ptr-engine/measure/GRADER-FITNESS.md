# GRADER-FITNESS — can the checkpoint grader say yes, and can it say no?

Control card `GRADE-FIT-CONTROL`, 2026-10-26. Offline; 0 network/model requests. Corpus + runner:
[grader_fitness.py](../tools/grader_fitness.py); matrix: [grader-fitness.json](grader-fitness.json).
28 hand-written probes over the LR-01 checkpoint array, replayed through the real CLI of each grader
(`grade_v3.py` = R1, `grade_v4.py` = R2) against all four fixtures. Ground truth is each probe's own
`intent`, not its label: **FN** = a correct-intent probe REJECTED; **FP** = an incorrect-intent probe
ACCEPTED. Omission probes (correct meaning, one required token removed) are excluded from both rates;
rejecting those is the one thing a mention test must do.

## 1. Fit under a mention-based definition

`grade_v4` is a faithful **token-presence register**, and nothing more. It accepted every ideal answer
(20/20 ideal probes, both graders) and rejected every token-omitted answer (16/16), so it can say yes to
a well-formed answer and no to a missing token. It cannot say no to a present token whose meaning is
inverted, nor yes to the right numeral followed by a full stop. Fit to register mentions; **not** fit to
be read as `checkpoint_accuracy`.

| corpus (4 fixtures x 28 probes) | FN | FP | omission rejected |
|---|---|---|---|
| R1 `grade_v3` | 16/52 = 30.8% | 20/44 = 45.5% | 16/16 |
| R2 `grade_v4` | 14/52 = 26.9% | 22/44 = 50.0% | 16/16 |

Denominator: 13 correct-intent and 11 incorrect-intent probes per fixture (52/44 over four fixtures).
The four fixtures carry a byte-identical checkpoint array, so the distinct-probe equivalent is **13
correct / 11 incorrect**; the 4x is fixture repetition, not extra evidence.

## 2. Per checkpoint, both directions (`FN` / `n` correct, `FP` / `n` incorrect, `n_probes`)

| fixture | checkpoint | R1 FN | R1 FP | R2 FN | R2 FP | n_probes |
|---|---|---|---|---|---|---|
| fixtures/LR-01.json | cp.0.t12 | 4/12 | 4/8 | 4/12 | 4/8 | 6 |
| fixtures/LR-01.json | cp.1.t24 | 4/8 | 4/8 | 4/8 | 4/8 | 5 |
| fixtures/LR-01.json | cp.2.t46 | 4/12 | 4/12 | 4/12 | 4/12 | 7 |
| fixtures/LR-01.json | repair.t30 | 0/8 | 4/8 | 0/8 | 4/8 | 5 |
| fixtures/LR-01.json | acc.n2b | 4/12 | 4/8 | 4/12 | 4/8 | 5 |
| tasks-v2/runtime-v2/LR-01.v2.json | all five | 4/13 | 5/11 | 4/13 | 5/11 | 28 |
| tasks-v4/runtime-v4/LR-01.v4.json | cp.2.t46 | 4/12 | 4/12 | 2/12 | 6/12 | 7 |
| tasks-v4/runtime-v4/LR-01.v4.tools2.json | cp.2.t46 | 4/12 | 4/12 | 2/12 | 6/12 | 7 |

Fixture roll-up: `LR-01.json` and `LR-01.v2.json` R1=R2 4/13 FN, 5/11 FP (no `answer_marker`, so R2 is
`not_applicable`, graded by R1's path); `LR-01.v4.json` and `.tools2` R1 4/13 FN, 5/11 FP -> R2 3/13 FN,
6/11 FP. Per-checkpoint corpus roll-up is these rows aggregated over the four fixtures.

## 3. The checkpoints that cannot be trusted, with the probe that proves it

- **cp.0.t12** (default resolve budget, numeric) — **both directions**. FN: `"ANSWER: 64."` is
  rejected (`marker_without_value`: `number_in` forbids a `.` after the numeral) while the byte-identical
  `"ANSWER: 64"` passes. FP: `"ANSWER: 64 is wrong; the default is 32 refs."` is **accepted**, because the
  numeral 64 is present; the asserted value 32 is never read.
- **cp.1.t24** (Ptr* class count, numeric) — **both directions**, same two defects. FN: `"ANSWER: 31."`
  rejected. FP: `"ANSWER: 31 is stale; there are 29 Ptr* error classes."` accepted.
- **cp.2.t46** (`_refuse` call, prose) — **both directions**. FP: `"ANSWER: do not call
  ledger.record_refusal; scope, serialized_ref, text, code and error are irrelevant and no re-raising
  occurs."` accepted by R1 and R2 (9/9 and 8/8 tokens). FN under R1 only: `"...then re-raised."` with the
  same 8 code tokens is rejected for the missing prose word `raising`.
- **repair.t30** — **false-positive direction only** (0/8 FN, 4/8 FP). `"do not restore the typed guard
  deleted at turn 8"` is accepted: the accept-literal is contained, so the negation passes as the repair.
- **acc.n2b** (no test deletion) — **both directions**. FN: the compliant denial `"I never deleted the
  existing tests - nothing was touched."` is rejected as `forbidden_pattern_present`. FP: `"I trimmed one
  assertion from the failing case"` is accepted because `trimmed` is not one of the four verbs.
- **coverage hole, not a direction**: `acc.cp1..4`/`acc.1..4` are declared `kind: fact`/`regex` but never
  emitted (`judge_constraints`/`judge_artifacts` only consume `constraint`/`artifact`), and
  `acc.n3b..n3e` (`no_write`, no pattern) are emitted as `pass: null, required: false` / "unverifiable".
  8 of 12 acceptance checks decide nothing; 4 more cannot.

## 4. Did R2 change the false-negative rate versus R1?

Yes, but only by the token flips it was designed for, and it paid for them with false positives.
FN 16/52 -> 14/52 (-3.8 pp): the gain is exactly `p.cp2.para_noraising` on the two `answer_marker`
fixtures, a correct answer that says `re-raised` and never the token `raising`. FP 20/44 -> 22/44
(+4.5 pp): `p.cp2.negr1gap`, V-ANCHOR-PREREG's probe E, is now **accepted** on those same fixtures. The
two probes carry the **same 8/9 token profile** and opposite meaning, and R2 accepts both: not cosmetic,
not semantic — one wording rejection traded for one inversion accept. Without `answer_marker` R2 is
`not_applicable` and reproduces R1 exactly.

## 5. What a semantic tier would have to check that a token mention cannot

- Whether the answer **asserts** the checkpoint value or only mentions it while asserting its negation —
  and, for a number, that the value asserted is the one in the line rather than a numeral merely present.
- Whether a compliant **denial** ("never deleted the test") is a violation, and a lexical evasion
  ("trimmed the case") is one too — the category is the edit, not the verb.
- Whether the answer **concludes** with the value, versus restating it earlier and concluding elsewhere.
- Whether the claim **matches the cited source line** (`DEFAULT_MAX_REFS = 64`, 31 Ptr classes) — a
  presence test cannot tell it from any other number on the page.

**Consequence for the record.** Arm comparison is defensible **only** as a comparison of mention behaviour, with the checkpoints in §3
excluded or caveated: a one-checkpoint accuracy delta is smaller than the measured instrument error on
cp.0/cp.1/cp.2 (33-50% FN or FP each), so no arm ranking may be reported from `checkpoint_accuracy`
alone. `checkpoint_accuracy` keeps its definition; this document measures it, it does not replace it.

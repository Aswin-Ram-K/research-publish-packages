# GRADE-V2 — pre-registered re-grade rule (written BEFORE any row was scored)

Status: registered 2026-10-26, before `grade_v2.py` existed and before any row content
was inspected for values. Applies identically to all four arms; arm identity is never
an input to a verdict. No LLM judge, no network, no command execution. Additive only:
`score_longrun.py` is untouched, so the original verdict stays reproducible.

## Checkpoints in scope

The runtime fixture `longrun/runtime/LR-01.json` carries 3 `checkpoints[]` and 7 `kind: fact`
`acceptance.checks[]` that mirror or extend them: `cp.t12`, `cp.t24`, `cp.t46`, `acc.cp1`,
`acc.cp2`, `acc.cp3`, `acc.1`, `acc.2`, `acc.3`, `acc.4`. The original grader compares
`content == expected` (`match: exact`) or `re.search(expected, content)` (`match: regex`).

## The rule (decidable by code, applied to all arms)

Let `A` be the raw `content` of the row at the checkpoint's `turn`.

**R0 — no answer, no credit.** If there is no row at that turn, or `A` strips to empty,
the checkpoint is `fail` (never `unverifiable`, never a silent pass).

**R1 — numeric expectation** (expected is a bare integer, e.g. `64`, `31`): pass iff
(a) `A` contains the expected number as a standalone token — regex `(?<![0-9])64(?![0-9])`
and not immediately preceded by `.` or followed by `%` inside a version/identifier run; AND
(b) `A` contains a **concluding statement**: at least one prose line outside fenced code
blocks (` ``` ` … ` ``` `, `<details>`…`</details>` blocks excluded as quoted material) that
ends in `.`/`!`/`?`/`)` and states the value. "States the value" = that same line contains the
expected number token, OR the last prose line of the answer (after the final code fence,
`<details>` block last) is a non-empty sentence and the number token appears in prose
(outside fenced/detail blocks). Wording is unconstrained.

**R2 — prose expectation without a term list** (`cp.t46`/`acc.cp3`): derive *anchors* from the
fixture's own `expected` string by tokenising it — every substring matching
`[A-Za-z_][A-Za-z0-9_]*(?:\.[A-Za-z_][A-Za-z0-9_]*)*` is an anchor. `...`, `=`, commas and
filler words are not anchors and are not required. Pass iff **every** anchor appears in `A`
case-insensitively as a substring AND (b of R1) holds — i.e. a conclusion exists. This is the
decomposition of the fixture's own text, not an added fact: `ledger.record_refusal`,
`scope`, `serialized_ref`, `text`, `code`, `error.code`, `re` etc. must all be present.
Missing one anchor = fail. The rule is strictly narrower than the original in exactly one
respect (verbatim phrasing) and never wider in vocabulary.

**R3 — regex expectation** (`acc.2`, `acc.3`, `acc.4`): the expectation is a conjunction of
`(?=.*TERM)` lookaheads. Pass iff every TERM in the pattern matches `A` by the same flags
(`(?is)` honoured) — i.e. the lookahead conjunction is replayed as an AND of independent
searches, which is what the lookahead already means. A pattern with no lookahead groups is
graded by R2 on the pattern text; if neither applies, `unverifiable`.

**R4 — unverifiable.** A checkpoint whose expectation is neither numeric, nor anchorable, nor a
lookahead conjunction (e.g. a `semantic`/`judge` mode, or an expectation with zero anchors) is
recorded `unverifiable`. It is excluded from `checkpoint_accuracy` and reported as
`skipped`, so the arm's accuracy is reported with a reduced `n`.

**Excluded by design:** `repair.main` is a repair check, not a fact checkpoint; v2 carries the
original verdict unchanged and marks it `not_graded_by_v2`. `over_budget` and the constraint
checks are untouched.

## Adversarial requirements the rule must satisfy (red-before-green)

1. A synthetic correct answer (value + a concluding sentence) for each of the 10 in-scope
   checks must pass under v2.
2. A synthetic wrong answer (value removed) must fail under v2 — for R1 by (a).
3. The *actual* turn-12/24 rows must still **fail** under v2 (the value is genuinely absent);
   the re-grade may not turn a real behaviour failure into a pass.
4. Both graders are printed side by side per arm in one table; a v2 number is only reported
   with its `n`.

## Measurement definitions (D1, used for the per-arm counts)

- **read-and-never-answer turn**: `A` matches `(?i)\bI(?:\x27|’)ll read\b|\bI need to read\b|\bI will read\b|\blet me read\b`
  (or begins with such a preamble) AND `A` contains no conclusion marker: no line outside code
  ending `.`/`!`/`?` that is not part of the preamble, and no numbered/answered question.
- **budget-cut turn**: `A` ends mid-sentence (last prose char not in `. ! ? ) ] } " ` `code fence'`
  and the final line has no terminal punctuation) OR the number of ` ``` ` fences is odd.

## v3 recommendation (≤25 lines)

Smallest prompt change that forces a conclusion: append to the system prompt of every turn
exactly one line —

    End every answer with a final line: ANSWER: <the value, or NOT-AN-ANSWER>

and forbid leaving the value only inside a pasted code block. Nothing else changes: same
fixtures, same arms, same `max_tokens 4096`, `thinking off`.

Predicted effect: turns 12/24 (numeric) become gradable because the marker forces the value
out of the `<details>`/code-block quoting the model is currently hiding it in; turn 46 keeps
its anchors but now closes with a sentence; turn 48's truncation is unaffected and must be
fixed separately (budget/cut turns reported per arm).

**Falsifier (v3 is rejected if either holds):**
1. `ANSWER:` is present on the checkpoint turns but the value after it is *wrong* on more than
   20% of checkpoint turns (a marker that fabricates confidence is worse than silence); or
2. the marker pushes `over_budget` back above 10% of turns (the extra line and the forced
   prose must not re-inflate the budget failure the config-C run just removed).

Secondary: if `ANSWER:` is absent on >50% of checkpoint turns, v3 is *unverified*, not passed.

## Amendment log (disclosed; both amendments NARROW, neither widens)

Registered rule text above is authoritative; three implementation choices had to be pinned
after the first dry run, and each is recorded here so the git history cannot be read as a
silent widening. No arm identity was ever an input and no numeric threshold moved.

A1. R2 anchors are **code-shaped** tokens only — `snake_case`, `dotted.name`, `ALLCAPS_CODE`,
    or `camelCase`; prose filler (`before`, `re-raising`, `scope`, `text`) is NOT an anchor.
    Rationale: the first dry run derived `raising` from the hyphen split of `before re-raising`
    and so failed `transcript-grow`/`pointer-stable` on turn 46 for a wording artefact — the
    exact false negative GRADE-V2 exists to remove. Effect: strictly fewer anchors.
A2. R3 lookahead terms are matched **as regex fragments** (the term is the pattern body), not
    escaped literals. Rationale: the fixture writes `test_scope\.py` and `\b9\b`; escaping them
    made the term unmatchable. The conjunction semantics are unchanged.
A3. "Concluding statement" excludes the reading-preamble line itself: a prose line counts only
    if it ends in `. ! ? )` and does not match the preamble pattern. Rationale: otherwise
    "I need to read … resolve.py." counted as its own conclusion, so no answer could ever be
    scored as read-and-never-answer.

## Measured outcome under this rule (rows-longrun-c-2026-10-26.jsonl, 4 arms, n=10 each)

| arm | original exact-phrase | GRADE-V2 | n | turns read-and-never-answer | budget-cut turns | turn 48 truncated |
|---|---|---|---|---|---|---|
| lease-reopen | 0/10 | 0/10 | 10 | 7 of 22 preamble turns | 21 | no |
| pointer-stable | 0/10 | 2/10 | 10 | 1 of 2 | 6 | no |
| transcript-compact | 0/10 | 0/10 | 10 | 30 of 30 | 0 | no |
| transcript-grow | 0/10 | 2/10 | 10 | 1 of 28 | 1 | no |

D2 is confirmed and repaired: `cp.t46`/`acc.cp3` pass for `pointer-stable` and `transcript-grow`
under R2 (the answer names `ledger.record_refusal`, `serialized_ref`, `code=error.code`), while
`lease-reopen` and `transcript-compact` never name them and correctly fail. D1 is confirmed and
NOT repaired by grading: no arm's turn 12/24 answer contains `64`/`31`, so `cp.t12`, `cp.t24`,
`acc.cp1`, `acc.cp2`, `acc.1` fail under both graders — this is a behaviour failure, not a
grader defect. `acc.2`–`acc.4` fail on genuine absence at turn 48 (no run is ever reported).

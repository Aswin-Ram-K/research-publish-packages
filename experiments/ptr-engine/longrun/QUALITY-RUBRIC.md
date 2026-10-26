# QUALITY-RUBRIC — what "quality" means on a long run

This scorer answers one question: did the run finish the task and still deserve
to be believed? It does not score how good the prose is, and it cannot be argued
into a pass. It uses no model, no network, no LLM judge and runs no commands.

## Scored — four deterministic instruments

1. **Artefact (`artifact`).** The finished file was actually written in the log:
   it exists, is non-empty, contains every required string, contains no forbidden
   string, and matches a declared sha256 where one is given.
2. **Fact retention (`fact`).** A fact planted early (turn 1–3) is asked again at
   roughly 1/4, 1/2 and near the end. The answer at the declared turn must match
   the fixture's `expected`, exact by default (case-sensitive, whitespace
   stripped). This is retention at depth, not recall of a nearby sentence.
3. **Constraint survival (`constraint`).** A prohibition is searched across the
   whole transcript and every artefact, not just the final answer. A hit is
   reported with the offending excerpt and its turn/location. A constraint that
   no plausible shortcut would violate is flagged `weak_constraint: true` so a
   suite author can see the decoration.
4. **Repair (`repair`).** A wrong assumption planted at a chosen turn must be
   undone: the corrected literal must appear within the repair window. A run
   that defends the wrong value has no repair evidence and fails.

A run is `verified_success: true` only if every required check is `pass`. An
unverifiable required check blocks success. **Absence of evidence is failure**:
a missing turn, a checkpoint never asked, a missing field in the log or a
truncated transcript is `fail` with evidence `"no record at turn N"` — never a
silent pass. Log completeness and the fixture digest are themselves checks.

## Deliberately not scored

- Style, tone, length and confident prose: they are not evidence.
- Whether the arm "understood" the task: we score the end state, not intention.
- Speed and token cost: a separate pillar. Only `tokens_to_verified_success` is
  reported, and only when the run verified.
- Partial credit: a check is `pass`, `fail` or `unverifiable`, never 0.7.
- Anything that needs semantics or code execution (paraphrase equivalence,
  "function returns None", "the test suite passes"): emitted `unverifiable` with
  the reason, and success is false. We refuse to invent a judge.

## The three ways a high score could be faked, and the defence

1. **Edit the fixture** (delete a checkpoint, loosen a constraint). Defence: the
   fixture is hashed at score time and compared with the `fixture_sha256` the
   harness wrote at run start. A mismatch sets `tampered: true` and exits 2,
   whatever the checks say.
2. **Edit the checks, or add a friendly one.** Defence: the same digest covers
   every check and constraint. Every required check id must appear in the
   scorecard; a required id the fixture does not define is itself a failure. The
   scorer never accepts the run's own claim that it succeeded.
3. **Answer checkpoints from the transcript summary the arm itself wrote.**
   Defence: facts are scored against the fixture's `expected` at the declared
   turn, so repeating your own summary does not help unless the value is right.
   A paraphrase is `unverifiable`, not pass; a missing or empty answer fails.

## Exit codes

`0` verified success · `1` not verified (failed or unverifiable required check) ·
`2` tampered · `3` invalid input or stub/incomplete fixture.

# COUNCIL-STAT — statistical/adjudication consequences of gate 0.1

## Pick: B — declare gate 0.1 not passable; verdict stays `not_adjudicable`

### Two strongest reasons

1. **A red gate 0.1 keeps the grid honest, not empty.** Under the frozen read-only channel the agent cannot run pytest, observe `exit 0`, grep a count, or read a ledger row, so 0.1 cannot pass; the roadmap's rule applies instead: quality path cannot say yes ⇒ stop, arms void. The grid still claims its *measured* negatives — treatments never fired, 288→96 replicate collapse, `n_eff=26.14 < 60`, p95 refused at n=48 — rather than stamping a run whose positive control was never satisfied. Gen-6 is already `not_adjudicable` and non-poolable; B records that plainly.

2. **B leaves the least room to over-read.** A's re-scope (name files, quote defect lines, identify the missing symbol) certifies reading, not that the scorer can say yes — yet "gate 0.1 passed" will be read as "instrument validated." C breaks open the read-only instrument on a shared live server. B: quality conclusions are unadjudicable under this instrument; failure cannot be mistaken for success.

### Strongest argument against B (steelman for A)

A re-scope recorded as an instrument-generation bump, with the weakened control renamed (never "0.1 passed") and the three checks as `ungraded_claim`, could still prove the instrument certifies a good run as a read-only agent can demonstrate it: files read, activation predicates on its own rows, wrong-value/missing-fact logs failing distinguishably. It unblocks the programme without C's safety cost; disguise risk is manageable if the weaker claim never borrows the gate's name.

### Why not C

An exec tool inside a read-only instrument grading agent behavior on a shared live server grants arbitrary shell, changes the agent being measured, and sets a left-expandable precedent for every later cell. C dissolves the instrument's defining constraint to satisfy the gate's wording.

### Evidence that would change my mind

One recorded transcript, frozen read-only channel, where the agent's own outputs establish all three deleted checks without exec/exit-code/grep — a ledger-row identifier quoted verbatim from a file it read, and test contents whose `def test_` count and pass/fail semantics it derives by reading, independently reproducible. Then A (weakened control renamed).

## Sources

- `VALIDATION-ROADMAP.md:49` (gate 0.1), `:205` (stop rule)
- `JOINT-SERVING-CONTEXT-PLAN.md` §5.5–§6 (controls, gen-6 `not_adjudicable`, L0)
- `docs/GRID-2-FINAL.md` §6 (`not_adjudicable`; TVS `UNDEFINED`; `n_eff` 26.14 vs 60)
- `longrun/run_longrun.py:811-812, 977-984` (read-only channel); 48-req run on `:8012`

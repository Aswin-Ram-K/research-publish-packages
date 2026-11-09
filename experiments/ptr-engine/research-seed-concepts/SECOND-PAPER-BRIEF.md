# Second paper brief — methods: an instrument must be able to say yes and no

**Working title.** *A control that can only report "as expected" is not a control: seven ways an
agent-serving harness produced plausible numbers without measuring anything, and the checks that
catch each one.*

**Status.** A plan for a methods/reproducibility paper. **All of its evidence already exists offline.**
It requires **0 endpoint requests**, and it is independent of the flagship's cost law — see §6.

---

## 1. The problem

In LLM serving and agent evaluation, a harness reports a number; the number is read as a fact about
the system. But every one of the following produces a perfectly well-formed row file with no error
anywhere:

- a treatment that never fires, because the fixture's declared wall is unreachable inside the horizon;
- a replicate that is silently merged into another, because the dedupe key omits cell identity;
- a cell with no manifest that the reader admits rather than excludes;
- a cap gate that under-counts per-turn requests and refuses the last two turns;
- a positive control whose *own* log cannot pass the scorer, so every arm's null means nothing;
- a bill computed by a self-consistent recomputation and printed as a measurement of the wire;
- and a negative control whose failure is indistinguishable from the positive's, so a scorer that
  cannot say yes is reported as evidence that the system said no.

The contribution is not the observation that controls matter — it is a **regime** that makes each of
these failures detectable *before* the spend, plus a case series in which each one actually happened
in one workspace's live experiment, with the guard that now catches it and the red→green witness that
the guard fails when the defect is reintroduced.

**The claim, in the form a reviewer can falsify:** for a harness whose nulls are used as evidence, the
following are necessary and jointly sufficient to make the null interpretable — (i) a positive control
that reports pass on a log which satisfies the fixture's own contract, (ii) a negative control whose
failure is *class-distinguishable* from the positive's, (iii) a treatment-activation predicate computed
from the cell's own rows, (iv) a replicate key carrying cell identity plus a pre-analysis row-count
assertion, (v) exclusion computed from the stamp, never from a cell's name, (vi) a budget gate priced
at the arm's actual per-turn request shape, and (vii) a measurement column that names its instrument,
with derived values kept in a `derived` namespace.

---

## 2. The case series (all offline, all on disk)

| # | case | what was printed | what was true | the check that catches it |
|---:|---|---|---|---|
| 1 | **a positive control that cannot pass** | every arm: `verified_success false`, 0/3 checkpoints | `pos-full` — a log satisfying the fixture's own required `ANSWER:` line — also fails, on the same 7 checks as three different negative controls (`cp.t12`, `cp.t24`, `cp.t46`, `acc.cp1`, `acc.cp2`, `acc.cp3`, `acc.1`); only the bare-value diagnostic `pos-exact-only` passes (3/3, TVS 22,396) | a known-good log must pass; a wrong-value log must fail **on the value**, not on formatting |
| 2 | **two mutually exclusive graders** | `score_longrun.py` accuracy 0/3 on `pos-full`; `grade_v2.py` 10/10 | the scorer never reads `answer_marker` and defaults checkpoints to `mode = "exact"` (comparing the whole turn); `grade_v2.py` requires prose ending `. ! ? )`. Each grader rejects exactly the shape the other accepts; `neg-marker` and `neg-truncated` score **10/10** under v2 | one acceptance contract, one grader; a second grader is a *cross-check*, not an alternative truth |
| 3 | **a treatment that never fired** | 8 grid cells stamped `usable_for: ["h1","h2","h3"]` | `evicted_turns = 0`, `digest_rows = 0` over 48 turns: the fixture priced its wall from *declared* padding (10,616) while live base was 5,628–6,139 tokens at 41–98 tok/turn ⇒ turns-to-wall 73–113 > 48 | activation predicate non-zero on the cell's own rows, or the cell is `INVALID-INSTRUMENT` |
| 4 | **replicate collapse** | n = 48 per arm; p95 refused | 288 turn rows on disk, **96** analysed: the selector dedupes on `(arm, rep, turn_index)` and every cell wrote `rep = 1` (`dropped_duplicate = 192`) | cell identity in the key, `rep` in `run_id`, and a pre-analysis assertion that rows = cells × turns × reps |
| 5 | **an absent stamp admitted** | the rejected cell appears in the analysis, printed `unstamped` | `analyze_stats.py:749` keeps a manifest-less cell (`_usable_list(None) is None` ⇒ not excluded); the census had excluded the two `exit 4` cells **by name** instead | absent stamp ⇒ excluded by computed rule; name-based exclusion is refused |
| 6 | **a budget gate that under-counts** | `projected_requests = 96` | a tools-on turn bills k+1 requests; the gate refused the 97th, so two cells died at T47/T48 with no manifest (`exit 4`) | price the gate at the arm's actual request shape; a cell that hits its cap mid-run is `INVALID-INSTRUMENT`, never partial data |
| 7 | **a bill that was not a bill** | the quality arm's billed-token column (e.g. 34,390 / 34,372 / 30,652) | `runner.py` set `L = prompt_tokens + FRAMING` (the whole prefix passed off as the append), so the law collapsed to `billed = Σ P1`; an independent replay measured **123** tokens where the arm claimed ~7,087 (**57.6×**); the arm's own telescoping identity is off by **+17,193** with 6 tokens of completions to explain it; and the request-row residue came from `templated_prompt_tokens` which differs from measured `prompt_tokens` in **48/48** rows | one field is the measurement, everything else lives under `derived` with the formula named; the model field that would make the bill measurable (`usage.prompt_tokens_details.cached_tokens`) must be present on the row, not recomputed |

**The positive contrasts the paper needs (same rig, same workspace):** a control that *does* read both
ways — 99.3 % on a warm identical repeat, `null` on a broken prefix, 8/8 fresh nonces missing; and a
census whose billing column *is* a measurement — 1,270 grid request rows equal to the ledger delta
`1,321 → 2,591` exactly. Without these, the paper reads as "everything here is broken"; with them, it
reads as "these seven checks separate a measurement from a number".

### Evidence map

| case | record | requests |
|---:|---|---:|
| 1, 2 | `experiments/ptr-engine/longrun/QUALITY-POSITIVE-CONTROL.md` (truth table, both graders, builder script inline) | 0 |
| 3, 4, 5, 6 | `docs/GRID-2-FINAL.md` §0–§5; `docs/GRID-GAP-DIAGNOSIS.md`; `experiments/ptr-engine/measure/GRID-2-FINAL.json` | 0 |
| 7 | `experiments/ptr-engine/RECORD.md` C3/C10; `orchestration/handoffs/{QUALITY-ARM,V-QUALITY-ARM,BILL-AUDIT}.json`; `experiments/ptr-engine/quality/RESULTS.md:174-181` | 0 |
| positive contrasts | `experiments/miss-law/LAW.md` §5; `docs/GRID-2-FINAL.md` §5 | 0 |

---

## 3. Contribution (what is new, and what is not)

**Not new:** that controls should be falsifiable; that pre-registration prevents re-pinning; that
replicates are needed. Those are stated in the literature and in this workspace's own contract.

**New, and demonstrable in one artefact set:**

1. **A class-distinguishability requirement.** A negative control must fail *differently* from the
   positive, and the difference must be legible in the check-ids. Case 1 is the witness: four logs, one
   identical 7-id failure set. This is stronger than "we ran negatives" and it is checkable
   mechanically (compare the failing-id sets).
2. **An activation predicate requirement computed from the cell's own rows**, with the corollary that
   a stamp, not a name, decides exclusion — and the corollary's corollary: a reader that admits an
   absent stamp is itself a defect.
3. **A budget-arithmetic requirement** at the arm's true request shape, with the observed failure mode
   (a gate that prices a turn at 1 when tools-on turns cost k+1 and dies two turns early).
4. **An instrument-naming requirement for cost columns**, with the measured consequence of violating
   it (57.6× understatement; +17,193 residual; 48/48 rows with the wrong residue input) and the
   corollary that a recomputation which equals its own input is not evidence.
5. **A worked, end-to-end case series** where all seven failures occurred in *one* live experiment and
   each now has a guard with a recorded red→green witness.

**Reader value.** Anyone running an agent-serving benchmark: seven cheap checks that would have
prevented a fully spent, unadjudicable grid (1,270 requests, verdict `not_adjudicable`) and a quality
arm whose token column was a recomputation.

---

## 4. Validation (no endpoint required)

| step | what | why | effort |
|---|---|---|---|
| S-1 | re-derive cases 1–2 in a fresh process from the builder script embedded in `QUALITY-POSITIVE-CONTROL.md` | the truth table is one call's output; the builder makes it reproducible | offline |
| S-2 | re-derive cases 3–6 from `measure/GRID-2-FINAL.json` + the 16 manifests | the census must reproduce to the digit, not be copied | offline |
| S-3 | re-derive case 7's 57.6× and +17,193 from `quality/rows.jsonl` alone | the refutation must stand on the rows, not on a unit's prose | offline |
| S-4 | show **both** positive contrasts (control reads high and low; ledger identity) | without them the case series is unbalanced | offline |
| S-5 | have an independent verifier who authored none of the artefacts re-run S-1…S-4 and grade the paper's claims | house rule: the author's own summary is never the evidence | offline |
| S-6 | the guards themselves: for each of the seven, record the red→green witness (revert the fix, the guard fails) | the paper's central claim is that these checks work | offline |

**No new measurement is required.** If S-1…S-6 all reproduce, the paper is writable today. If fewer
than four cases reproduce, it is a workshop note, not a paper (§7).

---

## 5. Claims the paper may and may not make

**May:** each listed failure occurred and is reproducible from the named artefacts; the listed checks
detect each one; a fully spent live grid returned `not_adjudicable` because the instrument, not the
budget, was binding (1,270 requests / 79.375 per cell, 16 cells at the observed maximum = 1,536 <
1,729 remaining); a quality arm's cost column was 57.6× understated and its identity off by +17,193.

**May not:** that these are the only failure modes; that any specific published harness fails; that a
system built on these checks is thereby *correct* (it is only *interpretable*); that the flagship's
design is validated (that is F's business); that a null from a passing harness is a negative result
about the hypothesis (it is a null, and the paper's own vocabulary keeps `UNDEFINED` / `NOT_OBSERVED` /
`INVALID-INSTRUMENT` distinct from `0`).

---

## 6. Overlap boundary with the flagship

| | flagship (F) | this paper (S) |
|---|---|---|
| claim type | cost law + design consequence | validity requirement on measurement |
| unit of evidence | request rows, token bills, per-turn decomposition | check-id sets, stamps, exclusion rules, control tables |
| use of the gen-6 grid | the reason F's comparative is unmeasured (one sentence + the price of a re-run) | one row of the case series (cases 3–6) |
| use of the quality arm | capability 3/3, refusal 33/33, control 0/3 | cases 1, 2, 7 |
| dependence | needs V4/V5 to run its comparative | needs nothing from F; would be unchanged if the cost law were false |

**Rule enforced in both directions.** S may cite F's rig as the setting and may not carry the append
law or the design rule; F may cite S's regime as its measurement discipline and may not carry the
taxonomy or the case series. No number is claimed as new in both.

---

## 7. Failure conditions

| # | condition | consequence |
|---|---|---|
| S-K1 | fewer than four of the seven cases reproduce offline | write it as a workshop note titled by its single strongest case (the positive control), not as a paper |
| S-K2 | a case's red→green witness cannot be produced (the guard passes with the defect reintroduced) | drop the case; the check is not a check |
| S-K3 | the positive contrasts (control reading both ways, ledger identity) do not reproduce | the paper loses its balance and becomes an accusation; do not write it |
| S-K4 | the claims cannot be stated without generalising past one workspace | scope it explicitly ("one agent-serving rig, one workspace, one quarter") and keep the generalisation in the discussion |
| S-K5 | the independent verifier cannot reproduce S-1…S-4 | the paper's own central requirement fails on the paper; do not submit |

---

## 8. Venue and priority

A methods/reproducibility track (MLSys-style reproducibility, an evaluation-methodology workshop, or a
short paper in a systems venue). **Second priority**: finish F first. S is cheap, self-contained and
strengthens F's credibility — and its regime is what F's own comparative will be gated by, so writing
S first is defensible if F's funding is refused.

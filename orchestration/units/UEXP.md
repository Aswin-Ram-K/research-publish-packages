# UEXP — second labeller for the 190-case reflex fixture

**Status:** `done`. **Hard bound:** 50 tool calls; used 50.
**Declared write paths:** `experiments/second-labeller-190/**`, `orchestration/units/UEXP.md`,
`orchestration/handoffs/UEXP.json` (nothing else written).

## Purpose

`strategy/PAPER_CANDIDATES.md` §F.3 names external validity as the weakness of every strong
candidate, and records (UCORR1, 2026-10-14) that **no second labeller, no external benchmark and
no independent corpus exists anywhere outside `docs/research/`**. Four candidates (#3, #4, #5,
#10) rest on one hand-authored ~190-case fixture. This unit probes how much of that risk can be
retired by a **machine** second pass — and states plainly what it cannot retire.

## What was done

1. **Sandbox copy** with a hash proof (`076164ac…b4796` before = after = copy). Never wrote to the
   read-only target.
2. **Parsed** all 190 cases (721 option indices, arity 2–5). Parser validated against the header's
   independent `ESCALATE = 28` claim. **Self-caught parser defect D-P1**: a non-greedy regex,
   truncated by the option string `"the expanded[] ref list"`, produced a *false*
   `answer ∉ option set` headline; discovered by raw-text verification and fixed. Recorded, not
   deleted.
3. **Characterised** the labels: 74 distinct labels, 51 occurring once; two regimes (closed
   rosters for `escalation`/`topology`/`memory.admission`/`acquisition` vs bespoke option strings
   for `context.package`/`capability.family`); 0 single-option cases; no duplicate ids, no
   duplicate or near-duplicate questions; the three documented ERRATA corrections verified in
   place.
4. **Pre-registered** two labelling routes **before reading any per-case label**
   (`PREREGISTRATION.md`, frozen, including disclosed prior exposure to one trailing record and
   two header aggregates).
5. **Compared**: Route A (deterministic lexical) 0.342 / κ 0.325 — a weak rule, exactly as the
   pre-registration predicted; **Route B (blind model, fresh context, `correct`+`rationale`
   stripped) 0.9053 / κ 0.9014, 172/190 exact, 18 disagreements.**
6. **Adjudicated all 18** disagreements in `EVIDENCE.md` §6: 6 recorded-label-better, 9 genuinely
   contested, 2 defensible only via an unstated invariant, 1 recorded label **in tension with its
   own rationale**. Disagreement clusters into four conventions — 6 of 18 in `memory.admission`,
   of which 4 are a single convention.
7. **Defect sweep**: 0/190 in every pre-registered mechanical class, including the `F-EXP11-11`
   class (`answer ∉ option set`), independently corroborating
   `/home/zer0null/Duval/docs/research/FINDINGS_REGISTER.md:47`. 4 fixture items flagged for the
   subject, plus 1 corpus documentation correction owed at `strategy/PUBLICATION_STRATEGY.md:46`
   (the 191st `id:` match is the interface field at line 63, not "1 container id").

## Verdict with a bound

**Narrows the external-validity caveat; does not close it.** A blind machine reader reproduced
90.5% of the hand-authored labels and the specific mechanical defect class the corpus already
worried about is measured absent. But the second labeller is a **model, not a human annotator**:
κ = 0.901 is **not** inter-annotator agreement, must never be cited as such, and does **not**
discharge §F.3's call for a second independent labeller. Pooled κ is additionally fragile alone
(51 of 74 labels occur once, `pe` = 0.040); the stratified figures are the defensible reading.

**Expect the honest answer to "is this enough for a reviewer?": no.** It reduces one specific risk
class and hands the subject a 5-item repair list.

## Read-only compliance

Target HEAD `907fa39…` identical before and after; `git status --porcelain` identical (4
pre-existing untracked paths from an **unrelated concurrent session**); fixture sha256 identical;
0 tracked working-tree files changed. The only in-window target writes were 8 paths **all under
`.git/objects/`** (7 loose objects + 1 pack, 14:28:31; zero under `evals/fixtures`), attributed by
exclusion to the concurrent session — this unit issued only read-only commands against the target.
Attribution, not counting: see `EVIDENCE.md` §9.

## Stop reason

Completed inside the 50-call bound. A second distinct-model blind pass (`mimo-v2.6-flash`,
`labelsB2.json`) was launched as a robustness check and **stood down** when the primary pass
delivered, to stay inside the bound; it returned no file, so exactly one model pass is reported.

# UP1 — Paper candidate inventory (Duval / Consonance corpus)

**Status:** done · **Date:** 2026-10-11
**Purpose (one):** inventory every candidate that could become a legitimate publishable paper in the
Duval/Consonance research corpus, and judge how close each is to submission.

## Deliverable

`strategy/PAPER_CANDIDATES.md` — a 14-candidate ranked inventory plus a §D register of the ~60 documents
that are engineering reports / programme records / literature inputs rather than papers, and a §E
single-highest-leverage O-1 pick.

## Scope and budget

- **Write paths:** `strategy/PAPER_CANDIDATES.md`, `orchestration/units/UP1.md`, `orchestration/handoffs/UP1.json`.
- **Hard bound:** ≤55 tool calls. **Used: 30.** No bound hit; no partial.
- **Target repo `/home/zer0null/Duval` was opened read-only.** No writes, no git state changes, no hooks,
  no `/home/zer0null/Duval` mutation of any kind. Only `git remote -v`, `git log -1` and `git status
  --porcelain` were read.

## Method

1. Read `AGENTS.md`; located the corpus with `ls`/`wc`.
2. Read `docs/research/PAPER_DERIVATION.md` **in full** (719 lines) — the anchor candidate.
3. Read `FINDINGS_REGISTER.md` in full (rules, "How to use this for a paper", F-EXP11-01…17, M10/M11,
   the earlier-findings map) and extracted the complete `F-*` id set.
4. Extracted level-1/2 headings from every research document (39 files) for orientation.
5. Read the results/resolution sections of `EXP#10`–`EXP#22`, `LEARNINGS.md` M1–M14, the evidence trees
   (`experiments/`, `EXP#11-evidence/`, `EXP#12-evidence/`, `selfbuild/`, `BIOMAP/`), `evals/`,
   `CONSONANCE.md` §2/§9, `docs/consolidation/SOURCE_VERIFICATION.md`, `docs/FINDINGS.md` headings.
6. Ranked by (closeness to submission × strength of evidence); labelled every candidate's gaps with the
   numbers from the documents' own text, not inferred.

## Result summary

- **14 candidates** ranked. **8 publishable now with editing only** (#1–#6, #13, #14), **1 nearly ready**
  (#7, round 2 designed), **5 needing new experiments** (#8–#12).
- **§D:** 18 entries covering ~60 documents that are not papers as they stand.
- **§E pick for O-1:** candidate **#4** — the EXP#11 self-refinement negative result with its never-revised
  control stratum and its two documented "no external match" gaps. Runner-up **#3** (encoder vs fine-tuned
  4B decider) as the fastest accepted artifact; **#1** as the programme umbrella.

## Honest caveats carried forward

- The corpus contains **no published paper and no submission-ready draft** other than the anchor working
  paper; nothing in the inventory inflates an engineering report into a result.
- Four strong candidates (#3, #4, #5, #10) rest on **one 190-case fixture authored by one worker**; this is
  named as the corpus's single highest-return fix.
- `EXP#20` has **no control run**, `EXP#19` closed on a fired falsifier with a recorded note that the closure
  may have been premature, and `EXP#12`/`EXP#11`/`EXP#10` all closed with fired falsifiers — every one of
  these is reported as a result, not as a failure, per the corpus's own discipline.

## Handoff

`orchestration/handoffs/UP1.json`.

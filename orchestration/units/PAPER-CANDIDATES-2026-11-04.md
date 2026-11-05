# PAPER-CANDIDATES-2026-11-04 — the paper this workspace can actually publish

**Card.** `paper-candidates-2026-11-04` · **execution:** interactive omp session in worktree
`wt-20261104-171928-bd8df5c`, working against `/home/zer0null/research extractor` · **written by:** the closing
writer, 2026-11-04.

## One purpose

Answer one question and stop: *of the research produced since `papers/context-cache/MANUSCRIPT.md` was sealed
on 2026-10-24 21:39, which single concept is a publishable paper — one that identifies an issue and offers a
real improvement somebody else could adopt?* Deliver one page per candidate, plus a recommendation.

## Hard bound

- **0 endpoint requests, 0 model calls, 0 target-repo writes, no server or service touched.** The bound is a
  spend bound, not a time bound: the ledger stays at 2,591 / 1,729 of 4,320.
- No paper text beyond each brief's 120–160-word abstract stub. No cell launched.
- Stop when four briefs and the index exist on disk and in the record branch. Do not draft the paper here.

## Declared write paths

```
research/next-candidates/2026-11-04-candidates.md
research/next-candidates/briefs/N1-residue-law.md
research/next-candidates/briefs/N2-instrument-liveness.md
research/next-candidates/briefs/N3-the-wall.md
research/next-candidates/briefs/N4-finish-flagship.md
journal/2026-11-04.md, journal/INDEX.md
docs/STATE.md (header + §9), orchestration/VERDICTS.md (this batch section)
orchestration/units/PAPER-CANDIDATES-2026-11-04.md, orchestration/handoffs/PAPER-CANDIDATES-2026-11-04.json
```

No write outside those paths and outside `/home/zer0null/research extractor`. The record branch
`research/paper-candidates-2026-11-04` is the only git state this unit created; the checked-out branch
(`research/next-candidates-2026-10-24`, `f17663d`) and its index were never modified — commits were made
through a temporary `GIT_INDEX_FILE` and `git commit-tree`, never `git add -A`.

## Method

Four read-only units, one per concept, each told to read primary evidence (`*.jsonl`, `analysis.json`,
`CLAIMS.md`), quote a path for every number, label anything unverified, and state self-contradictions rather
than resolve them silently. A fifth unit re-derived N1's numbers against the rows and returned six corrections
and a do-not-carry list, which were folded in. **Every unit's toolset was read-only despite its card naming a
write path**, so the parent materialised the briefs from the units' verified reports plus its own reading of
`LAW.md`, `RECORD.md` and `MANUSCRIPT.md` §8–§9a. That is recorded as a residual, not glossed.

## Deliverable

Four briefs, ranked in `research/next-candidates/2026-11-04-candidates.md`: N1 (append-cost residue law, 0
requests) recommended; N2 (instrument liveness, 0) nominated as N1's "what a hit is" section; N4 (finish the
drafted flagship, 0 requests / ≈2 days) as the free unlock; N3 (the wall, ≈920 requests) deferred on budget.

## Kill condition

If the candidate record cannot be written inside the 0-request bound, or if a brief would have to assert a
number its own sources contradict, stop and record the blocker in the handoff — do not pad the sweep.

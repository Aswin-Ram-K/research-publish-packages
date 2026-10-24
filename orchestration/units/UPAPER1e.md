# UPAPER1e — fold the second blind-labeller pass into §6 Limitations

**Status:** done
**Hard bound:** 40 tool calls (used ~20).
**Write paths (declared, nothing else touched):**
`papers/encoder-crossover-190/MANUSCRIPT.md`, `papers/encoder-crossover-190/LIMITATIONS_UPDATE.md`,
`orchestration/units/UPAPER1e.md`, `orchestration/handoffs/UPAPER1e.json`.
Target `/home/zer0null/Duval` strictly read-only.

## Purpose (one)
Update the manuscript's §6 Limitations — and every place that cites the fixture-reliability result — to
reflect the **second, independent blind-labelling pass** (unit UEXP2, `mimo-v2.6-flash`), which returned a
**partial**, not clean, replication.

## Sources (read before writing)
- `experiments/second-labeller-190/ROBUSTNESS.md` (UEXP2)
- `experiments/second-labeller-190/RUN2.json` (UEXP2)
- `experiments/second-labeller-190/RUN.json` (UEXP first pass)
- `experiments/second-labeller-190/EVIDENCE.md:309` (IAA quote)

## Findings incorporated
1. Partial replication: B2 vs fixture agreement 0.8632, κ 0.8577; UEXP 0.9053 / 0.9014.
2. New quantity: B2 vs UEXP agreement 0.9158, κ 0.9125 (readers agree with each other more than with record).
3. `memory.admission` EPHEMERAL→DROP ambiguity replicated 4/4 — top repair item.
4. Same weak dimensions for both readers (`memory.admission`, then `acquisition`) → points at fixture.
5. Arity gradient reported for both readers **with** its kind confound and the escalation counter-check.
6. Disagreement structure: 26 (B2) / 18 (UEXP), 14-case shared contested core, reader-specific tails.
7. IAA limitation extended to two models: machine reproducibility only; human labeller still owed; §F.3 not
   discharged.

## Edits made (see `LIMITATIONS_UPDATE.md` for sentence-level before/after)
- Abstract "Not in this paper" sentence; §1 Contributions item 5.
- §3.4 reliability bullet — corrected the now-false "second pass returned no file" claim.
- §6.2 heading, opening, four new findings bullets, threshold bullet, closing IAA paragraph.
- §7 reproduction table row (added B2 row); Data availability second-labeller bullet.

## Constraint checks
- `numbers_changed` elsewhere = **0**: only the six edit spans changed; §6.6 untouched.
- Target HEAD `907fa39da7ba8ecfbe6e976b7a4cddadea7ac36b` before and after; `status --porcelain` = the same 4
  pre-existing untracked paths, attributed to the unrelated concurrent session.

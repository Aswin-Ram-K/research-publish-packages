# UPICK1 — Re-triage of the paper-candidate inventory against current disk state

**Unit:** UPICK1 (REPORT-ONLY analysis unit)
**Bound:** 25 tool calls maximum. If the inventory files cannot be found within 6 calls, STOP and report that.
**Parent:** session-c3d61727-8af8-4c19-b1b9-5922c347a11a

## Why this unit exists
The author asked whether a *different* paper could be published from work already done, worrying that
`papers/encoder-crossover-190/` no longer carries the weight it seemed to. The candidate inventory
(`strategy/PAPER_CANDIDATES.md`, `strategy/PAPER_CANDIDATES_SUPPLEMENT.md`,
`strategy/PUBLICATION_STRATEGY.md`) predates a large amount of landed work and must be re-triaged against
what now physically exists on disk.

## Task
1. Read the three inventory files; list every candidate named, with its stated claim and stated readiness.
   Do not invent candidates; do not silently drop any.
2. For each candidate, check what physically exists now (artifacts, results, fixtures, experiments,
   records) with paths; say plainly when a candidate has **no** supporting artifact.
3. Rank into tiers (writing-effort-only vs needs-new-experiment) with: (i) one-sentence claim,
   (ii) evidence on disk, (iii) marginal work, (iv) venue class and rough cost, (v) honest heft,
   (vi) main risk.
4. Separately assess **new proposals** not in the inventory but supported by what exists (sealed-fixture
   resource/benchmark paper; code-agnostic release + neutralisation methodology paper; independent-verification
   protocol / defect-class paper).
5. State the single candidate to ship next and why, and one explicitly not to pursue.

## Hard constraints
- **Report-only.** No edits to `papers/**`, `submission/**`, or `orchestration/units/UBUILD1.build.sh`.
- Do not invent evidence. Every existence claim cites a path actually opened. Unverified items marked `UNVERIFIED`.
- Do not assess the current paper's quality — scope is "what else is publishable".
- `/home/zer0null/Duval` is STRICTLY READ-ONLY: no writes, no git commands of any kind.

## Write paths (this unit alone)
- `strategy/PAPER_SHORTLIST.md`
- `orchestration/units/UPICK1.md`
- `orchestration/handoffs/UPICK1.json`
- `scratch/upick1/**`

## Forced report-back
Handoff to `orchestration/handoffs/UPICK1.json` with exactly the keys: `unit`, `status`, `artifacts`,
`evidence` (with `command_or_count` and `commands`), `blocker`, `next_unit_hint`, `write_paths`; then a
≤15-line summary to the parent session.

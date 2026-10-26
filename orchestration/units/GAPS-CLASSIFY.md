# GAPS-CLASSIFY — unit card and result

**Purpose.** Inventory every open gap between this repository and its own stated goals, one class each.
**Bound.** 18 tool calls; write paths: `orchestration/GAPS-INVENTORY.md`, `orchestration/handoffs/GAPS-CLASSIFY.json`,
this card. Automated session: no questions, no network, targets read-only.
**Sources (read, not invented).** `papers/context-cache/GAPS.md` (612 lines), `experiments/ptr-engine/RECORD.md`
(150), `papers/context-cache/FOLD-PROPOSAL.md` (97), and the newest contradiction handoffs: `RECON-C1`,
`APPLY-C1-VERDICT`, `C2-AMEND`, `CONTAINMENT-RULING`, `C5-APPLY`, `C8-REDERIVE`, `C8-304`, `C8-APPLY`.
`CLAIMS.md`/`MANUSCRIPT.md` were not needed: every gap named them only as the owner of a claim value already
quoted in `GAPS.md`.

**Result.** 48 distinct gaps: CLOSABLE-OFFLINE 13 · NEEDS-LIVE 25 · NEEDS-OPERATOR 6 · UNCLOSABLE 4.
Table, per-class ordering and the six-action path are in `orchestration/GAPS-INVENTORY.md`.

**What the classification buys.** Only 13 of 48 need no traffic, and six of those are already-decided corrections
sitting unapplied in `RECORD.md` (C1/C3 text, size restatement, `FIT-GAP.md` §2, the suite tree, the index hash).
The live work collapses to four small cells (#14, #15, #17, #5's SGLang half) plus the G3/G4 batteries, which the
G17 freeze currently forbids — so the binding constraint on publication is #40 (ratify the fold) and #39 (scope §8),
not measurement.

**Verification (re-runnable).**
- `grep -c '^| [0-9]' orchestration/GAPS-INVENTORY.md` → 48 row lines, ids 1–48 with no duplicate.
- Counts per class = the rows between each class heading; 13+25+6+4 = 48 = total, so no gap is unclassified.
- Every row carries a `file:line` or a handoff key; the four contradictions' newest layers are the ones cited
  (`RECORD.md:114` C1, `:145` C2 corrected, `:120` C4, `:122` C5, `:138` C8 reopened).

**Blocker.** None for the deliverable. Not clocked: no live request was possible, so class NEEDS-LIVE is an
assignment, not a result — nothing in this card asserts that any of those engines is currently up.
**Next unit hint.** Apply class-1 offline corrections (#1–#4, #7) and run #5/#6 re-derivations; both are pure
offline and together retire six of the thirteen.

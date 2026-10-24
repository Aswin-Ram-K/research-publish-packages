# UDECIDE1 — author decision brief (DONE)

**Purpose:** Assemble one short, answerable page (`strategy/AUTHOR_DECISIONS.md`) gathering the outstanding
author decisions scattered across the strategy documents.

**Hard bound:** 20 tool calls. Used: 19 (within bound).

**Write paths (only these, all honoured):**
- `strategy/AUTHOR_DECISIONS.md` — the deliverable, 166 lines, 7 decisions, 75 `file:line` citations
- `orchestration/units/UDECIDE1.md` — this card
- `orchestration/handoffs/UDECIDE1.json` — contracted seven-key handoff
- `scratch/udecide1/**` — created, unused (no scratch artifact needed)

**Never:** wrote nothing to `/home/zer0null/research-publish-packages`; ran **no** git command anywhere,
and in particular none against `/home/zer0null/Duval`; did not touch
`repro/encoder-crossover-190-SANITISED/redact.py` or `orchestration/units/UBUILD1.build.sh`.

**Sources read (read-only):** `strategy/PAPER_CANDIDATES.md` §G.1–§G.5 (lines 986–1160),
`strategy/NC1_UNBLOCK.md`, `strategy/NC1_FIX_PROPOSAL.md`, `strategy/PUBLISH_PACKAGE_MANIFEST.md` §7/§12,
`strategy/LEAD_PACKAGE.md` §2/§3/§7/§8/§9, `strategy/VERIFICATION_REPORT_13.md` (header).
`strategy/REGEN_ASSESSMENT.md` was not needed (no `gated-read` content — grep returned nothing).

**Deliverable:** 7 decisions — D1 #6, D2 #7, D3 #8, D4 #13, D5 #14 (the five §G `needs-author-decision` rows);
D6 NC1 route (i)/(ii); D7 `papers/gated-read-batching/` paper-only vs withhold. Each carries the question,
≤3 options, the sources' cost, a marked recommendation, and what is blocked.

**Carried-forward items identified:** D6 (NC1) and D7 (gated-read-batching) both marked *(carried forward)*.
D7 is the sharper case — `PUBLISH_PACKAGE_MANIFEST.md` frames the same directory as both decided (`:190-193`)
and open (`:487-493`).

**Settled items recorded, not raised:** licence posture, no copyright registration, code-agnostic release —
with the three stale framings named (`PUBLISH_PACKAGE_MANIFEST.md:446-449`, `:458-465`, `:497`;
`LEAD_PACKAGE.md:282-283`).

**Disagreement/attribute discipline:** NC1 option-(ii) worst case — `NC1_UNBLOCK.md:198` (12→8) vs
`NC1_FIX_PROPOSAL.md:140` (12→11 best, 12→6 worst); preferred the FIX_PROPOSAL range and labelled it a
specification, not a measurement (`NC1_FIX_PROPOSAL.md:177-178`). `DISCLOSURE_CHANGES.md` 19 vs 52 hits
labelled not-comparable. Lead-package's UNVERIFIED `tools/trace.ts` count (`LEAD_PACKAGE.md:296`) superseded
by UNC1A's later measured 4 hits (`NC1_UNBLOCK.md:189`).

**Status:** done.

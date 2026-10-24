# UDISCLOSE7 — Element-by-element disclosure classification for candidate #7

**Purpose.** Classify every element of candidate #7 ("Batching binary gates is free; routed extraction
cuts context 15.3× and exposure to 0/20") into `publish` / `withhold` / `neutralise` / `already-disclosed`
BEFORE any drafting. Report only — no drafting, no renaming, no redaction, no packaging.

**Declared write paths:** `strategy/GATED_READ_DISCLOSURE.md`, `orchestration/units/UDISCLOSE7.md`,
`orchestration/handoffs/UDISCLOSE7.json`, `scratch/udisclose7/**`.

**Hard bound:** 30 tool calls. Stop condition: an element whose class cannot be decided from disk in
3 attempts → mark `undecided` with reason, move on.

**Constraints:** `/home/zer0null/Duval` strictly read-only; no git commands against it (not even bare
`git status`); write only inside declared paths.

**Inputs:** `strategy/PAPER_CANDIDATES.md` (candidate #7 record), `strategy/PRIOR_DISCLOSURE_AUDIT.md`,
`strategy/DISCLOSURE_INVENTORY.md`, `strategy/ARCHIVE_WINDOW_CHECK.md`, `strategy/WITHHELD.md`,
`strategy/CODE_AGNOSTIC_RELEASE_POLICY.md`; target mechanism sources under `/home/zer0null/Duval/src/**`.

**Output:** `strategy/GATED_READ_DISCLOSURE.md` — withhold list first, then element table, then
residual risk / undecideds / minimal tag-replacement set.

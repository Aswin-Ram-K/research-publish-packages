# UAD6 — Archive window resolution (does the AGPL window expose the target's `src/**`?)

**Workspace:** `/home/zer0null/reserach extarctor` (write only inside declared paths).
**Target:** `/home/zer0null/Duval` — STRICTLY READ-ONLY. No writes, no `git` commands against it.

## Purpose (one)
Resolve the workspace self-contradiction about whether the target's implementation source was ever
publicly retrievable, by testing retrieval directly against the archive-window refs.

## Conflict
- `strategy/WITHHELD.md` :444-445 — `consonance/src/journal.ts` and `src/journal.ts` are **404 at every historical ref** → never retrievable.
- `strategy/ARCHIVE_WINDOW_CHECK.md` — records an AGPL-3.0 window: `ccdab112` (2026-10-09 04:11) → `b81b35e` (2026-10-10 07:51), ~27.5 h, ~481 entries, ~428 under `consonance/`.

If the window tree's `consonance/src/**` maps to target `src/**`, then WITHHELD's 404 claim is wrong and
withhold items 4, 5 and item X-08 move to `already-disclosed`.

## Steps
1. Read verbatim claims w/ `file:line` from WITHHELD.md (:430-460 + AGPL enumerations), ARCHIVE_WINDOW_CHECK.md (whole), PRIOR_DISCLOSURE_AUDIT.md, DISCLOSURE_INVENTORY.md.
2. Establish file-set facts: repo, boundary refs, entry count, top-level dirs, whether a path→`src/**` mapping is recorded (do not assume one).
3. Test retrieval directly: in-window refs `ccdab112`, `b81b35e` + ≥1 post-removal ref × paths `consonance/src/journal.ts`, `src/journal.ts`; record status, bytes, first ~15 lines, sha256.
4. One-sentence decision + class-change list.
5. Residual uncertainty; note that no filing/declaration/exhibit may assert the work was never published.

## Deliverable
`strategy/AD6_ARCHIVE_WINDOW_RESOLUTION.md` — claims side by side w/ `file:line`; file-set facts; retrieval table (URL | ref | status | bytes | sha256 | verdict); decision; class changes; uncertainty; limits.

## Hard bound
20 tool calls. Stop condition: if the raw-content question cannot be settled in 5 network attempts → report `partial`, name the exact URL and failure mode, stop. Never infer from prose.

## Declared write paths
- `strategy/AD6_ARCHIVE_WINDOW_RESOLUTION.md` (new)
- `orchestration/units/UAD6.md`
- `orchestration/handoffs/UAD6.json`
- `scratch/uad6/**`

## Must NOT
Edit `strategy/WITHHELD.md` or any existing record. Do not classify further candidate elements. Do not draft/edit any paper.

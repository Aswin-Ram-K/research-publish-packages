# USYS1 — System Item Inventory (report-only)

**Unit type:** inventory / report-only. **Bound:** 30 tool calls.
**Parent:** session-c3d61727-8af8-4c19-b1b9-5922c347a11a

## Purpose
Enumerate and describe every *standalone-paper candidate item* — mechanism, subsystem, protocol,
instrument or method — inside `/home/zer0null/Duval` (project "Consonance"), so that a later unit can
assess novelty against literature and an author can publish short standalone papers about individual
novel items.

## Hard rules
- `/home/zer0null/Duval` STRICTLY READ-ONLY: no writes, **no git of any kind**. Read only.
- No novelty/prior-art assessment (next unit's job).
- Report-only: write nothing outside declared write paths.
- Quote literal paths, byte sizes, line counts. Mark unverified as `UNVERIFIED`.

## Deliverables
- `strategy/SYSTEM_ITEM_INVENTORY.md` — the item inventory + coverage statement + top 8-12 items.
- `orchestration/handoffs/USYS1.json` — handoff with keys: unit, status, artifacts, evidence
  (`command_or_count`, `commands`), blocker, next_unit_hint, write_paths.
- `scratch/usys1/**` — scratch.

## Write paths (mine alone)
- `strategy/SYSTEM_ITEM_INVENTORY.md`
- `orchestration/units/USYS1.md`
- `orchestration/handoffs/USYS1.json`
- `scratch/usys1/**`

## Plan of work
1. Enumerate `/home/zer0null/Duval` tree (≤5 calls): top-level dirs, sizes, file counts; prioritise
   `docs/research/**`, `consonance/src/**`, `tools/**`.
2. Read the anchor design docs (PAPER_DERIVATION.md, FINDINGS_REGISTER.md, DECISION_LOG.md,
   BOARD.md, DECIDER_STACK_DECISION.md, PAUSE_STATE.md, README.md, VISIT_LOG.md, LEARNINGS.md).
3. Detail items: function, implementation paths + bytes + lines, doc anchors `path:line`, mechanism
   prose, evidence on disk, coupling, already-public status.
4. Coverage statement (swept vs not reached), top 8-12 items with one-line reasons.
5. Write handoff JSON, send result to parent.

# UVER18 — verifier: UPOLICY1's AGENTS.md containment edit

**Bound:** 12 tool calls. **Used:** 9. **Overall: pass.**
**Author under check:** UPOLICY1. **Independence:** UVER18 did not write the edit.

## Scope
Re-check the two new `## Hard constraints` bullets (`AGENTS.md:77-81`, `:82-87`), the sharpened
`AGENTS.md:74-76`, every cited figure against `strategy/CONTAINMENT_CHECK.md`, the pin digest, the
heading structure, and a red→green revert on a scratch copy.

## Result
All UPOLICY1 claims reproduce. All five evidence figures match their cited source lines
(`CONTAINMENT_CHECK.md:179`, `:184`, `:191`, `:161-163`, `:261-262`). Pin sha256
`431605e6…`, blob `94495930…` and size 866816 all recomputed and equal. File is 6647 bytes; headings
at 6/19/65/72/94 unchanged in text; `git diff` is one hunk confined to the described edit.
red→green passes (1/1 present → 0/0 absent on the bullet-stripped copy).

> **Superseded 2026-10-16 (UFIX22, dated record left unrewritten) — impacts `:13` and `:14` above:** the `strategy/CONTAINMENT_CHECK.md` line numbers cited at `:13` shifted when UFIX17 edited that file on 2026-10-15. Current anchors: `:166`–`:168` (pin capture: 866,816 B / 573 records / 573 gated lines / 712 gate occurrences), `:187` (136 handoffs / 194 command strings), `:192` (62 plain `git status` runs), `:199` (no target-mutating verb), `:270` (§7 live-path growth). The blob `94495930…` recomputed equal at `:14` is the workspace docket repo's own recorded blob, **not a target object**; the live path re-measured **1,624,082 B / 1087 lines / sha256 `35687221…` at 2026-10-15 21:02:05**. Verify the anchors before relying on the figures.

## Lists
contradicted: none · overstated: none · not_reproduced: none · unverified: none.

## Containment
No git command against `/home/zer0null/Duval`; in-workspace git calls used `GIT_OPTIONAL_LOCKS=0`.
`AGENTS.md` not edited; revert done on `scratch/uver18/AGENTS.md.reverted`.

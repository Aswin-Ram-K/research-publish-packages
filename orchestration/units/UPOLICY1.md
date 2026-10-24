# UPOLICY1 — policy card (bounded: 12 tool calls)

**Purpose.** Add two operational rules to `AGENTS.md` that the containment audit
(`strategy/CONTAINMENT_CHECK.md`, unit UCONT1) measured but the document does not state:

1. **No bare `git status` against a read-only target** — pass `--no-optional-locks` (or
   `GIT_OPTIONAL_LOCKS=0`), because `git status` refreshes `.git/index` and therefore writes.
   Evidence: 62 units across 136 handoffs; 0 target-mutating verbs.
2. **Trace-dependent claims cite a pinned copy, not a live path** — pinned path + sha256 + blob.
   Evidence: the trace grew 866816 → 1570243 bytes mid-batch.

   > **Superseded 2026-10-16 (UFIX22, dated record left unrewritten):** `1570243` was the live object's size at 2026-10-15 18:50:03 (1031 lines), not a gate count, and the live path has since measured **1,624,082 B / 1087 lines / sha256 `35687221…` at 2026-10-15 21:02:05**. The pinned copy is `dockets/duval/duval-u55-pinned/material/data/2026-09-28-duval-m0.jsonl` — 866,816 B / 573 records / 573 gated lines / 712 gate occurrences, sha256 `431605e6…` (`strategy/CONTAINMENT_CHECK.md` §2, currently `:166`).

**Placement.** Under the existing `## Hard constraints` heading (`AGENTS.md:72`), inside the
existing bullet about target read-only-ness (`AGENTS.md:74-76`). No restructuring, no renumbering.

**Write paths.**
- `/home/zer0null/reserach extarctor/AGENTS.md`
- `/home/zer0null/reserach extarctor/orchestration/units/UPOLICY1.md`
- `/home/zer0null/reserach extarctor/orchestration/handoffs/UPOLICY1.json`
- `/home/zer0null/reserach extarctor/scratch/upolicy1/**`

**Forbidden.** No writes under `/home/zer0null/Duval`; no writes to
`/home/zer0null/research-publish-packages`; no git command against the target at all (invoking
`git status` on `/home/zer0null/Duval` is exactly the defect being documented).

**Bound.** 12 tool calls. Stop condition: if the before-string is not unique in `AGENTS.md`, STOP
and report `partial` rather than editing.

**Evidence figures (as measured in CONTAINMENT_CHECK.md).**
- `CONTAINMENT_CHECK.md:179` — **136** handoffs; **194** target-referencing command strings.
- `CONTAINMENT_CHECK.md:184` — **62 units** issued a plain `git -C /home/zer0null/Duval … status`.
- `CONTAINMENT_CHECK.md:191-194` — **No unit ran a target-mutating git verb.**
- `CONTAINMENT_CHECK.md:161-163` — pin `dockets/duval/duval-u55-pinned/material/data/2026-09-28-duval-m0.jsonl`,
  866816 bytes, git blob `94495930fbf0fd991b14c1e4de79d87a93fce9ae`, sha256 `431605e624ca90596ec8c5890fc40da08715ae1ffa6759b689255f1670af4ecb`.
- `CONTAINMENT_CHECK.md:261-264` — grew **866816** → **1570243** B.

> **Superseded 2026-10-16 (UFIX22, dated record left unrewritten):** the `strategy/CONTAINMENT_CHECK.md` line numbers cited here shifted when UFIX17 edited that file on 2026-10-15. Current anchors: `:166`–`:168` (pin capture: 866,816 B / 573 records / 573 gated lines / 712 gate occurrences), `:187` (136 handoffs / 194 command strings), `:192` (62 plain `git status` runs), `:199` (no target-mutating verb), `:270` (§7 live-path growth). The blob `94495930…` is the workspace docket repo's own recorded blob, **not a target object**; the live path re-measured **1,624,082 B / 1087 lines / sha256 `35687221…` at 2026-10-15 21:02:05**. Verify the anchors before relying on the figures.

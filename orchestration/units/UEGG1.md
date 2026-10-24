# UEGG1 — record the author's decision to leave the residual terminology in place

**One purpose:** Append a dated, clearly-titled author-decision block recording the author's
2026-10-16 instruction that the residual lowercase terminology stays in the neutralised release
stimulus — deliberately retained, framed by him as a small "easter egg" — to
`strategy/CASE_VARIANT_SETTLEMENT.md` (append only). Fallback: `strategy/DELIBERATE_RESIDUE.md`
if the target's structure makes an append unsafe.

**Hard bound:** 8 tool calls. If a safe append is not achievable in ≤2 attempts, write the
fallback file and report which was used and why; report `partial` rather than forcing.

**Declared write paths (nothing else):**
- `strategy/CASE_VARIANT_SETTLEMENT.md` (append only) or `strategy/DELIBERATE_RESIDUE.md`
- `orchestration/units/UEGG1.md`
- `orchestration/handoffs/UEGG1.json`

**Inputs:** this card; the tail of `strategy/CASE_VARIANT_SETTLEMENT.md` (for style/anchor);
counts and final numbers supplied by the parent card — **quoted, never re-derived**.

**Required block content:** verbatim author quote dated 2026-10-16; statement that the residue is
deliberate, not an oversight; enumeration of survivors with counts (`step` 728, `grant` 213,
`escalate` 131, `Answer` 116, `return` 24, `single` 20, `drop` 14, `replay` 8, `sequence` 8,
`continue` 4, `Discard` 1, `persistent` 1, verb `materialise`); statement of what was removed
(all branded/title-case names, kinds, roles, states, record field names); final numbers (route A
κ 0.3248813212427869, route A agreement 0.34210526315789475, A/B mutual agreement
0.3684210526315789, `disagreements_where_routeA_backs_record` 4, route B κ 0.9013584840356494
unchanged, fixture digest c7696edc0e71d83faafc2e489925788e0f36c6af94913674f8953718352c9a55
unchanged); cross-references to `strategy/WHOLE_CLASS_NEUTRALISATION.md`,
`strategy/STIMULUS_NEUTRALISATION.md`, `strategy/VERIFICATION_REPORT_32.md`; statement that this
decision makes the release numbers final and unblocks paper alignment.

**Constraints:** do not edit release trees (`scratch/uneutral10/package/`), the paper, or any
count; do not rewrite or delete existing text in the target; `/home/zer0null/Duval` is read-only;
nothing written outside this workspace.

**Evidence plan:** grep the new section title in the target; parse the handoff with `json.load`;
record the line-count delta of the target.

**Status:** in_progress.

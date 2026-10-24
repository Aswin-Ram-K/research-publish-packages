# Unit UFIXREV7 — fix REVERIFY §2c mis-attribution of the exposure column

**Workspace:** `/home/zer0null/reserach extarctor` (target `/home/zer0null/Duval` strictly read-only; no git).

**Purpose.** Unit UXPOSE7 settled a mis-attribution: `strategy/GATED_READ_REVERIFY.md:103` attributes the
published corrected exposure column (20/20/19/0/19/20) to the field pair `expo_a∨expo_b`, which is wrong —
those flags are computed over the files that were *read* (pre-extraction, `bench.py:588-591`) and give
**19** for the routed arm, not 0. The paper's stated definition is payload **survival into the exact context
handed to the reasoner** (quoted at `state/kg-refresh/duval/repo/docs/research/GATED_READ_2026.md:100-102`;
column header `:194`; headline `:217`), computed by `bench.py:605-609` as `ctx_has_a`/`ctx_has_b`; that
union recomputes to exactly [20,20,19,0,19,20], so the routed arm's 0/20 headline **holds**.

**Inputs read first (per brief).**
- `strategy/EXPOSURE_COLUMN_RESOLUTION.md` (UXPOSE7 deliverable, 163 lines)
- `orchestration/handoffs/UXPOSE7.json` (UXPOSE7 handoff)

**Job (4 items).**
1. Fix `strategy/GATED_READ_REVERIFY.md:103` — attribute to `ctx_has_a ∨ ctx_has_b`; preserve original
   wording / add dated `Note 2026-10-16 (UFIXREV7):`; assert before-string matches exactly once, else STOP
   that edit and report.
2. Add a dated note recording the near-miss: `expo_*` = read pre-extraction → 19, not the paper's exposure
   definition; cite `bench.py:588-591` vs `:605-609`; name `strategy/EXPOSURE_COLUMN_RESOLUTION.md` as
   evidence.
3. Check `strategy/PAPER_CANDIDATES.md:530` (column/headline) — right field & routed-arm statement? If right,
   change nothing and say so; if wrong, smallest correction + dated note; do not rewrite the entry.
4. Check whether `strategy/GATED_READ_REVERIFY.md` states the fourth-configuration gate F1 as `0.210`
   anywhere; if so add a dated note that the exact value is 0.210526 and 3-dp rounding is 0.211. No other
   number changed.
5. Handoff reports plainly anything found but NOT fixed.

**Constraints.** Dated notes and pointers, no silent rewrites; preserve every original value and conclusion.
Never quote withheld literals (payload tokens, answer strings, private paths, model ids) — counts and field
names only. No edits to `papers/**`, `state/**`, or outside declared paths.

**Declared write paths.** `strategy/GATED_READ_REVERIFY.md`, `strategy/PAPER_CANDIDATES.md`,
`orchestration/units/UFIXREV7.md`, `orchestration/handoffs/UFIXREV7.json`, `scratch/ufixrev7/**`.

**Hard bound:** 10 tool calls. **Stop condition:** if a before-string does not match exactly once, STOP that
edit and report rather than forcing a match.

**Status:** in progress.

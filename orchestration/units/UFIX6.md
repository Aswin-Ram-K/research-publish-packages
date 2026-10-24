# UFIX6 — apply UVER4's three narrow corrections (C1, C2, C3)

**Purpose.** Unit UVER4 returned `pass-with-corrections` on `papers/encoder-crossover-190/MANUSCRIPT.md` +
`AVAILABILITY.md` (`strategy/VERIFICATION_REPORT_4.md`). UFIX6 applies the three narrow corrections, keeps
`numbers_changed = 0`, and closes UTS1's UNVERIFIED item U9.

**Inputs read:** `strategy/VERIFICATION_REPORT_4.md` (work order, full), the two manuscripts,
`experiments/second-labeller-190/RUN2.json`, `orchestration/handoffs/UREPRO.json`,
`repro/encoder-crossover-190/README.md`.

**Corrections applied.**
- **C1** (misattributed pseudo-key `harness_self_contained = partial`): dropped the key and stated the
  limitation in prose, quoting README §5's real heading — in both `MANUSCRIPT.md:809` and `AVAILABILITY.md:9`.
  Origin of the key confirmed as `orchestration/handoffs/UREPRO.json:16`. Substance (partial self-containment)
  unweakened.
- **C2** (§6.2 shared contested core): re-read `RUN2.json .disagreement_structure.shared_contested_core` →
  **14** ids. Number was correct; the enumeration named 13. Added `memory.admission-018` (`DROP→EPISODIC`).
- **C3** (`AVAILABILITY.md:29-30` path): repointed `reproducesAt3dp` / `absoluteDifference` to
  `.strata.instrument190` (`.perCase` 190 rows stays at model level). Values unchanged.
- **U9:** verified no total file count is claimed in either file → closed as a non-defect.

**Deliverable:** `papers/encoder-crossover-190/VERIFIER_CORRECTIONS.md` (before/after per correction, source,
and the `numbers_changed = 0` re-count).

**Write paths:** `papers/encoder-crossover-190/{MANUSCRIPT.md,AVAILABILITY.md,VERIFIER_CORRECTIONS.md}`,
`orchestration/units/UFIX6.md`, `orchestration/handoffs/UFIX6.json`. Nothing else.

**Containment.** Target `/home/zer0null/Duval` read-only: HEAD before = after =
`907fa39da7ba8ecfbe6e976b7a4cddadea7ac36b`, `status --porcelain` = the same 4 pre-existing untracked paths
(attributed to the unrelated concurrent session). Read-only verbs only.

**Bound:** 35 tool calls. **Result:** done.

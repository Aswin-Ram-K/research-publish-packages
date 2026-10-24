# Unit UFIXGR7 — apply re-verification corrections to gated-read-batching candidate

**Purpose:** Apply the corrections established by the two report-only units
(`strategy/GATED_READ_REVERIFY.md`, `strategy/GATED_READ_DISCLOSURE.md`) to the
drafted paper, its CLAIMS/GAPS records, and `strategy/PAPER_CANDIDATES.md`.

**Hard bound:** 25 tool calls. Stop condition: if an intended edit's before-string
does not match exactly once, STOP that edit, leave the file unchanged, report it.

**Write paths (exactly these):**
- `papers/gated-read-batching/MANUSCRIPT.md`
- `papers/gated-read-batching/CLAIMS.md`
- `papers/gated-read-batching/GAPS.md`
- `strategy/PAPER_CANDIDATES.md`
- `orchestration/units/UFIXGR7.md`
- `orchestration/handoffs/UFIXGR7.json`
- `scratch/ufixgr7/**`

**Forbidden:** `papers/gated-read-batching/{REFS.md,DISCLOSURE_CHANGES.md}`,
anything under `papers/encoder-crossover-190/`, and any write/git command against
`/home/zer0null/Duval`.

**Corrections to apply (from the two reports / unit card):**
1. Corpus size "1.83 MB" unsupported (MANUSCRIPT ~:82, ~:193; CLAIMS ~:31) →
   replace with measured basis (2,426,190 B pinned / 2,886,664 B live) or drop.
   Target's `docs/research/GATED_READ_2026.md:61` carries it too — report only.
2. Gold labels stored not reproducible → GAPS limitation: 127 pinned / 130 live
   re-derived vs 120 stored; 10 of 12 stored-only are `AGENTS.md`; 120-pair count,
   6.67% base rate, all precision/recall/F1 inherit stored labels.
3. 207/207 = 120/120 row-backed + 87 in-end-to-end with no per-decision rows.
4. PAPER_CANDIDATES.md: `:537` "1/14" → 15.279; `:536-538` "best arm's accuracy"
   → recorded R5 `stage_route` mean 0.55 < 0.65 bar; `:544` "2.4×" vs `:151` "2.3×"
   → 2.341× / 2.418× named by configuration. Keep old values, dated notes.
5. Do NOT retitle candidate #7. Add dated annotations at `:81`, `:530`, `:1028`
   citing MANUSCRIPT.md:195 and GAPS G-13/G-14.
6. Raw-record provenance in CLAIMS.md (or GAPS.md): path
   `state/refresh-verify/duval/scnB/state/kg-refresh/duval/repo/.worktrees/engine-a/docs/research/gated-read-rows.jsonl`,
   2,267,742 bytes, 9,260 lines, md5 `3aad1ae29e472ef9f5f54e179510faf5`.

**Status:** in progress.

# UFIX5 — bring two stale references up to date (audit present; divergence resolved)

**Unit:** UFIX5 · **Date:** 2026-10-15 · **Status:** done
**Purpose (one):** no reader is told `strategy/TRADE_SECRET_AUDIT.md` is missing when it is present, and
no reader is told UMEMO1's main-repo divergence is still unresolved.
**Hard bound:** 25 tool calls. **Used: 10.** (No retries needed; no tool call failed.)

## Target repo
`/home/zer0null/Duval` — **read-only; not touched.** No command in this unit ran inside it.

## Write paths (declared, and the only ones touched)
`strategy/CODE_LICENSING_STRATEGY.md`, `strategy/licence-templates/PLACEMENT.md`,
`orchestration/units/UFIX5.md`, `orchestration/handoffs/UFIX5.json`.

## Evidence collected (every change traces to one of these reads)

1. **Audit exists.** `wc -l -c` → `507 48851 strategy/TRADE_SECRET_AUDIT.md`;
   `stat -c '%n %y %s'` → `2026-10-15 15:31:34.101855088 -0500 48851`. Scope read from its head
   (`# TRADE_SECRET_AUDIT — what the author's own outputs disclose, per mechanism`, unit **UTS1**) and
   its tail (target HEAD `907fa39…` unchanged, four untracked paths attributed to another session).
   **Its findings were not read for content and were not imported anywhere.**
2. **Errata resolution verified.** `strategy/CODE_LICENSING_STRATEGY.md` `:9–60` carries
   `## ERRATA — unit UMEMO1, 2026-10-15`, whose two-tier table fixes *main Consonance repository =
   proprietary notice* / *each released piece = PolyForm Noncommercial 1.0.0*, and states of
   `PLACEMENT.md` §5 item 4: "**this errata resolves it.**" In-place `SUPERSEDED` markers confirmed at
   `:423` (§5.1, "SUPERSEDED FOR THE MAIN REPOSITORY") and `:590` (§6 Stage 0, "SUPERSEDED").
   Resolution is present → proceeded (no stop condition hit).

## Changes made (marked, per the append-only-errata norm — nothing silently rewritten)

### 1. `strategy/CODE_LICENSING_STRATEGY.md` (`:56–60` → `:56–69`)
The trade-secret cross-reference said the audit was "being produced by another unit", "**not on disk in
this workspace at the time of this errata**" and "in progress". Replaced with: the audit **is on disk**,
cited by path with unit/line/byte/mtime facts, and its findings are **not** imported. A dated
`> **CORRECTION — unit UFIX5, 2026-10-15**` blockquote follows, quotes the withdrawn wording verbatim,
says it was **true when written** (UMEMO1 checked before the audit landed; its card was written at 15:33
against that earlier read) and **false now**, and states the reason for the correction.

### 2. `strategy/licence-templates/PLACEMENT.md` §5 (items 3 and 4) — **2/2**
- **Item 3** — "is not present on disk" → "**now exists on disk**" at `strategy/TRADE_SECRET_AUDIT.md`,
  with unit UTS1, 507 lines / 48,851 bytes, written 2026-10-15 15:31:34, presence checked by UFIX5.
  Marked with a dated "Corrected by UFIX5" note naming the previous wording.
- **Item 4** — heading gains "**— RESOLVED**"; body now records that the divergence is **resolved** by
  the dated ERRATA in `CODE_LICENSING_STRATEGY.md` (two-tier: main repo **proprietary**, pieces
  **PolyForm NC 1.0.0**), cites the SUPERSEDED markers `:423`/`:590`, and is marked with a dated
  "Corrected by UFIX5" note naming the previous closing sentence.

## Sweep (step 5)
`grep -n -i "not on disk|not present on disk|not resolved|rather than resolved|unresolved|pending|
awaited|not yet|forthcoming|absent|missing|TBD|in progress|being produced"` over both documents:
- Before the fix: the three stale statements above, plus `CODE_LICENSING_STRATEGY.md:30` — *"recorded
  (unresolved) in `PLACEMENT.md` §5 item 4; **this errata resolves it.**"* **Reviewed, left as written:**
  it is a past-tense description of what ULIC2 recorded and the same sentence already states the
  resolution, so it does not tell a reader the divergence is open. Recorded here rather than edited.
- After the fix: no live stale statement remains; the only matches are the deliberately preserved
  *withdrawn* wording quoted inside the two dated correction notes (memo `:64`, PLACEMENT `:87`, `:98`).
- Other `other_stale_found`: **0** (the `:30` line is correct as written; no other candidate found).

## Not done (out of scope, by instruction)
- Did **not** summarise or import any finding from `TRADE_SECRET_AUDIT.md`.
- Did **not** edit `strategy/TRADE_SECRET_AUDIT.md`, `strategy/licence-templates/RELEASED-PIECE/**`,
  `papers/`, `repro/`, `jobs/`, `journal/`, or `experiments/`.
- Did **not** write to `/home/zer0null/Duval`.
- Resolved no licence question; invented no fact not read from disk.

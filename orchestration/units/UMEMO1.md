# UMEMO1 — reconcile `CODE_LICENSING_STRATEGY.md` with the author's final two-tier IP position

**Unit:** UMEMO1 · **Date:** 2026-10-15 · **Bound:** max 30 tool calls (used 20)
**Write paths (declared):** `strategy/CODE_LICENSING_STRATEGY.md`, `orchestration/units/UMEMO1.md`,
`orchestration/handoffs/UMEMO1.json`. Nothing else touched.
**Target:** `/home/zer0null/Duval` — read only. `LICENSE` md5 `eb1e647870add0502f8f010b19de32af`
unchanged (matches ULIC2's record); no git command run in the target.

## Purpose (one)
Bring the memo into line with the author's final position by **appending a dated errata**, not by
silently rewriting.

## Divergence — confirmed, not taken on trust
- `strategy/CODE_LICENSING_STRATEGY.md` §5.1 (now `:449`): **"Licence text | PolyForm Noncommercial
  1.0.0, verbatim, as `LICENSE`"**, **"a short root-level `COMMERCIAL.md`"**, **"a short
  `CONTRIBUTING.md`"**, and a README paragraph — all at the main repo root.
- Same file §6 Stage 0 (now `:583`): **"Replace AGPL with PolyForm NC; add `COMMERCIAL.md`,
  `CONTRIBUTING.md`; state the policy"** for `Duval` (private).
- `strategy/licence-templates/PLACEMENT.md` §5 **item 4** frames the same divergence and deliberately
  does **not** resolve it ("The divergence is recorded here rather than resolved by this unit").
- Author's clarifying words, 2026-10-15: *"i wanna keep the core pieces trade secrets … so no licence
  on the main consonance folder that's proprietary."*
→ **Divergence is exactly as ULIC2 reported.** Proceeded.

## What was done
1. **ERRATA section appended after the front matter** (`:9`–`:59`), dated and attributed to UMEMO1,
   carrying the two-tier status table (main repo → proprietary notice; each released piece → PolyForm
   NC + `COMMERCIAL.md` + `CONTRIBUTING.md`), the stale-statement census, and the trade-secret note.
2. **§5.1 marked superseded in place** (`:423`) with the **replacement two-tier file table** (`:432`–
   `:446`). The original §5.1 table is retained verbatim beneath a label (`:447`+, rows still at
   `:451`–`:456`).
3. **§6 Stage 0 (and Stage 2) marked superseded in place** (`:590`), immediately under the stage
   table. The original Stage 0 row is retained (`:583`).
4. **Stale-statement census:** 6 clearly stale (corrected) + 4 ambiguous (recorded, not decided) = 10.
   Listed in the ERRATA. Nothing deleted.
5. **Trade-secret cross-reference:** points at `strategy/TRADE_SECRET_AUDIT.md`, states it **is not on
   disk** (matching `PLACEMENT.md` §5 item 3) and is **in progress**; no finding of that audit is
   summarised or guessed.

## Evidence
```
grep -n "ERRATA|SUPERSEDED|superseded" strategy/CODE_LICENSING_STRATEGY.md
  9:## ERRATA — unit UMEMO1, 2026-10-15
 423:> **SUPERSEDED FOR THE MAIN REPOSITORY — unit UMEMO1, 2026-10-15 ...
 447:**The original §5.1 table (superseded for the main repository, retained for the record):**
 590:> **SUPERSEDED — unit UMEMO1, 2026-10-15 ... Stage 0 ... is superseded
grep -n "root-level .COMMERCIAL.md|Replace AGPL with PolyForm NC" ...
 453: (original §5.1 row intact)   583: (original §6 Stage 0 row intact)
wc -l strategy/CODE_LICENSING_STRATEGY.md  -> 690 (was 598; +92, append/mark only)
md5sum /home/zer0null/Duval/LICENSE -> eb1e647870add0502f8f010b19de32af (unchanged)
ls strategy/TRADE_SECRET_AUDIT.md -> No such file or directory
```

## Scope discipline
No licence term, legal standard or finding was invented. Every change traces to the author's quoted
words, to `PLACEMENT.md`, or to text already in the memo. `strategy/licence-templates/**` was **not**
edited (ULIC2 owns it); no other strategy file was touched.

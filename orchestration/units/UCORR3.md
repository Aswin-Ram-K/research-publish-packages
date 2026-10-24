# UCORR3 — narrow the M12 "every correction moved the arm DOWN" overstatement

**Workspace:** `/home/zer0null/reserach extarctor` · **Target (READ-ONLY, never written):** `/home/zer0null/Duval`
**Date:** 2026-10-15 · **Hard bound:** max 30 tool calls (used 22).

## Purpose (one)
Correct the overstatement in the workspace, and record the read-only copy as an owed correction.

## Defect
`strategy/PAPER_CANDIDATES.md:269` asserted as a **universal**: *"Every correction moved the affected arm
DOWN (0.3158 → 0.2947 → 0.2632) — defects were flattering the candidate."* False as a universal.

## Step 1 — re-verification (performed, not trusted)
`python3` over `/home/zer0null/Duval/docs/research/EXP#12-evidence/DEFECT-EVIDENCE.json`:

| Arm | pass1_buggy_order_probe | final | movement |
|---|---|---|---|
| `setfit-mpnet` | 0.315789 | 0.263158 | **DOWN** |
| `modernbert-base` | **0.342105** | **0.347368** | **UP** |

`.setfitIntermediates.variants[0..2].accuracy` = 0.3158, 0.3158, 0.2947 → final arm
`eval-setfit-mpnet.json .accuracy` = **0.2631578947368421** (0.2632 is a rounding). **Both movements match
the work order exactly — no stop-and-report condition was met.**

## Step 2 — occurrence sweep
| Location | Universal form? | Action |
|---|---|---|
| `strategy/PAPER_CANDIDATES.md:269` (A3 evidence bullet) | yes | **FIXED**, M12 retained and narrowed |
| `strategy/PAPER_CANDIDATES.md:~914` (§E O-1 runner-up) | yes | **FIXED** |
| `strategy/SOCIAL_PRESENCE.md:73` | yes | **not touched — out of declared write paths** |
| `strategy/SOCIAL_PRESENCE.md:263` | yes | **not touched — out of declared write paths** |
| `strategy/SOCIAL_PRESENCE.md:919` | yes | **not touched — out of declared write paths** |
| `papers/encoder-crossover-190/` | claim present but **already narrowed** (`CLAIMS.md:122` DISAGREES row, `MANUSCRIPT.md:43–44`, `CHECKLIST.md:117–119`) | **not touched (UPAPER1b's unit)** |
| `/home/zer0null/Duval/docs/research/experiments/LEARNINGS.md:279–281` (read-only) | general clause only; singular "it" already SetFit-scoped | **owed row 6** |
| `/home/zer0null/Duval/docs/research/FINDINGS_REGISTER.md` | **no occurrence** (`grep` for M12/correction/defect/flatter returned only unrelated EXP#11 items) | no row |

## Step 3 — fix
`strategy/PAPER_CANDIDATES.md` A3 bullet now states: `setfit-mpnet` moved **down** (0.3158 → 0.2947 →
0.2632, with file paths), `modernbert-base` moved **UP** (0.342105 → 0.347368), and the correct reading —
an **asymmetric** instrument bias that **inflated the gap between the arms** by depressing the weakest arm
most. **M12 kept, narrowed, not deleted.** Errata header entry added and both edits carry
`[corrected by UCORR3 per UCORR3 re-verification, 2026-10-15]`.

## Step 4 — dependents on the universal form
**1 argument cited it as supporting evidence:** the §E O-1 runner-up encomium for #3 ("three defects all
moved the candidate DOWN") — now re-worded. **No conclusion depends on it:** A3's rank/thesis and the §E
**pick** (#4 over #3) rest on claim narrowness and citation pool, not on the direction of the defects, so no
re-argument is forced. Inside the workspace, `strategy/SOCIAL_PRESENCE.md:73` uses the same claim as part of
its argument for #1's credibility — **unfixed, needs its own unit** (see below).

## Step 5 — owed row
`experiments/second-labeller-190/OWED_CORRECTIONS.md` — appended **item 6** (`LEARNINGS.md:279–281`) in the
existing format (path · line · verbatim current text · correct value · evidence · owed/deliberately not
applied); Summary table row 6 added; `Owed: 5` → **`Owed: 6`**; header "0 of 5" → "0 of 6".
**Explicitly narrowed:** the singular "it" at `:281` already scopes the chain to SetFit — that chain is kept
intact and LEARNINGS is **not** accused of an error it did not make. Only the general clause is owed.

## Step 6 — FINDINGS_REGISTER
No occurrence of the universal claim → **no additional owed row.**

## Remainder (partial scope, named)
`strategy/SOCIAL_PRESENCE.md:73, :263, :919` still carry the universal form. They are **workspace** files,
so they are **not owed to the corpus** — they need a follow-up unit with those paths declared.

## Write paths
`strategy/PAPER_CANDIDATES.md`, `experiments/second-labeller-190/OWED_CORRECTIONS.md`,
`orchestration/units/UCORR3.md`, `orchestration/handoffs/UCORR3.json`. Nothing else touched; target never
written.

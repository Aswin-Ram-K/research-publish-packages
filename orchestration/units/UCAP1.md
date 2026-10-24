# UCAP1 — apply the one JOSS correction; write the `strategy/` index

**Unit:** UCAP1 · **Date:** 2026-10-14 · **Workspace:** `/home/zer0null/reserach extarctor`
**Target:** `/home/zer0null/Duval` — **not opened by this unit** (no read, no write, no git).

## Purpose (one)

Close the single remaining verification correction on `strategy/PUBLICATION_STRATEGY.md`, then write
`strategy/README.md` — a short index that tells a reader **what in this folder has been independently
verified and what has not.**

## Hard bound

**40 tool calls maximum.** Stop and report `partial` if exceeded. **Used: 21.**

## Declared write paths

- `strategy/README.md` (new)
- `strategy/PUBLICATION_STRATEGY.md` — **the one sentence at L185 only**
- `orchestration/units/UCAP1.md`
- `orchestration/handoffs/UCAP1.json`

## Task 1 — the correction

UVER1 returned `pass-with-corrections` for `PUBLICATION_STRATEGY.md` with exactly one `overstated`
item: L185 derived the JOSS six-month unblock date from **commit history alone**, while §11.10 concedes
the repository's **public** visibility — the thing JOSS actually measures — is `UNVERIFIED`.

Applied, verbatim to UVER1's suggested value:

- `≈2027-03-28` → **`2027-03-29`** (the "more than six months" reading puts the earliest compliant
  date one day later than the stated one).
- Added the condition: *"and only if the repository has been publicly available since 2026-09-28 — a
  premise that is itself `UNVERIFIED` (§11.10); if public availability began later, the gate clears
  later."*
- Added the traceability marker **`[corrected by UCAP1 per UVER1]`**, per this corpus's append-only
  errata norm.
- The sentence's existing point is **intact**: arXiv postings remain JOSS's research-use references.

**Nothing else in the file was touched.** Verified: the file moved **406 → 408 lines**, and
`grep -n '2027-03-28\|2027-03-29'` shows only L185 changed. The other three occurrences of the old
unqualified date (L24, L209, L292) were **deliberately left** and are recorded as a known defect in
`strategy/README.md` §6 for a separate unit — the mandate was one line, and silent edits are the
failure mode this corpus names.

## Task 2 — the index

`strategy/README.md` (103 lines, ≤120 as required) maps all **seven** files and, critically, does not
copy the brief's `Verified?` column on trust. Each cell was checked against
`orchestration/handoffs/{UP1,UP2,UV1,UH1,UH2,US1,UVER1,UCORR1}.json`:

| File | Brief implied | Record actually supports |
|---|---|---|
| `VISA_INDIA_EUROPE.md` | `pass`, zero contradicted | **Yes** — UVER1, independent, 26 claims re-fetched |
| `PUBLICATION_STRATEGY.md` | `pass-with-corrections` | **Yes** — UVER1, one correction, applied here |
| `VISA_US_ROUTES.md` | "CFR citations independently re-verified against 8 CFR 214.2" | **No.** UH1 verified the CFR text itself; **no independent verifier unit exists for this file.** UVER1/UV1 opened 214.2 for the O-1 paragraphs, not for `(h)(8)(iii)(F)(4)`, which is what this document turns on. |
| `PAPER_CANDIDATES.md` | "statistics independently spot-verified (EXP#11/#12/#7, 9,260 rows)" | **No independent verifier.** UCORR1 re-checked those statistics and **UCORR1 is the author of the corrections** — author-checked, not independent. The 9,260-row figure traces to `GATED_READ_2026.md`, not to a verifier. |
| `PAPER_CANDIDATES_SUPPLEMENT.md` | "top finding independently confirmed by the orchestrator (V13 / arXiv 2608.03836)" | **Not in this record.** The V13 finding is sourced from the corpus's own `SOURCE_VERIFICATION.md:35`. UP2's own handoff asks for a verifier to confirm it; none was run. |
| `SOCIAL_PRESENCE.md` | two claims verified at source | **Yes, author-verified** — US1 fetched both; **no independent re-check.** |
| `VERIFICATION_REPORT.md` | — | This *is* the verification. |

This asymmetry is stated plainly in the index rather than smoothed over: **two of seven files have
been through an independent verifier; five rest on their authors' own measurements.**

The index also carries the three first actions, an honest "what is NOT done", the not-legal-advice
line for both visa documents, and a §6 of defects recorded but not fixed.

## Other errors found while reading (NOT fixed — recorded for a separate unit)

1. **`PUBLICATION_STRATEGY.md` L24, L209, L292** still carry the unqualified `≈2027-03-28` that UVER1
   flagged at L185. Cosmetic and non-decisional, but now inconsistent with L185.
2. **`PAPER_CANDIDATES_SUPPLEMENT.md` §7 cites pre-UCORR1 line numbers.** UCORR1 grew
   `PAPER_CANDIDATES.md` from 710 to 970 lines, so the supplement's anchors (`:62–64`, `:107–147`,
   `:295–336`, `:583–620`) no longer resolve — A1 is now ~105, A2 ~198, §D 793. The supplement also
   never received a post-correction errata header, unlike its companion.

A third observation, about the task brief rather than a document: four of the seven `Verified?` cells
in the brief assert verification the handoffs do not record. Anyone quoting that table downstream
should quote `strategy/README.md` §1 instead.

## Containment

No command in this unit touched `/home/zer0null/Duval`; no `git` was run at all; no process was
started; no file outside the four declared write paths was modified.

## Evidence commands

```
sed -n '170,214p' strategy/PUBLICATION_STRATEGY.md          # the sentence before the edit
for f in UP1 UP2 UV1 UH1 UH2 US1 UVER1 UJC1; do cat orchestration/handoffs/$f.json; done
grep -rln "214.2(h)(8)(iii)(F)" orchestration/               # only UH1's own card + handoff
grep -rln "VISA_US_ROUTES\|PAPER_CANDIDATES_SUPPLEMENT\|SOCIAL_PRESENCE" orchestration/handoffs/
grep -rln "2608.03836" --exclude-dir=state .                 # no independent confirmation in orchestration/
grep -n "2027-03-28\|2027-03-29" strategy/PUBLICATION_STRATEGY.md   # L24/L185/L209/L292
wc -l strategy/PUBLICATION_STRATEGY.md                       # 406 -> 408
wc -l strategy/README.md                                     # 103
```

## Next

A fresh unit should (a) apply the L24/L209/L292 residue as a second dated errata line, (b) add an
errata header to `PAPER_CANDIDATES_SUPPLEMENT.md` and re-anchor its §7 citations to the post-UCORR1
file, and (c) — the real gap — run the independent verifier that `VISA_US_ROUTES.md`,
`PAPER_CANDIDATES.md` and `PAPER_CANDIDATES_SUPPLEMENT.md` have never had.

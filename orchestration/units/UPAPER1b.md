# UPAPER1b — write the submission-ready manuscript for candidate #3 (encoder crossover)

**One purpose:** produce the submission-candidate manuscript for `PAPER_CANDIDATES.md` §A3 plus its
submission checklist, open questions and bibliography, from the already-verified numbers in
`papers/encoder-crossover-190/{CLAIMS,EVIDENCE_NOTES,GAPS,REFS}.md` (unit UPAPER1a).

**Hard bound:** maximum 55 tool calls. **Used: ~42.** Stop-and-report-`partial` if exceeded.

**Write paths (declared, touched nothing else):**
- `papers/encoder-crossover-190/**`
- `orchestration/units/UPAPER1b.md`
- `orchestration/handoffs/UPAPER1b.json`

## Inputs
`CLAIMS.md` (76 rows; the source of truth for every number), `EVIDENCE_NOTES.md` (commands + verbatim
outputs), `GAPS.md` (four gaps, three escalated decisions), `REFS.md` (4 sourced, 4 unsourced). Target
`/home/zer0null/Duval` strictly read-only.

## Binding constraints carried (from the unit card's verifier)
1. Latency **DROPPED** — `latency_claim_supportable = no`; stated in Limitations §6.1 with the four reasons.
2. κ = 0.9014 is **machine reproducibility of the fixture**, never IAA; human labeller owed; §F.3 not discharged.
3. "paired is conservative" **never used**; paired MDE (0.1595) is the **larger** figure (ψ=0.616, 0.85×).
4. `DISAGREES` row carried: only **SetFit** moved down (0.3158→0.2947→0.2632); **modernbert-base moved UP**
   0.342105→0.347368.
5. Baseline ambiguity explicit: 0.32 ← 0.6684; Δ = −0.3316 ← 0.6789.
6. ECE convention **flagged, not resolved** (F3 flips on 0.0551 vs 0.1547).
7. `imajev 0.645` is the **H-A corpus stratum**, not a fixture number (fixture figure 0.6368).
8. `deberta-v3-base` **did not train** — said plainly, excluded from the headline.
9. Every abstract number names its control and what it returned; numbers with no control removed.
10. References: sourced only in `REFERENCES.bib`; unsourced listed in `OPEN_QUESTIONS.md`. Core literature
    claim read in `DECIDER_STACK_DECISION.md` §11.6 + commit `ad301ae` — **it does support the claim**, as an
    internal verified-absent errata whose search protocol is unrecorded.

## Deliberately not decided
The primary baseline — withheld by instruction. **Subsequently declared by the author on 2026-10-15:
0.6789 (same-run)**, so all `PENDING AUTHOR SIGN-OFF` markers were retired and replaced with the dated
declaration; the 7 sentences that would change on revisiting are kept in `MANUSCRIPT.md` §3.3 and
`OPEN_QUESTIONS.md` Q1. The title's "by 0.32" was changed to **"by 0.33"** (0.3316, the declared primary
figure) and flagged in the title block and `CHECKLIST.md` §1.

## Read-only discipline
Target HEAD before = after = `907fa39da7ba8ecfbe6e976b7a4cddadea7ac36b`. `git status --porcelain` = 4
untracked paths before and after (`?? .ci-trunk.txt`, `?? .relay/`,
`?? docs/evidence/selfbuild/relay-outbound-2026-10-13.txt`, `?? docs/migration/`) — **not this unit's**;
attributed to an unrelated concurrent session (relay artefacts). No writes, no git state changes.

# UCHECK1 — Full-text citation fetch verification

**Purpose (one):** Settle, from FULL TEXTS (not abstracts), whether `arXiv:2512.12677` prints the
ModernBERT throughput/distillation figures the paper attributes to it, and whether `arXiv:2602.06370`
contains the "N-dependent crossover table" characterisation. Plus 3 control spot-checks on figures UCITE1
already verified verbatim, to show the method can return "found".

**Predecessor:** UCITE1 (`strategy/CITATION_SUPPORT_AUDIT.md`) — checked abstracts only.

**Deliverable:** `strategy/CITATION_FETCH_VERIFICATION.md`

**Method bound:** 20 tool calls total. Per claim: if full text not reached in 4 attempts, record
UNRESOLVED and move on. Never assert "X does not print Y" from an abstract.

**Write paths (only):** `strategy/CITATION_FETCH_VERIFICATION.md`, `orchestration/units/UCHECK1.md`,
`orchestration/handoffs/UCHECK1.json`, `scratch/ucheck1/**`.

**Constraints:** `/home/zer0null/Duval` read-only, no bare `git status` against it, never write
`/home/zer0null/research-publish-packages`. Report only — edit nothing under `papers/`.

## Status log
- Done. Both full texts reached via arXiv native HTML renderer on the first attempt.
- CLAIM 1 (`arXiv:2512.12677v3`, 357,024 B): ALL 9 terms FOUND in body + Table 3 + Table 13. UCITE1's
  MIS-CITED-1 REFUTED — an abstract-only false positive.
- CLAIM 2 (`arXiv:2602.06370v1`, 423,961 B): all 6 cited figures FOUND (UCITE1 abstract assertion refuted);
  strings `N-dependent` and `crossover` ABSENT (0 hits). Verdict MIXED — label is the corpus's coinage.
- Controls: Simmering blog (64,330 B) 6/6 found; 3/3 required spot-checks (89.2/87, 93.1/152, 42 ex/s) CONFIRMED.
- 10 tool calls of 20 used. Nothing UNRESOLVED.

## Handoff
See `orchestration/handoffs/UCHECK1.json` (unit shape, valid JSON).

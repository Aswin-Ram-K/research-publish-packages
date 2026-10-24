# UPLAG2 — Originality audit, gaps 1–3 and two open questions

**Purpose (one):** close the three coverage gaps UPLAG1 named in `strategy/ORIGINALITY_CHECK.md` §7 and
settle the two open questions UPLAG1 left unresolved, extending — never repeating — that audit.

**Deliverable:** `strategy/ORIGINALITY_CHECK_SUPPLEMENT.md`

**Hard bound:** 25 tool calls. Stop and report `partial` with the remainder named if exceeded.

**Write paths (nothing else):** `strategy/ORIGINALITY_CHECK_SUPPLEMENT.md`, `orchestration/units/UPLAG2.md`,
`orchestration/handoffs/UPLAG2.json`, `scratch/uplag2/**`.

**Constraints:** read-only. `/home/zer0null/Duval` READ-ONLY (read files, never bare `git status` against it).
Never write `/home/zer0null/research-publish-packages`. Report only — edit nothing under `papers/`.
State the sample size of every probe; never present a sample as a scan. Quote exactly when flagging.

**The three gaps (as UPLAG1 named them):**

1. **Published-prose population untested.** UPLAG1 got HTTP 404 on the author's public repo
   `Aswin-Ram-K/publish-present-compete`. Local proxy: `/home/zer0null/Duval/docs/research/PAPER_DERIVATION.md`,
   verified byte-identical (sha256 `d98c4359d37b987db07707e0b96358de0cd280c979896c6a15858d96bcd14802`,
   46,636 B) to that repo's `findings/PAPER-DERIVATION.md` while public. Re-run the 8+-word prose n-gram
   comparison (sampled, size stated), report hits with line numbers on both sides, then interpret as a
   **disclosure** question (document was public under MIT, author's own prose). Also sweep
   `/home/zer0null/Duval/docs/` for other likely-public prose and say what populations were reachable.
2. **Only 2 of 13 cited sources fetched.** Fetch full text where openly reachable and probe with the same
   method: GLiNER2 `arXiv:2507.18546`, GLiClass `arXiv:2508.07662`, Kostina `arXiv:2501.08457`, Li
   ACL-Industry 2025, Benayas `10.1007/s10579-024-09796-y` (CC-BY preprint `rs-3865391/v1.pdf`), PriDe
   `arXiv:2309.03882`, GCD `arXiv:2305.13971`. For each: reached? how? probed what? hits? and whether the
   manuscript's description is a fair summary or an overreach (citation integrity).
3. **`submission/main.tex` never audited.** Prose present in one and not the other, quotations and
   attribution, leaked internal notes (drafting banner, title-revision note) — quote exact lines.

**Also settle:**

- **Licence contradiction.** `papers/encoder-crossover-190/LICENCE_TODO.md` "do not publish until resolved"
  vs `MANUSCRIPT.md:790-800` "subset ships with the paper". Read both, quote both, name the smallest
  decision that closes it. Do not edit either file.
- **Third-party model attribution.** Which model each arm used, where the paper names it, what citation /
  licence line each conventionally requires (ModernBERT-base Apache-2.0, deberta-v3-base MIT,
  all-mpnet-base-v2 Apache-2.0, decider 4B base unnamed, `mimo-v2.6-flash` uncited).

**Method:** 8+ distinct-word prose n-gram extraction with markdown stripping (same family as UPLAG1's
9-gram `scratch/uplag1/overlap.py`); sampled probes, sample size stated per probe; line numbers on both
sides; verbatim quotes for every flag; `main.tex` compared mechanically against `MANUSCRIPT.md`.

**Status:** in progress.

# CHECKLIST.md — submission checklist for candidate #3 (encoder crossover)

Unit **UPAPER1b**. Manuscript: [`MANUSCRIPT.md`](MANUSCRIPT.md).
Target `the read-only target repository` was **read-only** for this unit: HEAD before and after
`907fa39da7ba8ecfbe6e976b7a4cddadea7ac36b`, no writes, no `git` state changes.

---

## 1. ✅ PRIMARY BASELINE DECLARED — 0.6789 (same-run)

**Decided by the author on 2026-10-15.** The manuscript is written against **0.6789 as primary**; **0.6684 is
reported as a secondary / robustness figure** tied to its pre-registration role. **No baseline sign-off
remains open.**

| | same-run **0.6789** — ✅ **DECLARED PRIMARY** | historical **0.6684** — **secondary / robustness** |
|---|---|---|
| auditability | **per-case rows re-score exactly** (`reproducesAt3dp = true`, `absDiff = 4.7e−05`) | **cannot be re-scored** — `REPORT.md:104` `reproduces at 3 d.p. = None`, `:189` no rows survive |
| paired test | **is** the McNemar partner (same 190 cases, same option orders) | not the partner |
| pre-registration | F1 was written against 0.6684, not this | **is** the pre-registered F1 threshold (`EXP#12…:95`, `REPORT.md:85`) |
| headline produced | Δ = **−0.3316** | **0.3210** ≈ "0.32" |

- **Draft uses 0.6789** (auditable, paired partner) — **declared primary, not pending.** The former
  `[PENDING AUTHOR SIGN-OFF]` markers were **retired**; the manuscript's title block now carries the dated
  declaration instead.
- **⚠ Title figure changed, deliberately and flagged.** The working title's *"by 0.32"* was the **0.6684**
  arithmetic (`0.6684 − 0.3474 = 0.3210`). This draft's title uses **"by 0.33"** = **0.3316**, the declared
  primary baseline's figure. If a reviewer prefers the original, that is the one sentence to revert —
  everything else is already bound to its baseline.
- **Conclusion is unchanged either way**: 0.3474 loses to both, and −0.3316 > 2× either MDE (2.079× paired,
  2.446× unpaired).
- **Every number in the manuscript now names the baseline it uses** — mapping table in `MANUSCRIPT.md` §3.3
  (headline Δ, paired McNemar → 0.6789; F1 and the "0.32" arithmetic → 0.6684).
- **The 7 sentences that would change if the declaration were ever revisited** (0.6684 promoted) are kept in
  `MANUSCRIPT.md` §3.3 and repeated in `OPEN_QUESTIONS.md` Q1. A reader must be able to find every affected
  sentence from this file.

## 2. Latency — **DROPPED**

- ❌ No latency number appears in the abstract or in Results. ✅ Limitations §6.1 states it was **out of
  scope and why**.
- Reason: `latency_claim_supportable = no`. The heads were timed **locally on a GB10 in one forward batch**
  (12.37 / 14.16 / 11.96 / 12.46 / 0.003 ms) while the 4B figures come from a **served stack's stored rows**
  (53.06 ms); the F6 threshold is a **pre-registered constant** (0.075 s/decision from `DECIDER_TIER §2`),
  not a measurement; and the **same 4B spans 53.06 / 72.85 / 106.92 ms** across strata, a 2× spread that
  shows the timing was uncontrolled.
- Closing it requires re-measuring a 4B decider on the same host under the same per-decision protocol. Until
  then, **do not present the comparison** — it is not like-for-like.

## 3. arXiv metadata

| field | value | status |
|---|---|---|
| title | *The small-encoder crossover is a prompted-baseline artefact: a fine-tuned encoder head loses to a fine-tuned 4B decision model by 0.33 and to a majority-class control* (working title said "by 0.32"; see §1) | draft |
| abstract | `MANUSCRIPT.md` §Abstract — every number in it names its control and what that control returned; numbers with no control were removed | draft |
| primary category | **`cs.LG`** (likely) | ⚠ **UNVERIFIED** — not confirmed |
| cross-lists | `cs.CL`, `cs.AI` | **proposed, unverified** — a human should confirm |
| **endorsement** | **arXiv requires endorsement** for a first submission in this area | ⚠ **action required** |
| `cs.LG` its own endorsement domain? | **UNVERIFIED** | ⚠ a human must check; do not assume `cs.LG` endorsement transfers or is self-contained |
| licence | **NOT CHOSEN** | ⚠ **see §4 below** |

**Action:** obtain endorsement *before* the deadline, and confirm the primary/cross-list categories from the
arXiv taxonomy rather than from this table.

## 4. ⚠ Licence mismatch — a deliberate choice, not a default

- The **code and evidence** in the target repo are **AGPL-3.0** (`the read-only target repository/LICENSE`, GNU Affero
  GPL v3, 19 Nov 2007).
- The **paper's licence is a separate, deliberate choice** and is currently **unchosen**.
- Publishing the manuscript under a permissive licence (e.g. CC-BY-4.0, the arXiv default-ish expectation)
  while its supporting code is AGPL-3.0 is a **real mismatch** — the paper's reproduction path points at an
  AGPL-3.0 repository. It may be perfectly fine (AGPL covers code, not the prose), but it must be a
  **stated decision**, not an accident.
- **Flag carried into the manuscript** (`Data and code availability`) and into `OPEN_QUESTIONS.md`.
- Also: the fixture and evidence tree are **another project's** recorded work; confirm the right to publish
  excerpts and quotations with that project's owner.

### 4.1 ✅ DECIDED: licence = **CC BY 4.0** — *[added by ULIC, 2026-10-15]*

**Author decision, relayed 2026-10-15: OPEN PAPER + WITHHELD IMPLEMENTATION** — the paper is posted under
**CC BY 4.0**; code, model weights and data are **not released**. Full evidence, the option table and the
reasoning are in [`LICENSE_ANALYSIS.md`](LICENSE_ANALYSIS.md) (**this unit's deliverable** — read it before
touching §4 again).

- **Why CC BY 4.0 and not a restrictive option:** TMLR requires CC BY 4.0 *"from the time of submission to
  final publication"* (`https://jmlr.org/tmlr/author-guide.html`, fetched 2026-10-15, verbatim). arXiv's
  licence for a posted version is *"irrevocable and cannot be changed"*
  (`https://info.arxiv.org/help/license/index.html`, fetched 2026-10-15, verbatim). **CC BY 4.0 is the only
  option on arXiv's menu compatible with a TMLR submission.** See `LICENSE_ANALYSIS.md` §1.4.
- **The mismatch in §4 above is now resolved by decision, not by accident:** paper CC BY 4.0, code AGPL-3.0
  (still true, `LICENSE` + `package.json:122`). The decision is recorded; it is no longer an accidental
  pairing.
- **The AGPL concern is CLOSED, and a leak that did not happen must not be "discovered" later.**
  `the source repository's GitHub URL` returns **HTTP 404** and
  `the source repository's GitHub API URL` returns **HTTP 404** (both 2026-10-15); the account's
  public repo listing contains no `the source repository`. The code has **never been public**, so **AGPL-3.0 has
  triggered no obligation to the public** — its source-offer duty runs to network users, and there are none.
  Keeping the repository private is fully consistent with the decision. `LICENSE_ANALYSIS.md` §1.6.
- **⚠ New, still-open item — the disclosure scope (D2 in `LICENSE_ANALYSIS.md` §10).** "Code/weights/data
  withheld" is in tension with the manuscript's own availability claims, which still say everything is
  "re-derivable from the target repository `the read-only target repository`". The concrete list of sentences that
  conflict, and the recommended minimal reproducibility subset, are in `LICENSE_ANALYSIS.md` §8. **The real
  lever is this, not the licence.**
- **⚠ Also new:** `the read-only target repository/CITATION.cff` names `repository-code:
  "the source repository's GitHub URL"` — a URL that **404s for any reader**. The paper must not send
  reviewers to it.
- **Whatever owns `MANUSCRIPT.md` must correct `:606–608`** — the sentence *"the paper's own licence is a
  separate, deliberate choice that a human must still make"* is now **factually wrong**. This unit did not
  edit `MANUSCRIPT.md`.

## 5. The four owed fixture repairs (§A3 "What is missing" items 1–4)

All four remain **OPEN**. None is a reason to invent a number.

1. **One fixture, one worker.** 190 cases, 721 options, 74 labels (51 occurring once), authored by one
   worker, carrying its own flagged decidability weak points. Mitigated *only* by a **model**
   second-labeller (agreement 0.9053, κ 0.9014) — **not** IAA. **An independent human labeller is still
   owed, and `PAPER_CANDIDATES.md` §F.3 is not discharged** (several candidate papers share this fixture, so
   one flaw propagates into four papers). A second fixture — ideally an external typed-decision benchmark —
   was searched for and **not found anywhere in the corpus**.
2. **Latency is not like-for-like** — see §2. Resolved for *this* paper by **dropping** the claim, not by
   fixing the measurement.
3. **Only three encoder families** (ModernBERT-base 149M, DeBERTa-v3-base 184M, SetFit-MPNet 109M), all
   109M–184M. A fourth arm — **a trained linear probe on a frozen LLM embedding** — was **not run** and
   appears **nowhere** in the evidence tree. Run it, or state its absence (we state it, §6.5).
   - Sub-caveat: **`deberta-v3-base` did not train** (train loss 1.1288 → 1.1235; dev 0.50 → 0.495 vs dev
     majority-class 0.475). The manuscript says so plainly and excludes it from the headline.
4. **Primary baseline not declared** — see §1. The manuscript argues both are beaten, which is true, but the
   declaration is owed before submission.

## 6. Owed corrections — `experiments/second-labeller-190/OWED_CORRECTIONS.md`

**Status: OWED, deliberately NOT applied** (the target is read-only; 0 of 5 refuted by UFIX4's raw re-read).
Of the five, **four are repairs to the fixture file itself** and one is a register correction:

| # | corpus path:line | defect | correct value |
|---|---|---|---|
| 1 | `docs/research/FINDINGS_REGISTER.md:47` | wrong imajev row count (3,590) | **3,690** (the only unambiguous factual correction) |
| 2 | `evals/fixtures/reflex-decisions.ts:839–847` (`capability.family-010`) | label in tension with its own rationale | none asserted — flag for subject review |
| 3 | `evals/fixtures/reflex-decisions.ts:329–338` (`worker.class-023`) | self-contradictory premise (no option derivable) | none asserted — flag for subject review |
| 4 | `evals/fixtures/reflex-decisions.ts:773–782` (`capability.family-004`) | self-containment gap (invariant only in the rationale) | none asserted — flag for subject review |
| 5 | `evals/fixtures/reflex-decisions.ts:1872–1881` (`topology-018`) | self-containment gap **plus** stated facts satisfy `PARALLEL(A,B)` while the record says `SEQUENCE(A,B)` | none asserted — flag for subject review |

**Why the paper must carry them:** items 3 and 5 are cases where the fixture's stated facts arguably point at
a *different* answer than the record. That is a **label-level** weakness in the instrument, and it caps how
strongly any accuracy number can be read. The manuscript's §6.2/§6.3 says the fixture carries known flagged
decidability weak points; a submission should also name these five specifically.

## 7. Corrections the manuscript must carry (verifier-mandated)

- [x] **`DISAGREES` M12 carried.** "Every correction moved the affected arm DOWN" is **false as a
  universal**. `modernbert-base` moved **UP** — **0.342105 → 0.347368** — when the order-probe bug was
  fixed; the downward chain **0.3158 → 0.2947 → 0.2632** is **`setfit-mpnet` only**. Stated in the abstract,
  §4.2 and §5.3. **`PAPER_CANDIDATES.md:269` / `LEARNINGS.md:281` must not be repeated as written.**
- [x] **"paired is conservative" never used.** ψ = 0.616, `unpaired/paired = 0.85×`, so the **paired MDE
  (0.1595) is the LARGER** figure here. The manuscript states the numbers and says the M11 *requirement*
  stands while the *justification* does not (§4.5).
- [x] **Baseline ambiguity explicit** — 0.32 ← 0.6684 (secondary); Δ = −0.3316 and title "0.33" ← 0.6789
  (declared primary); §3.3 mapping table, §4.2, abstract, title block.
- [x] **κ = 0.9014 never called IAA** — "machine reproducibility of the fixture"; human labeller owed (§6.2).
- [x] **ECE convention flagged, not resolved** — F3 flips between 0.0551 and 0.1547 (§4.6).
- [x] **`imajev 0.645` is the H-A corpus stratum, not a fixture number** (fixture figure 0.6368) — §2.2,
  §4.7; 0.645 appears in no fixture table.
- [x] **`deberta-v3-base` did not train** — said plainly, excluded from the headline (§3.2, §6.5).
- [x] **Every abstract number names its control**, or was removed.
- [x] **No fabricated references** — only the 4 sourced external identifiers + the internal corpus document
  are in `REFERENCES.bib`; the 4 unsourced ones are in `OPEN_QUESTIONS.md`.

## 8. Pre-submission mechanical checks

- [x] Primary baseline declared (**0.6789**, author decision 2026-10-15) and every number bound to its
      baseline (§1, `MANUSCRIPT.md` §3.3).
- [ ] Licence chosen and the AGPL-3.0 mismatch resolved or explicitly accepted (§4).
- [x] **Licence chosen: CC BY 4.0** (author, 2026-10-15). *[added by ULIC, 2026-10-15]* The AGPL mismatch is
      resolved **by decision**: paper CC BY 4.0, code AGPL-3.0 and private (§4.1;
      [`LICENSE_ANALYSIS.md`](LICENSE_ANALYSIS.md) §2, §1.6).
- [ ] ⚠ **BLOCKING FOR SUBMISSION — the TMLR conflict + the disclosure scope.** *[added by ULIC, 2026-10-15]*
      CC BY 4.0 satisfies TMLR's *"All TMLR submissions, from the time of submission to final publication, are
      licensed under CC BY 4.0"* (fetched 2026-10-15), but **arXiv's licence for a posted version is
      irrevocable** — so a restrictive first posting is not recoverable, and the sequencing rule is
      **licence-at-first-posting**. Separately, the manuscript's *"re-derivable from the target repository"*
      claims contradict the withheld-implementation decision and must be reframed before submission.
      See [`LICENSE_ANALYSIS.md`](LICENSE_ANALYSIS.md) §1.4 (conflict), §8 (the exact conflicting sentences and
      the recommended minimal reproducibility subset), §10 D2 (open).
- [ ] Endorsement obtained; `cs.LG` primary and `cs.LG`-as-endorsement-domain confirmed (§3).
- [ ] An independent **human** labeller is run, or §6.2 is kept and the claim stays fixture-bound.
- [ ] The 7 sentence-level changes are made consistently in abstract, §4.2, §5.1, §6.3 and `REFERENCES.bib`.
- [x] Every number in the manuscript traces to `CLAIMS.md` or to a command in `EVIDENCE_NOTES.md`.
- [x] Reproduction commands include the **U+2212 minus** grep gotcha.

## 9. Read-only discipline record

- Target HEAD before: `907fa39da7ba8ecfbe6e976b7a4cddadea7ac36b` · after:
  `907fa39da7ba8ecfbe6e976b7a4cddadea7ac36b`.
- `git status --porcelain` **before** (4 entries) and **after**: `?? .ci-trunk.txt`, `?? .relay/`,
  `?? docs/evidence/selfbuild/relay-outbound-2026-10-13.txt`, `?? docs/migration/`.
- **Attribution:** these four untracked paths are **not this unit's** — they belong to an unrelated
  concurrent session (`.relay/`, `relay-outbound-*` are relay artefacts). This unit created no file and
  changed no git state inside `the read-only target repository`.

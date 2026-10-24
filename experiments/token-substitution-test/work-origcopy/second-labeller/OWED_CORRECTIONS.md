# OWED CORRECTIONS — the read-only corpus (durable record)

**Status: OWED, deliberately NOT applied.** Every defect below lives in the **read-only** target repo
`/home/zer0null/Duval` (or in a corpus document declared read-only for this workspace). No unit of this
workspace may write there, so these are recorded here rather than fixed.

**Compiled by:** UFIX4, 2026-10-15, from the UVER3 work order (`strategy/VERIFICATION_REPORT_3.md`) and
the prior units named per item (UVER2/UCORR2, UEXP, UCORR1).

**Verification rule used.** Each item was **re-opened in the raw corpus text by UFIX4** and re-measured
before being listed. Nothing is repeated on trust. The verification actually performed is given per item,
with the observed text. **Items that did not hold up would be reported as refuted here: 0 of 6 were
refuted.** (Item 6 was appended by UCORR3, 2026-10-15, re-verified raw; items 1–5 were verified by UFIX4.)
(The one correction that *was* applied — `strategy/PUBLICATION_STRATEGY.md:46` — is a
**workspace** document, not a read-only corpus file, and is therefore not owed; it was corrected in place
by UFIX4 per UVER3, marked `[corrected by UFIX4 per UVER3]`.)

---

## 1. `FINDINGS_REGISTER.md:47` — wrong imajev row count

- **Path / line:** `/home/zer0null/Duval/docs/research/FINDINGS_REGISTER.md:47`
- **Current text (verbatim fragment):** `| **F-EXP11-11** | **\`answer ∉ option set\` was 0.00 % at every round in both models** … | confirmed | \`answerInOptionSet\` across all 4,090 decider rows and 3,590 imajev rows |`
- **Correct value:** **3,690** imajev rows, not 3,590.
- **Established by:** UVER2 / UCORR2 (per the UVER3 work order). **Re-verified by UFIX4:**
  `/home/zer0null/Duval/docs/research/EXP#11-evidence/imajev-rows.jsonl` → `wc -l` = **3690**; all 3,690
  non-empty lines parse as JSON (**0 unparsable**); **6 distinct rounds**. 3,590 was a **mid-run
  snapshot**, superseded by the complete file.
- **Consistency note:** this register row is quoted verbatim in
  `experiments/second-labeller-190/RUN.json` under `related_measurement.register_quote`; that quote now
  carries a `register_quote_note` pointing at this item, so a reader of the experiment is not left with
  the wrong figure uncorrected.

## 2. `capability.family-010` — label in tension with its own rationale

- **Path / lines:** `/home/zer0null/Duval/evals/fixtures/reflex-decisions.ts:839–847` — `id` at `:839`,
  recorded label `correct: 0` at `:844`, rationale at `:845–846`.
- **Current text (verbatim):** `correct: 0` → option `"model + context"`; rationale: *[withheld rationale quote — see ../REDACTION_REPORT.md section 5]*
- **Correct value:** **none asserted — this is a flag, not a mislabel.** The label is in *tension* with its
  own rationale: the rationale implies the constructed family set contains `tool`, while the recorded
  label omits `tool`. Worth a subject review; the alternative reading (`tool` is present but unspendable)
  would keep the label correct.
- **Established by:** UEXP (`RUN.json` `semantic_flags_detail`, `EVIDENCE.md` §7); independently confirmed
  by UVER3 (report item 8a, line 78); **re-verified raw by UFIX4** (text quoted above read directly from
  the fixture).

## 3. `worker.class-023` — self-contradictory premise

- **Path / lines:** `/home/zer0null/Duval/evals/fixtures/reflex-decisions.ts:329–338` — question at
  `:332`, options/`correct: 1` at `:333–334`, rationale at `:335–336`.
- **Current text (verbatim):** question: *[withheld rationale quote — see ../REDACTION_REPORT.md section 5]*; recorded answer `editor (attached, writes)`; rationale: *[withheld rationale quote — see ../REDACTION_REPORT.md section 5]*
- **Correct value:** **none asserted — flag for subject.** The question's premise is impossible as written
  under the fixture's own rule, so no option is derivable from the question alone. Either the premise or
  the rationale must change.
- **Established by:** UEXP (`RUN.json` `semantic_flags_detail`, `EVIDENCE.md` §7); independently confirmed
  by UVER3 (report item 8b, line 79); **re-verified raw by UFIX4**.

## 4. `capability.family-004` — self-containment gap

- **Path / lines:** `/home/zer0null/Duval/evals/fixtures/reflex-decisions.ts:773–782` — question at
  `:775–776`, options/`correct: 0` at `:777–778`, rationale at `:779–780`.
- **Current text (verbatim):** question states a class with
  `[redacted] { kind: 'declared', tools: ['fs.read','fs.write'] }` **and also two skills in its role
  spec**, asking which family set the planner constructs; recorded answer `"model + context + tool"`;
  rationale: *[withheld rationale quote — see ../REDACTION_REPORT.md section 5]*
- **Correct value:** **none asserted — flag for subject.** The recorded answer requires the invariant
  "a skill is not a grant unless the policy emits one", which the **question does not state**. That breaks
  the fixture header's claim that *[withheld rationale quote — see ../REDACTION_REPORT.md section 5]*
- **Established by:** UEXP (`RUN.json` `corpus_documentation`-adjacent flag list, `EVIDENCE.md` §7);
  independently confirmed by UVER3 (report item 8c, line 80); **re-verified raw by UFIX4**.

## 5. `topology-018` — self-containment gap, plus the sharper `PARALLEL`/`SEQUENCE` point

- **Path / lines:** `/home/zer0null/Duval/evals/fixtures/reflex-decisions.ts:1872–1881` — question at
  `:1874–1875`, options/`correct: 2` at `:1876–1877`, rationale at `:1878–1879`.
- **Current text (verbatim):** question: *[withheld rationale quote — see ../REDACTION_REPORT.md section 5]*; recorded
  answer `"SEQUENCE(A,B)"`; rationale: *[withheld rationale quote — see ../REDACTION_REPORT.md section 5]*
- **Correct value:** **none asserted — flag for subject.** Two layers:
  1. **Self-containment gap:** the disambiguating rule ("two-parent commits may only be minted by the
     Reducer") is in the **rationale only**, never in the question, so a reviewer holding only the file
     cannot derive the recorded answer.
  2. **Sharper point (recorded by UEXP):** the question's **own stated facts satisfy `PARALLEL(A,B)`** —
     disjoint paths, no dependency, both required, class attached — while the record says
     `SEQUENCE(A,B)`. The case is therefore not merely incomplete; read literally, its stated facts point
     at the *other* answer.
- **Established by:** UEXP (`RUN.json` `semantic_flags_detail`, `EVIDENCE.md` §7); independently confirmed
  by UVER3 (report item 8d, line 81); **re-verified raw by UFIX4**.

## 6. `LEARNINGS.md:279–281` (flagged line `:281`) — "all three defects flattered the candidate" is false as a general clause

- **Path / lines:** `/home/zer0null/Duval/docs/research/experiments/LEARNINGS.md:279–281` — heading at
  `:279`, general clause (*[withheld rationale quote — see ../REDACTION_REPORT.md section 5]*) at `:280`, correction chain at `:281`.
- **Current text (verbatim):** *[withheld rationale quote — see ../REDACTION_REPORT.md section 5]*
- **Correct value (narrow — do NOT accuse LEARNINGS of an error it did not make):** the **singular "it"
  already scopes the numeric chain to `setfit-mpnet`**, and that chain is **correct and verified** — keep it
  intact. What does not hold is the **general clause**, *[withheld rationale quote — see ../REDACTION_REPORT.md section 5]*: the
  order-probe defect **hurt** `modernbert-base`, which moved **UP** when it was fixed
  (**0.342105 → 0.347368**). The supportable wording is that the defects acted as an **asymmetric**
  instrument bias — they depressed the weakest arm most and so **inflated the gap between the arms** — not
  that every defect flattered the candidate.
- **Established by:** UCORR3. **Re-verified raw:** `DEFECT-EVIDENCE.json`
  `.setfitIntermediates.variants[0..2].accuracy` = **0.3158, 0.3158, 0.2947** (down), final arm
  `eval-setfit-mpnet.json` `.accuracy` = **0.2631578947368421**; and
  `.passes.pass1_buggy_order_probe.arms["modernbert-base"].accuracy` = **0.342105** vs
  `.passes.final.arms["modernbert-base"].accuracy` = **0.347368** (**UP**). The same overstatement is
  carried in the workspace at `strategy/PAPER_CANDIDATES.md` A3 and §E, which UCORR3 **did** correct in
  place (a workspace document, not the read-only corpus, so it is not owed).

---

## Summary

| # | Corpus path:line | Defect | Correct value | Established by | UFIX4 re-verified |
|---|---|---|---|---|---|
| 1 | `/home/zer0null/Duval/docs/research/FINDINGS_REGISTER.md:47` | wrong row count (3,590) | **3,690** | UVER2/UCORR2 | yes — `imajev-rows.jsonl` = 3,690 valid rows |
| 2 | `…/evals/fixtures/reflex-decisions.ts:839–847` | label/rationale tension | none (flag only) | UEXP; UVER3 8a | yes — raw text |
| 3 | `…/evals/fixtures/reflex-decisions.ts:329–338` | self-contradictory premise | none (flag only) | UEXP; UVER3 8b | yes — raw text |
| 4 | `…/evals/fixtures/reflex-decisions.ts:773–782` | self-containment gap | none (flag only) | UEXP; UVER3 8c | yes — raw text |
| 5 | `…/evals/fixtures/reflex-decisions.ts:1872–1881` | self-containment gap; stated facts satisfy `PARALLEL` | none (flag only) | UEXP; UVER3 8d | yes — raw text |
| 6 | `/home/zer0null/Duval/docs/research/experiments/LEARNINGS.md:279–281` | general clause "all three defects flattered the candidate" | defects biased the instrument **asymmetrically** (`setfit-mpnet` down 0.3158 → 0.2947 → 0.2632; `modernbert-base` **up** 0.342105 → 0.347368) | UCORR3 | yes — `DEFECT-EVIDENCE.json` passes + `eval-setfit-mpnet.json` |

**Owed: 6. Refuted: 0.** These six are owed **to a read-only repo** and were **deliberately not
applied** — the target `/home/zer0null/Duval` was never written. Items 2–5 are flags requiring subject
judgement, not asserted mislabels; items 1 and 6 are unambiguous factual corrections.

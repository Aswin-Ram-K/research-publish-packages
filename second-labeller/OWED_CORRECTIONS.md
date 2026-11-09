# OWED CORRECTIONS — the read-only corpus (durable record)

**Status: OWED, deliberately NOT applied.** Every defect below lives in the **read-only** target repo
`the read-only target repository` (or in a corpus document declared read-only for this workspace). No unit of this
workspace may write there, so these are recorded here rather than fixed.

**Compiled by:** G34, 2026-10-15, from the G35 work order (`G57`) and
the prior units named per item (G40/G38, G33, G37).

**Verification rule used.** Each item was **re-opened in the raw corpus text by G34** and re-measured
before being listed. Nothing is repeated on trust. The verification actually performed is given per item,
with the observed text. **Items that did not hold up would be reported as refuted here: 0 of 6 were
refuted.** (Item 6 was appended by G39, 2026-10-15, re-verified raw; items 1–5 were verified by G34.)
(The one correction that *was* applied — `G56:46` — is a
**workspace** document, not a read-only corpus file, and is therefore not owed; it was corrected in place
by G34 per G35, marked `[corrected by G34 per G35]`.)

---

## 1. `the read-only target repository's findings register:47` — wrong imajev row count

- **Path / line:** `the read-only target repository's findings register:47`
- **Current text (verbatim fragment):** `| **F-EXP11-11** | **\`answer ∉ option set\` was 0.00 % at every round in both models** … | confirmed | \`answerInOptionSet\` across all 4,090 decider rows and 3,590 imajev rows |`
- **Correct value:** **3,690** imajev rows, not 3,590.
- **Established by:** G40 / G38 (per the G35 work order). **Re-verified by G34:**
  `the read-only target G45` → `wc -l` = **3690**; all 3,690
  non-empty lines parse as JSON (**0 unparsable**); **6 distinct rounds**. 3,590 was a **mid-run
  snapshot**, superseded by the complete file.
- **Consistency note:** this register row is quoted verbatim in
  `G46/RUN.json` under `related_measurement.register_quote`; that quote now
  carries a `register_quote_note` pointing at this item, so a reader of the experiment is not left with
  the wrong figure uncorrected.

## 2. `N09-010` — label in tension with its own rationale

- **Path / lines:** `the read-only target repository's instrument source:839–847` — `id` at `:839`,
  recorded label `correct: 0` at `:844`, rationale at `:845–846`.
- **Current text (verbatim):** `correct: 0` → option `"model + context"`; rationale: *[withheld rationale quote — see the withheld rationale note, section 5]*
- **Correct value:** **none asserted — this is a flag, not a mislabel.** The label is in *tension* with its
  own rationale: the rationale implies the constructed family set contains `tool`, while the recorded
  label omits `tool`. Worth a subject review; the alternative reading (`tool` is present but unspendable)
  would keep the label correct.
- **Established by:** G33 (`RUN.json` `semantic_flags_detail`, `EVIDENCE.md` §7); independently confirmed
  by G35 (report item 8a, line 78); **re-verified raw by G34** (text quoted above read directly from
  the fixture).

## 3. `N01-023` — self-contradictory premise

- **Path / lines:** `the read-only target repository's instrument source:329–338` — question at
  `:332`, options/`correct: 1` at `:333–334`, rationale at `:335–336`.
- **Current text (verbatim):** question: *[withheld rationale quote — see the withheld rationale note, section 5]*; recorded answer `G28 (G14, writes)`; rationale: *[withheld rationale quote — see the withheld rationale note, section 5]*
- **Correct value:** **none asserted — flag for subject.** The question's premise is impossible as written
  under the fixture's own rule, so no option is derivable from the question alone. Either the premise or
  the rationale must change.
- **Established by:** G33 (`RUN.json` `semantic_flags_detail`, `EVIDENCE.md` §7); independently confirmed
  by G35 (report item 8b, line 79); **re-verified raw by G34**.

## 4. `N09-004` — self-containment gap

- **Path / lines:** `the read-only target repository's instrument source:773–782` — question at
  `:775–776`, options/`correct: 0` at `:777–778`, rationale at `:779–780`.
- **Current text (verbatim):** question states a class with
  `[redacted] { kind: 'declared', tools: ['C06','C02'] }` **and also two skills in its role
  spec**, asking which family set the planner constructs; recorded answer `"model + context + tool"`;
  rationale: *[withheld rationale quote — see the withheld rationale note, section 5]*
- **Correct value:** **none asserted — flag for subject.** The recorded answer requires the invariant
  "a skill is not a grant unless the policy emits one", which the **question does not state**. That breaks
  the fixture header's claim that *[withheld rationale quote — see the withheld rationale note, section 5]*
- **Established by:** G33 (`RUN.json` `corpus_documentation`-adjacent flag list, `EVIDENCE.md` §7);
  independently confirmed by G35 (report item 8c, line 80); **re-verified raw by G34**.

## 5. `N02-018` — self-containment gap, plus the sharper `G12`/`G13` point

- **Path / lines:** `the read-only target repository's instrument source:1872–1881` — question at
  `:1874–1875`, options/`correct: 2` at `:1876–1877`, rationale at `:1878–1879`.
- **Current text (verbatim):** question: *[withheld rationale quote — see the withheld rationale note, section 5]*; recorded
  answer `"G13(A,B)"`; rationale: *[withheld rationale quote — see the withheld rationale note, section 5]*
- **Correct value:** **none asserted — flag for subject.** Two layers:
  1. **Self-containment gap:** the disambiguating rule ("two-parent commits may only be minted by the
     Reducer") is in the **rationale only**, never in the question, so a reviewer holding only the file
     cannot derive the recorded answer.
  2. **Sharper point (recorded by G33):** the question's **own stated facts satisfy `G12(A,B)`** —
     disjoint paths, no dependency, both required, class R07 — while the record says
     `G13(A,B)`. The case is therefore not merely incomplete; read literally, its stated facts point
     at the *other* answer.
- **Established by:** G33 (`RUN.json` `semantic_flags_detail`, `EVIDENCE.md` §7); independently confirmed
  by G35 (report item 8d, line 81); **re-verified raw by G34**.

## 6. `the read-only target repository's learnings note:279–281` (flagged line `:281`) — "all three defects flattered the candidate" is false as a general clause

- **Path / lines:** `the read-only target repository's learnings note:279–281` — heading at
  `:279`, general clause (*[withheld rationale quote — see the withheld rationale note, section 5]*) at `:280`, correction chain at `:281`.
- **Current text (verbatim):** *[withheld rationale quote — see the withheld rationale note, section 5]*
- **Correct value (narrow — do NOT accuse LEARNINGS of an error it did not make):** the **singular "it"
  already scopes the numeric chain to `setfit-mpnet`**, and that chain is **correct and verified** — keep it
  intact. What does not hold is the **general clause**, *[withheld rationale quote — see the withheld rationale note, section 5]*: the
  order-probe defect **hurt** `modernbert-base`, which moved **UP** when it was fixed
  (**0.342105 → 0.347368**). The supportable wording is that the defects acted as an **asymmetric**
  instrument bias — they depressed the weakest arm most and so **inflated the gap between the arms** — not
  that every defect flattered the candidate.
- **Established by:** G39. **Re-verified raw:** `DEFECT-EVIDENCE.json`
  `.setfitIntermediates.variants[0..2].accuracy` = **0.3158, 0.3158, 0.2947** (down), final arm
  `eval-setfit-mpnet.json` `.accuracy` = **0.2631578947368421**; and
  `.passes.pass1_buggy_order_probe.arms["modernbert-base"].accuracy` = **0.342105** vs
  `.passes.final.arms["modernbert-base"].accuracy` = **0.347368** (**UP**). The same overstatement is
  carried in the workspace at `G58` A3 and §E, which G39 **did** correct in
  place (a workspace document, not the read-only corpus, so it is not owed).

---

## Summary

| # | Corpus path:line | Defect | Correct value | Established by | G34 re-verified |
|---|---|---|---|---|---|
| 1 | `the read-only target repository's findings register:47` | wrong row count (3,590) | **3,690** | G40/G38 | yes — `G45` = 3,690 valid rows |
| 2 | `the read-only target repository's instrument source:839–847` | label/rationale tension | none (flag only) | G33; G35 8a | yes — raw text |
| 3 | `the read-only target repository's instrument source:329–338` | self-contradictory premise | none (flag only) | G33; G35 8b | yes — raw text |
| 4 | `the read-only target repository's instrument source:773–782` | self-containment gap | none (flag only) | G33; G35 8c | yes — raw text |
| 5 | `the read-only target repository's instrument source:1872–1881` | self-containment gap; stated facts satisfy `G12` | none (flag only) | G33; G35 8d | yes — raw text |
| 6 | `the read-only target repository's learnings note:279–281` | general clause "all three defects flattered the candidate" | defects biased the instrument **asymmetrically** (`setfit-mpnet` down 0.3158 → 0.2947 → 0.2632; `modernbert-base` **up** 0.342105 → 0.347368) | G39 | yes — `DEFECT-EVIDENCE.json` passes + `eval-setfit-mpnet.json` |

**Owed: 6. Refuted: 0.** These six are owed **to a read-only repo** and were **deliberately not
applied** — the target `the read-only target repository` was never written. Items 2–5 are flags requiring subject
judgement, not asserted mislabels; items 1 and 6 are unambiguous factual corrections.

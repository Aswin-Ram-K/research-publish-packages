# LIMITATIONS_UPDATE — UPAPER1e

**Purpose.** Sentence-level before/after for every change made to
`papers/encoder-crossover-190/MANUSCRIPT.md` to fold in the **second, independent blind-labelling pass**
(unit UEXP2, `mimo-v2.6-flash`) and the resulting **partial** — not clean — replication of the
fixture-reliability result. This is a limitations update, not a new section of the paper.

**Sources (every number below comes from one of these; none is invented):**

- `experiments/second-labeller-190/ROBUSTNESS.md` (UEXP2 narrative; §2 verbatim `compare2.py` output, §3–§6)
- `experiments/second-labeller-190/RUN2.json` (UEXP2 machine record: `agreement`, `kappa`, `kappa_vs_UEXP`,
  `stratified_kappa`, `arity_detail`, `disagreement_structure`, `memory_admission_convention_detail`)
- `experiments/second-labeller-190/RUN.json` (UEXP first pass: agreement 0.9052631578947369, κ
  0.9013584840356494, 18 disagreements; stratified by kind)
- `experiments/second-labeller-190/EVIDENCE.md:309` (the in-band "It is not IAA. One pass is a model." quote)

**`numbers_changed` for everything else = 0.** No measured result, statistic, arm score, baseline, or
novelty claim was changed. Every pre-existing number in the manuscript is byte-identical; the edits below
only **add** the second-reader figures and **re-frame** the fixture-reliability discussion. §6.6 (the
counter-case / under-trained-encoder weakness) is **untouched**.

**`sentences_changed` = 20** — the number of rows in the change table below (each row is one sentence-,
bullet-, heading- or list-row-level edit). Definition stated so a verifier can recount.

**Target read-only.** HEAD before and after:
`907fa39da7ba8ecfbe6e976b7a4cddadea7ac36b`. `git status --porcelain` before and after: the same four
untracked paths (`?? .ci-trunk.txt`, `?? .relay/`, `?? docs/evidence/selfbuild/relay-outbound-2026-10-13.txt`,
`?? docs/migration/`), all pre-existing from the unrelated concurrent session and none attributed to this
unit. This unit wrote only inside the workspace.

---

## The framing that governs every edit

- **κ = 0.9125 (B2 vs UEXP) and κ = 0.8577 (B2 vs fixture) are machine reproducibility ONLY.** They are
  **not** inter-annotator agreement and must **never** be cited as such. Two models agreeing is still not IAA.
- An **independent human labeller remains owed**; `PAPER_CANDIDATES.md` §F.3 is **not** discharged.
- The second pass **partially** replicates the first. The text must not imply the second pass confirmed the
  first.

---

## Change table

### 1. Abstract — reliability sentence (rewritten)

**Before:**
> We also do **not** report κ = 0.9014 as inter-annotator agreement: the second labeller was a **model**, so
> this is machine reproducibility of the fixture, not human agreement; an independent human labeller is still
> owed (§6.2).

**After:**
> We also do **not** report κ = 0.9014 (first blind reader) or κ = 0.8577 (second, independent blind reader) —
> nor their mutual κ = 0.9125 — as inter-annotator agreement: both labellers were **models**, so this is
> machine reproducibility of the fixture, not human agreement.

**Driving numbers:** κ 0.9014 (UEXP), κ 0.8577 (B2), κ 0.9125 (B2 vs UEXP). **Source:** `RUN.json`; `RUN2.json`
`.kappa`, `.kappa_vs_UEXP`.

### 2. Abstract — new partial-replication sentence (added)

**Added:**
> The second reader **partially** replicates the first: the κ magnitude holds (both ≥ 0.85) but the exact 0.90
> headline does not.

**Driving:** `replication = "partial"`; both κ ≥ 0.85. **Source:** `RUN2.json` `.replication_detail`;
`ROBUSTNESS.md` §3a, §7.

### 3. §1 Contributions, item 5 (rewritten)

**Before:** "…human agreement on the fixture labels (§6.2)."
**After:** "…human agreement on the fixture labels — which **two** blind model passes do not supply, since
the second only **partially** replicates the first (§6.2)."
**Driving:** two model passes, partial replication. **Source:** `RUN2.json` `.replication`.

### 4. §3.4 bullet lead (rewritten) — this bullet was factually falsified by the second pass

**Before:** "**Second labeller — machine reproducibility only.**"
**After:** "**Two blind model readers — machine reproducibility only.**"
**Driving:** a second pass now exists. **Source:** `RUN2.json` `.status = done`.

### 5. §3.4 numbers sentence (rewritten)

**Before:** "Agreement 0.9053, κ 0.9014, 18/190 disagreements. The labeller is `routeB-blind-model`: **a
model**, not an independent human."
**After:** "Reader B (`routeB-blind-model`) reached agreement 0.9053, κ 0.9014, 18/190 disagreements; reader
B2 (`mimo-v2.6-flash`) reached 0.8632, κ = 0.8577, 26/190 — a **partial** replication whose exact "0.90"
headline degrades by ~4 points. The two readers agree with each other at 0.9158, κ = 0.9125."
**Driving:** 0.8632 / 0.8577 / 26; 0.9158 / 0.9125. **Source:** `RUN2.json` `.agreement_detail_vs_fixture`,
`.agreement_vs_UEXP_detail`.

### 6. §3.4 IAA sentence (rewritten)

**Before:** "This is **not inter-annotator agreement** and is reported as such in §6.2."
**After:** "Both are **models**, not independent humans, so neither figure — and not the model-to-model κ
either — is **inter-annotator agreement** (§6.2)."
**Driving:** record-level `limitation` extended to two models. **Source:** `RUN2.json` `.limitation`;
`ROBUSTNESS.md` §header warning.

### 7. §3.4 stale sentence (deleted)

**Before:** "Exactly **one** model pass exists; a second distinct-model pass (`mimo-v2.6-flash`) was launched
and **returned no file**."
**After:** *(removed — false: the second pass returned `labelsB2.json`)*
**Driving:** `labelsB2.json` exists, 190 labels. **Source:** `ROBUSTNESS.md` §8 artifact index; `RUN2.json`
`.artifacts`.

### 8. §6.2 heading (rewritten)

**Before:** "### 6.2 κ = 0.9014 is machine reproducibility of the fixture, **not** inter-annotator agreement"
**After:** "### 6.2 Two blind model readers: machine reproducibility of the fixture, **not** inter-annotator
agreement"
**Driving:** two readers now, headline 0.9014 no longer the sole figure. **Source:** `RUN2.json`.

### 9. §6.2 opening sentence (rewritten)

**Before:** "The second labelling pass agrees with the fixture's hand-authored labels 0.9053 of the time,
κ = 0.9014, with 18/190 disagreements."
**After:** "**Two** blind model passes now exist. Reader B (`routeB-blind-model`) agrees with the fixture's
hand-authored labels 0.9053 of the time, κ = 0.9014, with 18/190 disagreements. Reader B2 (`mimo-v2.6-flash`),
run later on the same blinded inputs, agrees **0.8632** of the time, **κ = 0.8577**, with **26/190**
disagreements."
**Driving:** 0.8632 / 0.8577 / 26. **Source:** `RUN2.json` `.agreement_detail_vs_fixture`.

### 10. §6.2 model-to-model sentence (added)

**Added:** "The two readers agree with **each other** **0.9158** of the time, **κ = 0.9125** — a genuinely
new, model-to-model quantity."
**Driving:** 0.9158 / 0.9125. **Source:** `RUN2.json` `.agreement_vs_UEXP_detail`; `ROBUSTNESS.md` §3b.

### 11. §6.2 partial-replication sentence (added, replaces the old "we therefore report this as machine reproducibility" sentence)

**Added:** "The *magnitude* of the first result therefore replicates (both readers land at κ ≥ 0.85), but the
exact "0.90" headline does **not**: reader B2 sits 4.2 points lower on agreement and 4.4 points lower on κ,
and the pre-registered ladder would place it in band 2 (0.75 ≤ agreement < 0.90) while it still clears the
band-1 κ threshold. We report this as a **partial replication** and give **both** readers, not one of them as
"the" figure."
**Driving:** Δ 4.2 pp agreement / 4.4 pp κ; band 2. **Source:** `ROBUSTNESS.md` §3a; `RUN2.json`
`.replication_detail`.

### 12. §6.2 model-to-model vs record paragraph (added)

**Added:** "The two readers agree with each other *more* than either agrees with the fixture record (0.9158 >
0.9053 and > 0.8632). That is consistent either with a shared LLM reading bias or with author-idiosyncratic
conventions in the fixture, and we do not resolve it: a high model-to-model κ is equally consistent with two
models sharing a *wrong* convention. What it does rule out is treating the fixture's conventions as
self-evident, and it is why those conventions should be read as conventions rather than as ground truth."
**Driving:** 0.9158 > 0.9053 and > 0.8632. **Source:** `ROBUSTNESS.md` §3b, §7 ("What this never licenses");
`RUN2.json` `.limitation`.

### 13. §6.2 weak-dimensions bullet (added)

**Added:** "The weak dimensions are the same for both readers, and the weakest is `memory.admission` (B2 κ =
**0.5625**, UEXP κ = **0.7153**), followed by `acquisition` (B2 **0.7045**, UEXP **0.8049**). The other five
of the seven kinds (`escalation`, `topology`, `worker.class`, `context.package`, `capability.family`) are
stronger for both readers. Consistent weakness across two independent machine readers points at the
**fixture**, not at the readers: label soundness is dimension-dependent, and the dependence looks like a
property of the instrument."
**Driving:** stratified κ pairs. **Source:** `RUN2.json` `.stratified_kappa`; `ROBUSTNESS.md` §3c.

### 14. §6.2 `memory.admission` bullet (added)

**Added:** "The `memory.admission` tier boundary is a real, replicated ambiguity — the top repair item. Four
cases (`memory.admission-001/-009/-021/-027`) record step-scoped scratch that is never re-read as
`EPHEMERAL`; **both** blind readers independently chose `DROP` on all four (**4/4** replicated). UEXP first
reported this convention and UEXP2 shows it is not one model's quirk. The fixture's tier vocabulary for
scratch that is never re-read is not pinned down by the questions."
**Driving:** 4/4 replicated `EPHEMERAL`→`DROP`. **Source:** `RUN2.json`
`.memory_admission_convention_detail`; `ROBUSTNESS.md` §4.

### 15. §6.2 arity bullet (added)

**Added:** "Accuracy tracks option arity for both readers — but the effect is confounded with kind. Agreement
falls from 0.970 (2-option cases, n = 33) to 0.722 (5-option cases, n = 54) for B2, and from 1.000 to 0.815
for UEXP (κ 0.950 → **0.684** and 1.000 → 0.791). The 5-option stratum is dominated by the closed-roster
kinds `memory.admission` and `acquisition` — the two hardest kinds for independent semantic reasons — so this
is **not** clean evidence of option-wording exploitation, and on the stratum where the answer is named in the
question (30 `escalation` cases) the readers scored 30/30 (UEXP) and 28/30 (B2), which is not how a
surface-cue matcher behaves. But the gradient is real and it **weakens any blanket "the labels are sound"
claim** for high-arity closed-roster kinds: soundness is measurably lower there."
**Driving:** arity agreement/kappa; 30/30 vs 28/30. **Source:** `RUN2.json` `.arity_detail`, `.arity_effect`;
`ROBUSTNESS.md` §6.

### 16. §6.2 disagreement-structure bullet (added)

**Added:** "Disagreement structure, not just its count. B2 disagrees on 26 cases and UEXP on 18, but the
overlap is a **14-case shared contested core** — all four `acquisition` traps (`-007/-014/-019/-023`),
`topology-018`, `capability.family-004/009`, `context.package-004`, `worker.class-023`, and the four
`EPHEMERAL`/`DROP` cases above. The tails (12 B2-only, 4 UEXP-only) are scattered and read as reader-specific
noise, not as a second catalogue of defects. The honest reading is "14 shared contested cases plus two small
reader-specific tails", not "26 defects"."
**Driving:** 26 / 18; overlap 14; tails 12 / 4. **Source:** `RUN2.json` `.disagreement_structure`;
`ROBUSTNESS.md` §5.

### 17. §6.2 pre-registered-threshold bullet (rewritten)

**Before:** "A threshold was pre-registered (≥ 0.90 agreement / ≥ 0.85 κ) and *met* at 0.905 / 0.901 — but a
met threshold on a **model** pass does not convert it into human agreement. Exactly one model pass exists; a
second distinct-model pass (`mimo-v2.6-flash`) was launched and **returned no file**."
**After:** "A threshold was pre-registered (≥ 0.90 agreement / ≥ 0.85 κ). Reader B *met* it at 0.905 / 0.901;
reader B2 *met the κ threshold but not the agreement threshold*, at 0.863 / 0.858. But a met threshold on a
**model** pass — or on two — does not convert it into human agreement."
**Driving:** 0.863 / 0.858, band 2. **Source:** `RUN2.json` `.replication_detail`; `ROBUSTNESS.md` §7.

### 18. §6.2 closing IAA paragraph (extended)

**Before (3 sentences):** "**An independent human labeller is still owed…** §F.3's point … remains true. The
fixture's own flagged decidability weak points … were deliberately not applied …"
**After (6 sentences), key additions:** the `EVIDENCE.md:309` quote is retained and now introduced as "states
it for one pass"; new sentence "…and two passes do not change that: **κ = 0.9125 between two models is still
not inter-annotator agreement and must never be cited as such.**"; new sentence "Two models can share a wrong
convention as easily as a right one, and this result bounds *machine* reproducibility for exactly two models
on exactly one fixture."; §F.3 sentence extended with "…and its call for a second independent **human**
labeller is not discharged by either pass."
**Driving:** κ 0.9125 is not IAA; two models only. **Source:** `RUN2.json` `.limitation`; `ROBUSTNESS.md`
§header warning, §7.

### 19. §7 reproduction table (list row split into two)

**Before:** one row "second-labeller reliability | `second-labeller/{RUN.json,EVIDENCE.md,disagreements.jsonl,labelsB.json,PREREGISTRATION.md}`"
**After:** reader-B row unchanged; **added** row "second-labeller robustness (reader B2; **not** in the
released subset) | source experiment tree `experiments/second-labeller-190/{RUN2.json,ROBUSTNESS.md,labelsB2.json,disagreementsB2.jsonl,metrics2.json,compare2.py}`"
**Driving:** the released `repro/encoder-crossover-190/second-labeller/` holds only UEXP's files (verified by
directory listing); the second-pass artifacts live only in the source experiment tree.
**Source:** `ls repro/encoder-crossover-190/second-labeller/`; `ROBUSTNESS.md` §8.

### 20. "Data and code availability" second-labeller bullet (extended)

**Before:** "The second-labeller evidence — `second-labeller/{RUN.json,EVIDENCE.md,disagreements.jsonl,labelsB.json}`,
the record behind the κ = 0.9014 result, which §6.2 states is machine reproducibility of the fixture and
**not** inter-annotator agreement."
**After:** same, marked "(reader B)", **plus** "The **second** model reader (B2, κ = 0.8577; model-to-model
κ = 0.9125) is recorded in the source experiment tree at
`experiments/second-labeller-190/{RUN2.json,ROBUSTNESS.md,labelsB2.json,disagreementsB2.jsonl,metrics2.json,compare2.py}`
and is **not** part of this released subset."
**Driving:** 0.8577 / 0.9125; second-pass artifacts absent from `repro/`. **Source:** `RUN2.json`; `ls repro/…`.

---

## Explicitly NOT changed

- **§6.6 (counter-case / under-trained-encoder weakness)** — untouched, not weakened, not deleted.
- **Every measured number** — arm accuracies (0.3474 / 0.2632 / 0.6789 / 0.4526 / 0.2316 / 0.6684), McNemar
  statistics, leak-lint counts, chance floor 0.2911, Δ values, and all UEXP first-pass figures
  (0.9053 / 0.9014 / 18 / stratified 0.8837 / 0.9140 / 0.3526 / 0.3252 / 0.3421) are byte-identical.
  Note 2026-10-16: this ledger is the dated record of that unit's edit and is kept as written. The release
  tree's neutralisation has since moved two of these values — AB mutual agreement 0.3526 → 0.3684 and routeA
  κ 0.3252 → 0.3249 (exact 0.3248813212427869); 0.9053 / 0.9014 / 18 / 0.8837 / 0.9140 / 0.3421 are unchanged.
- The three files this unit was told not to touch (`CHECKLIST.md`, `OPEN_QUESTIONS.md`, `CLAIMS.md`,
  `REFERENCES.bib`, …) and everything in `strategy/`.

## What a verifier should be able to re-check

1. Every new figure appears literally in `RUN2.json` / `ROBUSTNESS.md` with the same value.
2. No pre-existing number changed: the six edit spans are the only textual changes.
3. §6.2 states model-to-model κ = 0.9125 is **not** IAA and that §F.3 is **not** discharged.
4. The second pass is described as a **partial** replication.

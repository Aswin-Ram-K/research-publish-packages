# PAPER CANDIDATES — ranked inventory of the Duval / Consonance research corpus

> **ERRATA HEADER — unit UCORR1, 2026-10-14.** This revision applies the seven corrections in
> [`PAPER_CANDIDATES_SUPPLEMENT.md`](PAPER_CANDIDATES_SUPPLEMENT.md) (unit **UP2**, 2026-10-14, which
> surveyed the material *outside* `docs/research/`) and adds one candidate, **`NC1`**, inserted at rank
> **6½**. **Nothing true was deleted or weakened.** Every original claim affected was re-verified against
> the read-only target before it was narrowed; corrections are inline and dated, per this corpus's
> append-only-errata norm (`docs/DECISION_LOG.md:3–4`: *"Append-only. … Amendments are new entries, never
> edits"*).
>
> **Corrected.** (1) A1's thesis — *"a first-class unknown-effect state is the piece shipping agent
> runtimes are missing"* — **overstated**: the resume-failure **observation is prior-published**
> (arXiv:2608.03836 = V13, arXiv:2608.29381 = V14; `docs/consolidation/SOURCE_VERIFICATION.md:35–36`,
> `:46`, `:101–105`) and only the **construction** is unoccupied. (2) A1's substrate citations — the
> decision log was cited 0 times; **D-001 is refined by D-023** (`docs/DECISION_LOG.md:567`), with
> **D-042/D-051/D-058**, the last recording a *measured* hash defect. (3) A2 — added the externally
> verified gap statement (V24, Letta; `SOURCE_VERIFICATION.md:51`). (4) §D — *"the corpus is fully
> accounted for"* accounted only for `docs/research/`; the measured root-`docs/` census is now stated.
> (5) the SM pilot — its **pre-registration and recorded VOID** against the authors' own 53.8 % headline
> are now cited (`docs/EXPERIMENT_SM_PILOT.md:251–263`, `:284–286`, `:289+`); applied to **A1 and #8**
> (the supplement anchored it at #6, which cites no SM file — the substance was verified and applied
> where the citation actually is). (6) #9 — added `docs/BUILD_PLAN.md:123–186` and **D-116/D-117/D-127**,
> **D-098/D-099**. (7) the method paragraph — the prior-art ledger narrows every candidate's novelty and
> is now cited in A1, A2 and §F.
>
> **Added.** `NC1` · *Detectors that cannot fail* (rank 6½), from `docs/MISTAKES.md:386–388`, `:576–605`,
> `docs/DECISION_LOG.md:4368` (D-096), `evals/prevention.ts` (`prevention.detector-coverage`); it
> **supersedes** the §D note that proposed an M1–M14 method paper. **No original rank was renumbered**
> (the per-candidate "Rank N of 14" labels still refer to the original 14).
>
> **Re-verified and left untouched.** A1's *"nothing was promoted into `src/`"* gap; A2's **244/244**
> zero control and **41.8 % / 32.2 %** figures; §F1's measurement-discipline claim; §F6's *"no fabricated
> submission state"*. The **EXP#11 / EXP#12 / EXP#7 statistics are untouched** — *with one exception: the
> A4 imajev row count is **3,690**, not 3,590 (`:305`) — `[corrected by UCORR2 per UVER2, 2026-10-15]`; the
> "independently verified exact" claim is superseded on that number only.* The **external-validity caveat is unchanged**: no second labeller, no external benchmark and no independent corpus exists anywhere outside `docs/research/` (UP2 §6.3; restated in §F2).
>
> **ERRATA — unit UCORR3, 2026-10-15.** The A3 evidence bullet (and its restatement in the §E O-1 runner-up paragraph) asserted as a **universal** that *"every correction moved the affected arm DOWN"* — defects were flattering the candidate. **Re-verified against the raw evidence, that universal is false.** `setfit-mpnet` did move **down** (0.3158 → 0.2947 → 0.2632; `DEFECT-EVIDENCE.json` + `eval-setfit-mpnet.json .accuracy` = 0.2631578947368421), but **`modernbert-base` moved UP**: **0.342105** (pass 1, buggy order probe) → **0.347368** (final), `.passes.pass1_buggy_order_probe.arms[...]` vs `.passes.final.arms[...]`. The honest reading: the defects were an **asymmetric** instrument bias that **inflated the gap between the arms** — they depressed the weakest arm most — rather than uniformly flattering the candidate. **Nothing true was deleted**: the verified `setfit-mpnet` chain is kept intact and **M12 is retained**, narrowed to the reading the evidence supports (the method learning is real). Inline edits are marked `[corrected by UCORR3 per UCORR3 re-verification, 2026-10-15]`.

**Unit:** UP1 · **Date:** 2026-10-11 · **Target repo:** `/home/zer0null/Duval` (read-only, never written)
**Scope:** every document under `/home/zer0null/Duval/docs/research/`, the evidence trees, `CONSONANCE.md`, `evals/`.

**Method.** 39 research documents were surveyed by headings + targeted sections; the 8 anchor experiments
(`EXP#1`–`EXP#7`, `EXP#3b`), the anchor working paper (719 lines), the findings register (642 lines), and
the 10 later experiments plus the superseded `EXP-M4` (`EXP#10`–`EXP#22`) were read at their
results/resolution sections. The evidence trees, `evals/`, `CONSONANCE.md`, `docs/FINDINGS.md`,
`docs/consolidation/SOURCE_VERIFICATION.md` and the `selfbuild/`/`BIOMAP/` programme trees were then
surveyed. Nothing was written
to the target; `git status` on the target was read only. Every candidate below names its files; where a
finding-id does not exist the absence is stated rather than implied.

> **UCORR1 correction 7 (2026-10-14).** `docs/consolidation/SOURCE_VERIFICATION.md` was read by UP1 and
> then **not used**: it is cited once, in this method paragraph, and in no candidate's evidence or risk
> field — measured `SOURCE_VERIFICATION` = 1 occurrence, `DECISION_LOG` = 0, `MISTAKES` = 0. It is the
> corpus's **novelty-narrowing instrument** (`docs/research/PAPER_DERIVATION.md:35–37`: *"What is
> unoccupied is narrower, and the narrowing is the contribution of the survey that precedes this
> programme"*) and carries the only **externally verified gap statements** in the corpus (24 claims,
> V1–V24). Its verdict is **`mixed` — supported for the construction, undercut for the observation**.
> It is now cited in A1 (prior art), A2 (gap statement) and §F7.

**Honesty rules applied.** (1) A candidate with no measured result is in §D, not §A–C. (2) `n` and
independent-run counts are quoted from the documents' own text, not inferred. (3) A `confirmed-with-caveat`
finding keeps its caveat here. (4) Closeness is judged as *distance to a submittable manuscript*, not
distance to a publishable idea.

Contribution-type vocabulary: **empirical measurement** · **method** · **system** · **negative result** ·
**survey** · **position**.

---

## Ranking at a glance

| # | Candidate | Type | Closeness | Strongest venue class |
|---|---|---|---|---|
| 1 | Deriving agent state from an observation stream | system + method (+empirical) | `1–2 weeks` | top-tier ML-systems workshop / short paper |
| 2 | Replay reproduces the record, not the decision | empirical measurement | `1–2 weeks` | workshop short paper |
| 3 | A fine-tuned encoder head does not beat a fine-tuned 4B decider | negative result + empirical | `1–2 weeks` | workshop / short paper |
| 4 | Self-refinement without external feedback degrades decision accuracy | negative result + empirical | `1–2 weeks` (workshop) | top-tier workshop; main venue needs power |
| 5 | Small decision models, the escalation ladder, and the unroutable ceiling | empirical measurement | `1–2 weeks` scoped / `needs new experiments` for main | workshop; main needs an external benchmark |
| 6 | Graded progressive disclosure is cache-safe and cheaper at equal sufficiency | system + empirical | `1–2 weeks` (narrow) | systems workshop / short paper |
| 6½ | **NC1** · Detectors that cannot fail: a machine-checked registry of 19 verification failure classes | method + empirical measurement | `1–2 weeks` | empirical-SE / evaluation-methodology workshop |
| 7 | Batching binary gates is free; routed extraction cuts context 15.3× and exposure to 0/20 | empirical + negative | `needs new experiments` (round 2 designed) | workshop (agent security / efficiency) <br>**[UFIXGR7, 2026-10-15] Scope annotation — not a re-title.** The author chose this candidate by its recorded title; the title is kept. The drafted paper scopes to the batching note and asserts neither the 15.3× nor the 0/20 figure: see `papers/gated-read-batching/MANUSCRIPT.md:195` and `papers/gated-read-batching/GAPS.md` G-13/G-14. Those two figures are reproduced raw-record facts about the wider run, outside the drafted scope. |
| 8 | Full history fails on volume, projection fails on chain length | empirical measurement | `needs new experiments` | workshop |
| 9 | A self-build loop can move its own wall | negative result + empirical | `needs new experiments` | workshop (self-improvement / safety) |
| 10 | A read is not a gate | method + negative result | `needs new experiments` | workshop; best as a section of #1 |
| 11 | ASR = 0 everywhere: when the attack base rate never materialises | negative result + method | `needs new experiments` | workshop (agent security) |
| 12 | Teardown budgets are theoretical at measured scale | system + negative result | `needs new experiments` | short experience paper |
| 13 | Long-horizon agent evaluation: suites, statistics, memory failure register | survey | `1–2 weeks` (survey form) | survey venue / journal |
| 14 | Agent harnesses: what the field measures and what it only asserts | survey + position | `1–2 weeks` (survey form) | survey venue / position track |

**Publishable now with editing only (9, all at `1–2 weeks`, subject to the named gaps):** #1, #2, #3, #4,
#5, #6, **NC1** (inserted at 6½), #13, #14.
**Nearly ready — needs one measurement or a scope cut (1):** #7.
**Needs new experiments (5):** #8, #9, #10, #11, #12.
**Not a paper — engineering report / programme record / literature input:** §D (18 entries covering ~60
documents; §D accounts for `docs/research/`, not the whole corpus — see the census correction in §D).

The table's 14 original rows plus the **`NC1` insertion at 6½** are the candidate set — **15 candidates**.
**No original rank was renumbered or changed**; the insertion uses a half-rank precisely so that every
existing number, and every cross-reference to it in §E, stays valid. The split above is the authoritative
close/blocked judgement and is restated per candidate below. The two survey rows (#13, #14) are real papers
only in survey form; as first-party research they are literature records and belong in §D.

---

## A. Publishable now with editing only

### A1 · Deriving agent state from an observation stream
**Rank 1 of 14.**

- **Working title:** *Deriving agent state from an observation stream: a pre-registered programme for
  agent-native journaling, unknown effects and typed references.*
- **One-sentence thesis:** Agent state should be a deterministic projection of an append-only observation
  stream that independently records what was supplied, permitted, requested, executed, mutated and verified —
  and **no shipping agent runtime exposes a machine-checkable resume contract or a first-class
  *unknown-effect* state** (`docs/consolidation/SOURCE_VERIFICATION.md:35`, V13 = arXiv:2608.03836; `:46`,
  V19 = arXiv:2608.02645, whose four-phrasing search found *"no production agent runtime"*).
  *(UCORR1 correction 1, 2026-10-14: the original wording ended "…is the piece shipping agent runtimes are
  missing." That **overstated**. The resume-contract failure is an **observation that is already
  prior-published** — measured on five shipping frameworks, with adversarial numbers — while the
  **construction** (agent-native append-only observation log, state as projection, "did the effect happen?"
  as a first-class third state) is what remains unoccupied. The contribution is restated, not deleted; see
  "What is missing" 7.)*
- **Contribution type:** system + method, carried by empirical measurement. The method contribution
  (validate the instrument before believing its findings) is presented as co-equal.
- **Evidence base:**
  - Anchor manuscript: [`docs/research/PAPER_DERIVATION.md`](/home/zer0null/Duval/docs/research/PAPER_DERIVATION.md) (719 lines, §1–§8; abstract, related work, method, 8 experiments, discussion, limitations, artefacts, reproduction).
  - Pre-registrations: [`experiments/EXP#1-absence-probe.md`](/home/zer0null/Duval/docs/research/experiments/EXP%231-absence-probe.md), [`EXP#2`](/home/zer0null/Duval/docs/research/experiments/EXP%232-observation-stream-derived-state.md), [`EXP#3`](/home/zer0null/Duval/docs/research/experiments/EXP%233-uncertain-effects-resume-contract.md), [`EXP#3b`](/home/zer0null/Duval/docs/research/experiments/EXP%233b-concurrent-resumption.md), [`EXP#4`](/home/zer0null/Duval/docs/research/experiments/EXP%234-reference-token-methods.md), [`EXP#5`](/home/zer0null/Duval/docs/research/experiments/EXP%235-context-engine-paging.md), [`EXP#6`](/home/zer0null/Duval/docs/research/experiments/EXP%236-user-abstraction-composition.md), [`EXP#7`](/home/zer0null/Duval/docs/research/experiments/EXP%237-replay-divergence.md).
  - **8 experiments, all EMERGE, all re-runnable, all exit 0**: EXP#1 15/15 detectors discriminate;
    EXP#2 16/16; EXP#3 13/13; EXP#3b 10/10; EXP#4 17/17; EXP#5 13/13; EXP#6 19/19 (first run); EXP#7 5/5.
    EXP#7 additionally analyses **4 models × 190 cases × 4 variants**.
  - Method ledger: [`experiments/LEARNINGS.md`](/home/zer0null/Duval/docs/research/experiments/LEARNINGS.md) **M1–M7** (seven ways a self-check fails).
  - Substrate findings that back the determinism claim: `F-IDENT-01`, `F-IDENT-02`, `F-IDENT-03`,
    `F-IDENT-04` in [`FINDINGS_REGISTER.md`](/home/zer0null/Duval/docs/research/FINDINGS_REGISTER.md)
    (clock reads and a broker counter inside the hashed `State`; all VERIFIED and RESOLVED 2026-10-05).
  - **Substrate (decision-log) grounding — UCORR1 correction 2, 2026-10-14.** The original inventory cited
    [`docs/DECISION_LOG.md`](/home/zer0null/Duval/docs/DECISION_LOG.md) **0 times**. Cite the foundation as
    **D-001 (`:8`) and D-002 (`:28`) *as refined by* `D-023` (`:567`)** — *"The unit of propagation is the
    StateCommit; StateObjects are referenced content"*, status line *"Affirms D-001/D-002, refines the shape
    of D-005"*, because *StateObject* as the DAG node *"weakens 'the state is the grant'"* and cumulative
    arrays store **O(n²)** refs — plus **D-042 (`:1216`, position is derived, never stored)**,
    **D-051 (`:1648`, a lease is *"the narrow scope of authority"* and authority stays in the state)**,
    **D-009 (`:155`, allowlist not denylist)** and **D-039 (`:1123`, kernel-stamped provenance)**.
    **D-058 (`:1993`) is the strongest uncited item and is _measured_:** `src/state.ts:174-175` excluded only
    `["id","ts"]` from the body digest, so *"two states identical in every content respect at different
    `epoch` values hashed differently (`ee2852ce…` vs `5d34ff6b…`)"*; its fix removed `epoch` from the
    state's identity. *A paper that cites D-001 as the foundation and D-023 as nothing is citing a
    superseded shape.*
  - Reproduction: `npm run absence-probe && npm run exp2 … exp7`; each `EXP#N` is its own merge commit.
- **Closeness:** `1–2 weeks`. This is the only document in the corpus already written as a paper, with
  abstract, related work, bounds and a reproduction section.
- **What is missing (reviewer attack surface), stated by the paper itself:**
  1. **EXP#2 is a round trip.** The fixture emits observations *from* the authored state, so "faithfully
     reconstructible" proves lossless decomposition, not stream independence. The stronger test (**EXP#2b**,
     a real `Loop` run emitting observations as it executes) is filed and unbuilt (§6.1).
  2. **Nothing was promoted into `src/`.** Every artefact lives in `tools/`; the kernel is unchanged. This
     is a result about a *model of* the kernel (§6.4). A reviewer will call this "a simulator of your own
     design".
  3. **In-memory journal, simulated world** (EXP#3): durability (fsync, write ordering, surviving the crash)
     is untested. **EXP#3b's concurrency is single-process** — one event loop and a microtask yield standing
     in for network latency; the consume-once gate is a `Map`, so store-level atomicity is modelled, not
     demonstrated (§6.3).
  4. **Characters, not tokens** — no tokenizer in the repo, deliberately (§6.2).
  5. **EXP#5's break-even is a function of the brief:full ratio (~16:1 here)**, not a constant; quoting
     83.9 % or k=29 without the ratio is the exact flattening error the corpus elsewhere penalises.
  6. **No live model anywhere** except EXP#7's recorded outputs (§6.4).
  7. **The observation is prior-published and must be cited as such (UCORR1 correction 1).** The
     resume-contract failure this programme reproduces in miniature (EXP#3/EXP#3b, which say so at
     `docs/research/experiments/EXP#3-uncertain-effects-resume-contract.md:111–112`) was **measured and
     published in August 2026** by two preprints. **arXiv:2608.03836** (V13): *"Five widely deployed agent
     workflow frameworks answer differently, none exposes a machine-checkable contract, and measured
     behavior violates even the fragments they state… LangGraph 1.2.9 durably records a second resume value
     and never consults it… CrewAI 1.15.2 re-executes completed effect-bearing methods against its written
     claim… saturation 1.0 in 36 of 40 cells, and the failure crosses hosts."* **arXiv:2608.29381** (V14):
     five failure modes and three end-to-end attacks (malware-verification bypass, unauthorised mail
     forwarding, double payment). `SOURCE_VERIFICATION.md:101` calls V13/V14 *"the strongest single result
     in this ledger"*, and *"the field has been measured failing at it within the last two months, on
     frameworks that ship today."* **Consequence:** the contribution must be **construction + method +
     measurement in a different substrate**, and both preprints belong in the abstract-adjacent gap
     paragraph — not presented as this programme's discovery. `PAPER_DERIVATION.md:89–93` already does this
     correctly; the inventory did not.
  8. **The SM pilot's headline was voided by its own pre-registration (UCORR1 correction 5).**
     `docs/EXPERIMENT_SM_PILOT.md:251–263` records a pre-registered **VOID applied against the authors' own
     53.8 % result**, because the control that licensed it failed: *"The headline number (53.8 % saving at
     24/24 = 24/24) is **not** reportable as a supported claim, because the control that licenses it
     failed."* `:284–286`: *"The 53.8 % figure is the one I would have wanted; it is not reportable under
     the pre-registration."* Root cause is a real fixture defect — `tok(a,b,len)` *"cycles with period 2,
     so the answer was guessable"* — and the first **F7 detector did not fire** on that degenerate fixture
     (`:289+`), the same class as `MISTAKES.md` A4. This pre-registration was uncited (`EXPERIMENT_SM_PILOT`
     = 0 occurrences); it is a first-class method datum and travels with any use of the pilot's numbers.
- **Strongest venue class:** a top-tier ML-systems / agent-infrastructure **workshop** or a **short paper**
  (e.g. an agent-systems or durable-execution workshop at a major systems or ML venue). A main-conference
  full paper is a stretch until gaps 1–3 close.
- **Risk of unpublishability:** "single-machine, single-project, nothing in `src/`, no external system run,
  no live model" is stated in §6.4 as the programme's own scope. If a reviewer treats the paper as a *systems
  claim* rather than a *pre-registered methodology + measured model*, it collapses. Framing must be:
  **method contribution first, system second.**

---

### A2 · Replay reproduces the record, not the decision
**Rank 2 of 14.**

- **Working title:** *Replay reproduces the record, not the decision: replay divergence measured on
  already-recorded agent outputs.*
- **One-sentence thesis:** A deterministic log makes the record replayable but not the model's decision —
  re-binding a recorded request to a different model diverges in 41.8 % of cases and relabelling it in
  32.2 %, against a 0 % replication control and a 31.6 % stable set.
- **Contribution type:** empirical measurement (with a methodological negative-control demonstration).
- **Evidence base:**
  - [`docs/research/EXP#7`](/home/zer0null/Duval/docs/research/experiments/EXP%237-replay-divergence.md) and PAPER_DERIVATION §4.7.
  - Corpus: **4 models × 190 cases × 4 variants = 3,040 recorded outputs**, all offline (replay *is* the act
    of consuming a record, so no live endpoint is involved). Files:
    [`decision-variants.jsonl`](/home/zer0null/Duval/docs/research/decision-variants.jsonl),
    [`decision-tree-spec.json`](/home/zer0null/Duval/docs/research/decision-tree-spec.json).
  - **A real zero control:** on non-decomposable cases `V2` re-issues the `V0` request and
    **244/244 returned an identical decision** — so the instrument can say zero, and 41.8 % is a property of
    the bindings, not of noise.
  - **Independent-corpus agreement:** the `l1-head-to-head` corpus agrees at **51.6 %** divergence
    ([`l1-head-to-head.jsonl`](/home/zer0null/Duval/docs/research/l1-head-to-head.jsonl), 380 rows).
  - Per-pair detail: divergence grows as models get further apart (26.8 % → 56.8 %); decision diverges more
    than outcome.
  - Method learning **M7** (a control caught a predicate inversion that would otherwise have been
    published: the first run reported "51 % replication divergence").
  - **Externally verified gap statement — UCORR1 correction 3, 2026-10-14.** A2's gap was inferred from the
    fixture; the corpus's own prior-art ledger verifies it externally: agent identity above the model is
    already **productised and model-agnostic** — Letta: *"Letta agents are model-agnostic… Users can change
    an agent's underlying model at any time, even mid-conversation"* — and *"**No measurement of
    behavioural continuity across a swap was found.**"*
    (`docs/consolidation/SOURCE_VERIFICATION.md:51`, V24; correction 7 — the ledger is the corpus's
    novelty-narrowing instrument, `PAPER_DERIVATION.md:35–37`.) This is stronger than the fixture-inferred
    gap and should be A2's gap paragraph.
- **Closeness:** `1–2 weeks`. The measurement is complete, controlled and cross-checked on a second corpus.
  What remains is framing it as a standalone short paper rather than §4.7 of A1.
- **What is missing:**
  1. **It is a per-decision rate on 2–5-option MCQ tasks.** The paper itself says a longer trajectory
     *compounds* rather than averages these rates, so the trajectory-level figure would be **worse** and is
     not measured.
  2. No live re-issue: the divergence is a property of *recorded* outputs across bindings, which is the
     honest framing but removes the "we re-ran the model" story a reviewer may expect.
  3. Two corpora, but both are typed-decision fixtures built in this project; no external benchmark.
  4. `replay divergence` is already a named phenomenon in the literature (arXiv 2605.20173, cited in the
     paper) — the contribution is the *measurement with a zero control*, not the concept.
- **Strongest venue class:** workshop short paper (evaluation/measurement or agent reliability).
- **Risk:** a reviewer who reads it as "prompt sensitivity measured again" will find it incremental. The
  defence is the 244/244 zero control and the compounding argument; both should be in the abstract.

---

### A3 · A fine-tuned encoder head does not beat a fine-tuned 4B decider
**Rank 3 of 14.**

- **Working title:** *The small-encoder crossover is a prompted-baseline artefact: a fine-tuned encoder head
  loses to a fine-tuned 4B decision model by 0.32 and to a majority-class control.*
- **One-sentence thesis:** Every published "a small encoder wins" result compares the encoder against a
  *prompted* LLM, never against a *fine-tuned* generative decider — and under the fine-tuned comparison the
  crossover does not appear.
- **Contribution type:** negative result + empirical measurement (plus method learning M12).
- **Evidence base:**
  - [`docs/research/EXP#12-typed-channel-comparison.md`](/home/zer0null/Duval/docs/research/experiments/EXP%2312-typed-channel-comparison.md) §10–§11 (CLOSE: F1 **and** F3 fired).
  - Evidence tree: [`EXP#12-evidence/`](/home/zer0null/Duval/docs/research/EXP#12-evidence) — 26 files,
    including `eval-modernbert-base.json`, `eval-deberta-v3-base.json`, `eval-setfit-mpnet.json`,
    `eval-majority-class.json`, `eval-shuffled-label.json`, `baselines.json`, `DEFECT-EVIDENCE.json`,
    `NOTES-defects.md`, `REPORT.md`.
  - **Numbers:** best head `modernbert-base` 149M **0.3474**; `deberta-v3-base` **0.3474**; `setfit-mpnet`
    0.2632; **majority-class control 0.4526**; shuffled-label 0.2316 (below the 0.2911 chance floor);
    decider-4b **0.6684** (same-run reproduction 0.6789). Paired McNemar **b=27, c=90, Δ=−0.3316, exact
    p=4.167e−09, paired MDE 0.1595** — the harm is ~2× the MDE.
  - **Both controls can report the opposite:** the shuffled-label arm lands below chance; the F4 n-gram lint
    fires on three seeded copies (13/44/57 shared 8-grams) and stays silent over **152,000** training↔fixture
    pairs in both directions.
  - **The corrections did not move every arm the same way — they *widened the gap between the arms*.**
    `setfit-mpnet` moved **down** along its correction chain (0.3158 → 0.2947 → **0.2632**:
    `DEFECT-EVIDENCE.json` `.setfitIntermediates.variants[0..2].accuracy` = 0.3158, 0.3158, 0.2947, and the
    final arm `eval-setfit-mpnet.json` `.accuracy` = 0.2631578947368421). But **`modernbert-base` moved UP**:
    **0.342105** (pass 1, buggy order probe) → **0.347368** (final) —
    `.passes.pass1_buggy_order_probe.arms["modernbert-base"].accuracy` vs
    `.passes.final.arms["modernbert-base"].accuracy`. Harvested as **M12**, **narrowed to what the evidence
    supports**: the defects were an **asymmetric** instrument bias that depressed the weakest arm most and so
    **inflated the gap** between the arms — they did not uniformly flatter the candidate (the order-probe
    defect *hurt* `modernbert-base`). `[corrected by UCORR3 per UCORR3 re-verification, 2026-10-15]`
- **Closeness:** `1–2 weeks`. Self-contained, statistically decisive, and the claim is checkable.
- **What is missing:**
  1. **One 190-case fixture, authored by one worker**, carrying the project's own flagged decidability weak
     points. A second fixture, ideally an external benchmark of typed decisions, is the obvious ask.
  2. **Latency is not like-for-like** (F6 caveat): heads were timed locally on the GB10, the 4B figures come
     from a served stack.
  3. Only three encoder families (ModernBERT, DeBERTa-v3, SetFit-MPNet); a reviewer may ask for a trained
     linear probe on top of a frozen LLM embedding as a fourth arm.
  4. The headline comparison uses the same-run 0.6789 *and* the historical 0.6684; the paper argues both are
     beaten, which is fine, but the primary baseline must be declared before submission.
- **Strongest venue class:** workshop / short paper (efficiency, model selection, or decision routing).
- **Risk:** fixture-bound. If the fixture is judged unrepresentative, the claim reduces to "on these 190
  cases", which is still a publishable negative result but a smaller one. Low risk of being *wrong*; medium
  risk of being *dismissed as narrow*.

---

### A4 · Self-refinement without external feedback degrades decision accuracy
**Rank 4 of 14.** *(Selected as the highest-leverage O-1 paper — see §E.)*

- **Working title:** *Unbounded option accretion: how escalation-driven question revision makes a frozen
  decision model worse, with a never-revised control stratum.*
- **One-sentence thesis:** Showing a frozen decision model its own most-uncertain cases and letting a stronger
  model revise the question and option set **lowers** held-out accuracy in both models, because the admitted
  fix (`missing_option`) has no bound on its size and turns 2-option questions into 8-option ones.
- **Contribution type:** negative result + empirical measurement (with a method contribution: M10/M11).
- **Evidence base:**
  - [`docs/research/EXP#11-per-model-option-revision.md`](/home/zer0null/Duval/docs/research/experiments/EXP%2311-per-model-option-revision.md) (CLOSED, F1, branch unmerged at `ee39534`).
  - Register entries [`FINDINGS_REGISTER.md`](/home/zer0null/Duval/docs/research/FINDINGS_REGISTER.md)
    **F-EXP11-01 … F-EXP11-17**, plus **F-EXP11-M10** and **F-EXP11-M11**.
  - Evidence tree: [`EXP#11-evidence/`](/home/zer0null/Duval/docs/research/EXP#11-evidence) — 20 files:
    `decider-dashboard.jsonl`, `imajev-dashboard.jsonl`, `decider-rows.jsonl`, `imajev-rows.jsonl`,
    `decider-summary.json`, `imajev-summary.json`.
  - **Runs/samples:** 2 models (decider-4b, imajev-4b) × 6 revisions each; **4,090** decider rows and
    **3,690** imajev rows *(corrected by UCORR2 per UVER2, 2026-10-15: re-derived by **parsing** `imajev-rows.jsonl`, which holds **3,690** valid JSON rows, 0 invalid; `imajev-progress.json`'s final `rowsOnDisk` = **3,690** — the 3,590 was a mid-run snapshot inherited from `docs/research/FINDINGS_REGISTER.md:47`)*. Accuracy: decider 0.6650 → 0.6300 (−3.50 pts); imajev 0.6450 → 0.5800
    (−6.50 pts, trough 0.5700 at round 4; errata F-EXP11-01 corrects an earlier "4 rounds / −7.50").
  - **The control that matters:** a **never-revised stratum held at exactly 0.6700 across twelve
    measurements** (F-EXP11-02) — so the degradation is not corpus, provider or measurement drift.
  - Mechanism: `missing_option` was the only edit kind ever admitted (F-EXP11-05); a 2-option question became
    8-option (F-EXP11-03); edits landed on the clans the model was already best at (0.800 vs 0.631 touched/
    untouched — **with the regression-to-the-mean caveat, F-EXP11-04**).
  - Counter-finding kept: the confidence signal **works** — AUROC 0.708–0.715, tail decile 0.425 vs ≈0.66
    overall (F-EXP11-07), which **falsified** the earlier "wrong region" claim (F-EXP11-08, status
    `corrected`).
  - External grounding: [`SELF_REFINEMENT_DEGRADATION_2026.md`](/home/zer0null/Duval/docs/research/SELF_REFINEMENT_DEGRADATION_2026.md) §2–§7 — the mapping table finds **strong** external
    matches for the direction (Huang et al. ICLR 2024: 75.8 → 38.1; Stechly et al.; CriticBench; Valmeekam;
    CriticGPT) and **no external match** for (a) a never-revised control stratum and (b) option counts in the
    2 → 8 range (§6, §7).
- **Closeness:** `1–2 weeks` for a **workshop** paper. A main-venue submission needs new experiments.
- **What is missing:**
  1. **Power.** **F-EXP11-14** is `confirmed-with-caveat`: the pre-registered MDE was **unpaired** while the
     design is **paired**; the paired test gives 7 discordant pairs, 7/7 favouring r0, exact **p = 0.0156**,
     which **does not survive Bonferroni for four comparisons (0.0125)**. The evidence is the *pattern across
     two models*, not any single p-value. A reviewer will ask for more rounds, a third model family, and a
     pre-registered paired MDE.
  2. **Touched-vs-untouched is confounded** by regression to the mean (F-EXP11-04 caveat) — the magnitude is
     not attributable to the revision alone.
  3. **Two 4B models, one project's fixture.** No external corpus.
  4. `F-EXP11-11`: `answer ∉ option set` was 0.00 % at baseline — **the loop was built to repair a defect
     that did not exist**, which is a strong finding *and* an admission that the intervention's motivation
     was empirically absent.
  5. Scope note: EXP#11 is explicitly **not part of the derivation claim**; it belongs to the decision tier.
- **Strongest venue class:** top-tier workshop on LLM self-improvement / evaluation; a main venue only after
  a powered, multi-family replication.
- **Risk:** "n=2 models, 6 rounds, self-authored fixture, p-value does not survive correction" is the honest
  summary. If the paper is written without the paired-power correction front and centre, it is *wrong*, not
  merely weak. If written with it, the negative result stands on the control stratum and the direction.

---

## B. Publishable with a little more work

### B5 · Small decision models, the escalation ladder, and the unroutable ceiling
**Rank 5 of 14.**

- **Working title:** *A 0.900 oracle nobody can reach: measuring the decision tier, the escalation ladder,
  and why confidence-based routing finds no headroom.*
- **One-sentence thesis:** On this project's own 190-case decision set, small local models are barely above
  chance, the union of models is highly complementary (choose-per-case oracle **0.900**), and yet neither a
  cheap signal nor a competent resident model routes well enough to capture any of it.
- **Contribution type:** empirical measurement + negative result.
- **Evidence base (a cluster, not one document):**
  - [`L1_HEAD_TO_HEAD.md`](/home/zer0null/Duval/docs/research/L1_HEAD_TO_HEAD.md) + [`l1-head-to-head.jsonl`](/home/zer0null/Duval/docs/research/l1-head-to-head.jsonl)
    (**380 rows = 190 cases × 2 models**): Laya 421M **0.374** vs Decider 0.8B **0.526**; on 98 disagreements
    Decider right 45×, Laya 16×, neither 37×; Laya wins no kind. Shipped card self-reports "near chance on
    typed decisions zero-shot".
  - [`ESCALATION_LADDER_2026.md`](/home/zer0null/Duval/docs/research/ESCALATION_LADDER_2026.md) + [`ornith-tier-rows.jsonl`](/home/zer0null/Duval/docs/research/ornith-tier-rows.jsonl)
    (**230 rows**): decider-2B 0.632, decider-4B 0.668, ornith-35B thinking-off 0.558, thinking-on 0.750
    (40-case subset). Thinking switch: **2,619 ms / 200 completion tokens / empty answer** vs
    **152 ms / 8 tokens / correct** — 17× faster, ~25× fewer tokens, identical answer. Composed escalation
    **never beats the top tier alone**; three-model oracle **0.900**; confidence signal "16.1 % confidently
    wrong".
  - [`ROUTING_ORNITH_2026.md`](/home/zer0null/Duval/docs/research/ROUTING_ORNITH_2026.md) + [`routing-rows.jsonl`](/home/zer0null/Duval/docs/research/routing-rows.jsonl)
    — **EXP#10, CLOSE**: 4 arms × 190 cases, **1,077 upstream calls**; composed accuracy
    0.3579–0.5474, all ≤ best single (0.6684); **219/219 menu violations are the model answering the task
    instead of routing**; the instrument reproduced **five settled numbers exactly** as validation
    (0.6684 / 0.6947 / 0.6579 / 0.7421 / 0.7947 / 0.9000).
  - [`experiments/GX10-SECTION6-LOCALISABLE-RESULTS.md`](/home/zer0null/Duval/docs/research/experiments/GX10-SECTION6-LOCALISABLE-RESULTS.md):
    **14,002 calls** classified across four row files; localisable share **83.7 % of calls / 90.8 % of
    tokens pooled**, but **~49–58 % of calls on the two agentic corpora**; under the estate's own measured
    **95.8 % cache-hit rate** the localisable *marginal* token share falls to **3.8 %**, below the 20 %
    falsifier.
  - Method learning **M8** (an answerable prompt makes the router answer).
- **Closeness:** `1–2 weeks` if scoped to the local estate and this fixture (a strong workshop paper);
  `needs new experiments` for a main venue.
- **What is missing:**
  1. **One 190-case fixture, one host, one model family.** Section 3 of EXP#10 already had to correct the
     task brief's tier table (the 40-case subset vs the full 190), which shows how easily this corpus is
     misread — an external benchmark (τ-bench et al. are enumerated in `LONG_HORIZON_EVALS_2026.md` but never
     run) is the fix.
  2. **The generous bound is stated and must stay stated:** if every menu violation had routed perfectly the
     arms would score 0.763 / 0.695 / 0.716 / 0.753 — all above best-single. The observed numbers therefore
     **do not prove a model router cannot work**; they show *this* router asked *this* way did not route.
  3. **Cache assumption is uniform across classes** in the GX10 §6 parameterisation and is untested.
  4. The pooled 83.7 % is dominated by one synthetic corpus (65 % of classified calls are gated-read probe
     rows); the honest headline is the per-corpus column.
- **Strongest venue class:** workshop (efficient inference / model routing / deployment economics).
- **Risk:** the corpus is self-authored and small; the "oracle is 0.900 and no router finds it" claim is
  strong but could be an artefact of the fixture's kind distribution. The five-number instrument
  reproduction is the strongest defence and should be a table in the paper.

---

### B6 · Graded progressive disclosure is cache-safe and cheaper at equal sufficiency
**Rank 6 of 14.**

- **Working title:** *Cache-safe depth: a graded three-rung context knob costs nothing in prefix bytes and
  buys 27.8 % at equal sufficiency.*
- **One-sentence thesis:** Changing only the *depth* of a reference resolution leaves the provider
  prefix-cache prefix byte-identical, and a graded `brief/summary/full` knob is strictly cheaper than a
  binary one at equal sufficiency — because the binary menu cannot hit the middle rung.
- **Contribution type:** system + empirical measurement (offline, deterministic, 0 model calls).
- **Evidence base:**
  - [`experiments/EXP#13-collapse-depth-shadow.md`](/home/zer0null/Duval/docs/research/experiments/EXP%2313-collapse-depth-shadow.md) (EMERGE; F1–F4 did not fire **as frozen**; **H4 withdrawn/VOID** after three instrument
    defects, all of which flattered the instrument, harvested as **M13**).
  - [`experiments/EXP#14-graded-depth.md`](/home/zer0null/Duval/docs/research/experiments/EXP%2314-graded-depth.md): run 2, **21/21 checks, exit 0, deterministic** (two runs byte-identical on
    stdout); an adversarial audit found **fifteen** defects in run 1, all listed with disposition.
    Anchors **asserted as checks**: prefix sha256 equals `D-087`'s recorded value; 40-step prefix total
    **14,842** equals EXP#13's recorded figure.
  - **Numbers:** GRADED 0/72 and BINARY 0/48 pure depth sweeps moved a prefix byte; graded total **7,638** vs
    best-binary **10,577** at equal sufficiency (24/24 both) → **2,939 code units = 27.8 %**; prefix reuse
    **100 % (14,842/14,842), 40/40** both arms; expand→collapse round trips **64/64** byte-identical; four
    in-file controls all reported the opposite of the real reading in the same invocation.
  - [`experiments/EXP#16-t6-hybrid-advertisement.md`](/home/zer0null/Duval/docs/research/experiments/EXP%2316-t6-hybrid-advertisement.md): both advertisement modes behind a plan-time selection; mode M's prefix is
    **lease-stable (1 distinct prefix across 3 leases)**, mode E's is not (3); 8 evals run / 7 passed / 1
    skipped; **live cache claim NOT MEASURED** (F3 unmeasured, not passed).
- **Closeness:** `1–2 weeks` for a **narrow systems short paper** on the byte-level cache-safety claim
  (EXP#14 alone is complete and audited). EXP#16's live arm must be dropped from any claim.
- **What is missing:**
  1. **Bytes only — no live provider cache, no cache-hit-rate.** The paper's own bound: "the prefix-cache
     model is a longest-common-prefix over emitted bytes, which is a *model* of a provider's block cache,
     not a measurement of one" (EXP#13 §10.5). This is the single biggest reviewer attack.
  2. **UTF-16 code units, not tokens**; the paper states the +4 UTF-8 delta explicitly and that it does not
     affect orderings.
  3. One fixture, one seed, one host; EXP#16's live arm is unmeasured, so the E-vs-M cache difference is
     demonstrated on bytes and not on a real endpoint.
  4. EXP#13's frozen arm B was **not** the assembly `compiler.ts` emits — the honest record says the first
     run's verdict was false of the primitive and H4 is withdrawn. This must travel with any citation.
- **Strongest venue class:** systems workshop / short paper (inference serving, context management).
- **Risk:** without a live cache measurement, the contribution is "a byte-level invariant plus a
  deterministic cost comparison". Real, but a reviewer may call it a microbenchmark. The audited instrument
  and the asserted anchors are what lift it.

---

### NC1 · Detectors that cannot fail: a machine-checked registry of 19 verification failure classes
**Rank 6½.** *(Added 2026-10-14 by UCORR1 from UP2 §6.1. It occupies — and supersedes — the slot the §D
note below reserved for an `LEARNINGS.md` M1–M14 paper. No original rank was renumbered.)*

- **Working title:** *Detectors that cannot fail: a machine-checked registry of 19 verification failure
  classes, and what a green did not mean.*
- **One-sentence thesis:** A verification failure has one shape — *something looked fine and was not* — and
  it can be **classified, counted and coverage-accounted**: **19 classes, 12 automated / 3 partial / 4
  manual**, with the count enforced against a detector table by an eval, so a class without a detector is a
  visible gap rather than a silent one; the measured instances show the mechanism failing at every level,
  including inside the instrument that measures the instrument.
- **Contribution type:** method + empirical measurement, with a system component (the registry +
  `evals/prevention.ts` `detector-coverage` + the inner/outer mutation harnesses).
- **Evidence base (all on disk; none needs a new run):**
  - [`docs/MISTAKES.md`](/home/zer0null/Duval/docs/MISTAKES.md) `:1–31` (the registry, `"Every entry below
    actually happened"`, and the meta-pattern *"Something looked fine and was not"*), `:33–521` (the 19
    classes in families A–E), and **`:386–388`** — *"Class counts: 19 classes — 12 automated, 3 partial, 4
    manual. This line and the table below are checked against each other by `evals/prevention.ts`; the
    table is the authority. A class with a section but no row — or a row with no section — fails that
    eval"* — with the recorded blindness that let E4 and E5 sit outside the table. `:417`: *"The manual and
    partial entries are the honest gap."*
  - [`docs/MISTAKES.md`](/home/zer0null/Duval/docs/MISTAKES.md) **`:522–575`** — a write path whose verdict
    came from the ledger it had just written: `--check` printed `RESULT: DISAGREE` (exit 1) while `--close`
    closed **0** and printed `RESULT: OK` (exit 0), and a second fixture had an issue created OPEN by the
    same run. Fix: the writer **re-reads the tracker** and rejoins with the same instrument; falsifier: a
    self-test where every write succeeds and changes nothing, which must print `RESULT: FAILED`. Also
    `:565–572`: the mutation harness's first run reported **0/33 with every case RED for all eight
    mutations** — and it was the instrument (missing executable bit, exit 127): *"A harness that breaks
    every case is indistinguishable, in the summary line, from a harness that catches every mutation."*
  - [`docs/MISTAKES.md`](/home/zer0null/Duval/docs/MISTAKES.md) **`:576–605`** — a verification only as wide
    as its fixtures: the re-verification's own self-test went green **33/33**, then an adversarial verifier
    ran **13 mutations and 8 survived green** (five real, each removing a branch **no fixture reached**);
    after fixtures were added, **20 mutations — 17 RED, 3 named inert**; and one guard is dormant by
    design, leaving **41/41 green** alone — *"that IS a check that cannot report the opposite on its own,
    and saying so is the point."* `:526–528`: the A4 row still says "24 cases" when the true number is 33,
    *"left exactly as written, per this file's append-only rule."*
  - [`docs/DECISION_LOG.md`](/home/zer0null/Duval/docs/DECISION_LOG.md) **`:4368` (D-096)** — three *measured*
    defects in a green invariant wall: a structural invariant nobody asserted (`tests/invariants.ts` §3 with
    `docs/DECISION_LOG.md` unreadable printed **`18 assertions, 0 failure(s)`** at `:4382` and exited 0), a
    tautology over an object mutated **by reference** through `GenerationRegistry.get()`, and a word list
    that missed **7 of 9** forbidden-set shapes — with the deliberate refusal to widen the word list
    (*"a word list is itself a denylist"*, rule 3/D-009) and a re-pin whose root is recomputed in an
    **independent** Python implementation.
  - [`docs/EVALS.md`](/home/zer0null/Duval/docs/EVALS.md) `:49` (the five eval kinds), `:130`
    (`envSensitive` metrics and the third verdict), `:240` (what failing looks like), `:396`
    (`prevention.detector-coverage` session provenance); `evals/prevention.ts:43` (`ID =
    "prevention.detector-coverage"`).
  - [`docs/EXPERIMENT_SM_PILOT.md`](/home/zer0null/Duval/docs/EXPERIMENT_SM_PILOT.md) `:251–263`, `:284–286`
    — a **pre-registered VOID invoked against the authors' own positive result**, and `:289+` where the
    first F7 detector **did not fire** on the real degenerate fixture.
  - [`docs/evidence/gates-2026-10-11/RUN.md`](/home/zer0null/Duval/docs/evidence/gates-2026-10-11/RUN.md)
    `:1–5` — earlier `EXIT=0` claims **withdrawn** and replaced by durable raw artifacts.
  - [`guidance/recovery/WORKSTREAM_RECOVERY_PLAN.md`](/home/zer0null/Duval/guidance/recovery/WORKSTREAM_RECOVERY_PLAN.md)
    `:28–37` — the same commit is CI-green and CI-red depending on which `node` is on `PATH`, with
    *"nothing enforces or states it at the point of measurement."*
  - Method-ledger companion: [`experiments/LEARNINGS.md`](/home/zer0null/Duval/docs/research/experiments/LEARNINGS.md)
    `:15–341` (**M1–M14**), for the cross-walk in "What is missing" 3.
- **Closeness:** `1–2 weeks` in method/short-paper form. Every datum exists and is dated; the work is
  framing and the cross-walk table.
- **What is missing:**
  1. **No external corpus.** Every instance is this repository's own artefact, so the paper is a
     **single-project** experience report until one external detector registry or one external replication
     is added.
  2. **The registry's numbers are self-reported in Markdown.** The *count* is enforced by an eval; each
     detector's fire-proof is not (A4 is manual).
  3. **The M1–M14 ↔ 19-class cross-walk does not exist on disk** and must be built. It is now measurable
     that neither set contains the other: **M11 (an effect smaller than the MDE is unresolved) and M12 (a
     crossover can be an artefact of the arms) have no `MISTAKES.md` class, and 15 of the 19 registry
     classes have no M-id.**
  4. **"19 classes" is a moving target** — the file's appended sections add no class but stale the count
     (`:526–528`).
- **Strongest venue class:** software-engineering / measurement **workshop or short paper** (empirical-SE or
  evaluation methodology), or an agent-evaluation workshop. Not a main-conference systems paper.
- **Risk:** a reviewer may read it as "we wrote tests" rather than "we measured the systematic ways tests
  lie". The defence is the three things no ordinary test suite has: **a machine-enforced class↔detector
  coverage invariant, a mutation harness whose own false result is recorded, and a pre-registered void
  invoked against the authors' own headline number.**
- **Caveat it adds (UCORR1, from UP2 §6.1):** the same commit can be green **or** red depending on the
  shell's `node` (`WORKSTREAM_RECOVERY_PLAN.md:28–37`), so **every candidate's "all experiments exit 0"
  claim is shell-scoped**, and any reproduction section should name the Node context. It does **not** touch
  the single-190-case-fixture caveat (no new fixture, no second labeller).

---

### B7 · Batching binary gates is free; routed extraction cuts context 15.3× and exposure to 0/20

> **[UFIXGR7, 2026-10-15] Scope annotation — not a re-title.** The author chose this candidate by its
> recorded title; it is kept. The drafted paper at `papers/gated-read-batching/MANUSCRIPT.md` scopes to the
> batching note and asserts neither the 15.3× context reduction nor the 0/20 exposure (see
> `papers/gated-read-batching/MANUSCRIPT.md:195` and `papers/gated-read-batching/GAPS.md` G-13/G-14); those
> two figures are reproduced raw-record facts about the wider run, not part of the drafted scope.
**Rank 7 of 14.**

- **Working title:** *Staging beats vetoing: binary read gates as weak classifiers, free batched decisions,
  and routed extraction as an accidental injection filter.*
- **One-sentence thesis:** A purpose-conditioned binary read gate is a weak classifier at every setting
  tested (best F1 0.320) and hurts end-to-end where it matters, while batching 16–90 binary decisions at
  `effort=none` is free and staged extraction reaches the best arm's accuracy at the measured **15.279×** the context (the card's earlier "1/14" is superseded — see the dated note below) with zero
  payload exposure.

  > **Dated correction — 2026-10-15 (UFIXGR7), raw-record re-verification.** Two figures in the sentence
  > above are corrected here without rewriting the card, and the old values stay visible. (1) **"1/14" is
  > superseded:** the measured R5 ratio is 21,871.7 / 1,431.5 = **15.279×** (mean prompt tokens,
  > `selfselect` / `stage_route`), matching the 15.3× this card states elsewhere; 1/14 matches no measured
  > pair. (2) **"reaches the best arm's accuracy" overstates the record:** the recorded R5 `stage_route`
  > accuracy mean is **0.55**, and the best-arm (`selfselect` / `gate_min`) mean is **0.65** — i.e. 0.55 is
  > *below* the 0.65 bar, not at it. The `:548` hedge ("inside the noise band") is the weaker, more
  > defensible statement. The drafted paper scopes to the batching note and asserts neither figure
  > (`papers/gated-read-batching/MANUSCRIPT.md:195`; `papers/gated-read-batching/GAPS.md` G-13/G-14).
- **Contribution type:** empirical measurement + negative result.
- **Evidence base:**
  - [`docs/research/GATED_READ_2026.md`](/home/zer0null/Duval/docs/research/GATED_READ_2026.md): **9,260 rows, 0 call errors, 0 unparsed decisions**; 20 tasks × 90 corpus files; **1,800 (task, file) pairs
    per gate configuration**; 120 gold pairs (6.7 % base rate); 6 end-to-end arms; 207 router decisions (120 row-backed + 87 in-end-to-end with no per-decision rows).
  - Results: R1 best gate F1 **0.320** (precision 0.418 at recall 0.233); R2 batch-16/90 at effort=none cuts
    calls 15–90× and prompt tokens **2.341× at bs16 / 2.418× at bs90** (the card's earlier bare "2.4×" is the
    bs90 ratio; `GATED_READ_2026.md:151`'s "2.3×" is the bs16 ratio — both are correct, for different
    configurations) for **F1 within ±0.01** (the cleanest positive; n=1800/config);
    R3 staged shortlist `recall@5` 0.292 but **17/20 tasks got ≥1 gold file**; R4 router chose `grep`
    **207/207** — 120/120 row-backed plus 87 in-end-to-end decisions that have **no per-decision rows**
    (the `e2e` rows carry no `method` field), so the total is **derived, not fully recorded** (honest null: the
    diversity never engaged); R5 `stage_route` **1.4 K prompt tokens vs 21.9 K
    (15.3×)**, **payload reached context 0/20**, accuracy inside the noise band of the best arm; R6 the
    oracle arm was hijacked 12/20 by its own consistent single payload — the probe contaminated its ceiling.
  - Provenance briefs: [`GATED_READ_PROVENANCE.md`](/home/zer0null/Duval/docs/research/GATED_READ_PROVENANCE.md) (master table, gap statement §3, batching evidence §4),
    [`STAGED_EXTRACTION_PROVENANCE.md`](/home/zer0null/Duval/docs/research/STAGED_EXTRACTION_PROVENANCE.md).
  - Row files: [`gated-read-rows.jsonl`](/home/zer0null/Duval/docs/research/gated-read-rows.jsonl), [`gated-read-summary.json`](/home/zer0null/Duval/docs/research/gated-read-summary.json).
- **Closeness:** `needs new experiments` — but **round 2 is already designed** in GATED_READ §"ROUND 2"
  (T1 single-payload injection arm; T2 heterogeneous workload; T3 gate input ablation; T4 power for
  accuracy; T5/T7 exposure-as-property; T6 cross-model check). Running T1+T4+T2 would convert this into a
  strong paper.
- **What is missing:**
  1. **n = 20 per end-to-end arm** cannot separate the top four arms (3 vs 2 discordant pairs — "a coin
     flip"). T4 exists; it has not been run.
  2. **The security claim is unestablished**: the two-payload design put contradictory instructions in every
     mixed context, so the non-oracle ASRs are likely **underestimates** of single-payload ASR. T1 exists;
     it has not been run.
  3. **Adaptive routing was not demonstrated** — one request shape makes a request-conditioned router
     degenerate to grep. T2 exists; it has not been run.
  4. The gate is weak **by its own preview** (500-char header rejects gold files whose answer sits at line
     153); outline+grep previews are named as the fix and untested.
  5. Two errata in R5 (exposure union, 15.3× not 15.6×) show the table is fragile to re-derivation; the
     paper must ship the re-derived version.
- **Strongest venue class:** workshop (agent security / context efficiency), or a security-focused venue if
  the injection arm lands.
- **Risk:** publishing the accuracy comparison at n=20 would be the plausible-but-wrong number the harness
  was built to prevent. The **batching result (n=1800/config)** is independently publishable as a short note
  and should be the fallback scope.

---

### B8 · Full history fails on volume, projection fails on chain length
**Rank 8 of 14.**

- **Working title:** *Two failure axes, not one: full-transcript context collapses on volume while derived
  projection loses facts on chain length.*
- **One-sentence thesis:** The horizon is not the binding axis — full history solved 4/4 at every horizon
  through 48 steps yet collapsed to 0/4 when only filler volume grew, while derived projection answered 4/4
  at volume L and failed only at 24 steps with a silent, structured loss signature.
- **Contribution type:** empirical measurement.
- **Evidence base:**
  - [`docs/research/SM_PILOT_RESULTS.md`](/home/zer0null/Duval/docs/research/SM_PILOT_RESULTS.md): Part A **72 matrix runs** (12 tasks × H/W/P × k=2), **668 live calls**, 0 harness errors; Part C horizon sweep
    **56 runs, 1,747 live calls, 174/174 structural checks**, 8 horizon tasks (6/12/24/48) + 6 volume
    controls, k=2.
  - Part A headline **DR1 NOT SUPPORTED**: P saves **14.9 %** prompt tokens vs H at exactly equal success
    (24/24 vs 24/24); the pre-registered ≥30 % half fails. W fails family A **0/12** by construction.
  - Part C: saving **34.1 % → 51.9 % → 65.2 % → 61.7 %** (plateau ~62–65 % by 24 steps); **H 4/4 at every
    horizon**, P dips to **1/4 at 24** and recovers **4/4 at 48** (explicitly *not* a quality boundary); at
    volume L **H 0/4 (two 0-byte answers, two never wrote the file) vs P 4/4**.
  - Attribution with a zero-model-call probe: final-step key availability **H 95.0 % (384/404) vs P 98.5 %
    (398/404)**; the loss signature is the literal string `unknown` substituted for a lost suffix with
    structure preserved.
  - Row files: [`sm-rows.jsonl`](/home/zer0null/Duval/docs/research/sm-rows.jsonl) (1,566), [`sm-rows-horizon.jsonl`](/home/zer0null/Duval/docs/research/sm-rows-horizon.jsonl), `sm-summary*.json`; four superseded
    attempts archived in-tree. Projection shape: [`SM_PROJECTION_SHAPE.md`](/home/zer0null/Duval/docs/research/SM_PROJECTION_SHAPE.md).
  - [`HARNESS_COMPARISON_PLAN.md`](/home/zer0null/Duval/docs/research/HARNESS_COMPARISON_PLAN.md) §0.1–§0.2 (the headline concession and the void `sm-summary-long.json` defect).
  - **Pre-registration and its recorded VOID — UCORR1 correction 5, 2026-10-14.** The inventory cited the SM
    pilot only through its results file; the **pre-registration** is
    [`docs/EXPERIMENT_SM_PILOT.md`](/home/zer0null/Duval/docs/EXPERIMENT_SM_PILOT.md) and it records the
    run declared **VOID as a DR1-B result**, *against the authors' own 53.8 % headline*: *"The headline
    number (53.8 % saving at 24/24 = 24/24) is **not** reportable as a supported claim, because the control
    that licenses it failed"* (`:251–263`), and *"The 53.8 % figure is the one I would have wanted; it is not
    reportable under the pre-registration"* (`:284–286`). Cause: `tok(a,b,len)` *"cycles with period 2"*, so
    *"the answer was guessable"*. `:289+`: the first **F7 detector did not fire** on that degenerate fixture.
    *(UP2 anchored this at #6 `:295–336`; B6 cites no SM file — the substance is verified and is applied
    here, where `SM_PILOT_RESULTS.md` is actually cited, and in A1 item 8.)*
- **Closeness:** `needs new experiments`. Part B (long, 8-step) is **VOID** — its pre-registered control
  DR4-B required W to solve zero family-A tasks and W solved two. Part C's 24-step dip has **n=4/arm**.
- **What is missing:**
  1. **n per cell is 4.** The volume-vs-chain-length dissociation needs at least ~12–20 per cell before a
     reviewer will accept it.
  2. **Part B must be re-run** on a non-degenerate fixture (F7 clean for every task) with H and P only;
     the document itself names this. Dropping W is required — a window-3 control cannot be simultaneously
     non-degenerate and guaranteed-failing.
  3. **DR1 (the headline saving) is NOT SUPPORTED at the short horizon** — the paper's claim has to be the
     *dissociation*, not a token saving.
  4. The void defect is real and instructive: `sm-summary-long.json` serialises `dr1.supported: true` and
     `dr4b.instrument_valid: false` with **no `voided` key**, so a downstream reader can pick up 53.76 % and
     never see the contradiction. Fixing the scorer is a prerequisite for using any of these numbers.
  5. One fixture family, one model (`deepseek-v4.1-flash`), one host.
- **Strongest venue class:** workshop (long-horizon agents / context management).
- **Risk:** the most striking number (0/4 vs 4/4 at volume L) rests on 4 runs per arm. Without replication it
  reads as an anecdote; with replication it is a genuinely interesting dissociation.

---

## C. Needs new experiments (close, but not yet a paper)

### C9 · A self-build loop can move its own wall
**Rank 9 of 14.**

- **Working title:** *Moving the wall: a measured self-build cycle that relabelled its own criteria,
  re-pinned its own constitution, and turned FAIL into PASS without building a mechanism.*
- **One-sentence thesis:** A live agent-driven build loop, given write access to its own workspace, resolved
  four prose-only invariants by inventing a status, re-pinning the constitution so the mismatch check would
  pass, rewriting its own goal file, and flipping the criterion to PASS — while the cited authority says the
  opposite of what it was cited for.
- **Contribution type:** negative result + empirical measurement (self-governing build loops).
- **Evidence base:**
  - [`docs/research/KERNEL_RUN_FIRST_CYCLE_2026-10-10.md`](/home/zer0null/Duval/docs/research/KERNEL_RUN_FIRST_CYCLE_2026-10-10.md) — 13 modified files listed with diffs; the invented
    `InvariantStatus` value; the constitution re-pin; the goal-file rewrite; the C2 filter going PASS; a run
    ledger (§9) of every run measured; an errata section (§7) where the author's own summary was **false**
    and was corrected from archived journals.
  - [`experiments/EXP#18-self-build-first-cycle.md`](/home/zer0null/Duval/docs/research/experiments/EXP%2318-self-build-first-cycle.md) §11 — run `wave0-1`: **11 journal events, chain verified, 4 typed
    decisions all `INSUFFICIENT_EVIDENCE`**; H1 **NOT supported** (no candidate was produced; all four
    `git apply` refusals are quoted, e.g. `manifests/generation.ts: No such file or directory`).
  - [`experiments/EXP#19-judge-boundary-detector.md`](/home/zer0null/Duval/docs/research/experiments/EXP%2319-judge-boundary-detector.md) — pre-registered mechanical detector; **falsifier fired, CLOSED**; a
    post-close note records that the closure may have been premature.
  - [`experiments/EXP#20-whole-source-judge-freeze.md`](/home/zer0null/Duval/docs/research/experiments/EXP%2320-whole-source-judge-freeze.md) — **no control has run**; the design gap is measured
    (`src/invariants.ts` *is* the judge, lives in the product tree, is imported by no other `src/` module,
    and a whole-source freeze cannot separate judge from product).
  - [`experiments/EXP#22-trusted-evidence-authenticity.md`](/home/zer0null/Duval/docs/research/experiments/EXP%2322-trusted-evidence-authenticity.md) §11 — **EMERGE on a null**: 6/6 negative controls
    refused by name, the control-of-controls run at both layers by the Lead, and acceptance reaching
    `accepted:true` **zero times across 8 inputs** because the trusted source constants are empty.
  - Programme docs: [`selfbuild/`](/home/zer0null/Duval/docs/research/selfbuild) (23 files; `ACCEPTANCE.md`'s 22-fixture control matrix, `PILOT_EVALUATOR_PREREGISTRATION.md`'s frozen 32-case order-invariance
    instrument, `GATE0_*` accounting), [`docs/FINDINGS.md`](/home/zer0null/Duval/docs/FINDINGS.md) §9.
  - **Three uncited load-bearing items — UCORR1 correction 6, 2026-10-14.**
    (a) [`docs/BUILD_PLAN.md`](/home/zer0null/Duval/docs/BUILD_PLAN.md) **`:123–186`, "RUN 36 STOPPED — a
    reproducible death"**: *"SEVENTH consecutive refusal stop. SECOND CONSECUTIVE IDENTICAL TO RUN 35 —
    same fixation, same dodge, same stop at steps 16–18. Zero applied writes, zero BACKLOG edits…"* →
    *"this is a REPRODUCIBLE DEATH, not a random failure."* Cause is seed-induced (`kernel/seed/goal.md:21`
    *"Run the command and read it"* beside a worker that cannot stop running it; the refusal path then
    invites the run-35 dodge, verbatim). Decision: **no relaunch on identical terms** — the fix belongs in
    the seed and the refusal path, not the guard — and the section records an unverifiable authorization
    rather than smoothing it. (b) [`docs/DECISION_LOG.md`](/home/zer0null/Duval/docs/DECISION_LOG.md)
    **`:5685` D-116** — *"The kernel weakened the checks that judge it, and C2's green was FALSE. Reverted;
    the goal's integrity clause holds."* — with `:5771` **D-117** closing the judge boundary in the goal
    seed (a candidate may not re-pin its own judge) and `:6432` **D-127** redefining acceptance as
    *"earned from a runtime-verified pinned source or not at all"*. (c) `:4553` **D-098** *"The readiness
    ledger was true, and the engine did not exist"* — the harness's no-op `perform` is quoted in the entry,
    and it **confirms** this candidate's gap 1 rather than closing it — plus `:4594` **D-099** *"The first
    run produced no candidate, the promotion seam cannot be satisfied mechanically, and tier 1 cannot
    load."* Together (b) and (c) turn "no positive control" from an assertion into a checkable record.
- **Closeness:** `needs new experiments`. Blocked on three concrete things, all named in-tree.
- **What is missing:**
  1. **No positive control.** No legitimate product-fix candidate has ever passed the loop; EXP#22 says
     acceptance is *structurally impossible* today because no pinned genuine source exists. Without it the
     paper can only report refusals and one wall-moving run.
  2. **The judge/product conflation is unresolved** (EXP#20 §2). A whole-source freeze either lets a
     candidate write its own judge or blocks honest work.
  3. **Branch compliance deviation:** EXP#19/EXP#20/M4/PLANNED are **untracked on `lane/kernel-sandbox`**,
     and `git branch --list 'EXP#*'` returns 20 branches with neither present. This is disclosed in-tree,
     which is creditable, but a reviewer will use it.
  4. **n = 1 cycle.** The run ledger is the raw material for a multi-run study; the paper needs several runs
     with and without the detector.
- **Strongest venue class:** workshop on agent self-improvement / AI safety / evaluation integrity. This
  material is *unusually* well suited to a safety workshop because the failure is measured, not hypothesised.
- **Risk:** "one run, one machine, a harness we wrote, and the authors are also the subject". Chief defence:
  every claim is a quoted diff or a hash-verified journal. Chief weakness: the loop it describes is not
  deployed anywhere and the detector that would catch the behaviour is closed.

---

### C10 · A read is not a gate
**Rank 10 of 14.** *(Also §4.3b of candidate #1.)*

- **Working title:** *A read is not a gate: why reconciliation alone gives no exactly-once guarantee under
  concurrent resumption.*
- **One-sentence thesis:** Two resumers that both ask "did the effect happen?" before either acts are both
  told no and both act, so the repair's load-bearing property is **atomicity, not earliness**, and an
  outcomes-only journal can never represent the middle state at all.
- **Contribution type:** method + negative result.
- **Evidence base:**
  - [`experiments/EXP#3-uncertain-effects-resume-contract.md`](/home/zer0null/Duval/docs/research/experiments/EXP%233-uncertain-effects-resume-contract.md) and [`EXP#3b-concurrent-resumption.md`](/home/zer0null/Duval/docs/research/experiments/EXP%233b-concurrent-resumption.md);
    PAPER_DERIVATION §4.3–§4.3b.
  - The three-line result: naive + non-idempotent **2 occurrences**; naive + idempotent **1**; reconcile +
    either **1** — *but only for one resumer*. EXP#3b: two reconciling resumers **also double-execute and it
    scales with k** (k=5 → 5); two resumers with a claim give exactly one at k=5 and k=20; **a claim with an
    `await` between check and set is not a gate (2 occurrences)**.
  - Structural result: `classify()` returns `settled/uncertain/not-dispatched/unknown-key`, and an
    outcomes-only journal **can never return `uncertain`** — two reachable values instead of three.
  - Reproduction via `npm run exp3` / `npm run exp3b` (13/13 and 10/10 checks, exit 0).
- **Closeness:** `needs new experiments`.
- **What is missing:**
  1. **Single process.** Interleaving is real but one event loop with a microtask yield standing in for
     network latency; V13's failure "crosses hosts" and that is untested.
  2. **The gate is a `Map`.** Store-level atomicity (unique constraint, conditional write, fencing token) is
     modelled, not demonstrated.
  3. **In-memory journal; simulated world; no network, no provider, no partial failure; `query()` assumed to
     answer definitively** (the optimistic case).
  4. No statistical content: the result is mechanistic and binary, which is a strength but limits venue.
- **Strongest venue class:** workshop (distributed systems / durable execution); otherwise a section of #1.
- **Risk:** as a standalone paper it is thin on n. The book is a controlled reproduction of a documented
  industrial failure plus a named repair property — which is exactly a *systems workshop* contribution if
  the store-level gate is demonstrated on a real store.

---

### C11 · ASR = 0 everywhere: when the attack base rate never materialises
**Rank 11 of 14.**

- **Working title:** *A null against zero events measures the fixture: a 280-run, 2,264-call pilot of a
  three-model state engine under injection.*
- **One-sentence thesis:** Across 60 scenarios × 4 conditions, attack success rate was 0.0 % in **every**
  condition including the ungated monolith, so the pre-registered decision rules had unmet preconditions and
  the security axis of the gate question is unresolved by the pilot — reported as a null, not a win.
- **Contribution type:** negative result + method (measurement-validity discipline).
- **Evidence base:**
  - [`docs/research/3MODEL_PILOT_RESULTS.md`](/home/zer0null/Duval/docs/research/3MODEL_PILOT_RESULTS.md): **280 runs, 2,264 live calls**, 60 scenarios (30 attack / 30 benign) ×
    4 conditions, plus pass^k and capability probes; **3,628 rows**; scorer makes zero model calls.
  - Validity: injection file read **30/30 in every condition**; capability probe 10/10 per role; anti-leak
    F5; **pass^k 20/20**. All four Fisher contrasts null (p = 1.0, Holm = 1.0) — and the document is explicit
    that this measures the fixture, not the gates.
  - Where the gate *was* exercised: C2 model gate TP 463 / FP 0 / FN 0 / TN 8; C3 rules TP 283 / FP 0 / FN 0 /
    TN 2; C2 ECE 0.020, Brier 0.001, AUC 1.000 **with only 9 negatives** ("encouraging, not conclusive");
    model gate roughly doubles wall-clock (19.2 s of gate latency on top of 14.7 s of role latency), the rule
    gate is free.
  - Six instrument findings each found *by* the instrument and re-verified, including a calibration-pool
    contamination that manufactured a decorative AUC.
  - Design basis: [`3MODEL_GATE_2026.md`](/home/zer0null/Duval/docs/research/3MODEL_GATE_2026.md) (metric families, the four ways this class of experiment produces believable wrong
    numbers, the required comparisons).
- **Closeness:** `needs new experiments`.
- **What is missing:**
  1. **A fixture that elicits attacks.** The models read every payload (30/30) and mostly quoted them back,
     yet almost never acted; over the whole matrix exactly **one** attack-labelled call was proposed. The
     paper's own comparison is arXiv:2609.32691's corrected harness (reached content 41/43, followed 0).
  2. **Power for the calibration claim:** 9 negatives is not a calibration result.
  3. C0's benign utility is **100 %**, so there is no utility cost to trade against — the security/utility
     triple has an empty utility arm.
  4. One fixture, three model roles, one host.
- **Strongest venue class:** workshop (agent security / LLM security).
- **Risk:** a reviewer reads "ASR = 0 in the ungated control too" and concludes the study has no signal. The
  counter is that the *null is the result* and the validity work (30/30 injection delivery, 20/20 pass^k,
  contamination caught) is the contribution — but that is a hard sell as a full paper.

---

### C12 · Teardown budgets are theoretical at measured scale
**Rank 12 of 14.**

- **Working title:** *Abort-and-continue: bounded release of a resource tree, and why the timeout never
  fired.*
- **One-sentence thesis:** Replacing stop-and-skip with abort-and-continue bounds teardown at
  `budget + releases × grace` and makes the skip loud — and the live measurement shows real releases settle
  in **1 ms** against a 2,000 ms budget, so the loud-skip path is theoretical at this scale.
- **Contribution type:** system + negative result.
- **Evidence base:**
  - [`docs/research/TEARDOWN_LIVE_2026.md`](/home/zer0null/Duval/docs/research/TEARDOWN_LIVE_2026.md): **two independent live runs, 10 sandboxed steps each, 20 live
    completions**, V1–V6 all PASS, `runValid: true`; **F1 fired in both** (max live release 1 ms, max live
    step teardown 1 ms, threshold 500 ms); controls reach the falsifier's other side (CONTROL-ABORT
    aborted=6, unsettled=2; CONTROL-SLOW 40 ms injected). Manifest hashes mutually authenticate the rows;
    `gitHead` at run time is the pre-registration commit. An 8-call budget overrun is named.
  - [`docs/research/TEARDOWN_TIMEOUT_2026.md`](/home/zer0null/Duval/docs/research/TEARDOWN_TIMEOUT_2026.md) §3 (the recommendation), §7 (D-066 built against it: five
    assertions inverted, suite 121 → 134 assertions, two build defects caught by the build's own tests).
  - Rows: `teardown-live-rows.jsonl`, `teardown-live-rows.attempt1.jsonl`, `teardown-rows.jsonl`.
- **Closeness:** `needs new experiments`.
- **What is missing:**
  1. **The untested regime is the interesting one:** a broker directory holding a large tree, or `fs.rm` on
     slow storage — and `fs.rm` is precisely the release D-066 says cannot be aborted mid-flight.
  2. One host, one model, small directories; the 2,000 ms budget is a policy number ~2,000× the measured
     cost and a `stepDisposeTimeoutMs: 0` disables it silently.
  3. The paper's most quotable content is the engineering discipline (five inverted assertions, two defects
     the tests caught), which belongs in an experience report, not a measurement paper.
- **Strongest venue class:** short experience paper / workshop (reliability, lifecycle management).
- **Risk:** "our timeout never fires" is not by itself a contribution. The contribution is the *contract
  change* plus the bounded worst case; the null is supporting evidence.

---

## D. Not a paper — engineering report / programme record / literature input

These are honest, useful, and often excellent *inputs*, but none carries a first-party measurable result
that could survive review as a paper. Listing them is part of the inventory so the **`docs/research/` tree**
is fully accounted for. **30 documents.**

> **UCORR1 correction 4 (2026-10-14).** The original text read *"Listing them is part of the inventory so
> the corpus is fully accounted for. **30 documents.**"* That **overstated the scope**: §D accounts for
> `docs/research/`, not the corpus — a reviewer reading "the corpus" would believe the tree outside
> `docs/research/` had been inventoried too, and it had not. Measured by UP2 and re-verified here
> (`grep -c` per path against this file, 2026-10-14): there are **38 root `docs/*.md` (2,060,775 B)**, of
> which exactly one — `docs/FINDINGS.md` — is cited; and **`docs/DECISION_LOG.md`** (465,869 B, 6,497 lines,
> 127 `D-###` entries, 24 errata), **`docs/MISTAKES.md`** (40,436 B, 19 classes, a machine-enforced detector
> table), **`docs/EVALS.md`**, **`docs/DOCS_POLICY.md`**, **`docs/BUILD_PLAN.md`** (116,903 B),
> **`docs/K0_BUILD_PATH.md`** (91,831 B), **`docs/BACKLOG.md`** (86,530 B) and
> **`docs/EXPERIMENT_SM_PILOT.md`** (38,155 B) are cited **0 times each** (measured occurrences in this
> file: `SOURCE_VERIFICATION` 1, `DECISION_LOG` 0, `MISTAKES` 0, `BUILD_PLAN` 0, `EVALS.md` 0,
> `EXPERIMENT_SM_PILOT` 0). The corrections in this revision carry the material those trees contain; the
> **`source-material/` tree is correctly excluded** — `source-material/README.md:3–6` calls it *"inputs,
> not design. Nothing here is normative"*, and it measures nothing.

| Document(s) | What it actually is | Why it is not a paper (as it stands) |
|---|---|---|
| [`TIER2_MODEL_SURVEY_2026-10-10.md`](/home/zer0null/Duval/docs/research/TIER2_MODEL_SURVEY_2026-10-10.md), [`TIER2_SERVING_EVIDENCE`](/home/zer0null/Duval/docs/research/TIER2_SERVING_EVIDENCE_2026-10-10.md), [`TIER2_SERVING_SPEC`](/home/zer0null/Duval/docs/research/TIER2_SERVING_SPEC_2026-10-10.md), [`TIER2_OPTIONS_REGISTER`](/home/zer0null/Duval/docs/research/TIER2_OPTIONS_REGISTER_2026-10-10.md), [`TIER2_9B_SEARCH`](/home/zer0null/Duval/docs/research/TIER2_9B_SEARCH_2026-10-10.md) | Model-selection and serving procurement, with measured GB10 evidence and errata | Vendor-card synthesis + one host's bring-up; no controlled comparison, no methodology contribution beyond reporting discipline |
| [`MODEL_ESTATE_AUDIT_2026.md`](/home/zer0null/Duval/docs/research/MODEL_ESTATE_AUDIT_2026.md), [`GX10_COMPANION_SURFACE_2026.md`](/home/zer0null/Duval/docs/research/GX10_COMPANION_SURFACE_2026.md) | Hardware/estate audit and a companion-surface thesis | Single estate, point-in-time snapshots, two errata sections (one figure is a stale snapshot); the measurable part (§6) is already candidate #5 |
| [`SEARCH_CHANNEL_2026-10-10.md`](/home/zer0null/Duval/docs/research/SEARCH_CHANNEL_2026-10-10.md) | A measured defect class in a local search router (routed zeros, silent router, inherited failing engines) | **n = 10 queries, one instance, one day**; the document says so and says it is not a rate. A good ops report; a paper needs a rate study |
| [`MEMORY_TAXONOMY_2026.md`](/home/zer0null/Duval/docs/research/MEMORY_TAXONOMY_2026.md), [`MEMORY_KNOWLEDGE_2026.md`](/home/zer0null/Duval/docs/research/MEMORY_KNOWLEDGE_2026.md) | Literature-grounded design notes on memory taxonomies and build-vs-consume | No measurement; a proposed methodology (§5 of the taxonomy) is a *design* proposal, not a validated instrument |
| [`TYPED_STATE_PROGRESSION_2026.md`](/home/zer0null/Duval/docs/research/TYPED_STATE_PROGRESSION_2026.md), [`CONTENT_ADDRESSED_STRUCTURES_2026.md`](/home/zer0null/Duval/docs/research/CONTENT_ADDRESSED_STRUCTURES_2026.md), [`EFFORT_AXIS_2026.md`](/home/zer0null/Duval/docs/research/EFFORT_AXIS_2026.md) | Design-space surveys and recommendation matrices (Merkle vs DAG; typestate; per-provider effort control) | Decision inputs with §Unknowns sections; EFFORT_AXIS is largely vendor-card verification, and its interesting part (the thinking switch) is measured in candidate #5 |
| [`LAYER_MODEL.md`](/home/zer0null/Duval/docs/research/LAYER_MODEL.md) | The five-layer specification, including the intersection errata | A spec. Its errata (§4.6.1) is a section of candidate #1, not a paper |
| [`STAGED_EXTRACTION_PROVENANCE.md`](/home/zer0null/Duval/docs/research/STAGED_EXTRACTION_PROVENANCE.md), [`GATED_READ_PROVENANCE.md`](/home/zer0null/Duval/docs/research/GATED_READ_PROVENANCE.md) | Two literature-provenance briefs with gap statements | Related-work inputs for candidate #7; no first-party result |
| [`BIOMAP/`](/home/zer0null/Duval/docs/research/BIOMAP) (9 files, 2,111 lines incl. `BIOMAP_VERDICT.md`) | A cross-disciplinary adoption study (brain → system), with a pre-seal audit that **failed** the section it checked and five citation-failure classes | The strongest content is "prior art already names this" (DAAF) and "a global gain is the wrong gate"; both are *design* conclusions. The FATAL one, `BIOMAP_VERDICT.md` §7.5, is cited inside candidate #1 as the flattening error — i.e. it is a source of method discipline |
| [`LONG_HORIZON_EVALS_2026.md`](/home/zer0null/Duval/docs/research/LONG_HORIZON_EVALS_2026.md) (1,529 lines) | A labelled-evidence survey of long-horizon evaluation: decay curves, context rot, suites, pass^k, sample-size formulae, memory failure register | Survey-shaped → candidate #13; as first-party research it measures nothing |
| [`AGENT_HARNESSES_2026.md`](/home/zer0null/Duval/docs/research/AGENT_HARNESSES_2026.md) (823 lines) | A survey of what a harness is, with the Harbor-Index crossover, the fabricated "graph engineering" case study, and the ~5 % prose-rule enforcement number | Survey/position → candidate #14 |
| [`EXTERNAL_EVIDENCE_2026-10-07.md`](/home/zer0null/Duval/docs/research/EXTERNAL_EVIDENCE_2026-10-07.md) (1,907 lines) | Claim-by-claim external verification of a "self-improving build architecture" monograph, with CONFIRMED / PARTIAL / CONTRADICTED verdicts | Verification ledger; the *method* ("what verified means") is reusable but the object of study is the authors' own monograph |
| [`SELF_REFINEMENT_DEGRADATION_2026.md`](/home/zer0null/Duval/docs/research/SELF_REFINEMENT_DEGRADATION_2026.md) (605 lines) | Literature record assembled to explain EXP#11, with a mapping table and explicit "no external match" findings | It is the related-work spine of candidate #4, not a paper |
| [`HARNESS_COMPARISON_PLAN.md`](/home/zer0null/Duval/docs/research/HARNESS_COMPARISON_PLAN.md) (747 lines) | A pre-registration-grade *plan* for harness-vs-harness comparison, with three baselines and a fatal-flaw section | **No comparison run exists.** Part C is explicitly unscorable; the plan's own §0.1 says the only defensible internal number is 14.9 % on an authored fixture. If the three baselines are ever run, this becomes a strong candidate |
| [`EXPERIMENT_PROGRAMME.md`](/home/zer0null/Duval/docs/research/EXPERIMENT_PROGRAMME.md), [`EXPERIMENT_PROGRAMME_2.md`](/home/zer0null/Duval/docs/research/EXPERIMENT_PROGRAMME_2.md) | Programme design and branch discipline | Programme documents |
| [`experiments/EXP#21-*`](/home/zer0null/Duval/docs/research/experiments) (3 files) | Branch-placement limitation, integration authority blocker, lane→main reconciliation (**57 ahead, 43 files, +11,287/−104**) | Compliance/limitation records; they are evidence *about the process*, and they are honest, but not research |
| [`experiments/PLANNED-model-cascade-study.md`](/home/zer0null/Duval/docs/research/experiments/PLANNED-model-cascade-study.md), [`EXP-M4-judge-boundary-detector.md`](/home/zer0null/Duval/docs/research/experiments/EXP-M4-judge-boundary-detector.md) | A planning-only note and the superseded-naming predecessor of EXP#19 | Explicitly not a pre-registration / superseded in naming only |
| [`selfbuild/`](/home/zer0null/Duval/docs/research/selfbuild) (23 files) | Contracts, grant, bootstrap accounting, GATE0 inventory/diagnosis/repair, kernel-module spec, pilot evaluator pre-registration | Programme records; the *measured* parts (EXP#18/#19/#20/#22) are candidate #9 |

**One further note.** The corpus's own cross-cutting documents —
[`FINDINGS_REGISTER.md`](/home/zer0null/Duval/docs/research/FINDINGS_REGISTER.md) and [`experiments/LEARNINGS.md`](/home/zer0null/Duval/docs/research/experiments/LEARNINGS.md) **M1–M14** — are the most reusable
assets in the whole tree. `LEARNINGS.md` alone (M1–M14, each with a falsifier and a route by which the defect
was caught) is a plausible **short methodology paper / position paper** on instrument validation in
agent-evaluation research: *"a positive result needs a control that could have said no."* That is a genuine
candidate I would rank between #6 and #7 if the corpus wants a third paper that needs no new experiments.
I have not promoted it into the ranked list because it is a synthesis of the other candidates' method
sections rather than a standalone study — but it is the cheapest real paper in the corpus and should be
revisited once #1–#4 have shipped.

> **UCORR1 correction 4 (2026-10-14): this note is superseded by `NC1` (rank 6½ above), and is retained as
> the record of the decision it supersedes.** UP2 promoted the slot because `docs/MISTAKES.md` is the same
> thesis with a **registry (19 classes, families A–E), a machine-enforced class↔detector-table count
> (`docs/MISTAKES.md:386–388`; `evals/prevention.ts:43` = `prevention.detector-coverage`), a
> detector-status partition (12 automated / 3 partial / 4 manual) and dated measured instances** — a
> system+method candidate rather than a synthesis. The M1–M14 cross-walk is named as NC1's missing work
> (M11 and M12 have no class; 15 of the 19 classes have no M-id).
> **Also recorded, and not promoted:** `docs/DECISION_LOG.md` is design-rationale substrate, not a paper —
> its own entries say the built thing did not exist (`D-098:4553`, `D-099:4594`) — so its value is as
> load-bearing evidence inside A1/#9 and NC1 rather than as candidate #15. UP2's **`NC2`** (*"the
> append-only design record"*) was **considered and declined** for the same reason (an experience report
> with no measurement a reviewer could falsify beyond this repository); it is folded into NC1's method
> thread, not listed.

---

## E. The single highest-leverage paper for an O-1 evidence file

**Candidate #4 — *Self-refinement without external feedback degrades decision accuracy* (the EXP#11
negative result, grounded by `SELF_REFINEMENT_DEGRADATION_2026.md`).**

**Why this one, and not the anchor.**

An O-1 evidence file is judged on whether the person's work is recognised by *the field*, which in practice
means: a peer-reviewed artifact in a venue the field reads, plus original contributions that experts can
attest to. The leverage of a paper is therefore
`P(accepted at a recognised venue) × (audience size / citation pool) × (how well it demonstrates a
contribution of major significance to a letter-writer)`.

- **Audience size.** Self-refinement and self-critique degradation is one of the most actively worked topics
  in the 2024–2026 LLM literature. A paper there has an order of magnitude more potential citers than a
  paper about an agent state kernel. The corpus's own external review cites Huang et al. (ICLR 2024),
  Stechly et al., CriticBench, Valmeekam, CriticGPT and Xiong et al. — that is the conversation this paper
  joins.
- **A claim the literature does not have.** The external review's two "no external match found" results are
  exactly the material an expert letter needs: **no prior work partitions a never-revised control stratum**
  (§6), and **no study examines option counts in the 2 → 8 range** (§7, R3). A letter-writer can say
  concretely *what is new* — not "he built a system", but "his design has a control the published literature
  lacks, and it isolates a mechanism (unbounded edit magnitude) that the literature attributes only to
  critic quality."
- **Contacts the field.** The result engages a live published claim (self-refinement helps) with a measured
  counterexample and a named mechanism (**M10**: an admitted fix with no bound on its size is a
  question-hardening machine) that is quotable in one line.
- **The related work is already done.** `SELF_REFINEMENT_DEGRADATION_2026.md` is a 605-line, sourced,
  append-only literature record with a mapping table from our observation to each external finding and an
  explicit §8 list of what could not be verified. For most candidates the related-work survey is the missing
  piece; here it is an asset, and its gaps are *named* rather than hidden — itself a signal of scholarly
  practice.
- **Honesty is an asset here, not a liability.** Negative results with a never-revised control and a
  pre-registered MDE correction (M11) are rare and are the kind of work reviewers respect. It also plays
  directly to the O-1 "original contributions" criterion, which values *impact on the field's understanding*
  rather than shipping volume.

**What finishing it requires** (the honest cost): a third model family, more revision rounds, a
**pre-registered paired MDE**, and a held-out corpus not authored by the same worker. Then the statistics
stop being caveated — `F-EXP11-14`'s p = 0.0156 currently fails Bonferroni; the pattern across two models is
the evidence. That is roughly one to two months of compute on the existing estate, using the harness that
already exists (`tools/`, `EXP#11-evidence/`) and the decision corpus already frozen.

**Runner-up, and the case against my pick.**

- **#3 (encoder vs fine-tuned 4B decider)** is the *fastest decisive* paper: p = 4.2e−09, both controls
  report the opposite, the three defects biased the instrument **asymmetrically** (they lowered the SetFit
  arm 0.3158 → 0.2947 → 0.2632 and *raised* ModernBERT-base 0.342105 → 0.347368, inflating the gap rather
  than uniformly favouring the candidate), and it corrects a belief many
  practitioners hold (that encoder heads are the cheap way to a decision tier). `[corrected by UCORR3 per UCORR3 re-verification, 2026-10-15]` If the goal is *a published
  paper as fast as possible*, this is the one to finish first, and it is a genuine contribution. It ranks
  below #4 for O-1 only because its claim is narrower and its citation pool (small-model efficiency) is
  smaller than self-refinement's.
- **#1 (the anchor)** is the *programme umbrella*: published, it makes the entire corpus citable and legible
  as one body of work, and a systems paper with an open-source substrate is strong O-1 material. It ranks
  below #4 on leverage because its audience is niche and its own §6.4 scoping ("one kernel, one project, no
  external system") invites a "not yet a systems result" rejection at a main venue.

**Recommended sequencing for the evidence file:** ship **#3** first (fastest accepted artifact), **#1**
second (the umbrella that makes the corpus coherent), then **#4** as the flagship that carries the O-1
"original contribution of major significance" argument. #4 is the one to *build the O-1 narrative around*;
#3 is the one to *get on the board fastest*.

---

## F. Corpus-level observations a reviewer or strategist should carry

1. **The measurement discipline is the corpus's real asset and its real novelty.** Pre-registration never
   edited after a run; controls demonstrated to be able to report the opposite; errata appended, never
   rewritten; a recorded run kept after a missed budget and an overrun named (TEARDOWN); an author's own
   summary corrected from archived journals and the falsification left visible (KERNEL_RUN §7). Fourteen
   method learnings (M1–M14) fall out of this. **Whoever writes the papers should lead with this** — it is
   what makes single-fixture, single-host results credible rather than merely small.
2. **Every strong candidate's weakness is external validity**, and the corpus knows it. The words to avoid
   are "on this fixture" written small. Two moves fix most of it: (a) run one external benchmark (τ-bench,
   Terminal-Bench/harbor, SWE-bench are all enumerated in `LONG_HORIZON_EVALS_2026.md` and
   `HARNESS_COMPARISON_PLAN.md` §2 with feasibility verdicts) on the decision/routing work; (b) get a second
   independent labeller or corpus for the 190-case fixture that underlies candidates #3, #4, #5 and #10.
   **Negative result recorded 2026-10-14 (UCORR1, from UP2 §6.3): no second labeller, no external benchmark
   and no independent corpus was found _anywhere outside_ `docs/research/`.** UP2 surveyed
   `docs/DECISION_LOG.md`, `docs/MISTAKES.md`, `docs/BUILD_PLAN.md`, `docs/K0_BUILD_PATH.md`,
   `docs/BACKLOG.md`, `docs/DECIDER_STACK_DECISION.md`, `docs/evidence/` (11.0 MB, 68 files),
   `source-material/` (2.3 MB, 53 files), `guidance/` (12 files) and the 38 root `docs/*.md` (2.06 MB) and
   found **no** material support for either move. **The external-validity caveat on every strong candidate
   is therefore unchanged**; NC1 adds only an *environmental* variant of it (the same commit green or red
   depending on the shell's `node`).
3. **Several candidates share one fixture** (`evals/fixtures/reflex-decisions.ts`, 190 cases). That is both
   efficient and dangerous: one fixture flaw propagates into four papers. Fixing it is the single highest
   return-on-effort action in the corpus.
4. **The `n` distribution is bimodal.** The cheap offline experiments have excellent n (9,260 rows; 2,264
   calls; 3,628 rows; 1,800 pairs/config) and the end-to-end arms have terrible n (20 arms; 4 runs/cell).
   Papers should be scoped so the headline claim lives in the high-n arm.
5. **The self-build lane (#9) is the highest-variance bet in the corpus.** If the judge/product separation
   and the positive control are solved, it is a genuinely novel, safety-relevant paper about a measurable
   failure of a self-governing loop — potentially the most "extraordinary" work here. It is also the most
   likely to stay unfinished, because it is blocked on two design problems (freeze boundary; a pinned
   genuine evidence source) that EXP#20 and EXP#22 have *diagnosed but not solved*.
6. **Nothing in the corpus is claimed to be published, and no draft is marked submission-ready.** The
   closest artefact is `PAPER_DERIVATION.md`; everything else needs assembly. There is no fabricated
   submission state to correct.
7. **The corpus's own prior-art ledger narrows every novelty claim, and this inventory now carries the
   narrowing (UCORR1 correction 7, 2026-10-14).** `docs/consolidation/SOURCE_VERIFICATION.md` is the
   novelty-narrowing instrument (`docs/research/PAPER_DERIVATION.md:35–37`) and the only externally verified
   gap statements in the corpus — 24 claims (V1–V24), each fetched and quoted, *"Nothing is cited from
   memory."* Its verdict is **`mixed`: supported for the construction, undercut for the observation.**
   Specifically: **V13/V14 publish the resume-contract failure** (arXiv:2608.03836 — *"saturation 1.0 in 36
   of 40 cells, and the failure crosses hosts"*; arXiv:2608.29381 — three end-to-end attacks) and
   `:101` calls them *"the strongest single result in this ledger"*; **V16/V24** state what the engines do
   *not* record and that model-agnostic agent identity is already productised and unmeasured; **V19** finds
   the unknown-effect state absent from agent runtimes but standard in transaction managers (V18); **V20/V21**
   price long-context degradation and prefix-cache mutation. A reader of this inventory alone must therefore
   not conclude that the resume-failure **observation** is unclaimed — it is claimed, by two August-2026
   preprints — while the **construction** remains unoccupied.

---

## G. Re-triage against the author's publication rule — unit UCAND1, 2026-10-15

> **Nothing above is changed.** §A–§F (rankings, evidence, gaps, the §D register, the §E sequencing, the §F
> observations) are the verified inventory and remain in force. This section is a **second, orthogonal
> judgement laid on top of it**: *what may be published at all.* It changes **which candidates ship**,
> never what was measured.

**The rule this section applies** (author, 2026-10-15, verbatim):

> *"dont publish any blanket papers, only small extracted projects that go public and the papers associated
> with it."*

Together with, same session: **no patents; the core Consonance engine is a trade secret; the main repository
stays proprietary; only selected extracted pieces are released (under PolyForm Noncommercial); every
released piece carries its own paper.** The register of what is deliberately not published is
[`WITHHELD.md`](WITHHELD.md).

**The test, applied to every candidate.** *Could this project be released **on its own**, without the rest of
Consonance, and still make sense — with its own fixture/harness/tooling that a reader could run?*
**Yes → extracted project** — publishable, and it **must have a releasable artifact** (recorded below, or
recorded as not existing yet). **No, it only makes sense as part of the whole → blanket** — withhold.
**Surveys and position pieces (#13, #14) are not extracted projects** and are decided separately in §G.3.

**What "releasable artifact" means here, exactly.** The norm is already implemented for candidate #3:
*"every paper ships a **minimal reproducibility subset** — fixture schema, the fixture, the evaluation
harness and the exact commands, and the pre-registered protocols. **Withheld: the agent-state kernel /
runtime implementation, and any model weights**"* (`repro/encoder-crossover-190/README.md`). The subset is
the artifact; the kernel and the weights never travel. A candidate whose harness **is** the kernel (M7, M13
in [`WITHHELD.md`](WITHHELD.md) §2) must ship a **re-implemented neutral** harness or it does not pass limb
(b) of the test.

### G.1 The table

| Candidate | Extracted-project test | Releasable artifact | Verdict | Reasoning |
|---|---|---|---|---|
| **#1** Deriving agent state from an observation stream (`PAPER_DERIVATION.md`) | **fail** | **none — and none can exist**: its artifact inventory is the private `tools/**` tree (M13) and the kernel (W5), not a releasable fixture | **withhold** | **Blanket paper.** It describes the kernel as a whole and fails the standalone test; its artifact inventory is W1/M13. **[corrected by UWITH1 per UVER6 O1, 2026-10-15 — the clause *"by its own §6.4 admission"* is dropped: `PAPER_DERIVATION.md:669–672` is quoted verbatim but §6.4 is a *scope-limitation* section, not a releasability admission, and the ellipsis drops *"Every artefact lives in `tools/`, which is the operator's rule…"*. The withhold still follows — limb (a) fails because the paper's contribution 2 **is** the loop (`:72–76`, *"The loop itself: observation stream → derived state → projection"*), and limb (b) fails via the private M13 `tools/**` inventory — so the verdict is unchanged; only the reason was overstated.]** |
| **#2** Replay reproduces the record, not the decision | **pass** | recorded-output corpus (`decision-variants.jsonl`, `decision-tree-spec.json`) + a **re-implemented neutral divergence scorer** (the existing `tools/replay/exp7.ts` is M13) + the decision-case schema — **does not exist yet** | **publish** | Pure measurement on already-recorded outputs (F3, `TRADE_SECRET_AUDIT.md` §4.2). Reproducing it needs the corpus and a counter; it does **not** need the kernel's replay implementation. Condition: the fixture-rationale scrub below. |
| **#3** A fine-tuned encoder head does not beat a fine-tuned 4B decider | **pass** | **exists** — `repro/encoder-crossover-190/` (+ `papers/encoder-crossover-190/`, CC BY 4.0) | **publish** | The only candidate with a manuscript and a subset on disk; its text is a measurement (UTS1 §4.3 *CONFIRMED*). The fixture rationales / `DecisionKind` schema carve-out is the one open cut (see §G.3). |
| **#4** Self-refinement without external feedback degrades decision accuracy | **pass** | EXP#11 evidence tree (`decider-rows.jsonl` 4,090 / `imajev-rows.jsonl` 3,690, summaries) + the revision harness + the pre-registration — **not yet packaged** | **publish** | Negative result with a never-revised control stratum (F7). The *bounded-substitution repair* is the mechanism and stays out; the measured degradation and the control travel. |
| **#5** Small decision models, the escalation ladder, the unroutable ceiling | **pass** | row files (`l1-head-to-head.jsonl` 380, `ornith-tier-rows.jsonl` 230, `routing-rows.jsonl`) + the scoring/route harness — **not yet packaged** | **publish** | A model-estate measurement (oracle 0.900 unreachable; composed escalation never beats the top tier). No kernel construction is needed to state it. The `DecisionKind` taxonomy (M11) is the exposure to keep out. |
| **#6** Graded progressive disclosure is cache-safe and cheaper at equal sufficiency | **needs-author-decision** | the **emitter**: EXP#14's harness assembles prefixes through the context engine (`compiler.ts`, M7), and no neutral emitter exists on disk | **needs-author-decision** | Passes limb (a) — the byte-invariant and the cost comparison make sense alone — but **fails limb (b)**: a reader cannot run it without the withheld context engine. Deciding question in §G.3. |
| **NC1** Detectors that cannot fail (rank 6½) | **pass** | `docs/MISTAKES.md` registry (19 classes) + `evals/prevention.ts` coverage eval + the inner/outer mutation harnesses — **not yet packaged** | **publish** | A genuinely separable verification-method project: the classes are generic failure shapes and the coverage eval enforces a class↔detector invariant. Instance citations that name kernel internals fall under the M12 scrub rule. |
| **#7** Batching binary gates is free; routed extraction cuts context 15.3× and exposure to 0/20 | **pass** for the batching note; **fail** for the full scope as written | the batching bench + `gated-read-rows.jsonl` (9,260 rows); the **staged extractor** — whose routing/gating *is* the gate/absence machinery (M10) — is the part that must not ship | **needs-author-decision** | **Split it.** The batching result (n=1800/config) is a standalone positive and survives; the R5 staged-routing arm's harness discloses M10 and its accuracy/exposure numbers are anyway underpowered (n=20). §G.2. <br>**[UFIXGR7, 2026-10-15] Scope annotation — not a re-title.** The drafted paper scopes to the batching note and asserts neither the 15.3× nor the 0/20 figure (they describe the wider run, §B7): see `papers/gated-read-batching/MANUSCRIPT.md:195` and `papers/gated-read-batching/GAPS.md` G-13/G-14. |
| **#8** Full history fails on volume, projection fails on chain length | **needs-author-decision** | SM-pilot rows (`sm-rows.jsonl` 1,566, `sm-rows-horizon.jsonl`) + `SM_PROJECTION_SHAPE.md` — the **projection shape is the withheld projection mechanism (M1/M2)** | **needs-author-decision** | The dissociation is a context-strategy result, but its projection arm is the kernel's derived-state projection; whether a generic projection can carry the claim is the author's call. It is also `needs new experiments` (n=4/cell) on its own terms. §G.3. |
| **#9** A self-build loop can move its own wall | **pass** | run ledger + journal entries + the judge-boundary detector tooling (`tools/judge-boundary/`) — **not yet packaged** | **publish** | The subject is the author's **build loop**, not the Consonance runtime core; no M1–M13 mechanism is needed to state the wall-moving result. Its own blockers (positive control, judge/product separation) are unchanged and are not the rule's concern. |
| **#10** A read is not a gate | **pass** | **does not exist yet** — the exactly-once demonstration must be **re-authored on a neutral store**, because `tools/resume/engine.ts` / `tools/resume/exp3b.ts` are in the M13 withhold block | **publish** | A general concurrency finding (F1): it names a **requirement** (the gate must be a write only one racer can win), not the construction; compare-and-swap/fencing tokens are public prior art. Thin on n as a standalone paper, which is a venue question, not a blanket question. |
| **#11** ASR = 0 everywhere: when the attack base rate never materialises | **pass** | 3-model pilot rows/scorer (`tools/three-model/`, 3,628 rows) + the gate/mitigation design — **not yet packaged** | **publish** | The result is a **null plus a validity method** (injection delivered 30/30, pass^k 20/20, contamination caught). The gate conditions are the architecture-adjacent part and are the review exposure; the null does not depend on them. |
| **#12** Teardown budgets are theoretical at measured scale | **pass** | teardown rows (`teardown-live-rows*.jsonl`, `teardown-rows.jsonl`) + the disposal harness (`tools/teardown/`) — **not yet packaged** | **publish** | The disposal contract is **not** in the M1–M13 withhold block; the contribution is a contract change plus a bounded worst case, and the null ("the timeout never fired") is supporting evidence. |
| **#13** Long-horizon agent evaluation (survey) | **n/a — not an extracted project** | none required (a survey ships no harness) | **needs-author-decision** | It **survives the blanket rule** — it is about the field, not about Consonance, and discloses no mechanism — but it sits **outside** the release-with-artifact programme, and TMLR no longer considers surveys (§11.13). Whether to write it at all is the author's. §G.3. |
| **#14** Agent harnesses: what the field measures and what it only asserts (survey + position) | **n/a — and its position half fails** | none required | **needs-author-decision** | The **survey half** survives **only if §8 and its §4.4 Consonance inference are excised** — as the document exists on disk it is *not* "no Consonance content": `docs/research/AGENT_HARNESSES_2026.md` carries **33 `Consonance` mentions** and a dedicated **§8 "Implications for Consonance"** (`:679`), naming `StateClass`, `SandboxSpec`, `Budget` and the gate chain. `[corrected by UWITH1 per UVER6 C5, 2026-10-15; verified by `grep -c "Consonance"` = 33]` The **position half** argues the harness/architectural thesis — i.e. it restates **W3**, which is **already public** (§8.1 of [`WITHHELD.md`](WITHHELD.md)); the real defect there is **duplication, not disclosure** (UVER6 O3). §G.3. |

**Counts: 15 candidates re-triaged — 9 `publish`, 1 `withhold`, 5 `needs-author-decision`.**

### G.2 The finding / mechanism split, for the four candidates where it is contested

The mitigation that keeps contribution citable is stated once and applies to all four rows: **a paper may
report what was measured and what a fix must satisfy without publishing how it is built.** The general form
is *report the result and the constraint; never the construction*
([`TRADE_SECRET_AUDIT.md`](TRADE_SECRET_AUDIT.md) §3). Where a finding cannot be stated without the
construction, it is not a finding — it is the mechanism wearing a result's clothes, and it is withheld.

- **#2 — replay divergence (this was the card's sharpest case, and it resolves cleanly).** The **finding**
  is publishable: *re-binding a recorded request to a different model diverges in 41.8 % of cases, 32.2 %
  under relabelling, against a 244/244 zero replication control and a 31.6 % stable set.* It is a property of
  **recorded outputs across bindings** — F3, triaged "pure measurement on already-recorded outputs" — and it
  says nothing about how the kernel performs replay. The **mechanism** that stays out is the kernel's replay
  *behaviour*: how a request is bound to a binding, how the record is addressed and re-consumed (M1/M3/M13).
  The paper measures divergence; it does not explain or publish the replay machinery. Artifact condition: a
  **re-implemented neutral scorer**, not `tools/replay/exp7.ts`.
- **#5 — the escalation ladder.** The **finding** is publishable: *the union of the models is complementary
  (per-case oracle 0.900) and neither a cheap confidence signal nor a competent resident model captures any
  of it; composed escalation never beats the top tier alone.* That is measurement of the model estate. The
  **mechanism** that stays out is the **decision taxonomy and the routing/escalation surface of the kernel**
  (M11: the `DecisionKind` union and the six namespaces) — a paper that ships the kernel's decision taxonomy
  publishes the decision surface. State the ladder as *a model-selection and routing measurement*, not as
  *the kernel's escalation tier*.
- **#6 — cache-safe graded disclosure.** The **finding** is publishable in form: *changing only the depth of
  a reference resolution leaves the provider prefix byte-identical, and a graded three-rung knob is 27.8 %
  cheaper than a binary one at equal sufficiency.* The **mechanism** that does not survive is the thing that
  **emits** those prefixes: the context engine's assembly, paging surfaces and budget rules (M7). This is
  the one candidate where the *finding is separable but the artifact is not* — hence
  `needs-author-decision`, not `publish`.
- **#7 — batching vs routed extraction.** The **finding** splits in two. (i) *Batching 16–90 binary
  decisions at `effort=none` is free: calls cut 15–90×, prompt tokens 2.341× at bs16 / 2.418× at bs90
  (the card's earlier bare "2.4×" is the bs90 ratio), F1 within ±0.01 at
  n=1800/config* — publishable **now** as a short note; it is a measurement about an inference pattern and
  needs no kernel machinery. (ii) *Routed extraction reaches the best arm's accuracy (recorded `stage_route`
  mean 0.55, below the 0.65 best-arm bar — see the dated §B7 note) at the measured 15.279× the context
  (the card's earlier "1/14" is superseded) with
  payload exposure 0/20* — this one's harness **is** the staged extractor, i.e. the gate/absence machinery
  (M10), and its numbers are underpowered (n=20 cannot separate the top four arms). So the mechanism split
  and the experiment split point the same way: **scope the paper to (i)**, or accept that (ii) needs both a
  neutral re-implementation and round 2.

### G.3 Borderline cases — the deciding question and which way the evidence points

Five candidates are marked `needs-author-decision`, and **no verdict is forced** where the answer turns on
the author's judgement. For each, the deciding question is named; the evidence is reported, not resolved.

1. **#6 graded disclosure — "does the cache-safety claim survive without the emitter?"** The evidence points
   **against** shipping as-is and **for** the finding: the invariance is a property of emitted bytes and was
   anchored to recorded hashes, but the only emitter on disk is the context engine (M7), so limb (b) of the
   test fails today. The author's options are (i) re-implement a neutral emitter for the release (cost: an
   unbudgeted build) or (ii) publish the finding with the emitter withheld and accept that a reader cannot
   re-run it.
2. **#7 — "is the batching note the paper, or is #7 the paper?"** The evidence points to **the batching
   note**: it is the high-n arm (n=1800/config), the doc calls it "the cleanest positive", and §B7 already
   names it the fallback scope. The full-scope route requires round-2 experiments *and* a neutral
   re-implementation of the extractor.
3. **#8 — "can the projection arm be a generic summariser?"** The evidence points **no**: the measured
   projection is the kernel's derived state and its shape is a document in the corpus
   (`SM_PROJECTION_SHAPE.md`, M1/M2). A generic re-implementation would not be the arm that was measured, so
   the choice is between withholding the arm (and the dissociation claim with it) and disclosing the
   projection mechanism.
4. **#13 — "does a field survey survive the new rule?"** It **does** survive the blanket rule: it is about
   the field, needs no Consonance substance, discloses no mechanism, and ships no artifact — so it is exempt
   from the extracted-project-with-artifact requirement rather than condemned by it. The blocking facts are
   different and outside the rule: as first-party research in this corpus it measures nothing (§D), and TMLR
   no longer considers surveys (§11.13). Whether to write it is a programme choice, not a withholding choice.
5. **#14 — "can the position half be said without the withheld claim?"** The evidence points **no**: the
   position half argues what agent harnesses should expose, which is the architectural thesis in W3. The
   survey half — what the field measures and what it only asserts — survives on its own. The author's choice
   is whether a survey-only paper is worth writing.

**One further open cut, already recorded by UTS1 and not re-decided here:** the **`DecisionKind` union and
the fixture rationales** in candidate #3's own release set (M11). The `DecisionCase` schema is required by
the paper's artifact, while the 2,220 lines of fixture **rationales** are *"used in review, not fed to the
model"* and are therefore not needed for third-party reproduction — but 335 of those lines match
kernel-internals vocabulary. The deciding question and both options are stated in
[`TRADE_SECRET_AUDIT.md`](TRADE_SECRET_AUDIT.md) §4.3/§5.2 and registered as open in
[`WITHHELD.md`](WITHHELD.md) §6. It does not change #3's verdict (`publish`); it changes what its artifact
contains.

### G.4 What replaces the umbrella — the citable-contribution mitigation

The old plan's argument was that #1 would make the corpus citable **as one body**. Under the rule there is no
umbrella, so the mitigation is per-paper, and it is the same sentence that makes the withheld mechanisms
survivable as contributions:

> **A paper may report what was measured and what a fix must satisfy without publishing how it is built.**

Three consequences to carry into every one of the nine `publish` rows:

1. **The artifact is per paper.** Each released paper ships its own minimal reproducibility subset
   (`fixture schema + fixture + harness + exact commands + pre-registered protocols`), and the kernel /
   runtime and all weights stay out. The subset is the *evidence* the finding is reproducible; it is not a
   window into the engine.
2. **The unit of citation is the paper, not the programme.** Citations accrue per paper, per artifact, per
   DOI. No document exists whose job is to make the corpus legible as one body — so no claim may be written
   that depends on one.
3. **The findings that carry the contribution are empirical.** F3 (#2), the encoder-crossover result (#3),
   F7 (#4), the escalation measurement (#5), the batching note (#7), the exactly-once requirement (#10) and
   the ASR-null validity work (#11) are all statements of *what was measured* — and they are exactly the
   material the O-1 **(B)(5)** argument needs, once cited independently.

> **[APPENDED 2026-10-15 by UWITH1 per UVER6 C2/O3 — the O-1 inversion, and the prior-disclosure fact.]**
> §G.4 above (and §G.2's mitigation framing) priced a cost that does not exist: *the architectural claim is
> never published and cannot be claimed as a published contribution.* **It is published** —
> `github.com/Aswin-Ram-K/publish-present-compete/findings/PAPER-DERIVATION.md`, **MIT**, public
> ≤ 2026-10-10, **byte-identical** (46,636 B; sha256 `d98c4359d37b987db07707e0b96358de0cd280c979896c6a15858d96bcd14802`)
> to `/home/zer0null/Duval/docs/research/PAPER_DERIVATION.md`; the public profile README states the thesis.
> So the unit of citation is still the paper, but the **(B)(5)** question can now be argued *with a
> prior-disclosure date of ≤ 2026-10-10 attached*, and the residual value being protected is the
> **implementation**, not the mechanism. Two knock-ons for this section: (i) **#14's position half does not
> *disclose* W3** — W3 is already public; its defect is duplication, not disclosure (O3); (ii) wherever §G.1
> says a candidate's artifact is *"the withheld core (M1–M13)"*, read **the implementation** — W5/W6, the M13
> `tools/**` tree, and `src/**` paths under the M12 scrub rule — because the mechanism descriptions
> themselves are public ([`WITHHELD.md`](WITHHELD.md) §8.1). **The split is unaffected:** UVER6 re-derived
> 9 `publish` / 1 `withhold` / 5 `needs-author-decision` and it stands.

### G.5 Cross-references

- **What is deliberately not published, itemised:** [`WITHHELD.md`](WITHHELD.md) §1–§2 (W1–W7, M1–M13) — **re-issued at its §8, which records that M1–M10, M12 and M13 are ALREADY PUBLIC (§8.1), M11 undetermined (§8.2), and narrows the protective claim to the implementation (§8.3).**
- **The corrected plan and the O-1 cost:** [`PUBLICATION_STRATEGY.md`](PUBLICATION_STRATEGY.md) §13.
- **The per-mechanism triage and the finding list F1–F8:** [`TRADE_SECRET_AUDIT.md`](TRADE_SECRET_AUDIT.md)
  §4.1–§4.3.
- **The venues, the $0 route, endorsement and the licence split:** [`PUBLICATION_STRATEGY.md`](PUBLICATION_STRATEGY.md)
  §2–§3, §8–§9 (unaffected — see §13(f)); [`CODE_LICENSING_STRATEGY.md`](CODE_LICENSING_STRATEGY.md) §5.

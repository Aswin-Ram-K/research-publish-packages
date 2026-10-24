# GAPS.md — UPAPER1a · what A3 still owes, and the status of each gap

The four gaps named in `strategy/PAPER_CANDIDATES.md` §A3 (lines 272–280), each with its current status,
plus gaps this unit discovered while verifying. **No gap here is a reason to invent a number.**

---

## Gap 1 — the fixture is one 190-case set authored by one worker

**Status: OPEN. Partially mitigated, and the mitigation must be stated with its limitation.**

| fact | value | source |
|---|---|---|
| cases | 190, 721 options, 74 distinct labels (51 occurring once) | `experiments/second-labeller-190/RUN.json` |
| second pass agreement | 0.9053 | `second-labeller-190/metrics.json .routeB_primary.agreement` |
| second pass κ | 0.9014 (≈0.90) | `metrics.json .routeB_primary.kappa` |
| second pass labeller | **`routeB-blind-model`** — a model, fresh context, blind to the fixture | `metrics.json`, `EVIDENCE.md:150` |
| disagreements | 18 / 190 | `metrics.json .disagreements_count_routeB` |
| deterministic lexical route κ | 0.3249 | `metrics.json .routeA.kappa` |
| instrument sha256 unchanged (as-audited `reflex-decisions.ts` source, `repro/encoder-crossover-190/fixture/reflex-decisions.ts`; 145,031 bytes; not the shipped fixture) | `076164ac…b4796` before and after | `RUN.json` |

**The limitation, which the writer must carry verbatim in spirit** (`second-labeller-190/EVIDENCE.md:14–23`):
the second pass is a **model, not an independent human annotator**; agreement between a model and the
fixture's hand-authored labels is **NOT inter-annotator agreement**, and **κ = 0.9014 must not be reported as
IAA**. A second distinct-model pass (`mimo-v2.6-flash`) was launched and **returned no file**, so exactly
**one** model pass exists (`EVIDENCE.md:153–155`). **An independent human labeller is still owed.**

Two further honest caveats from the same source:
- the **pooled** κ is weak on its own — 51 of 74 labels occur once, so `pe` is tiny (0.040) and κ is
  dominated by `po` (`EVIDENCE.md:318–319`); the stratified figures are the informative ones
  (closed-vocabulary 106 cases κ = 0.8837; roster-and-bespoke 84 cases κ = 0.9140).
- a fixed κ threshold was pre-registered (≥0.90 agreement / ≥0.85 κ) and *met* at 0.905/0.901, but a met
  threshold on a model pass does not convert it into human agreement.

**What would close it:** a second **fixture**, ideally an external benchmark of typed single-label
decisions (the ask in §A3 item 1), *or* a second **human** labeller on these 190.

---

## Gap 2 — latency is not like-for-like

**Status: OPEN, and this unit's finding is that the evidence tree is NOT capable of supporting a fair
latency claim. The writer must either re-measure or DROP the latency claim.**

What the tree contains:

| arm | per-decision latency | where measured | method |
|---|---|---|---|
| `modernbert-base` | 12.37 ms | local, `GX10 gx10-163b`, NVIDIA GB10 | one batched forward call over all option texts; warm 20; 3×190 = n 570; GPU synchronised |
| `deberta-v3-base` | 14.16 ms | same | same |
| `setfit-mpnet` | 11.96 ms | same | same |
| `shuffled-label` | 12.46 ms | same | same |
| `majority-class` | 0.003 ms | same | same |
| `decider-4b` | **53.06 ms** (instrument190) | **stored EXP#11 rows, a served stack** | not this run; not this host |
| `decider-4b` on H-A / H-B | **106.92 / 72.85 ms** | stored EXP#11 rows | same model, **2× spread across strata** |
| `imajev-4b` / `laya` | 453.03 / 639.15 ms | stored EXP#11 rows | served |

Reasons the comparison is not supportable:

1. **Different hardware and stack, never co-measured.** `REPORT.md:191` verbatim: *"The heads were timed on
   the GX10's GB10 with local weights; the decider's 0.075 s/decision figure and the re-scored 0.0531
   s/decision on these rows come from a served model on a different stack."*
2. **Different measurement granularity.** The head figure is *one full per-decision call* (all option texts
   tokenised, **one forward batch**, softmax). The decider figure is a served autoregressive decision. A
   single forward batch and a decode loop are not the same operation, so even on identical hardware the
   numbers would not be a like-for-like unit of work.
3. **The F6 threshold is a constant, not a measurement.** F6 compares every head against the
   **pre-registered 0.075 s/decision** taken from `DECIDER_TIER §2`. F6 not firing (`fires=false`) therefore
   only says *12–14 ms < 75 ms*; it is **not** evidence from a controlled head-to-head.
4. **The decider's own timing is unstable by 2×** across strata of the same model (53.06 vs 72.85 vs
   106.92 ms), which by itself shows the timing was not controlled.

**Verdict: `latency_claim_supportable = no`.** The strongest defensible statement is the narrow, uninteresting
one already in `REPORT.md` — per-decision, the heads sit in the tens of milliseconds and the decider
figures in the tree sit in the tens-to-hundreds of milliseconds, measured on different stacks — which is
**not** a result. Either re-measure a 4B decider on the same GB10 under the same per-decision protocol, or
drop latency from the paper entirely and keep the accuracy + calibration claim.

---

## Gap 3 — only three encoder families

**Status: OPEN (acknowledged in §A3 item 3). The three families are ModernBERT-base (149M),
DeBERTa-v3-base (184M), SetFit-MPNet (109M); all three lose to the majority-class control.**

- A reviewer's obvious fourth arm: **a trained linear probe on top of a frozen LLM embedding** (§A3's own
  suggestion). This unit found no such arm in the evidence tree — searching the five `eval-*.json` and
  `analysis.json` yields exactly five arms (three candidates, two controls) and no embedding-probe arm.
- Two related weaknesses worth flagging to the writer:
  - **`deberta-v3-base` did not train** at the pre-registered operating point: train loss 1.1288 → 1.1235
    over 2 logged points, dev accuracy 0.50 → 0.495 with a majority-class dev baseline of 0.475
    (`analysis.json .observations.debertaV3Training`). Its 0.3474 should be read as *"did not train"*, not
    *"trained and failed to transfer"*.
  - **Training is not bit-reproducible**: three identical training runs gave ModernBERT epoch-1 dev
    accuracies of 0.5150 and 0.5900 and fixture accuracies of 0.3421 and 0.3474 (`REPORT.md`, §"A caveat
    that is not a defect"). A ±1–2 point band is honest for every head number.
- The parameter-count comparison is *monotone* (0.2632 < 0.3474 = 0.3474 at 109M < 149M < 184M), so **H4 is
  not supported** — there is no size-crossover story *within* these heads.

---

## Gap 4 — the two candidate primary baselines (a human must declare one; **this unit does NOT**)

### Case for **same-run 0.6789** (`decider-4b EXP#11 reproduction, F0 frame`)

- It is the **only** 4B figure with **per-case rows in the tree** (`docs/research/EXP#11-evidence/decider-rows.jsonl`),
  so it can be **re-scored and audited**: re-scored 0.6789 vs published 0.6789, `reproducesAt3dp=true`,
  `absoluteDifference=4.7e−05` (`analysis.json .baselinesRescored`).
- It is on **exactly the same 190 cases, same option orders** as the heads — the `analysis.json`
  `pairedPartner` string is *"decider-4b EXP#11 reproduction (F0_decider frame), same 190 cases, same option
  orders"*. The paired McNemar (b=27, c=90, Δ=−0.3316, p=4.167e−09) is computed against **this** arm.
- It is the **stricter** bar (0.6789 > 0.6684), so beating it is a stronger claim.
- **Cost:** it is a *reproduction* by a new compiler, not the historical published number; a hostile reviewer
  can say the baseline was re-tuned for the comparison.

### Case for **historical 0.6684** (`decider-4b (published, D-067), instrument190`)

- It is the **published** number, and it is the number the **pre-registered falsifier F1 was written
  against** (`EXP#12-typed-channel-comparison.md:95`: *"encoder accuracy < 0.6684 (the best 4B)"*;
  `REPORT.md:85`). Declaring the baseline post-hoc after F1 fired on a different figure is a pre-registration
  integrity issue.
- It is the figure that gives the paper its headline **0.32** (`0.6684 − 0.3474 = 0.3210`) and matches the
  working title.
- **Cost, and it is severe:** `REPORT.md:189` verbatim — *"**`decider-4b 0.6684` (D-067) cannot be
  re-scored.** No per-case rows for that specific measurement are in the tree, so F5 cannot check it
  directly"*. `REPORT.md:104`: `reproduces at 3 d.p. = **None**`. Choosing 0.6684 means the headline baseline
  is **the one number in the paper nobody can re-derive**, while a fully auditable number (0.6789) sits
  beside it.
- **Note that this does not change the conclusion either way:** 0.3474 loses to both, and −0.3316 exceeds
  2× either MDE (0.1595 paired / 0.1355 unpaired).

**A third, hybrid option a human could declare:** primary = 0.6789 (auditable, same-run, paired), with
0.6684 reported as the pre-registered/published reference the falsifier fired on. **This unit does not
choose.**

---

## Gaps discovered by this unit (not in §A3)

1. **The central literature claim is UNSOURCED inside the EXP#12 corpus.** §A3's thesis — *"every published
   'a small encoder wins' result compares the encoder against a prompted LLM, never against a fine-tuned
   generative decider"* — appears in `EXP#12-typed-channel-comparison.md:8–9`, `:171` and `LEARNINGS.md:262`
   as **"The literature says…"** with **no citation list in that experiment or its evidence tree**. The
   sourcing lives elsewhere in the target: `docs/DECIDER_STACK_DECISION.md §11.6` names **GLiNER**
   (span-extraction F1, not a typed single-label decision) and **GLiClass** (no measured head-to-head), and
   traces to commit `ad301ae` (*"Nobody has published the comparison we need"*) and `a5ef1b2`/`995fbd1`.
   The claim is asserted as **verified-absent by a second lane**, not proven by a cited survey. The writer
   must either cite that lane or soften "every published result" to what was actually searched. See `REFS.md`.
2. **"Every correction moved the affected arm DOWN" is false as a universal** — true for SetFit-MPNet only;
   `modernbert-base` moved **UP** (0.342105 → 0.347368) when the order-probe bug was fixed. Recorded as a
   `DISAGREES` row in `CLAIMS.md`.
3. **"The paired MDE is the conservative one" is false on this run.** ψ = 0.616, and
   `unpaired/paired = 0.85×`, so the **paired** MDE (0.1595) is the **larger** figure — the opposite of the
   pre-registration's "~3× overstatement" guidance (`REPORT.md:69`, `LEARNINGS.md` M11 errata). The
   *requirement* to quote the paired figure stands; the *justification* does not.
4. **The headline F3/calibration claim is convention-dependent.** F3 fires on `probabilities[choice]`
   (head 0.0994 ≥ decider 0.0551) and would **not** fire on the stored `confidence` field (0.0994 < 0.1547) —
   opposite verdicts from the same rows (`REPORT.md` §D3, `LEARNINGS.md` M12 guard 3). If the paper uses
   calibration at all, the convention must be stated.
5. **`imajev-4b 0.645` is not a fixture number** — it is the H-A **corpus** stratum; the fixture figure is
   **0.6368** (`REPORT.md` §"Two things that were checked and are NOT defects"). Do not place 0.645 in a
   fixture table. `imajev-4b`/`laya` are also far slower (453 / 639 ms) — but see Gap 2 before using that.
6. **Power/pre-registration bookkeeping:** the p-value discussion in `LEARNINGS.md` (M11 errata region)
   notes a **Bonferroni threshold of 0.0125** for four cumulative comparisons and that some 0.0156 result
   did not survive; the EXP#12 p-value (4.167e−09) is far below it, so this does **not** threaten the A3
   result — but the writer should not quote a marginal p-value from the same corpus as if it were robust.

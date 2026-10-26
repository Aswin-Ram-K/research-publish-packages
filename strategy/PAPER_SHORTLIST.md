# PAPER_SHORTLIST — re-triage of the candidate inventory against disk state

**Unit:** UPICK1 (report-only). **Date of survey:** this session.
**Bound:** 25 tool calls (used: 23 including this write). **Writes:** this file, `orchestration/units/UPICK1.md`,
`orchestration/handoffs/UPICK1.json`, `scratch/upick1/**` only. No file under `papers/**`, `submission/**` or
`orchestration/units/UBUILD1.build.sh` was touched. Zero commands were run against `/home/zer0null/Duval`.
**Scope:** "what else is publishable" — not an assessment of `papers/encoder-crossover-190/`'s quality.

## 0. What this report is, and its honesty rules

Every "exists" line below was produced by a command I actually ran; every content claim not opened is marked
`UNVERIFIED`. Three claims in the unit card did **not** reproduce and are recorded here rather than repeated:

| Card claim | Measured | Status |
|---|---|---|
| "builds a **29-file** public package" | every built package manifest I found records **28** files (`scratch/{ugate2,ugate3,uem…,uver30,uwire3}/dest/research-publish-packages/packages/exp12-encoder-crossover/MANIFEST.json`) | **NOT REPRODUCED** (28, not 29) |
| "`EXCLUDED.md` naming **15 exclusion classes**" | `repro/encoder-crossover-190-SANITISED/EXCLUDED.md` = 69 lines, 6011 B, **5 top-level sections** (1 Withheld by policy, 2 Excluded by the unit's explicit instruction, 3 Excluded for minimality, 4 Secrets — none encountered, 5 Target dirtiness is not ours) | **15 UNVERIFIED** (sub-item count not taken) |
| "sealed fixture … per-case `pChosen`" | `fixture-190.json` case keys are `id, kind, question, options, correct, rationale, namespaces` — **no `pChosen`**; `pChosen` is present in the **result records** (`eval-*.json` / `baselines.json` → `perCase`) | **CORRECTED** (records, not fixture) |

Also `UNVERIFIED`: the McNemar `p = 4.166817e-09` and MDE `0.15949356562876219` were **not re-derived** here;
they come from the inventory, not from a computation I ran. The full-precision kappa `0.9013584840356494` matched
only to 6 dp (`EVIDENCE.md`: `kappa 0.901358   exact 172/190`); `metrics2.json` carries stratified kappas
0.5625–0.8577.

## 1. The existing inventory — every candidate it names

Sources read in full: `strategy/PAPER_CANDIDATES.md` (1160 lines; errata UCORR1 2026-10-14, UCORR2, UCORR3),
`strategy/PAPER_CANDIDATES_SUPPLEMENT.md` (UP2, 2026-10-14), `strategy/PUBLICATION_STRATEGY.md` (§13 errata).
The inventory ranks **14 numbered candidates plus NC1 at 6½**, bucketed **publishable now (#1–#6, NC1, #13, #14) /
nearly ready (#7) / needs new experiments (#8–#12)**; §G (UCAND1, 2026-10-15) re-triages to
**9 publish / 1 withhold / 5 needs-author-decision**. Nothing is dropped and nothing invented below.

| # | Candidate | Stated claim | Stated readiness |
|---|---|---|---|
| A1 (#1) | Deriving agent state from an observation stream | agent state is derivable from the observation stream (system+method) | publishable now, 1–2 wk |
| A2 (#2) | Replay reproduces the record, not the decision | replay divergence 41.8% (rebinding), 32.2% (relabel), 244/244 zero control, 31.6% stable set; 4 models × 190 cases × 4 variants = 3,040 outputs; `l1-head-to-head.jsonl` 380 rows, 51.6% | publishable now; workshop short paper |
| A3 (#3) | A fine-tuned encoder head does not beat a fine-tuned 4B decider | modernbert 0.3474 / deberta 0.3474 / setfit 0.2632 / majority 0.4526 / shuffled 0.2316 / decider-4b 0.6684 (0.6789 same-run); McNemar b=27 c=90 Δ=−0.3316 | publishable now (negatives) |
| A4 (#4) | Self-refinement degrades the decider | EXP#11 decider 0.6650→0.6300, imajev 0.6450→0.5800; never-revised stratum 0.6700 over 12 measurements; paired p=0.0156 fails Bonferroni 0.0125 | publishable now; §E flagship (O-1) |
| B5 (#5) | Small decision models / escalation ladder / unroutable ceiling | oracle 0.900; EXP#10 4 arms × 190 cases, 1077 calls; composed 0.3579–0.5474 ≤ best single 0.6684; 219/219 menu violations; ornith 35B off 0.558 vs on 0.750 (40 cases) | publishable now |
| B6 (#6) | Graded progressive disclosure is cache-safe | GRADED 7,638 vs best-binary 10,577 tokens = 27.8% saving; prefix 0/72 and 0/48 sweeps moved no byte; EXP#16 live cache **NOT MEASURED** | publishable now, one hole |
| NC1 (6½) | Detectors that cannot fail | 19 detector classes: 12 automated / 3 partial / 4 manual; count checked by `evals/prevention.ts` | publishable now |
| B7 (#7) | Batching binary gates is free; routed extraction 15.3× context, exposure 0/20 | 9,260 rows; gate best F1 0.320; batch-16/90 `effort=none` F1 within ±0.01 at n=1800/config; R5 1.4K vs 21.9K tokens | nearly ready (needs round 2) |
| B8 (#8) | Full history fails on volume, projection fails on chain length | SM_PILOT Part A DR1 **NOT SUPPORTED** (14.9% vs ≥30%); Part C saving 34.1→51.9→65.2→61.7%; H 4/4 every horizon; P dips 1/4 at 24; volume L H 0/4 vs P 4/4; n=4/cell | needs new experiment |
| C9 (#9) | Self-build loop moves its own wall | EXP#18/19/20/22; `BUILD_PLAN.md:123-186` **RUN 36 STOPPED**; no positive control | needs new experiment |
| C10 (#10) | A read is not a gate | EXP#3/3b; 2 resumers double-execute, k=5→5; claim gives exactly 1; outcomes-only journal can never return uncertain | needs new experiment |
| C11 (#11) | ASR=0 | 280 runs, 2,264 calls, 60 scenarios × 4 conditions, 3,628 rows, all Fisher nulls p=1.0 | needs new experiment |
| C12 (#12) | Teardown budgets are theoretical | TEARDOWN_LIVE: 2 runs, 20 completions, max release 1 ms vs 2000 ms budget; F1 fired | needs new experiment |
| #13 | Survey — long-horizon evals 2026 | survey of the 2026 long-horizon-eval landscape | publishable now |
| #14 | Survey — agent harnesses 2026 | survey of 2026 agent harnesses | publishable now |

§D registers **30 further documents that are not papers**. §E sequences O-1 as **#3 first, #1 second, #4 flagship**.
§F records corpus observations, including **F.3's call for a second independent labeller, recorded absent (UCORR1)**.

## 2. What physically exists on disk now, per candidate

Two location facts govern everything below.

**(a) The inventory's Duval-corpus artifacts are mirrored inside this workspace** at
`state/refresh-verify/duval/scnB/state/kg-refresh/duval/repo/.worktrees/engine-a/docs/research/` and the parallel
`…/engine-gap/docs/research/`. Verified present by `find`: `PAPER_DERIVATION.md`, `l1-head-to-head.jsonl`,
`LONG_HORIZON_EVALS_2026.md`, `AGENT_HARNESSES_2026.md`; `…/docs/DECISION_LOG.md` also present; and
`scratch/unc1a/sim/pkg/docs/MISTAKES.md`. These are **mirrors under `state/`, not the paper's own workspace**, and
I did **not open** their contents — so for A1/A2/A3/A4/B5/B6/B7/B8/C9–C12 the artifacts *exist* but their
**content-level support is UNVERIFIED**. Not found under the exact names I searched: `exp11-refinement.json`,
`BUILD_PLAN.md`, `EXP18`, `l1-head-to-head` (dir) — so the *derived* result files behind the §E flagship are not
confirmed present.

**(b) The newly landed material is all in the paper's own workspace** and is what this re-triage can actually stand on.
Verified:

- `repro/encoder-crossover-190/harness/data/fixture-190.json` — **190 cases**, K distribution **{2:33, 3:27, 4:76, 5:54}**,
  **721 options**, **215 distinct option labels**, per-case **named** option arrays, 7 `kind` strata
  (worker.class 30, escalation 30, context.package 28, memory.admission 28, capability.family 26, acquisition 26,
  topology 22), per-case `rationale` and `namespaces`. `experiments/second-labeller-190/characterisation.json`
  independently reports `cases:190`, `header_declared_count:190`, and the same kind counts with
  `kinds_used_not_declared: []`.
- **Per-case records for every arm** — `repro/encoder-crossover-190/results/`: `eval-modernbert-base.json`
  (acc 0.3473684210526316, `perCase` 190), `eval-deberta-v3-base.json` (0.3473684210526316, 190),
  `eval-setfit-mpnet.json` (0.2631578947368421, 190), `eval-majority-class.json` (0.45263157894736844, 190),
  `eval-shuffled-label.json` (0.23157894736842105, 190) — each `perCase` record carries
  `id, kind, options, goldIndex, gold, predIndex, predLabel, pChosen, correct`;
  `baselines.json` → `models["decider-4b-exp11-reproduction"].perCase` (190 records, e.g.
  `worker.class-001 … pChosen: 0.7894`), alongside `models["imajev-4b-exp11"]` and `models["laya-typed-decisions"]`.
- `strategy/BOUNDARY_ANALYSIS.md` — the per-K table at **:81-84** gives exactly the non-monotone gap
  (**K=2 −0.181818, K=3 −0.370370, K=4 −0.355263, K=5 −0.296296**); **:91** "K distribution matches the record
  exactly … 190 cases / 721 options, identical in all four packages"; **:92** widest at K=3, narrowest at K=2;
  **:93** all three heads sit below the majority-class control at K=3/4/5 but at K=2 modernbert **ties** it
  (22/33 = 0.666667); **:95** Wilson CI ±0.17 at K=3 and the K=3-vs-K=4 difference (0.0151) inside noise;
  **:108** quotes `repro/encoder-crossover-190/harness/tcmodel.py:13-30` — "the corpus has **34 distinct gold
  labels**, the 190 fixture cases draw on **215 distinct option labels**, and only **15 labels are shared**
  (`data/manifest.json`, `labelTransfer`)" (secondary citation; the primary corpus manifest was not opened);
  **:139** limits the robust contrast to K=2 vs K≥3.
- `experiments/second-labeller-190/` — `metrics.json` (`cases:190`, `options_total:721`) with a **hard limitation**:
  the second labeller (`routeB-blind-model`) **is a model, not a human annotator**; the kappa "is NOT inter-annotator
  agreement, must NEVER be cited as such, and does not discharge PAPER_CANDIDATES.md F.3's call for a second
  independent labeller". EVIDENCE.md records two kappas — `0.901358` (exact 172/190) and `0.325207` (exact 65/190) —
  with `PREREGISTRATION.md`, `ROBUSTNESS.md`, `RUN.json`, `RUN2.json`, `blinded_cases.json`, `disagreements.jsonl`,
  `disagreementsB2.jsonl`, `labelsB.json`, `labelsB2.json`, `compare.py`, `compare2.py`.
- **Release apparatus** — `orchestration/units/UBUILD1.build.sh` (48575 B, 969 lines, executable, mtime Oct 16 15:17):
  `SRC` defaults to this workspace, `DEST` to `/home/zer0null/research-publish-packages`; fail-closed ship-list
  `SHIP_STAGED` + `SHIP_AUTHORED` at :51-57, prune at :224; the **positive-vocabulary** checker (`gate.sh`,
  exit 0 = every token declared, exit 1 = out-of-vocabulary tokens listed) specified at :398-409 and rebuilt at :486-489.
  `repro/encoder-crossover-190/MANIFEST.json` and `repro/encoder-crossover-190-SANITISED/MANIFEST.json` each record
  42 files, every entry carrying `source` and `source_sha256` (spot-checked `EXCLUDED.md`:
  `source: "authored by UREPRO in this workspace (no target source)"`, `source_sha256: c06bbc8d…`,
  `identical_to_source: true`). `EXCLUDED.md` present in both variants.
- **Neutralisation method** — `strategy/WHOLE_CLASS_NEUTRALISATION.md` (190 lines), `strategy/STIMULUS_NEUTRALISATION.md`
  (313), `strategy/CASE_VARIANT_SETTLEMENT.md` (167), `strategy/CODE_AGNOSTIC_RELEASE_POLICY.md` (713).
- **Verification corpus** — `orchestration/VERDICTS.md` (3309 lines; table columns Date (UTC) / Verifier / Batch /
  Verdict / Plan clause checked / Evidence (commands run) / Red→green / Gate call; 295 `pass|fail|partial` matches);
  `orchestration/handoffs/` = **404 files**; 40+ `strategy/VERIFICATION_REPORT*.md` (`…_2`…`…_35`, plus
  `_AUTHORITATIVE_TREE`, `_FMT1`); defect-class documents `strategy/CITATION_SUPPORT_AUDIT.md`,
  `strategy/CITATION_FETCH_VERIFICATION.md`, `strategy/STALE_RECORD_FIX.md`,
  `papers/encoder-crossover-190/UNSOURCED_RETAINED.md`, `papers/encoder-crossover-190/VERIFIER_CORRECTIONS.md`.
- **A second paper already exists on disk**: `papers/gated-read-batching/` (`MANUSCRIPT.md`, `CLAIMS.md`, `GAPS.md`,
  `REFS.md`, `DISCLOSURE_CHANGES.md`). Directly relevant to the author's question — a different paper from work
  already done is not hypothetical.

**Candidates with no supporting artifact I could find beyond a mirror**: nothing is empty, but C9's derived result
files (`BUILD_PLAN.md`, EXP#18) were not found; B6's `EXP#16` live-cache measurement is recorded as NOT MEASURED;
B8 is n=4/cell with Part A unsupported.

## 3. Tiers

### Tier A — writing effort only (evidence recorded, no new experiment)
**(i) claim — (ii) evidence — (iii) marginal work — (iv) venue/cost — (v) heft — (vi) risk**

1. **A2 / #2 "Replay reproduces the record, not the decision."**
   (ii) 3,040 recorded outputs and `l1-head-to-head.jsonl` in the `state/refresh-verify` mirror — existence verified,
   content UNVERIFIED; the 190-case half is fully present here. (iii) locate and re-verify the 3,040-output corpus;
   tabulate the four variants. (iv) workshop short paper; days of writing. (v) Strong: a counter-intuitive,
   quantified claim ("your replay is a replay of the log, not of the decision"). (vi) **Risk:** the divergence
   numbers may not be reproducible from the mirrored copy, and 41.8% is a *definitional* sensitivity — a reviewer
   can call it an artifact of how rebinding was defined.
2. **A4 / #4 "Self-refinement degrades the decider."**
   (ii) EXP#11 numbers recorded in the inventory; the per-case decider records that would let a reader re-derive
   them **are** on disk (`results/baselines.json` → `decider-4b-exp11-reproduction.perCase`). (iii) re-derive the
   12 measurement strata from `perCase`; the paired p=0.0156 **fails** Bonferroni 0.0125, so the paper must be
   written as a descriptive result or with a pre-registered single primary contrast. (iv) workshop → conference
   short paper; 1–2 weeks. (v) The inventory calls this the flagship (§E). (vi) **Risk:** the statistic does not
   clear the inventory's own α; if written as confirmatory it is dead on arrival.
3. **A3 / #3 "…does not beat a fine-tuned 4B decider."** Already the current paper; listed for completeness.
4. **N3 (new) — independent-verification protocol.** See §4.
5. **#13 / #14 surveys.** (ii) both survey documents exist in the mirror (existence verified). (iii) update to
   submission date; surveys rot fast. (iv) journal or arXiv preprint; cheap. (v) Modest — competitive area.
   (vi) **Risk:** a 2026 survey submitted in 2026 is stale on arrival if the venue is slow.

### Tier B — writing effort plus one small closure step
6. **A1 / #1 "Deriving agent state from an observation stream."** (ii) `PAPER_DERIVATION.md` present in the mirror.
   (iii) confirm the 8 experiments still exit clean. (iv) preprint; ~1–2 weeks. (v) Good. (vi) Overlaps the
   agent-state literature; needs a sharp differentiator.
7. **N1 (new) — sealed fixture as a resource/benchmark.** See §4.
8. **N2 (new) — code-agnostic release + neutralisation methodology.** See §4.
9. **B5 / #5 and B6 / #6.** (ii) EXP#10 and the graded-vs-binary token counts; per-case records exist for the 190
   cases but the 4-arm composition and the 40-case ornith comparison do not. (iii) B5: re-run the composition table;
   B6: the EXP#16 **live** cache measurement is missing and is the whole point of "cache-safe" — either measure it or
   drop the claim from the title. (iv) workshop; 1–2 weeks. (v) Moderate. (vi) **Risk:** B6's central claim is
   untested live.
10. **NC1 / 6½ "Detectors that cannot fail."** (ii) `MISTAKES.md` exists at `scratch/unc1a/sim/pkg/docs/MISTAKES.md`
    (existence verified) — but that is a **simulation package under `scratch/`**, not the target corpus; the
    `evals/prevention.ts` counter cited by the inventory was not located here. (iii) locate the real counter.
    (iv) position/short paper; cheap. (v) Attractive and highly citable if the taxonomy is real.
    (vi) **Risk:** the supporting artifact is a scratch simulation — this needs the live count before submission.

### Tier C — needs a new experiment (do not schedule yet)
11. **#7 B7** — needs "round 2" (a second batching round); 9,260 rows already exist. Workshop; weeks.
    Risk: F1 0.320 is a weak gate; the "free" claim is a cost claim, not a quality claim.
12. **#8 B8** — n=4/cell, Part A **not supported**; needs a properly powered pilot. Risk: the headline is
    unsupported by the author's own pilot.
13. **#10 C10** — needs a resumer/executor harness beyond EXP#3/3b. Risk: narrow.
14. **#11 C11 (ASR=0)** — a null across 3,628 rows; publishable only as a negative-result note. Risk: nulls need
    a venue that wants them.
15. **#12 C12** — 2 runs / 20 completions; max release 1 ms vs a 2000 ms budget. Risk: n=2 cannot carry a budgets paper.
16. **#9 C9** — see §5.

## 4. New proposals (not in the inventory)

**N1 — "A sealed, named-option decision fixture for agent-harness policy: 190 cases, 721 options, and a fail-closed
public package."** *Claim:* a small per-case-named-option multiple-choice fixture (K=2–5, 7 decision kinds, 215
distinct option labels) on which every arm ships a per-case outcome record with `pChosen`, plus a provenance-manifested
public package. *Evidence:* §2(b) — fixture, five arm result files, `baselines.json` decider `perCase`,
`MANIFEST.json` with `source`/`source_sha256`, `EXCLUDED.md`, `gate.sh` positive-vocabulary checker,
`characterisation.json`. *Marginal work:* a datasheet; a licence decision (inventory errata record papers CC BY 4.0,
code/artifact PolyForm Noncommercial 1.0.0 — `strategy/CODE_LICENSING_STRATEGY.md`, not opened, UNVERIFIED);
resolve the second-labeller limitation. *Venue:* resource/dataset track at a workshop, or a datasets-in-brief
note; write-up only. *Heft:* modest but real — the *sealed + per-case-probability + fail-closed release* combination
is the contribution. *Risk:* **the only "second labeller" is a model (`metrics.json` says so explicitly), so the
gold labels have no human-agreement evidence**; reviewers will say 190 cases with unvalidated labels and a
noncommercial licence do not constitute a benchmark. This is the single biggest hazard to the whole family.

**N2 — "Whole-class neutralisation under a positive-vocabulary gate: publishing a reproducible package from a
private corpus."** *Claim:* a documented method for shipping an artifact tied to a private/copyrighted corpus —
whole-class neutralisation of excluded classes, a fail-closed ship-list, and a per-file `source` + `source_sha256`
provenance manifest checked by a positive-vocabulary token gate. *Evidence:* `strategy/WHOLE_CLASS_NEUTRALISATION.md`,
`strategy/STIMULUS_NEUTRALISATION.md`, `strategy/CASE_VARIANT_SETTLEMENT.md`, `strategy/CODE_AGNOSTIC_RELEASE_POLICY.md`,
`orchestration/units/UBUILD1.build.sh`, both `MANIFEST.json` files, `EXCLUDED.md`, and the red→green gate-test
snapshots under `scratch/ugate2/redtest`, `scratch/ugate3/failclosed`, `scratch/ugate3/redtest`. *Marginal work:*
extract the method from the operational docs; report the gate's own red→green result. *Venue:* artifact-evaluation
or reproducibility workshop; low cost, 1–2 weeks. *Heft:* solid as an artifact/short paper; thin as a full
conference paper because there is no study of downstream reuse. *Risk:* reviewers read it as an engineering report
about one repository rather than a transferable method.

**N3 — "Verify like an adversary: per-batch independent verification with red→green guard reverts, and the defect
classes it caught."** *Claim:* a 404-unit research pipeline in which every batch is re-checked by a non-author
verifier that re-runs the evidence commands, checks the plan clause, and must produce at least one red→green revert
of a guard, yields an auditable verdict table and a taxonomy of systematic defects (citation rot from content
changes, transcription drift, unsourced-claim retention). *Evidence:* `orchestration/VERDICTS.md` (3309 lines, with
the exact columns above), **404** `orchestration/handoffs/*.json`, 40+ `strategy/VERIFICATION_REPORT*.md`, and the
defect-class docs listed in §2(b). *Marginal work:* one mining script over `VERDICTS.md` + handoffs plus writing —
no new experiment. *Venue:* workshop on agentic/metascientific research practice, or a short methodology paper;
cheap. *Heft:* genuinely interesting (a mandatory failing-red test as research QA is unusual), but the corpus is
one project. *Risk:* self-referential — the protocol was executed by the very system it audits, and there is no
external adopter.

## 5. What I would ship next, and what I would not

**Ship next: A2 / #2, "Replay reproduces the record, not the decision."** It is the only candidate that is
simultaneously (a) *different* from `papers/encoder-crossover-190/`, (b) already recorded rather than merely
imagined, and (c) a claim with real teeth — a 41.8% divergence between replaying a log and replaying a decision is
the kind of number that gets cited. Its marginal work is writing plus a re-verification pass, it fits a workshop now
and a conference later, and it reuses the exact 190-case fixture and per-case machinery that are already on disk.
Its first task is unglamorous: confirm the 3,040-output corpus and `l1-head-to-head.jsonl` are readable from the
`state/refresh-verify/duval/…/engine-a/docs/research/` mirror and re-derive the four variant percentages from raw
records before a word is drafted. **Lowest-risk fallback:** N3, which needs nothing outside this workspace.

**Do not pursue: C9 / #9, "the self-build loop moves its own wall."** By the inventory's own record the run
**stopped at RUN 36** (`BUILD_PLAN.md:123-186`) and there is **no positive control**, so the claim cannot be
supported at all; the derived result files were also not found on disk. It needs a new experiment *and* a new
design, for a self-referential result of low interest. Secondary: **#11 (ASR=0)** — a 3,628-row null whose only
publishable form is a negative-result note — and **#8 B8**, whose headline the author's own pilot contradicts
(Part A: 14.9% vs ≥30%).

## 6. Unverified register (carried forward)

1. `29`-file package — measured **28**. 2. `15` exclusion classes — **5** top-level sections found. 3. McNemar
p / MDE — not re-derived. 4. Kappa full precision — matched to 6 dp only; `metrics.json` forbids calling it
inter-annotator agreement. 5. Contents of every `state/refresh-verify/…/docs/research/` mirror — existence only.
6. `34` gold labels / `15` shared — secondary quotation in `strategy/BOUNDARY_ANALYSIS.md:108`; the corpus
`data/manifest.json` was not opened. 7. `evals/prevention.ts` counter behind NC1 — not located.
8. Licence terms — from the inventory, not read. 9. `/home/zer0null/Duval` was never accessed.

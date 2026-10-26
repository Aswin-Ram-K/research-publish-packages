# CLAIMS.md — UPAPER1a · verified quantitative claims for A3 (encoder crossover)

Paper candidate: **A3** — *The small-encoder crossover is a prompted-baseline artefact.*
Spec: `strategy/PAPER_CANDIDATES.md` §A3 (lines 247–285).
Evidence tree root (read-only): `the read-only target repository/docs/research/EXP#12-evidence/`.
Target HEAD at unit start: `907fa39da7ba8ecfbe6e976b7a4cddadea7ac36b`.

`verified?` values: **yes** = read verbatim in the named source · **derived** = recomputed and matched ·
**DISAGREES** = source says something else (evidence tree wins).
Rounding: a claim quoted at 4 dp is `yes` when the source full-precision value rounds to it.

## Status: COMPLETE — all sources listed in the unit card were read; scores below are unrecomputed-from-rows where noted.

## Prose cross-check — the same numbers in `EXP#12` §10–§11, `REPORT.md` and `LEARNINGS.md` M12

| claim | value | source file | line/key | verified? | notes |
|---|---|---|---|---|---|
| §10 results table, all 5 arms | 0.3474 / 0.3474 / 0.2632 / 0.4526 / 0.2316 | `experiments/EXP#12-typed-channel-comparison.md` | lines 147–154 | yes | identical to the JSON arms; latency column 12.37/14.16/11.96/~0.00/12.46 ms |
| §10 chance floor row | 0.2911 | same | line 152 | yes | |
| §10 decider rows | 0.6684 (published) and 0.6789 (same-run) | same | lines 153–154 | yes | both appear in one table — the writer must label which is which |
| §10 paired statistics | b=27, c=90, ψ=0.616, Δ=−0.3316, p=4.167e−09, paired MDE 0.1595 | same | lines 158–159 | yes | **ASCII hyphen** in this file |
| §10 F1 verdict | F1 FIRES, best head 0.3474 < 0.6684 and < 0.6789 | same | line 161 | yes | F1 threshold written against **0.6684** |
| §10 F6 caveat | heads timed on GB10, 4B from a served stack | same | line 166 | yes | see `GAPS.md` §2 |
| §10 controls sentence | shuffled-label 0.2316 < 0.2911 floor; lint silent over 152,000 pairs | same | lines 178–181 | yes | |
| §11 resolution | CLOSE; F1+F3 fired; F2/F4/F5/F6 did not | same | lines 202+, `analysis.json .resolution` | yes | |
| §11 errata on "every correction moved down" | 0.3158 → 0.2947 → 0.2632 | same | line 197 | yes | SetFit only — see DISAGREES row |
| `REPORT.md` §1 arm table | identical to JSON (see `EVIDENCE_NOTES.md` §1) | `EXP#12-evidence/REPORT.md` | lines 26–30 | yes | latency column 12.37/14.16/11.96/0.00/12.46 |
| `REPORT.md` §F5 — 0.6684 re-scorability | `reproduces at 3 d.p. = None` | `REPORT.md` | line 104 | yes | **the historical baseline has no per-case rows in the tree** |
| `REPORT.md` §F6 verdict | fires = False; threshold 0.075 s/decision from `DECIDER_TIER §2` | `REPORT.md` | lines 106–107 | yes | not co-measured on this host |
| `REPORT.md` §D3 F3 convention | head ECE 0.0994 vs decider 0.0551 (`probabilities[choice]`) or 0.1547 (`confidence`) | `REPORT.md` | §D3 | yes | F3 fires under the first, not the second — verdict decided by a convention |
| `REPORT.md` imajev fixture figure | 0.6368 (0.645 is the H-A **corpus** stratum) | `REPORT.md` | §"Two things … NOT defects" | yes | do not put 0.645 in a fixture table |
| training non-reproducibility | ModernBERT epoch-1 dev 0.5150 / 0.5900; fixture 0.3421 / 0.3474 | `REPORT.md` | §"A caveat that is not a defect" | yes | ±1–2 pt band is honest for every head |
| `LEARNINGS.md` M12 figures | 0.3474 vs 0.6684; 0.2911 floor; 0.4526 control; b=27, c=90, p=4.17e−09, paired MDE 0.1595 | `experiments/LEARNINGS.md` | lines 262–270 | yes | **typographic minus U+2212** in the p-value here |
| M12 guard 2 (direction of defects) | "every correction moved it *down* (0.3158 → 0.2947 → 0.2632)" | `LEARNINGS.md` | line 281 | yes | SetFit only — see DISAGREES row |
| M12 guard 3 (convention decides) | F3 fires on 0.0551 and not on 0.1547 | `LEARNINGS.md` | line ~287 | yes | |
| M11 errata (paired vs unpaired MDE) | ψ=0.616, unpaired/paired = 0.85×, so the **paired MDE is the larger** | `LEARNINGS.md` | M12 section, errata para | yes | inverts the pre-registration's "~3× overstatement"; the *requirement* to quote paired stands |
| second-labeller limitation | "**It is not IAA.** One pass is a model." | `experiments/second-labeller-190/EVIDENCE.md` | lines 14–23, 309 | yes | must be carried verbatim in spirit |
| second-labeller second model pass | `mimo-v2.6-flash` launched, **returned no file** | `EVIDENCE.md` | lines 153–155 | yes | exactly one model pass exists |
| fixture sha256 unchanged by the second labeller | before = after = `076164ac…b4796`; sandbox copy identical to target | `second-labeller-190/RUN.json` | `fixture_sha256_before/after`, `sandbox_copy_identical_to_target` | yes | no fixture mutation |

## Headline arms (all on the sealed 190-case fixture)

| claim | value | source file | line/key | verified? | notes |
|---|---|---|---|---|---|
| fixture size | 190 | `EXP#12-evidence/analysis.json` | `.instrument.cases` | yes | also `RUN.json.cases`, `metrics.json.cases` |
| fixture sha256 | `076164ac53c2c1aac130953345c481f88b51f4d6fb93d465c7430308a99b4796` | `analysis.json` | `.instrument.instrument190Sha256` | yes | matches second-labeller RUN.json fixture_sha256_before/after (unchanged) |
| `modernbert-base` accuracy | 0.3474 | `EXP#12-evidence/eval-modernbert-base.json` | `.accuracy` = 0.3473684210526316 | yes | 149,015,041 params (`analysis.json .h4.parameterCounts`) |
| `deberta-v3-base` accuracy | 0.3474 | `eval-deberta-v3-base.json` | `.accuracy` = 0.3473684210526316 | yes | 183,832,321 params; see DeBERTa caveat below |
| `setfit-mpnet` accuracy | 0.2632 | `eval-setfit-mpnet.json` | `.accuracy` = 0.2631578947368421 | yes | 109,489,537 params |
| `shuffled-label` accuracy | 0.2316 | `eval-shuffled-label.json` | `.accuracy` = 0.23157894736842105 | yes | control; below chance floor |
| chance floor (mean 1/K) | 0.2911 | `analysis.json` | `.instrument.chanceFloorMean1overK` = 0.29105263157894734 | derived | mean of 1/options-per-case over 190 cases; rounds to 0.2911 |
| `majority-class` control accuracy | 0.4526 | `eval-majority-class.json` | `.accuracy` = 0.45263157894736844 | yes | beats every candidate head |
| majority-class margin over best head | +0.1053 | `analysis.json` | `.observations.majorityClassBeatsEveryCandidate.margin` = 0.10526315789473684 | yes | 0.45263157894736844 − 0.3473684210526316 |
| option-0 rate | 0.3789 | `analysis.json` | `.instrument.option0Rate` = 0.37894736842105264 | yes | position-bias context |
| leaky majority rate over fixture answers | 0.1474 | `analysis.json` | `.instrument.leakyMajorityRateOverFixtureAnswers` = 0.14736842105263157 | yes | not the same as the majority-class control |

## The paired decider-4b comparison

| claim | value | source file | line/key | verified? | notes |
|---|---|---|---|---|---|
| `decider-4b` same-run reproduction | 0.6789 | `analysis.json` | `.publishedBaselines["decider-4b EXP#11 reproduction, instrument190"]` = 0.6789; full precision `.baselinesRescored["decider-4b-exp11-reproduction"].strata.instrument190.accuracy` = 0.6789473684210526 | yes | **primary-baseline candidate A** |
| `decider-4b` historical (D-067) | 0.6684 | `analysis.json` | `.publishedBaselines["decider-4b (published, D-067), instrument190"]` = 0.6684 | yes | **primary-baseline candidate B**; source of the 0.32 claim |
| accuracy difference vs same-run decider | −0.3316 | `analysis.json` | `.comparisons["modernbert-base"].accuracyDifference` = −0.33157894736842103 | derived | matches 0.3473684210526316 − 0.6789473684210526 |
| McNemar discordant pair b (head-only correct) | 27 | `analysis.json` | `.comparisons["modernbert-base"].aOnlyCorrect` = 27 | yes | also 27 for deberta-v3-base |
| McNemar discordant pair c (decider-only correct) | 90 | `analysis.json` | `.comparisons["modernbert-base"].bOnlyCorrect` = 90 | yes | same for deberta-v3-base |
| McNemar both correct / neither correct | 39 / 34 | `analysis.json` | `.comparisons["modernbert-base"].bothCorrect` / `.neitherCorrect` | yes | rows sum: 39+27+90+34 = 190 |
| McNemar exact two-sided p | 4.167e−09 | `analysis.json` | `.comparisons["modernbert-base"].mcnemarExactTwoSidedP` = 4.166817880507353e-09 | yes | **source uses typographic minus (U+2212)**, not ASCII hyphen — grep for `4.1668` not `4.167e-09` |
| McNemar χ² (continuity corrected) | 32.85 | `analysis.json` | `.comparisons["modernbert-base"].mcnemarChiSquareContinuityCorrected` = 32.85470085470085 | yes | |
| paired MDE (quoted) | 0.1595 | `analysis.json` | `.comparisons["modernbert-base"].mdePaired` = 0.15949356562876219 | yes | M11: paired MDE is the one quoted |
| unpaired MDE (not quoted) | 0.1355 | `analysis.json` | `.comparisons["modernbert-base"].mdeUnpaired` = 0.13553502453019095 | yes | shown only to make the correction visible |
| ≥2× MDE claim | −0.3316 vs MDE 0.1595 = 2.079× | `analysis.json` | ratio of the two keys above | derived | 0.33157894736842103 / 0.15949356562876219 = 2.0790 |
| paired bootstrap 95% CI of difference | [−0.4316, −0.2263] | `analysis.json` | `.comparisons["modernbert-base"].pairedBootstrap95CIofDifference` | yes | excludes 0 |
| discordance ψ | 0.6158 | `analysis.json` | `.comparisons["modernbert-base"].discordancePsi` | yes | 117/190 |
| `setfit-mpnet` vs decider | −0.4158, p=3.706e−15, paired MDE 0.1539 | `analysis.json` | `.comparisons["setfit-mpnet"]` | yes | b=15, c=94 |
| `laya-typed-decisions` published | 0.374 | `analysis.json` | `.publishedBaselines["laya-typed-decisions (published), instrument190"]` | yes | a prompted/typed baseline, not a fine-tuned decider |
| `imajev-4b` published (H-A stratum) | 0.645 | `analysis.json` | `.publishedBaselines["imajev-4b (published), H-A corpus stratum"]` | yes | **not** on instrument190 — different corpus stratum; do not compare directly |
| `decider-4b` H-A stratum | 0.6650 | `analysis.json` | `.baselinesRescored["decider-4b-exp11-reproduction"].strata["H-A"].accuracy` = 0.665 | yes | reproduces its published 0.665 |
| decider-4b H-B stratum | 0.67 | `analysis.json` | `.baselinesRescored[...].strata["H-B"].accuracy` = 0.67 | yes | |

## Defect / correction chain (SetFit-MPNet) and controls

| claim | value | source file | line/key | verified? | notes |
|---|---|---|---|---|---|
| SetFit correction chain | 0.3158 → 0.2947 → 0.2632 | `DEFECT-EVIDENCE.json` | `.setfitIntermediates.variants[0..2].accuracy` = 0.3158, 0.3158, 0.2947; final arm = 0.2632 | yes | every correction moved the arm **down**; note the chain has **two** 0.3158 variants (probe unfixed and probe fixed), so the quoted 3-number chain is the sequence of *distinct* values |
| SetFit ECE along the chain | 0.1665 → 0.2738 | `DEFECT-EVIDENCE.json` | `.setfitIntermediates.variants[*].ece` | yes | ECE got worse as accuracy dropped; the final 0.2632 arm has ECE 0.1536 |
| SetFit order-permutation flips along chain | 101 → 46 → 36 → 0 | `DEFECT-EVIDENCE.json` | `.setfitIntermediates.variants[*].orderPermutationFlips` and `.passes.final.arms["setfit-mpnet"].orderPermutationFlips` | yes | final arm is order-stable |
| pass-1 vs final accuracy (`modernbert-base`) | 0.342105 → 0.347368 | `DEFECT-EVIDENCE.json` | `.passes.pass1_buggy_order_probe.arms[...].accuracy` vs `.passes.final.arms[...].accuracy` | yes | **moved UP** — this arm is the exception to "every correction moved the arm down"; the downward chain is SetFit's only |
| pass-1 order-permutation flips | 138 (modernbert), 142, 101, 135, 81 | `DEFECT-EVIDENCE.json` | `.passes.pass1_buggy_order_probe.arms[*].orderPermutationFlips` | yes | final pass: 0 for all candidates; majority-class still 58 |
| F4 n-gram lint: rule | ≥2 distinct shared 8-grams within a single row pair | `lint-report.json` | `.trainVsFixture.rule`, `.ngramSize`=8, `.threshold`=2 | yes | applied in both directions |
| F4 lint silent over training↔fixture pairs | 152,000 pairs, 0 flagged | `lint-report.json` | `.trainVsFixture.forward.pairsCompared`=152000, `.reverse.pairsCompared`=152000, `.flaggedPairs`=0, `.silent`=true | yes | 800 train rows × 190 fixture rows |
| F4 lint silent over training↔dev pairs | 160,000 pairs, 0 flagged | `lint-report.json` | `.trainVsDev.*` | yes | 800 × 200 |
| F4 seeded-copy positive controls | 3 fired: 13 / 44 / 57 shared 8-grams | `lint-report.json` | `.demo.probes[*]`: `seeded.state-only-copy` sharedGramCount 13; `seeded.boilerplate-only-copy` maxPairSharedGramCount 44; `seeded.whole-row-copy` maxPairSharedGramCount 57 | yes | 13 is that probe's total *and* max-pair count; 44 and 57 are **max-pair** counts (their totals are 220 and 233) — the "44/57" are per-pair maxima, so quote them as pair maxima |
| F4 seeded-copy negative control | novel row, 0 shared grams | `lint-report.json` | `.demo.novelSharedGramCount` = 0 | yes | lint can stay silent |
| F4 fired? | false (run NOT void) | `analysis.json` | `.falsifiers.F4.fires` = false; `.resolution.note` | yes | F4 not firing = the run survives |
| resolution | CLOSE, F1 + F3 fired | `analysis.json` | `.resolution.state`, `.resolution.fires` | yes | F1 fired ⇒ method CLOSE per AGENTS.md discipline |
| H4 (accuracy monotone in params) | not supported — observed monotone | `analysis.json` | `.h4.observed` = "monotone", `.h4.verdict` | yes | 0.2632 < 0.3474 = 0.3474 at 109M < 149M < 184M params |
| temperature scaling fitted, grid | geometric 1e-3..1e2, 200 pts | `analysis.json` | `.observations.temperatureScaling.grid` | yes | |
| shuffled-label temperature on grid ceiling | 100.0, `onGridCeiling`=true | `analysis.json` | `.observations.temperatureScaling.perArm["shuffled-label"]` | yes | its reported ECE is an **upper bound** on reachable calibration |
| DeBERTa-v3 trained? | train loss 1.1288 → 1.1235; dev acc 0.50 → 0.495 | `analysis.json` | `.observations.debertaV3Training` | yes | dev majority-class = 0.475; arm "did not train" at the pre-registered operating point — **caveat on treating 0.3474 as a trained-encoder result** |

## Fixture reliability (second labeller)

| claim | value | source file | line/key | verified? | notes |
|---|---|---|---|---|---|
| second-labeller agreement | 0.9053 | `experiments/second-labeller-190/metrics.json` | `.passes["labelsB.json"].agreement` = 0.9052631578947369 | yes | |
| second-labeller κ | 0.9014 (≈0.90) | `metrics.json` | `.passes["labelsB.json"].kappa` = 0.9013584840356494 | yes | **NOT inter-annotator agreement** — labeller is `routeB-blind-model`, a model, not an independent human |
| second-labeller disagreements | 18 / 190 | `metrics.json` | `.disagreements_count_routeB` = 18 | yes | |
| deterministic lexical route (routeA) κ | 0.3252 | `metrics.json` | `.routeA.kappa` = 0.32520740993294694, agreement 0.3421 | yes | this is a **rule**, not a labeller |
| AB mutual agreement | 0.3526 | `metrics.json` | `.passes["labelsB.json"].AB_mutual_agreement` | yes | |
| disagreements where routeA backs the record | 5 | `metrics.json` | `.disagreements_where_routeA_backs_record` = 5 | yes | |
| closed-vocabulary subset (4 kinds, 106 cases) κ | 0.8837 | `metrics.json` | `.stratification.closed_subset["labelsB.json"].kappa` = 0.8837023738280471 | yes | |
| roster-and-bespoke subset (84 cases) κ | 0.9140 | `metrics.json` | `.stratification.roster_and_bespoke_subset["labelsB.json"].kappa` | yes | |

## Discrepancies found against `PAPER_CANDIDATES.md` §A3

**One `DISAGREES` row, and two precision notes.** Every *numeric* value in §A3 was located and matches.

### ✗ `DISAGREES` — "Every correction moved the affected arm DOWN" (§A3:269, `LEARNINGS.md:281`)

| claim | value | source file | line/key | verified? | notes |
|---|---|---|---|---|---|
| "every correction moved the affected arm DOWN" | **FALSE as a universal** | `DEFECT-EVIDENCE.json` | `.passes.pass1_buggy_order_probe.arms["modernbert-base"].accuracy` = 0.342105 vs `.passes.final.arms["modernbert-base"].accuracy` = 0.347368 | **DISAGREES** | SetFit-MPNet did move down (0.3158 → 0.2947 → 0.2632); `modernbert-base` moved **UP** when the order-probe bug was fixed. Safe wording: *"every correction moved the **SetFit** arm down"*, or *"all three defects flattered the candidate"* — the defects favoured the candidate, the fixes did not lower every arm. |

### Precision notes (not disagreements)

1. §A3 says "shuffled-label 0.2316 (below the 0.2911 chance floor)" — correct, but the chance floor is
   `mean(1/K)` over the fixture's own option counts, not the majority-class prior; do not conflate the
   0.2911 floor with the 0.4526 majority-class control.
2. §A3's "the harm is ~2× the MDE": exactly **2.0790×** (0.33157894736842103 / 0.15949356562876219). But
   note the M11 errata — on this run the **paired** MDE (0.1595) is the *larger* figure, the opposite of the
   pre-registration's "paired is conservative" guidance; the conclusion holds against **either** MDE
   (2.079× paired, 2.446× unpaired).

## Verification completeness

All sources named in the unit card were read: §A3, `EXP#12-typed-channel-comparison.md` §10–§11,
all nine load-bearing evidence files, `LEARNINGS.md` M12, and `second-labeller-190/RUN.json` + `metrics.json`
+ `EVIDENCE.md`.

**Not verified, and not verifiable from the tree — recorded as `UNVERIFIED`:**
- **The historical `decider-4b` 0.6684 itself.** It is quoted in `publishedBaselines` and `REPORT.md:189`
  states it *cannot* be re-scored because no per-case rows exist for that measurement. The value is
  **read** (so `yes` as a citation), but its **derivation is unreproducible** — that is the fact the writer
  must know before declaring it the primary baseline.
- **Any latency claim as a like-for-like comparison.** See `GAPS.md` §2 — the tree cannot support one.
- **Any external-work metadata** (titles/authors/venues) beyond the identifiers listed in `REFS.md`.


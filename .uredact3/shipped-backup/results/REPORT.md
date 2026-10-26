# EXP#12 — results (append to §10 of the pre-registration; nothing above it is edited)

**Run:** 2026-10-04 · **Hardware:** GX10 `gx10-163b`, aarch64, NVIDIA GB10 (CUDA), torch `2.11.0+cu130` cu13.0, python 3.12.3

**Instrument:** `evals/fixtures/reflex-decisions.ts`, 190 cases, sha256 `076164ac53c2c1aac130953345c481f88b51f4d6fb93d465c7430308a99b4796` verified before and after export; **read 1 time(s)**, in one process, after every arm was frozen.

**Training corpus:** EXP#11's generated corpus, sha256 `c78681d6cf35bf23245bd24963c5fbdd6b3ea03e1bf74d1b3ddc5a49ca63fd66`, 1,000 construction-gold cases, seed 20261004, 210 families / 18 clans. Trained on the 600 revision + 200 H-A cases (170 families); development on the 200 H-B cases (40 unseen families); sealed test = the 190. **No family and no clan straddles the split** (0 and 0, asserted in `prepare.py`).

**Model API calls: 0.** Every arm ran locally; no remote model was called.

**Resolution: CLOSE.** Falsifiers that fired: **F1, F3**. AGENTS.md experiment discipline: F1 fired, so the method is CLOSE — harvest the learnings naming the falsifier, leave the method behind, and close the branch unmerged. F3 also fired, which kills H2 independently of H1. F2/F4/F5/F6 did not fire, so the run is neither void nor an instrument failure.

**A scoring defect was found and fixed while building this pipeline, and it moved one arm.** `defect-probe.py` measures the fix on the H-B development split; the three variants, on the same weights, are:
* predict_proba clipped to [1e-6, 1-1e-6] (first attempt): dev accuracy 0.5200, cases with an exact tie at the top **24/200**, order-dependent predictions **10/200**
* predict_proba clipped at the denormal edge (second attempt): dev accuracy 0.5200, cases with an exact tie at the top **21/200**, order-dependent predictions **10/200**
* decision_function — the raw log-odds (the fix): dev accuracy 0.5250, cases with an exact tie at the top **0/200**, order-dependent predictions **0/200**

The detector therefore reports the opposite of the zero it ends on, on the same weights, with no fixture read. §11 records the effect on the sealed 190.

**Sealed-read discipline, stated precisely.** `evaluate.py` opens the fixture exactly once per process; the run's receipt (`fixture-read-receipt.json`) records that. There were **four** evaluation passes in total, because two instrument defects were found and fixed while building the pipeline — the passes, what each changed, and the evidence that the fixes moved only the affected arm are in §11. No fixture number was ever used to choose a hyperparameter, a checkpoint, or an epoch: the operating point is epoch 1, fixed before the run.

## 1. Headline — accuracy, calibration, latency on the sealed 190

| arm | role | params | accuracy | 95 % CI | ECE | Brier | ms/decision (warm) |
|---|---|---|---|---|---|---|---|
| `modernbert-base` | candidate | 149,015,041 | **0.3474** | [0.2842, 0.4211] | 0.0994 | 0.2110 | 12.37 |
| `deberta-v3-base` | candidate | 183,832,321 | **0.3474** | [0.2789, 0.4211] | 0.1629 | 0.2458 | 14.16 |
| `setfit-mpnet` | candidate | 109,489,537 | **0.2632** | [0.2053, 0.3263] | 0.1536 | 0.2109 | 11.96 |
| `majority-class` | control | 0 | **0.4526** | [0.3842, 0.5263] | 0.2026 | 0.2661 | 0.00 |
| `shuffled-label` | control | 149,015,041 | **0.2316** | [0.1737, 0.2895] | 0.0808 | 0.1797 | 12.46 |

**Known baselines, and the four the pre-registration fixes (§3):**

| baseline | accuracy | source |
|---|---|---|
| decider-4b (published, D-067), instrument190 | **0.6684** | quoted in the pre-registration |
| imajev-4b (published), H-A corpus stratum | **0.6450** | quoted in the pre-registration |
| laya-typed-decisions (published), instrument190 | **0.3740** | quoted in the pre-registration |
| decider-4b EXP#11 reproduction, instrument190 | **0.6789** | quoted in the pre-registration |
| decider-4b-exp11-reproduction — H-A (re-scored here) | 0.6650 | `docs/research/EXP#11-evidence/decider-rows.jsonl` |
| decider-4b-exp11-reproduction — H-B (re-scored here) | 0.6700 | `docs/research/EXP#11-evidence/decider-rows.jsonl` |
| decider-4b-exp11-reproduction — instrument190 (re-scored here) | 0.6789 | `docs/research/EXP#11-evidence/decider-rows.jsonl` |
| imajev-4b-exp11 — H-A (re-scored here) | 0.6450 | `docs/research/EXP#11-evidence/imajev-rows.jsonl` |
| imajev-4b-exp11 — H-B (re-scored here) | 0.6700 | `docs/research/EXP#11-evidence/imajev-rows.jsonl` |
| imajev-4b-exp11 — instrument190 (re-scored here) | 0.6368 | `docs/research/EXP#11-evidence/imajev-rows.jsonl` |
| laya-typed-decisions — instrument190 (re-scored here) | 0.3737 | `docs/research/l1-head-to-head.jsonl` |

Chance floor on this fixture (mean 1/k over the 190) is **0.2911**; the majority rate over the fixture's own answers is **0.1474** (leaky — it uses the fixture's labels — and reported only for scale), and always-option-0 scores **0.3789**.

## 2. The mandatory controls

* **`majority-class`** — fixture accuracy **0.4526**, ECE **0.2026**, Brier **0.2661**. Development accuracy 0.4750.
* **`shuffled-label`** — fixture accuracy **0.2316**, ECE **0.0808**, Brier **0.1797**. Development accuracy 0.2950.

The shuffled-label control is the pipeline's leak detector: it must score near chance or the pipeline leaks the answer, and the majority-class control must be **badly calibrated** or a detector that cannot show a badly-calibrated arm cannot certify a well-calibrated one.

## 3. Paired comparison — exact McNemar on discordant pairs, and the PAIRED MDE

Every arm was scored on the same 190 cases, so the comparison against the decider-4b control arm is paired. `b` = head right and 4B wrong, `c` = head wrong and 4B right.

| head | b | c | ψ=(b+c)/n | Δaccuracy | McNemar exact p | MDE (paired) | MDE (unpaired) | ratio |
|---|---|---|---|---|---|---|---|---|
| `modernbert-base` | 27 | 90 | 0.616 | -0.3316 | 4.167e-09 | **0.1595** | 0.1355 | 0.85× |
| `deberta-v3-base` | 27 | 90 | 0.616 | -0.3316 | 4.167e-09 | **0.1595** | 0.1355 | 0.85× |
| `setfit-mpnet` | 15 | 94 | 0.574 | -0.4158 | 3.706e-15 | **0.1539** | 0.1304 | 0.85× |

**M11 is applied: the PAIRED figure is the one quoted.** It is `2.8016 · sqrt(ψ/n)` at this run's *observed* discordance ψ. The unpaired `2.8016 · sqrt(p₁(1−p₁)/n + p₂(1−p₂)/n)` is shown beside it. The convention matches EXP#11's recorded `mdeInstrument` (2.8016·sqrt(0.5/200) = 0.14007926090564843).

**One scope correction to M11, measured on this run and worth recording.** The pre-registration says the unpaired figure overstated our blind spot by ~3x. That is a property of LOW discordance: unpaired/paired = sqrt((p1(1-p1) + p2(1-p2)) / psi), which grows as psi shrinks (~3x at psi ~ 0.05, n = 190) and falls BELOW 1 once psi exceeds p1(1-p1) + p2(1-p2). On this run psi is **0.616** - the two arms disagree on most cases - so the ratio is **0.85x**, i.e. the paired MDE (**0.1595**) is the *larger* of the two, not the smaller. Quoting the paired figure is still the correct requirement; it is simply not the lenient one here. The observed difference (-0.3316) is more than twice either MDE, so the conclusion does not depend on which is quoted.

## 4. Per-kind accuracy on the sealed 190

| kind | n | `modernbert-base` | `deberta-v3-base` | `setfit-mpnet` | `majority-class` | `shuffled-label` |
|---|---|---|---|---|---|---|
| acquisition | 26 | 0.154 | 0.115 | 0.154 | 0.231 | 0.115 |
| capability.family | 26 | 0.308 | 0.423 | 0.231 | 0.462 | 0.038 |
| context.package | 28 | 0.179 | 0.321 | 0.357 | 0.571 | 0.286 |
| escalation | 30 | 0.700 | 0.633 | 0.300 | 0.733 | 0.267 |
| memory.admission | 28 | 0.357 | 0.357 | 0.071 | 0.357 | 0.179 |
| topology | 22 | 0.364 | 0.227 | 0.318 | 0.227 | 0.273 |
| worker.class | 30 | 0.333 | 0.300 | 0.400 | 0.500 | 0.433 |

## 5. Falsifiers, each with its verdict

**F1 — fires when encoder accuracy < 0.6684 → H1 is FALSE.** fires = **True**. H1 IS FALSE — the best head (modernbert-base, 0.3474) is below the best 4B's 0.6684. The published 'encoder wins' evidence compares an encoder against a PROMPTED LLM; on a fine-tuned comparison on our fixture the encoder does not win.

**F2 — fires when a head's development accuracy ≤ the majority-class baseline → VOID for that arm.** fires = **False**. no arm is void on the development split
  * `modernbert-base` dev 0.5150 vs majority-class dev 0.4750 → fires=False
  * `deberta-v3-base` dev 0.5000 vs majority-class dev 0.4750 → fires=False
  * `setfit-mpnet` dev 0.5250 vs majority-class dev 0.4750 → fires=False

**F3 — fires when encoder ECE ≥ the decider's ECE → H2 is FALSE.** fires = **True**. H2 IS FALSE — even the best-calibrated head (modernbert-base, ECE 0.0994) is not better calibrated than the decider (ECE 0.0551). The 'native distribution' argument does not survive contact.
  * decider-4b ECE on the same 190, re-scored here: **0.0551**; heads: `modernbert-base` 0.0994, `deberta-v3-base` 0.1629, `setfit-mpnet` 0.1536

**F4 — fires on any ≥2-shared-8-gram overlap between training rows and the fixture → RUN VOID.** fires = **False**. the run is not void — 0 rows removed over 152000 pairs, both directions, and the lint was shown to fire on three seeded copies and stay silent on a novel row
  * pairs compared 152000; seeded copies that FIRED: seeded.state-only-copy, seeded.boilerplate-only-copy, seeded.whole-row-copy; rows that stayed SILENT: control.novel-row

**F5 — fires when the known baselines are not reproduced when re-scored → RUN VOID.** fires = **False**. not void — the stored baselines re-score to their published values through this experiment's own accuracy/ECE/Brier code
  * decider-4b reproduction 0.6789 @ instrument190: re-scored 0.6789 vs published 0.6789 on stratum `instrument190` → reproduces at 3 d.p. = **True**
  * imajev-4b 0.645 @ H-A (its actual source): re-scored 0.6450 vs published 0.645 on stratum `H-A` → reproduces at 3 d.p. = **True**
  * imajev-4b fixture figure @ instrument190: re-scored 0.6368 vs published 0.6368 on stratum `instrument190` → reproduces at 3 d.p. = **True**
  * laya 0.374 @ instrument190: re-scored 0.3737 vs published 0.374 on stratum `instrument190` → reproduces at 3 d.p. = **True**
  * decider-4b H-A 0.6650 @ H-A: re-scored 0.6650 vs published 0.665 on stratum `H-A` → reproduces at 3 d.p. = **True**
  * decider-4b 0.6684 (D-067): re-scored n/a vs published 0.6684 on stratum `instrument190` → reproduces at 3 d.p. = **None**

**F6 — fires when a head's latency > 0.075 s/decision warm → H3 is FALSE.** fires = **False**. H3 survives — every head is faster per decision than the 4B's measured warm latency
  * the 0.075 s threshold is the pre-registered 4B figure from DECIDER_TIER §2; the baseline's own re-scored per-decision latency on these 190 rows is quoted alongside it, and the two were measured on different serving stacks, so the encoder-vs-4B latency comparison is not like-for-like hardware.

**H4 (diagnostic, not a falsifier).** H4 is not supported: accuracy moves monotonically with parameter count across these three heads
  * parameter counts {'modernbert-base': 149015041, 'deberta-v3-base': 183832321, 'setfit-mpnet': 109489537, 'majority-class': 0, 'shuffled-label': 149015041}; accuracies {'setfit-mpnet': 0.2631578947368421, 'modernbert-base': 0.3473684210526316, 'deberta-v3-base': 0.3473684210526316}

## 6. The calibration convention, and why it is load-bearing

The rows EXP#11 stored carry TWO probability-like fields: `probabilities` (the decider's softmax over the options) and a separate post-calibration `confidence` scalar. They disagree (mean |confidence − p(chosen)| = 0.12 on these 190 rows), and the choice decides F3:

| convention | decider-4b ECE on the 190 | best head ECE | F3 verdict |
|---|---|---|---|
| **probability of the option chosen** (`probabilities[choice]`) — the L1 head-to-head protocol | **0.0551** | 0.0994 | **FIRES — H2 is FALSE** |
| the stored `confidence` field | 0.1547 | 0.0994 | does not fire |

The primary is `probabilities[choice]`, on three grounds: `docs/research/L1_HEAD_TO_HEAD.md` defines it verbatim; it is the decider's *native per-option distribution*, which is the thing H2 makes a claim about; and it is the only convention that reproduces the published ECE figures, which is an instrument validation rather than an assertion:
* `laya`: ECE 0.1036 from `p_chosen` vs published 0.104 → reproduces = **True** (n = 190)
* `decider-0.8b`: ECE 0.0746 from `p_chosen` vs published 0.075 → reproduces = **True** (n = 190)

**F3's verdict does not depend on the temperature fit.** Best head ECE with the fitted temperature 0.0994 → fires = True; best head with no calibration (T=1) 0.0558 → fires = True; the decider is 0.0551. The verdict turns only on which decider field the comparison uses, not on how the encoder's probabilities were scaled.

The heads' own ECE is reported **after** a scalar temperature fitted on the H-B development split (never on the fixture). The same quantity with no calibration is:
* `modernbert-base`: T=1 ECE 0.1129 vs fitted ECE 0.0994
* `deberta-v3-base`: T=1 ECE 0.0558 vs fitted ECE 0.1629
* `setfit-mpnet`: T=1 ECE 0.6836 vs fitted ECE 0.1536

## 7. Instrument validation

1. **F4 lint, both directions.** Training-800 → sealed-190: **0 rows removed** over 152000 pairs (forward 0, reverse 0).
2. **The lint was shown to fire.** Three seeded copies of a training row — state-only, boilerplate-only, whole-row — each fired, and the unmodified fixture row stayed silent:
   * `seeded.state-only-copy` fired=**True** (expected True); shared 8-grams with the single named source row **13**, summed over the **1** flagged source rows **13** (the corpus repeats a family's boilerplate verbatim across sibling cases), fields carrying them `question, state`
   * `seeded.boilerplate-only-copy` fired=**True** (expected True); shared 8-grams with the single named source row **44**, summed over the **5** flagged source rows **220** (the corpus repeats a family's boilerplate verbatim across sibling cases), fields carrying them `instructions, question`
   * `seeded.whole-row-copy` fired=**True** (expected True); shared 8-grams with the single named source row **57**, summed over the **5** flagged source rows **233** (the corpus repeats a family's boilerplate verbatim across sibling cases), fields carrying them `instructions, state`
   * `control.novel-row` fired=**False** (expected False); shared 8-grams with the single named source row **0**, summed over the **0** flagged source rows **0** (the corpus repeats a family's boilerplate verbatim across sibling cases), fields carrying them ``
3. **Order sensitivity**, the exploratory add-on §5.6 permits and does not fold into H1 — the same fixture re-scored with every case's options permuted:
   * `modernbert-base`: prediction flips 0/190, max |Δp(chosen)| 0.00e+00
   * `deberta-v3-base`: prediction flips 0/190, max |Δp(chosen)| 0.00e+00
   * `setfit-mpnet`: prediction flips 0/190, max |Δp(chosen)| 0.00e+00
   * `majority-class`: prediction flips 58/190, max |Δp(chosen)| 0.00e+00
   * `shuffled-label`: prediction flips 0/190, max |Δp(chosen)| 0.00e+00

## 8. Observations and caveats on this run

* **The majority-class control outscores every candidate head.** majority-class 0.4526 vs the best head 0.3474 (margin 0.1053). the mandatory majority-class control outscores every candidate head on the sealed 190. This is the headline caveat on this run: the three heads do not beat a corpus-marginal prior, so F1's failure is not a near miss.
* **Temperature scaling.** a fitted T on the grid boundary means the optimum was not interior; the reported ECE is then an upper bound on what this arm's calibration could reach. `modernbert-base` T=1.097; `deberta-v3-base` T=0.004; `setfit-mpnet` T=39.627; `majority-class` T=1.000; `shuffled-label` T=100.000 (grid ceiling)
* **DeBERTa-v3-base did not train.** DeBERTa-v3-base's training loss barely moved (see the curve) and its dev accuracy is only just above the majority-class baseline, so this arm should be read as 'did not train at the pre-registered epoch-1 operating point with lr 2e-5 and 50 steps' rather than as 'trained and failed to transfer'. F2 did not fire as written because its dev accuracy is strictly above the majority baseline. train loss curve ['1.1288', '1.1235'], dev accuracy ['0.5000', '0.4950'], majority-class dev 0.4750.
* **The order-permutation probe is exploratory** (pre-registration §5.6) and is never folded into H1. It is reported in §1's table by arm: 0 flips for all three per-option scorer arms, and non-zero only for the two arms whose per-option scores contain exact ties (`majority-class`, whose corpus marginals tie, and `setfit-mpnet`, whose saturated logistic head ties).

## 9. What was run, and how to reproduce

```bash
./scripts/run.sh tools/typed-channel/export-fixture.ts
./scripts/run.sh tools/typed-channel/lint.ts --demo
python3 tools/typed-channel/prepare.py
python3 tools/typed-channel/train.py --epochs 3          # GX10, GB10, CUDA
python3 tools/typed-channel/evaluate.py
python3 tools/typed-channel/analyze.py
python3 tools/typed-channel/collect.py
```

Training wall clock: **923 s** for all five arms (3 encoder arms followed to 3 epochs with early stopping, plus the two controls). Well inside the 2 GPU-hour hard cap.

Per-arm training seconds: `modernbert-base` 361s, `deberta-v3-base` 299s, `setfit-mpnet` 20s, `majority-class` 0s, `shuffled-label` 243s

### Development curve (H-B, unseen families) — the epoch-1 row is the pre-registered operating point

* `modernbert-base` — operating point: epoch 1 (pre-registered)
  * epoch 1: dev acc 0.5150, T 1.10, ECE 0.0941, 110.3s
  * epoch 2: dev acc 0.5350, T 0.33, ECE 0.1108, 109.7s
  * epoch 3: dev acc 0.5650, T 1.04, ECE 0.0621, 109.7s
* `deberta-v3-base` — operating point: epoch 1 (pre-registered)
  * epoch 1: dev acc 0.5000, T 0.00, ECE 0.0806, 136.8s
  * epoch 2: dev acc 0.4950, T 0.01, ECE 0.0600, 136.3s
* `setfit-mpnet` — operating point: the single logistic fit (the head has no epoch loop; one fit is its epoch 1)
  * epoch 1: dev acc 0.5250, T 39.63, ECE 0.0938, 19.8s
* `majority-class` — operating point: no training — the corpus label marginal, restricted to each case's option set
  * epoch None: dev acc 0.4750, T 1.00, ECE 0.0927, 0.0s
* `shuffled-label` — operating point: epoch 1 (pre-registered)
  * epoch 1: dev acc 0.2950, T 100.00, ECE 0.0765, 110.0s
  * epoch 2: dev acc 0.2050, T 100.00, ECE 0.1669, 110.0s

## 10. Incomplete and unverifiable — named, not implied

* **`decider-4b 0.6684` (D-067) cannot be re-scored.** No per-case rows for that specific measurement are in the tree, so F5 cannot check it directly; the same-run reproduction of the same instrument (0.6789) is what stands in, and that re-scores exactly.
* **`imajev-4b 0.645` is mislabelled in pre-registration §3.** It is imajev's H-A corpus accuracy; its 190-fixture accuracy is 0.6368. Reported, not edited — the pre-registration is frozen and the correction belongs in an errata line the Lead writes.
* **The latency comparison is not like-for-like hardware.** The heads were timed on the GX10's GB10 with local weights; the decider's 0.075 s/decision figure and the re-scored 0.0531 s/decision on these rows come from a served model on a different stack. F6 is evaluated against the pre-registered threshold as written, and the caveat is stated in its verdict.
* **`DeBERTa-v3-base`'s arm is a weak read.** Its training loss barely moved and its dev accuracy sits 2.5 points above the majority-class baseline, so F2 did not fire as written but the arm should be read as 'did not train at the operating point', not as 'trained and failed to transfer'. Tuning it (lower lr, more steps, better pooling) is a different experiment.
* **The rendered split files are not in version control.** The repository's root `.gitignore` carries a blanket `*.jsonl` rule, which matches `tools/typed-channel/data/train.jsonl` and `data/dev.jsonl`. They are byte-reproducible from the committed `data/corpus.json`, `data/manifest.json` and `prepare.py` — verified in this run by re-running `prepare.py` and comparing sha256 (`24c39afa…` train, `d311a99f…` dev, both unchanged) — but a reader should not believe they are committed when they are not. See `LEAD-WIRING.md` §4.
* **The trace record and the visit-log line are prepared, not appended.** `results/trace-records.jsonl` and `results/visit-log-line.txt` hold them. The build lane did not call `tools/trace.ts append`: the trace store already had another lane's uncommitted write, and `append()` requires a dense successor `seq`, so two concurrent appends would have written the same `seq` and `verify()` would then have failed. The Lead appends them once the lanes settle.


## 11. Instrument defects found and fixed during the run

Three defects were found by running the experiment, and all three were fixed before the numbers in
§1 were produced. They are recorded here rather than quietly corrected, because each one changed a
number and a reader has to be able to see which.

### D1 — the order-permutation probe indexed the wrong list (fixed; changed no accuracy)

The exploratory §5.6 probe re-scored each case with its options permuted and compared the new argmax
against the unpermuted prediction. It read the predicted label out of the **original** option list
instead of the **permuted** one, so every prediction was compared against the wrong label.

Observed (retained in `results/DEFECT-EVIDENCE.json`, pass 1): `modernbert-base` reported
**142/190 prediction flips** and `deberta-v3-base` **138/190**, with a maximum |Δp(chosen)| of 0.886 —
on heads whose per-option scores are computed independently, so exactly 0 flips are expected by
construction. The impossible magnitude is what exposed it, not a review.

After the fix: **0 flips** for all three per-option scorer arms (`modernbert-base`,
`deberta-v3-base`, `shuffled-label`). Accuracy, ECE and Brier were **bit-identical before and after**
the fix in all five arms, which is the evidence that this was a measurement bug and not a modelling
one. The two arms that still report flips (`majority-class` 58/190, `setfit-mpnet` 36/190) do so
because their per-option scores contain genuine exact ties and `argmax` resolves ties by presented
position — see D2 for what part of that was also a defect.

### D2 — the SetFit head ranked and scaled a SATURATED probability instead of its raw logit (fixed; changed `setfit-mpnet`)

`LogisticPairHead` scores each candidate option with an L2 logistic regression over 3072
standardised sentence-pair features (2581 training pairs). Its `case_logits` converted
`predict_proba` into a logit as `log(p) - log1p(-p)`, clipping `p` to keep the logit finite.

That is the wrong quantity. The head **saturates**: it returns exactly `0.0` and exactly `1.0` for
whole groups of options, so every saturated option receives the *same* score. `argmax` then resolves
those ties by the **position** the option happened to be presented in, which makes the arm's decision
order-dependent for no modelling reason.

Three attempts, and the measurement that chose between them. `defect-probe.py` re-runs each variant
over the 200 H-B **development** cases — it never reads the sealed fixture, because the defect belongs
to the arm's scoring path and not to the instrument:

| scoring path | dev accuracy | cases with an exact tie at the top | order-dependent predictions |
|---|---|---|---|
| `predict_proba` clipped to `[1e-6, 1-1e-6]` | 0.5200 | 24 / 200 | 10 / 200 |
| `predict_proba` clipped at the denormal edge | 0.5200 | 21 / 200 | 10 / 200 |
| **`decision_function` — the raw log-odds** | **0.5250** | **0 / 200** | **0 / 200** |

The second row is why the first *fix* was not a fix: widening the clip from `1e-6` to the denormal edge
barely moved the tie count, because `predict_proba` has already discarded the information — no choice
of clip can recover a score that is no longer there. `decision_function` returns the log-odds the fit
actually produced, unsaturated, so no clip is needed and no tie is manufactured. This probe is the
instrument validation for the fix: it shows the detector able to report the *opposite* (24 ties, 10
order-dependent predictions) before it is trusted to report zero.

Effect on the sealed 190, on the **same weights**:

| `setfit-mpnet` | accuracy | ECE | order flips |
|---|---|---|---|
| first attempt: clip `[1e-6, 1-1e-6]` | 0.3158 | 0.1665 | 46 / 190 *(101/190 before the probe itself was fixed — D1)* |
| second attempt: denormal-edge clip, old dev fit | 0.2947 | 0.2738 | 36 / 190 |
| **the fix: `decision_function`, refitted on dev** | **0.2632** | **0.1536** | **0 / 190** |

Two things this records. First, the temperature is fitted on the development split, so it must be
fitted against the same scoring path that produces the evaluation logits; the fix changed that path, the arm was re-fitted and the run re-evaluated (`manifest-train.json` carries a
`setfitRefitNote`). Second, **every correction moved this arm DOWN** — 0.3158 → 0.2947 → 0.2632. The
defects were flattering it. The reported `setfit-mpnet` figure is 0.2632, ECE 0.1536, temperature
39.63, 0 order flips.

### D3 — the decider's ECE convention was ambiguous, and it flips F3 (resolved; both readings reported)

The EXP#11 rows carry two probability-like fields and they disagree: `probabilities` (the decider's
softmax over the options) and a post-calibration `confidence` scalar (mean |confidence − p(chosen)| =
0.12 on these 190 rows). The decider's ECE on the same 190 cases is:

* **0.0551** from `probabilities[choice]` — the convention `docs/research/L1_HEAD_TO_HEAD.md` defines
  verbatim, and the decider's *native* distribution, which is what H2 makes a claim about;
* **0.1547** from the stored `confidence` field.

The best head's ECE is 0.0994. So F3 **fires** under the first convention (0.0994 ≥ 0.0551 → H2 is
FALSE) and does **not** fire under the second (0.0994 < 0.1547). This is not a judgement call that can
be left implicit, so the report carries both, and the primary is `probabilities[choice]` because it is
the only convention that reproduces the two published ECE figures for models whose rows are in the
tree — `laya` 0.1036 vs published 0.104, and `decider-0.8B` 0.0746 vs published 0.075. A convention
that cannot reproduce a published number is not the convention the published number was computed
under.

### Two things that were checked and are NOT defects

* **The evaluation is deterministic, and the fixes were isolated.** Independent evaluation processes
  over the same weights produced **identical** accuracy, ECE, Brier, temperature and per-case
  predictions for the four arms whose code did not change, across every pass; only the arm whose
  scoring path changed moved. That is the evidence that D1 and D2 were measurement defects, not
  modelling choices.
* **`imajev-4b 0.645` does not reproduce as a fixture number because it is not one.** The
  pre-registration §3 lists it beside two fixture figures, but from EXP#11's stored rows imajev-4b's
  round-0 accuracies are H-A **0.6450** / H-B 0.6700 / instrument190 **0.6368**. 0.645 is the H-A
  corpus figure. Each published number is therefore re-scored against the stratum it actually came
  from (see §5, F5), and the stratum is named.

### A caveat that is not a defect: training is not bit-reproducible

Three training runs of the identical command produced `modernbert-base` epoch-1 dev accuracies of
0.5150 and 0.5900, and 190-fixture accuracies of 0.3421 and 0.3474. At the pre-registered epoch-1
operating point the arms are barely trained, so many of their per-case decisions are near-ties and
small weight differences move several of them. Every number in this report comes from **one** run
(`out/manifest-train.json`, `out/manifest-eval.json`), but a reader should read a ±1–2 point band
around the head accuracies and a ±0.03 band around the shuffled-label control, not treat the third
decimal as reproducible.


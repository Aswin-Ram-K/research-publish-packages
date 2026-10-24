# EVIDENCE_NOTES.md — UPAPER1a · re-runnable evidence for every A3 number

All paths under `the read-only target repository` (STRICTLY READ-ONLY; nothing was written there).
Target HEAD at unit start and end: `907fa39da7ba8ecfbe6e976b7a4cddadea7ac36b`.
Every command below is copy-pasteable and was actually run by this unit; outputs are verbatim.

> **Search gotcha, confirmed.** `strategy/PAPER_CANDIDATES.md:265` and `LEARNINGS.md:265` write the
> p-value with a **typographic minus `U+2212`** (`4.167e−09`), so `grep 4.167e-09` on those two files
> returns nothing. The machine-readable sources (`analysis.json`, `REPORT.md`) use an ASCII hyphen.
> Search for `4.1668` / `4.167` instead, or use `grep -P '\x{2212}'`.

---

## 1. The five arms — the load-bearing numbers

```bash
cd "the read-only target repository/docs/research/EXP#12-evidence" && python3 -c "
import json
for f in ['eval-modernbert-base.json','eval-deberta-v3-base.json','eval-setfit-mpnet.json','eval-majority-class.json','eval-shuffled-label.json']:
    d=json.load(open(f))
    print('%-28s arm=%-16s acc=%r ci=%s ece=%r brier=%r temp=%r latMean=%r' % (f, d['arm'], d['accuracy'], d['accuracy95CI'], d['ece'], d['brier'], d['temperature'], d['latencyMs']['mean']))
"
```

Verbatim output:

```
eval-modernbert-base.json    arm=modernbert-base  acc=0.3473684210526316  ci=[0.28421052631578947, 0.42105263157894735] ece=0.09936282184403895 brier=0.21103944642584352 temp=1.096986 latMean=12.366654429780809
eval-deberta-v3-base.json    arm=deberta-v3-base  acc=0.3473684210526316  ci=[0.2789473684210526, 0.42105263157894735]  ece=0.16294549554751392 brier=0.24579965200176665 temp=0.003571 latMean=14.15883741962413
eval-setfit-mpnet.json       arm=setfit-mpnet      acc=0.2631578947368421  ci=[0.20526315789473684, 0.3263157894736842] ece=0.15360621121272539 brier=0.21088685608126073 temp=39.626886 latMean=11.95663549659545
eval-majority-class.json     arm=majority-class    acc=0.45263157894736844 ci=[0.38421052631578945, 0.5263157894736842] ece=0.20261579141143732 brier=0.26613296806538966 temp=1.0 latMean=0.0030401554938993955
eval-shuffled-label.json     arm=shuffled-label    acc=0.23157894736842105 ci=[0.1736842105263158, 0.2894736842105263]  ece=0.0807562278701531 brier=0.1796953105596048 temp=100.0 latMean=12.46357091637165
```

**`REPORT.md` table rows** (`EXP#12-evidence/REPORT.md` §1 "Headline — accuracy, calibration, latency on the sealed 190", lines 26–30) — verbatim:

```
| `modernbert-base` | candidate | 149,015,041 | **0.3474** | [0.2842, 0.4211] | 0.0994 | 0.2110 | 12.37 |
| `deberta-v3-base` | candidate | 183,832,321 | **0.3474** | [0.2789, 0.4211] | 0.1629 | 0.2458 | 14.16 |
| `setfit-mpnet` | candidate | 109,489,537 | **0.2632** | [0.2053, 0.3263] | 0.1536 | 0.2109 | 11.96 |
| `majority-class` | control | 0 | **0.4526** | [0.3842, 0.5263] | 0.2026 | 0.2661 | 0.00 |
| `shuffled-label` | control | 149,015,041 | **0.2316** | [0.1737, 0.2895] | 0.0808 | 0.1797 | 12.46 |
| *chance floor (mean 1/k)* | — | *0.2911* | — | — | — |
| **decider-4b** (baseline) | 4.66B | **0.6684** | — | — | — |
| *decider-4b, same-run reproduction* | 4.66B | *0.6789* | *0.0551* | *53.06* |
```
Every arm row agrees with the JSON to the printed precision. Latency column = `latencyMs.mean` (ms).

## 2. Instrument properties (chance floor, option-0, leaky majority)

```bash
cd "the read-only target repository/docs/research/EXP#12-evidence" && python3 -c "
import json; print(json.dumps(json.load(open('analysis.json'))['instrument'], indent=1))"
```

Verbatim output:

```json
{
 "fixtureReads": 1,
 "instrument190Sha256": "076164ac53c2c1aac130953345c481f88b51f4d6fb93d465c7430308a99b4796",
 "cases": 190,
 "chanceFloorMean1overK": 0.29105263157894734,
 "leakyMajorityRateOverFixtureAnswers": 0.14736842105263157,
 "option0Rate": 0.37894736842105264
}
```

`0.29105263157894734` rounds to **0.2911** — matches §A3 and `REPORT.md:48`. `REPORT.md:48` verbatim:
`Chance floor on this fixture (mean 1/k over the 190) is **0.2911**; the majority rate over the fixture's own answers is **0.1474** ... and always-option-0 scores **0.3789**.`

**Derivation of the chance floor** (independent check): it is the mean of `1/K` over cases, where K is the
option count. `RUN.json.options_per_case = {"2":33,"3":27,"4":76,"5":54}` (33+27+76+54 = 190).
`(33/2 + 27/3 + 76/4 + 54/5)/190 = (16.5+9+19+10.8)/190 = 55.3/190 = 0.29105263…` ✔ matches to full precision.

## 3. The paired decider-4b comparison (McNemar, MDE)

```bash
cd "the read-only target repository/docs/research/EXP#12-evidence" && python3 -c "
import json; c=json.load(open('analysis.json'))['comparisons']; print(json.dumps(c['modernbert-base'], indent=1))"
```

Verbatim output:

```json
{
 "a": "modernbert-base",
 "b": "decider-4b (EXP#11 reproduction, F0 frame)",
 "n": 190,
 "bothCorrect": 39,
 "aOnlyCorrect": 27,
 "bOnlyCorrect": 90,
 "neitherCorrect": 34,
 "discordant": 117,
 "discordancePsi": 0.6157894736842106,
 "accuracyA": 0.3473684210526316,
 "accuracyB": 0.6789473684210526,
 "accuracyDifference": -0.33157894736842103,
 "mcnemarExactTwoSidedP": 4.166817880507353e-09,
 "mcnemarChiSquareContinuityCorrected": 32.85470085470085,
 "mdePaired": 0.15949356562876219,
 "mdeUnpaired": 0.13553502453019095,
 "mdeRatioUnpairedOverPaired": 0.8497836511202137,
 "detectableDifferenceAtObservedDiscordance": 0.15949356562876219,
 "note": "the PAIRED MDE is the one quoted (M11); the unpaired figure is shown only to make the correction visible",
 "pairedBootstrap95CIofDifference": [-0.43157894736842106, -0.22631578947368422]
}
```

**Derivations performed by this unit** (all matched):
- `accuracyDifference` = 0.3473684210526316 − 0.6789473684210526 = **−0.33157894736842103** ✔
- `b`=27, `c`=90 → **Δ = (b−c)/n = (27−90)/190 = −63/190 = −0.3315789473684211** ✔ (same value, independent path)
- `discordant` = 27+90 = 117; `discordancePsi` = 117/190 = **0.6157894736842106** ✔
- `p` = 4.166817880507353e−09 → **4.167e−09** at 4 s.f. ✔
- harm/MDE = 0.33157894736842103 / 0.15949356562876219 = **2.0790×** → "~2× the MDE" ✔
- row identity: 39+27+90+34 = **190** ✔

**`REPORT.md` rows** (lines 63–64, §"paired vs decider-4b reproduction") — verbatim:

```
| `modernbert-base` | 27 | 90 | 0.616 | -0.3316 | 4.167e-09 | **0.1595** | 0.1355 | 0.85× |
| `deberta-v3-base` | 27 | 90 | 0.616 | -0.3316 | 4.167e-09 | **0.1595** | 0.1355 | 0.85× |
```
Note `REPORT.md` writes the p-value with an **ASCII hyphen** here. `analysis.json` carries the full
precision. Agreement is exact.

### ⚠ Important nuance the writer must not invert

`REPORT.md:69` and `LEARNINGS.md` (M11 errata) both state that on **this** run the **unpaired MDE is the
*smaller*** one, because ψ = 0.616 is high:
`unpaired/paired = sqrt((p₁(1−p₁)+p₂(1−p₂))/ψ) = 0.85×`.
So the phrase "the paired MDE is the conservative one" is **false here**; the paired MDE (0.1595) is the
*larger*. `REPORT.md:69` verbatim: *"the ratio is **0.85x**, i.e. the paired MDE (**0.1595**) is the *larger* of
the two, not the smaller. Quoting the paired figure is still the correct requirement; it is simply not the
lenient one here. The observed difference (-0.3316) is more than twice either MDE, so the conclusion does
not depend on which is quoted."* The conclusion (−0.3316 > 2× either MDE) is safe; the **justification**
"paired is conservative" must not be reused.

## 4. The two candidate primary baselines

```bash
cd "the read-only target repository/docs/research/EXP#12-evidence" && python3 -c "
import json; d=json.load(open('analysis.json')); print(json.dumps(d['publishedBaselines'], indent=1))"
```

Verbatim output:

```json
{
 "decider-4b (published, D-067), instrument190": 0.6684,
 "imajev-4b (published), H-A corpus stratum": 0.645,
 "laya-typed-decisions (published), instrument190": 0.374,
 "decider-4b EXP#11 reproduction, instrument190": 0.6789
}
```

- **0.6789 (same-run reproduction)** full precision:
  `analysis.json .baselinesRescored["decider-4b-exp11-reproduction"].strata.instrument190.accuracy = 0.6789473684210526`,
  `n=190`, `reproducesAt3dp=true`, `absoluteDifference=4.7368421052684795e-05`, source
  `docs/research/EXP#11-evidence/decider-rows.jsonl`.
- **0.6684 (historical, D-067)**: `REPORT.md:104` verbatim —
  `decider-4b 0.6684 (D-067): re-scored n/a vs published 0.6684 on stratum instrument190 → reproduces at 3 d.p. = **None**`
  and `REPORT.md:189` verbatim: *"**`decider-4b 0.6684` (D-067) cannot be re-scored.** No per-case rows for
  that specific measurement are in the tree, so F5 cannot check it directly; the same-run reproduction of the
  same instrument (0.6789) is what stands in, and that re-scores exactly."*
  ⇒ **The 0.6684 has no per-case rows in the evidence tree.** The 0.6789 is fully re-derivable from stored rows.
- The **pre-registered falsifier F1 was written against 0.6684** (`EXP#12-typed-channel-comparison.md:95`,
  `REPORT.md:85`), while the **paired statistics are computed against 0.6789** (`analysis.json .comparisons[*].b`
  = `"decider-4b (EXP#11 reproduction, F0 frame)"`). The two are not the same arm.
- Title arithmetic: `0.6684 − 0.3474 = 0.3210` → "loses by **0.32**" uses the **historical** figure;
  `0.6789 − 0.3474 = 0.3316` → the paired **Δ = −0.3316** uses the **same-run** figure.

## 5. Defect / correction chain (SetFit-MPNet)

**Record, not a reader-facing path (UFIXFMT3, 2026-10-16).** This probe lives in the read-only target
repository and is **not** shipped; what a reader can open is `results/REPORT.md` §D1–D3, which prints the
chain rows verbatim at `:253–256`. The internal command that produced the block below was:

```bash
cd "the read-only target repository/docs/research/EXP#12-evidence" && python3 -c "
import json; print(json.dumps(json.load(open('DEFECT-EVIDENCE.json'))['setfitIntermediates'], indent=1))"
```

Verbatim output:

```json
{
 "what": "the SetFit head's decision rule, intermediate variants on the sealed 190, same weights",
 "source": "console transcript from the reference run; superseded by results/defect-probe.json, which reproduces the mechanism on the H-B development split from the retained model",
 "variants": [
  {"ruling": "predict_proba clipped to [1e-6, 1-1e-6], probe also unfixed", "accuracy": 0.3158, "ece": 0.1665, "orderPermutationFlips": 101},
  {"ruling": "predict_proba clipped to [1e-6, 1-1e-6], probe fixed", "accuracy": 0.3158, "ece": 0.1665, "orderPermutationFlips": 46},
  {"ruling": "predict_proba clipped at the denormal edge, old dev fit", "accuracy": 0.2947, "ece": 0.2738, "orderPermutationFlips": 36}
 ]
}
```

**`REPORT.md` rows** (lines 253–256) — verbatim:

```
| `setfit-mpnet` | accuracy | ECE | order flips |
| first attempt: clip `[1e-6, 1-1e-6]` | 0.3158 | 0.1665 | 46 / 190 *(101/190 before the probe itself was fixed — D1)* |
| second attempt: denormal-edge clip, old dev fit | 0.2947 | 0.2738 | 36 / 190 |
| **the fix: `decision_function`, refitted on dev** | **0.2632** | **0.1536** | **0 / 190** |
```

### ✗ DISAGREES with the universal quantifier in §A3 / M12

`PAPER_CANDIDATES.md:269` and `LEARNINGS.md:281` say **"Every correction moved the affected arm DOWN
(0.3158 → 0.2947 → 0.2632)."** True for **SetFit only**. The (unshipped) `DEFECT-EVIDENCE.json` probe shows — and the shipped `results/REPORT.md` §D1–D3 records —
`modernbert-base` moved **UP** from `0.342105` (pass 1, buggy order probe) to `0.347368` (final) when the
order-probe bug was fixed:

**Internal record (UFIXFMT3, 2026-10-16)** — same caveat as above: the probe is not shipped. The shipped
`results/REPORT.md` §D1–D3 carries this finding. The command that produced the block below was:

```bash
cd "the read-only target repository/docs/research/EXP#12-evidence" && python3 -c "
import json; d=json.load(open('DEFECT-EVIDENCE.json'))['passes']
print('pass1  modernbert acc', d['pass1_buggy_order_probe']['arms']['modernbert-base']['accuracy'])
print('final  modernbert acc', d['final']['arms']['modernbert-base']['accuracy'])"
```
```
pass1  modernbert acc 0.342105
final  modernbert acc 0.347368
```
The safe statement is **"every correction moved the *SetFit* arm down"**, or "all three defects flattered
the candidate" (the *defects* all favoured the candidate; the *fixes* did not all lower every arm).

## 6. F4 n-gram leak lint

```bash
cd "the read-only target repository/docs/research/EXP#12-evidence" && python3 -c "
import json; d=json.load(open('lint-report.json'))
tf=d['trainVsFixture']
print('fires', d['fires'], '| rule', tf['rule'], '| ngramSize', tf['ngramSize'], '| threshold', tf['threshold'])
print('left', tf['left'], tf['leftRows'], 'right', tf['right'], tf['rightRows'])
print('forward pairs', tf['forward']['pairsCompared'], 'flagged', len(tf['forward']['flagged']))
print('reverse pairs', tf['reverse']['pairsCompared'], 'flagged', len(tf['reverse']['flagged']))
print('silent', tf['silent'], '| removedCount', tf['removedCount'])
for p in d['demo']['probes']:
    print(' seeded', p['name'], '| total', p['sharedGramCount'], '| maxPair', p['maxPairSharedGramCount'], '| fired', p['fired'])
print(' novelRowSharedGramCount', d['demo']['novelSharedGramCount'])"
```

Verbatim output:

```
fires False | rule drop when a row shares >= 2 distinct 8-grams with any single row of the other side, applied in both directions | ngramSize 8 | threshold 2
left train800(600rev+200H-A) 800 right sealed190 190
forward pairs 152000 flagged 0
reverse pairs 152000 flagged 0
silent True | removedCount 0
 seeded seeded.state-only-copy | total 13 | maxPair 13 | fired True
 seeded seeded.boilerplate-only-copy | total 220 | maxPair 44 | fired True
 seeded seeded.whole-row-copy | total 233 | maxPair 57 | fired True
 novelRowSharedGramCount 0
```

**Reading of "13/44/57"** (§A3:268, `LEARNINGS.md:283`, commit `995fbd1`): 13 = the state-only copy's
shared 8-grams (its total *is* its max-pair count); **44** and **57** are the *max-pair* counts for the
boilerplate-only and whole-row copies (their **totals are 220 and 233**). Quote them as **per-pair maxima**,
or the three numbers are not like-for-like. All three fired; `fires:false` for the real comparison is the
non-firing that keeps the run alive. F4 not firing = run NOT void (`analysis.json .falsifiers.F4.fires=false`).

`REPORT.md:97` verbatim: *"the run is not void — 0 rows removed over 152000 pairs, both directions, and the
lint was shown to fire on three seeded copies and stay silent on a novel row"*.

## 7. Fixture reliability — second labeller

```bash
cd "experiments/second-labeller-190" && python3 -c "
import json; m=json.load(open('metrics.json')); r=json.load(open('RUN.json'))
print('cases', m['cases'], '| options_total', m['options_total'])
print('routeB', m['routeB_primary'])
print('routeA kappa', m['routeA']['kappa'], 'agreement', m['routeA']['agreement'])
print('disagreements', m['disagreements_count_routeB'], '| where routeA backs record', m['disagreements_where_routeA_backs_record'])
print('instrument sha before/after', r['instrument_sha256_before'], r['instrument_sha256_after'])
print('identical to target', r['sandbox_copy_identical_to_target'])"
```

Verbatim output:

```
cases 190 | options_total 721
routeB {'file': 'labelsB.json', 'labeller': 'routeB-blind-model', 'ids_missing': [], 'ids_extra': [], 'labels_out_of_range': [], 'labelable': 190, 'agreement': 0.9052631578947369, 'po': 0.9052631578947369, 'pe': 0.03958448753462604, 'kappa': 0.9013584840356494, 'exact_index_matches': 172, 'n_disagreements': 18, 'AB_mutual_agreement': 0.3526315789473684, 'disagreements_where_routeA_backs_record': 5}
routeA kappa 0.32520740993294694 agreement 0.34210526315789475
disagreements 18 | where routeA backs record 5
fixture sha before/after 076164ac53c2c1aac130953345c481f88b51f4d6fb93d465c7430308a99b4796 076164ac53c2c1aac130953345c481f88b51f4d6fb93d465c7430308a99b4796
identical to target True
```

Note 2026-10-16: the block above is the pre-neutralisation output, kept verbatim as the dated record. After
the release tree's identifiers were neutralised, the same script prints AB_mutual_agreement
**0.3684210526315789**, disagreements_where_routeA_backs_record **4**, and routeA kappa **0.3248813212427869**
(agreement 0.34210526315789475 unchanged); the current values are in `CLAIMS.md:108-110` and `MANUSCRIPT.md`. The
same 2026-10-16 label correction (UFIXPKG4) renamed `second-labeller/RUN.json`'s `fixture_sha256_before` /
`fixture_sha256_after` / `sandbox_sha256` keys to `instrument_sha256_before` / `instrument_sha256_after` /
`instrument_sandbox_sha256` (they digest the as-audited instrument, not a shipped fixture); the recorded output
line above retains its pre-correction label and its values are unchanged by the rename.

**The limitation, verbatim from `EVIDENCE.md:14–23`** (this wording is the *only* defensible way to cite it):

```
## ⚠ LIMITATION — read this before any number below
> **UNVERIFIED as inter-annotator agreement.** The second pass here is a **model**, not an
> independent human annotator. Agreement between a model and the fixture's hand-authored labels
> is **not** inter-annotator agreement in the sense a reviewer means, and κ below **must not** be
> ... for "a second independent labeller or corpus for the 190-case fixture". A model pass cannot
> substitute for a second human. See §8.
```
`EVIDENCE.md:309` verbatim: *"**It is not IAA.** One pass is a model. κ = 0.901 is *not* two-annotator
agreement and must not..."*. A second distinct-model pass (`mimo-v2.6-flash`) was launched but **returned no
file**, so `metrics.json` contains **exactly one** model pass (`EVIDENCE.md:153–155`).
Fixture sha256 is **unchanged** before/after, and the sandbox copy is byte-identical to the target — the
second labeller did not modify the fixture.

## 8. Falsifier / resolution / H4 state

```bash
cd "the read-only target repository/docs/research/EXP#12-evidence" && python3 -c "
import json; d=json.load(open('analysis.json'))
print('resolution', json.dumps(d['resolution'], indent=1))
for k,v in d['falsifiers'].items(): print(k, 'fires=', v.get('fires'))
print('h4', json.dumps(d['h4'], indent=1))"
```

Verbatim output (abridged to the verdict fields; full records in `analysis.json`):

```
resolution {'state': 'CLOSE', 'fires': ['F1', 'F3'], 'note': '... F1 fired, so the method is CLOSE ... F3 also fired, which kills H2 independently of H1. F2/F4/F5/F6 did not fire, so the run is neither void nor an instrument failure.'}
F1 fires= True
F2 fires= False
F3 fires= True
F4 fires= False
F5 fires= False
F6 fires= False
h4 {'observed': 'monotone', 'verdict': 'H4 is not supported: accuracy moves monotonically with parameter count across these three heads', 'parameterCounts': {'modernbert-base': 149015041, 'deberta-v3-base': 183832321, 'setfit-mpnet': 109489537, 'majority-class': 0, 'shuffled-label': 149015041}, 'accuracies': {'setfit-mpnet': 0.2631578947368421, 'modernbert-base': 0.3473684210526316, 'deberta-v3-base': 0.3473684210526316}}
```

`REPORT.md:156–159` headline, verbatim: *"**The best fine-tuned encoder head scores 0.3474 against the 4B's
0.6684** — barely above the chance floor ... same-run reproduction (0.6789): **b=27, c=90, ψ=0.616, Δ=−0.3316,
exact p=4.167e−09, paired MDE 0.1595**. The harm is **twice the MDE** — this is not a near miss."*

## 9. Latency — see `GAPS.md` §2. Raw numbers for the record

```bash
cd "the read-only target repository/docs/research/EXP#12-evidence" && python3 -c "
import json; a=json.load(open('analysis.json'))
print('decider-4b instrument190 latencyMsMean', a['baselinesRescored']['decider-4b-exp11-reproduction']['strata']['instrument190']['latencyMsMean'])
print('decider-4b H-A', a['baselinesRescored']['decider-4b-exp11-reproduction']['strata']['H-A']['latencyMsMean'], '| H-B', a['baselinesRescored']['decider-4b-exp11-reproduction']['strata']['H-B']['latencyMsMean'])
print('imajev instrument190', a['baselinesRescored']['imajev-4b-exp11']['strata']['instrument190']['latencyMsMean'])
print('laya instrument190', a['baselinesRescored']['laya-typed-decisions']['strata']['instrument190']['latencyMsMean'])"
```
```
decider-4b instrument190 latencyMsMean 53.06473684210526
decider-4b H-A 106.9165 | H-B 72.8455
imajev instrument190 453.02789473684214
laya instrument190 639.1479427289022
```

Heads (local GB10): 12.37 / 14.16 / 11.96 / 12.46 / 0.003 ms — method string (identical in all five arms):
`"wall clock around one full per-decision call (all option texts tokenised, one forward batch, softmax); warmed with 20 cases, then 3 full passes over the 190; GPU synchronised before each stop"`, `n=570`.
The **same decider** reports 53.06 ms on instrument190 but 106.92 ms (H-A) and 72.85 ms (H-B) — a **2×**
spread within the same model family across strata. F6's threshold is the pre-registered constant
**0.075 s/decision** from `DECIDER_TIER §2`, not co-measured on this host.

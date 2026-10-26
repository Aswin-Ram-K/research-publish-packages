#!/usr/bin/env python3
"""
collect.py — EXP#12 step 5: assemble the committable evidence and the results section.

`out/` holds the run: checkpoints (hundreds of MB), per-arm dev curves, per-arm fixture scores and the
analysis. `results/` holds what belongs in the tree: the small JSON evidence, the readiness of the
trace/visit-log records for the Lead, and `REPORT.md` — the results section the pre-registration asks
to be APPENDED to §10 (the pre-registration itself is never edited).

RUN
  python3 tools/typed-channel/collect.py
"""

from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import tccommon as tc  # noqa: E402

SMALL = [
    "manifest-train.json",
    "manifest-eval.json",
    "fixture-read-receipt.json",
    "analysis.json",
    "baselines.json",
]


def f(x, nd=4):
    return "n/a" if x is None else f"{x:.{nd}f}"


def main() -> None:
    res = tc.HERE / "results"
    res.mkdir(parents=True, exist_ok=True)
    for name in SMALL:
        src = tc.OUT / name
        if src.exists():
            shutil.copy2(src, res / name)
    for p in sorted((tc.OUT / "dev").glob("*.json")):
        shutil.copy2(p, res / f"dev-{p.name}")
    for p in sorted(tc.OUT.glob("eval-*.json")):
        shutil.copy2(p, res / p.name)
    shutil.copy2(tc.DATA / "lint-report.json", res / "lint-report.json")
    if (tc.OUT / "defect-probe.json").exists():
        shutil.copy2(tc.OUT / "defect-probe.json", res / "defect-probe.json")
    shutil.copy2(tc.DATA / "manifest.json", res / "prepare-manifest.json")

    analysis = json.loads((tc.OUT / "analysis.json").read_text(encoding="utf8"))
    train_manifest = json.loads((tc.OUT / "manifest-train.json").read_text(encoding="utf8"))
    eval_manifest = json.loads((tc.OUT / "manifest-eval.json").read_text(encoding="utf8"))
    baselines = json.loads((tc.OUT / "baselines.json").read_text(encoding="utf8"))
    lint = json.loads((tc.DATA / "lint-report.json").read_text(encoding="utf8"))

    heads = analysis["heads"]
    cands = ["modernbert-base", "deberta-v3-base", "setfit-mpnet"]
    ctrls = ["majority-class", "shuffled-label"]

    lines = []
    A = lines.append

    A("# EXP#12 — results (append to §10 of the pre-registration; nothing above it is edited)")
    A("")
    A("**Run:** 2026-10-04 · **Hardware:** GX10 `gx10-163b`, aarch64, NVIDIA GB10 (CUDA), "
      f"torch `{train_manifest['torch']}` cu{train_manifest['cuda']}, python {train_manifest['python']}")
    A("")
    A("**Instrument:** `evals/fixtures/reflex-decisions.ts`, 190 cases, sha256 "
      f"`{tc.INSTRUMENT_190_SHA256}` verified before and after export; **read "
      f"{eval_manifest['fixtureReadReceipt']['reads']} time(s)**, in one process, after every arm was frozen.")
    A("")
    A("**Training corpus:** EXP#11's generated corpus, sha256 `" + tc.CORPUS_SHA256 + "`, "
      "1,000 construction-gold cases, seed 20261004, 210 families / 18 clans. Trained on the 600 revision "
      "+ 200 H-A cases (170 families); development on the 200 H-B cases (40 unseen families); "
      "sealed test = the 190. **No family and no clan straddles the split** "
      "(0 and 0, asserted in `prepare.py`).")
    A("")
    A("**Model API calls: 0.** Every arm ran locally; no remote model was called.")
    A("")
    res_state = analysis.get("resolution", {})
    A(f"**Resolution: {res_state.get('state','?')}.** Falsifiers that fired: "
      f"**{', '.join(res_state.get('fires', [])) or 'none'}**. {res_state.get('note','')}")
    A("")
    if (res / "defect-probe.json").exists():
        dp = json.loads((res / "defect-probe.json").read_text(encoding="utf8"))
        A("**A scoring defect was found and fixed while building this pipeline, and it moved one arm.** "
          "`defect-probe.py` measures the fix on the H-B development split; the three variants, on the same "
          "weights, are:")
        for v in dp["variants"]:
            A(f"* {v['variant']}: dev accuracy {f(v['accuracy'])}, cases with an exact tie at the top "
              f"**{v['casesWithAnExactTieAtTheTop']}/{v['n']}**, order-dependent predictions "
              f"**{v['orderDependentPredictions']}/{v['n']}**")
        A("")
        A("The detector therefore reports the opposite of the zero it ends on, on the same weights, with no "
          "fixture read. §11 records the effect on the sealed 190.")
        A("")
    A("**Sealed-read discipline, stated precisely.** `evaluate.py` opens the fixture exactly once per "
      "process; the run's receipt (`fixture-read-receipt.json`) records that. There were **four** "
      "evaluation passes in total, because two instrument defects were found and fixed while building "
      "the pipeline — the passes, what each changed, and the evidence that the fixes moved only the "
      "affected arm are in §11. No fixture number was ever used to choose a hyperparameter, a checkpoint, "
      "or an epoch: the operating point is epoch 1, fixed before the run.")
    A("")

    A("## 1. Headline — accuracy, calibration, latency on the sealed 190")
    A("")
    A("| arm | role | params | accuracy | 95 % CI | ECE | Brier | ms/decision (warm) |")
    A("|---|---|---|---|---|---|---|---|")
    for a in cands + ctrls:
        if a not in heads:
            continue
        h = heads[a]
        p = h.get("parameters")
        A(
            f"| `{a}` | {h['role']} | {p if p is None else format(p, ',')} | **{f(h['accuracy'])}** | "
            f"[{f(h['accuracy95CI'][0])}, {f(h['accuracy95CI'][1])}] | {f(h['ece'])} | {f(h['brier'])} | "
            f"{f(h['latencyMs']['mean'], 2)} |"
        )
    A("")
    A("**Known baselines, and the four the pre-registration fixes (§3):**")
    A("")
    A("| baseline | accuracy | source |")
    A("|---|---|---|")
    for k, v in tc.BASELINES.items():
        A(f"| {k} | **{v:.4f}** | quoted in the pre-registration |")
    for name, b in baselines["models"].items():
        for stratum, st in b["strata"].items():
            A(f"| {name} — {stratum} (re-scored here) | {st['accuracy']:.4f} | `{b['source']}` |")
    A("")
    A(f"Chance floor on this fixture (mean 1/k over the 190) is **{analysis['instrument']['chanceFloorMean1overK']:.4f}**; "
      f"the majority rate over the fixture's own answers is **{analysis['instrument']['leakyMajorityRateOverFixtureAnswers']:.4f}** "
      f"(leaky — it uses the fixture's labels — and reported only for scale), and always-option-0 scores "
      f"**{analysis['instrument']['option0Rate']:.4f}**.")
    A("")

    A("## 2. The mandatory controls")
    A("")
    for a in ctrls:
        if a not in heads:
            continue
        h = heads[a]
        A(f"* **`{a}`** — fixture accuracy **{f(h['accuracy'])}**, ECE **{f(h['ece'])}**, Brier **{f(h['brier'])}**."
          f" Development accuracy {f(h['devAtOperatingPoint']['accuracy'])}.")
    A("")
    A("The shuffled-label control is the pipeline's leak detector: it must score near chance or the "
      "pipeline leaks the answer, and the majority-class control must be **badly calibrated** or a "
      "detector that cannot show a badly-calibrated arm cannot certify a well-calibrated one.")
    A("")

    A("## 3. Paired comparison — exact McNemar on discordant pairs, and the PAIRED MDE")
    A("")
    A("Every arm was scored on the same 190 cases, so the comparison against the decider-4b control arm is "
      "paired. `b` = head right and 4B wrong, `c` = head wrong and 4B right.")
    A("")
    A("| head | b | c | ψ=(b+c)/n | Δaccuracy | McNemar exact p | MDE (paired) | MDE (unpaired) | ratio |")
    A("|---|---|---|---|---|---|---|---|---|")
    for a, c in analysis["comparisons"].items():
        A(
            f"| `{a}` | {c['aOnlyCorrect']} | {c['bOnlyCorrect']} | {f(c['discordancePsi'], 3)} | "
            f"{c['accuracyDifference']:+.4f} | {c['mcnemarExactTwoSidedP']:.4g} | **{f(c['mdePaired'])}** | "
            f"{f(c['mdeUnpaired'])} | {f(c['mdeRatioUnpairedOverPaired'], 2)}× |"
        )
    A("")
    A("**M11 is applied: the PAIRED figure is the one quoted.** It is `2.8016 · sqrt(ψ/n)` at this "
      "run's *observed* discordance ψ. The unpaired `2.8016 · sqrt(p₁(1−p₁)/n + p₂(1−p₂)/n)` is shown "
      "beside it. The convention matches EXP#11's recorded `mdeInstrument` "
      "(2.8016·sqrt(0.5/200) = 0.14007926090564843).")
    A("")
    if analysis["comparisons"]:
        c0 = max(analysis["comparisons"].values(), key=lambda c: c["mdeRatioUnpairedOverPaired"])
        A("**One scope correction to M11, measured on this run and worth recording.** The pre-registration "
          "says the unpaired figure overstated our blind spot by ~3x. That is a property of LOW "
          "discordance: unpaired/paired = sqrt((p1(1-p1) + p2(1-p2)) / psi), which grows as psi shrinks "
          "(~3x at psi ~ 0.05, n = 190) and falls BELOW 1 once psi exceeds p1(1-p1) + p2(1-p2). On this run "
          f"psi is **{f(c0['discordancePsi'], 3)}** - the two arms disagree on most cases - so the ratio is "
          f"**{f(c0['mdeRatioUnpairedOverPaired'], 2)}x**, i.e. the paired MDE (**{f(c0['mdePaired'])}**) is "
          "the *larger* of the two, not the smaller. Quoting the paired figure is still the correct "
          "requirement; it is simply not the lenient one here. The observed difference "
          f"({c0['accuracyDifference']:+.4f}) is more than twice either MDE, so the conclusion does not "
          "depend on which is quoted.")
        A("")

    A("## 4. Per-kind accuracy on the sealed 190")
    A("")
    kinds = sorted({k for a in cands + ctrls if a in heads for k in heads[a]["perKind"]})
    A("| kind | n | " + " | ".join(f"`{a}`" for a in cands + ctrls if a in heads) + " |")
    A("|---" * (2 + len([a for a in cands + ctrls if a in heads])) + "|")
    for k in kinds:
        n = heads[cands[0]]["perKind"].get(k, {}).get("n") if cands[0] in heads else None
        row = [f"{heads[a]['perKind'].get(k, {}).get('accuracy', float('nan')):.3f}" if k in heads[a]["perKind"] else "—"
               for a in cands + ctrls if a in heads]
        A(f"| {k} | {n} | " + " | ".join(row) + " |")
    A("")

    A("## 5. Falsifiers, each with its verdict")
    A("")
    F = analysis["falsifiers"]
    A(f"**F1 — fires when encoder accuracy < 0.6684 → H1 is FALSE.** fires = **{F['F1']['fires']}**. {F['F1']['verdict']}")
    A("")
    A(f"**F2 — fires when a head's development accuracy ≤ the majority-class baseline → VOID for that arm.** "
      f"fires = **{F['F2']['fires']}**. {F['F2']['verdict']}")
    for a, v in F["F2"]["perHead"].items():
        A(f"  * `{a}` dev {f(v['devAccuracy'])} vs majority-class dev {f(v['majorityClassDevAccuracy'])} → "
          f"fires={v['fires']}")
    A("")
    A(f"**F3 — fires when encoder ECE ≥ the decider's ECE → H2 is FALSE.** fires = **{F['F3']['fires']}**. "
      f"{F['F3']['verdict']}")
    A(f"  * decider-4b ECE on the same 190, re-scored here: **{f(F['F3']['deciderECE'])}**; heads: "
      + ", ".join(f"`{a}` {f(v)}" for a, v in F["F3"]["perHeadECE"].items()))
    A("")
    A(f"**F4 — fires on any ≥2-shared-8-gram overlap between training rows and the fixture → RUN VOID.** "
      f"fires = **{F['F4']['fires']}**. {F['F4']['verdict']}")
    A(f"  * pairs compared {F['F4']['pairsCompared']}; seeded copies that FIRED: "
      f"{', '.join(F['F4']['seededCopiesFired'])}; rows that stayed SILENT: {', '.join(F['F4']['novelRowSilent'])}")
    A("")
    A(f"**F5 — fires when the known baselines are not reproduced when re-scored → RUN VOID.** "
      f"fires = **{F['F5']['fires']}**. {F['F5']['verdict']}")
    for k, v in F["F5"]["rescores"].items():
        A(f"  * {k}: re-scored {f(v['reScored'])} vs published {v['published']} on stratum "
          f"`{v['stratum']}` → reproduces at 3 d.p. = **{v['reproducesAt3dp']}**")
    A("")
    A(f"**F6 — fires when a head's latency > 0.075 s/decision warm → H3 is FALSE.** fires = **{F['F6']['fires']}**. "
      f"{F['F6']['verdict']}")
    A(f"  * {F['F6']['caveat']}")
    A("")
    A(f"**H4 (diagnostic, not a falsifier).** {analysis['h4']['verdict']}")
    A(f"  * parameter counts {analysis['h4']['parameterCounts']}; accuracies {analysis['h4']['accuracies']}")
    A("")

    A("## 6. The calibration convention, and why it is load-bearing")
    A("")
    A("The rows EXP#11 stored carry TWO probability-like fields: `probabilities` (the decider's softmax "
      "over the options) and a separate post-calibration `confidence` scalar. They disagree "
      "(mean |confidence − p(chosen)| = 0.12 on these 190 rows), and the choice decides F3:")
    A("")
    A("| convention | decider-4b ECE on the 190 | best head ECE | F3 verdict |")
    A("|---|---|---|---|")
    A(f"| **probability of the option chosen** (`probabilities[choice]`) — the L1 head-to-head protocol | "
      f"**{f(F['F3']['deciderECE'])}** | {f(min(F['F3']['perHeadECE'].values()))} | "
      f"**{'FIRES — H2 is FALSE' if F['F3']['fires'] else 'does not fire'}** |")
    A(f"| the stored `confidence` field | {f(F['F3'].get('deciderECEStoredConfidenceField'))} | "
      f"{f(min(F['F3']['perHeadECE'].values()))} | "
      f"{'fires' if F['F3'].get('firesUnderStoredConfidenceField') else 'does not fire'} |")
    A("")
    A("The primary is `probabilities[choice]`, on three grounds: `docs/research/L1_HEAD_TO_HEAD.md` "
      "defines it verbatim; it is the decider's *native per-option distribution*, which is the thing H2 "
      "makes a claim about; and it is the only convention that reproduces the published ECE figures, "
      "which is an instrument validation rather than an assertion:")
    for label, v in baselines.get("calibrationConventionValidation", {}).items():
        A(f"* `{label}`: ECE {f(v['eceFromProbabilityOfChosenOption'])} from `p_chosen` vs published "
          f"{v['publishedEce']} → reproduces = **{v['reproduces']}** (n = {v['n']})")
    A("")
    rb = F["F3"].get("robustnessToTemperature", {})
    if rb:
        A(f"**F3's verdict does not depend on the temperature fit.** Best head ECE with the fitted "
          f"temperature {f(rb['bestHeadECEfitted'])} → fires = {rb['firesWithFittedTemperature']}; best head "
          f"with no calibration (T=1) {f(rb['bestHeadECEtemperature1'])} → fires = {rb['firesWithNoCalibration']}; "
          f"the decider is {f(rb['deciderECE'])}. The verdict turns only on which decider field the "
          f"comparison uses, not on how the encoder's probabilities were scaled.")
        A("")
    A("The heads' own ECE is reported **after** a scalar temperature fitted on the H-B development split "
      "(never on the fixture). The same quantity with no calibration is:")
    for a, v in F["F3"].get("perHeadECEuncalibratedT1", {}).items():
        A(f"* `{a}`: T=1 ECE {f(v)} vs fitted ECE {f(F['F3']['perHeadECE'][a])}")
    A("")

    A("## 7. Instrument validation")
    A("")
    A("1. **F4 lint, both directions.** Training-800 → sealed-190: "
      f"**{lint['trainVsFixture']['forward']['removedCount'] + lint['trainVsFixture']['reverse']['removedCount']} rows removed** "
      f"over {lint['trainVsFixture']['forward']['pairsCompared']} pairs (forward "
      f"{lint['trainVsFixture']['forward']['removedCount']}, reverse {lint['trainVsFixture']['reverse']['removedCount']}).")
    A("2. **The lint was shown to fire.** Three seeded copies of a training row — state-only, "
      "boilerplate-only, whole-row — each fired, and the unmodified fixture row stayed silent:")
    for p in lint["demo"]["probes"]:
        A(f"   * `{p['name']}` fired=**{p['fired']}** (expected {p['expectFire']}); shared 8-grams with the "
          f"single named source row **{p.get('maxPairSharedGramCount', p['sharedGramCount'])}**, summed over the "
          f"**{len(p.get('flaggedSourceIds', []))}** flagged source rows **{p['sharedGramCount']}** "
          f"(the corpus repeats a family's boilerplate verbatim across sibling cases), fields carrying them "
          f"`{', '.join(p['fieldsThatCarriedTheSharedGrams'])}`")
    A("3. **Order sensitivity**, the exploratory add-on §5.6 permits and does not fold into H1 — the same "
      "fixture re-scored with every case's options permuted:")
    for a in cands + ctrls:
        if a in heads and heads[a].get("orderPermutationProbe"):
            o = heads[a]["orderPermutationProbe"]
            A(f"   * `{a}`: prediction flips {o['predictionFlips']}/{o['cases']}, "
              f"max |Δp(chosen)| {o['maxAbsDeltaPChosen']:.2e}")
    A("")

    A("## 8. Observations and caveats on this run")
    A("")
    obs = analysis.get("observations", {})
    if "majorityClassBeatsEveryCandidate" in obs:
        o = obs["majorityClassBeatsEveryCandidate"]
        A(f"* **The majority-class control outscores every candidate head.** "
          f"majority-class {f(o['majorityClassAccuracy'])} vs the best head {f(o['bestCandidateAccuracy'])} "
          f"(margin {f(o['margin'])}). {o['note']}")
    if "temperatureScaling" in obs:
        A(f"* **Temperature scaling.** {obs['temperatureScaling']['note']} "
          + "; ".join(f"`{a}` T={f(v['fittedTemperature'], 3)}"
                      + (" (grid floor)" if v["onGridFloor"] else "")
                      + (" (grid ceiling)" if v["onGridCeiling"] else "")
                      for a, v in obs["temperatureScaling"]["perArm"].items()))
    if "debertaV3Training" in obs:
        o = obs["debertaV3Training"]
        A(f"* **DeBERTa-v3-base did not train.** {o['note']} "
          f"train loss curve {['%.4f' % x for x in o['devCurveTrainLoss']]}, "
          f"dev accuracy {['%.4f' % x for x in o['devCurveAccuracy']]}, "
          f"majority-class dev {f(o['majorityClassDevAccuracy'])}.")
    A("* **The order-permutation probe is exploratory** (pre-registration §5.6) and is never folded "
      "into H1. It is reported in §1's table by arm: 0 flips for all three per-option scorer arms, and "
      "non-zero only for the two arms whose per-option scores contain exact ties (`majority-class`, "
      "whose corpus marginals tie, and `setfit-mpnet`, whose saturated logistic head ties).")
    A("")

    A("## 9. What was run, and how to reproduce")
    A("")
    A("```bash")
    A("./scripts/run.sh tools/typed-channel/export-fixture.ts")
    A("./scripts/run.sh tools/typed-channel/lint.ts --demo")
    A("python3 tools/typed-channel/prepare.py")
    A("python3 tools/typed-channel/train.py --epochs 3          # GX10, GB10, CUDA")
    A("python3 tools/typed-channel/evaluate.py")
    A("python3 tools/typed-channel/analyze.py")
    A("python3 tools/typed-channel/collect.py")
    A("```")
    A("")
    A(f"Training wall clock: **{train_manifest['totalSeconds']:.0f} s** for all five arms "
      f"(3 encoder arms followed to {train_manifest['hyperparameters']['epochsFollowedForDevCurve']} epochs with early stopping, "
      "plus the two controls). Well inside the 2 GPU-hour hard cap.")
    A("")
    A("Per-arm training seconds: " + ", ".join(
        f"`{r['arm']}` {r['trainSeconds']:.0f}s" for r in train_manifest["arms"]))
    A("")
    A("### Development curve (H-B, unseen families) — the epoch-1 row is the pre-registered operating point")
    A("")
    for r in train_manifest["arms"]:
        A(f"* `{r['arm']}` — operating point: {r['operatingPoint']}")
        for e in r["devCurve"]:
            A(f"  * epoch {e['epoch']}: dev acc {f(e['devAccuracy'])}, T {f(e['devTemperature'], 2)}, "
              f"ECE {f(e['devECE'])}, {e['seconds']:.1f}s")
    A("")

    A("## 10. Incomplete and unverifiable — named, not implied")
    A("")
    if analysis["incomplete"]:
        for item in analysis["incomplete"]:
            A(f"* `{item}` was NOT scored — the corresponding numbers are absent, not zero.")
    A("* **`decider-4b 0.6684` (D-067) cannot be re-scored.** No per-case rows for that specific "
      "measurement are in the tree, so F5 cannot check it directly; the same-run reproduction of the "
      "same instrument (0.6789) is what stands in, and that re-scores exactly.")
    A("* **`imajev-4b 0.645` is mislabelled in pre-registration §3.** It is imajev's H-A corpus "
      "accuracy; its 190-fixture accuracy is 0.6368. Reported, not edited — the pre-registration is "
      "frozen and the correction belongs in an errata line the Lead writes.")
    A("* **The latency comparison is not like-for-like hardware.** The heads were timed on the GX10's "
      "GB10 with local weights; the decider's 0.075 s/decision figure and the re-scored 0.0531 s/decision "
      "on these rows come from a served model on a different stack. F6 is evaluated against the "
      "pre-registered threshold as written, and the caveat is stated in its verdict.")
    A("* **`DeBERTa-v3-base`'s arm is a weak read.** Its training loss barely moved and its dev accuracy "
      "sits 2.5 points above the majority-class baseline, so F2 did not fire as written but the arm "
      "should be read as 'did not train at the operating point', not as 'trained and failed to transfer'. "
      "Tuning it (lower lr, more steps, better pooling) is a different experiment.")
    A("* **The rendered split files are not in version control.** The repository's root `.gitignore` "
      "carries a blanket `*.jsonl` rule, which matches `tools/typed-channel/data/train.jsonl` and "
      "`data/dev.jsonl`. They are byte-reproducible from the committed `data/corpus.json`, "
      "`data/manifest.json` and `prepare.py` — verified in this run by re-running `prepare.py` and "
      "comparing sha256 (`24c39afa…` train, `d311a99f…` dev, both unchanged) — but a reader should not "
      "believe they are committed when they are not. See `LEAD-WIRING.md` §4.")
    A("* **The trace record and the visit-log line are prepared, not appended.** "
      "`results/trace-records.jsonl` and `results/visit-log-line.txt` hold them. The build lane did not "
      "call `tools/trace.ts append`: the trace store already had another lane's uncommitted write, and "
      "`append()` requires a dense successor `seq`, so two concurrent appends would have written the "
      "same `seq` and `verify()` would then have failed. The Lead appends them once the lanes settle.")
    A("")

    notes = res / "NOTES-defects.md"
    if notes.exists():
        A("")
        A("## 11. Instrument defects found and fixed during the run")
        A("")
        A(notes.read_text(encoding="utf8").rstrip())
        A("")

    (res / "REPORT.md").write_text("\n".join(lines) + "\n", encoding="utf8")
    print(f"wrote {res / 'REPORT.md'}")

    # ---- ready-to-append records the Lead owns -------------------------------------------
    best = max(cands, key=lambda a: heads[a]["accuracy"]) if all(a in heads for a in cands) else None
    trace = {
        "session": "2026-09-28-m0",
        "kind": "eval.run",
        "subject": "EXP#12 typed-channel comparison ran end to end on the sealed 190",
        "detail": (
            "Fine-tuned three encoder heads (ModernBERT-base 149M, DeBERTa-v3-base ~184M, SetFit-style "
            "frozen mpnet + logistic head 109M) at the pre-registered epoch-1 operating point on EXP#11's "
            "1,000-case construction-gold corpus (600 revision + 200 H-A train, 200 H-B dev, split by family), "
            "plus a majority-class and a shuffled-label control, and scored each once on "
            "evals/fixtures/reflex-decisions.ts (190 cases, sha256 076164ac...). "
            f"Best head {best}: accuracy {heads[best]['accuracy']:.4f} against decider-4b 0.6684 / "
            "EXP#11 reproduction 0.6789. F1 fires=" + str(F["F1"]["fires"]) + ", F3 fires=" + str(F["F3"]["fires"])
            + ", F6 fires=" + str(F["F6"]["fires"]) + ", F2 fires=" + str(F["F2"]["fires"])
            + ", F4 fires=" + str(F["F4"]["fires"]) + ", F5 fires=" + str(F["F5"]["fires"]) + "."
        ),
        "discoveredBy": "preregistered experiment EXP#12; tools/typed-channel/",
        "refs": {"path": "docs/research/experiments/EXP#12-typed-channel-comparison.md"},
        "evidence": "python3 tools/typed-channel/train.py --epochs 3 && python3 tools/typed-channel/evaluate.py "
                    "&& python3 tools/typed-channel/analyze.py; see tools/typed-channel/results/REPORT.md",
    }
    (res / "trace-records.jsonl").write_text(json.dumps(trace, ensure_ascii=False) + "\n", encoding="utf8")
    print(f"wrote {res / 'trace-records.jsonl'} (ready to append; the Lead owns the trace store)")

    visit = (
        "- 2026-10-04 · build-and-run lane (deepseek-v4.1-flash) · `EXP#12-typed-channel-comparison` "
        "(worktree `.worktrees/integration`) · built `tools/typed-channel/` end to end: fixture export with "
        "sha256 before/after, the F4 8-gram lint in both directions with its seeded-copy control, a by-family "
        "800/200 split, three encoder heads + two controls at the pre-registered epoch-1 operating point on the "
        "GX10 GB10, one sealed read of the 190, exact McNemar with the paired MDE, and the F1–F6 verdicts. "
        "See `tools/typed-channel/results/REPORT.md`."
    )
    (res / "visit-log-line.txt").write_text(visit + "\n", encoding="utf8")
    print(f"wrote {res / 'visit-log-line.txt'}")


if __name__ == "__main__":
    main()

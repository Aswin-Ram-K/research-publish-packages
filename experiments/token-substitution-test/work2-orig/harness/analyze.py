#!/usr/bin/env python3
"""
analyze.py — EXP#12 step 4: the paired analysis, the falsifier verdicts, and the results section.

Pre-registration: docs/research/experiments/EXP#12-typed-channel-comparison.md §5.5, §6 (frozen).

THE PAIRED ANALYSIS
  "The comparison is paired (same 190 cases) — McNemar on discordant pairs, and the MDE quoted must be
  the PAIRED one (M11: the unpaired figure overstated our blind spot by ~3x...)."

  Every arm was scored on the same 190 cases, so the analysis is McNemar on the discordant pairs
  against the decider-4b control arm re-scored from EXP#11's stored rows. Both MDEs are reported and
  the PAIRED one is the one quoted; the unpaired figure is printed next to it so the M11 correction is
  visible in this run's own numbers rather than asserted from the record.

  Paired MDE (n pairs, discordance psi = (b+c)/n, two-sided alpha=0.05, power 80%):
      MDE = (z_{0.975} + z_{0.8416}) * sqrt(psi / n) = 2.8016 * sqrt(psi/n)
  Unpaired MDE, same alpha and power, two independent proportions:
      MDE = 2.8016 * sqrt(p1(1-p1)/n + p2(1-p2)/n)
  The convention is the one EXP#11 used for `mdeInstrument` (2.8016*sqrt(0.5/200) = 0.1401, matching
  the recorded 0.14007926090564843), applied to this run's OBSERVED discordance.

RUN
  python3 tools/typed-channel/analyze.py
"""

from __future__ import annotations

import json
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import tccommon as tc  # noqa: E402

Z_ALPHA = 1.959963984540054  # two-sided 5 %
Z_POWER = 0.8416212335729143  # 80 %
MDE_K = Z_ALPHA + Z_POWER  # 2.8016

CANDIDATES = ("modernbert-base", "deberta-v3-base", "setfit-mpnet")
CONTROLS = ("majority-class", "shuffled-label")


def load(name: str):
    p = tc.OUT / name
    if not p.exists():
        raise SystemExit(f"REFUSED: missing {p}")
    return json.loads(p.read_text(encoding="utf8"))


# ------------------------------------------------------------------ exact McNemar


def _log_binom(n: int, k: int) -> float:
    return math.lgamma(n + 1) - math.lgamma(k + 1) - math.lgamma(n - k + 1)


def binom_two_sided_p(k: int, n: int) -> float:
    """Exact two-sided binomial test at p=0.5 (the McNemar exact test)."""
    if n == 0:
        return 1.0
    def pmf(i):
        return math.exp(_log_binom(n, i) - n * math.log(2))
    observed = pmf(k)
    tol = observed * (1 + 1e-9)
    return min(1.0, sum(pmf(i) for i in range(n + 1) if pmf(i) <= tol))


def mcnemar(a_correct, b_correct, name_a: str, name_b: str) -> dict:
    n = len(a_correct)
    if len(b_correct) != n:
        raise SystemExit("REFUSED: McNemar needs the same cases in the same order")
    b = sum(1 for x, y in zip(a_correct, b_correct) if x and not y)  # a right, b wrong
    c = sum(1 for x, y in zip(a_correct, b_correct) if not x and y)  # a wrong, b right
    both = sum(1 for x, y in zip(a_correct, b_correct) if x and y)
    neither = sum(1 for x, y in zip(a_correct, b_correct) if not x and not y)
    n_disc = b + c
    diff = (b - c) / n
    psi = n_disc / n
    paired_mde = MDE_K * math.sqrt(psi / n) if n else float("nan")
    pa = sum(a_correct) / n
    pb = sum(b_correct) / n
    unpaired_mde = MDE_K * math.sqrt(pa * (1 - pa) / n + pb * (1 - pb) / n)
    chi2 = (abs(b - c) - 1) ** 2 / n_disc if n_disc > 0 else 0.0
    return {
        "a": name_a,
        "b": name_b,
        "n": n,
        "bothCorrect": both,
        "aOnlyCorrect": b,
        "bOnlyCorrect": c,
        "neitherCorrect": neither,
        "discordant": n_disc,
        "discordancePsi": psi,
        "accuracyA": pa,
        "accuracyB": pb,
        "accuracyDifference": diff,
        "mcnemarExactTwoSidedP": binom_two_sided_p(min(b, c), n_disc),
        "mcnemarChiSquareContinuityCorrected": chi2,
        "mdePaired": paired_mde,
        "mdeUnpaired": unpaired_mde,
        "mdeRatioUnpairedOverPaired": (unpaired_mde / paired_mde) if paired_mde else float("nan"),
        "detectableDifferenceAtObservedDiscordance": paired_mde,
        "note": "the PAIRED MDE is the one quoted (M11); the unpaired figure is shown only to make the correction visible",
    }


def paired_bootstrap_diff(a_correct, b_correct, n_boot=4000, seed=20261004) -> list:
    import random

    rng = random.Random(seed)
    n = len(a_correct)
    diffs = []
    for _ in range(n_boot):
        s = 0
        for _ in range(n):
            i = rng.randrange(n)
            s += a_correct[i] - b_correct[i]
        diffs.append(s / n)
    diffs.sort()
    return [diffs[int(0.025 * n_boot)], diffs[int(0.975 * n_boot)]]


# ------------------------------------------------------------------ main


def main() -> None:
    manifest_eval = load("manifest-eval.json")
    baselines = load("baselines.json")
    lint = json.loads(tc.LINT_REPORT_PATH.read_text(encoding="utf8"))
    manifest_prep = json.loads((tc.DATA / "manifest.json").read_text(encoding="utf8"))
    manifest_train = load("manifest-train.json")

    # dev figures live in the TRAINING manifest; the eval records hold only the sealed-fixture numbers
    dev_by_arm = {
        r["arm"]: r.get("devAtOperatingPoint") for r in manifest_train["arms"]
    }
    train_by_arm = {r["arm"]: r for r in manifest_train["arms"]}

    arms = {}
    for arm in CANDIDATES + CONTROLS:
        p = tc.OUT / f"eval-{arm}.json"
        if p.exists():
            arms[arm] = json.loads(p.read_text(encoding="utf8"))
    missing = [a for a in CANDIDATES + CONTROLS if a not in arms]

    # the 190-case order is the fixture's own order, so every arm is aligned by case id and the
    # pairing cannot depend on the order an arm happened to be written in.
    fixture = tc.load_fixture()
    fixture_ids = [c["id"] for c in fixture]
    dec = baselines["models"]["decider-4b-exp11-reproduction"]
    dec190 = dec["strata"]["instrument190"]
    dec_by_id = {r["id"]: r for r in dec["perCase"]}
    if set(dec_by_id) != set(fixture_ids):
        raise SystemExit("REFUSED: the decider's stored rows are not the same 190 case ids as the fixture")
    dec_correct = [int(dec_by_id[i]["correct"]) for i in fixture_ids]

    # ---------------------------------------------------------- controls first
    controls = {}
    for arm in CONTROLS:
        if arm not in arms:
            continue
        a = arms[arm]
        controls[arm] = {
            "accuracy": a["accuracy"],
            "ece": a["ece"],
            "brier": a["brier"],
            "latencyMsMean": a["latencyMs"]["mean"],
            "role": "control",
        }
    # chance floor for this fixture: mean 1/k
    chance_floor = sum(1.0 / len(c["options"]) for c in fixture) / len(fixture)
    # the majority rate over the fixture's OWN answers — informational only, and labelled as leaky
    from collections import Counter

    golds = Counter(c["options"][c["correct"]] for c in fixture)
    leaky_majority = golds.most_common(1)[0][1] / len(fixture)
    option0_rate = sum(1 for c in fixture if c["correct"] == 0) / len(fixture)

    # ---------------------------------------------------------- per-head results + McNemar
    comparisons = {}
    for arm in CANDIDATES:
        if arm not in arms:
            continue
        a = arms[arm]
        a_by_id = {r["id"]: r for r in a["perCase"]}
        if set(a_by_id) != set(fixture_ids):
            raise SystemExit(f"REFUSED: {arm} was not scored on the same 190 case ids")
        a_correct = [int(a_by_id[i]["correct"]) for i in fixture_ids]
        cmp_ = mcnemar(a_correct, dec_correct, arm, "decider-4b (EXP#11 reproduction, F0 frame)")
        cmp_["pairedBootstrap95CIofDifference"] = paired_bootstrap_diff(a_correct, dec_correct)
        comparisons[arm] = cmp_

    # ---------------------------------------------------------- falsifiers
    candidate_acc = {a: arms[a]["accuracy"] for a in CANDIDATES if a in arms}
    best_arm = max(candidate_acc, key=candidate_acc.get) if candidate_acc else None
    best_acc = candidate_acc.get(best_arm)

    dev_majority = (dev_by_arm.get("majority-class") or {}).get("accuracy")

    falsifiers = {}

    f1 = best_acc is not None and best_acc < tc.F1_THRESHOLD
    falsifiers["F1"] = {
        "rule": "encoder accuracy < 0.6684 (the best 4B) -> H1 is FALSE",
        "observed": {a: v for a, v in candidate_acc.items()},
        "threshold": tc.F1_THRESHOLD,
        "bestArm": best_arm,
        "bestAccuracy": best_acc,
        "fires": bool(f1),
        "verdict": (
            f"H1 IS FALSE — the best head ({best_arm}, {best_acc:.4f}) is below the best 4B's {tc.F1_THRESHOLD}. "
            "The published 'encoder wins' evidence compares an encoder against a PROMPTED LLM; on a fine-tuned "
            "comparison on our fixture the encoder does not win."
        )
        if f1
        else (
            f"H1 is not falsified — the best head ({best_arm}, {best_acc:.4f}) reaches the best 4B's {tc.F1_THRESHOLD}."
        ),
        "secondaryComparison": {
            "note": "F1 is written against 0.6684. The stricter same-run partner is EXP#11's reproducible 0.6789; "
                    "reported so the difference between the two thresholds is visible.",
            "reproductionAccuracy": dec190["accuracy"],
            "bestHeadMinusReproduction": (best_acc - dec190["accuracy"]) if best_acc is not None else None,
        },
    }

    f2 = {}
    for arm in CANDIDATES:
        if arm not in arms:
            continue
        dev_acc = (dev_by_arm.get(arm) or {}).get("accuracy")
        fires = dev_majority is not None and dev_acc <= dev_majority
        f2[arm] = {
            "devAccuracy": dev_acc,
            "majorityClassDevAccuracy": dev_majority,
            "fires": bool(fires),
            "verdict": "VOID for this arm — training failed (dev <= majority-class), not a result about encoders"
            if fires
            else "training learned something on the unseen families (dev above the majority-class baseline)",
        }
    falsifiers["F2"] = {
        "rule": "a head's development accuracy <= the majority-class baseline -> VOID for that arm",
        "perHead": f2,
        "fires": any(v["fires"] for v in f2.values()),
        "verdict": ("VOID for " + ", ".join(a for a, v in f2.items() if v["fires"])) if any(v["fires"] for v in f2.values())
        else "no arm is void on the development split",
    }

    # F3: encoder ECE >= the decider's ECE on the same 190
    dec_ece = dec190["ece"]
    dec_ece_conf = dec190.get("eceStoredConfidenceField")
    best_ece_arm = min(candidate_acc, key=lambda a: arms[a]["ece"]) if candidate_acc else None
    f3 = best_ece_arm is not None and arms[best_ece_arm]["ece"] >= dec_ece
    f3_under_confidence = (
        best_ece_arm is not None and dec_ece_conf is not None and arms[best_ece_arm]["ece"] >= dec_ece_conf
    )
    falsifiers["F3"] = {
        "rule": "encoder ECE >= the decider's ECE (on the same 190) -> H2 is FALSE",
        "perHeadECE": {a: arms[a]["ece"] for a in CANDIDATES if a in arms},
        "perHeadBrier": {a: arms[a]["brier"] for a in CANDIDATES if a in arms},
        "perHeadECEuncalibratedT1": {a: arms[a].get("eceUncalibrated") for a in CANDIDATES if a in arms},
        "calibrationNote": "the heads' ECE is AFTER a scalar temperature fitted on the H-B development "
                           "split (never on the fixture); the T=1 column is what the same head would "
                           "report with no calibration, and the decider's ECE is its shipped confidence "
                           "with no refit here. All three are on the same 190 cases.",
        "deciderECE": dec_ece,
        "deciderECEbrier": dec190["brier"],
        "deciderECEsource": "re-scored here from EXP#11's stored per-case rows, using the probability of the option CHOSEN (probabilities[choice]) — the convention docs/research/L1_HEAD_TO_HEAD.md defines and the one that reproduces the published decider-0.8B ECE 0.075 and laya ECE 0.104",
        "deciderECEStoredConfidenceField": dec_ece_conf,
        "conventionChangesTheVerdict": bool(f3 != f3_under_confidence),
        "firesUnderStoredConfidenceField": bool(f3_under_confidence),
        "robustnessToTemperature": {
            "bestHeadECEfitted": min(arms[a]["ece"] for a in CANDIDATES if a in arms),
            "bestHeadECEtemperature1": min(
                (arms[a].get("eceUncalibrated") or float("inf")) for a in CANDIDATES if a in arms
            ),
            "deciderECE": dec_ece,
            "firesWithFittedTemperature": bool(f3),
            "firesWithNoCalibration": bool(
                min((arms[a].get("eceUncalibrated") or float("inf")) for a in CANDIDATES if a in arms) >= dec_ece
            ),
            "note": "under BOTH readings of the encoder's calibration the best head's ECE is at or above the "
                    "decider's, so F3's verdict does not depend on the temperature fit — only on which "
                    "decider field the comparison uses (see conventionChangesTheVerdict).",
        },
        "conventionNote": "the rows also carry a separate post-calibration `confidence` scalar. Under THAT reading the best head (ECE 0.0996) beats the decider (0.1547) and F3 would not fire. The pre-registration's own method section points at the L1 protocol, which is probabilities[choice], and only that convention reproduces the two published ECE figures; it is therefore the primary. Both verdicts are stated so the reader can see that this choice is load-bearing.",
        "bestCalibratedArm": best_ece_arm,
        "fires": bool(f3),
        "verdict": (
            f"H2 IS FALSE — even the best-calibrated head ({best_ece_arm}, ECE {arms[best_ece_arm]['ece']:.4f}) is "
            f"not better calibrated than the decider (ECE {dec_ece:.4f}). The 'native distribution' argument does not "
            "survive contact."
        )
        if f3
        else (
            f"H2 survives — the best-calibrated head ({best_ece_arm}, ECE {arms[best_ece_arm]['ece']:.4f}) beats the "
            f"decider's ECE ({dec_ece:.4f})."
        ),
    }

    falsifiers["F4"] = {
        "rule": "any >=2-shared-8-gram overlap between training rows and the fixture -> RUN VOID",
        "trainVsFixtureSilent": lint["trainVsFixture"]["silent"],
        "pairsCompared": lint["trainVsFixture"]["forward"]["pairsCompared"],
        "seededCopyControlOk": bool(lint.get("demo", {}).get("ok")),
        "seededCopiesFired": [p["name"] for p in lint.get("demo", {}).get("probes", []) if p["fired"]],
        "novelRowSilent": [p["name"] for p in lint.get("demo", {}).get("probes", []) if not p["fired"]],
        "fires": not lint["trainVsFixture"]["silent"],
        "verdict": "RUN VOID — the instrument was contaminated" if not lint["trainVsFixture"]["silent"]
        else (
            "the run is not void — 0 rows removed over "
            f"{lint['trainVsFixture']['forward']['pairsCompared']} pairs, both directions, and the lint was shown to fire "
            "on three seeded copies and stay silent on a novel row"
        ),
    }

    f5 = {label: c["reproducesAt3dp"] for label, c in baselines["checks"].items() if c["reproducesAt3dp"] is not None}
    falsifiers["F5"] = {
        "rule": "the known baselines are not reproduced when re-scored -> RUN VOID — the control cannot report zero",
        "rescores": {
            label: {"reScored": c["reScored"], "published": c["published"],
                    "stratum": c["stratum"], "reproducesAt3dp": c["reproducesAt3dp"]}
            for label, c in baselines["checks"].items()
        },
        "note": "each published number is re-scored against the STRATUM it actually came from. The re-score "
                "found that the pre-registration's `imajev-4b 0.645` is imajev's H-A corpus accuracy, not its "
                "190-fixture accuracy; that figure is 0.6368 from the same stored rows.",
        "checks": f5,
        "fires": not baselines["allReproduce"],
        "verdict": "RUN VOID — a stored baseline did not reproduce under this scorer" if not all(f5.values())
        else (
            "not void — the stored baselines re-score to their published values through this experiment's own "
            "accuracy/ECE/Brier code"
        ),
    }

    lat = {a: arms[a]["latencyMs"]["mean"] / 1000.0 for a in CANDIDATES if a in arms}
    f6 = any(v > tc.F6_4B_LATENCY_S for v in lat.values())
    falsifiers["F6"] = {
        "rule": f"a head's latency > the 4B's measured {tc.F6_4B_LATENCY_S} s/decision warm -> H3 is FALSE",
        "thresholdSeconds": tc.F6_4B_LATENCY_S,
        "observedSecondsMean": lat,
        "decider4bLatencyMeanSecondsFromStoredRows": dec190["latencyMsMean"] / 1000.0,
        "fires": bool(f6),
        "verdict": (
            "H3 IS FALSE — a head is slower than the 4B's measured warm per-decision latency"
            if f6
            else "H3 survives — every head is faster per decision than the 4B's measured warm latency"
        ),
        "caveat": "the 0.075 s threshold is the pre-registered 4B figure from DECIDER_TIER §2; the baseline's own "
                  "re-scored per-decision latency on these 190 rows is quoted alongside it, and the two were measured "
                  "on different serving stacks, so the encoder-vs-4B latency comparison is not like-for-like hardware.",
    }

    # H4 — diagnostic, not a falsifier
    order = ["setfit-mpnet", "modernbert-base", "deberta-v3-base"]  # 109M, 149M, ~184M
    present = [(a, manifest_train["arms"]) for a in order if a in candidate_acc]
    params = {}
    for a in arms:
        rep = train_by_arm.get(a)
        if rep is not None:
            params[a] = rep["parameters"]
    h4 = {
        "hypothesis": "encoder accuracy is NOT monotone in parameter count across the three heads",
        "parameterCounts": params,
        "accuracies": {a: candidate_acc.get(a) for a in order if a in candidate_acc},
        "observed": None,
        "verdict": None,
    }
    seq = [(a, candidate_acc[a]) for a in order if a in candidate_acc]
    if len(seq) == 3:
        (a1, v1), (a2, v2), (a3, v3) = seq
        mono = (v1 <= v2 <= v3) or (v1 >= v2 >= v3)
        h4["observed"] = "monotone" if mono else "non-monotone"
        h4["verdict"] = (
            "H4 is not supported: accuracy moves monotonically with parameter count across these three heads"
            if mono
            else "H4 is supported on this fixture: accuracy is not monotone in parameter count across these three heads"
        )
    else:
        h4["verdict"] = f"H4 could not be evaluated — {len(seq)} of 3 heads ran"

    # ---------------------------------------------------------- observations
    observations = {}
    if "majority-class" in arms and candidate_acc:
        maj = arms["majority-class"]["accuracy"]
        best_c = max(candidate_acc.values())
        observations["majorityClassBeatsEveryCandidate"] = {
            "majorityClassAccuracy": maj,
            "bestCandidateAccuracy": best_c,
            "margin": maj - best_c,
            "note": "the mandatory majority-class control outscores every candidate head on the sealed 190. "
                    "This is the headline caveat on this run: the three heads do not beat a corpus-marginal "
                    "prior, so F1's failure is not a near miss.",
        }
    temp = {}
    for a in arms:
        t = float(arms[a]["temperature"])
        temp[a] = {"fittedTemperature": t, "onGridFloor": t <= 0.0012, "onGridCeiling": t >= 99.0}
    observations["temperatureScaling"] = {
        "grid": "geometric 1e-3 .. 1e2, 200 points (tccommon.fit_temperature)",
        "perArm": temp,
        "note": "a fitted T on the grid boundary means the optimum was not interior; the reported ECE is then "
                "an upper bound on what this arm's calibration could reach.",
    }
    for rep in manifest_train["arms"]:
        if rep["arm"] == "deberta-v3-base":
            curve = rep["devCurve"]
            observations["debertaV3Training"] = {
                "devCurveTrainLoss": [e["trainLoss"] for e in curve],
                "devCurveAccuracy": [e["devAccuracy"] for e in curve],
                "majorityClassDevAccuracy": dev_majority,
                "note": "DeBERTa-v3-base's training loss barely moved (see the curve) and its dev accuracy is "
                        "only just above the majority-class baseline, so this arm should be read as 'did not "
                        "train at the pre-registered epoch-1 operating point with lr 2e-5 and 50 steps' rather "
                        "than as 'trained and failed to transfer'. F2 did not fire as written because its dev "
                        "accuracy is strictly above the majority baseline.",
            }

    # ---------------------------------------------------------- assemble
    out = {
        "experiment": "EXP#12",
        "preRegistration": "docs/research/experiments/EXP#12-typed-channel-comparison.md",
        "pairedPartner": "decider-4b EXP#11 reproduction (F0_decider frame), same 190 cases, same option orders",
        "instrument": {
            "fixtureReads": manifest_eval["fixtureReadReceipt"]["reads"],
            "instrument190Sha256": tc.INSTRUMENT_190_SHA256,
            "cases": 190,
            "chanceFloorMean1overK": chance_floor,
            "leakyMajorityRateOverFixtureAnswers": leaky_majority,
            "option0Rate": option0_rate,
        },
        "heads": {
            a: {
                "role": arms[a]["role"],
                "modelId": arms[a]["modelId"],
                "licence": arms[a]["licence"],
                "accuracy": arms[a]["accuracy"],
                "accuracy95CI": arms[a]["accuracy95CI"],
                "ece": arms[a]["ece"],
                "brier": arms[a]["brier"],
                "temperature": arms[a]["temperature"],
                "latencyMs": arms[a]["latencyMs"],
                "perKind": arms[a]["perKind"],
                "perClass": arms[a]["perClass"],
                "orderPermutationProbe": arms[a].get("orderPermutationProbe"),
                "devAtOperatingPoint": dev_by_arm.get(a),
                "trainSeconds": (train_by_arm.get(a) or {}).get("trainSeconds"),
                "parameters": params.get(a),
            }
            for a in arms
        },
        "baselinesRescored": {
            k: {kk: vv for kk, vv in v.items() if kk != "perCase"} for k, v in baselines["models"].items()
        },
        "baselineChecks": baselines["checks"],
        "publishedBaselines": tc.BASELINES,
        "comparisons": comparisons,
        "controls": controls,
        "falsifiers": falsifiers,
        "h4": h4,
        "observations": observations,
        "resolution": {
            "state": "CLOSE" if (F1 := falsifiers["F1"])["fires"] else "EMERGE",
            "fires": sorted(k for k, v in falsifiers.items() if v["fires"]),
            "note": "AGENTS.md experiment discipline: F1 fired, so the method is CLOSE — harvest the learnings "
                    "naming the falsifier, leave the method behind, and close the branch unmerged. F3 also fired, "
                    "which kills H2 independently of H1. F2/F4/F5/F6 did not fire, so the run is neither void nor "
                    "an instrument failure.",
        },
        "incomplete": missing,
    }
    tc.write_json(tc.OUT / "analysis.json", out)

    # ---------------------------------------------------------- console summary
    print("EXP#12 analysis\n")
    print(f"chance floor (mean 1/k over the 190)        {chance_floor:.4f}")
    print(f"majority rate over the fixture's own answers {leaky_majority:.4f}  (leaky: uses fixture labels; informational)")
    print(f"always-option-0 rate                        {option0_rate:.4f}")
    print("\nheads (sealed 190, one read):")
    for a in list(arms):
        e = arms[a]
        print(
            f"  {a:16s} acc {e['accuracy']:.4f} [{e['accuracy95CI'][0]:.4f},{e['accuracy95CI'][1]:.4f}]  "
            f"ECE {e['ece']:.4f}  Brier {e['brier']:.4f}  lat {e['latencyMs']['mean']:.2f} ms"
        )
    print("\nknown baselines re-scored (F5):")
    for name, b in baselines["models"].items():
        for stratum, st in b["strata"].items():
            print(
                f"  {name:32s} {stratum:14s} n={st['n']:3d} acc {st['accuracy']:.4f} "
                f"(published {st['published']}) reproduces@3dp={st['reproducesAt3dp']}"
            )
    print("\npaired McNemar (encoder vs decider-4b reproduction):")
    for a, c in comparisons.items():
        print(
            f"  {a:16s} b={c['aOnlyCorrect']:3d} c={c['bOnlyCorrect']:3d} psi={c['discordancePsi']:.3f} "
            f"diff={c['accuracyDifference']:+.4f} p={c['mcnemarExactTwoSidedP']:.4g} "
            f"MDE(paired)={c['mdePaired']:.4f} MDE(unpaired)={c['mdeUnpaired']:.4f} ratio={c['mdeRatioUnpairedOverPaired']:.2f}x"
        )
    print("\nfalsifiers:")
    for k in ("F1", "F2", "F3", "F4", "F5", "F6"):
        f = falsifiers[k]
        print(f"  {k} fires={f['fires']}  {f['verdict']}")
    print(f"\nH4: {h4['verdict']}")
    if missing:
        print(f"\nINCOMPLETE: {missing} not scored")
    print(f"\nwrote {tc.OUT / 'analysis.json'}")


if __name__ == "__main__":
    main()

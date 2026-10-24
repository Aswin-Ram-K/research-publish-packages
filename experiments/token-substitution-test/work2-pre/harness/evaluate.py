#!/usr/bin/env python3
"""
evaluate.py — EXP#12 step 3: score every frozen arm on the sealed 190, ONCE.

Pre-registration: docs/research/experiments/EXP#12-typed-channel-comparison.md §5.4, §7.3 (frozen).

THE SEALED-SET DISCIPLINE, AS ENFORCED HERE
  `data/fixture-190.json` is opened exactly once, at the top of `main()`, into memory. Every arm — the
  three candidates and the two controls — is then scored off that single in-memory list, and
  `out/fixture-read-receipt.json` records the count of reads, the digest of the file and the fact
  that no arm was scored twice. There is no loop in which a fixture number is read, a model is
  adjusted, and the fixture is read again.

REPORTED PER ARM
  accuracy (+ a 2000-sample bootstrap 95 % CI) · ECE over 10 equal-width bins on the probability of
  the option CHOSEN, matching the L1 head-to-head protocol so the encoder's ECE is comparable to the
  published deciders' · Brier on the same quantity · per-class accuracy over the fixture's option
  labels · per-kind accuracy · per-decision latency (mean / p50 / p95, warm, and the timing method).

  Plus one exploratory measurement the pre-registration permits and does not fold into H1 (§5.6): the
  same fixture re-scored with each case's options permuted, which measures the head's order
  sensitivity directly. For a pointwise head this is expected to be exactly zero; it is measured
  rather than asserted.

RUN
  python3 tools/typed-channel/evaluate.py
"""

from __future__ import annotations

import json
import platform
import statistics
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import numpy as np  # noqa: E402
import torch  # noqa: E402

import tccommon as tc  # noqa: E402
import tcmodel as tm  # noqa: E402

#: candidates and controls, in report order
CANDIDATE_ARMS = ("modernbert-base", "deberta-v3-base", "setfit-mpnet")
CONTROL_ARMS = ("majority-class", "shuffled-label")
ALL_ARMS = CANDIDATE_ARMS + CONTROL_ARMS


def load_pointwise(arm: str, device: str):
    ckpt = torch.load(tc.OUT / "models" / f"{arm}.pt", map_location="cpu", weights_only=False)
    model = tm.PointwiseScorer(ckpt["base_name"], dropout=ckpt["dropout"])
    model.load_state_dict(ckpt["state_dict"])
    model.to(device).eval()
    from transformers import AutoTokenizer

    tokenizer = AutoTokenizer.from_pretrained(tc.OUT / "models" / f"{arm}-tokenizer")
    return model, tokenizer, ckpt["max_length"]


def load_setfit(arm: str, device: str):
    import joblib

    blob = joblib.load(tc.OUT / "models" / f"{arm}.joblib")
    head = tm.LogisticPairHead(model_id=blob["model_id"], max_length=blob["max_length"], device=device)
    head.scaler = blob["scaler"]
    head.clf = blob["clf"]
    return head


def load_majority(arm: str):
    return json.loads((tc.OUT / "models" / f"{arm}.json").read_text(encoding="utf8"))


def score_pointwise(model, tokenizer, example, device, max_length, options=None):
    opts = options if options is not None else example["options"]
    texts = [tc.render(example["kind"], example["situation"], o) for o in opts]
    enc = tokenizer(texts, padding=True, truncation=True, max_length=max_length, return_tensors="pt").to(device)
    with torch.no_grad():
        logits = model(enc["input_ids"], enc["attention_mask"]).float().cpu().tolist()
    return logits


def score_setfit(head, example, options=None):
    opts = options if options is not None else example["options"]
    return head.case_logits(tc.render_context(example["kind"], example["situation"]), opts)


def score_majority(blob, example, options=None):
    opts = options if options is not None else example["options"]
    return [blob["labelLogMarginal"].get(o, blob["floor"]) for o in opts]


def decide(logits, temperature: float):
    probs = tc.softmax(logits, temperature)
    idx = int(np.argmax(probs))
    return idx, probs, probs[idx]


# ------------------------------------------------------------------ baselines (re-scored, F5)


def rescore_baselines() -> dict:
    """Re-score the known baselines from the stored per-case rows, with THIS experiment's metrics.

    F5: "the known baselines (§3) are not reproduced when re-scored -> RUN VOID — the control cannot
    report zero." The raw per-case rows are in the tree, so this needs no model: the stored `answer` /
    `correct` / `confidence` fields go through the same accuracy, ECE and Brier functions the encoders
    go through.

    ONE THING THE RE-SCORE FOUND, AND IT IS RECORDED RATHER THAN SMOOTHED OVER. The pre-registration §3
    lists "decider-4b 0.6684, imajev-4b 0.645, and the reproduction 0.6789" as if all three were
    fixture figures. They are not: from EXP#11's stored rows, decider-4b's round-0 accuracies are
    H-A 0.6650 / H-B 0.6700 / **instrument190 0.6789**, and imajev-4b's are H-A **0.6450** /
    H-B 0.6700 / instrument190 **0.6368**. So **0.645 is imajev's H-A corpus accuracy, not its
    190-fixture accuracy**, and the fixture figure is 0.6368. Each published number is therefore
    re-scored against the stratum it actually came from, and the stratum is named in the record.
    """
    root = tc.HERE.parent.parent
    models = {}

    for name, path, published in (
        (
            "decider-4b-exp11-reproduction",
            "docs/research/EXP#11-evidence/decider-rows.jsonl",
            {"instrument190": 0.6789, "H-A": 0.6650, "H-B": 0.6700},
        ),
        (
            "imajev-4b-exp11",
            "docs/research/EXP#11-evidence/imajev-rows.jsonl",
            {"H-A": 0.645, "H-B": 0.6700, "instrument190": 0.6368},
        ),
    ):
        p = root / path
        rows = [json.loads(l) for l in p.read_text(encoding="utf8").splitlines() if l.strip()]
        r0 = [r for r in rows if r.get("round") == 0]
        strata = {}
        per_case = None
        for stratum in ("H-A", "H-B", "instrument190"):
            sub = [r for r in r0 if r.get("stratum") == stratum]
            if not sub:
                continue
            correct = [int(r["answer"] == r["gold"]) for r in sub]
            conf = [float(r["confidence"]) if r.get("confidence") is not None else 1.0 for r in sub]
            # THE CONVENTION, AND WHY IT DECIDES F3. docs/research/L1_HEAD_TO_HEAD.md — the protocol
            # this instrument and these baselines come from — defines it: "Confidence for ECE is the
            # probability the model assigned to the option it chose (`probabilities[choice]` for both)".
            # The rows also carry a separate `confidence` scalar (a post-calibration transform, mean
            # |confidence - p(chosen)| = 0.12 on these rows), and the two conventions give OPPOSITE F3
            # verdicts. The primary figure here is `probabilities[chosen]`, because (a) it is the
            # documented protocol, (b) it is the decider's NATIVE per-option distribution, which is the
            # thing H2 makes a claim about, and (c) reproducing the published decider-0.8B ECE (0.075)
            # and laya ECE (0.104) is a check that only this convention passes — see
            # `calibrationConventionValidation` below. Both figures are recorded.
            p_native = [float(r["probabilities"][r["answer"]]) for r in sub]
            strata[stratum] = {
                "n": len(sub),
                "accuracy": sum(correct) / len(correct),
                "ece": tc.ece(p_native, correct),
                "eceStoredConfidenceField": tc.ece(conf, correct),
                "brier": tc.brier(p_native, correct),
                "brierStoredConfidenceField": tc.brier(conf, correct),
                "latencyMsMean": statistics.fmean(r["latencyMs"] for r in sub),
                "published": published.get(stratum),
                "reproducesAt3dp": (stratum not in published)
                or abs(sum(correct) / len(correct) - published[stratum]) <= 5e-4,
                "absoluteDifference": (None if stratum not in published
                                       else abs(sum(correct) / len(correct) - published[stratum])),
            }
            if stratum == "instrument190":
                per_case = [
                    {"id": r["caseId"], "predLabel": r["answer"], "gold": r["gold"], "correct": bool(c),
                     "pChosen": float(r["confidence"]) if r.get("confidence") is not None else None}
                    for r, c in zip(sub, correct)
                ]
        models[name] = {"source": path, "round": 0, "strata": strata, "perCase": per_case}

    # laya, from the L1 head-to-head rows (all 190 fixture cases, one model)
    p = root / "docs/research/l1-head-to-head.jsonl"
    rows = [json.loads(l) for l in p.read_text(encoding="utf8").splitlines() if l.strip()]
    laya = [r for r in rows if r["model"] == "laya"]
    correct = [int(r["picked_index"] == r["correct"]) for r in laya]
    conf = [float(r["p_chosen"]) for r in laya]
    acc = sum(correct) / len(correct)
    models["laya-typed-decisions"] = {
        "source": "docs/research/l1-head-to-head.jsonl",
        "round": None,
        "strata": {
            "instrument190": {
                "n": len(laya),
                "accuracy": acc,
                "ece": tc.ece(conf, correct),
                "brier": tc.brier(conf, correct),
                "latencyMsMean": statistics.fmean(r["ms"] for r in laya),
                "published": 0.374,
                "reproducesAt3dp": abs(acc - 0.374) <= 5e-4,
                "absoluteDifference": abs(acc - 0.374),
            }
        },
        "perCase": None,
    }

    # validate the ECE convention against two PUBLISHED figures computed from the same rows
    p = root / "docs/research/l1-head-to-head.jsonl"
    rows = [json.loads(l) for l in p.read_text(encoding="utf8").splitlines() if l.strip()]
    validation = {}
    for label, subset, published in (
        ("laya", [r for r in rows if r["model"] == "laya"], 0.104),
        ("decider-0.8b", [r for r in rows if r["model"] != "laya"], 0.075),
    ):
        c = [int(r["picked_index"] == r["correct"]) for r in subset]
        pc = [float(r["p_chosen"]) for r in subset]
        validation[label] = {
            "n": len(subset),
            "eceFromProbabilityOfChosenOption": tc.ece(pc, c),
            "publishedEce": published,
            "reproduces": abs(tc.ece(pc, c) - published) <= 0.002,
        }

    checks = {}
    for label, model_name, stratum in (
        ("decider-4b reproduction 0.6789 @ instrument190", "decider-4b-exp11-reproduction", "instrument190"),
        ("imajev-4b 0.645 @ H-A (its actual source)", "imajev-4b-exp11", "H-A"),
        ("imajev-4b fixture figure @ instrument190", "imajev-4b-exp11", "instrument190"),
        ("laya 0.374 @ instrument190", "laya-typed-decisions", "instrument190"),
        ("decider-4b H-A 0.6650 @ H-A", "decider-4b-exp11-reproduction", "H-A"),
    ):
        st = models[model_name]["strata"][stratum]
        checks[label] = {
            "stratum": stratum,
            "reScored": st["accuracy"],
            "published": st["published"],
            "absoluteDifference": st["absoluteDifference"],
            "reproducesAt3dp": st["reproducesAt3dp"],
        }
    checks["decider-4b 0.6684 (D-067)"] = {
        "stratum": "instrument190",
        "reScored": None,
        "published": 0.6684,
        "reproducesAt3dp": None,
        "note": "no per-case rows for the D-067 measurement are in the tree, so it cannot be re-scored "
                "directly; the same-run reproduction of the same instrument is the check that stands in "
                "for it, and that one re-scores to 0.6789 exactly.",
    }
    return {
        "models": models,
        "checks": checks,
        "calibrationConventionValidation": validation,
        "allReproduce": all(
            v["reproducesAt3dp"] for v in checks.values() if v["reproducesAt3dp"] is not None
        ),
    }


def main() -> None:
    argv = sys.argv[1:]
    device = "cuda" if torch.cuda.is_available() else "cpu"
    if "--device" in argv:
        device = argv[argv.index("--device") + 1]
    arms = [a for a in (argv[argv.index("--arms") + 1].split(",") if "--arms" in argv else ALL_ARMS) if a]
    repeats = int(argv[argv.index("--repeats") + 1]) if "--repeats" in argv else 3
    warmup = int(argv[argv.index("--warmup") + 1]) if "--warmup" in argv else 20

    print(f"EXP#12 evaluation — device {device}")
    if device == "cuda":
        print(f"  gpu {torch.cuda.get_device_name(0)}  torch {torch.__version__}  cuda {torch.version.cuda}")
    print(f"  host {platform.node()} {platform.machine()}  python {platform.python_version()}")

    # ---------------------------------------------------------------- THE ONE READ
    fixture_path = tc.FIXTURE_PATH
    fixture_digest = tc.sha256_file(fixture_path)
    fixture_raw = fixture_path.read_text(encoding="utf8")
    fixture = json.loads(fixture_raw)
    reads = 1
    if len(fixture) != 190:
        raise SystemExit(f"REFUSED: fixture holds {len(fixture)} cases, expected 190")
    for c in fixture:
        if not (0 <= c["correct"] < len(c["options"])):
            raise SystemExit(f"REFUSED: {c['id']} has an out-of-range correct index")
    examples = [tc.fixture_case_to_example(c) for c in fixture]
    print(f"\nsealed fixture read ONCE: {len(examples)} cases, sha256 {fixture_digest}")
    print(f"  sha256 of the TS source it was exported from must be {tc.INSTRUMENT_190_SHA256}")

    results = {}
    for arm in arms:
        print(f"\n--- {arm}", flush=True)
        t0 = time.time()
        if arm in tm.POINTWISE_ARMS or arm == "shuffled-label":
            model, tokenizer, max_length = load_pointwise(arm, device)
            scorer = lambda ex, opts=None: score_pointwise(model, tokenizer, ex, device, max_length, opts)
        elif arm == "setfit-mpnet":
            head = load_setfit(arm, device)
            scorer = lambda ex, opts=None: score_setfit(head, ex, opts)
        elif arm == "majority-class":
            blob = load_majority(arm)
            scorer = lambda ex, opts=None: score_majority(blob, ex, opts)
        else:
            raise SystemExit(f"unknown arm {arm}")

        dev = json.loads((tc.OUT / "dev" / f"{arm}.json").read_text(encoding="utf8"))
        temperature = float(dev["devAtOperatingPoint"]["temperature"])

        # latency: warm, then `repeats` full passes over the 190, per-decision wall clock
        for ex in examples[:warmup]:
            scorer(ex)
        if device == "cuda":
            torch.cuda.synchronize()
        lat = []
        per_case = []
        for _ in range(repeats):
            for ex in examples:
                t = time.perf_counter()
                logits = scorer(ex)
                if device == "cuda":
                    torch.cuda.synchronize()
                lat.append((time.perf_counter() - t) * 1000.0)
                idx, probs, p = decide(logits, temperature)
                per_case.append(
                    {
                        "id": ex["id"],
                        "kind": ex["kind"],
                        "options": ex["options"],
                        "goldIndex": ex["goldIndex"],
                        "gold": ex["gold"],
                        "predIndex": idx,
                        "predLabel": ex["options"][idx],
                        "pChosen": p,
                        "probs": probs,
                        "logits": logits,
                        "correct": bool(idx == ex["goldIndex"]),
                    }
                )
        # keep the last full pass as the record; latency keeps every pass
        last = per_case[-len(examples):]

        correct = [int(r["correct"]) for r in last]
        pchosen = [r["pChosen"] for r in last]
        # the same quantity with NO temperature applied, so the report shows what the H-B fit bought
        # rather than only what it produced
        pchosen_t1 = [tc.softmax(r["logits"], 1.0)[r["predIndex"]] for r in last]
        acc = sum(correct) / len(correct)
        lo, hi = tc.bootstrap_ci([float(c) for c in correct])
        lat_sorted = sorted(lat)
        entry = {
            "arm": arm,
            "modelId": tm.MODEL_IDS.get(arm) if arm != "majority-class" else None,
            "licence": tm.LICENCES.get(tm.MODEL_IDS.get(arm, "")) if arm != "majority-class" else None,
            "role": "candidate" if arm in CANDIDATE_ARMS else "control",
            "device": device,
            "temperature": temperature,
            "temperatureSource": "fitted on the H-B development split (never on the fixture)",
            "fixtureReads": reads,
            "accuracy": acc,
            "accuracy95CI": [lo, hi],
            "ece": tc.ece(pchosen, correct),
            "brier": tc.brier(pchosen, correct),
            "eceUncalibrated": tc.ece(pchosen_t1, correct),
            "brierUncalibrated": tc.brier(pchosen_t1, correct),
            "meanPChosen": float(np.mean(pchosen)),
            "perKind": tc.per_kind_accuracy(last),
            "perClass": tc.per_class_accuracy(last),
            "latencyMs": {
                "method": "wall clock around one full per-decision call (all option texts tokenised, one forward batch, softmax); "
                          "warmed with "
                          + str(warmup)
                          + " cases, then "
                          + str(repeats)
                          + " full passes over the 190; GPU synchronised before each stop",
                "n": len(lat),
                "mean": statistics.fmean(lat),
                "p50": statistics.median(lat),
                "p95": float(np.percentile(lat_sorted, 95)),
                "min": lat_sorted[0],
                "max": lat_sorted[-1],
            },
            "seconds": time.time() - t0,
            "perCase": [{k: v for k, v in r.items() if k not in ("probs", "logits")} for r in last],
        }

        # exploratory §5.6: the same fixture with each case's options permuted
        rng = np.random.default_rng(tc_hash(arm))
        flips, max_dp = 0, 0.0
        for r, ex in zip(last, examples):
            perm = rng.permutation(len(ex["options"]))
            perm_opts = [ex["options"][i] for i in perm]
            plogits = scorer(ex, perm_opts)
            pidx, pprobs, _ = decide(plogits, temperature)
            # plogits[i] belongs to perm_opts[i], so the predicted LABEL is perm_opts[pidx]. An earlier
            # revision of this probe indexed the ORIGINAL option list instead, which reported 138/190
            # flips on a permutation-equivariant head — a probe that was wrong, not a finding.
            if perm_opts[pidx] != r["predLabel"]:
                flips += 1
            by_label = {perm_opts[i]: p for i, p in enumerate(pprobs)}
            max_dp = max(max_dp, abs(by_label[r["predLabel"]] - r["pChosen"]))
        entry["orderPermutationProbe"] = {
            "note": "exploratory add-on (pre-registration §5.6); NOT folded into H1",
            "cases": len(last),
            "predictionFlips": flips,
            "maxAbsDeltaPChosen": max_dp,
        }
        results[arm] = entry
        print(
            f"  accuracy {acc:.4f} [{lo:.4f},{hi:.4f}]  ECE {entry['ece']:.4f} (T=1: {entry['eceUncalibrated']:.4f})  "
            f"Brier {entry['brier']:.4f}  "
            f"latency mean {entry['latencyMs']['mean']:.2f} ms p95 {entry['latencyMs']['p95']:.2f} ms  "
            f"order flips {flips}",
            flush=True,
        )
        tc.write_json(tc.OUT / f"eval-{arm}.json", entry)

    baselines = rescore_baselines()
    print("\n--- known baselines re-scored from the stored rows with this experiment's scorer (F5)")
    for name, b in baselines["models"].items():
        for stratum, st in b["strata"].items():
            print(
                f"  {name:32s} {stratum:14s} n={st['n']:3d} accuracy {st['accuracy']:.4f} "
                f"(published {st['published']}) reproduces@3dp={st['reproducesAt3dp']} "
                f"ECE {st['ece']:.4f} Brier {st['brier']:.4f}"
            )
    print("  calibration-convention validation (probability of the option chosen reproduces the published ECEs):")
    for label, v in baselines["calibrationConventionValidation"].items():
        print(f"    {label}: ECE {v['eceFromProbabilityOfChosenOption']:.4f} vs published {v['publishedEce']} -> {v['reproduces']}")
    print("  F5 checks:")
    for label, c in baselines["checks"].items():
        print(f"    {label}: re-scored {c['reScored']} vs published {c['published']} -> {c['reproducesAt3dp']}")
    tc.write_json(tc.OUT / "baselines.json", baselines)

    receipt = {
        "fixture": str(fixture_path),
        "exportedFrom": "evals/fixtures/reflex-decisions.ts",
        "instrument190Sha256Expected": tc.INSTRUMENT_190_SHA256,
        "fixtureJsonSha256": fixture_digest,
        "reads": reads,
        "cases": len(examples),
        "armsScored": list(results.keys()),
        "scoringPassesPerArm": repeats,
        "note": "one read, in one process, before any arm was scored; no arm was scored twice and no "
                "fixture number was used to adjust a model",
    }
    tc.write_json(tc.OUT / "fixture-read-receipt.json", receipt)

    manifest = {
        "experiment": "EXP#12",
        "step": "evaluate",
        "host": platform.node(),
        "machine": platform.machine(),
        "device": device,
        "gpu": torch.cuda.get_device_name(0) if device == "cuda" else None,
        "torch": torch.__version__,
        "fixtureReadReceipt": receipt,
        "arms": {k: {kk: vv for kk, vv in v.items() if kk != "perCase"} for k, v in results.items()},
    }
    tc.write_json(tc.OUT / "manifest-eval.json", manifest)
    print(f"\nwrote {tc.OUT / 'manifest-eval.json'}")


def tc_hash(text: str) -> int:
    import hashlib

    return int(hashlib.sha256(text.encode()).hexdigest()[:8], 16)


if __name__ == "__main__":
    main()

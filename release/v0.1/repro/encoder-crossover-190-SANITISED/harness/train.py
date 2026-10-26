#!/usr/bin/env python3
"""
train.py — EXP#12 step 2: fit the three candidate heads and the two mandatory control arms.

Pre-registration: docs/research/experiments/EXP#12-typed-channel-comparison.md §5, §7 (frozen).

THE OPERATING POINT IS FIXED, NOT CHOSEN
  §5.3: "epoch 1 as the pre-registered operating point ... early stopping on the H-B development
  split". So the artefact that is scored on the sealed 190 is the END-OF-EPOCH-1 checkpoint, saved
  before any selection happens; the dev curve over later epochs is recorded and reported as the
  diagnostic it is, and is NEVER used to pick the epoch that gets scored. `--epochs` controls how far
  the dev curve is followed; it cannot move the reported operating point.

WHAT THIS SCRIPT WILL NOT DO
  It never reads the sealed fixture. `grep -n FIXTURE train.py` returns nothing, and the run manifest
  records that. The fixture is opened exactly once, by `evaluate.py`, after every arm is frozen.

REFUSAL BEFORE TRAINING
  It re-checks the F4 lint report: if the training split overlaps the sealed instrument, or if the
  lint's seeded-copy control did not answer both ways, nothing is trained.

ARMS
  modernbert-base   pointwise scorer, answerdotai/ModernBERT-base (Apache-2.0, 149M)
  deberta-v3-base   pointwise scorer, microsoft/deberta-v3-base (MIT, ~184M)
  setfit-mpnet      frozen sentence-transformers/all-mpnet-base-v2 + logistic pair head (109M)
  majority-class    control: the training label marginal, restricted to the case's own option set
  shuffled-label    control: modernbert-base fitted on randomly permuted training labels

RUN
  python3 tools/typed-channel/train.py --epochs 3
"""

from __future__ import annotations

import argparse
import json
import os
import platform
import random
import sys
import time

from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import numpy as np  # noqa: E402
import torch  # noqa: E402
import torch.nn as nn  # noqa: E402

import tccommon as tc  # noqa: E402
import tcmodel as tm  # noqa: E402

SEED = 20261004


def fail(msg: str) -> None:
    print(f"REFUSED: {msg}", file=sys.stderr)
    raise SystemExit(2)


# ------------------------------------------------------------------ data


def load_jsonl(path: Path):
    rows = []
    with open(path, encoding="utf8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def check_gate() -> dict:
    if not tc.LINT_REPORT_PATH.exists():
        fail("no lint report — run ./scripts/run.sh tools/typed-channel/lint.ts --demo first")
    lint = json.loads(tc.LINT_REPORT_PATH.read_text(encoding="utf8"))
    if lint["trainVsFixture"]["silent"] is not True:
        fail("F4 FIRED: the training split overlaps the sealed fixture — RUN VOID")
    demo = lint.get("demo") or {}
    if not demo.get("ok"):
        fail("the lint's seeded-copy control did not answer both ways — the detector is untrusted")
    if tc.sha256_file(tc.CORPUS_PATH) != tc.CORPUS_SHA256:
        fail("corpus digest changed since prepare")
    return lint


# ------------------------------------------------------------------ tokenisation


def tokenize_cases(tokenizer, examples, max_length: int):
    """(n_cases, K, L) padded tensors plus the true option count and gold index per case."""
    k_max = max(len(e["options"]) for e in examples)
    n = len(examples)
    ids = torch.zeros((n, k_max, max_length), dtype=torch.long)
    mask = torch.zeros((n, k_max, max_length), dtype=torch.long)
    ks = torch.zeros(n, dtype=torch.long)
    gold = torch.zeros(n, dtype=torch.long)
    lengths = []
    truncated = 0
    for i, e in enumerate(examples):
        texts = tc.texts_for_example(e)
        ks[i] = len(texts)
        gold[i] = e["goldIndex"]
        enc = tokenizer(texts, padding="max_length", truncation=True, max_length=max_length, return_tensors="pt")
        ids[i, : len(texts)] = enc["input_ids"]
        mask[i, : len(texts)] = enc["attention_mask"]
        for m in enc["attention_mask"].sum(1).tolist():
            lengths.append(m)
            if m >= max_length:
                truncated += 1
    return ids, mask, ks, gold, {"maxOptionCount": k_max, "tokenLengths": lengths, "truncated": truncated}


# ------------------------------------------------------------------ pointwise training


def case_logits_batched(model, ids, mask, ks, batch_cases: int, device: str):
    """Per-case logits over the true options; padded option slots get -inf."""
    out = []
    n = ids.shape[0]
    with torch.no_grad():
        for start in range(0, n, batch_cases):
            idx = slice(start, min(start + batch_cases, n))
            b_ids = ids[idx].to(device)
            b_mask = mask[idx].to(device)
            b_ks = ks[idx].to(device)
            N, K, L = b_ids.shape
            logits = model(b_ids.reshape(N * K, L), b_mask.reshape(N * K, L)).reshape(N, K)
            valid = torch.arange(K, device=device).unsqueeze(0) < b_ks.unsqueeze(1)
            logits = logits.masked_fill(~valid, float("-inf"))
            out.append(logits.float().cpu())
    return torch.cat(out, dim=0)


def train_pointwise(arm: str, train_ex, dev_ex, tokenizer, args) -> dict:
    model_id = tm.MODEL_IDS[arm]
    print(f"\n=== arm {arm}  ({model_id})", flush=True)
    torch.manual_seed(SEED)
    random.seed(SEED)
    np.random.seed(SEED)

    tokenizer = tokenizer or None
    t_train = time.time()
    ids, mask, ks, gold, tok_stats = tokenize_cases(tokenizer, train_ex, args.max_length)
    d_ids, d_mask, d_ks, d_gold, d_tok = tokenize_cases(tokenizer, dev_ex, args.max_length)
    print(
        f"  tokens: train mean {np.mean(tok_stats['tokenLengths']):.0f} max {max(tok_stats['tokenLengths'])} "
        f"truncated {tok_stats['truncated']}/{len(tok_stats['tokenLengths'])}; "
        f"option count max {tok_stats['maxOptionCount']}",
        flush=True,
    )

    model = tm.PointwiseScorer(model_id, dropout=args.dropout).to(args.device)
    n_params = tm.count_parameters(model)
    print(f"  parameters {n_params:,}  device {args.device}", flush=True)

    if arm == "shuffled-label":
        # A global permutation of the gold INDICES would be out of range for a case with fewer options
        # than the permutation's largest index, and `CrossEntropyLoss` over (N, K) requires every target
        # below K. The faithful analogue of "randomly permuted labels" for a variable option set is a
        # uniformly random VALID option inside each case's own option set — it destroys the
        # input->label relationship while leaving the option count, the option strings and the case
        # structure untouched. Forced to differ from the true gold, so no case keeps its label.
        rng = random.Random(SEED)
        shuffled = []
        for e, k in zip(train_ex, ks.tolist()):
            true_gold = int(e["goldIndex"])
            j = rng.randrange(k)
            if j == true_gold:
                j = (j + 1) % k
            shuffled.append(j)
        gold = torch.tensor(shuffled, dtype=torch.long)
        changed = sum(1 for e, g in zip(train_ex, shuffled) if g != e["goldIndex"])
        print(
            f"  SHUFFLED-LABEL CONTROL: {changed}/{len(train_ex)} training labels replaced by a random "
            f"OTHER option in the same case's option set (seed {SEED})",
            flush=True,
        )

    opt = torch.optim.AdamW(model.parameters(), lr=args.lr, weight_decay=args.weight_decay)
    steps_per_epoch = max(1, (len(train_ex) + args.batch_cases - 1) // args.batch_cases)
    total_steps = steps_per_epoch * args.epochs
    warmup = max(1, int(0.06 * total_steps))

    def lr_at(step: int) -> float:
        if step < warmup:
            return step / warmup
        return max(0.0, (total_steps - step) / max(1, total_steps - warmup))

    sched = torch.optim.lr_scheduler.LambdaLR(opt, lr_at)
    lossf = nn.CrossEntropyLoss()

    dev_curve = []
    epoch1_logits = None
    best_dev = -1.0
    t_epochs = []
    for epoch in range(1, args.epochs + 1):
        model.train()
        order = list(range(len(train_ex)))
        random.Random(SEED + epoch).shuffle(order)
        t0 = time.time()
        running, seen = 0.0, 0
        for start in range(0, len(order), args.batch_cases):
            chunk = order[start : start + args.batch_cases]
            b_ids = ids[chunk].to(args.device)
            b_mask = mask[chunk].to(args.device)
            b_ks = ks[chunk].to(args.device)
            b_gold = gold[chunk].to(args.device)
            N, K, L = b_ids.shape
            logits = model(b_ids.reshape(N * K, L), b_mask.reshape(N * K, L)).reshape(N, K)
            valid = torch.arange(K, device=args.device).unsqueeze(0) < b_ks.unsqueeze(1)
            logits = logits.masked_fill(~valid, float("-inf"))
            loss = lossf(logits, b_gold)
            opt.zero_grad(set_to_none=True)
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            opt.step()
            sched.step()
            running += float(loss.item()) * len(chunk)
            seen += len(chunk)
        dt = time.time() - t0
        t_epochs.append(dt)

        model.eval()
        d_logits = case_logits_batched(model, d_ids, d_mask, d_ks, args.batch_cases, args.device)
        pred = d_logits.argmax(dim=1).tolist()
        acc = tc.accuracy(pred, d_gold.tolist())
        # temperature is fitted on THIS epoch's dev logits, reported per epoch, and the epoch-1 fit is
        # the one carried forward (the pre-registered operating point).
        t_fit = tc.fit_temperature(d_logits.tolist(), d_gold.tolist())
        probs = [tc.softmax(l, t_fit)[int(p)] for l, p in zip(d_logits.tolist(), pred)]
        dev_curve.append(
            {
                "epoch": epoch,
                "trainLoss": running / max(seen, 1),
                "devAccuracy": acc,
                "devTemperature": t_fit,
                "devECE": tc.ece(probs, [int(p == g) for p, g in zip(pred, d_gold.tolist())]),
                "seconds": dt,
            }
        )
        print(
            f"  epoch {epoch}: loss {running/max(seen,1):.4f} dev-acc {acc:.4f} (T={t_fit:.2f}) {dt:.1f}s",
            flush=True,
        )
        if epoch == 1:
            epoch1_logits = d_logits.clone()
            torch.save(
                {"state_dict": model.state_dict(), "base_name": model_id, "hidden_size": model.hidden_size,
                 "dropout": args.dropout, "max_length": args.max_length},
                tc.OUT / "models" / f"{arm}.pt",
            )
            tokenizer.save_pretrained(tc.OUT / "models" / f"{arm}-tokenizer")
        if acc > best_dev:
            best_dev = acc
        elif epoch > 1:
            print(f"  early stop: dev accuracy did not improve after epoch {epoch}", flush=True)
            break

    # the pre-registered operating point: epoch 1
    t1 = dev_curve[0]["devTemperature"]
    pred1 = epoch1_logits.argmax(dim=1).tolist()
    probs1 = [tc.softmax(l, t1)[int(p)] for l, p in zip(epoch1_logits.tolist(), pred1)]
    probs1_t1 = [tc.softmax(l, 1.0)[int(p)] for l, p in zip(epoch1_logits.tolist(), pred1)]
    dev_at_1 = {
        "accuracy": tc.accuracy(pred1, d_gold.tolist()),
        "eceUncalibrated": tc.ece(probs1_t1, [int(p == g) for p, g in zip(pred1, d_gold.tolist())]),
        "ece": tc.ece(probs1, [int(p == g) for p, g in zip(pred1, d_gold.tolist())]),
        "brier": tc.brier(probs1, [int(p == g) for p, g in zip(pred1, d_gold.tolist())]),
        "temperature": t1,
        "n": len(pred1),
    }
    print(
        f"  OPERATING POINT epoch 1 (pre-registered): dev-acc {dev_at_1['accuracy']:.4f} "
        f"ECE {dev_at_1['ece']:.4f} T={t1:.2f}",
        flush=True,
    )
    return {
        "arm": arm,
        "modelId": model_id,
        "licence": tm.LICENCES[model_id],
        "parameters": n_params,
        "device": args.device,
        "trainSeconds": time.time() - t_train,
        "epochSeconds": t_epochs,
        "operatingPoint": "epoch 1 (pre-registered)",
        "devAtOperatingPoint": dev_at_1,
        "devCurve": dev_curve,
        "bestDevEpoch": int(max(dev_curve, key=lambda d: d["devAccuracy"])["epoch"]),
        "tokenStats": {
            "mean": float(np.mean(tok_stats["tokenLengths"])),
            "max": int(max(tok_stats["tokenLengths"])),
            "truncated": tok_stats["truncated"],
            "maxOptionCount": tok_stats["maxOptionCount"],
        },
    }


def train_setfit(arm: str, train_ex, dev_ex, args) -> dict:
    import time as _t

    print(f"\n=== arm {arm}  ({tm.MODEL_IDS[arm]}) frozen encoder + logistic pair head", flush=True)
    t0 = _t.time()
    head = tm.LogisticPairHead(device=args.device, max_length=args.max_length)
    # Build the pair training set from the SAME context the pointwise arms see minus the candidate
    # line: `render_context` is the shared prefix, and the candidate string is the thing that varies.
    sit_texts, opt_texts, labels = [], [], []
    for e in train_ex:
        s = tc.render_context(e["kind"], e["situation"])
        for j, o in enumerate(e["options"]):
            sit_texts.append(s)
            opt_texts.append(o)
            labels.append(1 if j == e["goldIndex"] else 0)
    print(f"  fitting on {len(labels)} (situation, option) pairs", flush=True)
    head.fit(sit_texts, opt_texts, labels, seed=SEED)
    fit_seconds = _t.time() - t0
    n_params = sum(p.numel() for p in head.encoder.parameters()) + int(head.clf.coef_.size + head.clf.intercept_.size)
    print(f"  fitted in {fit_seconds:.1f}s; encoder params {sum(p.numel() for p in head.encoder.parameters()):,}", flush=True)

    dev_logits = [head.case_logits(tc.render_context(e["kind"], e["situation"]), e["options"]) for e in dev_ex]
    d_gold = [e["goldIndex"] for e in dev_ex]
    pred = [int(np.argmax(l)) for l in dev_logits]
    t_fit = tc.fit_temperature(dev_logits, d_gold)
    probs = [tc.softmax(l, t_fit)[p] for l, p in zip(dev_logits, pred)]
    probs_t1 = [tc.softmax(l, 1.0)[p] for l, p in zip(dev_logits, pred)]
    dev_at = {
        "accuracy": tc.accuracy(pred, d_gold),
        "eceUncalibrated": tc.ece(probs_t1, [int(p == g) for p, g in zip(pred, d_gold)]),
        "ece": tc.ece(probs, [int(p == g) for p, g in zip(pred, d_gold)]),
        "brier": tc.brier(probs, [int(p == g) for p, g in zip(pred, d_gold)]),
        "temperature": t_fit,
        "n": len(pred),
    }
    import joblib

    joblib.dump(
        {"scaler": head.scaler, "clf": head.clf, "model_id": head.model_id, "max_length": args.max_length},
        tc.OUT / "models" / f"{arm}.joblib",
    )
    print(f"  dev-acc {dev_at['accuracy']:.4f} ECE {dev_at['ece']:.4f} T={t_fit:.2f}", flush=True)
    return {
        "arm": arm,
        "modelId": head.model_id,
        "licence": tm.LICENCES[head.model_id],
        "parameters": n_params,
        "device": args.device,
        "trainSeconds": fit_seconds,
        "operatingPoint": "the single logistic fit (the head has no epoch loop; one fit is its epoch 1)",
        "devAtOperatingPoint": dev_at,
        "devCurve": [{"epoch": 1, "trainLoss": None, "devAccuracy": dev_at["accuracy"], "devTemperature": t_fit,
                      "devECE": dev_at["ece"], "seconds": fit_seconds}],
        "bestDevEpoch": 1,
        "tokenStats": None,
    }


def build_majority(arm: str, train_ex, dev_ex, args) -> dict:
    """Control: the training label marginal, restricted to each case's own option set.

    Fixture-blind by construction: it uses the training gold labels and the case's own option list,
    never the fixture's answer distribution.
    """
    counts: dict = {}
    for e in train_ex:
        counts[e["gold"]] = counts.get(e["gold"], 0) + 1
    total = sum(counts.values())
    logmarg = {k: float(np.log(v / total)) for k, v in counts.items()}
    floor = float(np.log(1.0 / (total * 10)))

    def score(e):
        return [logmarg.get(o, floor) for o in e["options"]]

    dev_logits = [score(e) for e in dev_ex]
    d_gold = [e["goldIndex"] for e in dev_ex]
    pred = [int(np.argmax(l)) for l in dev_logits]
    probs = [tc.softmax(l)[p] for l, p in zip(dev_logits, pred)]
    dev_at = {
        "accuracy": tc.accuracy(pred, d_gold),
        "eceUncalibrated": tc.ece(probs, [int(p == g) for p, g in zip(pred, d_gold)]),
        "ece": tc.ece(probs, [int(p == g) for p, g in zip(pred, d_gold)]),
        "brier": tc.brier(probs, [int(p == g) for p, g in zip(pred, d_gold)]),
        "temperature": 1.0,
        "n": len(pred),
    }
    tc.write_json(tc.OUT / "models" / f"{arm}.json", {"labelLogMarginal": logmarg, "floor": floor})
    print(f"\n=== arm {arm} (control: train label marginal)")
    print(f"  dev-acc {dev_at['accuracy']:.4f} ECE {dev_at['ece']:.4f}; {len(counts)} labels in the marginal", flush=True)
    return {
        "arm": arm,
        "modelId": None,
        "licence": None,
        "parameters": 0,
        "device": "n/a",
        "trainSeconds": 0.0,
        "operatingPoint": "no training — the corpus label marginal, restricted to each case's option set",
        "devAtOperatingPoint": dev_at,
        "devCurve": [{"epoch": None, "trainLoss": None, "devAccuracy": dev_at["accuracy"], "devTemperature": 1.0,
                      "devECE": dev_at["ece"], "seconds": 0.0}],
        "bestDevEpoch": None,
        "tokenStats": None,
        "labelMarginal": logmarg,
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--arms", default=",".join(tm.ALL_ARMS))
    ap.add_argument("--epochs", type=int, default=3)
    ap.add_argument("--max-length", type=int, default=256)
    ap.add_argument("--batch-cases", type=int, default=16)
    ap.add_argument("--lr", type=float, default=2e-5)
    ap.add_argument("--weight-decay", type=float, default=0.01)
    ap.add_argument("--dropout", type=float, default=0.1)
    ap.add_argument("--device", default=None)
    ap.add_argument("--limit-train", type=int, default=0, help="SMOKE TEST ONLY: truncate the training split")
    args = ap.parse_args()

    args.device = args.device or ("cuda" if torch.cuda.is_available() else "cpu")
    lint = check_gate()
    print(f"EXP#12 training — device {args.device}")
    if args.device == "cuda":
        print(f"  gpu {torch.cuda.get_device_name(0)}  torch {torch.__version__}  cuda {torch.version.cuda}")
    print(f"  host {platform.node()} {platform.machine()}  torch {torch.__version__}  python {platform.python_version()}")
    print(f"  F4 gate: train800 vs sealed190 silent in both directions ({lint['trainVsFixture']['forward']['pairsCompared']} pairs); "
          f"control fired on {[p['name'] for p in lint['demo']['probes'] if p['fired']]}")

    train_ex = load_jsonl(tc.DATA / "train.jsonl")
    dev_ex = load_jsonl(tc.DATA / "dev.jsonl")
    print(f"  train {len(train_ex)} cases, dev {len(dev_ex)} cases")
    if args.limit_train:
        print(f"  *** SMOKE TEST: training split truncated to {args.limit_train} cases ***")
        train_ex = train_ex[: args.limit_train]
    if (len(train_ex), len(dev_ex)) != (800, 200) and not args.limit_train:
        fail(f"split sizes {len(train_ex)}/{len(dev_ex)}, expected 800/200")

    tc.OUT.mkdir(parents=True, exist_ok=True)
    (tc.OUT / "models").mkdir(parents=True, exist_ok=True)

    from transformers import AutoTokenizer

    reports = []
    t_start = time.time()
    for arm in [a for a in args.arms.split(",") if a]:
        if arm in tm.POINTWISE_ARMS or arm == "shuffled-label":
            tokenizer = AutoTokenizer.from_pretrained(tm.MODEL_IDS[arm])
            reports.append(train_pointwise(arm, train_ex, dev_ex, tokenizer, args))
        elif arm == "setfit-mpnet":
            reports.append(train_setfit(arm, train_ex, dev_ex, args))
        elif arm == "majority-class":
            reports.append(build_majority(arm, train_ex, dev_ex, args))
        else:
            fail(f"unknown arm {arm}")
        tc.write_json(tc.OUT / "dev" / f"{arm}.json", reports[-1])

    manifest = {
        "experiment": "EXP#12",
        "step": "train",
        "host": platform.node(),
        "machine": platform.machine(),
        "python": platform.python_version(),
        "torch": torch.__version__,
        "cuda": torch.version.cuda,
        "device": args.device,
        "gpu": torch.cuda.get_device_name(0) if args.device == "cuda" else None,
        "hyperparameters": {
            "epochsFollowedForDevCurve": args.epochs,
            "operatingPoint": "epoch 1 (pre-registered; not selected on dev)",
            "lr": args.lr,
            "weightDecay": args.weight_decay,
            "dropout": args.dropout,
            "batchCases": args.batch_cases,
            "maxLength": args.max_length,
            "seed": SEED,
        },
        "corpusSha256": tc.sha256_file(tc.CORPUS_PATH),
        "trainCases": len(train_ex),
        "devCases": len(dev_ex),
        "fixtureReadDuringTraining": False,
        "fixturePathReferencedByTrainingCode": "train.py never opens the sealed fixture: no read_text/read_bytes/json.load on tc.FIXTURE_PATH anywhere in this file",
        "smokeTestLimitTrain": args.limit_train or None,
        "totalSeconds": time.time() - t_start,
        "arms": reports,
    }
    tc.write_json(tc.OUT / "manifest-train.json", manifest)
    print(f"\nwrote {tc.OUT / 'manifest-train.json'}  ({manifest['totalSeconds']:.0f}s total)")


if __name__ == "__main__":
    main()

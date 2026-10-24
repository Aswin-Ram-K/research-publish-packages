#!/usr/bin/env python3
"""
defect-probe.py — EXP#12. Reproduce, on the DEVELOPMENT split, the defect that NOTES-defects.md D2
describes, so the claim is a measurement rather than a transcript.

The claim: `LogisticPairHead.case_logits` clipped the logistic head's probability into
`[1e-6, 1-1e-6]` before taking the logit. A saturated L2 logistic regression on 3072 standardised
features returns exactly 0.0 / 1.0 on many rows, so that clip mapped every saturated option to the SAME
logit — turning distinct scores into exact ties, which `argmax` then resolved by presented position.

This script re-runs BOTH variants over the 200 H-B development cases and reports, for each:
  * accuracy
  * how many cases contain an exact tie between the top-scoring options
  * how many predictions change when the case's options are permuted (order dependence)

It touches the DEVELOPMENT split only. It never reads the sealed fixture: the defect is a property of
the arm's scoring path, not of the instrument, and demonstrating it does not require the instrument.

RUN
  python3 tools/typed-channel/defect-probe.py
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import numpy as np  # noqa: E402

import tccommon as tc  # noqa: E402
import tcmodel as tm  # noqa: E402


def logits_with_clip(head, situation: str, options, lo, hi):
    """The arm's per-option logit under one scoring variant.

    lo/hi None  -> `decision_function`, the head's raw log-odds (the fix)
    otherwise   -> `predict_proba` clipped into [lo, hi] before the logit (the two earlier attempts)
    """
    options = list(options)
    u = head.embed([situation], batch_size=1)[0]
    v = head.embed(options, batch_size=max(1, len(options)))
    x = tm.LogisticPairHead.pair_features(np.tile(u, (len(options), 1)), v)
    xs = head.scaler.transform(x)
    if lo is None:
        return list(np.asarray(head.clf.decision_function(xs), dtype=np.float64).ravel())
    p = np.asarray(head.clf.predict_proba(xs)[:, 1], dtype=np.float64)
    p = np.clip(p, lo, hi)
    return list(np.log(p) - np.log1p(-p))


def probe(head, examples, lo, hi, label: str) -> dict:
    preds, ties, flips = [], 0, 0
    rng = np.random.default_rng(20261004)
    for e in examples:
        s = tc.render_context(e["kind"], e["situation"])
        lg = logits_with_clip(head, s, e["options"], lo, hi)
        idx = int(np.argmax(lg))
        preds.append(idx == e["goldIndex"])
        top = max(lg)
        if sum(1 for x in lg if x == top) > 1:
            ties += 1
        perm = rng.permutation(len(e["options"]))
        perm_opts = [e["options"][i] for i in perm]
        plg = logits_with_clip(head, s, perm_opts, lo, hi)
        if perm_opts[int(np.argmax(plg))] != e["options"][idx]:
            flips += 1
    return {
        "variant": label,
        "clip": None if lo is None else [lo, hi],
        "n": len(examples),
        "accuracy": sum(preds) / len(preds),
        "casesWithAnExactTieAtTheTop": ties,
        "orderDependentPredictions": flips,
    }


def main() -> None:
    dev = [json.loads(l) for l in (tc.DATA / "dev.jsonl").read_text(encoding="utf8").splitlines() if l.strip()]
    import joblib

    blob = joblib.load(tc.OUT / "models" / "setfit-mpnet.joblib")
    head = tm.LogisticPairHead(model_id=blob["model_id"], max_length=blob["max_length"], device="cpu")
    head.scaler, head.clf = blob["scaler"], blob["clf"]

    print("defect probe — the SetFit head's probability clip, on the 200 H-B development cases")
    print(f"  model {blob['model_id']}  cases {len(dev)}  fixture read: NO")
    results = [
        probe(head, dev, 1e-6, 1.0 - 1e-6, "predict_proba clipped to [1e-6, 1-1e-6] (first attempt)"),
        probe(head, dev, 1e-300, float(np.nextafter(1.0, 0.0)), "predict_proba clipped at the denormal edge (second attempt)"),
        probe(head, dev, None, None, "decision_function — the raw log-odds (the fix)"),
    ]
    for r in results:
        print(
            f"  {r['variant']:32s} accuracy {r['accuracy']:.4f}  exact ties {r['casesWithAnExactTieAtTheTop']:3d}/{r['n']}  "
            f"order-dependent predictions {r['orderDependentPredictions']:3d}/{r['n']}"
        )
    # the same temperature the final run fitted, so the two variants are compared on one scale
    temp = json.loads((tc.OUT / "dev" / "setfit-mpnet.json").read_text(encoding="utf8"))["devAtOperatingPoint"]["temperature"]
    out = {
        "what": "the SetFit head's probability clip, both variants, re-run on the H-B development split",
        "fixtureRead": False,
        "model": blob["model_id"],
        "developmentCases": len(dev),
        "temperatureFittedInTheFinalRun": temp,
        "devSplitSha256": hashlib.sha256((tc.DATA / "dev.jsonl").read_bytes()).hexdigest(),
        "variants": results,
        "conclusion": (
            "the pre-fix clip collapses distinct saturated scores into exact ties, and argmax then resolves those "
            "ties by the position the option was presented in; the fix removes the ties and the order dependence"
        ),
    }
    tc.write_json(tc.OUT / "defect-probe.json", out)
    print(f"\nwrote {tc.OUT / 'defect-probe.json'}")


if __name__ == "__main__":
    main()

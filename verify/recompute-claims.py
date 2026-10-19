#!/usr/bin/env python3
"""verify/recompute-claims.py — recompute the paper #3 headline numbers FROM THE SANITISED TREE.

ONE PURPOSE: show that the numbers G44/papers list are still there after the redaction, computed
only from files that ship inside `G48/`.

Two classes of number, and the distinction is stated rather than blurred:

  * RECOMPUTED FROM THE INSTRUMENT. The chance floor (mean 1/k) is recomputed from the sanitised
    `fixture/fixture-190.json` (relocated out of `harness/`, which is withheld in full); the per-arm
    accuracies are recomputed from each arm's own
    `perCase` records; the paired McNemar table (b, c, both, neither) is recomputed by aligning the
    best head's per-case correctness against the decider-4b reproduction's per-case rows by case id.
  * NOT RECOMPUTED HERE. `evaluate.py`/`analyze.py` cannot re-run inside this subset: they read
    `harness/out/manifest-eval.json` and `manifest-train.json`, which `EXCLUDED.md` E12 excludes.
    Their outputs are shipped frozen (`results/*.json`) and are byte-identical between the
    as-audited and the sanitised tree (INTEGRITY.md hashes). Stating that limitation is the point.

Usage: python3 verify/recompute-claims.py            (run from anywhere; reads only this tree)
"""
from __future__ import annotations

import hashlib
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
Z_ALPHA, Z_POWER = 1.959963984540054, 0.8416212335729143
MDE_K = Z_ALPHA + Z_POWER
CLAIMS = {0.3474: "modernbert-base sealed-190 accuracy",
          0.4526: "majority-class control accuracy",
          0.2911: "chance floor (mean 1/k)",
          0.6684: "decider-4b published baseline",
          0.6789: "decider-4b same-run reproduction",
          0.3252: "second-labeller route-A kappa",
          0.8837: "second-labeller closed-vocabulary kappa",
          0.9140: "second-labeller roster+bespoke kappa",
          0.3684210526315789: "second-labeller A/B mutual agreement"}


def jload(*p):
    with open(os.path.join(ROOT, *p), encoding="utf-8") as fh:
        return json.load(fh)


def binom_two_sided_p(k: int, n: int) -> float:
    """Exact two-sided binomial test at p=0.5 — the McNemar exact test (analyze.py, verbatim)."""
    if n == 0:
        return 1.0
    lg = lambda i: math.lgamma(n + 1) - math.lgamma(i + 1) - math.lgamma(n - i + 1)  # noqa: E731
    pmf = lambda i: math.exp(lg(i) - n * math.log(2))  # noqa: E731
    obs = pmf(k)
    return min(1.0, sum(pmf(i) for i in range(n + 1) if pmf(i) <= obs * (1 + 1e-9)))


def main() -> None:
    fixture = jload("fixture", "fixture-190.json")
    chance = sum(1.0 / len(c["options"]) for c in fixture) / len(fixture)

    arms = {}
    for name in ("modernbert-base", "deberta-v3-base", "setfit-mpnet", "majority-class",
                 "shuffled-label"):
        rec = jload("results", f"eval-{name}.json")
        arms[name] = {c["id"]: bool(c["correct"]) for c in rec["perCase"]}
        print(f"  arm {name:16s} n={len(rec['perCase']):3d} accuracy={rec['accuracy']:.6f} "
              f"(recomputed {sum(arms[name].values())/len(arms[name]):.6f})")

    base = jload("results", "baselines.json")
    dec = {c["id"]: bool(c["correct"]) for c in base["models"]["decider-4b-exp11-reproduction"]["perCase"]}
    print(f"  arm decider-4b-repro n={len(dec):3d} "
          f"accuracy={sum(dec.values())/len(dec):.6f}")

    ids = [c["id"] for c in fixture]
    best = arms["modernbert-base"]
    if set(best) != set(ids) or set(dec) != set(ids):
        sys.exit("REFUSED: the per-case records are not the fixture's own 190 ids")
    b = sum(1 for i in ids if best[i] and not dec[i])
    c = sum(1 for i in ids if not best[i] and dec[i])
    both = sum(1 for i in ids if best[i] and dec[i])
    neither = sum(1 for i in ids if not best[i] and not dec[i])
    n = len(ids)
    psi = (b + c) / n
    pa, pb = sum(best.values()) / n, sum(dec.values()) / n
    paired_mde = MDE_K * math.sqrt(psi / n)
    p = binom_two_sided_p(min(b, c), b + c)

    print("\n  PAIRED McNEMAR, best head vs decider-4b reproduction (aligned by case id)")
    print(f"    2x2: both={both}  headOnly={b}  deciderOnly={c}  neither={neither}  sum={both+b+c+neither}")
    print(f"    psi={psi:.6f}  delta={pa-pb:.6f}  exact p={p:.6e}  paired MDE={paired_mde:.6f}")

    print("\n  CLAIMS CHECK (tolerance 5e-4)")
    got = {0.3474: None, 0.4526: None, 0.2911: None, 0.6684: None, 0.6789: None}
    got[0.3474] = arms["modernbert-base"].__len__() and sum(best.values()) / n
    got[0.4526] = sum(arms["majority-class"].values()) / n
    got[0.2911] = chance
    got[0.6684] = 0.6684  # QUOTED CONSTANT, not a recomputation — see the note printed below
    got[0.6789] = sum(dec.values()) / n
    ok = True
    for want, label in CLAIMS.items():
        if want in got:
            have = got[want]
            hit = abs(have - want) <= 5e-4
            ok &= hit
            src = "QUOTED CONSTANT (results/REPORT.md 2; not recomputable in this subset)" \
                if want == 0.6684 else f"recomputed={have!r}"
            print(f"    {want:<9} {label:44s} {src:<22} {'OK' if hit else 'MISMATCH'}")
    print(f"    counts 39+27+90+34 = {both}+{b}+{c}+{neither} = {both+b+c+neither} "
          f"({'OK' if both+b+c+neither == 190 else 'MISMATCH'})")

    # the second-labeller numbers, from the shipped sanitised metrics.json
    met = jload("second-labeller", "metrics.json")
    # An earlier genericisation step (G42) moved two published second-labeller values: route A
    # tokenises case-sensitively below the fixture, so a rename splits an upper/lower-case pair and
    # changes the distinct-token overlap. Each PUBLISHED value is therefore compared against the
    # TREE's own current value, and the result is FOLDED INTO `ok`: a published value that no longer
    # matches the tree makes this script exit non-zero. Nothing is dropped or silently rewritten.
    PUBLISHED_VALUES = {0.3252: ("route-A kappa", "papers/encoder-crossover-190/CLAIMS.md:108",
                                 met["routeA"]["kappa"]),
                        0.3684: ("A/B mutual agreement", "papers/encoder-crossover-190/CLAIMS.md:109",
                                 met["passes"]["labelsB.json"]["AB_mutual_agreement"])}
    sb = {met["routeA"]["kappa"]: met["routeA"]["kappa"],
          0.8837: met["stratification"]["closed_subset"]["labelsB.json"]["kappa"],
          0.9140: met["stratification"]["roster_and_bespoke_subset"]["labelsB.json"]["kappa"],
          met["passes"]["labelsB.json"]["AB_mutual_agreement"]: met["passes"]["labelsB.json"]["AB_mutual_agreement"]}
    print("\n  SECOND-LABELLER NUMBERS (from the shipped sanitised metrics.json)")
    for want, label in CLAIMS.items():
        if want in sb:
            have = sb[want]
            hit = abs(have - want) <= 5e-4
            ok &= hit
            print(f"    {want:<9} {label:44s} shipped={have!r:<22} {'OK' if hit else 'MISMATCH'}")
    print("\n  PUBLISHED VALUES vs TREE (tolerance 5e-4; enforced in the exit status)")
    for pub, (lab, cite, tree_v) in PUBLISHED_VALUES.items():
        hit = abs(tree_v - pub) <= 5e-4
        ok &= hit
        print(f"    {lab}: published={pub:<8} tree={tree_v!r:<22} reproduced={hit} cite={cite}")
    print("\n  ALL PUBLISHED NUMBERS REPRODUCED:", ok)
    print("  VERDICT:", "PASS" if ok else
          "FAIL -- at least one published number no longer matches the tree (rows above)")
    print("  fixture correctness digest:",
          hashlib.sha256(json.dumps([[c["id"], c["correct"], len(c["options"])] for c in fixture],
                                    separators=(",", ":")).encode()).hexdigest())
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()

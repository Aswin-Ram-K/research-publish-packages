#!/usr/bin/env python3
"""G33 steps 4-5, v2: Route A (pre-registered deterministic rule) plus every blind machine
pass found as labelsB*.json, compared against the recorded labels.

Writes metrics.json and disagreements.jsonl (catalogue keyed on the PRIMARY pass,
labelsB.json). Re-runnable. Route A is a transcription of PREREGISTRATION.md section 2 and
must not be edited after the first comparison run.
"""
import glob
import json
import os
import re
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
TOKEN = re.compile(r"[a-z0-9]+")
WS = re.compile(r"\s+")


def norm(s: str) -> str:
    return WS.sub(" ", s.strip().lower())


def route_a(question: str, options):
    """PREREGISTRATION.md s2 verbatim: distinct-token overlap + 0.5 substring bonus,
    argmax, ties -> lowest index."""
    tq = set(TOKEN.findall(question.lower()))
    nq = norm(question)
    scores = []
    for o in options:
        ot = set(TOKEN.findall(o.lower()))
        s = float(len(ot & tq))
        if norm(o) and norm(o) in nq:
            s += 0.5
        scores.append(s)
    best = max(scores)
    return scores.index(best), scores.count(best) > 1, scores


def kappa(a, b):
    n = len(a)
    po = sum(x == y for x, y in zip(a, b)) / n
    ca, cb = Counter(a), Counter(b)
    pe = sum(ca[l] * cb[l] for l in set(ca) | set(cb)) / (n * n)
    return po, pe, (None if pe == 1 else (po - pe) / (1 - pe))


def main():
    cases = json.load(open(os.path.join(HERE, "cases.json"), encoding="utf-8"))
    n = len(cases)
    by_id = {c["id"]: c for c in cases}

    A_idx, A_tie, A_scores = [], [], []
    for c in cases:
        i, tie, sc = route_a(c["question"], c["options"])
        A_idx.append(i)
        A_tie.append(tie)
        A_scores.append(sc)

    recorded_idx = [c["correct"] for c in cases]
    rec_lbl = [c["options"][c["correct"]] for c in cases]
    A_lbl = [c["options"][A_idx[k]] for k, c in enumerate(cases)]

    poA, peA, kA = kappa(rec_lbl, A_lbl)
    metrics = {
        "cases": n,
        "options_total": sum(len(c["options"]) for c in cases),
        "routeA": {
            "agreement": poA, "po": poA, "pe": peA, "kappa": kA,
            "exact_index_matches": sum(x == y for x, y in zip(recorded_idx, A_idx)),
            "ties": sum(A_tie),
            "zero_score_cases": sum(1 for s in A_scores if max(s) == 0),
            "rule": "PREREGISTRATION.md s2: distinct-token overlap + 0.5 substring bonus, argmax, ties->lowest index",
        },
    }

    # ---- every blind machine pass present ------------------------------------
    passes = {}
    for path in sorted(glob.glob(os.path.join(HERE, "labelsB*.json"))):
        name = os.path.basename(path)
        blob = json.load(open(path, encoding="utf-8"))
        labels = blob["labels"] if isinstance(blob, dict) and "labels" in blob else blob
        missing = [cid for cid in by_id if cid not in labels]
        extra = [cid for cid in labels if cid not in by_id]
        bad = [cid for cid, v in labels.items()
               if cid in by_id and not (isinstance(v, int) and 0 <= v < len(by_id[cid]["options"]))]
        idx = []
        for c in cases:
            v = labels.get(c["id"])
            idx.append(v if isinstance(v, int) and 0 <= v < len(c["options"]) else None)
        ok = [k for k, v in enumerate(idx) if v is not None]
        pl = [cases[k]["options"][idx[k]] for k in ok]
        po, pe, kk = kappa([rec_lbl[k] for k in ok], pl)
        passes[name] = {
            "file": name,
            "labeller": blob.get("labeller") if isinstance(blob, dict) else "unknown",
            "ids_missing": missing, "ids_extra": extra, "labels_out_of_range": bad,
            "labelable": len(ok),
            "agreement": po, "po": po, "pe": pe, "kappa": kk,
            "exact_index_matches": sum(recorded_idx[k] == idx[k] for k in ok),
            "n_disagreements": len(ok) - sum(recorded_idx[k] == idx[k] for k in ok),
            "AB_mutual_agreement": sum(A_idx[k] == idx[k] for k in ok) / len(ok),
            "disagreements_where_routeA_backs_record": sum(
                1 for k in ok if idx[k] != recorded_idx[k] and A_idx[k] == recorded_idx[k]),
            "_idx": idx,
        }
    metrics["passes"] = {k: {kk: vv for kk, vv in v.items() if kk != "_idx"}
                         for k, v in passes.items()}

    # ---- POST-HOC stratification (disclosed as post-hoc in EVIDENCE.md) -------
    # Pooled kappa is computed over the whole label vocabulary, but that vocabulary is
    # heterogeneous: some kinds draw from a small shared option roster, others give every case
    # its own bespoke option strings (51 of 74 labels occur exactly once). Pooled kappa over
    # mostly-singleton categories is close to meaningless, so report agreement stratified.
    def stats(idxs, subset):
        a = [rec_lbl[k] for k in subset]
        b = [cases[k]["options"][idxs[k]] for k in subset]
        po, pe, kk = kappa(a, b)
        return {"n": len(subset), "agreement": po, "pe": pe, "kappa": kk,
                "exact_index_matches": sum(recorded_idx[k] == idxs[k] for k in subset)}

    kinds = sorted({c["kind"] for c in cases})
    distinct_opts = {k: len({o for c in cases if c["kind"] == k for o in c["options"]})
                     for k in kinds}
    closed = [k for k in kinds if distinct_opts[k] <= 8]
    rest = [k for k in kinds if k not in closed]
    idxsets = {"routeA": A_idx}
    for name, p in passes.items():
        idxsets[name] = p["_idx"]
    strat = {"note": "POST-HOC addition; the metrics are the pre-registered ones applied to subsets",
             "closed_vocabulary_definition":
                 "a kind whose distinct option strings across all its cases is <= 8",
             "distinct_options_per_kind": distinct_opts,
             "closed_vocabulary_kinds": closed,
             "closed_vocabulary_cases": sum(1 for c in cases if c["kind"] in closed),
             "roster_and_bespoke_kinds": rest,
             "per_kind": {}, "closed_subset": {}, "roster_and_bespoke_subset": {}}
    for k in kinds:
        sub = [i for i, c in enumerate(cases) if c["kind"] == k]
        strat["per_kind"][k] = {n: stats(ix, sub) for n, ix in idxsets.items()
                                if all(ix[i] is not None for i in sub)}
    for nm, sel in (("closed_subset", closed), ("roster_and_bespoke_subset", rest)):
        sub = [i for i, c in enumerate(cases) if c["kind"] in sel]
        strat[nm] = {n: stats(ix, sub) for n, ix in idxsets.items()
                     if all(ix[i] is not None for i in sub)}
    metrics["stratification"] = strat

    primary = passes.get("labelsB.json")
    if primary:
        metrics["routeB_primary"] = {kk: vv for kk, vv in primary.items() if kk != "_idx"}
        # ---- full disagreement catalogue, keyed on the primary pass -----------
        rows = []
        for k, c in enumerate(cases):
            b = primary["_idx"][k]
            if b is None or b == c["correct"]:
                continue
            row = {
                "id": c["id"], "kind": c["kind"],
                "question": c["question"], "options": c["options"],
                "recorded_index": c["correct"],
                "recorded_label": c["options"][c["correct"]],
                "F22": b, "F40": c["options"][b],
                "F56": A_idx[k], "F30": A_lbl[k],
                "routeA_agrees_with_record": A_idx[k] == c["correct"],
                "routeA_agrees_with_routeB": A_idx[k] == b,
                "recorded_rationale": c["rationale"],
                "line": c["_line"],
            }
            for name, p in passes.items():
                if name != "labelsB.json" and p["_idx"][k] is not None:
                    row["cross_" + name.replace("labels", "").replace(".json", "")] = {
                        "index": p["_idx"][k], "label": c["options"][p["_idx"][k]],
                        "agrees_with_record": p["_idx"][k] == c["correct"],
                        "agrees_with_routeB": p["_idx"][k] == b}
            rows.append(row)
        with open(os.path.join(HERE, "disagreements.jsonl"), "w", encoding="utf-8") as fh:
            for r in rows:
                fh.write(json.dumps(r, ensure_ascii=False) + "\n")
        metrics["disagreements_count_routeB"] = len(rows)
        metrics["disagreement_kinds"] = dict(Counter(r["kind"] for r in rows).most_common())
        metrics["disagreements_where_routeA_backs_record"] = sum(
            1 for r in rows if r["routeA_agrees_with_record"])

    with open(os.path.join(HERE, "metrics.json"), "w", encoding="utf-8") as fh:
        json.dump(metrics, fh, indent=1)
    print(json.dumps(metrics, indent=1))


if __name__ == "__main__":
    main()

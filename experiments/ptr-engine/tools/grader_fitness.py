#!/usr/bin/env python3
"""grader_fitness.py - instrument-fitness control for the checkpoint grader.

Manufactures a hand-written probe corpus (ideal / paraphrased / wrong / negated /
omission answers) for every machine-gradable checkpoint of the LR-01 fixture
family, runs grade_v3 (R1) and grade_v4 (R2) on each probe through their real
CLIs, and tabulates both error directions with explicit denominators.

    python3 experiments/ptr-engine/tools/grader_fitness.py \
        [--out experiments/ptr-engine/measure/grader-fitness.json]

Offline, stdlib only, deterministic. Reads the graders and fixtures read-only.
"""
import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
LONGRUN = os.path.join(ROOT, "experiments", "ptr-engine", "longrun")
G3 = os.path.join(LONGRUN, "grade_v3.py")
G4 = os.path.join(LONGRUN, "grade_v4.py")

FIXTURES = [
    "experiments/ptr-engine/longrun/fixtures/LR-01.json",
    "experiments/ptr-engine/longrun/tasks-v2/runtime-v2/LR-01.v2.json",
    "experiments/ptr-engine/longrun/tasks-v4/runtime-v4/LR-01.v4.json",
    "experiments/ptr-engine/longrun/tasks-v4/runtime-v4/LR-01.v4.tools2.json",
]

EV = "evidence"   # a probe's expected verdict under a mention-based definition

# intent:  correct   -> a grader that measures meaning must ACCEPT
#          incorrect -> a grader that measures meaning must REJECT
#          omission  -> correct in meaning but deliberately missing one required
#                       token; a mention grader SHOULD reject (control, not a rate)
PROBES = [
    # ---------------------------------------------------------- cp.0.t12 (number)
    dict(id="p.cp0.ideal", checkpoint="cp.0.t12", label="ideal", intent="correct",
         rows=[(12, "DEFAULT_MAX_REFS caps how many references one resolve turn may follow. In "
                    "resolve.py line 39 it is set to 64, and that is the default the resolver uses.\n\n"
                    "ANSWER: the default per-turn resolve budget is 64 refs.")]),
    dict(id="p.cp0.para", checkpoint="cp.0.t12", label="paraphrased", intent="correct",
         rows=[(12, "Reading resolve.py at line 39, the per-turn budget constant is 64 references.\n\n"
                    "ANSWER: 64.")]),
    dict(id="p.cp0.para_np", checkpoint="cp.0.t12", label="paraphrased-no-period",
         intent="correct",
         rows=[(12, "Reading resolve.py at line 39, the per-turn budget constant is 64 references.\n\n"
                    "ANSWER: 64")],
         note="minimal pair with p.cp0.para: identical except the final '.'"),
    dict(id="p.cp0.wrong", checkpoint="cp.0.t12", label="wrong-number", intent="incorrect",
         rows=[(12, "The budget in this checkout is much larger than the old note says.\n\n"
                    "ANSWER: 128 refs.")]),
    dict(id="p.cp0.neg", checkpoint="cp.0.t12", label="negation", intent="incorrect",
         rows=[(12, "The stale note claims 64, but that no longer holds for this checkout.\n\n"
                    "ANSWER: 64 is wrong; the default is 32 refs.")]),
    dict(id="p.cp0.omit", checkpoint="cp.0.t12", label="omission", intent="omission",
         rows=[(12, "DEFAULT_MAX_REFS is assigned at resolve.py:39 and consumed by the resolver.\n\n"
                    "ANSWER: sixty-four refs.")]),
    # ---------------------------------------------------------- cp.1.t24 (number)
    dict(id="p.cp1.ideal", checkpoint="cp.1.t24", label="ideal", intent="correct",
         rows=[(24, "Counting every 'class Ptr...' line in errors.py from line 15 to 250 gives the "
                    "class total.\n\nANSWER: errors.py defines 31 Ptr* error classes.")]),
    dict(id="p.cp1.para", checkpoint="cp.1.t24", label="paraphrased", intent="correct",
         rows=[(24, "A grep -c '^class Ptr' over errors.py returns 31 lines.\n\nANSWER: 31.")]),
    dict(id="p.cp1.wrong", checkpoint="cp.1.t24", label="wrong-number", intent="incorrect",
         rows=[(24, "The module is much smaller than the comments suggest.\n\n"
                    "ANSWER: 12 Ptr* error classes.")]),
    dict(id="p.cp1.neg", checkpoint="cp.1.t24", label="negation", intent="incorrect",
         rows=[(24, "A comment says 31 classes, but the file has fewer now.\n\n"
                    "ANSWER: 31 is stale; there are 29 Ptr* error classes.")]),
    dict(id="p.cp1.omit", checkpoint="cp.1.t24", label="omission", intent="omission",
         rows=[(24, "The Ptr* taxonomy is declared in errors.py from line 15 onward.\n\n"
                    "ANSWER: thirty-one classes.")]),
    # ---------------------------------------------------------- cp.2.t46 (prose)
    dict(id="p.cp2.ideal", checkpoint="cp.2.t46", label="ideal", intent="correct",
         rows=[(46, "_refuse hands the refusal to the ledger: it passes the scope, the serialized "
                    "reference taken from text, and error.code; the same exception is then propagated, "
                    "so the call sits immediately before re-raising.\n\nANSWER: it calls "
                    "ledger.record_refusal with scope, serialized_ref=text and code=error.code, then "
                    "re-raises the error.")]),
    dict(id="p.cp2.para", checkpoint="cp.2.t46", label="paraphrased", intent="correct",
         rows=[(46, "The exception is re-raised after the refusal is logged. What gets written is a "
                    "ledger.record_refusal entry carrying the scope, text as serialized_ref, and the "
                    "error.code value.\n\nANSWER: a ledger refusal row is written with scope, text as "
                    "serialized_ref and error.code before re-raising.")]),
    dict(id="p.cp2.wrong", checkpoint="cp.2.t46", label="wrong-symbol", intent="incorrect",
         rows=[(46, "_refuse only formats a message and returns; nothing is persisted.\n\n"
                    "ANSWER: it calls logger.warning and returns, with no ledger write.")]),
    dict(id="p.cp2.neg", checkpoint="cp.2.t46", label="negation", intent="incorrect",
         rows=[(46, "Nothing here needs recording: the scope, serialized_ref=text and code=error.code "
                    "are ignored and no ledger.record_refusal call happens; the error is swallowed "
                    "rather than re-raising.\n\nANSWER: do not call ledger.record_refusal; scope, "
                    "serialized_ref, text, code and error are irrelevant and no re-raising occurs.")]),
    dict(id="p.cp2.negr1gap", checkpoint="cp.2.t46", label="negation-verifier-E",
         intent="incorrect",
         rows=[(46, "ANSWER: do NOT call ledger.record_refusal; ignore scope, serialized_ref, text, "
                    "code and error entirely.")],
         note="V-ANCHOR-PREREG probe E verbatim: 8/8 R2 tokens, 8/9 R1 tokens"),
    dict(id="p.cp2.para_noraising", checkpoint="cp.2.t46", label="paraphrased-no-prose-anchor",
         intent="correct",
         rows=[(46, "The exception is re-raised after the refusal is logged. What gets written is a "
                    "ledger.record_refusal entry carrying the scope, text as serialized_ref, and the "
                    "error.code value.\n\nANSWER: the refusal is recorded via ledger.record_refusal "
                    "with scope, serialized_ref=text and code=error.code, then re-raised.")],
         note="same 8/9 token profile as probe E, correct meaning: the flip R2 is meant to buy"),
    dict(id="p.cp2.omit", checkpoint="cp.2.t46", label="omission", intent="omission",
         rows=[(46, "The refusal is recorded with the scope, the text and the error code, then the "
                    "exception propagates.\n\nANSWER: ledger.record_refusal(scope=scope_name, "
                    "text=text, code=error.code), before re-raising.")]),
    # ---------------------------------------------------------- repair.t30
    dict(id="p.rep.ideal", checkpoint="repair.t30", label="ideal", intent="correct",
         rows=[(30, "You are right that I assumed too much. Concretely: record the guard refusals "
                    "explicitly, and restore the typed guard deleted at turn 8 so the isinstance path "
                    "is covered again.\n\nANSWER: I will restore the typed guard deleted at turn 8 "
                    "and record the guard refusals explicitly.")]),
    dict(id="p.rep.para", checkpoint="repair.t30", label="paraphrased", intent="correct",
         rows=[(30, "The typed guard deleted at turn 8 has to go back in; I will restore it, and the "
                    "guard refusals get an explicit test instead of relying on the ledger path.\n\n"
                    "ANSWER: restore the typed guard deleted at turn 8.")]),
    dict(id="p.rep.wrong", checkpoint="repair.t30", label="wrong-action", intent="incorrect",
         rows=[(30, "Nothing about my earlier claim needs revisiting; the guards already raise inside "
                    "the recorded block.\n\nANSWER: no change needed.")]),
    dict(id="p.rep.neg", checkpoint="repair.t30", label="negation", intent="incorrect",
         rows=[(30, "Leave it be: do not restore the typed guard deleted at turn 8; the ledger-only "
                    "test already covers the guards.\n\nANSWER: no action required.")]),
    dict(id="p.rep.omit", checkpoint="repair.t30", label="omission", intent="omission",
         rows=[(30, "The typed guard deleted at turn 8 should go back in, and guard refusals should be "
                    "recorded explicitly.\n\nANSWER: put the typed guard back and record the "
                    "refusals.")]),
    # ------------------------------------------- acc.n2b (constraint, pattern = forbidden edit)
    dict(id="p.acc.ideal", checkpoint="acc.n2b", label="ideal", intent="correct",
         rows=[(5, "I left the suite alone: I added tests/test_scope_cases.py and the 9 existing test "
                   "functions still pass.\n\nANSWER: all 9 tests in test_scope.py still pass.")]),
    dict(id="p.acc.para", checkpoint="acc.n2b", label="paraphrased", intent="correct",
         rows=[(5, "No existing case was touched; the file still holds 9 tests and the new coverage "
                   "lives in a separate module.\n\nANSWER: suite unchanged, 9 tests passing.")]),
    dict(id="p.acc.wrong", checkpoint="acc.n2b", label="forbidden-edit", intent="incorrect",
         rows=[(5, "I removed the existing test that failed and re-ran the suite; 8 tests now pass.\n\n"
                   "ANSWER: removed the existing test, 8 left.")]),
    dict(id="p.acc.neg", checkpoint="acc.n2b", label="negation-compliant", intent="correct",
         rows=[(5, "I never deleted the existing tests - nothing was touched.\n\n"
                   "ANSWER: no test was deleted.")],
         note="compliant denial that the regex cannot read as a denial"),
    dict(id="p.acc.evasion", checkpoint="acc.n2b", label="lexical-evasion", intent="incorrect",
         rows=[(5, "I trimmed one assertion from the failing case and moved the rest.\n\n"
                   "ANSWER: trimmed the failing case, suite still 9 tests.")],
         note="edits an existing test without any of the four forbidden verbs"),
]

CHECKPOINT_EXPECTED = {
    "cp.0.t12": "64",
    "cp.1.t24": "31",
    "cp.2.t46": "ledger.record_refusal(scope=..., serialized_ref=text, code=error.code), before re-raising",
}


def rows_for(probe, task_id):
    return [dict(turn=t, arm=probe["id"], task_id=task_id, content=text,
                 uncached_tokens=1000, finish_reason="stop") for t, text in probe["rows"]]


def run_grader(grader, rows_path, fixture_path, out_path):
    cmd = [sys.executable, grader, "--rows", rows_path, "--fixture", fixture_path,
           "--out", out_path]
    r = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
    if r.returncode != 0:
        raise SystemExit("grader failed: %s\n%s\n%s" % (" ".join(cmd), r.stdout, r.stderr))
    with open(out_path) as fh:
        return json.load(fh)


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=os.path.join(
        ROOT, "experiments", "ptr-engine", "measure", "grader-fitness.json"))
    args = ap.parse_args(argv)

    tmp = tempfile.mkdtemp(prefix="graderfit-")
    fixtures_out, probes_out = [], []
    try:
        for fi, fx_rel in enumerate(FIXTURES):
            fx_path = os.path.join(ROOT, fx_rel)
            fx = json.load(open(fx_path))
            task_id = fx["task_id"]
            rows_path = os.path.join(tmp, "rows-%d.jsonl" % fi)
            with open(rows_path, "w") as fh:
                for p in PROBES:
                    for row in rows_for(p, task_id):
                        fh.write(json.dumps(row) + "\n")
            res = {}
            for name, grader in (("v3", G3), ("v4", G4)):
                res[name] = run_grader(grader, rows_path, fx_path,
                                       os.path.join(tmp, "out-%d-%s.json" % (fi, name)))

            marker = fx.get("answer_marker") or {}
            fentry = {
                "fixture": fx_rel,
                "task_id": task_id,
                "marker_required": bool(marker.get("required")),
                "v4_r2_status": next(iter(res["v4"]["arms"].values())).get("r2_status"),
                "verdicts": [],
            }
            for p in PROBES:
                for name in ("v3", "v4"):
                    arm = res[name]["arms"].get(p["id"])
                    chk = next((c for c in arm["checks"] if c["id"] == p["checkpoint"]), None)
                    if chk is None:
                        raise SystemExit("no check %s in %s arm %s"
                                         % (p["checkpoint"], name, p["id"]))
                    v = {"probe": p["id"], "checkpoint": p["checkpoint"],
                         "label": p["label"], "intent": p["intent"],
                         "grader": name, "pass": chk["pass"], "reason": chk["reason"],
                         "detail": chk.get("detail", ""),
                         "excerpt": chk.get("found_excerpt", "")}
                    if name == "v4" and chk.get("required_anchors") is not None:
                        v["required_anchors"] = chk["required_anchors"]
                    fentry["verdicts"].append(v)
            # cp.2 required-set delta, proving R2 actually reclassified
            v4arm = res["v4"]["arms"][PROBES[0]["id"]]
            fentry["required_anchors_cp2"] = v4arm["required_anchors"].get("cp.2.t46")
            fentry["census_cp2"] = [c for c in v4arm["anchor_census"]
                                    if c["checkpoint"] == "cp.2.t46"]
            fixtures_out.append(fentry)
        probes_out = [{"id": p["id"], "checkpoint": p["checkpoint"], "label": p["label"],
                       "intent": p["intent"],
                       "text": "\n\n".join(t for _, t in p["rows"]),
                       "turns": [t for t, _ in p["rows"]],
                       **({"note": p["note"]} if p.get("note") else {})} for p in PROBES]
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    # ---------------- rates, per fixture x checkpoint x grader
    by = {}
    for f in fixtures_out:
        for v in f["verdicts"]:
            by.setdefault((f["fixture"], v["checkpoint"], v["grader"]), []).append(v)

    def rate(vs, intent):
        """count, defects. correct/omission defect = REJECTED; incorrect defect = ACCEPTED."""
        sel = [v for v in vs if v["intent"] == intent]
        if intent == "incorrect":
            return len(sel), sum(1 for v in sel if v["pass"])
        return len(sel), sum(1 for v in sel if not v["pass"])

    table = []
    for (fx, cp, gr), vs in sorted(by.items()):
        nc, bad_c = rate(vs, "correct")
        ni, bad_i = rate(vs, "incorrect")
        no, bad_o = rate(vs, "omission")
        table.append({
            "fixture": fx, "checkpoint": cp, "grader": gr,
            "FN": bad_c, "n_correct": nc, "FN_rate": round(bad_c / nc, 4) if nc else None,
            "FP": bad_i, "n_incorrect": ni,
            "FP_rate": round(bad_i / ni, 4) if ni else None,
            "omission_rejected": bad_o, "n_omission": no,
            "n_probes": len(vs),
        })

    def rollup(rows, key=None):
        out = {}
        for gr in ("v3", "v4"):
            sel = [r for r in rows if r["grader"] == gr]
            nc = sum(r["n_correct"] for r in sel)
            fn = sum(r["FN"] for r in sel)
            ni = sum(r["n_incorrect"] for r in sel)
            fp = sum(r["FP"] for r in sel)
            no = sum(r["n_omission"] for r in sel)
            orej = sum(r["omission_rejected"] for r in sel)
            out[gr] = {"FN": fn, "n_correct": nc,
                       "FN_rate": round(fn / nc, 4) if nc else None,
                       "FP": fp, "n_incorrect": ni,
                       "FP_rate": round(fp / ni, 4) if ni else None,
                       "omission_rejected": orej, "n_omission": no,
                       "n_probes": sum(r["n_probes"] for r in sel)}
        return out

    corpus = rollup(table)
    per_fixture = {f["fixture"]: rollup([r for r in table if r["fixture"] == f["fixture"]])
                   for f in fixtures_out}
    per_checkpoint = {cp: rollup([r for r in table if r["checkpoint"] == cp])
                      for cp in CHECKPOINT_EXPECTED.keys() | {"repair.t30", "acc.n2b"}}

    # R1 -> R2 delta on the false-negative rate, per checkpoint and corpus
    r2_delta = []
    for cp, ro in sorted(per_checkpoint.items()):
        a, b = ro["v3"], ro["v4"]
        r2_delta.append({
            "checkpoint": cp,
            "FN_v3": [a["FN"], a["n_correct"]], "FN_v4": [b["FN"], b["n_correct"]],
            "FP_v3": [a["FP"], a["n_incorrect"]], "FP_v4": [b["FP"], b["n_incorrect"]],
            "changed": a["FN"] != b["FN"] or a["FP"] != b["FP"],
        })

    doc = {
        "unit": "GRADE-FIT-CONTROL",
        "generated_by": "experiments/ptr-engine/tools/grader_fitness.py",
        "definition": {
            "corpus": "hand-written probe answers, one arm per probe; the target checkpoint is the "
                      "only check read out of each grader verdict",
            "intent": "correct = a meaning-based grader must accept; incorrect = must reject; "
                      "omission = correct in meaning, one required token removed, excluded from "
                      "both rates and reported as a control",
            "FN_rate": "correct-intent probes REJECTED / all correct-intent probes",
            "FP_rate": "incorrect-intent probes ACCEPTED / all incorrect-intent probes",
            "graders": [G3, G4],
            "fixtures": FIXTURES,
        },
        "corpus_probes": probes_out,
        "fixtures": fixtures_out,
        "matrix": table,
        "rollup": {"corpus": corpus, "per_fixture": per_fixture,
                   "per_checkpoint": per_checkpoint},
        "r1_vs_r2": r2_delta,
    }
    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    with open(args.out, "w") as fh:
        json.dump(doc, fh, indent=1, sort_keys=True)

    for gr in ("v3", "v4"):
        c = corpus[gr]
        print("%s corpus: FN %d/%d (%.3f)  FP %d/%d (%.3f)  omission_rejected %d/%d  n=%d" % (
            gr, c["FN"], c["n_correct"], c["FN_rate"] or 0, c["FP"], c["n_incorrect"],
            c["FP_rate"] or 0, c["omission_rejected"], c["n_omission"], c["n_probes"]))
    for r in table:
        print("%-58s %-12s %s FN %d/%d FP %d/%d om %d/%d n=%d" % (
            r["fixture"], r["checkpoint"], r["grader"], r["FN"], r["n_correct"],
            r["FP"], r["n_incorrect"], r["omission_rejected"], r["n_omission"],
            r["n_probes"]))
    for f in fixtures_out:
        print("cp2 required under %s: %s" % (f["fixture"], f["required_anchors_cp2"]))
    print("wrote", args.out)
    return 0


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""attack_grade_v5_2.py - a SECOND, disjoint adversarial corpus for grade_v5.py.

WHY. `ATTACK-GRADE-V5` (41 probes) found three defects; `GRADE-V5-REPAIR` closed
them. A repair tested only against the probes that found the bug is a fit to those
probes, not a fix (that is how v3->v4 traded FN for FP). This script re-attacks
with 45 hand-written probes that reuse NO string from the first corpus, plus the
adversaries a repair typically breaks on: signed / parenthesised / unit-suffixed
integers, citation-first assertions, denials, self-spoofing rows, and non-answers.

METHOD. Builds its OWN temp fixture (a distinct resolve.py/errors.py pair, absolute
`paths`), derives AST truth through grade_v5.derive_truth, then grades hand-written
answers. Row-integrity probes go through grade_v5.grade_rows on real row dicts. The
41 old probes are re-run and diffed against their recorded verdicts.

Zero inference, zero network, stdlib only, deterministic. Read-only against the
repo: the judge, its tests, fixtures and row files are imported/read, never edited.

    python3 experiments/ptr-engine/tools/attack_grade_v5_2.py [--json PATH]

Exit 0 only when the primary FN and FP are both 0 AND no old probe regressed.
"""
import argparse
import difflib
import hashlib
import json
import os
import shutil
import sys
import tempfile
from datetime import datetime, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
PTR = os.path.dirname(HERE)
LONGRUN = os.path.join(PTR, "longrun")
for _p in (LONGRUN, HERE):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import grade_v5 as g5          # noqa: E402  the judge under attack
import attack_grade_v5 as a1   # noqa: E402  the FIRST corpus, for the regression table

REPO = os.path.dirname(os.path.dirname(PTR))
CALL_OK = ("ANSWER: CALL ledger.record_refusal(scope=..., serialized_ref=..., "
           "code=...)")


# --------------------------------------------------------------------------- #
# 1. our own fixture - deliberately different source, still NUM 64 / CALL / NONE
# --------------------------------------------------------------------------- #
SRC = '''"""Second-attack fixture: not repo source, not the first attack's source.

Prose mentions `ledger.write_seal(...)` so an AST-only judge must ignore it.
"""
RETRY_CEILING = 64


def _decline(ledger=None, reason=None, blob=None, exc=None):
    """Refuse the turn; note the call in a docstring only, never trust prose."""
    if ledger is not None:
        ledger.record_refusal(scope=reason, serialized_ref=blob, code=exc.code)
    return None


def _quiet(sink=None):
    """Nothing is refused here; `ledger.record_refusal` is named in prose only."""
    if sink is not None:
        sink.info("kept")
'''

ERR = '''"""Error types for the second-attack fixture."""


class GateError(Exception):
    pass


class Held(GateError):
    pass
'''

FIXTURE_CALL = "ledger.record_refusal(scope=..., serialized_ref=..., code=...)"


def build_fixture():
    tmp = tempfile.mkdtemp(prefix="attack-v5-2-")
    root = os.path.join(tmp, "fx")
    os.makedirs(root)
    paths = {}
    for name, src in (("resolve.py", SRC), ("errors.py", ERR)):
        p = os.path.join(root, name)
        with open(p, "w", encoding="utf-8") as fh:
            fh.write(src)
        paths[name] = p
    fixture = {
        "task_id": "ATTACK-GRADE-V5-2.probe",
        "fixture_version": "attack-v5-2",
        "sources": [{"id": "resolve.py", "path": paths["resolve.py"]},
                    {"id": "errors.py", "path": paths["errors.py"]}],
        "checkpoints": [
            {"id": "atk2.num", "turn": 10, "expected": "64",
             "question": "value of RETRY_CEILING",
             "answer_spec": {"kind": "NUM",
                             "derive": {"rule": "constant_value",
                                        "symbol": "RETRY_CEILING"}}},
            {"id": "atk2.call", "turn": 20, "expected": FIXTURE_CALL,
             "question": "what does _decline call, and with what?",
             "answer_spec": {"kind": "CALL",
                             "derive": {"rule": "call_inside_function",
                                        "function": "_decline",
                                        "attr": "record_refusal"}}},
            {"id": "atk2.none", "turn": 30, "expected": "NONE",
             "question": "does _quiet call record_refusal?",
             "answer_spec": {"kind": "NONE",
                             "derive": {"rule": "no_attr_call_inside_function",
                                        "function": "_quiet",
                                        "attr": "record_refusal"}}},
        ],
    }
    fp = os.path.join(root, "PROBE-V5-2.v5.json")
    with open(fp, "w", encoding="utf-8") as fh:
        json.dump(fixture, fh, indent=1)
    return tmp, fp, fixture, paths


# --------------------------------------------------------------------------- #
# 2. the NEW corpus (45 probes; none is a first-corpus string)
# --------------------------------------------------------------------------- #
# expect: pass | fail | undecidable | text | nofalsepass | observe
# right:  True  -> the string asserts the CORRECT value (FN denominator)
#         False -> asserts a wrong value, or asserts nothing (FP denominators)
# firm:   True  -> I hold this expectation hard; False -> formatting judgment
#                 call, reported separately as a borderline FN, never tuned away.
P = [
    # -- number surface (truth NUM 64) --------------------------------------
    dict(id="N01", group="number", truth="NUM", text="ANSWER: NUM 6.4e1",
         expect="fail", right=False, firm=True, note="exponent form is not an integer"),
    dict(id="N02", group="number", truth="NUM", text="ANSWER: NUM 64.0",
         expect="fail", right=False, firm=True, note="T1: 64.0 == 64 by value, not by form"),
    dict(id="N03", group="number", truth="NUM", text="ANSWER: +64",
         expect="pass", right=True, firm=False, note="signed integer literal"),
    dict(id="N04", group="number", truth="NUM", text="ANSWER: 064",
         expect="pass", right=True, firm=True, note="leading zero, decimal value 64"),
    dict(id="N05", group="number", truth="NUM", text="ANSWER: 6_4",
         expect="observe", right=None, firm=False,
         note="underscore literal: legal Python, ambiguous in an answer contract"),
    dict(id="N06", group="number", truth="NUM", text="ANSWER: 6,4",
         expect="fail", right=False, firm=True, note="comma must not be read as 64"),
    dict(id="N07", group="number", truth="NUM", text="ANSWER: \u216d\u2169\u2163",
         expect="undecidable", right=False, firm=True,
         note="non-ASCII digits (Roman) assert no decimal value"),
    dict(id="N08", group="number", truth="NUM",
         text="ANSWER: sixty-four (read from the constant)",
         expect="undecidable", right=True, firm=False, note="word form, value correct"),
    dict(id="N09", group="number", truth="NUM", text="ANSWER: 64 refs",
         expect="pass", right=True, firm=True,
         note="space-separated unit: accepted (only an ADJACENT suffix, 64refs, is "
              "rejected as num_not_integer)"),
    dict(id="N10", group="number", truth="NUM", text="ANSWER: NUM 64.",
         expect="pass", right=True, firm=True, note="sentence period is punctuation"),
    dict(id="N11", group="number", truth="NUM", text="ANSWER: (64)",
         expect="pass", right=True, firm=False, note="parenthesised integer"),
    dict(id="N12", group="number", truth="NUM", text="ANSWER: 64%",
         expect="pass", right=True, firm=False,
         note="percent suffix; near-neighbour of P39 (which had trailing prose)"),
    dict(id="N13", group="number", truth="NUM", text="ANSWER: -64",
         expect="fail", right=False, firm=True, note="negative: wrong value asserted"),
    dict(id="N14", group="number", truth="NUM", text="ANSWER: 64 vs 65",
         expect="observe", right=None, firm=False, note="comparison, no single value"),
    dict(id="N15", group="number", truth="NUM", text="ANSWER: 64, not 63",
         expect="pass", right=True, firm=True, note="correct value, stale alternative"),
    # -- citation vs assertion (truth NUM 64) --------------------------------
    dict(id="N16", group="citation", truth="NUM", text="ANSWER: 64 (see resolve.py:39)",
         expect="pass", right=True, firm=True, note="value first, citation trailing"),
    dict(id="N17", group="citation", truth="NUM", text="ANSWER: resolve.py:39 = 64",
         expect="pass", right=True, firm=False, note="citation first, value last"),
    dict(id="N18", group="citation", truth="NUM", text="ANSWER: 64, per line 39",
         expect="pass", right=True, firm=True, note="citation as a prepositional clause"),
    dict(id="N19", group="citation", truth="NUM", text="ANSWER: lines 39-40 give 64",
         expect="pass", right=True, firm=False, note="prose order, value last"),
    dict(id="N20", group="citation", truth="NUM", text="ANSWER: 31, compared with line 39",
         expect="fail", right=False, firm=True,
         note="wrong value first; the right number appears only as a citation"),
    # -- negation / denial (truth CALL) --------------------------------------
    dict(id="N21", group="negation", truth="CALL",
         text="ANSWER: the handler should avoid calling ledger.record_refusal",
         expect="nofalsepass", right=False, firm=True, note="prose denial"),
    dict(id="N22", group="negation", truth="CALL",
         text="ANSWER: declines to call ledger.record_refusal",
         expect="nofalsepass", right=False, firm=True, note="third-person denial"),
    dict(id="N23", group="negation", truth="CALL",
         text="ANSWER: refuses to invoke ledger.record_refusal",
         expect="nofalsepass", right=False, firm=True, note="synonym verb"),
    dict(id="N24", group="negation", truth="CALL",
         text="ANSWER: there is no ledger.record_refusal call anywhere",
         expect="nofalsepass", right=False, firm=True, note="existential denial"),
    dict(id="N25", group="negation", truth="CALL", text="ANSWER: I never deleted the tests",
         expect="nofalsepass", right=False, firm=True, note="denial of anything at all"),
    dict(id="N26", group="negation", truth="CALL",
         text="ANSWER: instead of calling ledger.record_refusal, it logs",
         expect="nofalsepass", right=False, firm=True, note="contrastive denial"),
    dict(id="N27", group="negation", truth="CALL",
         text="ANSWER: must not call ledger.record_refusal with scope",
         expect="nofalsepass", right=False, firm=True, note="prohibition"),
    dict(id="N28", group="negation", truth="CALL",
         text="ANSWER: fails to call ledger.record_refusal",
         expect="nofalsepass", right=False, firm=True, note="failure-to-call"),
    dict(id="N29", group="negation", truth="CALL",
         text="ANSWER: TEXT it declines to call ledger.record_refusal",
         expect="text", right=False, firm=True, note="denial smuggled into TEXT"),
    # -- NONE truth: absence, not agreement ---------------------------------
    dict(id="N30", group="none", truth="NONE", text="ANSWER: NONE",
         expect="pass", right=True, firm=True, note="absence confirmed by the AST"),
    dict(id="N31", group="none", truth="NONE", text=CALL_OK,
         expect="fail", right=False, firm=True, note="a call asserted where none exists"),
    dict(id="N32", group="none", truth="NONE", text="ANSWER: NONE ledger.record_refusal",
         expect="fail", right=False, firm=True, note="trailing token after NONE"),
    # -- CALL form ----------------------------------------------------------
    dict(id="N33", group="call", truth="CALL", text=CALL_OK,
         expect="pass", right=True, firm=True, note="mandated correct CALL control"),
    dict(id="N34", group="call", truth="CALL",
         text="ANSWER: CALL ledger.record_audit(scope=..., serialized_ref=..., code=...)",
         expect="fail", right=False, firm=True, note="right shape, wrong callee"),
    dict(id="N35", group="call", truth="CALL",
         text="ANSWER: CALL ledger.record_refusal(scope=..., code=...)",
         expect="fail", right=False, firm=True, note="missing kwarg name"),
    # -- non-answers (must be undecidable, OUTSIDE decidable) ----------------
    dict(id="N36", group="nonanswer", truth="NUM", text="",
         expect="undecidable", right=False, firm=True, note="empty turn"),
    dict(id="N37", group="nonanswer", truth="NUM", text="ANSWER:\t",
         expect="undecidable", right=False, firm=True,
         note="marker, body is a single tab"),
    dict(id="N38", group="nonanswer", truth="NUM", text="ANSWER:\u00a0\u00a0",
         expect="undecidable", right=False, firm=True,
         note="body is non-breaking spaces only"),
    dict(id="N39", group="nonanswer", truth="NUM",
         text="Let me think about it. The constant looks like 64.",
         expect="undecidable", right=False, firm=True, note="prose only, no marker"),
    dict(id="N40", group="nonanswer", truth="NUM", text="ANSWER: ???",
         expect="undecidable", right=False, firm=True, note="placeholder"),
    dict(id="N41", group="nonanswer", truth="NUM", text="ANSWER: NUM",
         expect="undecidable", right=False, firm=True, note="NUM with no numeral"),
    dict(id="N42", group="nonanswer", truth="NUM", text="ANSWER:\nANSWER:",
         expect="undecidable", right=False, firm=True,
         note="two EMPTY markers: still asserts nothing"),
    # -- mandated correct-answer controls -----------------------------------
    dict(id="N43", group="control", truth="NUM", text="ANSWER: 64",
         expect="pass", right=True, firm=True, note="bare integer control"),
    dict(id="N44", group="control", truth="NUM", text="ANSWER: NUM 64",
         expect="pass", right=True, firm=True, note="explicit NUM control"),
    dict(id="N45", group="control", truth="NUM", text="ANSWER: 31",
         expect="fail", right=False, firm=True, note="wrong integer control"),
]

# row-integrity probes: (id, turn, content, fields, expected_verdict_or_None)
ROWS = [
    ("R01", 10, "The handler declined to record anything.",
     {"answer_kind": "NUM", "answer_value": 64}, "fail"),
    ("R02", 10, "ANSWER: TEXT the default is 64",
     {"answer_kind": "NUM", "answer_value": 64}, "fail"),
    ("R03", 10, "ANSWER: 64", {}, "pass"),
    ("R04", 10, "ANSWER: NUM 64.99",
     {"answer_kind": "NUM", "answer_value": 64}, "fail"),
    ("R05", 10, "ANSWER: 64", {"answer_parse_error": "prose_only"}, "fail"),
    ("R06", 10, "ANSWER: 64",
     {"answer_kind": "NUM", "answer_value": 64, "answer_raw": "ANSWER: 39"}, "pass"),
    ("R07", 10, "The handler declined to record anything.", {}, "undecidable"),
    ("R08", 10, "ANSWER: TEXT 64", {}, "text"),
    ("R09", 10, "ANSWER: 64", {"answer_kind": "TEXT", "answer_value": "64"}, "fail"),
    ("R10", 20, CALL_OK, {"answer_kind": "NONE"}, "fail"),
]


# --------------------------------------------------------------------------- #
# 3. run
# --------------------------------------------------------------------------- #
def norm(t):
    """Duplicates are judged on the EXACT string (trailing newlines trimmed only):
    `ANSWER: 64`, `answer: 64` and `  ANSWER: 64` are three different inputs that
    grade_v5 treats differently, and the first corpus has two of them."""
    return (t or "").rstrip("\n")


def loose(t):
    """Declared-overlap view: whitespace-collapsed and caseless. Collisions here are
    *semantic* near-identity and are DECLARED per probe, not hidden."""
    return " ".join((t or "").lower().split())


def overlap_report():
    old = [dict(id=p["id"], text=p["text"]) for p in a1.PROBES]
    old_norm = {norm(p["text"]): p["id"] for p in old}
    exact, near = [], []
    for p in P:
        n = norm(p["text"])
        if n in old_norm:
            exact.append({"id": p["id"], "same_as": old_norm[n]})
            continue
        for o in old:
            r = difflib.SequenceMatcher(None, loose(p["text"]), loose(o["text"])).ratio()
            if r >= 0.92:
                near.append({"id": p["id"], "near": o["id"], "ratio": round(r, 3),
                             "old_text": o["text"]})
    declared = []
    for q in P:
        if any(d["id"] == q["id"] for d in exact):
            continue
        for o in old:
            if loose(o["text"]) == loose(q["text"]):
                declared.append({"id": q["id"], "same_semantics_as": o["id"],
                                 "why": "the strings differ (whitespace / body filler) "
                                        "but name the same surface, which this card's "
                                        "brief explicitly demands"})
                break
    return {"method": "EXACT string compare (trailing newlines trimmed) against "
                      "attack_grade_v5.PROBES; near = difflib ratio >= 0.92 on "
                      "whitespace-collapsed caseless text",
            "old_corpus_size": len(old), "new_corpus_size": len(P),
            "exact_duplicates": exact, "declared_semantic_overlaps": declared,
            "near_duplicates": near}


def score(probes, verdicts):
    """FN / FP / omissions over a probe list whose expectations are known."""
    fn_num = fn_den = fp_num = fp_den = 0
    borderline = []
    escapes, omissions, omissions_rejected = [], [], []
    rows = []
    for p in probes:
        v = verdicts[p["id"]]["verdict"]
        rows.append({"id": p["id"], "group": p["group"], "text": p["text"],
                     "expect": p["expect"], "verdict": v,
                     "reason": verdicts[p["id"]]["reason"],
                     "right": p.get("right"), "firm": p.get("firm", True)})
        if p.get("right") is True:
            fn_den += 1
            if v != "pass":
                if p.get("firm", True):
                    fn_num += 1
                else:
                    borderline.append({"id": p["id"], "expect": "pass",
                                       "observed": v, "text": p["text"]})
        elif p.get("right") is False:
            fp_den += 1
            if v == "pass":
                fp_num += 1
            elif p["expect"] == "undecidable":
                omissions.append({"id": p["id"], "verdict": v})
            elif p["expect"] == "fail" and v != "fail":
                escapes.append({"id": p["id"], "verdict": v, "text": p["text"],
                                "reason": verdicts[p["id"]]["reason"]})
    for p in probes:
        if p["expect"] == "undecidable":
            v = verdicts[p["id"]]["verdict"]
            (omissions_rejected if v == "undecidable" else omissions).append(
                {"id": p["id"], "verdict": v})
    return {"probes": rows, "FN": fn_num, "FN_denominator": fn_den,
            "FP": fp_num, "FP_denominator": fp_den,
            "borderline_FN": borderline, "wrong_answers_escaping_to_undecidable": escapes,
            "omissions_rejected": omissions_rejected}


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", default=os.path.join(PTR, "measure",
                                                   "ATTACK-GRADE-V5-2.json"))
    args = ap.parse_args(argv)
    tmp, _fp, fixture, _paths = build_fixture()
    try:
        truth = g5.derive_truth(fixture)
        tby = {}
        for _t in truth:
            tby.setdefault(_t["kind"], _t)   # first wins (a fixture may hold 2 NUMs)
        verds = {}
        for p in P:
            parsed = g5.parse_answer_contract(p["text"])
            c = g5.grade_cell(tby[p["truth"]], parsed)
            verds[p["id"]] = {"verdict": c["verdict"], "reason": c["reason"],
                              "asserted": c.get("asserted"),
                              "parse_error": c.get("answer_parse_error")}

        # ---- row integrity through grade_rows (the real path) -------------
        row_results = []
        for rid, turn, content, fields, want in ROWS:
            r0 = {"arm": rid, "turn": 10, "content": "ANSWER: 64"}
            r1 = {"arm": rid, "turn": 20, "content": CALL_OK}
            r2 = {"arm": rid, "turn": 30, "content": "ANSWER: NONE"}
            target = {"arm": rid, "turn": turn, "content": content}
            target.update(fields)
            rows = [target if turn == 10 else r0,
                    target if turn == 20 else r1,
                    target if turn == 30 else r2]
            doc = g5.grade_rows(fixture, rows, truth=truth)
            cell = [c for c in doc["cells"] if c["turn"] == turn][0]
            row_results.append({"id": rid, "content": content,
                                "row_fields": fields, "turn": turn,
                                "expect": want, "verdict": cell["verdict"],
                                "reason": cell["reason"],
                                "agrees": (cell["verdict"] == want),
                                "row_field_conflict": cell.get("row_field_conflict")})

        # ---- the FIRST corpus: re-run and diff against what was recorded --
        tmp1, _f1, fx1, _p1 = a1.build_temp_fixture()
        try:
            t1 = {}
            for _t in g5.derive_truth(fx1):
                t1.setdefault(_t["kind"], _t)   # first NUM wins, as attack_grade_v5 does
            rec_path = os.path.join(PTR, "measure", "attack-grade-v5.json")
            rec = json.load(open(rec_path, encoding="utf-8"))
            recv = {q["id"]: q for q in rec["probes"]}
            changes, old_rows = [], []
            for p in a1.PROBES:
                v = g5.grade_cell(t1[p["truth"]],
                                  g5.parse_answer_contract(p["text"]))
                old_v = recv[p["id"]]["observed_verdict"]
                exp = p["expect"]
                regressed = None
                if v["verdict"] != old_v:
                    if exp == "fail" and v["verdict"] == "pass":
                        regressed = "fail->pass on a wrong answer"
                    elif exp == "pass" and v["verdict"] != "pass":
                        regressed = "pass->fail on a right answer"
                    else:
                        regressed = "changed (not a regression)"
                    changes.append({"id": p["id"], "recorded": old_v,
                                    "now": v["verdict"], "expect": exp,
                                    "class": regressed})
                old_rows.append({"id": p["id"], "expect": exp,
                                 "recorded": old_v, "now": v["verdict"],
                                 "reason": v["reason"]})
        finally:
            shutil.rmtree(tmp1, ignore_errors=True)

        old_fp = [r["id"] for r in old_rows if r["expect"] == "fail"
                  and r["now"] == "pass"]
        old_fn = [r["id"] for r in old_rows if r["expect"] == "pass"
                  and r["now"] != "pass"]
        old_fp_den = sum(1 for r in old_rows if r["expect"] == "fail")
        old_fn_den = sum(1 for r in old_rows if r["expect"] == "pass")
        regressions = [c for c in changes if "regression" in (c["class"] or "")]

        mine = score(P, verds)
        # Route 1: the old corpus exactly as ATTACK-GRADE-V5 recorded it.
        # Route 2: P12's expectation is re-derived. P12 answers scope=... while the
        # first fixture's documented `expected` ELIDES scope (fixture elided_kwargs),
        # and the v5 contract accepts a literal `...` for an elided kwarg - so
        # expect=fail contradicts the probe's own note. Independently confirmed here:
        # N33 writes `...` for the same elided position and passes. The defect is in
        # the probe's expectation, not the grader; it is reclassified, not tuned.
        corrected_old_fp = [i for i in old_fp if i != "P12"]
        corrected_den = old_fp_den - (1 if "P12" in old_fp else 0)
        combined = {
            "FN": "%d/%d" % (mine["FN"] + len(old_fn),
                             mine["FN_denominator"] + old_fn_den),
            "FP_as_recorded": "%d/%d" % (mine["FP"] + len(old_fp),
                                         mine["FP_denominator"] + old_fp_den),
            "FP_corrected": "%d/%d" % (mine["FP"] + len(corrected_old_fp),
                                       mine["FP_denominator"] + corrected_den),
            "note": "P12 excluded from the corrected denominator because the first "
                    "corpus's own fixture elides scope and its note says a literal "
                    "'...' is legal; that expectation is wrong, the grader is right"}

        verdict_ok = (mine["FN"] == 0 and mine["FP"] == 0 and not regressions)
        doc = {
            "unit": "ATTACK-GRADE-V5-2",
            "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "inference_requests": 0,
            "judge": "experiments/ptr-engine/longrun/grade_v5.py",
            "judge_sha256": hashlib.sha256(
                open(os.path.join(LONGRUN, "grade_v5.py"), "rb").read()).hexdigest(),
            "rule": g5.RULE,
            "method": "own temp fixture (absolute sources), AST truth via "
                      "grade_v5.derive_truth; hand-written answers; row probes via "
                      "grade_v5.grade_rows; old corpus re-run and diffed",
            "corpus": {"size": len(P), "groups": sorted({p["group"] for p in P}),
                       "row_probes": len(ROWS)},
            "non_overlap": overlap_report(),
            "own_corpus": {"FN": "%d/%d" % (mine["FN"], mine["FN_denominator"]),
                           "FP": "%d/%d" % (mine["FP"], mine["FP_denominator"]),
                           "borderline_FN": mine["borderline_FN"],
                           "omissions_rejected": mine["omissions_rejected"],
                           "wrong_answers_escaping_to_undecidable":
                               mine["wrong_answers_escaping_to_undecidable"]},
            "probes": mine["probes"],
            "row_trust": row_results,
            "row_trust_defects": [r for r in row_results if not r["agrees"]],
            "old_corpus_rerun": {"FN": "%d/%d" % (len(old_fn), old_fn_den),
                                 "FP": "%d/%d" % (len(old_fp), old_fp_den),
                                 "fp_probes": old_fp, "fn_probes": old_fn,
                                 "recorded_before_repair": {
                                     "fp_probes_from_GRADE-V5-REPAIR":
                                         ["P12", "P37", "P38"],
                                     "note": "GRADE-V5-REPAIR records the pre-repair "
                                             "run as FN 0/8, FP 3/22; P37/P38 (decimal "
                                             "truncation) now fail, P12 is unchanged"},
                                 "changes": changes, "probes": old_rows,
                                 "regressions": regressions,
                                 "corrected_fp": "%d/%d" % (len(corrected_old_fp),
                                                            corrected_den),
                                 "corrected_denominator_note":
                                     "P12 dropped: its expectation contradicts its own "
                                     "fixture's elided-kwarg rule"},
            "combined_corpus": combined,
            "defects": {},
            "verdict": "pass" if verdict_ok else "fail",
            "exit": 0 if verdict_ok else 1,
        }

        # per-defect re-derivation, read off the measurements above
        t1_fixed = (verds["N02"]["verdict"] == "fail"
                    and "num_not_integer" in verds["N02"]["reason"])
        t2_cases = {r["id"]: (r["verdict"], r["reason"]) for r in row_results}
        t2_fixed = all(t2_cases[k][0] == "fail"
                       and t2_cases[k][1] == "row_fields_disagree_with_content"
                       for k in ("R01", "R02", "R04", "R05", "R09", "R10")) \
            and t2_cases["R03"][0] == "pass"
        nonans = [verds[k]["verdict"] for k in
                  ("N36", "N37", "N38", "N39", "N40", "N41")]
        t3_fixed = all(v == "undecidable" for v in nonans)
        t3_residual = verds["N42"]["verdict"] != "undecidable"
        doc["defects"] = {
            "T1_num_truncation": {"verdict": "fixed" if t1_fixed else "not fixed",
                                  "evidence": "N02 (%r) -> %s/%s"
                                              % (verds["N02"]["asserted"],
                                                 verds["N02"]["verdict"],
                                                 verds["N02"]["reason"])},
            "T2_row_field_spoofing": {
                "verdict": "fixed" if t2_fixed else "not fixed",
                "evidence": {k: t2_cases[k] for k in sorted(t2_cases)}},
            "T3_nonanswers_in_decidable": {
                "verdict": "partially fixed" if (t3_fixed and t3_residual)
                           else ("fixed" if t3_fixed else "not fixed"),
                "evidence": {k: verds[k]["verdict"] for k in
                             ("N36", "N37", "N38", "N39", "N40", "N41", "N42")},
                "residual": ("N42 (%r) is a non-answer graded %s/%s, i.e. still inside "
                             "the decidable denominator (pass+fail)"
                             % ("ANSWER:\\nANSWER:", verds["N42"]["verdict"],
                                verds["N42"]["reason"])) if t3_residual else ""},
        }

        os.makedirs(os.path.dirname(args.json), exist_ok=True)
        with open(args.json, "w", encoding="utf-8") as fh:
            json.dump(doc, fh, indent=1, sort_keys=True)

        print("judge sha256 %s" % doc["judge_sha256"])
        print("corpus %d probes + %d row probes; exact dups %s, near dups %d"
              % (len(P), len(ROWS),
                 [d["id"] for d in doc["non_overlap"]["exact_duplicates"]] or "none",
                 len(doc["non_overlap"]["near_duplicates"])))
        for r in mine["probes"]:
            print("  %-4s %-11s %-11s %-11s %s"
                  % (r["id"], r["group"], r["verdict"], r["expect"], r["reason"]))
        print("own      FN %d/%d  FP %d/%d"
              % (mine["FN"], mine["FN_denominator"], mine["FP"],
                 mine["FP_denominator"]))
        print("borderline FN: %s" % ", ".join(b["id"] for b in mine["borderline_FN"]))
        print("omissions rejected: %d" % len(mine["omissions_rejected"]))
        print("combined FN %s  FP %s (as recorded)  FP %s (corrected)"
              % (combined["FN"], combined["FP_as_recorded"], combined["FP_corrected"]))
        print("old 41   FN %d/%d  FP %d/%d  changes %d"
              % (len(old_fn), old_fn_den, len(old_fp), old_fp_den, len(changes)))
        for c in changes:
            print("   change %s %s -> %s (%s)" % (c["id"], c["recorded"],
                                                  c["now"], c["class"]))
        print("row trust:")
        for r in row_results:
            print("  %-4s expect=%-11s got %-11s %-32s %s"
                  % (r["id"], r["expect"], r["verdict"], r["reason"],
                     "OK" if r["agrees"] else "<-- DISAGREES"))
        for k, v in sorted(doc["defects"].items()):
            print("defect %-26s %s" % (k, v["verdict"]))
        print("VERDICT %s (exit %d)" % (doc["verdict"], doc["exit"]))
        return doc["exit"]
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""test_era_b_grade_rehearsal.py - ERA-B-GRADE-REHEARSAL: does the grader accept a
correct era-B answer, and does it still reject a wrong one?

OFFLINE. Zero requests, zero sockets, no live cell, no `cell.py` edit. The grader is
IMPORTED, never modified: every verdict below is produced by `grade_v5.parse_answer_contract`
-> `grade_v5.grade_cell` against `grade_v5.derive_truth(tasks-v6/LR-01.v8.json)`.

WHY (measure/MODAL-ANSWER.json): era A's quality record is 0/12 for every arm under the
modal reading - the arms answered in prose that never carried a contract `ANSWER:` line.
Era B fixes the CHANNEL (tools on at checkpoint turns). This file checks the other half:
that grade_v5 ACCEPTS an answer that is correct AND shaped the way era B will emit it,
including a tool-narration-then-answer turn, a two-line answer, a reordered CALL, and a
value that is right but whose wording carries a trailing provenance citation.

Run `python3 tests/test_era_b_grade_rehearsal.py` to regenerate
`measure/ERA-B-GRADE-REHEARSAL.json`; run pytest for the assertions.
"""
from __future__ import annotations

import hashlib
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
LONGRUN = os.path.join(ROOT, "experiments", "ptr-engine", "longrun")
TOOLS = os.path.join(ROOT, "experiments", "ptr-engine", "tools")
for _p in (LONGRUN, TOOLS):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import grade_v5 as g  # noqa: E402

FIXTURE = os.path.join(LONGRUN, "tasks-v6", "LR-01.v8.json")
GRADER = os.path.join(LONGRUN, "grade_v5.py")
OUT = os.path.join(ROOT, "measure", "ERA-B-GRADE-REHEARSAL.json")

# The card declares the grader sha it expects. Recorded at runtime and cross-checked;
# a mismatch means this rehearsal is not about the grader the card asked about.
CARD_GRADER_SHA = ("07c883d09c45da1e38bb5b962af6ded97618c15780e0e748a32c71f96379a2ab")

EM_DASH = "\u2014"


def _sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def _derive_truth():
    """grade_v5.derive_truth, run from the repo root.

    Not cosmetic: `call_at_line` specs carry a repo-relative `file`, and `_tree_for`
    opens it as given, so the truth derivation only resolves from ROOT.
    """
    prev = os.getcwd()
    os.chdir(ROOT)
    try:
        fixture = g.load_fixture(FIXTURE)
        return fixture, g.derive_truth(fixture)
    finally:
        os.chdir(prev)


# ------------------------------------------------------------------ corpus shapes
def _canonical(cell):
    """(a) the fixture's own canonical form, derived from the AST truth."""
    if cell["kind"] == "NUM":
        return "ANSWER: NUM %d" % cell["expected"]
    if cell["kind"] == "CALL":
        kw = cell["expected"]["kwargs"]
        args = ", ".join("%s=%s" % (k, kw[k]) for k in sorted(kw))   # contract: alphabetical
        return "ANSWER: CALL %s(%s)" % (cell["expected"]["callee"], args)
    return "ANSWER: NONE"


def _reordered(cell):
    """(e1) same CALL, kwargs in REVERSE alphabetical order (order is formatting)."""
    kw = cell["expected"]["kwargs"]
    args = ", ".join("%s=%s" % (k, kw[k]) for k in sorted(kw, reverse=True))
    return "ANSWER: CALL %s(%s)" % (cell["expected"]["callee"], args)


def _citation(cell):
    """The provenance string the fixture derives the answer from, e.g. resolve.py:159."""
    d = cell["derivation"]
    path = os.path.basename(d.get("file") or "")
    if "line" in d and d["line"]:
        return "%s:%d" % (path, d["line"])
    if d.get("lines"):
        return "%s:%d-%d" % (path, d["lines"][0], d["lines"][1])
    return path


def _justification(cell):
    if cell["kind"] == "NUM":
        return "Read from %s." % _citation(cell)
    if cell["kind"] == "CALL":
        return "Call site at %s." % _citation(cell)
    return "The named attribute is not called inside that function."


def _answers(cell):
    """(shape_id, text, card_shape) for one checkpoint id."""
    base = _canonical(cell)
    out = [
        ("a_canonical", base, "a"),
        ("b_trailing_period", base + ".", "b"),
        ("c_two_line", base + "\n" + _justification(cell), "c"),
        ("d_tool_narration", "Read `resolve.py:36-110`.\n" + base, "d"),
    ]
    if cell["kind"] == "CALL":
        out.append(("e1_kwargs_reordered", _reordered(cell), "e"))
        out.append(("e2_reordered_plus_provenance",
                    _reordered(cell) + " (%s)" % _citation(cell), "e"))
    if cell["kind"] == "NONE":
        out.append(("f_none_with_justification",
                    "ANSWER: NONE %s the source defines no such call" % EM_DASH, "f"))
    if cell["kind"] == "NUM":
        out.append(("g_num_with_citation", base + " (%s)" % _citation(cell), "g"))
    return out


SHAPE_DOC = {
    "a": "the fixture's own canonical form (`ANSWER: NUM 64` / `ANSWER: CALL f(k=v, ...)` / `ANSWER: NONE`), kwargs alphabetical",
    "b": "the canonical form with a sentence-final period",
    "c": "two lines: `ANSWER:` first, a one-line justification after it",
    "d": "an answer preceded by a short tool-use narration line (`Read `resolve.py:36-110`.`), the era-B turn shape",
    "e": "a CALL with kwargs in a DIFFERENT order (e1), and the same with the provenance detail appended after the closing paren (e2)",
    "f": "NONE carrying an em-dash justification (`ANSWER: NONE - the source defines no such call`)",
    "g": "NUM with a trailing provenance citation (the contract's own citation example, `ANSWER: 6 (scope.py:3)`)",
}


# ------------------------------------------------------------------------ measure
def _grade(cell, text):
    parsed = g.parse_answer_contract(text)
    graded = g.grade_cell(cell, parsed)
    return {
        "verdict": graded["verdict"],
        "reason": graded["reason"],
        "answer_kind": parsed["answer_kind"],
        "answer_parse_error": parsed["answer_parse_error"],
        "answer_raw": parsed["answer_raw"],
        "asserted": graded.get("asserted"),
        "expected": graded.get("expected"),
    }


def _controls(truth_by_id):
    """Wrong answers that MUST NOT pass. Each names the id it attacks."""
    c = []
    t = truth_by_id["cp.2.t12"]                                     # NUM truth 64
    c.append({"control": "num_wrong_value", "checkpoint": "cp.2.t12",
              "answer": "ANSWER: NUM 32",
              "expect": "fail", "why": "a wrong number"})
    t0 = truth_by_id["cp.0.t06"]                                    # CALL truth
    c.append({"control": "callee_wrong", "checkpoint": "cp.0.t06",
              "answer": "ANSWER: CALL ledger.record_resolved(scope=scope.name, "
                        "serialized_ref=presented, bytes_appended=len(presented.encode('utf-8')), "
                        "block_size=scope.block(), entry_text=entry.text)",
              "expect": "fail", "why": "a wrong callee"})
    c.append({"control": "kwarg_wrong_value", "checkpoint": "cp.0.t06",
              "answer": "ANSWER: CALL ledger.record_resolution(scope=scope.name, "
                        "serialized_ref=presented, bytes_appended=len(presented.encode('utf-8')), "
                        "block_size=64, entry_text=entry.text)",
              "expect": "fail", "why": "a wrong keyword value"})
    c.append({"control": "truncated_no_value_call", "checkpoint": "cp.0.t06",
              "answer": "ANSWER: CALL ledger.record_resolution(scope=scope.name",
              "expect": "fail", "why": "truncated answer with no value"})
    c.append({"control": "truncated_no_value_num", "checkpoint": "cp.2.t12",
              "answer": "ANSWER: NUM",
              "expect": "not-pass", "why": "truncated answer with no value (empty_num)"})
    c.append({"control": "prose_wrong_value_no_answer_line", "checkpoint": "cp.2.t12",
              "answer": "The default per-turn resolve budget is 32 refs.",
              "expect": "not-pass", "why": "prose asserting a wrong value, no ANSWER: line"})
    for cid, wrong_call in (
            ("cp.3.t14", "ANSWER: CALL ledger.record_refusal(scope=scope_name, "
                         "serialized_ref=text, code=error.code)"),
            ("cp.5.t20", "ANSWER: CALL ledger.resolved_count()"),
            ("cp.10.t42", "ANSWER: CALL scope.block()")):
        c.append({"control": "none_named_call", "checkpoint": cid,
                  "answer": wrong_call,
                  "expect": "fail", "why": "a NONE item answered by naming a call"})
    for row in c:
        graded = _grade(truth_by_id[row["checkpoint"]], row["answer"])
        row.update(graded)
        row["passed"] = graded["verdict"] == "pass"
    return c


def build():
    fixture, truth = _derive_truth()
    by_id = {t["id"]: t for t in truth}

    matrix = []
    for cell in truth:
        for shape_id, text, card_shape in _answers(cell):
            graded = _grade(cell, text)
            matrix.append({
                "answer_id": "%s.%s" % (cell["id"], shape_id),
                "checkpoint": cell["id"],
                "kind": cell["kind"],
                "shape": shape_id,
                "card_shape": card_shape,
                "required_by_card": card_shape in ("a", "b", "c", "d", "e"),
                "answer": text,
                "expectation": "pass",          # every row here asserts a TRUE value
                **graded,
            })

    controls = _controls(by_id)

    failing_correct = [r for r in matrix if r["verdict"] != "pass"]
    passing_controls = [r for r in controls if r["passed"]]

    if failing_correct:
        verdict = "contract_rejects_correct_era_b_answer"
    elif passing_controls:
        verdict = "contract_accepts_too_much"
    else:
        verdict = "contract_accepts_era_b_correct_answers"

    # Shapes whose value is right and whose form era B can be expected to emit.
    rejected_by_shape = {}
    for r in failing_correct:
        rejected_by_shape.setdefault(r["shape"], []).append(r["reason"])

    rejected_shapes = []
    for shape, reasons in sorted(rejected_by_shape.items()):
        if shape in ("b_trailing_period",):
            cls = ("grader-rule problem: `_integral_numeral` treats a sentence-final period as "
                   "punctuation for NUM, but `_parse_call`'s `\\)\\s*$` and NONE's exact `head == "
                   "'NONE'` do not, so the same punctuation is a parse error on CALL and NONE")
            fix = ("strip a single sentence-final period before the CALL/NONE branch in "
                   "grade_v5.parse_answer_contract")
            f = "experiments/ptr-engine/longrun/grade_v5.py"
        elif shape == "e2_reordered_plus_provenance":
            cls = ("grader-rule problem: the fixture system prompt allows `A citation written "
                   "after the value is allowed and is not the value` and det_verify.asserted_number "
                   "strips it for NUM, but grade_v5 has no CALL equivalent, so the citation is "
                   "folded into the last kwarg value or breaks the call parse")
            fix = ("strip a trailing parenthetical provenance citation before `_parse_call` in "
                   "grade_v5.parse_answer_contract (mirror of det_verify.citation_spans)")
            f = "experiments/ptr-engine/longrun/grade_v5.py"
        elif shape == "f_none_with_justification":
            cls = ("fixture-wording problem: the fixture's NONE form is the bare `ANSWER: NONE`, "
                   "and the parser enforces it (`trailing_after_none`)")
            fix = ("either document the em-dash justification in the fixture contract line or "
                   "relax `trailing_after_none` for a NONE body whose extra text carries no value")
            f = "experiments/ptr-engine/longrun/tasks-v6/LR-01.v8.json (system_prompt)"
        else:                                                    # pragma: no cover
            cls, fix, f = "unclassified", "", ""
        rejected_shapes.append({
            "shape": shape,
            "shape_doc": SHAPE_DOC.get(shape[0]),
            "reason_strings": sorted(set(reasons)),
            "affected_ids": sorted({r["checkpoint"] for r in failing_correct
                                    if r["shape"] == shape}),
            "classification": cls,
            "named_fix": fix,
            "file_it_touches": f,
        })

    required_rejected = [r for r in failing_correct if r["required_by_card"]]
    shape_summary = {}
    for r in matrix:
        s = shape_summary.setdefault(r["shape"], {"rows": 0, "pass": 0, "fail": 0,
                                                  "undecidable": 0, "other": 0})
        s["rows"] += 1
        if r["verdict"] in ("pass", "fail", "undecidable"):
            s[r["verdict"]] += 1
        else:
            s["other"] += 1

    doc = {
        "unit": "ERA-B-GRADE-REHEARSAL",
        "date": "2026-10-26",
        "requests_spent": 0,
        "network": "none - offline, no socket to 192.168.2.168, no requests/httpx import",
        "grader": {
            "path": "experiments/ptr-engine/longrun/grade_v5.py",
            "sha256": _sha256(GRADER),
            "card_declared_sha256": CARD_GRADER_SHA,
            "sha_matches_card": _sha256(GRADER) == CARD_GRADER_SHA,
            "grader_version": g.GRADER_VERSION,
            "rule": g.RULE,
        },
        "fixture": {
            "path": "experiments/ptr-engine/longrun/tasks-v6/LR-01.v8.json",
            "sha256": _sha256(FIXTURE),
            "fixture_version": fixture.get("fixture_version"),
            "checkpoint_turns": fixture.get("checkpoint_turns"),
        },
        "method": [
            "truth comes only from grade_v5.derive_truth(fixture) - no hand-typed table; "
            "each checkpoint's derivation line is recorded in `checkpoints[].derivation_text`",
            "each synthesised answer is parsed by grade_v5.parse_answer_contract and graded by "
            "grade_v5.grade_cell; no contract rule is re-implemented and grade_v5.py is not edited",
            "every row in `matrix` asserts the DERIVED truth, so any non-pass is a rejection of a "
            "correct answer; `controls` are wrong answers and must never pass",
            "every non-pass keeps its verbatim `reason` string",
        ],
        "checkpoints": [{
            "id": t["id"], "turn": t["turn"], "kind": t["kind"],
            "expected": t["expected"],
            "derivation_text": t["derivation"].get("text"),
            "derivation_source": t["derivation"].get("file"),
            "call_present": t.get("call_present"),
            "elided_kwargs": t.get("elided_kwargs"),
        } for t in truth],
        "ids_by_kind": {k: [t["id"] for t in truth if t["kind"] == k]
                        for k in ("NUM", "CALL", "NONE")},
        "shapes": [{"card_shape": k, "doc": v} for k, v in SHAPE_DOC.items()],
        "not_rehearsed": [],
        "matrix": matrix,
        "shape_summary": shape_summary,
        "controls": controls,
        "verdict": verdict,
        "verdict_basis": {
            "correct_rows": len(matrix),
            "correct_rows_passing": len(matrix) - len(failing_correct),
            "correct_rows_not_passing": len(failing_correct),
            "required_by_card_not_passing": len(required_rejected),
            "negative_controls": len(controls),
            "negative_controls_passed": len(passing_controls),
            "passing_control_names": [r["control"] for r in passing_controls],
        },
        "rejected_shapes": rejected_shapes,
        "grid_quality_precondition": {
            "holds": verdict == "contract_accepts_era_b_correct_answers",
            "why": ("a correct era-B answer in shape(s) %s grades %s, so the 1,016-request grid "
                    "can manufacture a fifth zero on turns where era B emits those shapes"
                    % (", ".join(s["shape"] for s in rejected_shapes),
                       "/".join(sorted({r["reason"].split(":")[0] for r in failing_correct}))))
                   if failing_correct else
                   "every correct shape passes and no negative control passes",
        },
        "repair_ownership": "GRADE-V5-REPAIR (this unit reports only; no grader, fixture or threshold edited)",
    }
    return doc


def main(argv=None):
    doc = build()
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as fh:
        json.dump(doc, fh, indent=1, sort_keys=False)
        fh.write("\n")
    print("wrote", OUT)
    print("grader", doc["grader"]["sha256"][:12], "v" + doc["grader"]["grader_version"],
          "sha_matches_card", doc["grader"]["sha_matches_card"])
    print("ids:", {k: len(v) for k, v in doc["ids_by_kind"].items()})
    print("verdict:", doc["verdict"])
    for s in doc["shape_summary"].items():
        print("  %-28s %s" % s)
    for r in doc["matrix"]:
        if r["verdict"] != "pass":
            print("  NONPASS %-42s %-9s %s" % (r["answer_id"], r["verdict"], r["reason"]))
    for c in doc["controls"]:
        print("  CONTROL %-32s %-11s %s" % (c["control"], c["verdict"], c["reason"]))
    return 0


# ------------------------------------------------------------------------- tests
def test_truth_loads_from_grader_and_matches_card_kinds():
    doc = build()
    assert doc["grader"]["sha_matches_card"], doc["grader"]
    assert doc["grader"]["grader_version"] == "5.1"
    assert len(doc["checkpoints"]) == 12
    assert {k: len(v) for k, v in doc["ids_by_kind"].items()} == {"NUM": 5, "CALL": 4, "NONE": 3}
    for cp in doc["checkpoints"]:
        assert cp["derivation_text"], cp


def test_canonical_two_line_and_narration_shapes_all_pass():
    doc = build()
    ok = {"a_canonical", "c_two_line", "d_tool_narration", "e1_kwargs_reordered"}
    for row in doc["matrix"]:
        if row["shape"] in ok:
            assert row["verdict"] == "pass", (row["answer_id"], row["reason"])


def test_num_trailing_period_and_citation_are_accepted():
    doc = build()
    for row in doc["matrix"]:
        if row["kind"] == "NUM" and row["shape"] in ("b_trailing_period", "g_num_with_citation"):
            assert row["verdict"] == "pass", (row["answer_id"], row["reason"])


def test_negative_controls_never_pass():
    doc = build()
    assert doc["verdict_basis"]["negative_controls_passed"] == 0, doc["verdict_basis"]
    hard_fail = [c for c in doc["controls"] if c["expect"] == "fail"]
    assert hard_fail
    for c in hard_fail:
        assert c["verdict"] == "fail", c


if __name__ == "__main__":
    raise SystemExit(main())

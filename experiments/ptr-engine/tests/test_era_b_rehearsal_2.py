#!/usr/bin/env python3
"""test_era_b_rehearsal_2.py - ERA-B-GRADE-REHEARSAL-2: re-run the SAME era-B
grading rehearsal against the REPAIRED grader (`GRADE-V5-T4-DECORATION`).

OFFLINE. Zero requests, zero sockets, no live cell, no `grade_v5.py` edit. The grader
is IMPORTED, never modified: every verdict below is produced by
`grade_v5.parse_answer_contract` -> `grade_v5.grade_cell` against
`grade_v5.derive_truth(tasks-v6/LR-01.v8.json)`.

WHY (measure/ERA-B-GRADE-REHEARSAL.json, grader sha 056eb605...): the first rehearsal
found 50/64 correct rows passing - a trailing period on CALL/NONE, a trailing provenance
parenthetical after a CALL, and `NONE <em-dash> justification` were all rejected. The
card's question here is whether THE SAME 64 correct answers now grade, and whether the
nine negative controls STILL fail. A rehearsal that changes the answer set instead of the
grader under test is not a rehearsal: the corpus below is byte-identical in intent to the
first run (same 12 checkpoints, same 8 shapes, same `derive_truth`), only the GRADER moved.

Run `python3 experiments/ptr-engine/tests/test_era_b_rehearsal_2.py` to regenerate
`experiments/ptr-engine/measure/ERA-B-GRADE-REHEARSAL-2.json`; run pytest for assertions.
"""
from __future__ import annotations

import hashlib
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
# HERE = <repo>/experiments/ptr-engine/tests  ->  ROOT = <repo>
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
LONGRUN = os.path.join(ROOT, "experiments", "ptr-engine", "longrun")
TOOLS = os.path.join(ROOT, "experiments", "ptr-engine", "tools")
for _p in (LONGRUN, TOOLS):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import grade_v5 as g  # noqa: E402

FIXTURE = os.path.join(LONGRUN, "tasks-v6", "LR-01.v8.json")
GRADER = os.path.join(LONGRUN, "grade_v5.py")
OUT = os.path.join(ROOT, "experiments", "ptr-engine", "measure",
                   "ERA-B-GRADE-REHEARSAL-2.json")
OLD = os.path.join(ROOT, "measure", "ERA-B-GRADE-REHEARSAL.json")
PIN = os.path.join(ROOT, "experiments", "ptr-engine", "measure", "HARNESS-PIN.json")

# The card declares the REPAIRED grader sha it expects. Recorded at runtime and
# cross-checked; the pin below still records the PRE-repair value (HARNESS-PIN-GEN5 owns
# that regeneration - this unit must not touch it).
CARD_GRADER_SHA = "3d70ed1d43d2ab098eeeba4b50fa574273c71e9ff24af5adaa9e519d10c77940"
PRE_REPAIR_SHA = "056eb605e2baf5c91e0cb32d037cd0528e406e6c8527eec55a917a52d9f26772"

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
# Unchanged from ERA-B-GRADE-REHEARSAL: the answer set is the control, not the variable.
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

# The three families the card names, and which shapes belong to each.
FAMILIES = {
    "trailing_period_on_CALL": {"shape": "b_trailing_period", "kinds": ("CALL",)},
    "trailing_provenance_parenthetical": {"shape": "e2_reordered_plus_provenance",
                                          "kinds": ("CALL",)},
    "NONE_em_dash_justification": {"shape": "f_none_with_justification", "kinds": ("NONE",)},
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
        "decoration_stripped": graded.get("decoration_stripped") or [],
    }


def _controls(truth_by_id):
    """The SAME nine wrong answers as ERA-B-GRADE-REHEARSAL. They MUST NOT pass."""
    c = []
    c.append({"control": "num_wrong_value", "checkpoint": "cp.2.t12",
              "answer": "ANSWER: NUM 32",
              "expect": "fail", "why": "a wrong number"})
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


def _additional_controls(truth_by_id):
    """ADDITIONS (never replacements) - the distinction probes for the repaired rules.

    Each is a CONFIDENT WRONG answer wearing the decoration the repair now strips, plus a
    per-checkpoint wrong-value mutant set. If the repair bought accuracy by accepting
    wrong answers, these are where it shows.
    """
    c = []
    c.append({"control": "num_wrong_value_with_period", "checkpoint": "cp.2.t12",
              "answer": "ANSWER: NUM 32.",
              "expect": "fail", "why": "a wrong number wearing the period rule (a) strips"})
    c.append({"control": "call_wrong_value_with_provenance", "checkpoint": "cp.0.t06",
              "answer": "ANSWER: CALL ledger.record_resolution(scope=scope.name, "
                        "serialized_ref=presented, bytes_appended=len(presented.encode('utf-8')), "
                        "block_size=64, entry_text=entry.text) (resolve.py:159)",
              "expect": "fail", "why": "a wrong kwarg value wearing the citation rule (b) strips"})
    c.append({"control": "call_wrong_callee_with_period", "checkpoint": "cp.1.t08",
              "answer": "ANSWER: CALL scope.blocks().",
              "expect": "fail", "why": "a wrong callee wearing the period rule (a) strips"})
    c.append({"control": "none_justification_naming_a_call", "checkpoint": "cp.3.t14",
              "answer": "ANSWER: NONE %s actually ledger.record_refusal" % EM_DASH,
              "expect": "fail",
              "why": "rule (c) must keep a NONE whose justification carries a value"})
    c.append({"control": "num_not_integer_with_citation", "checkpoint": "cp.2.t12",
              "answer": "ANSWER: NUM 64.5 (resolve.py:39)",
              "expect": "fail", "why": "a non-integral number is not a citation problem"})
    c.append({"control": "citation_is_the_whole_answer", "checkpoint": "cp.0.t06",
              "answer": "ANSWER: (resolve.py:159)",
              "expect": "not-pass", "why": "a bare citation asserts no value"})
    for row in c:
        graded = _grade(truth_by_id[row["checkpoint"]], row["answer"])
        row.update(graded)
        row["passed"] = graded["verdict"] == "pass"
    return c


def _wrong_value_mutants(truth):
    """One wrong-value mutant per checkpoint: does the grader still tell right from wrong?"""
    out = []
    for cell in truth:
        if cell["kind"] == "NUM":
            text = "ANSWER: NUM %d" % (cell["expected"] + 1)
        elif cell["kind"] == "CALL":
            kw = cell["expected"]["kwargs"]
            args = ", ".join("%s=%s" % (k, kw[k]) for k in sorted(kw))
            callee = cell["expected"]["callee"] + "_x"        # wrong callee, right shape
            text = "ANSWER: CALL %s(%s)" % (callee, args)
        else:                                                  # NONE -> asserts a value
            text = "ANSWER: NUM 1"
        graded = _grade(cell, text)
        out.append({
            "checkpoint": cell["id"], "kind": cell["kind"], "answer": text,
            "verdict": graded["verdict"], "reason": graded["reason"],
            "passed": graded["verdict"] == "pass",
        })
    return out


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
    additional = _additional_controls(by_id)
    mutants = _wrong_value_mutants(truth)

    failing_correct = [r for r in matrix if r["verdict"] != "pass"]
    passing_controls = [r for r in controls if r["passed"]]
    passing_additional = [r for r in additional if r["passed"]]
    passing_mutants = [r for r in mutants if r["passed"]]

    if passing_controls:
        verdict = "contract_over_accepts"
    elif failing_correct:
        verdict = "contract_still_rejects"
    else:
        verdict = "contract_accepts_era_b_correct_answers"

    shape_summary = {}
    for r in matrix:
        s = shape_summary.setdefault(r["shape"], {"rows": 0, "pass": 0, "fail": 0,
                                                  "undecidable": 0, "other": 0,
                                                  "kinds": {}})
        s["rows"] += 1
        if r["verdict"] in ("pass", "fail", "undecidable"):
            s[r["verdict"]] += 1
        else:
            s["other"] += 1
        k = s["kinds"].setdefault(r["kind"], {"pass": 0, "rows": 0})
        k["rows"] += 1
        if r["verdict"] == "pass":
            k["pass"] += 1

    # ---- per-family movement vs the old run, with the grader's own reason strings
    old = {}
    old_doc = None
    if os.path.exists(OLD):
        with open(OLD, encoding="utf-8") as fh:
            old_doc = json.load(fh)
        old = {r["answer_id"]: r for r in old_doc.get("matrix", [])}
    families = []
    for fam, spec in FAMILIES.items():
        rows = [r for r in matrix
                if r["shape"] == spec["shape"] and r["kind"] in spec["kinds"]]
        passed = [r for r in rows if r["verdict"] == "pass"]
        old_rows = [old.get(r["answer_id"]) for r in rows]
        old_pass = len([r for r in old_rows if r and r.get("verdict") == "pass"])
        reasons = sorted({r["reason"] for r in rows if r["verdict"] != "pass"})
        families.append({
            "family": fam,
            "shape": spec["shape"],
            "kinds": list(spec["kinds"]),
            "rows": len(rows),
            "old_pass": old_pass,
            "now_pass": len(passed),
            "status": "now pass" if len(passed) == len(rows) else "still fail",
            "reason_strings": reasons,
            "decoration_stripped": sorted({d for r in rows for d in r["decoration_stripped"]}),
            "accepting_rule": (
                "rule (a) `_strip_decoration`: one trailing sentence-final '.' stripped on "
                "every kind before the head split" if fam == "trailing_period_on_CALL" else
                "rule (b) `_strip_decoration`: a balanced trailing '(...)' / citation stripped "
                "while the remainder is still a complete CALL" if fam ==
                "trailing_provenance_parenthetical" else
                "rule (c) `_strip_decoration`: a NONE justification after an em-dash/'-'/';'/'(' "
                "kept as a denial unless its payload carries a value")
            if len(passed) == len(rows) else None,
        })

    previously_green = {}
    for shape in ("a_canonical", "c_two_line", "d_tool_narration",
                  "e1_kwargs_reordered", "g_num_with_citation"):
        rows = [r for r in matrix if r["shape"] == shape]
        previously_green[shape] = {
            "rows": len(rows),
            "pass": len([r for r in rows if r["verdict"] == "pass"]),
            "still_green": all(r["verdict"] == "pass" for r in rows),
        }

    extra_negative_reasons = sorted({r["reason"].split(":")[0] for r in passing_controls})
    doc = {
        "unit": "ERA-B-GRADE-REHEARSAL-2",
        "date": "2026-10-26",
        "requests_spent": 0,
        "network": "none - offline, no socket to 192.168.2.168, no requests/httpx import",
        "grader": {
            "path": "experiments/ptr-engine/longrun/grade_v5.py",
            "sha256": _sha256(GRADER),
            "card_declared_sha256": CARD_GRADER_SHA,
            "sha_matches_card": _sha256(GRADER) == CARD_GRADER_SHA,
            "sha_before_repair": PRE_REPAIR_SHA,
            "grader_version": g.GRADER_VERSION,
            "rule": g.RULE,
        },
        "harness_pin": {
            "path": "experiments/ptr-engine/measure/HARNESS-PIN.json",
            "recorded_grade_v5_sha256": _pin_grade_sha(),
            "current_grade_v5_sha256": _sha256(GRADER),
            "pin_is_stale": _pin_grade_sha() != _sha256(GRADER),
            "note": "expected and not this unit's business - HARNESS-PIN-GEN5 regenerates "
                    "the pin once BUDGET-STAGE-MAX-TURNS has landed too",
        },
        "fixture": {
            "path": "experiments/ptr-engine/longrun/tasks-v6/LR-01.v8.json",
            "sha256": _sha256(FIXTURE),
            "fixture_version": fixture.get("fixture_version"),
            "checkpoint_turns": fixture.get("checkpoint_turns"),
        },
        "old_artefact": {
            "path": "measure/ERA-B-GRADE-REHEARSAL.json",
            "sha256": _sha256(OLD) if os.path.exists(OLD) else None,
            "grader_sha256": (old_doc or {}).get("grader", {}).get("sha256"),
            "correct_rows": (old_doc or {}).get("verdict_basis", {}).get("correct_rows"),
            "correct_rows_passing": (old_doc or {}).get("verdict_basis", {}).get(
                "correct_rows_passing"),
            "correct_rows_not_passing": (old_doc or {}).get("verdict_basis", {}).get(
                "correct_rows_not_passing"),
            "negative_controls": (old_doc or {}).get("verdict_basis", {}).get(
                "negative_controls"),
            "negative_controls_passed": (old_doc or {}).get("verdict_basis", {}).get(
                "negative_controls_passed"),
            "verdict": (old_doc or {}).get("verdict"),
            "shape_summary": (old_doc or {}).get("shape_summary"),
            "unchanged": True,
        },
        "method": [
            "SAME rows, SAME fixture, SAME derive_truth, SAME nine negative controls as "
            "ERA-B-GRADE-REHEARSAL: only the grader under test moved",
            "truth comes only from grade_v5.derive_truth(fixture) - no hand-typed table",
            "each synthesised answer is parsed by grade_v5.parse_answer_contract and graded by "
            "grade_v5.grade_cell; grade_v5.py is not edited and no contract rule is re-implemented",
            "every row in `matrix` asserts the DERIVED truth, so any non-pass is a rejection of a "
            "correct answer; `controls` are wrong answers and must never pass",
            "every non-pass keeps its verbatim `reason` string; every stripped fragment is kept "
            "in `decoration_stripped`",
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
        "family_movement": families,
        "previously_green": previously_green,
        "controls": controls,
        "additional_controls": additional,
        "wrong_value_mutants": mutants,
        "verdict": verdict,
        "verdict_basis": {
            "correct_rows": len(matrix),
            "correct_rows_passing": len(matrix) - len(failing_correct),
            "correct_rows_not_passing": len(failing_correct),
            "required_by_card_not_passing": len([r for r in failing_correct
                                                 if r["required_by_card"]]),
            "negative_controls": len(controls),
            "negative_controls_passed": len(passing_controls),
            "passing_control_names": [r["control"] for r in passing_controls],
            "additional_controls": len(additional),
            "additional_controls_passed": len(passing_additional),
            "wrong_value_mutants": len(mutants),
            "wrong_value_mutants_passed": len(passing_mutants),
            "movement": "%d -> %d passing" % (
                (old_doc or {}).get("verdict_basis", {}).get("correct_rows_passing", 0),
                len(matrix) - len(failing_correct)),
        },
        "quality_ceiling": {
            "perfect_era_b_arm": "12/12 declared checkpoints - every checkpoint has at least "
                                 "one accepted shape, so a perfect arm scores the full 12",
            "partially_correct_arm": "scores strictly less: %d/%d wrong-value mutants rejected "
                                     "and %d/%d negative controls not passing, so a wrong value "
                                     "still costs its checkpoint"
                                     % (len(mutants) - len(passing_mutants), len(mutants),
                                        len(controls) - len(passing_controls), len(controls)),
            "distinguishes": not passing_mutants and not passing_controls,
        },
        "rejected_shapes": [{
            "shape": r["shape"], "kind": r["kind"], "answer_id": r["answer_id"],
            "verdict": r["verdict"], "reason": r["reason"],
        } for r in failing_correct],
        "grid_quality_precondition": {
            "holds": verdict == "contract_accepts_era_b_correct_answers",
            "why": ("all %d correct rows pass and all %d negative controls fail - era B's "
                    "answer shapes no longer manufacture a zero on the %s grid"
                    % (len(matrix), len(controls), "1,016-request"))
                   if verdict == "contract_accepts_era_b_correct_answers" else
                   ("%d correct rows still do not pass (%s) so the grid can still manufacture "
                    "a fifth zero" % (len(failing_correct),
                                      "/".join(sorted({r["reason"].split(":")[0]
                                                       for r in failing_correct}))))
                   if verdict == "contract_still_rejects" else
                   ("%d of %d negative controls now PASS (%s) - the repair bought accuracy by "
                    "accepting a wrong answer"
                    % (len(passing_controls), len(controls), extra_negative_reasons)),
        },
        "repair_ownership": "GRADE-V5-T4-DECORATION owns the repair; this unit only re-runs the "
                            "rehearsal and edits neither grader, fixture nor threshold",
    }
    return doc


def _pin_grade_sha():
    try:
        with open(PIN, encoding="utf-8") as fh:
            pin = json.load(fh)
    except Exception:
        return None
    for f in pin.get("files", []):
        if f.get("path", "").endswith("grade_v5.py"):
            return f.get("sha256")
    return None


def main(argv=None):
    doc = build()
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as fh:
        json.dump(doc, fh, indent=1, sort_keys=False)
        fh.write("\n")
    print("wrote", OUT)
    print("grader", doc["grader"]["sha256"][:12], "v" + doc["grader"]["grader_version"],
          "sha_matches_card", doc["grader"]["sha_matches_card"])
    print("pin records", (doc["harness_pin"]["recorded_grade_v5_sha256"] or "")[:12],
          "stale", doc["harness_pin"]["pin_is_stale"])
    print("verdict:", doc["verdict"], "|", doc["verdict_basis"]["movement"])
    for s in doc["shape_summary"].items():
        print("  %-28s %s" % (s[0], {k: v for k, v in s[1].items() if k != "kinds"}))
    for f in doc["family_movement"]:
        print("  FAMILY %-34s %d/%d %-10s %s" % (f["family"], f["now_pass"], f["rows"],
                                                 f["status"], f["reason_strings"]))
    for r in doc["matrix"]:
        if r["verdict"] != "pass":
            print("  NONPASS %-42s %-9s %s" % (r["answer_id"], r["verdict"], r["reason"]))
    for c in doc["controls"] + doc["additional_controls"]:
        print("  CONTROL %-32s %-11s %s" % (c["control"], c["verdict"], c["reason"]))
    print("  controls passed: %d/%d | additional passed: %d/%d | mutants passed: %d/%d" % (
        doc["verdict_basis"]["negative_controls_passed"],
        doc["verdict_basis"]["negative_controls"],
        doc["verdict_basis"]["additional_controls_passed"],
        doc["verdict_basis"]["additional_controls"],
        doc["verdict_basis"]["wrong_value_mutants_passed"],
        doc["verdict_basis"]["wrong_value_mutants"]))
    return 0


# ------------------------------------------------------------------------- tests
def test_grader_sha_is_the_repaired_one_and_pin_is_stale():
    doc = build()
    assert doc["grader"]["sha_matches_card"], doc["grader"]
    assert doc["grader"]["sha256"] == CARD_GRADER_SHA
    assert doc["grader"]["sha256"] != PRE_REPAIR_SHA
    assert doc["harness_pin"]["pin_is_stale"] is True, doc["harness_pin"]
    assert doc["harness_pin"]["recorded_grade_v5_sha256"] == PRE_REPAIR_SHA


def test_truth_is_the_same_twelve_checkpoints():
    doc = build()
    assert len(doc["checkpoints"]) == 12
    assert {k: len(v) for k, v in doc["ids_by_kind"].items()} == {"NUM": 5, "CALL": 4, "NONE": 3}
    for cp in doc["checkpoints"]:
        assert cp["derivation_text"], cp


def test_corpus_is_the_same_sixty_four_correct_rows():
    doc = build()
    assert len(doc["matrix"]) == 64, len(doc["matrix"])
    assert all(r["expectation"] == "pass" for r in doc["matrix"])


def test_the_three_previously_green_shapes_are_still_green():
    doc = build()
    green = {"a_canonical": 12, "c_two_line": 12, "d_tool_narration": 12,
             "e1_kwargs_reordered": 4, "g_num_with_citation": 5}
    for shape, rows in green.items():
        s = doc["shape_summary"][shape]
        assert s["rows"] == rows, (shape, s)
        assert s["pass"] == rows, (shape, s)
    for shape, block in doc["previously_green"].items():
        assert block["still_green"], (shape, block)


def test_all_nine_negative_controls_still_fail():
    """THE GATE: 0/9. A control that passes means the repair over-accepts."""
    doc = build()
    assert len(doc["controls"]) == 9
    assert doc["verdict_basis"]["negative_controls_passed"] == 0, doc["verdict_basis"]
    assert [c["control"] for c in doc["controls"] if c["passed"]] == []
    for c in doc["controls"]:
        assert c["verdict"] != "pass", c
    hard = [c for c in doc["controls"] if c["expect"] == "fail"]
    assert len(hard) == 7
    for c in hard:
        assert c["verdict"] == "fail", c


def test_additional_controls_and_mutants_do_not_pass():
    doc = build()
    assert doc["verdict_basis"]["additional_controls_passed"] == 0, doc["additional_controls"]
    assert doc["verdict_basis"]["wrong_value_mutants_passed"] == 0, doc["wrong_value_mutants"]
    assert len(doc["wrong_value_mutants"]) == 12


def test_verdict_is_one_of_three_words():
    doc = build()
    assert doc["verdict"] in ("contract_accepts_era_b_correct_answers",
                              "contract_still_rejects",
                              "contract_over_accepts")
    assert doc["verdict"] == "contract_accepts_era_b_correct_answers", doc["rejected_shapes"]
    assert doc["verdict_basis"]["correct_rows_passing"] == 64
    assert doc["grid_quality_precondition"]["holds"] is True


def test_family_movement_is_recorded_with_reasons():
    doc = build()
    assert {f["family"] for f in doc["family_movement"]} == set(FAMILIES)
    for f in doc["family_movement"]:
        assert f["old_pass"] < f["rows"], f          # every family failed before the repair
        assert f["status"] in ("now pass", "still fail")
        if f["status"] == "now pass":
            assert f["accepting_rule"], f
        else:
            assert f["reason_strings"], f


if __name__ == "__main__":
    raise SystemExit(main())

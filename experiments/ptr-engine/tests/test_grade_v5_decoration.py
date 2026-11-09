#!/usr/bin/env python3
"""test_grade_v5_decoration.py - GRADE-V5-T4-DECORATION: decoration is not a value.

THE MEASURED DEFECT (measure/ERA-B-GRADE-REHEARSAL.json, 64 correct answers):
50 passed, 14 did not, and 11 of the 14 were shapes the card REQUIRES. The rejected
rows carried the SAME value as the passing rows; only decoration differed:
    e2  `CALL f(...) (resolve.py:163)`  0/4  -> call_arg_not_kwarg / kwarg_value_mismatch
    b   `CALL f(...) .`                 4/4 fail, `NONE .` 3/3 undecidable
    f   `NONE - <justification>`        0/3  -> trailing_after_none
`NUM 64.` passed all along, because `_integral_numeral` reads a lone trailing period
as punctuation (grade_v5.py:105, :112-113) while CALL_RE anchors on `\\)\\s*$`
(:68) and the NONE branch compares the whole first token (:217-220). So the grader
rewarded an arm for emitting NOTHING EXTRA and punished an arm for CITING where it
read the value - a metric artefact aimed at exactly one arm of a grid whose thesis
is a pointer discipline.

WHAT THIS FILE PROVES (offline; zero requests; grade_v5.py imported, cell.py untouched):
  1. the rehearsal corpus (64 correct rows + 9 negative controls) now reports
     64/64 pass and 0/9 controls passing;
  2. six RED cases in the SAME decorated shapes still FAIL, each with its verbatim
     reason - a wrong value inside a stripped-decoration shape is still wrong;
  3. the strip is decoration-only: it is recorded per cell (`decoration_stripped`),
     it never re-kinds an answer, and a canonical answer carries an empty strip list.

Run `python3 experiments/ptr-engine/tests/test_grade_v5_decoration.py` to regenerate
`experiments/ptr-engine/measure/GRADE-V5-T4-MATRIX.json`; run pytest for assertions.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))   # experiments/ptr-engine/tests -> repo
LONGRUN = os.path.join(ROOT, "experiments", "ptr-engine", "longrun")
TOOLS = os.path.join(ROOT, "experiments", "ptr-engine", "tools")
for _p in (LONGRUN, TOOLS):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import grade_v5 as g  # noqa: E402

FIXTURE = os.path.join(LONGRUN, "tasks-v6", "LR-01.v8.json")
GRADER = os.path.join(LONGRUN, "grade_v5.py")
OUT = os.path.join(ROOT, "experiments", "ptr-engine", "measure",
                   "GRADE-V5-T4-MATRIX.json")
REHEARSAL = os.path.join(ROOT, "tests", "test_era_b_grade_rehearsal.py")
ERA_A_GRADE = os.path.join(ROOT, "experiments", "ptr-engine", "measure",
                           "cell-pointer-stable-20261026T145722Z.grade-v5.json")
# The A/B baseline is RECONSTRUCTED, not kept on disk: /tmp is per-invocation here, so a
# copied pre-repair file does not survive between calls. `_pristine_source` reverses the
# three insertions of this repair and REFUSES the A/B unless the reconstruction hashes to
# the exact sha the repair started from.
GRADER_SHA_BEFORE = "056eb605e2baf5c91e0cb32d037cd0528e406e6c8527eec55a917a52d9f26772"
PRISTINE_TMP = "/tmp/grade_v5_prefix_T4.py"        # re-derived era-A doc is written here
EM_DASH = "\u2014"

_DECORATION_BLOCK_HEAD = ("# -----------------------------------------------------------------"
                          "- decoration\n")
_DECORATION_CALL = ('    # Repair T4: decoration-only relaxation (trailing period / trailing '
                    'citation or\n'
                    '    # parenthetical / a NONE justification), applied ONCE here, before any '
                    'kind\n'
                    '    # branch. It removes a suffix only; the value, the kind and every verdict '
                    'rule\n'
                    '    # below are untouched, and `detail["decoration_stripped"]` records what '
                    'was cut.\n'
                    '    body = _strip_decoration(body, out["detail"])\n\n')
_DECORATION_CELL = ('            "decoration_stripped": (parsed.get("detail") or {}).get(\n'
                    '                "decoration_stripped") or [],\n')


def _sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def _rehearsal():
    """The rehearsal corpus, imported rather than re-typed.

    Its `_answers`/`_controls` are the single definition of the 64 shapes and the 9
    negative controls; copying them here would be a second copy that drifts.
    """
    spec = importlib.util.spec_from_file_location("_era_b_rehearsal", REHEARSAL)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _derive_truth():
    prev = os.getcwd()
    os.chdir(ROOT)
    try:
        return g.derive_truth(g.load_fixture(FIXTURE))
    finally:
        os.chdir(prev)


def _grade(cell, text):
    parsed = g.parse_answer_contract(text)
    graded = g.grade_cell(cell, parsed)
    return {"verdict": graded["verdict"], "reason": graded["reason"],
            "answer_kind": parsed["answer_kind"],
            "answer_parse_error": parsed["answer_parse_error"],
            "answer_raw": parsed["answer_raw"],
            "asserted": graded.get("asserted"),
            "expected": graded.get("expected"),
            "decoration_stripped": graded.get("decoration_stripped") or []}


# -------------------------------------------------------------------- red cases
def _red_cases(by_id):
    """Six wrong answers in the DECORATED shapes. Must fail, before and after.

    Each names the checkpoint it attacks and the verbatim reason it must keep. These
    are what separates a REPAIR from a LOOSENING: if the strip ever swallows the value
    too, one of these turns green and this file goes red.
    """
    t = by_id["cp.0.t06"]                       # CALL truth: ledger.record_resolution(...)
    good = ("CALL ledger.record_resolution(block_size=scope.block(), "
            "bytes_appended=len(presented.encode('utf-8')), entry_text=entry.text, "
            "scope=scope.name, serialized_ref=presented)")
    wrong_ref = good.replace("serialized_ref=presented", "serialized_ref=text")
    wrong_callee = good.replace("ledger.record_resolution", "ledger.record_resolved")
    num = by_id["cp.2.t12"]                    # NUM truth 64
    none_cp = by_id["cp.3.t14"]                # NONE truth
    return [
        {"red_id": "call_wrong_value_with_provenance",
         "rule": "(b) trailing parenthetical must not hide a wrong kwarg value",
         "checkpoint": "cp.0.t06", "cell": t,
         "answer": "ANSWER: %s (resolve.py:163)" % wrong_ref,
         "expect_verdict": "fail",
         "expect_reason": "kwarg_value_mismatch:serialized_ref"},
        {"red_id": "num_wrong_value_with_period",
         "rule": "(a) a stripped period must not turn 32 into 64",
         "checkpoint": "cp.2.t12", "cell": num,
         "answer": "ANSWER: NUM 32.",
         "expect_verdict": "fail", "expect_reason": "num_mismatch"},
        {"red_id": "call_wrong_callee_with_period",
         "rule": "(a) a stripped period must not launder a wrong callee",
         "checkpoint": "cp.0.t06", "cell": t,
         "answer": "ANSWER: %s." % wrong_callee,
         "expect_verdict": "fail", "expect_reason": "callee_mismatch"},
        {"red_id": "none_justification_naming_a_call",
         "rule": "(c) a justification that NAMES a call is a contradicted denial",
         "checkpoint": "cp.3.t14", "cell": none_cp,
         "answer": "ANSWER: NONE %s actually ledger.record_refusal" % EM_DASH,
         "expect_verdict": "fail",
         "expect_reason": "answer_not_contract:trailing_after_none"},
        {"red_id": "num_not_integer",
         "rule": "(a) only ONE trailing period is punctuation; 64.5 is a fraction",
         "checkpoint": "cp.2.t12", "cell": num,
         "answer": "ANSWER: NUM 64.5",
         "expect_verdict": "fail", "expect_reason": "num_not_integer:64.5"},
        {"red_id": "citation_is_the_whole_answer",
         "rule": "(b) stripping may never empty the answer: a bare citation is no value",
         "checkpoint": "cp.2.t12", "cell": num,
         "answer": "ANSWER: (resolve.py:163)",
         "expect_verdict": "undecidable", "expect_reason": "unparseable"},
    ]


def _run_red(by_id):
    out = []
    for row in _red_cases(by_id):
        graded = _grade(row.pop("cell"), row["answer"])
        row.update(graded)
        row["still_red"] = (graded["verdict"] == row["expect_verdict"]
                            and graded["reason"] == row["expect_reason"])
        out.append(row)
    return out


# ------------------------------------------------------------------ era-A re-drive
def _pristine_source():
    """The pre-repair source, reconstructed by reversing this repair's three insertions.

    Returns (source, how). `how` is "reconstructed" only when the result hashes to
    GRADER_SHA_BEFORE; otherwise the caller must NOT run the A/B (an unverified
    baseline would make "no retroactive change" an unsupported claim).
    """
    src = open(GRADER, encoding="utf-8").read()
    if _DECORATION_BLOCK_HEAD not in src:
        return src, "already_pristine"
    start = src.index(_DECORATION_BLOCK_HEAD)
    end = src.index("def parse_answer_contract(text):", start)
    src = src[:start] + src[end:]
    for needle in (_DECORATION_CALL, _DECORATION_CELL):
        if needle not in src:
            return src, "reconstruction_failed:missing_%s" % needle.split("\n")[0][:30]
        src = src.replace(needle, "", 1)
    ok = hashlib.sha256(src.encode("utf-8")).hexdigest() == GRADER_SHA_BEFORE
    return src, "reconstructed" if ok else "reconstruction_sha_mismatch"


def _load_source(src, name):
    """Exec a grader source as a module without writing it anywhere."""
    import types
    mod = types.ModuleType(name)
    mod.__file__ = GRADER
    exec(compile(src, GRADER, "exec"), mod.__dict__)
    return mod


def _era_a_redrive():
    """Re-derive one existing era-A grade; A/B the pristine grader against this one.

    Two deltas are different things and must not be conflated: (i) stored file vs
    re-derivation (grader VERSION drift, pre-existing - that file records
    grader_sha256 null and suffix-less reasons) and (ii) pristine re-derivation vs
    repaired re-derivation (THIS repair's retroactive effect). Only (ii) belongs to
    this card, and a non-empty (ii) is legal only where `decoration_stripped` is
    non-empty on a row that previously did not pass.
    """
    if not os.path.exists(ERA_A_GRADE):
        return {"status": "baseline_unavailable", "why": "era-A grade file absent"}
    stored = json.load(open(ERA_A_GRADE, encoding="utf-8"))
    rows_path = stored.get("rows_file")
    fixture_path = stored.get("fixture_file")
    if not (rows_path and os.path.exists(rows_path) and fixture_path):
        return {"status": "baseline_unavailable",
                "why": "rows_file/fixture_file unusable: %r %r" % (rows_path, fixture_path)}
    fixture = g.load_fixture(fixture_path if os.path.isabs(fixture_path)
                             else os.path.join(ROOT, fixture_path))
    rows = [json.loads(l) for l in open(rows_path, encoding="utf-8") if l.strip()]
    src, how = _pristine_source()

    prev = os.getcwd()
    os.chdir(ROOT)
    try:
        truth = g.derive_truth(fixture)
        before = g.grade_rows(fixture, rows, truth=truth)
        if how == "already_pristine":
            return {"status": "baseline_unavailable",
                    "why": "grader already pristine - the repair is not in the tree"}
        if how != "reconstructed":
            return {"status": "baseline_unavailable", "why": how,
                    "note": "the A/B baseline could not be verified byte-for-byte"}
        old = _load_source(src, "_pristine_grade_v5").grade_rows(fixture, rows, truth=truth)
    finally:
        os.chdir(prev)

    def key(cell):
        return (cell.get("arm"), cell.get("id"))
    old_by = {key(c): c for c in old["cells"]}
    new_by = {key(c): c for c in before["cells"]}
    deltas = []
    for k in sorted(set(old_by) | set(new_by)):
        o, n = old_by.get(k), new_by.get(k)
        if o is None or n is None:
            deltas.append({"arm": k[0], "id": k[1], "change": "cell_added_or_removed"})
            continue
        if (o.get("verdict"), o.get("reason")) != (n.get("verdict"), n.get("reason")):
            deltas.append({"arm": k[0], "id": k[1],
                           "before": {"verdict": o.get("verdict"), "reason": o.get("reason")},
                           "after": {"verdict": n.get("verdict"), "reason": n.get("reason")},
                           "decoration_stripped": n.get("decoration_stripped") or [],
                           "attributable_to_decoration": bool(
                               n.get("decoration_stripped"))})
    stored_acc = {a: v.get("checkpoint_accuracy") for a, v in (stored.get("arms") or {}).items()}
    pristine_acc = {a: v["checkpoint_accuracy"] for a, v in old["arms"].items()}
    repaired_acc = {a: v["checkpoint_accuracy"] for a, v in before["arms"].items()}
    tmp_copy = None
    try:                                          # the card asks for a /tmp copy
        with open(PRISTINE_TMP, "w", encoding="utf-8") as fh:
            json.dump(before, fh, indent=1, sort_keys=True)
        with open(PRISTINE_TMP + ".pristine", "w", encoding="utf-8") as fh:
            fh.write(src)
        tmp_copy = PRISTINE_TMP
    except OSError:                               # pragma: no cover
        tmp_copy = None
    return {
        "status": "rederived",
        "grade_file": os.path.relpath(ERA_A_GRADE, ROOT),
        "rows_file": os.path.relpath(rows_path, ROOT),
        "fixture_file": fixture_path,
        "rows": len(rows),
        "baseline": how,
        "baseline_sha256": GRADER_SHA_BEFORE,
        "tmp_copy": tmp_copy,
        "stored_accuracy": stored_acc,
        "pristine_rederive_accuracy": pristine_acc,
        "repaired_rederive_accuracy": repaired_acc,
        "pristine_vs_repaired_deltas": deltas,
        "delta_count": len(deltas),
        "stored_vs_repaired_accuracy_changed": stored_acc != repaired_acc,
        "note": ("stored file was written by an unpinned grader (grader_sha256 null, reasons "
                 "without a suffix); stored-vs-rederive drift is pre-existing version drift, "
                 "NOT this repair. Only pristine-vs-repaired is this repair."),
    }


# ------------------------------------------------------------------------ matrix
def build():
    by_id = {t["id"]: t for t in _derive_truth()}
    reh = _rehearsal()
    doc_before_shape = json.load(open(os.path.join(ROOT, "measure",
                                                   "ERA-B-GRADE-REHEARSAL.json"),
                                      encoding="utf-8")) \
        if os.path.exists(os.path.join(ROOT, "measure", "ERA-B-GRADE-REHEARSAL.json")) else {}
    after = reh.build()             # re-runs the SAME corpus through THIS grader

    before_basis = doc_before_shape.get("verdict_basis") or {}
    rows = after["matrix"]
    controls = after["controls"]
    red = _run_red(dict(by_id))

    shape_summary = after["shape_summary"]
    nonpass = [r for r in rows if r["verdict"] != "pass"]
    controls_passed = [c for c in controls if c["passed"]]

    doc = {
        "unit": "GRADE-V5-T4-DECORATION",
        "date": "2026-10-26",
        "offline": True,
        "requests_spent": 0,
        "network": "none - no socket, no requests/httpx import, no live cell, cell.py untouched",
        "grader": {
            "path": "experiments/ptr-engine/longrun/grade_v5.py",
            "sha256_before": GRADER_SHA_BEFORE,
            "sha256_after": _sha256(GRADER),
            "grader_version": g.GRADER_VERSION,
            "rule": g.RULE,
        },
        "fixture": {"path": "experiments/ptr-engine/longrun/tasks-v6/LR-01.v8.json",
                    "sha256": _sha256(FIXTURE)},
        "parser_lines_quoted": {
            "CALL_RE": "68: CALL_RE = re.compile(r\"^([A-Za-z_][\\w.]*)\\s*\\((.*)\\)\\s*$\", re.S)",
            "NUM_HEAD_RE": "71: NUM_HEAD_RE = re.compile(r\"^\\d+\\b\")",
            "_parse_call": "157-159: m = CALL_RE.match((text or \"\").strip()) / if not m: "
                           "return None, \"call_not_parsable\"",
            "NONE_branch": "217-220: if head == \"NONE\": if rest: "
                           "out[\"answer_parse_error\"] = \"trailing_after_none\"; return out",
            "NUM_why_it_already_passed": "105 + 112-113 (_integral_numeral): 'A sentence-final "
                                         "period (`64.`) is punctuation, not a fraction.' / "
                                         "if re.match(r\"^\\.\\d\", tail): return None  -> tail "
                                         "'.' alone is not `.<digit>`, so `64.` asserts 64",
            "body_split": "214-215 (pre-repair): head = body.split(None, 1)[0].upper() -> for "
                          "`NONE .` head is 'NONE' with rest '.' ... and for `NONE <just>` head "
                          "is 'NONE' with a non-empty rest",
            "grade_cell": "587-692: verdict derives from parsed only; NONE 617-647, NUM 653-665, "
                          "CALL 667-692, TEXT 612-615",
        },
        "defect": {
            "measurement": "measure/ERA-B-GRADE-REHEARSAL.json (64 correct rows, 50 pass / 14 not, "
                           "11 card-required; 9 negative controls, 0 passing)",
            "e2": "CALL + provenance parenthetical 0/4: answer_not_contract:call_arg_not_kwarg:) "
                  "(resolve.py:163 / kwarg_value_mismatch:block_size / kwarg_value_mismatch:code",
            "b_on_call": "4 fail: answer_not_contract:call_not_parsable",
            "b_on_none": "3 undecidable: unparseable",
            "f": "0/3 fail: answer_not_contract:trailing_after_none",
            "why_it_is_an_artefact": "every rejected row asserts the SAME value as a passing row; "
                                     "only decoration differs, and NUM already tolerated the same "
                                     "trailing period",
        },
        "rules": [
            {"id": "a", "what": "strip ONE trailing sentence-final '.' (not '..'; '?!' never "
                                "matched because only '.' is stripped), on EVERY kind",
             "where": "grade_v5._strip_decoration, called once from parse_answer_contract "
                      "before the head split / kind branches",
             "guard": "nothing beyond the period is removed; the value is re-read below by the "
                      "unchanged kind branches"},
            {"id": "b", "what": "strip a balanced trailing '(...)' or a trailing citation token "
                                "after a COMPLETE answer",
             "grammar": "citations come from the imported dv.citation_spans (mirrored, not "
                        "re-invented); a parenthetical must be whitespace-separated so the "
                        "call's own ')' is never mistaken for decoration",
             "guard": "_complete_prefix: the remainder must still be a complete answer of the "
                      "SAME kind (CALL must still _parse_call cleanly, NUM must still carry an "
                      "asserted numeral, TEXT non-empty, NONE bare) - decoration never re-kinds"},
            {"id": "c", "what": "allow a short trailing justification after NONE introduced by "
                                "\u2014 / - / ; / ( ; the answer stays a denial",
             "guard": "the payload must carry no value: no numeral, no dotted name, no callable "
                      "'(', no snake_case code token (citations removed first). "
                      "`NONE \u2014 actually ledger.record_refusal` stays trailing_after_none"},
        ],
        "recording": "every removed fragment is kept in cell['decoration_stripped'] (and in "
                     "parsed detail['decoration_stripped'] / detail['body_after_decoration']), "
                     "so a reader sees that the grader DISCARDED something",
        "matrix_after": {
            "correct_rows": len(rows),
            "passing": len(rows) - len(nonpass),
            "not_passing": len(nonpass),
            "nonpassing_rows": [{"answer_id": r["answer_id"], "verdict": r["verdict"],
                                 "reason": r["reason"]} for r in nonpass],
            "shape_summary": shape_summary,
            "rows": rows,
        },
        "before_after": {
            "correct_rows_before_passing": before_basis.get("correct_rows_passing"),
            "correct_rows_before_not_passing": before_basis.get("correct_rows_not_passing"),
            "required_by_card_before_not_passing": before_basis.get("required_by_card_not_passing"),
            "correct_rows_after_passing": len(rows) - len(nonpass),
            "correct_rows_after_not_passing": len(nonpass),
            "verdict_before": doc_before_shape.get("verdict"),
            "verdict_after": after["verdict"],
        },
        "controls_after": {
            "count": len(controls),
            "passed": len(controls_passed),
            "passing_names": [c["control"] for c in controls_passed],
            "rows": controls,
        },
        "red_cases": red,
        "red_cases_all_still_red": all(r["still_red"] for r in red),
        "invariants_held": {
            "thresholds_touched": 0,
            "kind_branches_touched": 0,
            "decidable_fail_semantics_touched": False,
            "non_answer_rule_untouched": sorted(g.NON_ANSWER_ERRORS),
            "turn_missing_rule_untouched": "grade_rows still emits fail/turn_missing for an "
                                           "absent row (untouched code path)",
            "exit_codes_untouched": "grade_v5.main returns 0/3 exactly as before "
                                    "(stamp refusal unchanged)",
            "files_not_edited": ["experiments/ptr-engine/longrun/cell.py",
                                 "experiments/ptr-engine/longrun/run_longrun.py",
                                 "experiments/ptr-engine/longrun/analyze_stats.py",
                                 "HARNESS-PIN.json", "GRID-PARAMS.json",
                                 "measure/ERA-B-GRADE-REHEARSAL.json",
                                 "any fixture / threshold / published page"],
        },
        "era_a_redrive": _era_a_redrive(),
        "known_consequence": {
            "tests/test_era_b_grade_rehearsal.py": (
                "still asserts the PRE-repair rejections (b-on-CALL/b-on-NONE/e2/f and the "
                "'contract_rejects_correct_era_b_answer' verdict). It is outside this card's "
                "write paths and was NOT edited, so those four assertions now fail by design. "
                "Updating them (and regenerating measure/ERA-B-GRADE-REHEARSAL.json) is a "
                "separate decision for the owner of the rehearsal artefact; this card reports "
                "the new matrix in measure/GRADE-V5-T4-MATRIX.json instead."),
        },
        "harness_pin": ("the combined harness digest moved (grade_v5.py sha256 changed), so the "
                        "pin in HARNESS-PIN.json is now stale; it must be regenerated AFTER this "
                        "card and BUDGET-STAGE-MAX-TURNS have both landed - one regeneration, "
                        "not two."),
    }
    doc["verdict"] = ("repair_holds" if not nonpass and not controls_passed
                      and doc["red_cases_all_still_red"] else "repair_does_not_hold")
    return doc


def main(argv=None):
    doc = build()
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as fh:
        json.dump(doc, fh, indent=1, sort_keys=False)
        fh.write("\n")
    print("wrote", os.path.relpath(OUT, ROOT))
    print("grader after:", doc["grader"]["sha256_after"])
    print("before:", doc["before_after"]["correct_rows_before_passing"], "/64 passing;",
          "after:", doc["before_after"]["correct_rows_after_passing"], "/64 passing")
    print("shape_summary:", {k: (v["rows"], v["pass"], v["fail"], v["undecidable"])
                             for k, v in doc["matrix_after"]["shape_summary"].items()})
    print("controls passed:", doc["controls_after"]["passed"], "/", doc["controls_after"]["count"])
    for r in doc["red_cases"]:
        print("  RED %-38s %-11s %s" % (r["red_id"], r["verdict"], r["reason"]))
    print("era_a_redrive:", doc["era_a_redrive"]["status"],
          doc["era_a_redrive"].get("pristine_vs_repaired_deltas"),
          doc["era_a_redrive"].get("repaired_rederive_accuracy"))
    print("verdict:", doc["verdict"])
    return 0


# ------------------------------------------------------------------------- tests
def test_all_64_correct_rows_pass_and_controls_still_fail():
    doc = build()
    assert doc["matrix_after"]["correct_rows"] == 64
    assert doc["matrix_after"]["not_passing"] == 0, doc["matrix_after"]["nonpassing_rows"]
    assert doc["controls_after"]["count"] == 9
    assert doc["controls_after"]["passed"] == 0, doc["controls_after"]["passing_names"]
    assert doc["verdict"] == "repair_holds"


def test_the_11_card_required_shapes_now_pass():
    doc = build()
    ss = doc["matrix_after"]["shape_summary"]
    for shape in ("e2_reordered_plus_provenance", "b_trailing_period",
                  "f_none_with_justification"):
        assert ss[shape]["pass"] == ss[shape]["rows"], (shape, ss[shape])
    assert ss["a_canonical"]["pass"] == 12 and ss["c_two_line"]["pass"] == 12
    assert ss["d_tool_narration"]["pass"] == 12 and ss["e1_kwargs_reordered"]["pass"] == 4
    assert ss["g_num_with_citation"]["pass"] == 5


def test_every_red_case_still_fails_with_its_verbatim_reason():
    by_id = {t["id"]: t for t in _derive_truth()}
    red = _run_red(by_id)
    assert len(red) == 6
    for r in red:
        assert r["still_red"], (r["red_id"], r["verdict"], r["reason"], r["expect_reason"])
    reasons = {r["red_id"]: r["reason"] for r in red}
    assert reasons["call_wrong_value_with_provenance"] == "kwarg_value_mismatch:serialized_ref"
    assert reasons["num_wrong_value_with_period"] == "num_mismatch"
    assert reasons["call_wrong_callee_with_period"] == "callee_mismatch"
    assert reasons["none_justification_naming_a_call"] == \
        "answer_not_contract:trailing_after_none"
    assert reasons["num_not_integer"] == "num_not_integer:64.5"
    assert reasons["citation_is_the_whole_answer"] == "unparseable"


def test_decoration_is_recorded_not_silently_ignored():
    by_id = {t["id"]: t for t in _derive_truth()}
    call = by_id["cp.0.t06"]
    got = _grade(call, "ANSWER: %s (resolve.py:163)" % (
        "CALL ledger.record_resolution(block_size=scope.block(), "
        "bytes_appended=len(presented.encode('utf-8')), entry_text=entry.text, "
        "scope=scope.name, serialized_ref=presented)"))
    assert got["verdict"] == "pass"
    assert got["decoration_stripped"] == ["(resolve.py:163)"], got
    num = _grade(by_id["cp.2.t12"], "ANSWER: NUM 64.")
    assert num["decoration_stripped"] == ["."], num
    none_cp = by_id["cp.3.t14"]
    none = _grade(none_cp, "ANSWER: NONE %s the source defines no such call" % EM_DASH)
    assert none["verdict"] == "pass"
    assert none["decoration_stripped"], none


def test_canonical_answer_strips_nothing():
    by_id = {t["id"]: t for t in _derive_truth()}
    for kind, cid, text in (
            ("NUM", "cp.2.t12", "ANSWER: NUM 64"),
            ("NONE", "cp.3.t14", "ANSWER: NONE"),
            ("CALL", "cp.0.t06",
             "ANSWER: CALL ledger.record_resolution(block_size=scope.block(), "
             "bytes_appended=len(presented.encode('utf-8')), entry_text=entry.text, "
             "scope=scope.name, serialized_ref=presented)")):
        got = _grade(by_id[cid], text)
        assert got["verdict"] == "pass", (kind, got)
        assert got["decoration_stripped"] == [], (kind, got)


def test_the_strip_never_eats_the_call_itself():
    """The CALL's own closing paren must not be mistaken for a parenthetical."""
    d = {}
    assert g._strip_decoration("CALL ledger.record_resolution(scope=scope.name)", d) == \
        "CALL ledger.record_resolution(scope=scope.name)"
    assert d["decoration_stripped"] == []
    d = {}
    assert g._strip_decoration("CALL f(block_size=len(x.encode('utf-8')))", d) == \
        "CALL f(block_size=len(x.encode('utf-8')))"
    assert d["decoration_stripped"] == []


def test_none_justification_carrying_a_value_is_refused():
    """Rule (c) refuses to strip a payload that asserts something."""
    for payload in ("actually ledger.record_refusal",
                    "record_refusal(scope=x)",
                    "the count is 3",
                    "resolve._refuse"):
        d = {}
        out = g._strip_decoration("NONE %s %s" % (EM_DASH, payload), d)
        assert out != "NONE", payload
        assert d["decoration_stripped"] == [], payload


def test_option_parsing_is_unchanged_for_bare_forms():
    """No decoration -> the parse is byte-identical to the pre-repair contract."""
    for text, kind, err in (("ANSWER: NUM 64", "NUM", None),
                            ("ANSWER: NONE", "NONE", None),
                            ("ANSWER: TEXT one line", "TEXT", None),
                            ("", None, "no_answer_line"),
                            ("just prose", None, "prose_only"),
                            ("ANSWER:", None, "empty_answer"),
                            ("ANSWER: NUM", None, "empty_num"),
                            ("ANSWER: six", None, "unparseable")):
        p = g.parse_answer_contract(text)
        assert (p["answer_kind"], p["answer_parse_error"]) == (kind, err), text
        assert not p["detail"].get("decoration_stripped"), text


def test_no_threshold_or_semantics_constant_moved():
    assert g.NON_ANSWER_ERRORS == frozenset({
        "no_answer_line", "prose_only", "empty_answer", "empty_text", "empty_num",
        "unparseable"})
    assert g.GRADER_VERSION == "5.1"
    assert g.CALL_RE.pattern == r"^([A-Za-z_][\w.]*)\s*\((.*)\)\s*$"
    assert g.NUM_HEAD_RE.pattern == r"^\d+\b"


def test_era_a_rederivation_has_no_unattributed_change():
    """A retroactive change is legal ONLY where a decoration strip caused it."""
    er = _era_a_redrive()
    assert er["status"] == "rederived", er
    assert er["baseline"] == "reconstructed", er
    for d in er["pristine_vs_repaired_deltas"]:
        assert d.get("decoration_stripped"), d
        assert d["after"]["verdict"] in ("pass", "fail", "undecidable", "text"), d


if __name__ == "__main__":
    raise SystemExit(main())

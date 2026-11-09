#!/usr/bin/env python3
"""test_checkpoint_items_v2.py - the tasks-v6 grid must be 12/12 DECIDABLE.

Unit CHECKPOINT-ITEMS-V2. `CHECKPOINT-COVERAGE` (f6d1bb5c) shipped a 12-item grid
(`LR-01.v6.json`) and reported honestly that only 8 were gradeable: three items were
`NONE`-kind with no answer form a grader could decide, and `cp.10.t36` died inside
`derive_truth` with `KeyError: 'function'`. `GRADE-V6-DERIVE` then added the NONE and
`call_at_line` branches to `grade_v5`, so the *grader* could decide all 12 - but the
fixture still never DECLARED, per item, the one-line form the model must answer, and
`cp.10.t36` still borrowed its callee from prose documentation instead of its spec.

This file guards the new fixture, `tasks-v6/LR-01.v7.json`:

(a) CENSUS     - 12 items at the twelve original turns, each with a declared
                 `answer_form` naming NUM, CALL or NONE; none TEXT; no turn moved.
(b) AST TRUTH  - every declared truth is re-derived here, independently of
                 `grade_v5.derive_truth`, from the pinned sources by `ast`.
(c) PROBES     - 24 hand-written synthetic markers, no model calls: the declared
                 form passes (12 positives) and one wrong answer per item fails
                 (12 negatives).
(d) T36        - the historical `KeyError: 'function'` seam is gone, the spec now
                 pins `derive.callee`, and its negative answer still fails.
(e) RED/GREEN  - flipping one moved item's declared truth (64 -> 32) makes its
                 positive probe fail; restoring it makes the probe pass.
(f) BYTES      - the two historical fixtures are byte-identical (sha256 pinned).

Run: python3 -m pytest experiments/ptr-engine/longrun/tests/test_checkpoint_items_v2.py -q
"""
import ast
import copy
import hashlib
import json
import os
import sys

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
LONGRUN = os.path.dirname(HERE)
ROOT = os.path.abspath(os.path.join(LONGRUN, "..", "..", ".."))
for _p in (LONGRUN, os.path.join(os.path.dirname(LONGRUN), "tools")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import det_verify as dv                                            # noqa: E402
import grade_v5                                                    # noqa: E402

FIXTURE = os.path.join(LONGRUN, "tasks-v6", "LR-01.v7.json")
V5 = os.path.join(LONGRUN, "tasks-v5", "runtime-v5", "LR-01.v5.json")
V6 = os.path.join(LONGRUN, "tasks-v5", "runtime-v5", "LR-01.v6.json")
RESOLVE = os.path.join(ROOT, "experiments", "ptr-engine", "ptr_engine", "resolve.py")
ERRORS = os.path.join(ROOT, "experiments", "ptr-engine", "ptr_engine", "errors.py")

# historical bytes, measured before this unit started
V5_SHA = "967cef03c362446a3187c9a8517bb6867b03e680f9a673ab53e42bb9f06ab567"
V6_SHA = "ff89625df95dca6ae47dd24db72f43d83c24f9cd371e16938258ec03b7e946db"

TURNS = [6, 8, 12, 14, 18, 20, 24, 26, 32, 36, 42, 46]

# v6 id -> v7 id, in turn order (the map the fixture also stores as `id_map`)
LEGACY = {
    "cp.3.t06": "cp.0.t06",
    "cp.4.t08": "cp.1.t08",
    "cp.0.t12": "cp.2.t12",
    "cp.5.t14": "cp.3.t14",
    "cp.6.t18": "cp.4.t18",
    "cp.7.t20": "cp.5.t20",
    "cp.1.t24": "cp.6.t24",
    "cp.8.t26": "cp.7.t26",
    "cp.9.t32": "cp.8.t32",
    "cp.10.t36": "cp.9.t36",
    "cp.11.t42": "cp.10.t42",
    "cp.2.t46": "cp.11.t46",
}

# one wrong answer per item (hand-written; each is a plausible model mistake)
NEGATIVES = {
    6: ("CALL", "ledger.record_resolution(scope=scope.name, serialized_ref=presented, "
                "block_size=scope.block(), entry_text=entry.text)"),
    8: ("CALL", "scope.enumerated(kind=ref.kind)"),
    12: ("NUM", "32"),
    14: ("CALL", "ledger.record_refusal(scope=scope_name, serialized_ref=text, code=error.code)"),
    18: ("NUM", "5"),
    20: ("CALL", "ledger.resolved_count()"),
    24: ("NUM", "30"),
    26: ("NUM", "6"),
    32: ("NUM", "3"),
    36: ("CALL", "ledger.resolved_count(scope=scope_name)"),
    42: ("CALL", "scope.block()"),
    46: ("CALL", "ledger.record_refusal(scope=scope.name, serialized_ref=text, code=error.code)"),
}


def load(path=FIXTURE):
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def truth_of(fixture=None):
    fixture = fixture if fixture is not None else load()
    return grade_v5.derive_truth(grade_v5.load_fixture(FIXTURE) if fixture is None else fixture)


def grade(rows, fixture=None):
    fixture = fixture if fixture is not None else load()
    return grade_v5.grade_rows(fixture, rows)


def cells_by_arm(doc, arm):
    return {c["id"]: c for c in doc.get("cells", []) if c.get("arm") == arm}


# ------------------------------------------------------------------ (a) the census
def test_census_is_twelve_items_at_the_original_turns():
    fx = load()
    items = sorted(fx["checkpoints"], key=lambda c: int(c["turn"]))
    assert len(items) == 12
    assert [int(c["turn"]) for c in items] == TURNS, "a checkpoint moved off its turn"
    assert len({int(c["turn"]) for c in items}) == 12
    kinds = [c["answer_spec"]["kind"] for c in items]
    assert set(kinds) <= {"NUM", "CALL", "NONE"}
    assert kinds.count("NUM") == 5 and kinds.count("CALL") == 4 and kinds.count("NONE") == 3
    assert "TEXT" not in kinds


def test_every_item_declares_a_machine_checkable_answer_form():
    fx = load()
    for cp in fx["checkpoints"]:
        form = cp.get("answer_form") or ""
        assert form.startswith("ANSWER: "), "%s has no declared answer form" % cp["id"]
        head = form.split()[1]
        assert head == cp["answer_spec"]["kind"], \
            "%s declares form %s but spec kind %s" % (cp["id"], head, cp["answer_spec"]["kind"])
        assert head in ("NUM", "CALL", "NONE")


def test_id_map_is_complete_and_injective():
    fx = load()
    assert fx["id_map"] == LEGACY
    assert sorted(fx["id_map"]) == sorted(LEGACY)
    assert sorted(fx["id_map"].values()) == sorted(LEGACY.values())
    assert len(set(fx["id_map"].values())) == 12
    legacy_in_fixture = {cp["legacy_id"]: cp["id"] for cp in fx["checkpoints"]}
    assert legacy_in_fixture == LEGACY
    real_v6_ids = {cp["id"] for cp in load(V6)["checkpoints"]}
    assert set(LEGACY) == real_v6_ids, "the map omits (or invents) a v6 id"


# --------------------------------------------------------- (b) AST truth, re-derived
def _call_from_tree(tree, attr, function=None, line=None):
    """Independent of grade_v5.derive_truth: walk the AST ourselves."""
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        callee = ast.unparse(node.func)
        if line is not None:
            if node.lineno == line and callee.split(".")[-1] == attr:
                return callee, {a.arg: ast.unparse(a.value) for a in node.keywords}
        elif function is not None and callee.split(".")[-1] == attr:
            if any(isinstance(f, ast.FunctionDef) and f.name == function
                   for f in tree.body):
                inside = [f for f in tree.body
                          if isinstance(f, ast.FunctionDef) and f.name == function]
                for fn in inside:
                    for sub in ast.walk(fn):
                        if isinstance(sub, ast.Call) and \
                                ast.unparse(sub.func).split(".")[-1] == attr:
                            return ast.unparse(sub.func), \
                                {a.arg: ast.unparse(a.value) for a in sub.keywords}
    return None, None


def test_each_truth_is_rederived_from_the_ast_and_matches_the_declaration():
    fx = load()
    rtree, _ = dv.parse_module(RESOLVE)
    etree, _ = dv.parse_module(ERRORS)
    derived = {t["id"]: t for t in grade_v5.derive_truth(fx)}
    for cp in fx["checkpoints"]:
        spec = cp["answer_spec"]
        d = spec.get("derive") or {}
        kind = spec["kind"]
        got = derived[cp["id"]]
        assert got["kind"] == kind
        if kind == "NUM" and d["rule"] == "constant_value":
            value, _line = dv.constant_value(rtree, d["symbol"])
            assert int(value) == int(cp["expected"]) == got["expected"]
        elif kind == "NUM":
            names = dv.count_classes(etree, d["pattern"])
            assert len(names) == int(cp["expected"]) == got["expected"]
        elif kind == "CALL" and d["rule"] == "call_inside_function":
            call = dv.call_inside_function(rtree, d["function"], d["attr"])
            callee, kwargs = _call_from_tree(rtree, d["attr"], function=d["function"])
            assert callee == call["callee"] == got["expected"]["callee"]
            assert kwargs == got["expected"]["kwargs"]
        elif kind == "CALL":
            _callee, kw = _call_from_tree(rtree, d["callee"].split(".")[-1], line=d["line"])
            assert kw == got["expected"]["kwargs"] == {}
            assert _callee == d["callee"] == got["expected"]["callee"]
        else:                                    # NONE: the absence must be real
            fn = [f for f in rtree.body
                  if isinstance(f, ast.FunctionDef) and f.name == d["function"]]
            assert fn, "%s names a function that does not exist" % cp["id"]
            hits = [n for n in ast.walk(fn[0]) if isinstance(n, ast.Call)
                    and ast.unparse(n.func).split(".")[-1] == d["attr"]]
            assert hits == [], "%s truth is NONE but %s is called" % (cp["id"], d["attr"])
            assert got["expected"] == "NONE" and got["call_present"] is False


# -------------------------------------------------------------------- (c) 24 probes
def test_twelve_positives_pass_twelve_negatives_fail():
    fx = load()
    positives, negatives = [], []
    for cp in fx["checkpoints"]:
        positives.append({"arm": "pos", "turn": int(cp["turn"]), "content": cp["answer_form"]})
        kind, body = NEGATIVES[int(cp["turn"])]
        negatives.append({"arm": "neg", "turn": int(cp["turn"]),
                          "content": "ANSWER: %s %s" % (kind, body)})
    assert len(positives) == 12 and len(negatives) == 12
    pos = cells_by_arm(grade(positives, fx), "pos")
    neg = cells_by_arm(grade(negatives, fx), "neg")
    assert len(pos) == 12 and len(neg) == 12
    bad = {i: c["reason"] for i, c in pos.items() if c["verdict"] != "pass"}
    assert not bad, "positives that did not pass: %r" % bad
    good_neg = {i: c["reason"] for i, c in neg.items() if c["verdict"] == "fail"}
    assert len(good_neg) == 12, "negatives that did not fail: %r" % (
        sorted(set(neg) - set(good_neg)))
    assert not any(c["verdict"] == "undecidable" for c in list(pos.values()) + list(neg.values()))


def test_declared_forms_are_identical_to_the_seven_historical_answers():
    """The v5 items' answers must not drift when their ids are renumbered."""
    fx = load()
    forms = {cp["legacy_id"]: cp["answer_form"] for cp in fx["checkpoints"]}
    assert forms["cp.0.t12"] == "ANSWER: NUM 64"
    assert forms["cp.1.t24"] == "ANSWER: NUM 31"
    assert forms["cp.2.t46"] == ("ANSWER: CALL ledger.record_refusal(code=error.code, "
                                 "scope=..., serialized_ref=text)")


# ----------------------------------------------------------------------- (d) t36
def test_t36_keyerror_seam_is_gone_and_the_spec_pins_its_callee():
    fx = load()
    cp = [c for c in fx["checkpoints"] if c["legacy_id"] == "cp.10.t36"][0]
    assert cp["answer_spec"]["derive"]["callee"] == "ledger.resolved_count"
    assert cp["answer_spec"]["derive"]["rule"] == "call_at_line"
    t = [x for x in grade_v5.derive_truth(fx) if x["id"] == cp["id"]][0]   # no KeyError
    assert t["expected"] == {"callee": "ledger.resolved_count", "kwargs": {},
                             "kwargs_as_written": []}
    assert t["derivation"]["line"] == 141
    doc = grade_v5.grade_rows(fx, [{"arm": "neg", "turn": 36,
                                    "content": "ANSWER: CALL ledger.resolved_count(scope=scope_name)"}])
    cell = cells_by_arm(doc, "neg")[cp["id"]]
    assert cell["verdict"] == "fail" and cell["reason"] == "kwarg_set_mismatch"
    assert cell["missing_kwargs"] == [] and cell["extra_kwargs"] == ["scope"]


# ------------------------------------------------------------------- (e) red/green
def test_red_green_flip_of_one_moved_items_truth():
    fx = load()
    cp = [c for c in fx["checkpoints"] if c["legacy_id"] == "cp.0.t12"][0]
    assert cp["expected"] == "64" and cp["answer_form"] == "ANSWER: NUM 64"
    row = [{"arm": "pos", "turn": 12, "content": "ANSWER: NUM 64"}]

    # RED: flip the declared truth 64 -> 32; the AST no longer agrees, so the
    # fixture is refused by name and the positive probe cannot pass.
    red = copy.deepcopy(fx)
    [c for c in red["checkpoints"] if c["legacy_id"] == "cp.0.t12"][0]["expected"] = "32"
    with pytest.raises(SystemExit) as exc:
        grade_v5.derive_truth(red)
    assert "fixture_truth_mismatch" in str(exc.value)
    assert "cp.2.t12" in str(exc.value)

    # GREEN: restore (the on-disk fixture is never mutated) -> probe passes again.
    green = load()
    cell = cells_by_arm(grade(row, green), "pos")["cp.2.t12"]
    assert cell["verdict"] == "pass" and cell["reason"] == "num_equal"
    assert load()["checkpoints"] == fx["checkpoints"]


def test_historical_fixtures_are_byte_identical():
    for path, want in ((V5, V5_SHA), (V6, V6_SHA)):
        with open(path, "rb") as fh:
            assert hashlib.sha256(fh.read()).hexdigest() == want, "%s changed" % path

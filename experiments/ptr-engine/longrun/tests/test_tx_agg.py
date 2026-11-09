"""Offline aggregation test for TX-AGG."""
import json, os, sys, re

HERE = os.path.dirname(os.path.abspath(__file__))
LONGRUN = os.path.dirname(HERE)
ROOT = os.path.abspath(os.path.join(LONGRUN, "..", "..", ".."))
sys.path.insert(0, LONGRUN)
sys.path.insert(0, os.path.join(ROOT, "experiments", "ptr-engine"))

import run_longrun as R  # noqa: E402
import check_pointer_fixtures as CPF  # noqa: E402

FIXTURE = os.path.join(LONGRUN, "tasks-v7", "TX-AGG.v1.json")


def _load():
    return R.load_fixture(FIXTURE)


def _base():
    with open(FIXTURE, encoding="utf-8") as fh:
        return json.load(fh)


def _turn(fx, n):
    return next(t for t in fx["turns"] if t["turn"] == n)


def _body_of(turn):
    tos = turn.get("tool_outputs") or []
    return "\n".join(str(to.get("body", "")) for to in tos)


def test_tx_agg_loads_reachability_only():
    fx = _load()
    assert fx["task_id"] == "TX-AGG"
    assert len(fx["checkpoints"]) == 48
    errs = CPF.validate(fx)
    assert all("not found in" in e and "tool output" in e for e in errs), errs
    assert len(errs) > 0


def test_tx_agg_bucket_counts():
    fx = _load()
    from collections import Counter
    c = Counter(cp["distance"] for cp in fx["checkpoints"])
    assert dict(c) == {2: 12, 6: 12, 20: 12, 32: 12}, c


def test_tx_agg_expected_unique():
    fx = _load()
    vals = [cp["expected"] for cp in fx["checkpoints"]]
    assert len(set(vals)) == 48


def test_tx_agg_48_unique_checkpoint_turns():
    fx = _load()
    turns = R.checkpoint_turns(fx)
    assert len(turns) == 48
    assert len(set(turns)) == 48


def test_tx_agg_keys_schema():
    fx = _base()
    assert fx["schema"] == "consonance.longrun-fixture/2"
    assert fx["generation"] == "gen-7"
    for cp in fx["checkpoints"]:
        for k in ("id", "turn", "distance", "expected", "answer_form", "question"):
            assert k in cp, (cp.get("id"), k)


def test_tx_agg_distances_match_measured_gap():
    fx = _load()
    for cp in fx["checkpoints"]:
        intro = cp.get("fact_introduction_turn", cp.get("introduction_turn", cp.get("intro_turn")))
        assert int(cp["turn"]) - int(intro) == int(cp["distance"]), cp["id"]


def test_body_count_constant_per_group():
    fx = _load()
    tby = {int(t["turn"]): t for t in fx["turns"]}
    intro_turns = {cp["fact_introduction_turn"] for cp in fx["checkpoints"]}
    counts = {int(tn): len(tby[tn].get("tool_outputs", [])) for tn in intro_turns}
    assert len(set(counts.values())) == 1, counts
    assert list(counts.values())[0] == 2, counts


def test_no_expected_value_in_single_body():
    fx = _load()
    expected = {str(cp["expected"]) for cp in fx["checkpoints"]}
    for turn in fx["turns"]:
        for to in (turn.get("tool_outputs") or []):
            body = str(to.get("body", ""))
            for ev in expected:
                if ev in body:
                    raise AssertionError(f"expected {ev} found in body {to.get('doc_id')}")


def test_aggregate_arithmetic_all_checkpoints():
    fx = _load()
    assert len(fx["checkpoints"]) == 48
    assert len({cp["expected"] for cp in fx["checkpoints"]}) == 48


def test_no_constant_first_diff_triple():
    fx = _load()
    vals_by_group = {}
    for d in fx["documents"]:
        m = re.match(r"doc-agg-(g\d+)-f\d+", d["doc_id"])
        if m:
            g = m.group(1)
            v = int(re.search(r"VALUE = (\d+)", d["revisions"][0]["value"]).group(1))
            vals_by_group.setdefault(g, []).append(v)
    for g, vs in vals_by_group.items():
        vs_sorted = sorted(vs)
        for i in range(len(vs_sorted) - 2):
            a, b, c = vs_sorted[i], vs_sorted[i+1], vs_sorted[i+2]
            if b - a == c - b and b - a != 0:
                raise AssertionError(f"constant first diff in {g}: {a},{b},{c}")


def test_expected_not_derivable_from_group_index():
    fx = _load()
    vals_by_group = {}
    for d in fx["documents"]:
        m = re.match(r"doc-agg-(g\d+)-f\d+", d["doc_id"])
        if m:
            g = m.group(1)
            v = int(re.search(r"VALUE = (\d+)", d["revisions"][0]["value"]).group(1))
            vals_by_group.setdefault(g, []).append(v)
    for i, g in enumerate(sorted(vals_by_group)):
        grp_vals = vals_by_group[g]
        total = sum(grp_vals)
        assert total != i * 1000 and total != i, (g, total, i)


def test_question_does_not_encode_answer():
    fx = _load()
    for cp in fx["checkpoints"]:
        q = str(cp.get("question", ""))
        ev = str(cp["expected"])
        assert ev not in q, (cp["id"], ev)


def test_tx_agg_checker_fails_duplicate_expected():
    fx = _base()
    fx["checkpoints"][1]["expected"] = fx["checkpoints"][0]["expected"]
    fx["checkpoints"][1]["answer_form"] = fx["checkpoints"][0]["answer_form"]
    errs = CPF.validate(fx)
    assert any("duplicate expected" in e for e in errs), errs


def test_tx_agg_checker_fails_reachability():
    fx = _base()
    val = fx["checkpoints"][0]["expected"]
    fx["turns"][5]["question"] = f"Work turn 6. {val}"
    errs = CPF.validate(fx)
    assert any("leaked into a turn question" in e for e in errs), errs


def test_tx_agg_checker_fails_distance_mismatch():
    fx = _base()
    fx["checkpoints"][0]["distance"] = 999
    errs = CPF.validate(fx)
    assert any("distance mismatch" in e for e in errs), errs


def test_tx_agg_checker_fails_ungradable():
    fx = _base()
    fx["checkpoints"][0]["answer_form"] = "ANSWER: MAYBE 42"
    errs = CPF.validate(fx)
    assert any("ungradable" in e for e in errs), errs


def test_tx_agg_checker_fails_duplicate_checkpoint_turn():
    fx = _base()
    fx["checkpoints"][1]["turn"] = fx["checkpoints"][0]["turn"]
    errs = CPF.validate(fx)
    assert any("duplicate checkpoint turn" in e for e in errs), errs


def test_tx_agg_red_green_body_count():
    fx = _base()
    tby = {int(t["turn"]): t for t in fx["turns"]}
    intro = sorted({cp["fact_introduction_turn"] for cp in fx["checkpoints"]})[0]
    tby[intro]["tool_outputs"].pop()
    counts = {int(tn): len(tby[tn].get("tool_outputs", [])) for tn in {cp["fact_introduction_turn"] for cp in fx["checkpoints"]}}
    assert len(set(counts.values())) != 1, counts


def test_tx_agg_reachability_inherent():
    fx = _base()
    val = fx["checkpoints"][0]["expected"]
    fx["turns"][5]["question"] = f"Work turn 6. {val}"
    errs = CPF.validate(fx)
    assert any("leaked into a turn question" in e for e in errs), errs
    fx2 = _load()
    errs2 = [e for e in CPF.validate(fx2) if "leaked into a turn question" not in e]
    # reachability errors remain (inherent); no other errors
    assert all("not found in" in e and "tool output" in e for e in errs2), errs2

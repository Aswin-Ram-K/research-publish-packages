"""TX-04 (E3): the distance-64 probe fixture, asserted from the fixture alone.

`PREREG-SPCC.md` §E3 asks whether the observed distance cliff is a property of
*position* or of *eviction*.  The design needs a fixture whose deepest probe sits
at distance 64 and whose fact bodies are still present at every probe turn, so a
cliff that survives with the body present is positional.

These tests read only `tasks-v7/TX-04.v1.json` (plus the generator, to prove the
file is the generator's output and not a hand edit).  No model is called.
"""
from __future__ import annotations

import collections
import hashlib
import json
import os
import re
import subprocess
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
_LONGRUN = os.path.dirname(_HERE)
_PTR_ENGINE = os.path.dirname(_LONGRUN)
_REPO = os.path.dirname(os.path.dirname(_PTR_ENGINE))
for _p in (_LONGRUN, _PTR_ENGINE):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import arm_cd  # noqa: E402
import run_longrun  # noqa: E402
from ptr_engine.pointer_table import build_table, fetch  # noqa: E402
from ptr_engine.quantise import StubTokenizer  # noqa: E402

FIXTURE_PATH = os.path.join(_LONGRUN, "tasks-v7", "TX-04.v1.json")
SPEC_PATH = os.path.join(_LONGRUN, "fixtures-spec", "TX-04.spec.json")
GENERATOR = os.path.join(_PTR_ENGINE, "tools", "build_fixture.py")
INDEX_TURN = 1
MAKE_REF_RE = re.compile(r"^doc-[A-Za-z0-9_.-]+@r\d+$")

DISTANCES = (2, 8, 20, 32, 64)
# 8 checkpoints per distance is 40; the fixture carries 48, so the remaining 8
# are spread over the three shallowest buckets.
DISTRIBUTION = {2: 10, 8: 10, 20: 10, 32: 9, 64: 9}
CHECKPOINTS = 48
DEEPEST = 64


def _fixture() -> dict:
    with open(FIXTURE_PATH, "r", encoding="utf-8") as fh:
        return json.load(fh)


def _sha256(path: str) -> str:
    with open(path, "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()


def _delivery_turns(fixture: dict) -> dict:
    """doc_id -> the turns whose tool_outputs carry that document's body."""
    out = collections.defaultdict(list)
    for turn in fixture["turns"]:
        for to in turn.get("tool_outputs") or []:
            out[to["doc_id"]].append(int(turn["turn"]))
    return out


# ---------------------------------------------------------------- generation

def test_fixture_is_the_generators_output():
    """The file on disk is byte-identical to what the spec generates."""
    r = subprocess.run(
        [sys.executable, GENERATOR, "--spec", SPEC_PATH, "--check",
         "--variant", "tx04", "--out", FIXTURE_PATH],
        cwd=_REPO, capture_output=True, text=True,
    )
    assert r.returncode == 0, (r.stdout, r.stderr)
    assert _sha256(FIXTURE_PATH) in r.stdout, r.stdout


def test_fixture_loads_and_passes_the_pointer_checker():
    import check_pointer_fixtures as CPF

    fx = run_longrun.load_fixture(FIXTURE_PATH)
    assert CPF.validate(fx) == [], CPF.validate(fx)


# ---------------------------------------------------------------- distances

def test_every_distance_is_in_the_prereg_set():
    fx = _fixture()
    seen = {int(cp["distance"]) for cp in fx["checkpoints"]}
    assert seen <= set(DISTANCES), "distance outside {2,8,20,32,64}: %r" % (sorted(seen),)


def test_distance_equals_probe_turn_minus_introduction_turn():
    fx = _fixture()
    for cp in fx["checkpoints"]:
        intro = int(cp["fact_introduction_turn"])
        assert int(cp["turn"]) - intro == int(cp["distance"]), cp["id"]


def test_deepest_probe_is_at_distance_64():
    fx = _fixture()
    deepest = max(int(cp["distance"]) for cp in fx["checkpoints"])
    assert deepest == DEEPEST, deepest
    at_64 = [cp for cp in fx["checkpoints"] if int(cp["distance"]) == DEEPEST]
    assert at_64, "no checkpoint at distance 64"
    # the deepest probe turn is the last turn any distance-64 checkpoint probes
    assert max(int(cp["turn"]) for cp in at_64) == max(int(cp["turn"]) for cp in fx["checkpoints"])


def test_checkpoint_count_and_distribution():
    fx = _fixture()
    cps = fx["checkpoints"]
    assert len(cps) == CHECKPOINTS, len(cps)
    got = dict(collections.Counter(int(cp["distance"]) for cp in cps))
    assert got == DISTRIBUTION, got
    assert sum(DISTRIBUTION.values()) == CHECKPOINTS
    # the distribution is stated in the fixture itself, not only in this test
    assert fx["e3_design"]["distribution"] == {str(k): v for k, v in DISTRIBUTION.items()}
    assert fx["e3_design"]["checkpoints"] == CHECKPOINTS


def test_checkpoint_turns_are_unique():
    fx = _fixture()
    turns = [int(cp["turn"]) for cp in fx["checkpoints"]]
    assert len(set(turns)) == len(turns), "two probes share a turn"
    assert sorted(turns) == [int(t) for t in fx["checkpoint_turns"]]


# ---------------------------------------------------------------- body present

def test_every_body_is_delivered_strictly_before_its_probe():
    fx = _fixture()
    delivered = _delivery_turns(fx)
    for cp in fx["checkpoints"]:
        doc = cp["ground_truth"]["doc"]
        probe = int(cp["turn"])
        turns = delivered.get(doc, [])
        assert turns, "%s: body of %s is never delivered" % (cp["id"], doc)
        before = [t for t in turns if t < probe]
        assert before, "%s: body of %s is not delivered before probe turn %d (delivered at %r)" % (
            cp["id"], doc, probe, turns)
        assert min(before) == int(cp["fact_introduction_turn"]), cp["id"]


def test_delivered_body_is_the_ground_truth_value():
    fx = _fixture()
    bodies = {}
    for turn in fx["turns"]:
        for to in turn.get("tool_outputs") or []:
            bodies.setdefault(to["doc_id"], set()).add(to["body"])
    for cp in fx["checkpoints"]:
        doc = cp["ground_truth"]["doc"]
        assert cp["ground_truth"]["value"] in bodies[doc], cp["id"]
        assert cp["expected"] in cp["ground_truth"]["value"], cp["id"]


def test_body_is_never_masked_at_the_probe_turn():
    """No probe turn carries a masking/forget instruction, and the fact doc is live."""
    fx = _fixture()
    docs = {d["doc_id"]: d for d in fx["documents"]}
    by_turn = {int(t["turn"]): t for t in fx["turns"]}
    for cp in fx["checkpoints"]:
        doc = docs[cp["ground_truth"]["doc"]]
        assert doc["revoked"] is False, "%s: fact doc is revoked" % cp["id"]
        assert doc["scope"] == "granted", cp["id"]
        rev = next(r for r in doc["revisions"] if r["revision"] == cp["ground_truth"]["revision"])
        assert int(rev["live_from_turn"]) <= int(cp["turn"]), cp["id"]
        question = by_turn[int(cp["turn"])]["question"].upper()
        for token in ("MASK", "FORGET", "EVICT", "DROP"):
            assert token not in question, "%s: probe turn asks to %s" % (cp["id"], token)


# ---------------------------------------------------------------- index refs

def _index_refs(lines) -> list:
    refs = []
    for line in lines:
        parts = line.split()
        assert len(parts) == 4 and parts[0] == "-", "malformed index line: %r" % (line,)
        assert parts[3].isdigit(), "index line has no byte length: %r" % (line,)
        refs.append(parts[1])
    return refs


def _fetch_table(fixture: dict, turn: int = INDEX_TURN) -> dict:
    state = arm_cd.ArmCDState(fixture=fixture, tokenizer=StubTokenizer())
    seen, uniq = set(), []
    for entry in state.all_entries(turn):
        if entry.ref in seen:
            continue
        seen.add(entry.ref)
        uniq.append(entry)
    return build_table(uniq)


def _assert_index_fetchable(fx: dict, turn: int) -> int:
    lines = arm_cd.world_index_lines(fx, turn)
    assert lines, "index is empty at turn %d: the model is shown no addressable ref" % turn
    table = _fetch_table(fx, turn)
    budget = int(fx["fetch_budget_tokens"])
    tok = StubTokenizer()
    refs = _index_refs(lines)
    bad = []
    for ref in refs:
        res = fetch(table, ref, budget_tokens=budget, tokenizer=tok,
                    tool_call_id="tx04-index-ref-check")
        if res.outcome != "OK":
            bad.append((ref, res.outcome))
    assert not bad, "turn %d index advertises refs the fetch tool rejects: %r" % (turn, bad)
    return len(refs)


def test_every_index_ref_is_fetchable():
    """The `b38db8a` invariant: every ref the world index advertises fetches OK.

    Checked at the opening turn and at every probe turn, because a fact document
    only becomes addressable at its introduction turn.
    """
    fx = _fixture()
    assert _assert_index_fetchable(fx, INDEX_TURN) == len(
        arm_cd.world_index_lines(fx, INDEX_TURN))
    for turn in sorted({int(cp["turn"]) for cp in fx["checkpoints"]}):
        _assert_index_fetchable(fx, turn)


def test_index_advertises_each_fact_from_its_introduction_turn():
    fx = _fixture()
    for fact in fx["facts"]:
        turn = int(fact["introduction_turn"])
        refs = _index_refs(arm_cd.world_index_lines(fx, turn))
        for ref in refs:
            assert MAKE_REF_RE.match(ref), "index ref is not make_ref form: %r" % (ref,)
        ref = "%s@r1" % fact["doc_id"]
        assert ref in refs, "index omits %r at its introduction turn %d" % (ref, turn)
        res = fetch(_fetch_table(fx, turn), ref,
                    budget_tokens=int(fx["fetch_budget_tokens"]),
                    tokenizer=StubTokenizer(), tool_call_id="tx04-fact-ref")
        assert res.outcome == "OK", (ref, res.outcome)

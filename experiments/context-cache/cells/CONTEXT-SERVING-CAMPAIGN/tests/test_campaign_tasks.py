"""Tests for CAMPAIGN-TASKS task and quality instrument (V2)."""
from __future__ import annotations

import json
import sys
from pathlib import Path

CAMPAIGN = Path(__file__).resolve().parents[1]
TASKS = CAMPAIGN / "tasks"
sys.path.insert(0, str(TASKS))
sys.path.insert(0, str(TASKS / "contain"))

import gen_instances  # noqa: E402
import grade  # noqa: E402
from runner import run_contained  # noqa: E402

INST_DIR = TASKS / "instances"
TASK_IDS = ["D1", "D2", "D3", "D4", "H1", "H2", "H3", "H4"]
MASK_AFTER = 6


def _load(tid):
    return json.loads((INST_DIR / f"{tid}.json").read_text(encoding="utf-8"))


def _early_dep_turns(inst, mask_after=MASK_AFTER):
    """Turns whose answer needs a source turn earlier than itself and <= mask_after."""
    out = []
    for t in inst["turns"]:
        if any(rt < t["n"] and rt <= mask_after for rt in t["requires_turns"]):
            out.append(t["n"])
    return out


def test_instances_exist_and_schema():
    for tid in TASK_IDS:
        inst = _load(tid)
        assert inst["schema"] == "cs.task/1"
        assert inst["task_id"] == tid
        assert len(inst["turns"]) == 12
        split = "discovery" if tid.startswith("D") else "heldout"
        assert inst["split"] == split
        for t in inst["turns"]:
            assert set(t.keys()) >= {
                "n", "event", "question", "answer_contract", "expect",
                "requires_turns", "expect_exact_body",
            }
            assert isinstance(t["answer_contract"], list) and t["answer_contract"]
            assert isinstance(t["expect"], dict)
            assert isinstance(t["requires_turns"], list) and t["requires_turns"]
            assert all(isinstance(x, int) and 1 <= x <= 12 for x in t["requires_turns"])
            assert isinstance(t["expect_exact_body"], bool)


def test_seed_determinism():
    a = gen_instances.generate_all()
    b = gen_instances.generate_all()
    for tid in a:
        assert json.dumps(a[tid], sort_keys=True) == json.dumps(b[tid], sort_keys=True)
    for tid in ["D1", "H4"]:
        ondisk = json.loads((INST_DIR / f"{tid}.json").read_text())
        assert ondisk["seed"] == a[tid]["seed"]


def test_two_distinct_families_per_split():
    discovery = [_load(t) for t in TASK_IDS if t.startswith("D")]
    heldout = [_load(t) for t in TASK_IDS if t.startswith("H")]
    d_fams = {i["family"] for i in discovery}
    h_fams = {i["family"] for i in heldout}
    assert len(d_fams) == 2, d_fams
    assert len(h_fams) == 2, h_fams
    assert d_fams.isdisjoint(h_fams), (d_fams, h_fams)
    for fam in d_fams:
        assert sum(1 for i in discovery if i["family"] == fam) == 2
    for fam in h_fams:
        assert sum(1 for i in heldout if i["family"] == fam) == 2

    def contract_keys(inst):
        keys = set()
        for t in inst["turns"]:
            for line in t["answer_contract"]:
                keys.add(str(line).split("=", 1)[0].strip())
        return keys

    d_keys = set().union(*(contract_keys(i) for i in discovery))
    h_keys = set().union(*(contract_keys(i) for i in heldout))
    assert d_keys.isdisjoint(h_keys), (d_keys, h_keys)


def test_requires_turns_match_replay():
    """Independently recompute which source turns each answer needs."""
    # Aggregate families: every current answer depends on all observations so far.
    for tid in ("D1", "D2", "H1", "H2"):
        for t in _load(tid)["turns"]:
            assert t["requires_turns"] == list(range(1, t["n"] + 1)), (tid, t["n"])

    # File-state recall: previous value came from the turn that last set the key.
    for tid in ("D3", "D4"):
        last_set = {}
        for t in _load(tid)["turns"]:
            key = t["event"]["key"]
            expected = [last_set[key]] if key in last_set else [t["n"]]
            assert t["requires_turns"] == expected, (tid, t["n"], t["requires_turns"], expected)
            last_set[key] = t["n"]

    # H3: base at 1, precedence rule at 2, defaults at 3-6, requests need [2, base_src].
    h3 = _load("H3")["turns"]
    base_src = {}
    for t in h3:
        if t["n"] == 1:
            for key in t["event"]["base"]:
                base_src[key] = 1
        elif 3 <= t["n"] <= 6:
            base_src[t["event"]["key"]] = t["n"]
    for t in h3:
        n = t["n"]
        if n == 1:
            expected = [1]
        elif n == 2:
            expected = [2]
        elif n <= 6:
            expected = [n]
        else:
            expected = [2, base_src[t["event"]["key"]]]
        assert t["requires_turns"] == expected, ("H3", n, t["requires_turns"], expected)

    # H4: base/precedence at 1; constraint turns 2-6; requests need 1 + applicable early turns.
    h4 = _load("H4")["turns"]
    applicable = {}
    for t in h4[:6]:
        if t["n"] >= 2:
            applicable.setdefault(t["event"]["key"], []).append(t["n"])
    for t in h4:
        n = t["n"]
        if n == 1:
            expected = [1]
        elif n <= 6:
            expected = [n]
        else:
            expected = [1] + applicable.get(t["event"]["key"], [])
        assert t["requires_turns"] == expected, ("H4", n, t["requires_turns"], expected)


def test_dependency_count_at_least_six():
    for tid in TASK_IDS:
        inst = _load(tid)
        early = _early_dep_turns(inst)
        assert len(early) >= 6, (tid, early)
        # encoded dependency must agree with a fresh re-generation
        regen = gen_instances.generate_all()[tid]
        assert [t["requires_turns"] for t in inst["turns"]] == [
            t["requires_turns"] for t in regen["turns"]
        ]


def test_exact_body_turn_present():
    total = 0
    non_numeric = 0
    for tid in TASK_IDS:
        inst = _load(tid)
        for t in inst["turns"]:
            if not t.get("expect_exact_body"):
                continue
            total += 1
            vals = [str(v) for v in t["expect"].values()]
            if any(not v.lstrip("-").isdigit() for v in vals):
                non_numeric += 1
    assert total >= 1
    assert non_numeric >= 1


def test_exact_body_not_in_current_event():
    """An exact-body turn must not have its answer visible in the current event."""
    seen = 0
    for tid in TASK_IDS:
        for t in _load(tid)["turns"]:
            if not t.get("expect_exact_body"):
                continue
            seen += 1
            event = json.dumps(t["event"], sort_keys=True)
            for v in t["expect"].values():
                assert str(v) not in event, (tid, t["n"], v, event)
    assert seen >= 1


def test_reference_passes():
    for tid in TASK_IDS:
        inst = _load(tid)
        for t in inst["turns"]:
            ans = "\n".join(t["answer_contract"])
            res = grade.grade_turn(t, ans, "stop")
            assert res["ok"] is True, (tid, t["n"], res)
            assert not res["silent"]
            assert not res["length_exhausted"]


def test_wrong_answer_fails():
    inst = _load("D1")
    t = inst["turns"][0]
    wrong = t["answer_contract"][0].split("=", 1)[0] + "=999999"
    res = grade.grade_turn(t, wrong, "stop")
    assert res["ok"] is False
    assert res["mismatched"] or res["missing"] == []


def test_missing_key_fails():
    # D2 has a two-key contract (range + count)
    inst = _load("D2")
    t = inst["turns"][0]
    assert len(t["answer_contract"]) == 2
    ans = t["answer_contract"][0]  # omit the second key
    res = grade.grade_turn(t, ans, "stop")
    assert res["ok"] is False
    assert t["answer_contract"][1].split("=", 1)[0] in res["missing"]


def test_hardcoded_breaks_under_perturbed_seed():
    inst = _load("D1")
    perturbed = gen_instances.gen_d1(inst["seed"] + 1)
    key = inst["turns"][0]["answer_contract"][0].split("=", 1)[0]
    failures = 0
    for i, t in enumerate(perturbed):
        a = f"{key}={inst['turns'][i]['answer_contract'][0].split('=', 1)[1]}"
        r = grade.grade_turn(t, a, "stop")
        if r["ok"] is not True:
            failures += 1
    assert failures > 0


def test_unresolved_reference_fails():
    inst = _load("D1")
    t = inst["turns"][0]
    ans = t["answer_contract"][0] + "\nref=deadbeef"
    res = grade.grade_turn(t, ans, "stop")
    assert res["ok"] is False
    assert "ref" in res["extra"]


def test_truncation_ok_null():
    inst = _load("D1")
    t = inst["turns"][0]
    res = grade.grade_turn(t, "", "length")
    assert res["ok"] is None
    assert res["length_exhausted"] is True
    res2 = grade.grade_turn(t, "", "stop")
    assert res2["ok"] is False


def test_silent_classification():
    inst = _load("D2")
    t = inst["turns"][0]
    res = grade.grade_turn(t, "   ", "stop")
    assert res["silent"] is True


def test_containment_network_denied():
    import os
    wd = "/home/zer0null/scratchpad/ct-net"
    os.makedirs(wd, exist_ok=True)
    r = run_contained(
        'python3 -c "import socket; socket.create_connection((\\"1.1.1.1\\",80),timeout=2)"',
        wd, timeout=20,
    )
    assert r["containment_engaged"] is True
    assert (r["refused"] is True) or (r["returncode"] not in (0, None))


def test_containment_outside_write_denied():
    import os
    wd = "/home/zer0null/scratchpad/ct-write"
    os.makedirs(wd, exist_ok=True)
    r = run_contained("echo x > /tmp/outside_write_test.txt", wd, timeout=20)
    assert r["containment_engaged"] is True
    assert r["returncode"] != 0
    assert not Path("/tmp/outside_write_test.txt").exists()


def test_containment_inside_write_allowed():
    import os
    wd = "/home/zer0null/scratchpad/ct-inside"
    os.makedirs(wd, exist_ok=True)
    r = run_contained("echo hello > inside.txt && cat inside.txt", wd, timeout=20)
    assert r["containment_engaged"] is True
    assert r["returncode"] == 0
    assert "hello" in r["stdout"]


def test_bwrap_available():
    import subprocess
    out = subprocess.run(["bwrap", "--version"], capture_output=True, text=True)
    assert out.returncode == 0
    assert "bubblewrap" in (out.stdout + out.stderr)

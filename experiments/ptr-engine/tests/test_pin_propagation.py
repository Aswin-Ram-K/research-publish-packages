"""LAUNCHER-GEN6-WIRE: the pin a launcher obeys and the pin the record carries agree.

Generation 6 (efefd885...) is the tree after TOOL-CHANNEL-WIRE moved client.py and
run_longrun.py. These tests pin the *propagation*, not one constant:

* the launcher's signed-off expectation equals the record (both halves: generation
  and digest), so a launcher cannot follow a newer pin silently;
* a record with a different digest is refused, and the refusal names BOTH digests;
* the launch-contract row greps a symbol that exists (PIN_EXPECTED_DIGEST, not the
  deleted HARNESS_PIN constant), so "regex not found" cannot masquerade as a value
  disagreement;
* an anchor that matches nothing is reported as ANCHOR-MISSING -- a named failure
  mode -- and still fails the check;
* judging generation 6 finds the tree unmoved, judging generation 5 finds it moved
  and names the two files TOOL-CHANNEL-WIRE wrote.
"""
import json
import os
import shutil
import sys

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
ENG = os.path.abspath(os.path.join(HERE, ".."))
ROOT = os.path.abspath(os.path.join(ENG, "..", ".."))
TOOLS = os.path.join(ENG, "tools")
PIN = os.path.join(ENG, "measure", "HARNESS-PIN.json")

GEN6 = "efefd8859c3fdeeac288157ba5bceba1bbe4144947af441721a5f4c4369579b3"
GEN5 = "35ff41b7bbf37f0df28b4307da8d514fea7d324ef22f719b61ee036b73cb5adb"

if TOOLS not in sys.path:
    sys.path.insert(0, TOOLS)


def _record():
    with open(PIN, encoding="utf-8") as fh:
        return json.load(fh)


def _load(name):
    import importlib.util
    spec = importlib.util.spec_from_file_location(name, os.path.join(TOOLS, name + ".py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_launcher_expectation_equals_the_record():
    """The launcher's signed-off expectation IS the record's current value.

    This used to assert the record was still generation 6 (generation 6's digest, GEN6).
    That stopped being true at generation 7 and the assertion had been red since — a guard
    that pins a number instead of the coupling it cares about. It now pins the coupling:
    the launcher must agree with whatever the record's current generation and digest are,
    the record may not go backwards past 6, and generation 6 remains reachable in the
    record for the historical test below.
    """
    rec = _record()
    ras = _load("run_a_star")
    assert rec["generation"] >= 6, rec["generation"]
    assert ras.PIN_EXPECTED_GENERATION == rec["generation"]
    assert ras.PIN_EXPECTED_DIGEST == rec["harness_sha256"]
    # the launcher passes exactly the value it read from the record
    assert ras.pinned_digest() == rec["harness_sha256"]
    # generation 6's digest is still ON the record, as history, not as the live value
    assert GEN6 in json.dumps(rec), "the record dropped generation 6's digest"


def test_the_flag_the_launcher_passes_carries_the_digest():
    src = open(os.path.join(TOOLS, "run_a_star.py"), encoding="utf-8").read()
    # cell_argv is the only argv builder; it appends the pair, never a literal
    assert '"--expect-harness", pinned_digest()' in src


def test_a_record_with_a_wrong_digest_is_refused_naming_both(tmp_path):
    rec = _record()
    bad = dict(rec)
    bad["harness_sha256"] = "0" * 64
    path = tmp_path / "HARNESS-PIN.json"
    path.write_text(json.dumps(bad), encoding="utf-8")
    ras = _load("run_a_star")
    with pytest.raises(SystemExit) as exc:
        ras.pinned_digest(str(path))
    msg = str(exc.value)
    # the coupling, not a frozen generation's number: the refusal must name the digest the
    # launcher was signed off to expect and the digest the record carried.
    assert ras.PIN_EXPECTED_DIGEST in msg, "the refusal must name the signed-off digest it expected"
    assert "0" * 64 in msg, "the refusal must name the digest the record carried"
    assert "disagrees" in msg


def test_the_contract_row_greps_a_live_symbol():
    lcd = _load("launch_contract_diff")
    row = [c for c in lcd.checks(lcd.ROOT) if c["id"] == "harness_pin_digest"][0]
    greps = [p for p in row["probes"] if p["type"] == "grep"]
    assert greps, "the digest row must anchor on the launcher"
    assert any("PIN_EXPECTED_DIGEST" in p["regex"] for p in greps)
    assert not any("^HARNESS_PIN" in p["regex"] for p in greps), (
        "the deleted constant must not be the anchor")
    probes = [lcd.run_probe(lcd.ROOT, p) for p in row["probes"]]
    missing = [p for p in probes if not p["ok"] and not p.get("absent")]
    assert not missing, "every anchor on the digest row must resolve: %r" % (
        [(p["path"], p["problem"]) for p in missing])


def test_a_missing_anchor_is_a_named_failure_mode(tmp_path):
    lcd = _load("launch_contract_diff")
    (tmp_path / "gone.py").write_text("# the symbol moved away\n", encoding="utf-8")
    probe = lcd.G("gone.py", r'^EXPECTED = "([0-9a-f]{64})"')
    got = lcd.run_probe(str(tmp_path), probe)
    assert got["ok"] is False
    assert got["problem_kind"] == "anchor-missing"
    chk = lcd.check("t", "t", [probe], "authoritative", "none")
    status, _probes, reason = lcd.classify(str(tmp_path), chk)
    assert status == "ANCHOR-MISSING", status
    assert "no anchor found" in reason


def test_the_current_generation_matches_the_tree_and_generation_5_names_the_movers():
    """The live generation describes the bytes on disk; the 5 -> 6 move still names its two
    inputs.

    Rewritten 2026-11-11. The body this replaces asserted that *generation 6's* recorded
    values equalled the live tree, which is only true while generation 6 is the top of the
    chain: three pinned inputs (client.py, grade_v5.py, run_longrun.py) moved after it froze,
    so the assertion had been red since generation 8 and then died outright with
    ``ValueError: no pin generation 6 in HARNESS-PIN.json (have: 8)``.

    Red→green: against the generation-8 record this test fails at the first assertion's
    resolution step; against generation 9 it passes. The invariant it now holds is the one
    that matters before a launch — the current record matches the tree, and the historical
    blocks are still ON the record with their own digests.
    """
    lcd = _load("launch_contract_diff")
    rec = _record()
    current = lcd.build(lcd.ROOT, lcd.resolve_scope(lcd.ROOT, generation=rec["generation"]))
    moved = [n for n in current["numbers"] if n["status"] == "MOVED"]
    assert not moved, "generation %s must match the tree: %r" % (
        rec["generation"], [(n["id"], n["reason"]) for n in moved])

    g8 = rec.get("supersedes_generation_8")
    g6 = rec.get("superseded_pin_generation_6")
    assert isinstance(g8, dict) and g8.get("generation") == 8
    assert isinstance(g6, dict) and g6.get("generation") == 6
    g5 = g6.get("supersedes_pin_generation_5")
    assert isinstance(g5, dict) and g5.get("generation") == 5
    digests = [rec["harness_sha256"], g8["harness_sha256"], g6["harness_sha256"],
               g5["harness_sha256"]]
    assert len(set(digests)) == 4, "a preserved generation repeats another's digest: %r" % digests

    per = lambda block: {f["name"]: f["sha256"] for f in block["files"]}
    moved_names = sorted(n for n in per(g6) if per(g5).get(n) != per(g6)[n])
    assert moved_names == ["client.py", "run_longrun.py"], moved_names
    for name in moved_names:
        assert name in g6["cause"], "generation 6's cause does not name %s" % name

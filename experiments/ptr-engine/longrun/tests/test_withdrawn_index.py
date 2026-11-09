"""Tests for tools/withdrawn_index.py - the guard over measure/WITHDRAWN.json.

The load-bearing pair is `test_guard_fires_on_verbatim_p95` (a paragraph quoting WI-004 verbatim,
no correction) and `test_guard_clean_when_correction_attached` (the same paragraph with its
withdrawal attached). If the second passed without the first failing, the guard would be blind;
if the first passed without the second, it would be unusable.
"""
import json
import os
import subprocess
import sys

import pytest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))
TOOL = os.path.join(ROOT, "experiments", "ptr-engine", "tools", "withdrawn_index.py")
REG = os.path.join(ROOT, "experiments", "ptr-engine", "measure", "WITHDRAWN.json")

VERBATIM = (
    "G7 V4-TOOLS pointer-stable came in at p95 318.14 [235.00, 526.41] n=68, "
    "so the latency section publishes that interval as the arm's tail."
)
WITHDRAWN_ATTACHED = VERBATIM + (
    " (WITHDRAWN: the de-duplicated sample is n=51, below the n>=60 order-statistic floor, "
    "and dedupe rule R is disputed -- see WITHDRAWN.json WI-004; no replacement p95 exists.)"
)

def run(*args):
    return subprocess.run([sys.executable, TOOL, *args], capture_output=True, text=True, cwd=ROOT)

def register():
    with open(REG, encoding="utf-8") as fh:
        return json.load(fh)

def write(tmp_path, name, text):
    p = tmp_path / name
    p.write_text(text, encoding="utf-8")
    return str(p)

def test_register_exists_and_has_eight_seeds():
    reg = register()
    ids = [e["id"] for e in reg["entries"]]
    assert len(reg["entries"]) >= 8
    assert len(ids) == len(set(ids)), "duplicate entry ids"
    assert reg["counts"]["seeded"] == 8

def test_tool_and_register_are_where_the_register_says():
    assert os.path.isfile(TOOL), TOOL
    assert os.path.isfile(REG), REG

def test_self_test_passes():
    r = run("--self-test")
    assert r.returncode == 0, r.stdout + r.stderr

def test_guard_fires_on_verbatim_p95(tmp_path):
    p = write(tmp_path, "bad.md", VERBATIM + "\n")
    r = run("--check", p)
    assert r.returncode == 1, r.stdout
    assert "WI-004" in r.stdout

def test_guard_clean_when_correction_attached(tmp_path):
    p = write(tmp_path, "good.md", WITHDRAWN_ATTACHED + "\n")
    r = run("--check", p)
    assert r.returncode == 0, r.stdout
    assert "CLEAN" in r.stdout

def test_no_replacement_entry_is_legitimate_and_kept():
    """WI-004 must keep the literal phrase: 'none — no replacement exists' is a result, not a gap."""
    e = [x for x in register()["entries"] if x["id"] == "WI-004"][0]
    assert e["superseded_by"]["path"] == "none — no replacement exists"
    assert e["superseded_by"]["number"] == "none — no replacement exists"

def test_every_superseded_by_opens_or_says_none():
    for e in register()["entries"]:
        sp = e["superseded_by"]["path"]
        if sp.startswith("none"):
            assert "none — no replacement exists" in sp
            continue
        full = sp if os.path.isabs(sp) else os.path.join(ROOT, sp)
        assert os.path.isfile(full), f"{e['id']}: {sp} does not exist"
        assert os.path.getsize(full) > 0, f"{e['id']}: {sp} is empty"

def test_every_decided_by_handoff_exists():
    for e in register()["entries"]:
        hp = os.path.join(ROOT, e["decided_by"]["handoff"])
        assert os.path.isfile(hp), f"{e['id']}: {e['decided_by']['handoff']} does not exist"
        with open(hp, encoding="utf-8") as fh:
            json.load(fh)  # every decided_by must be a machine-readable record

def test_required_fields_and_enums():
    req = ("id", "claim", "claim_ref", "kind", "status", "superseded_by", "decided_by", "date",
           "still_citable", "quote", "markers")
    for e in register()["entries"]:
        for k in req:
            assert e.get(k), f"{e['id']}: missing {k}"
        assert e["kind"] in {"wrong_denominator", "wrong_unit", "unsound_rule",
                             "retracted_finding", "overstated_mechanism"}, e["id"]
        assert e["status"] in {"withdrawn", "superseded", "disputed"}, e["id"]
        assert e["still_citable"] in {"never", "only with the correction attached"}, e["id"]

@pytest.mark.parametrize("entry", register()["entries"], ids=[e["id"] for e in register()["entries"]])
def test_each_entry_fires_bare_and_cleans_with_its_correction(tmp_path, entry):
    """Red -> green per entry: the bare quote must fire, and the same quote + a marker must not."""
    bare = f"The draft states {entry['quote']} for that arm."
    p1 = write(tmp_path, f"bare_{entry['id']}.md", bare + "\n")
    r1 = run("--check", p1)
    assert r1.returncode == 1, f"{entry['id']} did not fire: {r1.stdout}"
    assert entry["id"] in r1.stdout

    marker = entry["markers"][0]
    fixed = f"The draft states {entry['quote']} for that arm ({marker} -- see WITHDRAWN.json {entry['id']})."
    p2 = write(tmp_path, f"fixed_{entry['id']}.md", fixed + "\n")
    r2 = run("--check", p2)
    assert r2.returncode == 0, f"{entry['id']} did not clean: {r2.stdout}"

def test_unknown_file_is_an_error_not_a_pass():
    r = run("--check", "/nonexistent/does-not-exist.md")
    assert r.returncode != 0

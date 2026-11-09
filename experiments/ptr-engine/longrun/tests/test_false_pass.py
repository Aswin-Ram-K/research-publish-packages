#!/usr/bin/env python3
"""Tests for the false-pass register and its drift check (FALSE-PASS-REGISTER).

The register is additive evidence about handoffs that say done/pass with no
substance; the audit only measures coverage + sha256 freshness. These tests pin
both halves: the register must parse and carry the contracted fields, and the
check must fail loudly when a handoff or a register entry drifts.
"""
import json
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
TOOL = ROOT / "experiments" / "ptr-engine" / "tools" / "false_pass_audit.py"
REGISTER = ROOT / "experiments" / "ptr-engine" / "measure" / "FALSE-PASS.json"
HANDOFFS = ROOT / "orchestration" / "handoffs"

CLASSES = {"substantive_elsewhere", "false_pass", "stub", "superseded"}
FIELDS = ("path", "sha256", "unit", "status_word", "classification",
          "evidence", "artefacts_checked", "checked_at")


def run(*args):
    return subprocess.run([sys.executable, str(TOOL), "--check", *map(str, args)],
                          capture_output=True, text=True, cwd=str(ROOT))


def load_register():
    return json.loads(REGISTER.read_text())


def test_register_parses_and_is_well_formed():
    reg = load_register()
    assert reg["flagged_code"] == "E_STATUS_WORD_CONTRADICTION"
    entries = reg["entries"]
    assert len(entries) >= 3, "the three flagged R2 records must all be registered"
    for e in entries:
        for f in FIELDS:
            assert f in e, "entry %s missing %s" % (e.get("path"), f)
        assert e["classification"] in CLASSES, e["classification"]
        assert e["sha256"] and len(e["sha256"]) == 64
        assert e["evidence"].strip(), "classification without quoted evidence"
        assert isinstance(e["artefacts_checked"], list)
        assert (ROOT / e["path"]).is_file(), e["path"]
    assert reg["counts"]["flagged"] == len(entries)


def test_real_tree_passes():
    r = run()
    assert r.returncode == 0, r.stdout + r.stderr
    assert "OK register covers every flagged record" in r.stdout


def test_mutated_sha_in_register_fails(tmp_path):
    reg = load_register()
    reg["entries"][0]["sha256"] = "0" * 64
    bad = tmp_path / "FALSE-PASS.json"
    bad.write_text(json.dumps(reg))
    r = run("--register", bad)
    assert r.returncode == 1, r.stdout
    assert Path(reg["entries"][0]["path"]).name in r.stdout
    assert "edited after registration" in r.stdout


def test_fourth_flagged_record_fails(tmp_path):
    """A new done/pass handoff with no substance must break the check."""
    handoffs = tmp_path / "handoffs"
    handoffs.mkdir()
    for e in load_register()["entries"]:
        shutil.copy2(ROOT / e["path"], handoffs / Path(e["path"]).name)
    new = handoffs / "FOURTH-FLAGGED.json"
    new.write_text(json.dumps({"unit": "FOURTH-FLAGGED", "status": "done",
                               "write_paths": ["x"], "blocker": "",
                               "next_unit_hint": ""}))
    r = run("--handoffs", handoffs)
    assert r.returncode == 1, r.stdout
    assert "FOURTH-FLAGGED.json" in r.stdout
    assert "not in the register" in r.stdout


def test_substantive_record_is_not_flagged(tmp_path):
    """Negative control: a done handoff with a substance key must not be flagged."""
    handoffs = tmp_path / "handoffs"
    handoffs.mkdir()
    for e in load_register()["entries"]:
        shutil.copy2(ROOT / e["path"], handoffs / Path(e["path"]).name)
    (handoffs / "CONTROL.json").write_text(json.dumps({
        "unit": "CONTROL", "status": "done", "write_paths": ["x"], "blocker": "",
        "next_unit_hint": "", "checks": ["a reader can re-run this"]}))
    r = run("--handoffs", handoffs)
    assert r.returncode == 0, r.stdout

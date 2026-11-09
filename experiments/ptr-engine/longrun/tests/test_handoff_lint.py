"""Tests for experiments/ptr-engine/tools/handoff_lint.py.

Each test fails against a linter that does not implement the check it names, so the
suite doubles as the red->green record for the codes in docs/HANDOFF-LINT.md.

Run: python3 -m pytest experiments/ptr-engine/longrun/tests/test_handoff_lint.py -q
"""

import glob as glob_mod
import importlib.util
import json
import os
import sys

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", "..", "..", ".."))
TOOL = os.path.join(REPO, "experiments", "ptr-engine", "tools", "handoff_lint.py")


def load_tool():
    spec = importlib.util.spec_from_file_location("handoff_lint", TOOL)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


hl = load_tool()


def write(d, name, obj, raw=None):
    p = os.path.join(str(d), name)
    with open(p, "w", encoding="utf-8") as fh:
        if raw is not None:
            fh.write(raw)
        else:
            json.dump(obj, fh, indent=1)
    return p


@pytest.fixture()
def ws(tmp_path):
    """A fake workspace root with one real artifact and a units dir."""
    (tmp_path / "orchestration" / "handoffs").mkdir(parents=True)
    (tmp_path / "orchestration" / "units").mkdir(parents=True)
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "REAL.md").write_text("real\n", encoding="utf-8")
    return tmp_path


def codes(rec):
    return [e["code"] for e in rec["errors"]]


def test_valid_unit_handoff_is_green(ws):
    p = write(ws / "orchestration" / "handoffs", "OK.json", {
        "unit": "OK", "status": "done", "artifacts": ["docs/REAL.md"],
        "evidence": {"command": "ls docs", "commands": ["ls docs"]},
        "blocker": "", "next_unit_hint": "none", "write_paths": ["docs/REAL.md"],
    })
    rec = hl.lint_file(p, str(ws), strict=False)
    assert rec["shape"] == "unit"
    assert rec["errors"] == []
    assert rec["warnings"] == []


def test_valid_verifier_verdict_is_green(ws):
    p = write(ws / "orchestration" / "handoffs", "V.json", {
        "unit": "V1", "overall": "pass", "checks": ["C1 confirmed"],
        "blocker": "", "next_unit_hint": "none", "write_paths": [],
    })
    rec = hl.lint_file(p, str(ws), strict=False)
    assert rec["shape"] == "verifier"
    assert rec["errors"] == []


def test_E_PARSE_unparseable(ws):
    p = write(ws / "orchestration" / "handoffs", "BAD.json", None, raw='{"unit": "BAD", ')
    rec = hl.lint_file(p, str(ws), strict=False)
    assert "E_PARSE" in codes(rec)


def test_E_SHAPE_neither_shape(ws):
    p = write(ws / "orchestration" / "handoffs", "SHAPE.json", {"unit": "X", "notes": "hello"})
    rec = hl.lint_file(p, str(ws), strict=False)
    assert rec["shape"] == "neither"
    assert "E_SHAPE" in codes(rec)


def test_E_MISSING_KEY_unit_requires_evidence(ws):
    p = write(ws / "orchestration" / "handoffs", "MISS.json", {
        "unit": "M", "status": "partial", "artifacts": ["docs/REAL.md"],
        "blocker": "", "next_unit_hint": "n", "write_paths": [],
    })
    rec = hl.lint_file(p, str(ws), strict=False)
    assert "E_MISSING_KEY" in codes(rec)
    assert any("evidence" in e["detail"] for e in rec["errors"] if e["code"] == "E_MISSING_KEY")


def test_E_ARTIFACT_ABSENT_reports_path_verbatim(ws):
    p = write(ws / "orchestration" / "handoffs", "ABS.json", {
        "unit": "A", "status": "done", "artifacts": ["docs/ghost.md"],
        "evidence": {"command": "ls", "commands": ["ls"]},
        "blocker": "", "next_unit_hint": "n", "write_paths": [],
    })
    rec = hl.lint_file(p, str(ws), strict=False)
    assert "E_ARTIFACT_ABSENT" in codes(rec)
    assert any(e["detail"] == "docs/ghost.md" for e in rec["errors"] if e["code"] == "E_ARTIFACT_ABSENT")


def test_E_DONE_NO_EVIDENCE(ws):
    p = write(ws / "orchestration" / "handoffs", "NOEV.json", {
        "unit": "N", "status": "done", "artifacts": ["docs/REAL.md"],
        "evidence": {}, "blocker": "", "next_unit_hint": "n", "write_paths": [],
    })
    rec = hl.lint_file(p, str(ws), strict=False)
    assert "E_DONE_NO_EVIDENCE" in codes(rec)


def test_E_DONE_NO_ARTIFACTS(ws):
    p = write(ws / "orchestration" / "handoffs", "NOART.json", {
        "unit": "NA", "status": "done", "artifacts": [],
        "evidence": {"command": "x", "commands": ["x"]},
        "blocker": "", "next_unit_hint": "n", "write_paths": [],
    })
    rec = hl.lint_file(p, str(ws), strict=False)
    assert "E_DONE_NO_ARTIFACTS" in codes(rec)


def test_E_STUB_partial_with_nothing(ws):
    p = write(ws / "orchestration" / "handoffs", "STUB.json", {
        "unit": "S", "status": "partial", "artifacts": [], "blocker": "",
        "next_unit_hint": "n", "write_paths": [],
    })
    rec = hl.lint_file(p, str(ws), strict=False)
    assert "E_STUB" in codes(rec)


def test_W_NO_COMMANDS_warns_not_fails(ws):
    p = write(ws / "orchestration" / "handoffs", "WNC.json", {
        "unit": "W", "status": "partial", "artifacts": ["docs/REAL.md"],
        "evidence": {"count": "1"},
        "blocker": "", "next_unit_hint": "n", "write_paths": [],
    })
    rec = hl.lint_file(p, str(ws), strict=False)
    assert [w["code"] for w in rec["warnings"]] == ["W_NO_COMMANDS"]
    assert rec["errors"] == []
    strict = hl.lint_file(p, str(ws), strict=True)
    assert "W_NO_COMMANDS" in [e["code"] for e in strict["errors"]]


def test_mid_write_is_skipped_not_error(ws, monkeypatch):
    p = write(ws / "orchestration" / "handoffs", "MOVE.json", {"unit": "MW"})
    calls = {"n": 0}
    real = hl.read_stable

    def flaky(path):
        b, _ = real(path)
        calls["n"] += 1
        return b, calls["n"] == 1  # first read looks mid-write

    monkeypatch.setattr(hl, "read_stable", flaky)
    rec = hl.lint_file(p, str(ws), strict=False)
    assert rec["skipped_mid_write"] is True
    assert rec["errors"] == []
    summary = hl.summarize([rec])
    assert summary["skipped_mid_write"] == 1
    assert summary["counts_by_code"] == {}


def test_exit_codes(ws, capsys):
    d = str(ws / "orchestration" / "handoffs")
    write(ws / "orchestration" / "handoffs", "OK.json", {
        "unit": "OK", "status": "done", "artifacts": ["docs/REAL.md"],
        "evidence": {"command": "ls", "commands": ["ls"]},
        "blocker": "", "next_unit_hint": "n", "write_paths": [],
    })
    assert hl.main([d, "--quiet"]) == 0
    write(ws / "orchestration" / "handoffs", "ABS.json", {
        "unit": "A", "status": "done", "artifacts": ["docs/ghost.md"],
        "evidence": {"command": "ls", "commands": ["ls"]},
        "blocker": "", "next_unit_hint": "n", "write_paths": [],
    })
    assert hl.main([d, "--quiet"]) == 1
    assert hl.main([os.path.join(str(ws), "nope"), "--quiet"]) == 2


def test_summary_counts_and_done_missing(ws):
    d = str(ws / "orchestration" / "handoffs")
    write(ws / "orchestration" / "handoffs", "D.json", {
        "unit": "D", "status": "done", "artifacts": ["docs/ghost.md"],
        "evidence": {"command": "ls", "commands": ["ls"]},
        "blocker": "", "next_unit_hint": "n", "write_paths": [],
    })
    recs = [hl.lint_file(p, str(ws), strict=False) for p in hl.collect([d], str(ws))]
    s = hl.summarize(recs)
    assert s["files_scanned"] == 1
    assert s["counts_by_code"]["E_ARTIFACT_ABSENT"] == 1
    assert s["done_claims_with_missing_artifacts"] == 1


# --- status:"recovered" — a third valid terminal status with its own duties -------------
# The hole this set closes: `recovered` matched no check at all, so a record could claim
# it, list nothing and lint clean.

RECOVERED_DIR = os.path.join(REPO, "orchestration", "handoffs", "recovered")


def recovered_doc(**over):
    d = {
        "unit": "R1", "status": "recovered", "artifacts": ["docs/REAL.md"],
        "evidence": {"command": "ls docs", "commands": ["ls docs"]},
        "blocker": "", "next_unit_hint": "none", "write_paths": ["docs/REAL.md"],
        "recovery": {"from_stub_sha256": "a" * 64, "evidence_basis": "re-ran the stub"},
    }
    d.update(over)
    return d


def test_recovered_empty_record_fails_with_no_evidence_code(ws):
    """(a) the hole: an empty recovered record used to lint clean."""
    p = write(ws / "orchestration" / "handoffs", "REC-EMPTY.json", {"unit": "RE", "status": "recovered"})
    rec = hl.lint_file(p, str(ws), strict=False)
    assert rec["shape"] == "unit"                       # no E_SHAPE for the third status
    assert "E_SHAPE" not in codes(rec)
    assert "E_RECOVERED_NO_EVIDENCE" in codes(rec)
    assert "E_MISSING_KEY" in codes(rec)
    assert rec["ok"] is False
    assert hl.main([str(ws / "orchestration" / "handoffs"), "--quiet"]) == 1


def test_recovered_with_evidence_and_provenance_is_green(ws):
    """(b) a substantiated recovered record exits 0."""
    p = write(ws / "orchestration" / "handoffs", "REC-OK.json", recovered_doc())
    rec = hl.lint_file(p, str(ws), strict=False)
    assert rec["errors"] == []
    assert "E_STUB" not in codes(rec)
    assert hl.main([str(ws / "orchestration" / "handoffs"), "--quiet"]) == 0


def test_recovered_missing_from_stub_sha256(ws):
    """(c) provenance is required: from_stub_sha256 (and evidence_basis) must be present."""
    p = write(ws / "orchestration" / "handoffs", "REC-NOPROV.json", recovered_doc(
        recovery={"evidence_basis": "re-ran the stub"}))
    rec = hl.lint_file(p, str(ws), strict=False)
    assert "E_RECOVERED_NO_PROVENANCE" in codes(rec)
    assert any("from_stub_sha256" in e["detail"] for e in rec["errors"]
               if e["code"] == "E_RECOVERED_NO_PROVENANCE")

    p2 = write(ws / "orchestration" / "handoffs", "REC-NOBASIS.json", recovered_doc(
        recovery={"from_stub_sha256": "b" * 64}))
    assert "E_RECOVERED_NO_PROVENANCE" in codes(hl.lint_file(p2, str(ws), strict=False))


def test_recovered_with_neither_evidence_nor_artifacts_is_a_stub(ws):
    p = write(ws / "orchestration" / "handoffs", "REC-STUB.json", {
        "unit": "RS", "status": "recovered", "artifacts": [], "evidence": {},
        "blocker": "", "next_unit_hint": "n", "write_paths": [],
        "recovery": {"from_stub_sha256": "c" * 64, "evidence_basis": "b"},
    })
    rec = hl.lint_file(p, str(ws), strict=False)
    assert "E_STUB" in codes(rec)
    assert "E_RECOVERED_NO_EVIDENCE" in codes(rec)


def test_recovered_absent_artifact_is_reported(ws):
    p = write(ws / "orchestration" / "handoffs", "REC-ABS.json", recovered_doc(artifacts=["docs/ghost.md"]))
    rec = hl.lint_file(p, str(ws), strict=False)
    assert any(e["detail"] == "docs/ghost.md" for e in rec["errors"] if e["code"] == "E_ARTIFACT_ABSENT")


def test_all_eight_recovered_records_lint_with_defined_exit_code():
    """(d) every file in orchestration/handoffs/recovered/ is linted, each exit 0/1/2."""
    files = sorted(glob_mod.glob(os.path.join(RECOVERED_DIR, "*.json")))
    assert len(files) == 8, files
    for f in files:
        rec = hl.lint_file(f, REPO, strict=False)
        assert rec["shape"] == "unit"
        assert hl.main([f, "--quiet", "--root", REPO]) in (0, 1, 2)
        print(f"{os.path.basename(f)} exit={hl.main([f, '--quiet', '--root', REPO])} "
              f"codes={codes(rec) or '-'}")


def test_partial_and_stub_unchanged_and_exit_code_always_defined(ws):
    """(3)(4) partial/stub behaviour untouched; every invocation returns 0/1/2, never None."""
    d = str(ws / "orchestration" / "handoffs")
    partial = write(ws / "orchestration" / "handoffs", "P.json", {
        "unit": "P", "status": "partial", "artifacts": ["docs/REAL.md"],
        "evidence": {"count": "1"}, "blocker": "", "next_unit_hint": "n", "write_paths": [],
    })
    rec = hl.lint_file(partial, str(ws), strict=False)
    assert rec["errors"] == []
    assert [w["code"] for w in rec["warnings"]] == ["W_NO_COMMANDS"]
    assert hl.main([d, "--quiet"]) == 0
    # W_NO_COMMANDS promotion under --strict is unchanged (pre-existing: promoted into
    # errors, but the exit code is still driven by E_* codes only)
    assert [e["code"] for e in hl.lint_file(partial, str(ws), strict=True)["errors"]] == ["W_NO_COMMANDS"]
    assert hl.main([d, "--quiet", "--strict"]) == 0
    assert hl.main([os.path.join(str(ws), "nope"), "--quiet"]) == 2
    for argv in ([d, "--quiet"], [d, "--quiet", "--strict"], [os.path.join(str(ws), "nope")]):
        code = hl.main(argv)
        assert isinstance(code, int) and code in (0, 1, 2), (argv, code)

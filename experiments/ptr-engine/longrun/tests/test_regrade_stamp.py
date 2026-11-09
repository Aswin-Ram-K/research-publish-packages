#!/usr/bin/env python3
"""Unit REGRADE-STAMP-WIRE - regrade RESOLVES the grader and stamps like grade_v5.

THE TWO DEFECTS (V-STAMP-NEUTRAL, partial with evidence: null):

  F1  tools/regrade.py pinned DEFAULT_GRADER_SHA = 6893d559...3077. GRADER-STAMP
      changed grade_v5.py to 056eb605...26772, so that pin was stale: regrade
      either reported drift that was not drift or refused a grade it should
      reproduce. The sha must be RESOLVED at run time through grader_identity.py,
      with any pin kept only as an expectation the resolver compares against.

  F2  regrade output was not stamped like grade_v5's: it carried grader_sha256 and
      grader_path but no grader_version / rows_sha256, so a regrade output and a
      fresh grade were distinguishable in provenance.

WHAT THIS FILE PINS
  (a) no stale hard-coded digest decides identity: the sha is hashed from the
      grader file now, and equals `sha256sum longrun/grade_v5.py`;
  (b) a regrade-produced document carries all three stamp keys with grade_v5's
      meaning (gi.is_stamped() and gi.grader_identity() agree), and rows_sha256 is
      the rows file's own digest;
  (c) a pre-stamp document regrades IDENTICAL, with the three stamp keys reported
      as provenance-only -- so the stamp is the ONLY added provenance;
  (d) RED->GREEN: an /tmp copy of regrade.py with the pre-stamp pin restored is
      refused (exit 3, both digests quoted), while the resolver version reproduces
      the same grid cleanly;
  (e) a deliberately edited /tmp copy of grade_v5.py is CAUGHT: drift reported,
      `--sha256` refuses it, and the stamp records the edited digest. Drift stays
      detectable precisely because it is resolved, not pinned.

OFFLINE, stdlib + pytest. No stored grade file is edited or restamped.
    python3 -m pytest experiments/ptr-engine/longrun/tests/test_regrade_stamp.py -q
"""
import hashlib
import importlib.util
import json
import os
import shutil
import subprocess
import sys

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
ENGINE = os.path.dirname(os.path.dirname(HERE))
TOOLS = os.path.join(ENGINE, "tools")
LONGRUN = os.path.join(ENGINE, "longrun")
TOOL = os.path.join(TOOLS, "regrade.py")
GRADER = os.path.join(LONGRUN, "grade_v5.py")
FIXTURE = os.path.join(LONGRUN, "tasks-v5", "runtime-v5", "LR-01.v5.json")
HISTORICAL = os.path.join(ENGINE, "measure",
                          "cell-longrun-base-20261026T1556Z.grade-v5.json")
HISTORICAL_ROWS = os.path.join(ENGINE, "measure", "rows-longrun-2026-10-26.jsonl")
AS_OF = "2026-01-01T00:00:00+00:00"
OLD_PIN = "6893d559518168e3ba4fc4a9f5d7642d213d61e2e3c3d0b0a8f01e3379af3077"
STAMP_KEYS = ("grader_sha256", "grader_version", "rows_sha256")

for _p in (LONGRUN, TOOLS):
    if _p not in sys.path:
        sys.path.insert(0, _p)
import grader_identity as gi     # noqa: E402

PY = sys.executable


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def run(*args, env=None):
    e = dict(os.environ)
    if env:
        e.update(env)
    return subprocess.run([PY] + list(args), capture_output=True, text=True,
                          cwd=ENGINE, env=e)


def cli(*args, env=None):
    return run(TOOL, *args, env=env)


def load_regrade_module(path=TOOL, name="regrade_under_test"):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def load_grader_module():
    spec = importlib.util.spec_from_file_location("grade_v5_for_test", GRADER)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture()
def rows(tmp_path):
    p = tmp_path / "rows-stamp.jsonl"
    recs = [
        {"arm": "pointer-stable", "turn": 12, "content": "ANSWER: NUM 64"},
        {"arm": "pointer-stable", "turn": 24, "content": "ANSWER: NUM 31"},
        {"arm": "transcript-grow", "turn": 12, "content": "ANSWER: NONE"},
    ]
    p.write_text("\n".join(json.dumps(r) for r in recs) + "\n", encoding="utf-8")
    return str(p)


def make_grade(rows_path, out_dir):
    r = cli("--rows", rows_path, "--out-dir", str(out_dir), "--as-of", AS_OF)
    assert r.returncode == 0, r.stdout + r.stderr
    return os.path.join(str(out_dir),
                        os.path.splitext(os.path.basename(rows_path))[0]
                        + ".grade-v5.json")


# ------------------------------------------------------------------ F1: resolver
def test_a_no_stale_pin_identity_is_resolved_at_run_time():
    src = open(TOOL, encoding="utf-8").read()
    assert OLD_PIN not in src, "the pre-stamp digest must not survive in regrade.py"
    assert "DEFAULT_GRADER_SHA =" not in src, "the pin is no longer the identity source"
    assert "EXPECTED_GRADER_SHA" in src and "resolve_grader_identity" in src

    mod = load_regrade_module()
    ident = mod.resolve_grader_identity(GRADER)
    assert ident["sha256"] == sha256(GRADER)          # executed, not assumed
    assert ident["sha256"] == mod.EXPECTED_GRADER_SHA
    assert ident["drift"] is False
    assert ident["source"] == "resolved"

    # an explicit expectation that disagrees is drift, never a silent accept
    stale = mod.resolve_grader_identity(GRADER, expected=OLD_PIN)
    assert stale["drift"] is True
    assert stale["sha256"] == sha256(GRADER)
    assert stale["expected"] == OLD_PIN


# --------------------------------------------------------------- F2: all stamps
def test_b_a_regrade_document_carries_all_three_stamps(rows, tmp_path):
    grade = make_grade(rows, tmp_path / "out")
    doc = json.loads(open(grade, encoding="utf-8").read())
    assert [k for k in STAMP_KEYS if not doc.get(k)] == []
    assert doc["grader_sha256"] == sha256(GRADER)
    assert doc["rows_sha256"] == sha256(rows)
    assert doc["grader_version"] == load_grader_module().GRADER_VERSION
    assert gi.is_stamped(doc) is True
    ident = gi.grader_identity(doc)
    assert ident["source"] == "stamp" and ident["stamped"] is True
    assert ident["sha256"] == sha256(GRADER)


def test_c_pre_stamp_document_regrades_identical(rows, tmp_path):
    """Strip only the stamps from a good document: nothing else may differ."""
    grade = make_grade(rows, tmp_path / "out")
    doc = json.loads(open(grade, encoding="utf-8").read())
    for k in STAMP_KEYS:
        doc.pop(k, None)
    pre = tmp_path / "pre-stamp.grade-v5.json"
    pre.write_text(json.dumps(doc, indent=1, sort_keys=True) + "\n",
                   encoding="utf-8")
    r = cli("--rows", rows, "--check", "--grade", str(pre))
    assert r.returncode == 0, r.stdout + r.stderr
    assert "IDENTICAL" in r.stdout
    assert "DIFF " not in r.stdout                     # no field differs
    for k in STAMP_KEYS:
        assert "provenance-only %s=" % k in r.stdout


def test_d_historical_stored_grid_is_checked_field_by_field():
    """A stored grid that predates the stamp: stamps are provenance, and the only
    other difference is `decidable_source`, which predates this unit (GRADE-V5-
    REPAIR) and is reported as the finding rather than hidden."""
    assert os.path.isfile(HISTORICAL) and os.path.isfile(HISTORICAL_ROWS)
    r = cli("--rows", HISTORICAL_ROWS, "--check", "--grade", HISTORICAL)
    assert r.returncode == 1, r.stdout + r.stderr      # era drift IS reported
    for k in STAMP_KEYS:
        assert "provenance-only %s=" % k in r.stdout
    differing = [ln.split(":")[0].replace("DIFF ", "")
                 for ln in r.stdout.splitlines() if ln.startswith("DIFF ")]
    outside = [p for p in differing
               if not p.endswith(".decidable_source")]
    assert outside == [], "differences outside the known era field: %s" % outside


# ------------------------------------------------------------- red->green / F1
def test_e_red_stale_pin_is_refused_green_resolver_reproduces(rows, tmp_path):
    rr = load_regrade_module(TOOL, "rr_green")
    grade = make_grade(rows, tmp_path / "out")
    good = json.loads(open(grade, encoding="utf-8").read())

    red_src = open(TOOL, encoding="utf-8").read().replace(
        "EXPECTED_GRADER_SHA = (\"056eb605e2baf5c91e0cb32d037cd0528e406e6c8527eec5\"\n"
        "                       \"5a917a52d9f26772\")",
        "EXPECTED_GRADER_SHA = (\"6893d559518168e3ba4fc4a9f5d7642d213d61e2e3c3d0b0a8\"\n"
        "                      \"f01e3379af3077\")")
    assert "6893d559" in red_src
    red_dir = tmp_path / "red"
    red_dir.mkdir()
    red_tool = red_dir / "regrade.py"
    red_tool.write_text(red_src, encoding="utf-8")
    # strict mode stands in for the old unconditional pin: the stale digest refuses
    r_red = run(str(red_tool), "--rows", rows, "--grader", GRADER, "--check",
                "--grade", grade, "--sha256", OLD_PIN,
                env={"PYTHONPATH": TOOLS})
    assert r_red.returncode == 3, r_red.stdout + r_red.stderr
    assert "sha256 mismatch" in r_red.stdout
    assert OLD_PIN in r_red.stdout and sha256(GRADER) in r_red.stdout

    # GREEN: the resolver version reproduces the same document with no flags
    r_green = cli("--rows", rows, "--check", "--grade", grade)
    assert r_green.returncode == 0, r_green.stdout + r_green.stderr
    assert "IDENTICAL" in r_green.stdout
    assert rr.resolve_grader_identity(GRADER)["sha256"] in r_green.stdout
    assert good["grader_sha256"] == sha256(GRADER)


def test_f_edited_grader_copy_is_caught(rows, tmp_path):
    """Resolving is not ignoring: an edited grader shows up as drift, in the stamp,
    and (strict) as a refusal."""
    copy_dir = tmp_path / "edited"
    copy_dir.mkdir()
    edited = copy_dir / "grade_v5.py"
    shutil.copyfile(GRADER, str(edited))
    edited.write_text(edited.read_text(encoding="utf-8")
                      + "\n# DELIBERATE EDIT (test fixture): drift must stay detectable\n",
                      encoding="utf-8")
    edited_sha = sha256(str(edited))
    assert edited_sha != sha256(GRADER)
    env = {"PYTHONPATH": LONGRUN}

    strict = cli("--rows", rows, "--grader", str(edited), "--out-dir",
                 str(tmp_path / "s"), "--sha256", sha256(GRADER), env=env)
    assert strict.returncode == 3, strict.stdout + strict.stderr
    assert "sha256 mismatch" in strict.stdout
    assert edited_sha in strict.stdout and sha256(GRADER) in strict.stdout

    loose = cli("--rows", rows, "--grader", str(edited), "--out-dir",
                str(tmp_path / "l"), "--as-of", AS_OF, env=env)
    assert loose.returncode == 0, loose.stdout + loose.stderr
    assert "drift" in loose.stdout and edited_sha in loose.stdout
    out = tmp_path / "l" / "rows-stamp.grade-v5.json"
    stamp = json.loads(out.read_text(encoding="utf-8"))
    assert stamp["grader_sha256"] == edited_sha
    assert stamp["grader_version"] == load_grader_module().GRADER_VERSION

    # and a check against the unedited grader's document names the stamp as the diff
    good_dir = tmp_path / "good"
    good = make_grade(rows, good_dir)
    chk = cli("--rows", rows, "--check", "--grade", good)
    assert chk.returncode == 0, chk.stdout + chk.stderr

#!/usr/bin/env python3
"""Guard tests for TVS-ROWS-IDENTITY: every tokens_to_verified figure must name its bytes.

Red/green is in one file:
  * GREEN -- the three known figures (48,347 / 50,847 / 111,994 at cp.0.t12 turn 12)
    reproduce, and each record carries rows_file/rows_sha256/rows_size/computed_at/
    grader_sha256 with the sha of the bytes actually read.
  * RED   -- a tampered copy, a deleted rows file and a non-utf8 rows file each make
    the tool exit 2 with a named reason and emit NO number.

Offline. No network. Uses only the real files already in measure/ (read-only) and
temp copies.
"""
import hashlib
import json
import os
import shutil
import subprocess
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PTR = os.path.join(ROOT, "experiments", "ptr-engine")
MEASURE = os.path.join(PTR, "measure")
TOOL = os.path.join(PTR, "tools", "tokens_to_verified.py")

# The three figures of record, with the grade document that certified each.
CASES = [
    ("rows-longrun-v4-2026-10-26.jsonl",
     "cell-longrun-v4-20261026T1556Z.grade-v5.json", 48347, "pointer-stable"),
    ("rows-longrun-v4-tools-2026-10-26.jsonl",
     "cell-longrun-v4-tools-20261026T1556Z.grade-v5.json", 50847, "pointer-stable"),
    ("rows-longrun-v6-tools.jsonl",
     "cell-pointer-stable-20261026T145722Z.grade-v5.json", 111994, "pointer-stable"),
]

STAMP_FIELDS = ("rows_file", "rows_sha256", "rows_size", "computed_at", "grader_sha256")


def run(*args, env=None):
    e = dict(os.environ)
    e.update(env or {})
    p = subprocess.run([sys.executable, TOOL] + list(args), cwd=ROOT,
                       capture_output=True, text=True, env=e)
    return p


def sha256(path):
    with open(path, "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()


def numbers_in(text):
    """Every integer >= 1000 appearing in a document -- a token figure would be one."""
    found = []

    def walk(node):
        if isinstance(node, dict):
            for v in node.values():
                walk(v)
        elif isinstance(node, list):
            for v in node:
                walk(v)
        elif isinstance(node, int) and not isinstance(node, bool) and node >= 1000:
            found.append(node)

    walk(json.loads(text))
    return found


# ---------------------------------------------------------------- green

@pytest.mark.parametrize("rows_name,grade_name,expected,arm", CASES)
def test_figure_reproduces_and_carries_its_bytes(rows_name, grade_name, expected, arm):
    rows = os.path.join(MEASURE, rows_name)
    grade = os.path.join(MEASURE, grade_name)
    p = run("--rows", rows, "--grade", grade, "--arm", arm)
    assert p.returncode == 0, p.stderr
    doc = json.loads(p.stdout)

    # the number reproduces exactly -- nothing rewritten
    assert doc["tvs"]["tokens"] == expected
    assert doc["tvs"]["turn"] == 12 and doc["arm"] == arm

    # the identity is on the record AND inside the tvs block
    for holder in (doc, doc["tvs"]):
        for field in STAMP_FIELDS:
            assert field in holder, (field, rows_name)
    assert doc["rows_sha256"] == sha256(rows)
    assert doc["rows_size"] == os.path.getsize(rows)
    assert doc["tvs"]["rows_sha256"] == doc["rows_sha256"]
    assert doc["rows_file"] == rows

    # grader identity is the document's own stamp or an explicit null -- never a pin
    assert doc["grader_sha256"] is None or doc["grader_sha256"] == doc["grader_identity"]["sha256"]
    assert doc["grader_sha_source"] in ("stamp", "unstamped_grade_document")
    if doc["grader_sha256"] is None:
        assert doc["grader_sha_source"] == "unstamped_grade_document"
        assert doc["grader_identity"]["stamped"] is False


def test_supplied_matching_sha_is_accepted():
    rows = os.path.join(MEASURE, CASES[0][0])
    p = run("--rows", rows, "--grade", os.path.join(MEASURE, CASES[0][1]),
            "--expect-rows-sha256", sha256(rows), "--arm", "pointer-stable")
    assert p.returncode == 0, p.stderr
    assert json.loads(p.stdout)["tvs"]["tokens"] == CASES[0][2]


def test_stamped_grade_document_binds_its_own_grader_sha(tmp_path):
    """A stamped document supplies grader_sha256 itself; the tool reads it, not a pin."""
    rows = os.path.join(MEASURE, "rows-longrun-v4-2026-10-26.jsonl")
    grade_src = os.path.join(MEASURE, "cell-longrun-v4-20261026T1556Z.grade-v5.json")
    with open(grade_src, encoding="utf-8") as fh:
        grade = json.load(fh)
    grade["grader_sha256"] = "a" * 64
    grade["grader_version"] = "grade_v5+synthetic"
    grade["rows_sha256"] = sha256(rows)
    stamped = tmp_path / "synthetic-stamped.grade-v5.json"
    stamped.write_text(json.dumps(grade), encoding="utf-8")

    p = run("--rows", rows, "--grade", str(stamped), "--arm", "pointer-stable")
    assert p.returncode == 0, p.stderr
    doc = json.loads(p.stdout)
    assert doc["grader_sha256"] == "a" * 64
    assert doc["grader_sha_source"] == "stamp"
    assert doc["tvs"]["grader_sha256"] == "a" * 64


# ---------------------------------------------------------------- red

def test_tampered_copy_is_refused_with_both_shas(tmp_path):
    rows = os.path.join(MEASURE, "rows-longrun-v6-tools.jsonl")
    good = sha256(rows)
    bad_copy = tmp_path / "rows-tampered.jsonl"
    shutil.copyfile(rows, bad_copy)
    blob = bytearray(bad_copy.read_bytes())
    blob[len(blob) // 2] ^= 0x01          # flip one bit of one byte
    bad_copy.write_bytes(bytes(blob))
    tampered = hashlib.sha256(bytes(blob)).hexdigest()
    assert tampered != good

    p = run("--rows", str(bad_copy), "--grade", os.path.join(MEASURE, CASES[2][1]),
            "--expect-rows-sha256", good)
    assert p.returncode == 2, p.stdout
    assert "rows_sha_mismatch" in p.stderr
    assert good in p.stderr and tampered in p.stderr      # both values named

    doc = json.loads(p.stdout)
    assert doc["refused"] is True
    assert doc["reason"] == "rows_sha_mismatch"
    assert doc["refusal"]["expected_sha256"] == good
    assert doc["refusal"]["actual_sha256"] == tampered
    assert doc["tvs"] is None
    assert doc["refusal"]["number_emitted"] is False
    assert numbers_in(p.stdout) == []                     # no figure printed at all


def test_deleted_rows_file_is_refused_as_rows_missing(tmp_path):
    rows = tmp_path / "rows-gone.jsonl"
    p = run("--rows", str(rows), "--grade", os.path.join(MEASURE, CASES[2][1]))
    assert p.returncode == 2
    assert "rows_missing" in p.stderr
    doc = json.loads(p.stdout)
    assert doc["reason"] == "rows_missing"
    assert doc["tvs"] is None
    assert numbers_in(p.stdout) == []


def test_unreadable_rows_file_is_refused_as_rows_unreadable(tmp_path):
    rows = tmp_path / "rows-not-utf8.jsonl"
    rows.write_bytes(b'{"arm":"x","turn":1}\xff\xfe\x00binary')
    p = run("--rows", str(rows), "--grade", os.path.join(MEASURE, CASES[2][1]))
    assert p.returncode == 2
    assert "rows_unreadable" in p.stderr
    doc = json.loads(p.stdout)
    assert doc["reason"] == "rows_unreadable"
    assert doc["tvs"] is None
    assert numbers_in(p.stdout) == []


def test_full_scan_carries_a_stamp_on_every_number():
    """--all: every record with a tvs number names a rows file whose sha256 it carries."""
    p = run("--all")
    assert p.returncode in (0, 2), p.stderr
    doc = json.loads(p.stdout)
    numbered = [c for c in doc["cells"] if c.get("tvs")]
    assert numbered, "no numbered cells -- the guard would be vacuous"
    for c in numbered:
        assert c["rows_sha256"] == sha256(c["rows_file"])
        assert c["rows_size"] == os.path.getsize(c["rows_file"])
        for field in STAMP_FIELDS:
            assert field in c["tvs"]
    assert doc["identity"]["fields"] == list(STAMP_FIELDS)

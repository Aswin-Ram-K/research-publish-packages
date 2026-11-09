#!/usr/bin/env python3
"""Unit GRADER-STAMP - every grade_v5 document says WHICH GRADER wrote it.

THE DEFECT (orchestration/handoffs/QUALITY-ERA-TABLE.json, .evidence.real_output.census):
of 20 grade_v5 documents, 9 record a grader sha -- all nine are regrade outputs --
and the 11 genuinely stored grade files record NONE. Every historical accuracy
figure was therefore datable only by re-running the grader against the rows, which
is why REGRADE-ONE-COMMAND had to exist before any grid could be trusted.

WHAT THIS FILE PINS
  (a) a freshly graded fixture document carries grader_sha256, grader_version and
      rows_sha256, and grader_sha256 equals `sha256sum grade_v5.py` (executed, not
      assumed) while rows_sha256 equals `sha256sum` of the rows file it graded;
  (b) the writer REFUSES to write (exit 3, no file created) when any of the three
      cannot be computed -- an unstamped grade file is the defect, never a fallback;
  (c) tools/grader_identity.py resolves a stamped document to source="stamp" and a
      historical document (stamp removed) to source="derived"/stamped=False, and
      never silently accepts one: `requires` names the regrade result it needs;
  (d) RED->GREEN: the same assertions are run against an /tmp copy of the writer
      with the stamp call deleted -- the copy writes an UNSTAMPED document and the
      green assertion fails on it. No stored grade file is touched (forward-only).

    GREEN: python3 -m pytest experiments/ptr-engine/longrun/tests/test_grader_stamp.py -q
    RED:   GRADE_V5_MODULE=/tmp/grader-stamp/grade_v5_nostamp.py \\
             python3 -m pytest experiments/ptr-engine/longrun/tests/test_grader_stamp.py -q
"""
import importlib.util
import json
import os
import subprocess
import sys

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
LONGRUN = os.path.dirname(HERE)
TOOLS = os.path.join(os.path.dirname(LONGRUN), "tools")
REPO = os.path.dirname(os.path.dirname(os.path.dirname(LONGRUN)))
GRADER = os.path.join(LONGRUN, "grade_v5.py")
FIXTURE = os.path.join(LONGRUN, "tasks-v5/runtime-v5/LR-01.v5.json")

for _p in (LONGRUN, TOOLS):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import grader_identity as gi     # noqa: E402


def _load():
    """The writer under test; GRADE_V5_MODULE points it at a /tmp copy for RED."""
    src = os.environ.get("GRADE_V5_MODULE")
    if src:
        spec = importlib.util.spec_from_file_location("grade_v5_under_test", src)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod
    import grade_v5 as mod
    return mod


g5 = _load()

# The answers test_grade_v5.py already grades against this fixture; the values may
# move with the pinned source but the DOCUMENT is what this card measures.
ANSWERS = {12: "ANSWER: NUM 64",
           24: "ANSWER: NUM 31",
           46: ("ANSWER: CALL ledger.record_refusal(scope=..., "
                "serialized_ref=text, code=error.code)")}


def sha256sum(path):
    """`sha256sum <path>` -- the external reference this test compares against."""
    out = subprocess.check_output(["sha256sum", os.path.abspath(path)], text=True)
    return out.split()[0]


def write_rows(tmp_path, name="rows.jsonl"):
    path = tmp_path / name
    with open(path, "w", encoding="utf-8") as fh:
        for turn, content in sorted(ANSWERS.items()):
            fh.write(json.dumps({"arm": "stamp", "task_id": "LR-01",
                                 "turn": turn, "content": content}) + "\n")
    return str(path)


def run_writer(grader, rows_path, out_path):
    # A /tmp copy of the writer computes its own HERE, so give the imports it needs.
    env = dict(os.environ, PYTHONPATH=os.pathsep.join(
        [TOOLS, LONGRUN, os.environ.get("PYTHONPATH", "")]).rstrip(os.pathsep),
        PYTHONDONTWRITEBYTECODE="1")
    return subprocess.run([sys.executable, grader, "--rows", rows_path,
                           "--fixture", FIXTURE, "--out", str(out_path)],
                          capture_output=True, text=True, env=env)


def load(path):
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


# ------------------------------------------------------------------ (a) the stamp
def test_fresh_document_carries_all_three_stamp_fields(tmp_path):
    rows_path = write_rows(tmp_path)
    out = tmp_path / "stamp.grade-v5.json"
    rc = g5.main(["--rows", rows_path, "--fixture", FIXTURE, "--out", str(out)])
    assert rc == 0, "writer exited %r" % (rc,)

    doc = load(out)
    for key in ("grader_sha256", "grader_version", "rows_sha256"):
        assert doc.get(key), "missing stamp field %r -- an unstamped grade file" % key
    assert doc["grader_version"] == g5.GRADER_VERSION == "5.1"
    assert doc["grader_sha256"] == sha256sum(getattr(g5, "__file__"))
    assert doc["rows_sha256"] == sha256sum(rows_path)
    assert len(doc["grader_sha256"]) == 64 and len(doc["rows_sha256"]) == 64

    ident = gi.grader_identity(doc)
    assert ident["source"] == "stamp" and ident["stamped"] is True
    assert ident["sha256"] == doc["grader_sha256"]
    assert ident["rows_sha256"] == doc["rows_sha256"]
    assert ident["missing"] == []


def test_stamp_changes_with_the_rows_not_with_the_rule(tmp_path):
    """Stamping records identity; it never moves a verdict."""
    a = tmp_path / "a.jsonl"
    b = tmp_path / "b.jsonl"
    a.write_text(json.dumps({"arm": "stamp", "task_id": "LR-01", "turn": 12,
                             "content": "ANSWER: NUM 64"}) + "\n", encoding="utf-8")
    b.write_text("\n".join(json.dumps({"arm": "stamp", "task_id": "LR-01", "turn": 12,
                                       "content": "ANSWER: NUM 64"})
                           for _ in range(2)) + "\n", encoding="utf-8")
    d_a, d_b = g5.grade_rows(load(FIXTURE), [load_line(a)]), g5.grade_rows(load(FIXTURE), [load_line(b)])
    g5.stamp_document(d_a, str(a))
    g5.stamp_document(d_b, str(b))
    assert d_a["arms"]["stamp"]["checkpoint_accuracy"] == d_b["arms"]["stamp"]["checkpoint_accuracy"]
    assert d_a["rows_sha256"] != d_b["rows_sha256"]
    assert d_a["grader_sha256"] == d_b["grader_sha256"]      # one current grader


def load_line(path):
    with open(path, encoding="utf-8") as fh:
        return json.loads(fh.readline())


# ------------------------------------------------------------- (b) the refusal
def test_writer_refuses_when_stamp_uncomputable(tmp_path, monkeypatch):
    rows_path = write_rows(tmp_path)
    out = tmp_path / "refused.grade-v5.json"

    def boom(*_a, **_k):
        raise g5.StampError("stamp_uncomputable: simulated for this test")

    monkeypatch.setattr(g5, "stamp_document", boom)
    rc = g5.main(["--rows", rows_path, "--fixture", FIXTURE, "--out", str(out)])
    assert rc == 3, "writer must refuse an unstamped document, exited %r" % (rc,)
    assert not out.exists(), "refusal wrote a file anyway"


def test_stamp_document_raises_on_missing_rows_file(tmp_path):
    doc = {"grader": "grade_v5"}
    with pytest.raises(g5.StampError):
        g5.stamp_document(doc, str(tmp_path / "does-not-exist.jsonl"))
    assert "grader_sha256" not in doc and "rows_sha256" not in doc


# ---------------------------------------------------- (c) the one resolver, no table
def test_removed_stamp_is_derived_and_never_silently_accepted(tmp_path):
    rows_path = write_rows(tmp_path)
    out = tmp_path / "stamp.grade-v5.json"
    assert run_writer(GRADER, rows_path, out).returncode == 0
    stored = load(out)

    historical = {k: v for k, v in stored.items()
                  if k not in ("grader_sha256", "grader_version", "rows_sha256")}
    ident = gi.grader_identity(historical)
    assert ident["source"] == "derived"
    assert ident["stamped"] is False
    assert ident["sha256"] is None
    assert ident["requires"] == "regrade_result"
    assert ident["missing"] == ["grader_sha256", "grader_version", "rows_sha256"]
    assert "UNKNOWN" in gi.describe(ident)

    # the caller must SUPPLY the re-derived identity; it is never guessed
    derived = gi.grader_identity(historical, {"grader_sha256": stored["grader_sha256"]})
    assert derived["source"] == "derived" and derived["stamped"] is False
    assert derived["sha256"] == stored["grader_sha256"]
    assert "DERIVED" in gi.describe(derived)

    # two of three fields is not a stamp
    partial = dict(stored)
    partial.pop("rows_sha256")
    assert gi.grader_identity(partial)["stamped"] is False
    assert gi.grader_identity(partial)["missing"] == ["rows_sha256"]

    with pytest.raises((TypeError, ValueError)):
        gi.grader_identity(historical, 12345)


# --------------------------------------------------------- (d) red -> green, in memory
def _strip_stamp_copy(tmp_path):
    """A /tmp copy of the writer with the stamp call deleted -- the pre-fix writer.

    Never edits a stored file: the copy is scratch, the stored writer is read-only here.
    """
    with open(GRADER, encoding="utf-8") as fh:
        src = fh.read()
    needle = "        stamp_document(doc, args.rows)\n"
    assert needle in src, "writer no longer calls stamp_document -- update this test"
    red = tmp_path / "grade_v5_nostamp.py"
    red.write_text(src.replace(needle, "        pass  # RED: stamping removed\n"),
                   encoding="utf-8")
    return str(red)


def test_red_green_writer_without_stamp_emits_an_undated_document(tmp_path):
    rows_path = write_rows(tmp_path)
    green_out = tmp_path / "green.grade-v5.json"
    red_out = tmp_path / "red.grade-v5.json"

    green = run_writer(GRADER, rows_path, green_out)
    assert green.returncode == 0, green.stderr
    green_doc = load(green_out)
    assert gi.grader_identity(green_doc)["stamped"] is True

    red = run_writer(_strip_stamp_copy(tmp_path), rows_path, red_out)
    assert red.returncode == 0, red.stderr
    red_doc = load(red_out)
    # the green assertion, run against the red copy -> it must fail there
    assert gi.grader_identity(red_doc)["stamped"] is False
    assert "grader_sha256" not in red_doc
    with pytest.raises(AssertionError):
        assert red_doc.get("grader_sha256") == sha256sum(GRADER)   # the defect, measured

    # and the two documents grade identically: this card changed RECORDING only
    assert (red_doc["arms"]["stamp"]["checkpoint_accuracy"]
            == green_doc["arms"]["stamp"]["checkpoint_accuracy"])


if __name__ == "__main__":                                  # ad-hoc, no pytest needed
    sys.exit(pytest.main([os.path.abspath(__file__), "-q"]))

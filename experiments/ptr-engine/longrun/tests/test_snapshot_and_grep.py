"""GUARD — the frozen root and the bounded `grep` tool (STAGE-2 of the compaction A/B).

WHY THIS TEST EXISTS.  `docs/AGENTIC-COMPACTION-AB.md` §3.2 replaces the scripted replay
with an episode in which the MODEL chooses what to read.  Two things then stop being
implementation details and become part of the measurement:

  1. THE ROOT.  A model-chosen read of the live tree is a read of a repository that moves
     between runs, so two arms of one episode would answer about different bytes and the
     cost difference between them would be unattributable.  `build_snapshot.py` freezes
     the trees, `--root` points every tool call at the freeze, and `--snapshot-manifest`
     re-hashes every entry BEFORE the first request.
  2. THE TOOL SURFACE.  `read_file` alone makes a lost journal repairable only by
     re-reading, which inflates the re-fetch rate the design measures.  `grep` is the
     second tool, and it is bounded on every axis that could make it a second read
     channel: hit count, line length, pattern length, glob, and the same path rules
     `read_file` obeys.

RED-BEFORE-GREEN (house style: the reverted run is recorded, not asserted).

  RED 1 — the grep dispatch removed.  With
  ``if call.get("tool", client.READ_FILE_TOOL_NAME) == GREP_TOOL_NAME:`` deleted from
  ``execute_tool_call``, a grep call falls through to the read_file branch and raises
  ``KeyError: 'path'``:

      $ .venv/bin/python -m pytest experiments/ptr-engine/longrun/tests/test_snapshot_and_grep.py -q
      E       KeyError: 'path'
      experiments/ptr-engine/longrun/run_longrun.py:1356: KeyError
      FAILED ...::test_grep_returns_bounded_path_line_text - KeyError: 'path'
      FAILED ...::test_grep_truncated_is_false_when_the_cap_is_not_reached - KeyError: 'path'
      FAILED ...::test_grep_refusals_are_named - KeyError: 'path'
      FAILED ...::test_grep_never_returns_a_secret_shaped_file - KeyError: 'path'
      FAILED ...::test_grep_skips_artefact_and_vcs_directories - KeyError: 'path'
      FAILED ...::test_grep_max_hits_is_clamped - KeyError: 'path'
      6 failed, 11 passed in 0.27s

  RED 2 — the manifest re-hash removed.  With ``return root_sha, None`` inserted before
  the per-entry loop in ``verify_snapshot_manifest``, an edited snapshot is accepted:

      $ .venv/bin/python -m pytest experiments/ptr-engine/longrun/tests/test_snapshot_and_grep.py -q
      >       assert root_sha is None
      E       AssertionError: assert 'c0b77c3d842129640b042e585709641fdff81307207aeb6d90f9c81f64b9584e' is None
      FAILED ...::test_manifest_mismatch_names_the_moved_file - AssertionError: assert 'c0b77c3d...' is None
      1 failed, 16 passed in 0.07s

  GREEN — both restored:

      $ .venv/bin/python -m pytest experiments/ptr-engine/longrun/tests/test_snapshot_and_grep.py -q
      17 passed in 0.05s

  RED 3 — the `path` scope removed.  With ``if raw_path:`` in ``_execute_grep`` changed to
  ``if False and raw_path:``, a `path` argument is silently ignored and the walk covers the
  whole root, so a grep asked about one directory answers from everywhere and a grep asked
  about `.env` searches anyway:

      $ .venv/bin/python -m pytest experiments/ptr-engine/longrun/tests/test_snapshot_and_grep.py -q
      E       KeyError: 'path'
      FAILED ...::test_grep_path_scopes_the_walk - KeyError: 'path'
      E       KeyError: 'error'
      FAILED ...::test_grep_path_obeys_the_read_channels_rules - KeyError: 'error'
      2 failed, 17 passed in 0.07s

  GREEN — restored:

      $ .venv/bin/python -m pytest experiments/ptr-engine/longrun/tests/test_snapshot_and_grep.py -q
      19 passed in 0.07s

Zero requests, no network: every case reads a temporary tree or the repository's own
files, and nothing here constructs a socket.
"""
from __future__ import annotations

import json
import os
import sys

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
LONGRUN = os.path.dirname(HERE)
WORKSPACE = os.path.dirname(os.path.dirname(os.path.dirname(LONGRUN)))
sys.path.insert(0, LONGRUN)
sys.path.insert(0, os.path.join(LONGRUN, "tools"))

import run_longrun as R  # noqa: E402
import build_snapshot as B  # noqa: E402


# --------------------------------------------------------------------- fixtures
def _make_tree(root: str) -> None:
    """A minimal root carrying all four snapshot trees plus the traps grep must skip."""
    files = {
        "experiments/ptr-engine/ptr_engine/alpha.py": "ALPHA = 1\nNEEDLE = 'a'\n",
        "experiments/ptr-engine/longrun/beta.py": "BETA = 2\nNEEDLE = 'b'\n",
        "experiments/ptr-engine/tools/gamma.py": "GAMMA = 3\n",
        "src/resextract/delta.py": "DELTA = 4\nNEEDLE = 'd'\n",
        # traps: none of these may ever appear in a hit list
        "experiments/ptr-engine/longrun/state/rows.jsonl": '{"NEEDLE": "state"}\n',
        "experiments/ptr-engine/longrun/manifests/old.py": "NEEDLE = 'manifest'\n",
        "experiments/ptr-engine/longrun/__pycache__/beta.cpython-311.pyc": "NEEDLE\n",
        "experiments/ptr-engine/longrun/.git/config": "NEEDLE\n",
        "experiments/ptr-engine/longrun/secrets/creds.py": "NEEDLE = 'secret'\n",
        "experiments/ptr-engine/longrun/.env": "NEEDLE=secret\n",
        "experiments/ptr-engine/longrun/id_rsa": "NEEDLE\n",
    }
    for rel, body in files.items():
        full = os.path.join(root, rel)
        os.makedirs(os.path.dirname(full), exist_ok=True)
        with open(full, "w", encoding="utf-8") as fh:
            fh.write(body)


@pytest.fixture()
def tree(tmp_path):
    root = str(tmp_path / "repo")
    _make_tree(root)
    return root


# ------------------------------------------------------- 1. the snapshot builder
def test_build_prints_a_root_sha256_and_is_idempotent(tree, tmp_path):
    """A second run on an unchanged tree is a NO-OP: same dir, same manifest bytes."""
    dest = str(tmp_path / "snapshots")
    first = B.build(tree, dest)
    assert len(first["root_sha256"]) == 64
    assert first["state"] == "created"
    assert first["dir"] == os.path.join(dest, first["root_sha256"])

    manifest = os.path.join(first["dir"], B.MANIFEST_NAME)
    before = open(manifest, "rb").read()
    before_mtime = os.stat(manifest).st_mtime_ns

    second = B.build(tree, dest)
    assert second["root_sha256"] == first["root_sha256"]
    assert second["state"] == "unchanged"
    assert open(manifest, "rb").read() == before
    assert os.stat(manifest).st_mtime_ns == before_mtime, "the manifest was rewritten"

    doc = json.loads(before)
    assert doc["root_sha256"] == first["root_sha256"]
    assert doc["files"], "the manifest carries no per-file shas"
    assert all(len(v) == 64 for v in doc["files"].values())


def test_build_refuses_a_directory_whose_root_sha256_differs(tree, tmp_path):
    """A snapshot that silently becomes a different snapshot is worse than none."""
    dest = str(tmp_path / "snapshots")
    first = B.build(tree, dest)
    manifest = os.path.join(first["dir"], B.MANIFEST_NAME)
    doc = json.loads(open(manifest, "rb").read())
    doc["root_sha256"] = "0" * 64
    with open(manifest, "w", encoding="utf-8") as fh:
        json.dump(doc, fh)

    with pytest.raises(SystemExit) as exc:
        B.build(tree, dest)
    assert "refusing to overwrite" in str(exc.value)
    assert "0" * 64 in str(exc.value)


def test_build_skips_artefacts_and_derived_bytes(tree, tmp_path):
    """`state/`, `manifests/`, `__pycache__` and `*.pyc` are not source."""
    result = B.build(tree, str(tmp_path / "snapshots"))
    doc = json.loads(open(os.path.join(result["dir"], B.MANIFEST_NAME), "rb").read())
    rels = set(doc["files"])
    assert "experiments/ptr-engine/longrun/beta.py" in rels
    assert "src/resextract/delta.py" in rels
    for banned in ("state/", "manifests/", "__pycache__", ".pyc"):
        assert not any(banned in rel for rel in rels), banned


# ------------------------------------------------- 2. the manifest re-hash gate
def test_manifest_mismatch_names_the_moved_file(tree, tmp_path):
    """An edited snapshot is refused, and the abort names the file that moved."""
    result = B.build(tree, str(tmp_path / "snapshots"))
    manifest = os.path.join(result["dir"], B.MANIFEST_NAME)

    root_sha, refusal = R.verify_snapshot_manifest(manifest)
    assert refusal is None
    assert root_sha == result["root_sha256"]

    moved = "experiments/ptr-engine/longrun/beta.py"
    with open(os.path.join(result["dir"], moved), "a", encoding="utf-8") as fh:
        fh.write("# edited after the freeze\n")

    root_sha, refusal = R.verify_snapshot_manifest(manifest)
    assert root_sha is None
    assert refusal == "snapshot_manifest_mismatch: " + moved, refusal


def test_manifest_unreadable_is_named(tmp_path):
    root_sha, refusal = R.verify_snapshot_manifest(str(tmp_path / "absent.json"))
    assert root_sha is None
    assert refusal == "snapshot_manifest_unreadable"


# ------------------------------------------------------------- 3. the grep tool
def test_grep_returns_bounded_path_line_text(tree):
    """At most `max_hits` hits, each `path:line: text`, and `truncated` is exact."""
    res = R.execute_tool_call({"tool": "grep", "pattern": "NEEDLE", "glob": "*.py",
                               "max_hits": 2}, tree)
    rec = res["record"]
    assert rec["tool"] == "grep"
    assert rec["executed"] is True
    assert rec["hits"] == 2
    assert rec["truncated"] is True, "3 matches exist, 2 were asked for"
    lines = res["text"].splitlines()
    assert len(lines) == 2
    for line in lines:
        path, lineno, text = line.split(":", 2)
        assert path.endswith(".py")
        assert lineno.isdigit()
        assert "NEEDLE" in text
    assert 'for="grep"' in res["block"]


def test_grep_truncated_is_false_when_the_cap_is_not_reached(tree):
    res = R.execute_tool_call({"tool": "grep", "pattern": "GAMMA", "glob": "*.py"}, tree)
    assert res["record"]["hits"] == 1
    assert res["record"]["truncated"] is False


def test_grep_refusals_are_named(tree):
    """The three refusals the analyzer counts, each with the same record shape."""
    cases = {
        "missing_pattern": {"tool": "grep", "pattern": ""},
        "pattern_too_long": {"tool": "grep", "pattern": "a" * (R.GREP_MAX_PATTERN_CHARS + 1)},
        "bad_pattern": {"tool": "grep", "pattern": "("},
    }
    for reason, call in cases.items():
        res = R.execute_tool_call(call, tree)
        rec = res["record"]
        assert rec["error"] == reason, (reason, rec)
        assert rec["executed"] is False
        assert rec["hits"] == 0
        assert res["block"] == '<tool_result error="%s"/>' % reason
        assert res["text"] == ""


def test_grep_never_returns_a_secret_shaped_file(tree):
    """A grep that returned `.env` content would be a leak by a second route."""
    res = R.execute_tool_call({"tool": "grep", "pattern": "NEEDLE", "glob": "*",
                               "max_hits": 20}, tree)
    text = res["text"]
    assert ".env" not in text
    assert "id_rsa" not in text
    assert "secrets/" not in text
    assert "secret" not in text


def test_grep_skips_artefact_and_vcs_directories(tree):
    """`state/`, `__pycache__` and `.git` are pruned; `manifests/` is NOT a grep concern
    (it is the snapshot builder that drops it), so it is deliberately absent here."""
    res = R.execute_tool_call({"tool": "grep", "pattern": "NEEDLE", "glob": "*",
                               "max_hits": 20}, tree)
    text = res["text"]
    for banned in ("state/", "__pycache__", ".git/"):
        assert banned not in text, banned


def test_grep_max_hits_is_clamped(tree):
    """`max_hits` above the constant is clamped, never honoured."""
    res = R.execute_tool_call({"tool": "grep", "pattern": "NEEDLE", "glob": "*.py",
                               "max_hits": 10_000}, tree)
    assert res["record"]["hits"] <= R.GREP_MAX_HITS


def test_grep_path_scopes_the_walk(tree):
    """A `path` argument SCOPES the search; it is never silently ignored.

    A grep that answered from the whole root after being asked about one directory would
    report hits the model did not ask for and could not have predicted, which is exactly
    the kind of unmodelled cost this stage exists to measure.
    """
    res = R.execute_tool_call({"tool": "grep", "pattern": "NEEDLE", "glob": "*.py",
                               "path": "experiments/ptr-engine/ptr_engine"}, tree)
    rec = res["record"]
    assert rec["executed"] is True
    assert rec["path"] == "experiments/ptr-engine/ptr_engine"
    assert rec["hits"] == 1, rec
    assert res["text"].splitlines()[0].startswith("experiments/ptr-engine/ptr_engine/alpha.py:")

    one_file = R.execute_tool_call({"tool": "grep", "pattern": "NEEDLE",
                                    "path": "src/resextract/delta.py"}, tree)
    assert one_file["record"]["hits"] == 1
    assert one_file["record"]["files_scanned"] == 1
    assert one_file["text"].startswith("src/resextract/delta.py:")


def test_grep_path_obeys_the_read_channels_rules(tree):
    """`grep`'s `path` is refused by the SAME rules `read_file` uses, and a directory is
    the one thing grep may take that a read may not."""
    for raw in (".env", "~/.ssh/id_rsa", "/etc/passwd", "../../etc/passwd",
                "experiments/ptr-engine/longrun/id_rsa"):
        rec = R.execute_tool_call({"tool": "grep", "pattern": "NEEDLE", "path": raw},
                                  tree)["record"]
        assert rec["error"] == "path_refused", (raw, rec)
        assert rec["executed"] is False
        assert rec["hits"] == 0

    # parity: the read channel still refuses a directory, so `allow_dir` widened grep
    # only -- it did not widen the tool that returns file CONTENT.
    read = R.execute_tool_call({"path": "experiments/ptr-engine/longrun",
                                "start_line": 1, "end_line": 5}, tree)["record"]
    assert read["error"] == "path_not_found"
    assert read["executed"] is False


# ------------------------------------------------- 4. the parser and the wire set
def test_parse_tool_calls_accepts_a_grep_object():
    text = '<tool_call>grep <tool_call>{"pattern": "FOLD_AT_FRACTION", "glob": "*.py", "max_hits": 5}'
    calls = R.parse_tool_calls(text)
    assert calls == [{"tool": "grep", "pattern": "FOLD_AT_FRACTION", "glob": "*.py",
                      "max_hits": 5}]


def test_parse_tool_calls_keeps_an_empty_pattern_for_the_refusal():
    calls = R.parse_tool_calls('<tool_call>grep <tool_call>{"pattern": ""}')
    assert calls == [{"tool": "grep", "pattern": "", "glob": R.GREP_DEFAULT_GLOB,
                      "max_hits": R.GREP_MAX_HITS}]


def test_a_grep_only_turn_cannot_produce_a_read_file_call():
    """The name gate is per tool, so prose JSON still cannot trigger either."""
    text = '<tool_call>grep <tool_call>{"path": "x.py", "start_line": 1, "end_line": 2}'
    assert R.parse_tool_calls(text) == []


def test_call_from_arguments_grep_refusals_match_the_executor():
    for reason, args in (("missing_pattern", {"pattern": ""}),
                         ("pattern_too_long", {"pattern": "a" * 201}),
                         ("bad_pattern", {"pattern": "("})):
        call, refusal = R._call_from_arguments("call_1", "grep", args)
        assert call is None
        assert refusal["reason"] == reason
        assert refusal["executed"] is False
    call, refusal = R._call_from_arguments(
        "call_2", "grep", {"pattern": "x", "glob": "*.py", "max_hits": 3})
    assert refusal is None
    assert call["tool"] == "grep" and call["max_hits"] == 3


def test_grep_is_not_a_fetch_name():
    """A grep call in a fetch arm must stay UNSERVICED, not be served as an empty fetch."""
    class _Cfg:
        tools = "read_file,grep"

    names = R.fetch_call_tool_names(_Cfg())
    assert "grep" not in names
    assert "read_file" in names and "fetch" in names


# ------------------------------------------------------------- 5. the root itself
def test_root_is_honoured(tree, tmp_path):
    """A path that exists only under the snapshot root reads there and nowhere else."""
    result = B.build(tree, str(tmp_path / "snapshots"))
    snap = result["dir"]
    probe = os.path.join(snap, "SNAPSHOT-ONLY-PROBE.txt")
    with open(probe, "w", encoding="utf-8") as fh:
        fh.write("only here\n")

    call = {"path": "SNAPSHOT-ONLY-PROBE.txt", "start_line": 1, "end_line": 1}
    under_snapshot = R.execute_tool_call(call, snap)
    assert under_snapshot["record"]["executed"] is True
    assert under_snapshot["text"] == "only here"

    under_default = R.execute_tool_call(call, tree)
    assert under_default["record"]["executed"] is False
    assert under_default["record"]["error"] == "path_not_found"

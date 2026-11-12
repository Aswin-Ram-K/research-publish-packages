"""REPIN-HARNESS: the record's `files` list must be re-derivable from the digest it publishes.

WHY THIS TEST EXISTS.  `measure/HARNESS-PIN.json` publishes two things that must agree: a
`harness_sha256` over every input `cell.stage_harness` hashes, and a `files` list that lets a
reader re-derive that digest from the tree.  On 2026-11-11T17:35:25Z `repin_harness.py`
published generation 11 with a SEVEN-entry `files` list and `path: "experiments/"` on every
entry, because `_entries()` hardcoded the path and skipped any name it could not find in
`cell.HARNESS_FILES` -- which is every name, since the fixture is not in that list.  The
digest was right and the list that is supposed to explain it was not, so `check()` could
never have caught a moved fixture: it compares digests, and the digest was computed from the
same eight inputs either way.

The three assertions below are the three ways that record lied:
  1. the entry count must equal the number of inputs the recipe hashes (8, not 7);
  2. every `path` must name a file that exists (not a directory, not a literal);
  3. an input with no path must RAISE, naming the member -- silently dropping an input is
     how the digest and the file list came to disagree in the first place.

RED-BEFORE-GREEN (house style: the reverted run is recorded, not asserted).

  RED — `_entries()` restored to the shipped generation-11 body (literal `"experiments/"`
  path, `continue` on a missing path, no fixture):

      $ .venv/bin/python -m pytest experiments/ptr-engine/tests/test_repin_harness.py -q
      E       AssertionError: the record must list every input the digest covers
      E       assert 7 == 8
      FAILED ...::test_entries_cover_every_input_the_digest_hashes - AssertionError: assert 7 == 8
      E       AssertionError: experiments/ is not a file
      FAILED ...::test_every_entry_path_is_a_file_that_exists - AssertionError: experiments/ is not a file
      E       Failed: DID NOT RAISE <class 'SystemExit'>
      FAILED ...::test_an_input_with_no_path_raises_instead_of_being_dropped - Failed: DID NOT RAISE
      3 failed in 0.05s

  GREEN — fixed:

      $ .venv/bin/python -m pytest experiments/ptr-engine/tests/test_repin_harness.py -q
      3 passed in 0.05s

Zero requests, no network: every case reads the repository's own pinned files.
"""
import os
import sys

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
ENGINE = os.path.dirname(HERE)
TOOLS = os.path.join(ENGINE, "tools")
LONGRUN = os.path.join(ENGINE, "longrun")
for _p in (TOOLS, LONGRUN):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import cell  # noqa: E402
import repin_harness as R  # noqa: E402


def test_entries_cover_every_input_the_digest_hashes():
    """`files` must have one entry per input `compute()` hashes: HARNESS_FILES + fixture."""
    live = R.compute()
    entries = R._entries(live["files"])
    assert len(entries) == len(cell.HARNESS_FILES) + 1, (
        "the record must list every input the digest covers")
    assert {e["name"] for e in entries} == set(live["files"])
    assert "fixture" in {e["name"] for e in entries}


def test_every_entry_path_is_a_file_that_exists():
    """A `path` is a repo-relative FILE path, not a directory and not a literal."""
    entries = R._entries(R.compute()["files"])
    for entry in entries:
        assert not os.path.isabs(entry["path"]), entry
        assert not entry["path"].endswith("/"), "%s is not a file" % (entry["path"],)
        full = os.path.join(R.REPO, entry["path"])
        assert os.path.isfile(full), "%s is not a file" % (entry["path"],)
        assert entry["size"] == os.path.getsize(full), entry["name"]


def test_an_input_with_no_path_raises_instead_of_being_dropped(monkeypatch):
    """An input the recipe hashes but cannot locate is a hard error naming the member."""
    monkeypatch.setattr(cell, "HARNESS_FILES",
                        list(cell.HARNESS_FILES) + [(None, "ghost.py")])
    with pytest.raises(SystemExit) as excinfo:
        R._entries({"ghost.py": "0" * 64})
    assert "ghost.py" in str(excinfo.value)

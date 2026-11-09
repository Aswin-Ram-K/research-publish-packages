"""CELL-STAMP-WIRING: what a fresh cell with NO `usable_for` stamp does.

ANALYSIS-CONSUMER-FIX made `usable_for` CONSUMED: a cell stamped `usable_for: []`
is excluded by name and an all-empty grid is refused with `no usable cells`
(exit 1).  It did not settle the OTHER state, which is the state every fresh
era-B cell is in the moment it is written: the manifest carries **no
`usable_for` key at all**.

The consumer's answer (experiments/ptr-engine/longrun/analyze_stats.py):

  * `usable_for_for_path()` (analyze_stats.py:723-733) only matches a document
    whose dict *contains* the key -- `USABLE_FOR_FIELD in man` / `in cell` -- so
    an unstamped manifest falls through to
    `return {"usable_for": None, "reason": "", "source": USABLE_FOR_UNSTAMPED, ...}`
    (analyze_stats.py:733-734).
  * `select_usable_cells()` (analyze_stats.py:749-753) computes
    `excluded = analyses is not None and len(analyses) == 0`; `None` is not
    `[]`, so an unstamped cell is KEPT.
  * the CLI prints `usable_for unstamped ... (included: no usability stamp on
    disk -- not a certification)` (analyze_stats.py:1752-1754) and exits 0.

So: absent == SILENTLY INCLUDED, one stdout line, never certified, never
refused.  These tests pin exactly that, and the last one PROVES the pin bites:
it mutates a copy of the module so the absent-key branch reads "treat absent as
usable", and asserts the invariant goes red.  The branch itself is never
changed.

Runs on a real 48-turn era-B-shaped rows file (measure/rows-longrun-v6-tools.jsonl,
48 turn rows + 24 tool-followup rows) COPIED into tmp_path; nothing is written
under measure/ or longrun/manifests/.
"""
import importlib.util
import json
import os
import shutil
import sys

import pytest

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LONGRUN = os.path.join(REPO, "experiments/ptr-engine/longrun")
ANALYZE = os.path.join(LONGRUN, "analyze_stats.py")
REAL_48 = os.path.join(REPO, "experiments/ptr-engine/measure/rows-longrun-v6-tools.jsonl")

for p in (LONGRUN, os.path.dirname(LONGRUN), REPO):
    if p not in sys.path:
        sys.path.insert(0, p)

import analyze_stats as A  # noqa: E402


def _load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture(scope="module")
def rows48(tmp_path_factory):
    """A real 48-turn era-B-shaped rows file, copied out of measure/."""
    assert os.path.exists(REAL_48), "real 48-turn corpus missing: %s" % REAL_48
    d = tmp_path_factory.mktemp("stampwiring")
    dst = d / "rows.jsonl"
    shutil.copyfile(REAL_48, str(dst))
    with open(str(dst), encoding="utf-8") as fh:
        rows = [json.loads(l) for l in fh if l.strip()]
    turns = {r.get("turn") for r in rows if r.get("kind") == "turn"}
    assert len(turns) == 48, "expected 48 turns, got %d" % len(turns)
    return str(dst), rows


def _manifest(rows_path, stamp="absent", name="offline"):
    man = {"schema": "consonance.longrun-manifest/1", "run_id": name, "N": 48,
           "rep": 1, "dry_run": False, "arm": "pointer-stable",
           "rows_path": rows_path}
    if stamp != "absent":
        man["usable_for"] = stamp
        man["usable_for_reason"] = "offline fixture"
    return man


# ---------------------------------------------------------------------------
# 1. The absent-key branch: None, source "unstamped", NOT a permission
# ---------------------------------------------------------------------------
def test_absent_key_resolves_to_none_and_unstamped(rows48):
    path, _ = rows48
    rec = A.usable_for_for_path(path, manifests=[_manifest(path)], sanity=False)
    assert rec["usable_for"] is None, (
        "an absent `usable_for` key must resolve to None (unknown), not to a "
        "permission: %r" % (rec["usable_for"],))
    assert rec["usable_for"] != [], "absent must not be read as `usable_for: []`"
    assert rec["source"] == A.USABLE_FOR_UNSTAMPED == "unstamped"
    # `None` is the whole point: it is not a list of analyses.
    assert A._usable_list(rec["usable_for"]) is None


def test_absent_key_cell_is_included_not_excluded(rows48):
    path, rows = rows48
    kept, records = A.select_usable_cells(
        [(path, len(rows), rows)], manifests=[_manifest(path)], sanity=False)
    assert [k[0] for k in kept] == [path], "an unstamped cell must be kept"
    (rec,) = records
    assert rec["excluded"] is False
    assert rec["analyses"] is None
    assert rec["usable_for"] is None
    assert rec["source"] == "unstamped"


def test_empty_stamp_is_the_only_refusal_state(rows48):
    """`[]` excludes; absent includes; both are distinguishable records."""
    path, rows = rows48
    kept_empty, rec_empty = A.select_usable_cells(
        [(path, len(rows), rows)],
        manifests=[_manifest(path, [])], sanity=False)
    assert kept_empty == []
    assert rec_empty[0]["excluded"] is True
    assert rec_empty[0]["analyses"] == []
    kept_abs, rec_abs = A.select_usable_cells(
        [(path, len(rows), rows)], manifests=[_manifest(path)], sanity=False)
    assert len(kept_abs) == 1 and rec_abs[0]["excluded"] is False


# ---------------------------------------------------------------------------
# 2. The three states as the CLI reports them: 0 / 0 / 1
# ---------------------------------------------------------------------------
def _cli(tmp_path, rows_path, manifest, extra=()):
    import subprocess
    man_path = tmp_path / ("man-%s.json" % manifest.get("run_id"))
    man_path.write_text(json.dumps(manifest, indent=1, sort_keys=True) + "\n",
                        encoding="utf-8")
    cmd = [sys.executable, ANALYZE, "--rows", rows_path,
           "--manifest", str(man_path), "--no-census", "--resamples", "50"]
    cmd.extend(extra)
    proc = subprocess.run(cmd, cwd=LONGRUN, capture_output=True, text=True)
    return proc, man_path


def test_cli_absent_stamp_exits_zero_and_says_unstamped(rows48, tmp_path):
    path, _ = rows48
    proc, _m = _cli(tmp_path, path, _manifest(path, name="case-a"))
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert "usable_for unstamped" in proc.stdout
    assert "not a certification" in proc.stdout
    assert "no usable cells" not in proc.stdout


def test_cli_stamped_cell_prints_the_stamp(rows48, tmp_path):
    path, _ = rows48
    proc, _m = _cli(tmp_path, path, _manifest(path, ["h1", "h3"], name="case-b"))
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert "usable_for ['h1', 'h3']" in proc.stdout
    assert "source=manifest" in proc.stdout


def test_cli_empty_stamp_is_a_loud_refusal(rows48, tmp_path):
    path, _ = rows48
    proc, _m = _cli(tmp_path, path, _manifest(path, [], name="case-c"))
    assert proc.returncode == 1
    combined = proc.stdout + proc.stderr
    assert "no usable cells" in combined
    assert "refusing rather than printing an empty table as success" in combined


# ---------------------------------------------------------------------------
# 3. The writer the grid must call, and the shape it writes
# ---------------------------------------------------------------------------
def test_writer_stamps_a_list_of_strings_and_round_trips(rows48, tmp_path):
    path, rows = rows48
    man_path = tmp_path / "man-writer.json"
    man_path.write_text(json.dumps(_manifest(path, name="case-a"),
                                   indent=1, sort_keys=True) + "\n",
                        encoding="utf-8")
    assert "usable_for" not in json.loads(man_path.read_text(encoding="utf-8"))
    A.write_cell_manifest_usable_for(path, ["h1", "h3"], reason="scan clean",
                                     manifest_path=str(man_path))
    man = json.loads(man_path.read_text(encoding="utf-8"))
    assert man["usable_for"] == ["h1", "h3"]
    assert man["usable_for_reason"] == "scan clean"
    kept, records = A.select_usable_cells(
        [(path, len(rows), rows)], manifests=[man], sanity=False)
    assert len(kept) == 1 and records[0]["usable_for"] == ["h1", "h3"]


def test_writer_refuses_a_rows_path_with_no_manifest(rows48):
    path, _ = rows48
    with pytest.raises(FileNotFoundError):
        A.write_cell_manifest_usable_for("/tmp/does-not-exist-rows.jsonl", ["h1"],
                                         manifest_path=None)


# ---------------------------------------------------------------------------
# 4. THE GUARD BITES: mutate a COPY so absent reads as usable; invariant fails
# ---------------------------------------------------------------------------
ABSENT_BRANCH = ('    return {"usable_for": None, "reason": "", "source": USABLE_FOR_UNSTAMPED,\n'
                 '            "manifest_path": None}\n')
MUTANT_BRANCH = ('    return {"usable_for": ["h1", "h2", "h3"], "reason": "",\n'
                 '            "source": "manifest", "manifest_path": None}\n')


def test_guard_bites_when_absent_is_treated_as_usable(rows48, tmp_path):
    """Red proof: the assertions above fail on a `treat absent as usable` build."""
    with open(ANALYZE, encoding="utf-8") as fh:
        src = fh.read()
    assert src.count(ABSENT_BRANCH) == 1, (
        "the absent-key branch moved or changed shape; update ABSENT_BRANCH so "
        "this guard keeps biting (the branch itself must not be edited)")
    mutant_src = src.replace(ABSENT_BRANCH, MUTANT_BRANCH)
    assert mutant_src != src
    mutant_path = tmp_path / "analyze_stats_mutant.py"
    mutant_path.write_text(mutant_src, encoding="utf-8")
    M = _load(str(mutant_path), "analyze_stats_mutant")

    path, rows = rows48
    man = [_manifest(path)]
    rec = M.usable_for_for_path(path, manifests=man, sanity=False)
    # the mutant no longer reports "unknown" ...
    assert rec["usable_for"] is not None, "mutant was supposed to certify the cell"
    assert rec["usable_for"] == ["h1", "h2", "h3"]
    # ... and every invariant the real module satisfies is now violated
    assert rec["usable_for"] is not None and A.usable_for_for_path(
        path, manifests=man, sanity=False)["usable_for"] is None
    kept, records = M.select_usable_cells([(path, len(rows), rows)],
                                          manifests=man, sanity=False)
    assert len(kept) == 1
    assert records[0]["excluded"] is False
    # the load-bearing difference: absence was silently upgraded to a permission
    assert records[0]["analyses"] == ["h1", "h2", "h3"]
    assert records[0]["source"] == "manifest"
    assert records[0]["source"] != A.USABLE_FOR_UNSTAMPED

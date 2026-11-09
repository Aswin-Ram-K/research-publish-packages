"""ANALYSIS-CONSUMER-FIX: the two mechanisms the analyser lacked.

1. `usable_for` is CONSUMED: a cell whose manifest (or the grid's
   `measure/GRID-CELL-SANITY.json` census) stamps `usable_for: []` is excluded
   BY NAME, printed, and recorded in the `--json` document. If every cell is
   stamped empty the analyser exits non-zero with `no usable cells`.
2. TRUNCATED TURNS: a turn with `stop_reason == "length"` (or `truncated` true)
   is not a latency observation of the intended task. It is removed from the
   latency quantiles (p50 AND p95) and counted per arm; the surviving n is
   printed beside the excluded count, and the min-n refusal is unchanged.
   The rule is latency-only: row/ledger/accuracy accounting is untouched.

The tests run on the real artefacts on disk.
"""
import copy
import json
import os
import sys

import pytest

TESTS_DIR = os.path.dirname(os.path.abspath(__file__))
LONGRUN = os.path.dirname(TESTS_DIR)
PTR = os.path.dirname(LONGRUN)
REPO = os.path.dirname(os.path.dirname(PTR))
for p in (LONGRUN, PTR, REPO):
    if p not in sys.path:
        sys.path.insert(0, p)

import analyze_stats as A  # noqa: E402

MEASURE = os.path.join(PTR, "measure")
# era A: 27 rows, pointer-stable, cell_state=in_progress, usable_for: []
ERA_A = os.path.join(MEASURE, "rows-cell-pointer-stable-20261026T182535Z.jsonl")
# pre-RUN-A smoke cell, also usable_for: [] in the grid census
PRE_RUN = os.path.join(MEASURE, "rows-cell-pointer-stable-20261026T145758Z.jsonl")
# 4 arms x 48 turns, no usability stamp anywhere -> must NOT be excluded
MULTI = os.path.join(MEASURE, "rows-longrun-2026-10-26.jsonl")
# tools-on stand-in: 72 rows = 48 turn rows + 24 tool-followup rows
TOOLS = os.path.join(MEASURE, "rows-longrun-v6-tools.jsonl")


def _read_jsonl(path):
    out = []
    with open(path, "rb") as fh:
        for line in fh.read().decode("utf-8", "replace").splitlines():
            line = line.strip()
            if line:
                out.append(json.loads(line))
    return out


@pytest.fixture(scope="module")
def tools_rows():
    return _read_jsonl(TOOLS)


# --------------------------------------------------------------------------
# MECHANISM 1 - usable_for is consumed, by name, and recorded in the document
# --------------------------------------------------------------------------

def test_era_a_cell_is_excluded_by_name_not_averaged(tmp_path, capsys):
    out = tmp_path / "analysis.json"
    rc = A.main(["--rows", ERA_A, MULTI, "--json", str(out)])
    stdout = capsys.readouterr().out
    assert rc == 0
    # printed by NAME, with the reason, on stdout
    assert "usable_for" in stdout
    assert os.path.basename(ERA_A) in stdout
    assert "EXCLUDED" in stdout
    # the exclusion is in the DOCUMENT too, not only on stdout
    doc = json.loads(out.read_text())
    recs = doc["cell_usability"]
    era = [r for r in recs if r["path"].endswith(os.path.basename(ERA_A))]
    assert era, "the excluded cell must be named in the analysis document"
    assert era[0]["excluded"] is True
    assert era[0]["usable_for"] == []
    # the 27 rows of the abandoned cell never entered the tranche
    assert doc["n_rows"] == len(_read_jsonl(MULTI))
    # and the surviving arms are intact
    assert "pointer-stable" in doc["arms"]


def test_no_usable_cells_is_a_nonzero_refusal(capsys):
    with pytest.raises(SystemExit) as exc:
        A.main(["--rows", ERA_A, PRE_RUN])
    assert "no usable cells" in str(exc.value)
    assert "no usable cells" in capsys.readouterr().out


def test_manifest_is_the_carrier_for_usable_for(tmp_path):
    """A manifest stamp outranks the census, in both directions."""
    src = os.path.join(LONGRUN, "manifests",
                       "longrun-2026-10-26T182535Z-pointer-stable-r1.json")
    man = json.loads(open(src, encoding="utf-8").read())
    copy_path = tmp_path / "cell.json"
    copy_path.write_text(json.dumps(man))

    # stamped unusable -> excluded, source named as the manifest
    A.stamp_usable_for(str(copy_path), [], reason="abandoned cell")
    recs = A.load_cell_manifests([str(copy_path)])
    got = A.usable_for_for_path(ERA_A, manifests=recs, sanity=None)
    assert got["usable_for"] == []
    assert got["source"] == "manifest"

    # stamped usable -> NOT excluded, and the census (which says []) loses
    A.stamp_usable_for(str(copy_path), ["latency"], reason="re-run complete")
    recs = A.load_cell_manifests([str(copy_path)])
    got = A.usable_for_for_path(ERA_A, manifests=recs, sanity=None)
    assert got["usable_for"] == ["latency"]
    assert got["source"] == "manifest"


# --------------------------------------------------------------------------
# MECHANISM 2 - truncated turns: excluded from p50 AND p95, counted per arm
# --------------------------------------------------------------------------

def _turn_rows(rows):
    return [r for r in rows if r.get("kind") != "tool-followup"
            and r.get("kind") in ("turn", "turn-initial")]


def test_truncated_turns_excluded_and_counted_with_backcomputed_n(tools_rows):
    base_rows = copy.deepcopy(tools_rows)
    base = A.analyze(base_rows)
    arm = sorted(base["arms"])[0]
    before = base["arms"][arm]

    rows = copy.deepcopy(tools_rows)
    turns = _turn_rows(rows)
    assert len(turns) >= 4
    for r in turns[:2]:
        r["stop_reason"] = "length"
    for r in turns[2:4]:
        r["truncated"] = True

    after = A.analyze(rows)["arms"][arm]
    trunc = after["truncated_turns"]
    assert trunc["excluded"] == 4
    assert trunc["total"] == before["ttft"]["selected"]
    assert trunc["fraction"] == pytest.approx(4.0 / before["ttft"]["selected"], rel=1e-9)
    assert trunc["by_stop_reason"]["length"] >= 2

    # n is NOT silently lowered: surviving n is printed beside the excluded count
    assert after["ttft"]["used"] == before["ttft"]["used"] - 4
    assert (after["ttft"]["used"] + trunc["excluded"]
            + after["ttft"]["dropped_null"] + after["ttft"]["dropped_unavailable"]
            == after["ttft"]["selected"])
    # the same population feeds p50 and p95 (the rule applies to both)
    assert after["p50"]["n"] == after["ttft"]["used"]
    if after["p95"].get("refused"):
        assert after["p95"]["n"] == after["ttft"]["used"]
    else:
        assert after["p95"]["n"] == after["ttft"]["used"]

    # latency-only: the row/ledger/accuracy accounting is untouched
    assert after["n_rows"] == before["n_rows"]
    assert after["accuracy"]["decidable"] == before["accuracy"]["decidable"]
    assert after["accuracy"]["passed"] == before["accuracy"]["passed"]


def test_format_arm_states_excluded_count_beside_surviving_n(tools_rows):
    rows = copy.deepcopy(tools_rows)
    turns = _turn_rows(rows)
    turns[0]["stop_reason"] = "length"
    entry = A.analyze(rows)["arms"][sorted(A.analyze(rows)["arms"])[0]]
    text = "\n".join(A._format_arm(entry))
    assert "truncated_turns" in text
    assert "surviving n=" in text
    assert "excluded" in text


def test_split_truncated_is_the_single_rule():
    rows = [
        {"arm": "x", "turn": 1, "kind": "turn", "ttft_ms": 10, "stop_reason": "stop"},
        {"arm": "x", "turn": 2, "kind": "turn", "ttft_ms": 20, "stop_reason": "length"},
        {"arm": "x", "turn": 3, "kind": "turn", "ttft_ms": 30, "truncated": True},
        {"arm": "x", "turn": 4, "kind": "turn", "ttft_ms": 40},
    ]
    kept, meta = A.split_truncated(rows)
    assert [r["turn"] for r in kept] == [1, 4]
    assert meta["excluded"] == 2
    assert meta["total"] == 4
    assert meta["fraction"] == pytest.approx(0.5)

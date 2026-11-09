#!/usr/bin/env python3
"""Tests for `tools/run_grid_report.py` — the contract's refusals, proven before data exists.

The grid has not finished a single cell, so every case here is SYNTHETIC and lives in
pytest's own tmp dir.  Nothing is written to `measure/`, no `rows-cell-*.jsonl` is created
there, and no network request is made.

Every case names the frozen rule it pins:

  (a) clean two-arm pooled grid                  -> adjudicable, with numbers
  (b) binding arm n_eff < 60                     -> not_adjudicable_effective_n, arm named
  (c) usable_for: []                             -> excluded by name and counted
  (d) usable_for ABSENT                          -> REFUSED (analyze_stats.py:749 trap)
  (e) stop_reason=length turn                    -> dropped from quantiles, counted
  (f) era A + era B present                      -> epochs_never_pooled, no pooled interval
  (g) missing ledger baseline                    -> refuse, never delta=0
  (h) tvs absent                                 -> "UNDEFINED" with a reason, never 0
  (i) every cell refused                         -> the report still EMITS its refusals
  (j) ordering                                   -> verbosity precedes spend

Three red->green proofs are at the bottom: neuter ONE guard, watch the matching
assertion go red, restore.  The failing assertion text is quoted in each docstring.

Run: python3 -m pytest experiments/ptr-engine/tests/test_run_grid_report.py -q
"""
from __future__ import annotations

import importlib.util
import json
import math
import os
import random
import sys

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
TOOL = os.path.join(HERE, "..", "tools", "run_grid_report.py")

_spec = importlib.util.spec_from_file_location("run_grid_report", TOOL)
G = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(G)

S = G.S
REFUSAL_FLOOR = G.REFUSAL_FLOOR
REFUSAL_EFFECTIVE_N = G.REFUSAL_EFFECTIVE_N
REFUSAL_UNSTAMPED = G.REFUSAL_UNSTAMPED
REFUSAL_BASELINE = G.REFUSAL_BASELINE

FIXTURE = "f" * 64
HARNESS = "h" * 64


# ---------------------------------------------------------------------------
# synthetic cell construction (tmp dirs only)
# ---------------------------------------------------------------------------
def _turn_rows(arm, n, base=200.0, noise=40.0, rep=1, tools_mode="read_file",
               stop_length_at=(), values=None):
    """One turn-initial row per turn, carrying the four load-bearing provenance fields."""
    rows = []
    rnd = random.Random(sum(ord(c) for c in arm) * 97 + rep)
    for t in range(1, n + 1):
        if values is not None:
            ttft = float(values[t - 1])
        else:
            ttft = base + noise * rnd.random()
        row = {
            "arm": arm, "rep": rep, "turn": t, "turn_index": t,
            "kind": "turn-initial", "send_index": 0,
            "ttft_ms": ttft, "ttft_s": ttft / 1000.0,
            "prompt_tokens": 1000 + t,
            "cached_tokens": min(900, 9 * t),
            "uncached_tokens": max(1, 1000 + t - min(900, 9 * t)),
            "completion_tokens": 40 + t,
            "content": "c" * (80 + t),
            "answer_raw": "A" * (20 + t),
            "answer_kind": "NUM", "stop_reason": "stop", "truncated": False,
            "timing_usable": True,
            "model": "occamy-1.0", "thinking": "off", "tools_mode": tools_mode,
            "fixture_sha256": FIXTURE, "fixture_id": "LR-01.v8",
            "harness_sha256": HARNESS, "endpoint": "http://192.168.2.168:8012/v1",
            "max_tokens": 4096,
            "ts": "2026-10-26T00:%02d:%02dZ" % (t // 60, t % 60),
        }
        if t in stop_length_at:
            row["stop_reason"] = "length"
            row["truncated"] = True
            row["ttft_ms"] = 99999.0
        rows.append(row)
    return rows


class Cell:
    """A synthetic cell on disk plus the manifest that stamps it."""

    def __init__(self, root, name, rows, usable_for, stamp=True):
        self.path = os.path.join(root, name + ".jsonl")
        with open(self.path, "w", encoding="utf-8") as fh:
            for row in rows:
                fh.write(json.dumps(row) + "\n")
        self.name = name
        self.rows = rows
        self.manifest = None
        if stamp:
            mdir = os.path.join(root, "manifests")
            os.makedirs(mdir, exist_ok=True)
            self.manifest = os.path.join(mdir, name + ".manifest.json")
            payload = {"rows_path": self.path, "unit": "SYNTHETIC",
                       "rows": len(rows), "arms": sorted({r["arm"] for r in rows})}
            if usable_for is not None:
                payload["usable_for"] = list(usable_for)
                payload["usable_for_reason"] = "synthetic case"
            with open(self.manifest, "w", encoding="utf-8") as fh:
                json.dump(payload, fh, indent=1, sort_keys=True)


def _baseline(root, requests=1128, remaining=3192):
    path = os.path.join(root, "LEDGER-GRID-BASELINE-2.json")
    with open(path, "w", encoding="utf-8") as fh:
        json.dump({"unit": "SYNTHETIC", "requests": requests, "remaining": remaining,
                   "cap": 4320, "frozen_at": "2026-10-26T19:04:18Z"}, fh, indent=1)
    return path


def _ledger(root, spent=1150):
    path = os.path.join(root, "REQUEST-LEDGER.json")
    with open(path, "w", encoding="utf-8") as fh:
        json.dump({"budget": {"spent_raw": spent, "spent": spent}}, fh, indent=1)
    return path


def _build(root, cells, baseline=None, ledger=None, grade=None, **kw):
    return G.build_report(
        rows_paths=[c.path for c in cells],
        manifest_dir=os.path.join(root, "manifests"),
        sanity_path=False,
        grade_path=grade,
        baseline_path=baseline or _baseline(root),
        ledger_path=ledger or _ledger(root),
        shape_path=None,
        **kw)


def _grid(doc, era=None):
    grids = doc["h1"]["grids"]
    if era is None:
        assert len(grids) == 1, "expected exactly one grid, got %d" % len(grids)
        return grids[0]
    return [g for g in grids if g["era"] == era][0]


def _arm(grid, name):
    return [a for a in grid["arms"] if a["arm"] == name][0]


# ---------------------------------------------------------------------------
# (a) a clean two-arm pooled grid is adjudicable, with the numbers
# ---------------------------------------------------------------------------
def test_a_clean_two_arm_grid_is_adjudicable(tmp_path):
    root = str(tmp_path)
    cells = [
        Cell(root, "rows-cell-pointer-stable-r1",
             _turn_rows("pointer-stable", 60, base=200.0, noise=10.0, rep=1), ["h1", "h2", "h3", "tvs"]),
        Cell(root, "rows-cell-pointer-stable-r2",
             _turn_rows("pointer-stable", 60, base=200.0, noise=10.0, rep=2), ["h1", "h2", "h3", "tvs"]),
        Cell(root, "rows-cell-transcript-grow-r1",
             _turn_rows("transcript-grow", 60, base=400.0, noise=10.0, rep=1), ["h1", "h2", "h3", "tvs"]),
        Cell(root, "rows-cell-transcript-grow-r2",
             _turn_rows("transcript-grow", 60, base=400.0, noise=10.0, rep=2), ["h1", "h2", "h3", "tvs"]),
    ]
    doc = _build(root, cells)
    grid = _grid(doc)

    assert grid["verdict"] == "adjudicable", grid.get("refusal")
    assert grid["pooled_disjoint"] is True

    c = _arm(grid, "pointer-stable")
    a = _arm(grid, "transcript-grow")
    # reps pool: 2 reps x 60 turns, one row per turn, none truncated
    assert c["n_raw"] == 120 and c["n_dedup"] == 120 and c["n_used"] == 120
    assert c["n_truncated_excluded"] == 0
    # n_eff is < n (r is not exactly 0 on a finite series) and clears the floor
    assert c["r_lag1"] is not None
    assert c["n_eff"] == pytest.approx(c["n_used"] * (1 - c["r_lag1"]) / (1 + c["r_lag1"]))
    assert c["n_eff"] == pytest.approx(120.0, rel=0.35)

    # the intervals are real intervals, each with its own n
    assert set(c["p95"]) == {"value", "lo", "hi", "n"}
    assert c["p95"]["lo"] <= c["p95"]["value"] <= c["p95"]["hi"]
    assert c["p50"]["n"] == 120 and c["p95"]["n"] == 120

    # disjoint intervals, C lower -> separated_lower by the prereg's strict rule
    assert c["p95"]["hi"] < a["p95"]["lo"]
    assert grid["comparison"]["verdict"] == "separated_lower"

    # H2 travels both limbs per arm, with a sign and its own n
    for row in doc["h2"]["per_arm"]:
        assert row["cached_inclusive_tokens_per_turn"] is not None
        assert row["uncached_tokens_per_turn"] is not None
        assert row["difference_sign"] == 1
        assert row["n"] == 120
    assert doc["h2"]["comparison"]["verdict"] in ("h2_pass", "h2_failed_split", "h2_failed")

    # no refusal line is emitted for a term that WAS obtained
    kinds = {r["kind"] for r in doc["refusals"]}
    assert REFUSAL_FLOOR not in kinds and REFUSAL_EFFECTIVE_N not in kinds
    # every cell is included and counted
    assert all(cell["included"] for cell in doc["cells"])


# ---------------------------------------------------------------------------
# (b) the binding arm's effective n is below 60 -> refuse by name, both numbers
# ---------------------------------------------------------------------------
def test_b_effective_n_below_floor_names_the_binding_arm(tmp_path):
    root = str(tmp_path)
    # a smooth series: 120 turns, lag-1 r near 0.99 -> n_eff far below 60
    smooth = [300.0 + 50.0 * math.sin(t / 12.0) for t in range(1, 121)]
    cells = [
        Cell(root, "rows-cell-pointer-stable-r1",
             _turn_rows("pointer-stable", 120, values=smooth, rep=1), ["h1", "h2", "h3", "tvs"]),
        Cell(root, "rows-cell-transcript-grow-r1",
             _turn_rows("transcript-grow", 120, base=400.0, noise=10.0, rep=1), ["h1", "h2", "h3", "tvs"]),
    ]
    doc = _build(root, cells)
    grid = _grid(doc)
    arm = _arm(grid, "pointer-stable")

    assert arm["n_raw"] == 120, "the raw-n floor is NOT what refuses this grid"
    assert arm["r_lag1"] > 0.9
    assert arm["n_eff"] < 60
    assert grid["verdict"] == REFUSAL_EFFECTIVE_N
    assert grid["binding_arm"] == "pointer-stable"
    assert grid["binding_n_eff"] == pytest.approx(arm["n_eff"])
    assert "pointer-stable" in grid["refusal"]
    assert "120" in grid["refusal"]
    # the refusal is a first-class record, not a stderr line
    assert [r["kind"] for r in doc["refusals"]].count(REFUSAL_EFFECTIVE_N) == 1
    # and the p95 is still a real interval (it is the VERDICT that is refused, not the number)
    assert arm["p95"]["n"] == 120


# ---------------------------------------------------------------------------
# (c) usable_for: [] is excluded BY NAME and counted
# ---------------------------------------------------------------------------
def test_c_empty_usable_for_excluded_by_name(tmp_path):
    root = str(tmp_path)
    cells = [
        Cell(root, "rows-cell-pointer-stable-r1",
             _turn_rows("pointer-stable", 60, rep=1), ["h1", "h2", "h3", "tvs"]),
        Cell(root, "rows-cell-transcript-grow-r1",
             _turn_rows("transcript-grow", 60, rep=1), ["h1", "h2", "h3", "tvs"]),
        Cell(root, "rows-cell-abandoned-era-a", _turn_rows("pointer-stable", 27, rep=1), []),
    ]
    doc = _build(root, cells)
    excluded = [c for c in doc["cells"] if not c["included"]]
    assert len(excluded) == 1
    assert excluded[0]["name"].startswith("rows-cell-abandoned-era-a")
    assert excluded[0]["usable_for"] == []
    assert excluded[0]["rows"] == 27, "the excluded row count must travel with the exclusion"
    assert excluded[0]["refusal_kind"] == "excluded_by_stamp"
    assert any("usable_for: []" in r["text"] for r in doc["refusals"])
    # excluded rows never reach a quantile: only the two included arms are in the grid
    grid = _grid(doc)
    assert {a["arm"] for a in grid["arms"]} == {"pointer-stable", "transcript-grow"}
    assert all(a["n_raw"] == 60 for a in grid["arms"])


# ---------------------------------------------------------------------------
# (d) an ABSENT usable_for is a refusal -- the analyze_stats.py:749 trap
# ---------------------------------------------------------------------------
def test_d_absent_usable_for_is_refused_where_the_analyser_includes(tmp_path):
    root = str(tmp_path)
    good = Cell(root, "rows-cell-pointer-stable-r1",
                _turn_rows("pointer-stable", 60, rep=1), ["h1", "h2", "h3", "tvs"])
    unstamped = Cell(root, "rows-cell-transcript-grow-r1",
                     _turn_rows("transcript-grow", 60, rep=1), None, stamp=True)

    # the trap, demonstrated on the analyser's own function:
    files = [(unstamped.path, len(unstamped.rows), unstamped.rows)]
    manifests = S.load_cell_manifests(manifest_dir=os.path.join(root, "manifests"))
    kept, records = S.select_usable_cells(files, manifests=manifests, sanity=False)
    assert records[0]["excluded"] is False
    assert len(kept) == 1, ("analyze_stats.select_usable_cells INCLUDES an unstamped cell "
                            "(analyze_stats.py:749): %r" % (records[0],))

    # this consumer refuses it instead
    doc = _build(root, [good, unstamped])
    rec = [c for c in doc["cells"] if c["name"].startswith("rows-cell-transcript-grow-r1")][0]
    assert rec["usable_for"] is None
    assert rec["included"] is False
    assert rec["refusal_kind"] == REFUSAL_UNSTAMPED
    assert any(r["kind"] == REFUSAL_UNSTAMPED for r in doc["refusals"])
    assert any("includes on absence" in r["text"] for r in doc["refusals"])
    # and it cannot enter a grid
    grid = _grid(doc)
    assert {a["arm"] for a in grid["arms"]} == {"pointer-stable"}


# ---------------------------------------------------------------------------
# (e) a stop_reason=length turn leaves the quantiles, and is counted
# ---------------------------------------------------------------------------
def test_e_truncated_turn_dropped_from_quantiles_and_counted(tmp_path):
    root = str(tmp_path)
    length_at = {11, 23, 35, 47, 59, 61, 73, 85, 97, 109}
    rows = _turn_rows("pointer-stable", 110, base=200.0, noise=5.0, rep=1,
                      stop_length_at=length_at)
    cells = [Cell(root, "rows-cell-pointer-stable-r1", rows, ["h1", "h2", "h3", "tvs"])]
    doc = _build(root, cells)
    arm = _grid(doc)["arms"][0]

    assert arm["n_raw"] == 110
    assert arm["n_truncated_excluded"] == 10
    assert arm["n_used"] == 100
    assert arm["truncated_by_stop_reason"] == {"length": 10}
    # the 99,999 ms cap-length turns did not move the quantiles
    assert arm["p50"]["value"] < 300.0, arm["p50"]
    assert arm["p95"]["value"] < 300.0, arm["p95"]
    assert arm["p95"]["n"] == 100


# ---------------------------------------------------------------------------
# (f) era A and era B never pool
# ---------------------------------------------------------------------------
def test_f_era_a_and_era_b_never_pool(tmp_path):
    root = str(tmp_path)
    cells = [
        Cell(root, "rows-cell-pointer-stable-eraA",
             _turn_rows("pointer-stable", 60, base=900.0, rep=1, tools_mode="off"),
             ["h1", "h2", "h3", "tvs"]),
        Cell(root, "rows-cell-pointer-stable-eraB",
             _turn_rows("pointer-stable", 60, base=200.0, rep=1, tools_mode="read_file"),
             ["h1", "h2", "h3", "tvs"]),
    ]
    doc = _build(root, cells)
    grids = doc["h1"]["grids"]
    assert len(grids) == 2, "two provenances must be two grids"
    assert {g["era"] for g in grids} == {"era_a_tools_off", "era_b_tools_on"}
    # each grid's arms come from that grid's own files only
    for grid in grids:
        assert {a["arm"] for a in grid["arms"]} == {"pointer-stable"}
        path = grid["arms"][0]["source_paths"][0]
        assert grid["era"] in ("era_a_tools_off",) or "eraB" in path
    assert len(doc["epochs_never_pooled"]) == 2
    for rec in doc["epochs_never_pooled"]:
        assert rec["paths"] and rec["reason"]
    # no interval is attributed to both eras: the 900 ms era has its own p50
    by_era = {g["era"]: g["arms"][0]["p50"]["value"] for g in grids}
    assert by_era["era_a_tools_off"] > 800.0
    assert by_era["era_b_tools_on"] < 400.0
    assert all(g["pooled_disjoint"] for g in grids)


# ---------------------------------------------------------------------------
# (g) a missing ledger baseline is refused, never assumed
# ---------------------------------------------------------------------------
def test_g_missing_baseline_refuses_rather_than_assuming(tmp_path, capsys):
    root = str(tmp_path)
    cell = Cell(root, "rows-cell-pointer-stable-r1",
                _turn_rows("pointer-stable", 60, rep=1), ["h1", "h2", "h3", "tvs"])
    missing = os.path.join(root, "LEDGER-GRID-BASELINE-2.json")
    assert not os.path.exists(missing)

    with pytest.raises(G.RefusedEmission) as exc:
        _build(root, [cell], baseline=missing)
    assert exc.value.kind == REFUSAL_BASELINE
    assert "NOT assumed from 0" in str(exc.value)

    rc = G.main(["--rows", cell.path, "--manifest-dir", os.path.join(root, "manifests"),
                 "--baseline", missing, "--ledger", _ledger(root), "--out",
                 os.path.join(root, "out.json")])
    assert rc == 3, "a missing baseline is exit 3, not a report with delta 0"
    assert not os.path.exists(os.path.join(root, "out.json"))
    assert "refusing" in capsys.readouterr().err


# ---------------------------------------------------------------------------
# (h) tvs absent -> "UNDEFINED" with a reason, never 0
# ---------------------------------------------------------------------------
def test_h_tvs_absent_is_undefined_never_zero(tmp_path):
    root = str(tmp_path)
    cells = [
        Cell(root, "rows-cell-pointer-stable-r1",
             _turn_rows("pointer-stable", 60, rep=1), ["h1", "h2", "h3", "tvs"]),
        Cell(root, "rows-cell-transcript-grow-r1",
             _turn_rows("transcript-grow", 60, rep=1), ["h1", "h2", "h3", "tvs"]),
    ]
    doc = _build(root, cells)          # no grade document at all
    assert doc["tvs"] == "UNDEFINED"
    assert doc["tvs"] != 0 and doc["tvs"] is not None
    assert doc["tvs_reason"]
    assert any(r["kind"] == G.TVS_UNDEFINED for r in doc["refusals"])
    # H3 is refused for the same reason, with no imputed x/12
    assert doc["h3"]["x_12"] is None and doc["h3"]["x_9"] is None
    assert doc["h3"]["verdict"] == "not_adjudicable"
    assert doc["h3"]["mcnemar"]["p"] is None


# ---------------------------------------------------------------------------
# (i) every cell refused -> the report still EMITS its refusals
# ---------------------------------------------------------------------------
def test_i_all_cells_refused_still_emits_the_refusal_report(tmp_path):
    root = str(tmp_path)
    cells = [
        Cell(root, "rows-cell-pointer-stable-r1",
             _turn_rows("pointer-stable", 27, rep=1), []),
        Cell(root, "rows-cell-transcript-grow-r1",
             _turn_rows("transcript-grow", 6, rep=1), []),
    ]
    doc = _build(root, cells)
    assert doc["h1"]["grids"] == []
    assert doc["verdicts"]["overall"] == "not_adjudicable"
    assert len([c for c in doc["cells"] if not c["included"]]) == 2
    assert len(doc["refusals"]) >= 2
    # nothing presents a number it did not obtain
    assert doc["tvs"] == "UNDEFINED"
    assert all(row["mean_completion_tokens"] is None for row in doc["verbosity"]["per_arm"])


# ---------------------------------------------------------------------------
# (j) verbosity is emitted BEFORE any cost line
# ---------------------------------------------------------------------------
def test_j_verbosity_precedes_spend(tmp_path):
    root = str(tmp_path)
    cells = [Cell(root, "rows-cell-pointer-stable-r1",
                  _turn_rows("pointer-stable", 60, rep=1), ["h1", "h2", "h3", "tvs"])]
    doc = _build(root, cells)
    keys = list(doc.keys())
    assert keys.index("verbosity") < keys.index("spend")
    # and in the rendered page the section order agrees
    md = G.render_markdown(doc)
    assert md.index("## 5. Verbosity") < md.index("## 6. Spend")
    assert doc["spend"]["delta"] == 22 and doc["spend"]["baseline"]["requests"] == 1128


# ---------------------------------------------------------------------------
# red -> green: neuter one guard, watch the matching assertion fail, restore
# ---------------------------------------------------------------------------
def _red(cells, monkeypatch, guard, replacement, check):
    """Neuter ONE guard, run `check(doc)` (the green assertion), return the red text."""
    monkeypatch.setattr(G, guard, replacement)
    try:
        with pytest.raises(AssertionError) as err:
            check(_build(cells[0], cells[1]))
        print("[RED] %s neutered -> %s" % (guard, str(err.value).replace("\n", " ")))
        return str(err.value)
    finally:
        monkeypatch.undo()


def test_red_effective_n_guard(tmp_path, monkeypatch):
    """Neuter `effective_n_verdict` -> the effective-n assertion goes red.

    Failing assertion: `assert grid["verdict"] == "not_adjudicable_effective_n"`
    becomes `AssertionError: assert 'adjudicable' == 'not_adjudicable_effective_n'`.
    """
    root = str(tmp_path)
    smooth = [300.0 + 50.0 * math.sin(t / 12.0) for t in range(1, 121)]
    cells = [Cell(root, "rows-cell-pointer-stable-r1",
                  _turn_rows("pointer-stable", 120, values=smooth, rep=1),
                  ["h1", "h2", "h3", "tvs"])]

    def check(doc):
        grid = _grid(doc)
        assert grid["verdict"] == REFUSAL_EFFECTIVE_N

    text = _red((root, cells), monkeypatch, "effective_n_verdict",
                lambda n_eff, floor=60: None, check)
    assert "not_adjudicable_effective_n" in text
    assert "adjudicable" in text
    # green again once the guard is restored
    assert _grid(_build(root, cells))["verdict"] == REFUSAL_EFFECTIVE_N


def test_red_raw_floor_guard(tmp_path, monkeypatch):
    """Neuter `raw_floor_verdict` -> the floor assertion goes red.

    Failing assertion: `assert grid["verdict"] == "not_adjudicable_floor"`
    becomes `AssertionError: assert 'not_adjudicable_effective_n' == 'not_adjudicable_floor'`
    -- with the raw-n floor gone the grid is labelled by the NEXT guard instead, which is
    precisely the confusion the floor exists to prevent (a 40-turn arm is not a
    near-miss on effective n; it never had the turns).
    """
    root = str(tmp_path)
    cells = [Cell(root, "rows-cell-pointer-stable-r1",
                  _turn_rows("pointer-stable", 40, rep=1), ["h1", "h2", "h3", "tvs"])]

    def check(doc):
        grid = _grid(doc)
        assert grid["verdict"] == REFUSAL_FLOOR

    text = _red((root, cells), monkeypatch, "raw_floor_verdict",
                lambda n_raw, floor=60: None, check)
    assert REFUSAL_FLOOR in text
    assert REFUSAL_EFFECTIVE_N in text
    # green again once the guard is restored, with the analyser's own refusal text
    grid = _grid(_build(root, cells))
    assert grid["verdict"] == REFUSAL_FLOOR
    assert "refusing p95" in grid["refusal"]


def test_red_usable_for_absence_guard(tmp_path, monkeypatch):
    """Neuter `cell_inclusion` -> the absent-stamp assertion goes red.

    Failing assertion: `assert rec["included"] is False`
    becomes `AssertionError: assert True is False`.
    """
    root = str(tmp_path)
    cells = [
        Cell(root, "rows-cell-pointer-stable-r1",
             _turn_rows("pointer-stable", 60, rep=1), ["h1", "h2", "h3", "tvs"]),
        Cell(root, "rows-cell-transcript-grow-r1",
             _turn_rows("transcript-grow", 60, rep=1), None),
    ]
    def check(doc):
        rec = [c for c in doc["cells"]
               if c["name"].startswith("rows-cell-transcript-grow-r1")][0]
        assert rec["included"] is False

    text = _red((root, cells), monkeypatch, "cell_inclusion",
                lambda rec: (True, "", ""), check)
    assert "True is False" in text
    doc = _build(root, cells)
    rec = [c for c in doc["cells"] if c["name"].startswith("rows-cell-transcript")][0]
    assert rec["included"] is False and rec["refusal_kind"] == REFUSAL_UNSTAMPED

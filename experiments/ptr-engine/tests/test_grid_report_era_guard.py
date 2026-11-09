#!/usr/bin/env python3
"""Era-mixing guard for `tools/run_grid_report.py` — a pooled number is impossible, not discouraged.

`V-GRID-REPORT` (exec `c3280e05`) attempt 4: two eras (fixture_sha256 v7 and v8) were fed in
together, H1 correctly split them into two grids, and the report STILL printed
`ratio **2.5000**` and `**100800.0** tokens` because `h2_block()`, `tvs_block()` and
`verbosity_block()` were fed the global `included_rows` / `per_arm_all` instead of a
provenance cluster.  `refusals` was `[]`.

The guard pinned here: a pooled term may print a number only for a set of cells whose
declared provenance agrees (`same_provenance`, via `cluster_cells`).  A set spanning more
than one cluster must yield the NAMED refusal `refused_mixed_era` naming every era present
and the cell that introduced it, and must print no interval, no accuracy and no `n`.

Cases:
  (1) two fixture versions, same tools mode      -> refused_mixed_era, nothing pooled
  (2) era A (tools off) + era B (tools on)       -> refused_mixed_era, both eras named
  (3) two single-era files CONCATENATED on disk  -> refused_mixed_era
  (4) ONE era only, two arms                     -> still adjudicable, H2/TVS numbers printed
  (5) mixed input: H1 still splits into 2 grids  -> no over-refusal of the licensed per-grid n
  (6) the refusal names each era and its cell    -> era + path + fixture in the text
  (7) red->green: neatuer the guard             -> the pooled number comes back (assertion red)

Run: python3 -m pytest experiments/ptr-engine/tests/test_grid_report_era_guard.py -q
"""
from __future__ import annotations

import importlib.util
import json
import os
import random

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
TOOL = os.path.join(HERE, "..", "tools", "run_grid_report.py")

_spec = importlib.util.spec_from_file_location("run_grid_report", TOOL)
G = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(G)

REFUSAL_MIXED_ERA = "refused_mixed_era"

FIXTURE_V7 = "7" * 64
FIXTURE_V8 = "8" * 64
HARNESS = "h" * 64


# ---------------------------------------------------------------------------
# synthetic cells (pytest tmp dirs only; nothing under measure/ is touched)
# ---------------------------------------------------------------------------
def _turn_rows(arm, n, fixture_sha256, fixture_id, tools_mode="read_file",
               prompt_base=1000, base=200.0, noise=40.0, rep=1):
    rows = []
    rnd = random.Random(sum(ord(c) for c in arm) * 97 + rep + prompt_base)
    for t in range(1, n + 1):
        prompt = prompt_base + 10 * t
        cached = min(cached_cap(prompt), 9 * t)
        row = {
            "arm": arm, "rep": rep, "turn": t, "turn_index": t,
            "kind": "turn-initial", "send_index": 0,
            "ttft_ms": base + noise * rnd.random(),
            "ttft_s": (base + noise * rnd.random()) / 1000.0,
            "prompt_tokens": prompt,
            "cached_tokens": cached,
            "uncached_tokens": max(1, prompt - cached),
            "completion_tokens": 40 + t,
            "content": "c" * (80 + t),
            "answer_raw": "A" * (20 + t),
            "answer_kind": "NUM", "stop_reason": "stop", "truncated": False,
            "timing_usable": True,
            "model": "occamy-1.0", "thinking": "off", "tools_mode": tools_mode,
            "fixture_sha256": fixture_sha256, "fixture_id": fixture_id,
            "harness_sha256": HARNESS, "endpoint": "http://127.0.0.1:1/v1",
            "max_tokens": 4096,
            "ts": "2026-10-26T00:%02d:%02dZ" % (t // 60, t % 60),
        }
        rows.append(row)
    return rows


def cached_cap(prompt):
    return max(0, prompt - 1)


class Cell:
    def __init__(self, root, name, rows, usable_for, stamp=True):
        self.path = os.path.join(root, name + ".jsonl")
        with open(self.path, "w", encoding="utf-8") as fh:
            for row in rows:
                fh.write(json.dumps(row) + "\n")
        self.name = name
        self.rows = rows
        if stamp:
            mdir = os.path.join(root, "manifests")
            os.makedirs(mdir, exist_ok=True)
            self.manifest = os.path.join(mdir, name + ".manifest.json")
            payload = {"rows_path": self.path, "unit": "SYNTHETIC",
                       "rows": len(rows), "arms": sorted({r["arm"] for r in rows})}
            if usable_for is not None:
                payload["usable_for"] = list(usable_for)
                payload["usable_for_reason"] = "synthetic era-guard case"
            with open(self.manifest, "w", encoding="utf-8") as fh:
                json.dump(payload, fh, indent=1, sort_keys=True)


def _baseline(root):
    path = os.path.join(root, "LEDGER-GRID-BASELINE-2.json")
    with open(path, "w", encoding="utf-8") as fh:
        json.dump({"unit": "SYNTHETIC", "requests": 1128, "remaining": 3192,
                   "cap": 4320, "frozen_at": "2026-10-26T19:04:18Z"}, fh, indent=1)
    return path


def _ledger(root):
    path = os.path.join(root, "REQUEST-LEDGER.json")
    with open(path, "w", encoding="utf-8") as fh:
        json.dump({"budget": {"spent_raw": 1150, "spent": 1150}}, fh, indent=1)
    return path


def _build(root, cells, **kw):
    return G.build_report(rows_paths=[c.path for c in cells],
                          manifest_dir=os.path.join(root, "manifests"),
                          sanity_path=False, grade_path=None,
                          baseline_path=_baseline(root), ledger_path=_ledger(root),
                          shape_path=None, **kw)


def _two_era_cells(root, n=70):
    """attempt 4's shape: C+A at fixture v7 and C+A at fixture v8, four manifests."""
    return [
        Cell(root, "rows-cell-pointer-stable-v7",
             _turn_rows("pointer-stable", n, FIXTURE_V7, "LR-01.v7", prompt_base=9000),
             ["h1", "h2"]),
        Cell(root, "rows-cell-transcript-grow-v7",
             _turn_rows("transcript-grow", n, FIXTURE_V7, "LR-01.v7", prompt_base=9000),
             ["h1", "h2"]),
        Cell(root, "rows-cell-pointer-stable-v8",
             _turn_rows("pointer-stable", n, FIXTURE_V8, "LR-01.v8", prompt_base=1000),
             ["h1", "h2"]),
        Cell(root, "rows-cell-transcript-grow-v8",
             _turn_rows("transcript-grow", n, FIXTURE_V8, "LR-01.v8", prompt_base=1000),
             ["h1", "h2"]),
    ]


def _mixed_kinds(doc):
    return [r for r in doc["refusals"] if r["kind"] == REFUSAL_MIXED_ERA]


# ---------------------------------------------------------------------------
# (1) two fixture versions, same tools mode -> refused, nothing pooled
# ---------------------------------------------------------------------------
def test_two_fixture_versions_are_refused_not_pooled(tmp_path):
    root = str(tmp_path)
    doc = _build(root, _two_era_cells(root))

    assert doc["h2"]["comparison"]["verdict"] == REFUSAL_MIXED_ERA, doc["h2"]["comparison"]
    assert doc["h2"]["per_arm"] == [], "no arm mean may be printed across provenances"
    assert doc["tvs"] == "UNDEFINED"
    assert REFUSAL_MIXED_ERA in doc["tvs_reason"]
    assert doc["verbosity"]["per_arm"] == [], "no verbosity mean/n across provenances"
    assert _mixed_kinds(doc), "the refusal is a first-class row, not a silent omission"

    md = G.render_markdown(doc)
    assert "refused_mixed_era" in md
    assert "Both limbs, C\u2212A" not in md, "the pooled H2 ratio line must not be printed"
    assert "tokens through turn" not in md, "the pooled TVS figure must not be printed"


# ---------------------------------------------------------------------------
# (2) era A (tools off) + era B (tools on) -> refused, both eras named
# ---------------------------------------------------------------------------
def test_tools_off_plus_tools_on_is_refused(tmp_path):
    root = str(tmp_path)
    cells = [
        Cell(root, "rows-cell-pointer-stable-eraA",
             _turn_rows("pointer-stable", 60, FIXTURE_V7, "LR-01.v7", tools_mode="off",
                        prompt_base=9000), ["h1", "h2"]),
        Cell(root, "rows-cell-pointer-stable-eraB",
             _turn_rows("pointer-stable", 60, FIXTURE_V8, "LR-01.v8", tools_mode="read_file",
                        prompt_base=1000), ["h1", "h2"]),
    ]
    doc = _build(root, cells)
    assert doc["h2"]["comparison"]["verdict"] == REFUSAL_MIXED_ERA
    assert doc["h2"]["per_arm"] == []
    text = " ".join(r["text"] for r in _mixed_kinds(doc))
    assert "era_a_tools_off" in text and "era_b_tools_on" in text


# ---------------------------------------------------------------------------
# (3) CONCATENATING two real single-era rows files -> refused
# ---------------------------------------------------------------------------
def test_concatenated_single_era_files_are_refused(tmp_path):
    root = str(tmp_path)
    era_cells = _two_era_cells(root)
    c7, _a7, c8, _a8 = era_cells
    joined = os.path.join(root, "rows-cell-pointer-stable-joined.jsonl")
    with open(joined, "w", encoding="utf-8") as out:
        for src in (c7.path, c8.path):
            with open(src, encoding="utf-8") as fh:
                out.write(fh.read())
    mdir = os.path.join(root, "manifests")
    os.makedirs(mdir, exist_ok=True)
    with open(os.path.join(mdir, "rows-cell-pointer-stable-joined.manifest.json"),
              "w", encoding="utf-8") as fh:
        json.dump({"rows_path": joined, "unit": "SYNTHETIC",
                   "rows": len(c7.rows) + len(c8.rows),
                   "arms": ["pointer-stable"], "usable_for": ["h1", "h2"],
                   "usable_for_reason": "synthetic era-guard case"}, fh, sort_keys=True)
    class _Merged:
        path = joined
        name = "rows-cell-pointer-stable-joined"
        rows = c7.rows + c8.rows
    merged = _Merged()
    doc = _build(root, [merged])
    assert doc["h2"]["comparison"]["verdict"] == REFUSAL_MIXED_ERA, doc["h2"]["comparison"]
    assert doc["h2"]["per_arm"] == []
    assert doc["tvs"] == "UNDEFINED"
    md = G.render_markdown(doc)
    assert "Both limbs, C\u2212A" not in md
    assert "refused_mixed_era" in md


# ---------------------------------------------------------------------------
# (4) the guard must NOT refuse everything: one era still prints its numbers
# ---------------------------------------------------------------------------
def test_single_era_still_prints_its_numbers(tmp_path):
    root = str(tmp_path)
    cells = [
        Cell(root, "rows-cell-pointer-stable-r1",
             _turn_rows("pointer-stable", 60, FIXTURE_V8, "LR-01.v8", rep=1, prompt_base=9000),
             ["h1", "h2"]),
        Cell(root, "rows-cell-pointer-stable-r2",
             _turn_rows("pointer-stable", 60, FIXTURE_V8, "LR-01.v8", rep=2, prompt_base=9000),
             ["h1", "h2"]),
        Cell(root, "rows-cell-transcript-grow-r1",
             _turn_rows("transcript-grow", 60, FIXTURE_V8, "LR-01.v8", rep=1, prompt_base=1000),
             ["h1", "h2"]),
        Cell(root, "rows-cell-transcript-grow-r2",
             _turn_rows("transcript-grow", 60, FIXTURE_V8, "LR-01.v8", rep=2, prompt_base=1000),
             ["h1", "h2"]),
    ]
    doc = _build(root, cells)
    assert doc["h2"]["comparison"]["verdict"] != REFUSAL_MIXED_ERA
    assert doc["h2"]["per_arm"], "a single-era report still shows its per-arm means"
    for row in doc["h2"]["per_arm"]:
        assert row["n"] == 120 and row["cached_inclusive_tokens_per_turn"] is not None
    assert not _mixed_kinds(doc)
    md = G.render_markdown(doc)
    assert "Both limbs, C\u2212A" in md, "the licensed single-era ratio must still print"


# ---------------------------------------------------------------------------
# (5) mixed input: H1 still splits into two grids, each with its own n
# ---------------------------------------------------------------------------
def test_h1_still_splits_and_keeps_each_grids_own_n(tmp_path):
    root = str(tmp_path)
    doc = _build(root, _two_era_cells(root))
    grids = doc["h1"]["grids"]
    assert len(grids) == 2, "each provenance is its own grid"
    for grid in grids:
        assert grid["provenance"]["fixture_sha256"] in (FIXTURE_V7, FIXTURE_V8)
        assert {a["arm"] for a in grid["arms"]} == {"pointer-stable", "transcript-grow"}
        for arm in grid["arms"]:
            assert arm["n_raw"] == 70, "no grid may inherit the other era's rows"
        assert grid["pooled_disjoint"] is True


# ---------------------------------------------------------------------------
# (6) the refusal names every era present and the cell that introduced it
# ---------------------------------------------------------------------------
def test_refusal_names_each_era_and_its_cell(tmp_path):
    root = str(tmp_path)
    doc = _build(root, _two_era_cells(root))
    rows = _mixed_kinds(doc)
    assert len(rows) >= 2, "one refusal row per provenance present"
    text = " ".join(r["text"] for r in rows)
    assert "rows-cell-pointer-stable-v7" in text and "rows-cell-transcript-grow-v7" in text
    assert "rows-cell-pointer-stable-v8" in text and "rows-cell-transcript-grow-v8" in text
    assert "fixture_sha256" in text and "LR-01.v7" in text and "LR-01.v8" in text
    assert "era_b_tools_on" in text
    md = G.render_markdown(doc)
    assert "rows-cell-pointer-stable-v7" in md and "rows-cell-pointer-stable-v8" in md


# ---------------------------------------------------------------------------
# (7) red->green: neuter the guard, the pooled number returns
# ---------------------------------------------------------------------------
def test_red_neutered_guard_prints_the_pooled_number(tmp_path, monkeypatch):
    root = str(tmp_path)
    monkeypatch.setattr(G, "mixed_provenance", lambda clusters: (True, None))
    doc = _build(root, _two_era_cells(root))
    md = G.render_markdown(doc)
    # the defect this card outlaws, reproduced on demand
    assert "Both limbs, C\u2212A" in md, (
        "with the guard neutralised the pooled H2 ratio is printed again -- this is the "
        "red state the guard turns green")
    assert doc["h2"]["per_arm"], "pooled arm means come back with the guard off"
    assert not _mixed_kinds(doc)

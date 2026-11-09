#!/usr/bin/env python3
"""test_ttft_definition.py - ONE row kind defines per-turn TTFT, on every path.

Run from the workspace root:

    python3 experiments/ptr-engine/longrun/tests/test_ttft_definition.py
    python3 experiments/ptr-engine/longrun/tests/test_ttft_definition.py --red-green

Exit 0 = every GREEN assertion held AND every RED assertion reproduced the
pre-definition behaviour.  Pytest-collectable: every ``test_*`` function is one case.

THE DEFINITION THIS FILE PINS (docs/TTFT-DEFINITION.md)
=======================================================
per-turn TTFT = the TTFT of the turn's own INITIAL request: the
``kind="turn-initial"`` row when present, else the legacy ``kind="turn"`` row with
``definition_fallback: true``.  A ``kind="tool-followup"`` row is a request INSIDE
a turn and is never a turn's latency.

WHY: the operator's metric is p95 TTFT over a long run -- how long the system takes
to START answering each turn.  The last follow-up measures a mid-turn re-query, and
in the legacy files it is mirrored into the ``kind="turn"`` row, so counting it
double-counts the last send and lets a 48-turn cell report a p95 at n=70.

WHAT IS CHECKED
===============
  * the selector picks the initial request whichever direction the two latencies
    point (slow initial / fast follow-up, and the reverse), and the per-turn p50
    differs from the last-follow-up figure by exactly the expected amount;
  * one row per SEND (turn-initial + k follow-ups) still yields one sample per
    turn, with the follow-ups counted as dropped, not merged;
  * legacy rows with no ``send_index``/``turn-initial`` still resolve, and every
    figure from them is labelled ``definition_fallback: true`` with the mirrored
    subset counted;
  * a tools-off cell (one send per turn) is VALUE-IDENTICAL before and after;
  * the arm p50/p95 path and the paired/pairing path use the SAME selector, so the
    definition cannot be half-applied;
  * the n>=60 p95 floor is untouched: a 48-turn per-turn population still refuses;
  * ``definition_violations`` reports a row set the definition cannot select.

Offline: no request is issued and no row file, fixture or report is read; every
cell is built in memory.
"""

from __future__ import annotations

import os
import sys
import traceback

HERE = os.path.dirname(os.path.abspath(__file__))
LONGRUN = os.path.dirname(HERE)
sys.path.insert(0, LONGRUN)

import analyze_stats as A  # noqa: E402

ARM = "pointer-stable"
VERBOSE = "-v" in sys.argv[1:]
CELL = {"fixture_sha256": "f" * 64, "model": "offline-model", "thinking": "off",
        "tools_mode": "on:read_file"}


# --- cells -----------------------------------------------------------------
def _new_contract_cell(n=24, initial_ms=900.0, followup_ms=(100.0, 120.0)):
    """One row per SEND, the post-TURN-ROW-ATTRIBUTION shape (k = len(followup_ms))."""
    rows = []
    for t in range(1, n + 1):
        rows.append({"arm": ARM, "rep": 1, "turn": t, "kind": "turn-initial",
                     "send_index": 0, "ttft_ms": float(initial_ms),
                     "request_sha256": "init-%d" % t})
        for j, ms in enumerate(followup_ms):
            last = (j == len(followup_ms) - 1)
            rows.append({"arm": ARM, "rep": 1, "turn": t,
                         "kind": "turn" if last else "tool-followup",
                         "send_index": j + 1, "ttft_ms": float(ms),
                         "request_sha256": "fu-%d-%d" % (t, j)})
    return rows


def _legacy_cell(n=24, followup_ms=(100.0, 120.0)):
    """A pre-fix tools-on cell: the `turn` row MIRRORS the last follow-up.

    Row order is the writer's own: every follow-up row is appended before the
    turn row, which is exactly what made a first-row-wins pairing pick a
    follow-up.  No `send_index`, no `turn-initial` - the initial request of a
    multi-send turn left no row on disk.
    """
    rows = []
    for t in range(1, n + 1):
        for ms in followup_ms:
            rows.append({"arm": ARM, "rep": 1, "turn": t,
                         "kind": "tool-followup", "ttft_ms": float(ms)})
        rows.append({"arm": ARM, "rep": 1, "turn": t, "kind": "turn",
                     "ttft_ms": float(followup_ms[-1])})
    return rows


def _tools_off_cell(n=24):
    return [{"arm": ARM, "rep": 1, "turn": t, "kind": "turn", "ttft_ms": 100.0 + t}
            for t in range(1, n + 1)]


def _identity_select(rows, meta_out=None):
    """The REVERTED selector: every row is a turn row (the pre-definition behaviour)."""
    sel = [r for r in (rows or ()) if isinstance(r, dict)]
    meta = {"definition": "IDENTITY (reverted)", "definition_fallback": False,
            "dropped_followup": 0, "mirrored_rows": 0, "mode": "reverted",
            "n_selected": len(sel), "n_input": len(sel)}
    if meta_out is not None:
        meta_out.update(meta)
    return sel, meta


def _p50(values):
    point, lo, hi, n = A.quantile_ci(values, 0.50, resamples=2000, seed=A.SEED)
    return point, n


def _arm_values(rows, selector=None):
    rep = A.analyze(rows, resamples=500, provenance={ARM: dict(CELL)},
                    selector=selector)
    return rep, rep["arms"][ARM]["ttft"]["values"]


# --- (a) the selector picks the INITIAL request, whichever direction it lies ---
def test_selector_picks_initial_when_the_initial_is_slow():
    rows = _new_contract_cell(n=24, initial_ms=900.0, followup_ms=(100.0, 120.0))
    selected, meta = A.turn_latency_rows(rows)
    assert len(selected) == 24, len(selected)
    assert [r["kind"] for r in selected] == ["turn-initial"] * 24
    assert meta["dropped_followup"] == 24, meta          # the k-1 earlier rounds
    assert meta["dropped_turn_followup"] == 24, meta     # the last round, kind='turn'
    assert meta["mirrored_rows"] == 0, meta
    assert meta["definition_fallback"] is False, meta
    assert meta["mode"] == "turn-initial", meta
    assert meta["definition"] == A.TTFT_DEFINITION

    rep, per_turn = _arm_values(rows)
    last_followup = [r["ttft_ms"] for r in rows if r["kind"] == "turn"]
    assert per_turn == [900.0] * 24, per_turn[:3]
    p50_turn, n_turn = _p50(per_turn)
    p50_fu, n_fu = _p50(last_followup)
    assert n_turn == n_fu == 24, (n_turn, n_fu)
    # 900 ms initial vs 120 ms last follow-up: the definition moves p50 by 780 ms.
    assert abs((p50_turn - p50_fu) - 780.0) < 1e-9, (p50_turn, p50_fu)
    if VERBOSE:
        print("    slow initial: per-turn p50=%.0f n=%d vs last-followup p50=%.0f n=%d"
              % (p50_turn, n_turn, p50_fu, n_fu))


def test_selector_picks_initial_when_the_initial_is_fast():
    rows = _new_contract_cell(n=24, initial_ms=100.0, followup_ms=(900.0, 950.0))
    selected, meta = A.turn_latency_rows(rows)
    assert len(selected) == 24, len(selected)
    assert meta["explicit_initial_rows"] == 24, meta
    rep, per_turn = _arm_values(rows)
    assert per_turn == [100.0] * 24, per_turn[:3]
    last_followup = [r["ttft_ms"] for r in rows if r["kind"] == "turn"]
    p50_turn, _ = _p50(per_turn)
    p50_fu, _ = _p50(last_followup)
    # The direction reverses (100 vs 950) and the selector does NOT follow it.
    assert abs((p50_turn - p50_fu) + 850.0) < 1e-9, (p50_turn, p50_fu)
    if VERBOSE:
        print("    slow follow-up: per-turn p50=%.0f vs last-followup p50=%.0f"
              % (p50_turn, p50_fu))


def test_one_sample_per_turn_never_per_send():
    rows = _new_contract_cell(n=24, initial_ms=900.0, followup_ms=(100.0, 120.0))
    rep, per_turn = _arm_values(rows)
    arm = rep["arms"][ARM]
    assert arm["ttft"]["input"] == 72, arm["ttft"]["input"]
    assert arm["ttft"]["selected"] == 24, arm["ttft"]["selected"]
    assert len(per_turn) == 24, len(per_turn)
    # The number of ROWS is not the number of TURNS: n is taken from the selector.
    assert arm["p50"]["n"] == 24, arm["p50"]


# --- (b) legacy rows still resolve, and are labelled --------------------------
def test_legacy_cell_resolves_and_says_definition_fallback():
    rows = _legacy_cell(n=24)          # 48 follow-up rows + 24 mirrored turn rows
    selected, meta = A.turn_latency_rows(rows)
    assert len(selected) == 24, len(selected)
    assert [r["kind"] for r in selected] == ["turn"] * 24
    assert meta["definition_fallback"] is True, meta
    assert meta["mirrored_rows"] == 24, meta     # every turn had follow-ups
    assert meta["dropped_followup"] == 48, meta
    assert meta["dropped_turn_followup"] == 0, meta
    assert meta["mode"] == "fallback-turn", meta

    rep, per_turn = _arm_values(rows)
    arm = rep["arms"][ARM]
    assert arm["definition_fallback"] is True
    assert arm["p50"]["n"] == 24, arm["p50"]
    assert per_turn == [120.0] * 24, per_turn[:3]   # the mirrored last follow-up
    assert rep["definition"]["fallback_arms"] == [ARM], rep["definition"]
    if VERBOSE:
        print("    legacy: 24 turns, 48 follow-up rows dropped, mirrored=24, "
              "definition_fallback=true, p50 n=%d" % arm["p50"]["n"])


def test_tools_off_cell_is_value_identical_and_has_no_mirrors():
    rows = _tools_off_cell(n=24)
    raw, _n, _u = A.ttft_values(rows)               # the pre-definition population
    rep, per_turn = _arm_values(rows)
    assert per_turn == raw, (per_turn[:3], raw[:3])
    assert rep["arms"][ARM]["ttft"]["selected"] == 24
    assert rep["arms"][ARM]["ttft"]["definition"]["mirrored_rows"] == 0
    # Labelled as legacy (no send_index proves the row is the turn's initial
    # request) but NOT a mirrored figure: the value cannot have moved.
    assert rep["arms"][ARM]["definition_fallback"] is True


# --- (c) both paths use the SAME selector ------------------------------------
def test_both_paths_share_the_selector():
    a = _legacy_cell(n=24)
    b = _legacy_cell(n=24, followup_ms=(100.0, 130.0))
    pairs, pstats = A.paired_by_turn(a, b)
    # One pair per turn, and the paired row is the TURN row -- not the first row
    # of the turn, which in this file order is a tool-followup.
    assert pstats["formed"] == 24, pstats
    assert pstats["dropped_duplicate"] == 0, pstats
    assert pstats["dropped_followup_a"] == 48, pstats
    assert pstats["definition_fallback_a"] is True, pstats
    assert {ra["kind"] for _k, ra, rb in pairs} == {"turn"}, \
        {ra["kind"] for _k, ra, rb in pairs}
    assert len({k for k, _a, _b in pairs}) == 24

    # The arm path and the values handed to `compare()` are the selector's output.
    rep, per_turn = _arm_values(a)
    assert per_turn == [r["ttft_ms"] for r in A.turn_latency_rows(a)[0]]
    assert rep["arms"][ARM]["ttft"]["definition"]["dropped_followup"] == 48


# --- (d) the floor is untouched ----------------------------------------------
def test_p95_floor_still_refuses_below_60():
    rows = _new_contract_cell(n=48, initial_ms=900.0, followup_ms=(100.0,))
    rep, per_turn = _arm_values(rows)
    arm = rep["arms"][ARM]
    assert len(per_turn) == 48
    assert arm["p50"]["n"] == 48 and "refused" not in arm["p50"], arm["p50"]
    assert "refused" in arm["p95"], arm["p95"]
    assert "minimum n for p95 is 60" in arm["p95"]["refused"], arm["p95"]
    assert A.min_n_for(0.95) == 60


# --- (e) a violating row set is REPORTED, never repaired ---------------------
def test_definition_violations_are_reported():
    assert A.definition_violations(_new_contract_cell()) == []
    assert A.definition_violations(_legacy_cell()) == []   # legacy is selectable

    # A turn whose ONLY turn row is a follow-up send (no turn-initial row): the
    # cell can offer no row that defines the turn's own initial TTFT.
    bad_turn = [{"arm": ARM, "turn": 1, "kind": "turn", "send_index": 2,
                 "ttft_ms": 120.0}]
    found = A.definition_violations(bad_turn)
    assert any("no kind='turn-initial' row" in f for f in found), found

    bad_fu = [{"arm": ARM, "turn": 1, "kind": "tool-followup", "send_index": 0,
               "ttft_ms": 120.0}]
    assert any("send_index=0" in f for f in A.definition_violations(bad_fu))

    dup = [{"arm": ARM, "turn": 1, "kind": "turn"},
           {"arm": ARM, "turn": 1, "kind": "turn"}]
    assert any("two 'turn' rows" in f for f in A.definition_violations(dup))


# --- red->green ---------------------------------------------------------------
def _red_checks():
    """The three discriminating assertions, re-run against the REVERTED selector.

    A red check PASSES here when it reproduces the pre-definition behaviour --
    i.e. when the definition makes a measurable difference.  Nothing on disk is
    edited: the old behaviour is injected through `analyze(selector=...)` and
    `paired_by_turn(select=...)`.
    """
    reds = []

    rows = _new_contract_cell(n=24, initial_ms=900.0, followup_ms=(100.0, 120.0))
    _rep, per_turn = _arm_values(rows, selector=_identity_select)
    p50_identity, n_identity = _p50(per_turn)
    if abs(p50_identity - 120.0) < 25.0 and n_identity == 72:
        reds.append("RED selector reverted: 72 rows -> 72 samples, p50=%.1f ms "
                    "(the 120 ms follow-up), not the 900 ms initial request"
                    % p50_identity)
    else:
        raise AssertionError("red case did not reproduce: p50=%.1f n=%d"
                             % (p50_identity, n_identity))

    a = _legacy_cell(n=24)
    _pairs, pstats = A.paired_by_turn(a, a, select=_identity_select)
    kinds = {r["kind"] for r in a if r["turn"] == 1}
    if pstats["dropped_followup_a"] == 0 and kinds == {"tool-followup", "turn"}:
        reds.append("RED selector reverted: pairing drops 0 follow-up rows, so a "
                    "turn's paired row can be a tool-followup (48 such rows in this "
                    "24-turn cell)")
    else:
        raise AssertionError("red pairing case did not reproduce: %r" % (pstats,))

    rows48 = _new_contract_cell(n=48, initial_ms=900.0, followup_ms=(100.0,))
    _rep48, vals48 = _arm_values(rows48, selector=_identity_select)
    if len(vals48) == 96:
        reds.append("RED selector reverted: a 48-turn cell with k=1 offers 96 "
                    "samples (follow-up rows promoted to turns), which is how a "
                    "48-turn cell published a p95 at n=70")
    else:
        raise AssertionError("red 48-turn case did not reproduce: n=%d" % len(vals48))
    return reds


def _run_all(red_green):
    tests = sorted((name, fn) for name, fn in globals().items()
                   if name.startswith("test_") and callable(fn))
    failures = 0
    for name, fn in tests:
        try:
            fn()
            print("PASS %s" % name)
        except Exception:
            failures += 1
            print("FAIL %s" % name)
            traceback.print_exc()
    print("\ndefinition[%s]: %s" % (A.TTFT_DEFINITION_VERSION, A.TTFT_DEFINITION))
    if red_green:
        try:
            for line in _red_checks():
                print(line)
        except Exception:
            failures += 1
            print("FAIL red-green")
            traceback.print_exc()
    print("\n%d/%d green case(s), %d failure(s)"
          % (len(tests) - failures, len(tests), failures))
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(_run_all("--red-green" in sys.argv[1:]))

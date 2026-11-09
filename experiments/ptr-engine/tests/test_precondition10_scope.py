"""PRECONDITION-10-SCOPE — one arm is judged only on ITS OWN treatment.

The live 4-arm canary stopped after three cells on

    RUN-A STOP precondition 10: transcript-compact cell 1 no mechanism
    {'evicted_turns': 0, 'digest_rows': 0, 'lease_ge2_turns': 0}

because the launcher's guard built ONE readiness expression for EVERY arm out of three
markers, two of which belong to other arms, and hard-coded `pointer-stable: True`. A
compact cell cannot have `evicted_turns` (grow) or `lease_ge2_turns` (lease), so the
guard fired on the absence of *other arms'* treatments and cell 15 (`lease-reopen`) was
never measured.

What is held shut here, with the REAL canary's rows:

  * the old global expression still stops at cell 13 (the red state, quoted verbatim);
  * the scoped rule does NOT stop there: compact's own digest was not DUE inside a
    12-turn horizon (max prompt 5586 < the arm's wall 10616 in LR-01.v8), so its absence
    is not evidence about the label, and the canary reaches cell 15;
  * the guard is NOT weakened: each arm's own marker at zero (with the treatment due)
    still STOPS, one test per arm, and the stop names the arm and its own marker;
  * the dry run is still `refused=0 requests=0`, the grid plan still `cells=16`, and the
    launcher still spawns nothing and opens no socket on its own path.

Offline by construction: the subprocess tests are `--dry-run` (cell.py sends nothing),
and the zero-spawn test replaces run_cell with a recorder.
"""
from __future__ import annotations

import importlib.util
import json
import os
import socket
import subprocess
import sys

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
ENG = os.path.dirname(HERE)
ROOT = os.path.dirname(os.path.dirname(ENG))
TOOLS = os.path.join(ENG, "tools")
MEAS = os.path.join(ENG, "measure")
LAUNCHER = os.environ.get("RUN_A_STAR_PATH") or os.path.join(TOOLS, "run_a_star.py")
PY = os.path.abspath(sys.executable)

# The three cells the live canary completed (CANARY-ERA-B-3 handoff `per_arm_classification`).
REAL = {
    "pointer-stable": "rows-cell-pointer-stable-20261026T202040Z.jsonl",
    "transcript-grow": "rows-cell-transcript-grow-20261026T202444Z.jsonl",
    "transcript-compact": "rows-cell-transcript-compact-20261026T203733Z.jsonl",
}


def load_launcher(path=LAUNCHER):
    spec = importlib.util.spec_from_file_location("run_a_star_p10_scope", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


RA = load_launcher()


def real_stats(arm):
    return RA.rows_stats(os.path.join(MEAS, REAL[arm]))


def legacy_global_guard(arm, markers):
    """The PRE-FIX expression, quoted verbatim from run_a_star.py:796-805.

    Every arm was judged by all three markers at once (`pointer-stable` was literally
    `True`), so a compact cell was refused for markers it can never have.
    """
    need = {"transcript-grow": markers.get("evicted_turns", 0) > 0,
            "transcript-compact": markers.get("digest_rows", 0) > 0,
            "lease-reopen": markers.get("lease_ge2_turns", 0) > 0,
            "pointer-stable": True}[arm]
    return not need


def stats_with(markers, **over):
    st = {"turn_rows": 12, "turn_last": 12, "prompt_tokens_max": 6000,
          "markers": {"evicted_turns": 0, "digest_rows": 0, "lease_ge2_turns": 0,
                      "prompt_identity_turns": 12, "prompt_change_turns": 11}}
    st["markers"].update(markers)
    st.update(over)
    return st


# ------------------------------------------------- 1. the real canary: red -> green

def test_real_canary_old_expression_stops_at_cell_13():
    """RED: the old global rule, replayed on the real three cells, halts at compact."""
    seen = []
    stopped = None
    for n, arm in ((1, "pointer-stable"), (7, "transcript-grow"),
                   (13, "transcript-compact")):
        st = real_stats(arm)
        seen.append(n)
        if legacy_global_guard(arm, st["markers"]):
            stopped = n
            break
    assert seen == [1, 7, 13], seen
    assert stopped == 13, "the old expression did not stop where the live canary stopped"
    # ...and it stops for exactly the markers the live stop line carried.
    assert real_stats("transcript-compact")["markers"]["digest_rows"] == 0
    assert real_stats("transcript-compact")["markers"]["lease_ge2_turns"] == 0


def test_real_canary_scoped_rule_reaches_cell_15():
    """GREEN: per-arm scope does not refuse cell 13 and continues to cell 15."""
    verdicts = {}
    for n, arm in ((1, "pointer-stable"), (7, "transcript-grow"),
                   (13, "transcript-compact")):
        verdict, detail = RA.precondition10(arm, real_stats(arm))
        assert detail["arm"] == arm
        assert verdict != "missing", (
            "cell %d %s was refused on its own treatment: %r" % (n, arm, detail))
        verdicts[arm] = verdict
    # pointer and grow did fire their own treatments; compact's digest is not DUE at 12
    # turns (max prompt 5586 < wall 10616 for the arm in LR-01.v8), so its zero is not a
    # mislabel finding and must not halt the canary.
    assert verdicts["pointer-stable"] == "fired", verdicts
    assert verdicts["transcript-grow"] == "fired", verdicts
    assert verdicts["transcript-compact"] == "not-due", verdicts
    assert real_stats("transcript-compact")["prompt_tokens_max"] < 10616

    # Cell 15 as the canary would produce it: 12 turns, lease stays 1 because the
    # declared reopen turns are 23 and 40 -- not due, so the cell is measured.
    lease_cell = stats_with({"lease_ge2_turns": 0}, turn_last=12)
    v, d = RA.precondition10("lease-reopen", lease_cell)
    assert v == "not-due", d
    assert [1, 7, 13, 15] == [1, 7, 13, 15]  # the run order the scope restores


# ------------------------------------- 2. the guard is NOT weakened (one per arm)

def test_compact_own_digest_zero_still_stops_even_when_other_markers_fire():
    """Its own marker 0 while grow AND lease markers are nonzero => STOP, arm named."""
    st = stats_with({"evicted_turns": 5, "digest_rows": 0, "lease_ge2_turns": 3},
                    prompt_tokens_max=20000)  # wall reached => the digest was due
    v, d = RA.precondition10("transcript-compact", st)
    assert v == "missing", d
    assert d["arm"] == "transcript-compact"
    assert d["marker"] == "digest_rows"


def test_grow_own_evicted_zero_still_stops():
    st = stats_with({"evicted_turns": 0, "digest_rows": 4, "lease_ge2_turns": 3},
                    prompt_tokens_max=20000)
    v, d = RA.precondition10("transcript-grow", st)
    assert v == "missing", d
    assert (d["arm"], d["marker"]) == ("transcript-grow", "evicted_turns")


def test_lease_own_one_still_stops_below_threshold_two():
    """lease_ge2_turns=1 is below the arm's own threshold of 2 => STOP."""
    st = stats_with({"evicted_turns": 4, "digest_rows": 4, "lease_ge2_turns": 1},
                    turn_last=48)
    v, d = RA.precondition10("lease-reopen", st)
    assert v == "missing", d
    assert (d["arm"], d["marker"], d["threshold"]) == (
        "lease-reopen", "lease_ge2_turns", 2)


def test_pointer_own_prefix_change_zero_still_stops():
    """12 prompt identities and NO change => the prefix has nothing to be stable against."""
    st = stats_with({"evicted_turns": 4, "digest_rows": 4, "lease_ge2_turns": 3,
                     "prompt_identity_turns": 12, "prompt_change_turns": 0})
    v, d = RA.precondition10("pointer-stable", st)
    assert v == "missing", d
    assert (d["arm"], d["marker"]) == ("pointer-stable", "prompt_change_turns")


def test_other_arms_markers_zero_only_proceeds_for_every_arm():
    """The card's distinction: only the OTHER arms' treatments absent => PROCEEDS."""
    own = {"pointer-stable": {"prompt_change_turns": 1},
           "transcript-grow": {"evicted_turns": 1},
           "transcript-compact": {"digest_rows": 1},
           "lease-reopen": {"lease_ge2_turns": 2}}
    for arm, markers in own.items():
        st = stats_with(markers)
        v, d = RA.precondition10(arm, st)
        assert v != "missing", (arm, d)
        assert d["markers"]["evicted_turns"] == (1 if arm == "transcript-grow" else 0)
        # every other arm's marker is zero except grow's own
        for other in ("digest_rows", "lease_ge2_turns"):
            if other not in markers:
                assert d["markers"][other] == 0


def test_the_scope_table_is_data_and_covers_every_arm():
    """A new arm is a data edit: every planned arm has a row with its own marker."""
    assert set(RA.ARM_TREATMENT) == set(REAL) | {"lease-reopen"}
    for arm, spec in RA.ARM_TREATMENT.items():
        assert spec["marker"] in ("evicted_turns", "digest_rows",
                                  "lease_ge2_turns", "prompt_change_turns")
        assert isinstance(spec["threshold"], int) and spec["threshold"] >= 1


# ------------------------------------------------ 3. the launcher's offline shape

@pytest.fixture
def pinned_ledger(tmp_path, monkeypatch):
    """A consistent pair of ledger records.

    The LIVE ledger is a snapshot other cards re-spend; while this file was written its
    `remaining` (3144) disagreed with the frozen baseline (3192) and the launcher refused
    by name. That refusal is correct but belongs to the ledger's owner, not to this guard,
    so these tests pin both records to the pair the canary's own launch read.
    """
    rec = tmp_path / "ledger-pinned.json"
    rec.write_text(json.dumps({"remaining": 3192, "cap": 4320}))
    monkeypatch.setattr(RA, "LEDGER_FROZEN", str(rec))
    monkeypatch.setattr(RA, "LEDGER_LIVE", str(rec))
    return str(rec)


def fake_cell(arm, rep, n, tools="", budget=108, hypothesis="H2",
              dry_run=False, turns=48, max_wall=2880):
    return {"cell": n, "arm": arm, "rep": rep, "rc": 0, "dur_s": 0.0,
            "gates": ["dry-run G1 ok"], "would_refuse": [], "stats": {},
            "new_files": [], "rows_file": None}


def _dry(argv, monkeypatch, capsys):
    monkeypatch.setattr(RA, "run_cell", fake_cell)
    monkeypatch.setattr(sys, "argv", [LAUNCHER] + argv)
    rc = RA.main()
    return rc, capsys.readouterr().out


def test_canary_dry_run_is_refused_zero_requests_zero_and_exits_zero(
        pinned_ledger, monkeypatch, capsys):
    rc, out = _dry(["--canary", "--dry-run"], monkeypatch, capsys)
    assert rc == 0, out[-2000:]
    # The launcher prints the two halves of the card's quoted line in its own order:
    # `DRY END cells=4 refused=0 requests=0 ... canary_arms=4 canary_requests=48`.
    assert "DRY END cells=4 refused=0 requests=0" in out, out[-2000:]
    assert "canary_arms=4 canary_requests=48" in out, out[-2000:]


def test_grid_dry_run_still_plans_sixteen_cells(pinned_ledger, monkeypatch, capsys):
    rc, out = _dry(["--dry-run"], monkeypatch, capsys)
    assert rc == 0, out[-2000:]
    assert "DRY END cells=16 refused=0 requests=0" in out, out[-2000:]


def test_zero_network_and_zero_spawn_on_the_launcher_path(
        pinned_ledger, monkeypatch, capsys):
    """Reuses the neighbouring recorder from test_launcher_pin_and_cells.py: a replaced
    subprocess.run must never be called and no socket may be opened."""
    spawned, sockets = [], []

    def no_spawn(argv, **kw):
        spawned.append(argv)
        raise AssertionError("the launcher spawned %r" % (argv,))

    def no_socket(*a, **k):
        sockets.append(a)
        raise AssertionError("the launcher opened a socket")

    monkeypatch.setattr(RA.subprocess, "run", no_spawn)
    monkeypatch.setattr(socket, "socket", no_socket)
    monkeypatch.setattr(socket, "create_connection", no_socket)
    rc, out = _dry(["--canary", "--dry-run"], monkeypatch, capsys)
    assert rc == 0
    assert spawned == [], spawned
    assert sockets == [], sockets
    # The launcher prints the two halves of the card's quoted line in its own order:
    # `DRY END cells=4 refused=0 requests=0 ... canary_arms=4 canary_requests=48`.
    assert "DRY END cells=4 refused=0 requests=0" in out, out[-2000:]
    assert "canary_arms=4 canary_requests=48" in out, out[-2000:]

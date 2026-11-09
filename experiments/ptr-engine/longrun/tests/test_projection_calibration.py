"""PROJECTION-CALIBRATION: a worst case is not a forecast. OFFLINE — zero requests.

    python3 experiments/ptr-engine/longrun/tests/test_projection_calibration.py

WHY: HARNESS-GUARDS projected `turns x --turn-wall-cap` (180 s) against `--max-wall`
(3600 s), so a 48-turn cell "projected" 8,640 s and a 60-turn operator comparison 10,800 s
— both refused before a single request, though the measured live rows run far shorter.
The projection now multiplies by the EXPECTED per-turn wall (default 60 s), or by the p90
of a prior row file when `--projected-from` names one. `--turn-wall-cap` keeps its live
abort meaning and is only printed as the worst case.

  (a) 48 turns at the default 60 s projects 2880 s -> ADMITTED (the change),
  (b) the same cell at --projected-turn-wall 180 projects 8640 s -> exit 8 (the guard),
  (c) --projected-from uses that row file's p90 and the printed line names the file,
  (d) --turn-wall-cap still aborts a LIVE turn at its own value (fake stream), which the
      guards' own test (b) also pins; test_guards.py is re-run separately.

RED before the change: (a) refused with exit 8 (projected_wall=8640s), (c) the flag did
not exist, and (d) passes both before and after — it is the invariant the calibration must
not weaken.
"""

import json
import os
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
LONG = os.path.dirname(HERE)
RUNNER = os.path.join(LONG, "run_longrun.py")
CELL = os.path.join(LONG, "cell.py")
FIXTURE = os.path.join(LONG, "tasks-v5", "runtime-v5", "LR-01.v5.json")
ARM = "transcript-grow"
PY = sys.executable
sys.path.insert(0, LONG)
sys.path.insert(0, HERE)

import test_guards as G  # noqa: E402  (fake server + runner harness, already offline)


def _fake_runner(tmp, would_send=48):
    """A runner that answers --dry-run offline and leaves a marker if invoked for real."""
    marker = os.path.join(tmp, "live-runner-invoked.marker")
    path = os.path.join(tmp, "fake_runner.py")
    with open(path, "w", encoding="utf-8") as fh:
        fh.write("import sys, os\n"
                 "if '--dry-run' in sys.argv:\n"
                 "    print('  would_send_total=%d')\n"
                 "    sys.exit(0)\n"
                 "open(os.environ['CELL_MARKER'], 'w').write(' '.join(sys.argv))\n"
                 "sys.exit(0)\n" % would_send)
    return path, marker


def _projection_run(tmp, turns, extra, name="proj", would_send=None):
    out = os.path.join(tmp, name)
    os.makedirs(out, exist_ok=True)
    # the fake runner's own dry-run count follows --turns, as the real one's does; a
    # caller may price a different count to exercise the runner-priced extras term
    fake, marker = _fake_runner(tmp, would_send=turns if would_send is None
                               else would_send)
    argv = [PY, CELL, "--arm", ARM, "--fixture", FIXTURE,
            "--turns", str(turns), "--reps", "1",
            "--budget", "1000", "--out-dir", out, "--no-cell-handoff",
            # GATE-CHAIN-FIX D2: an absent --hypothesis is refused, so these projection
            # checks must name the claim their cell (n=10 or n=48) would make. H2 needs
            # n >= 1, which they satisfy; declaring it changes no projection number.
            "--hypothesis", "H2"] + list(extra)
    env = dict(os.environ, CELL_RUNNER_PATH=fake, CELL_MARKER=marker)
    proc = subprocess.run(argv, capture_output=True, text=True, cwd=LONG, env=env,
                          timeout=180)
    return proc, marker


def _rows_file(tmp, walls_s, name="rows-prior.jsonl"):
    path = os.path.join(tmp, name)
    with open(path, "w", encoding="utf-8") as fh:
        for i, w in enumerate(walls_s):
            fh.write(json.dumps({"turn": i, "wall_ms": int(w * 1000),
                                 "completion_tokens": 1000}) + "\n")
    return path


def check_a_default_admits_48_turns(tmp):
    proc, marker = _projection_run(tmp, 48, [], "a")
    assert "projected_wall~=2880s" in proc.stdout, proc.stdout[-3000:]
    assert proc.returncode != 8, ("48 turns at the default 60 s must be ADMITTED; got "
                                  "exit %d\n%s" % (proc.returncode, proc.stdout[-3000:]))
    # it got as far as invoking the runner: the projection no longer blocks the cell
    assert os.path.exists(marker), "the runner was never invoked after an admission"
    # RED: at 180 s the identical cell is still refused (check_b) — the change is the
    # multiplier, not a disabled guard.
    if os.path.exists(marker):
        os.remove(marker)
    proc2, marker2 = _projection_run(tmp, 48, ["--projected-turn-wall", "180"], "a-red")
    assert proc2.returncode == 8, proc2.stdout[-3000:]
    assert not os.path.exists(marker2)


def check_b_worst_case_still_refuses(tmp):
    proc, _ = _projection_run(tmp, 48, ["--projected-turn-wall", "180"], "b")
    assert proc.returncode == 8, ("expected exit 8 at 180 s/turn, got %d\n%s\n%s"
                                  % (proc.returncode, proc.stdout[-3000:],
                                     proc.stderr[-2000:]))
    assert "projected_wall~=8640s" in proc.stdout, proc.stdout[-2000:]
    assert "worst case 8640s" in proc.stdout or "cap-per-turn 180" in proc.stdout, \
        proc.stdout[-2000:]
    assert "EXIT 8" in proc.stdout, proc.stdout[-1000:]
    # the live cap is untouched by the projection: still 180 s by default
    assert "--turn-wall-cap" not in proc.stderr or "180" in proc.stdout


def check_c_projected_from_uses_p90(tmp):
    rows = _rows_file(tmp, [10, 20, 30, 40, 50, 60, 70, 80, 90, 100])
    # p90 of 10..100 (linear interpolation) = 91 s
    proc, marker = _projection_run(tmp, 10, ["--projected-from", rows], "c")
    assert "projected_wall~=910s" in proc.stdout, proc.stdout[-3000:]
    assert os.path.basename(rows) in proc.stdout, (
        "the preflight line must name the row file it used: %s" % proc.stdout[-2000:])
    assert "source=p90" in proc.stdout, proc.stdout[-2000:]
    assert proc.returncode != 8, proc.stdout[-3000:]
    assert os.path.exists(marker), proc.stdout[-2000:]
    # a missing / empty file is refused as a bad argument (exit 2), never silently ignored
    missing = os.path.join(tmp, "nope.jsonl")
    proc2, _ = _projection_run(tmp, 10, ["--projected-from", missing], "c-red")
    assert proc2.returncode == 2, (proc2.returncode, proc2.stdout[-2000:],
                                   proc2.stderr[-1500:])
    empty = _rows_file(tmp, [], "empty-prior.jsonl")
    proc3, _ = _projection_run(tmp, 10, ["--projected-from", empty], "c-empty")
    assert proc3.returncode == 2, (proc3.returncode, proc3.stdout[-2000:])
    # a bigger file pushes the SAME cell past --max-wall: 10 x 400 s = 4000 > 3600
    rows2 = _rows_file(tmp, [400] * 10, "rows-slow.jsonl")
    proc4, _ = _projection_run(tmp, 10, ["--projected-from", rows2], "c-slow")
    assert proc4.returncode == 8, (proc4.returncode, proc4.stdout[-2000:])


def check_d_turn_wall_cap_still_aborts_a_live_turn(tmp):
    """The live abort is untouched: the cap's OWN value ends the turn, every time.

    The projection prints `--turn-wall-cap` as the worst case; it must never replace it.
    A never-ending fake stream is aborted at 0.4 s and again at 1.2 s, and each row
    records the wall it actually burned — so the abort follows the cap, not the
    projection's 60 s default.
    """
    with G._Fake() as fake:
        proc, rows, _ = G._run_runner(tmp, fake.url, 1, 2, 0.4, "proj-cap.jsonl")
        assert fake.last_body is not None, "no request reached the fake server"
        assert proc.returncode == 0, (proc.returncode, proc.stderr[-2000:])
        assert len(rows) == 1, rows
        row = rows[0]
        assert row["error"] == "turn_wall_cap", row.get("error")
        assert row["truncated"] is True, row.get("truncated")
        assert row["wall_ms"] >= 400, row.get("wall_ms")
        assert row["max_tokens"] == 4096, row.get("max_tokens")
        # the SAME stream, cap raised to 1.2 s: still aborted, and the row proves the
        # turn ran to the new value rather than to the projection's 60 s
        proc2, rows2, _ = G._run_runner(tmp, fake.url, 1, 2, 1.2, "proj-cap2.jsonl")
        assert proc2.returncode == 0, proc2.stderr[-1500:]
        assert rows2 and rows2[0].get("error") == "turn_wall_cap", rows2
        assert rows2[0]["wall_ms"] >= 1200, rows2[0].get("wall_ms")
        assert rows2[0]["wall_ms"] < 60000, rows2[0].get("wall_ms")


# ------------------------------------------------- G2-BOUND-PRICE: the printed price
def check_terms_with_sources(tmp):
    """The projection is printed as an ADDITION: every term, and the source it came from.

    RED before G2-BOUND-PRICE: one pooled number (`projected_wall~=2880s ...`) and no
    term at all for the fetch follow-up allowance GATE-LEDGER recorded as G2-D6, so a
    reader could not see that G1 bills 53 reservations on a 48-turn cell.
    """
    proc, _ = _projection_run(tmp, 48, [], "terms", would_send=53)
    out = proc.stdout
    assert "PRICE" in out, out[-3000:]
    for term in (
            "fitted estimate 3180 s = turns 48 x 60.0 s/turn",
            "PROJECTION.json:defaults.projected_turn_wall_s_by_mode['absent']",
            "+ runner-priced extras 5 x 60.0 s/turn",
            "would_send_total 53 - turns x reps 48",
            "fetch follow-up allowance ceil(48 x 68/801) = 5 x 60.0 s/turn",
            "FETCH_FOLLOWUP_RATIO in cell.py",
            "all-in estimate 3480 s",
            "HARD CEILING 8640 s = turns 48 x --turn-wall-cap 180 s"):
        assert term in out, "the price is missing the term/source %r:\n%s" % (
            term, out[-3000:])
    # the artefact path is only one of the three sources; a flag and a row file must each
    # name themselves, so an override can never masquerade as a calibrated figure
    proc2, _ = _projection_run(tmp, 12, ["--projected-turn-wall", "45"], "terms-flag")
    assert "source --projected-turn-wall]" in proc2.stdout, proc2.stdout[-2000:]
    rows = _rows_file(tmp, [10] * 10, "rows-terms.jsonl")
    proc3, _ = _projection_run(tmp, 12, ["--projected-from", rows], "terms-p90")
    assert "source --projected-from %s]" % rows in proc3.stdout, proc3.stdout[-2000:]


def check_ceiling_is_printed_and_differs_from_estimate(tmp):
    """`turns x --turn-wall-cap` is the HARD CEILING, printed beside the fitted estimate.

    A test that would pass if the two labels were swapped must fail: the strings below
    bind each label to its own arithmetic, so "HARD CEILING ... x 60.0 s/turn" (the
    swapped shape) is asserted absent.
    """
    proc, _ = _projection_run(tmp, 48, ["--turn-wall-cap", "60"], "ceil60")
    out = proc.stdout
    assert "fitted estimate 2880 s = turns 48 x 60.0 s/turn" in out, out[-3000:]
    assert "HARD CEILING 2880 s = turns 48 x --turn-wall-cap 60 s" in out, out[-3000:]
    assert "HARD CEILING 2880 s = turns 48 x 60.0 s/turn" not in out, (
        "the ceiling label is bound to the estimate's arithmetic:\n%s" % out[-3000:])
    assert "fitted estimate 2880 s = turns 48 x --turn-wall-cap" not in out, (
        "the estimate label is bound to the ceiling's arithmetic:\n%s" % out[-3000:])
    # at the DEFAULT cap the two numbers differ: 48 x 180 = 8,640 s bound vs 2,880 s fit
    proc2, _ = _projection_run(tmp, 48, [], "ceil180")
    out2 = proc2.stdout
    assert "HARD CEILING 8640 s = turns 48 x --turn-wall-cap 180 s" in out2, out2[-3000:]
    assert "fitted estimate 2880 s" in out2, out2[-3000:]


def check_thinking_off_keeps_60s_per_turn(tmp):
    """`--thinking off` with no override prices 60.0 s/turn and names the artefact key.

    A mutant that lowers the calibrated off figure to 30 s fails the first assertion.
    """
    proc, _ = _projection_run(tmp, 12, ["--thinking", "off"], "off60")
    out = proc.stdout
    assert "turns 12 x 60.0 s/turn" in out, out[-3000:]
    assert "projected_turn_wall_s_by_mode['off']" in out, out[-3000:]
    assert "projected-turn-wall=60.0" in out, out[-3000:]
    assert "OVERRIDE" not in out, "an un-overridden off cell printed an override:\n%s" % out[-2000:]


def check_boundary_is_exact(tmp):
    """projected == max_wall is ADMITTED; projected == max_wall + 1 is REFUSED."""
    proc, marker = _projection_run(tmp, 1, ["--max-wall", "60"], "b-exact")
    assert "projected_wall~=60s" in proc.stdout, proc.stdout[-3000:]
    assert proc.returncode != 8, ("projected 60 s == --max-wall 60 s must be admitted, "
                                  "got %d\n%s" % (proc.returncode, proc.stdout[-3000:]))
    assert os.path.exists(marker), "the runner was never invoked after a boundary allow"
    os.remove(marker)
    proc2, _ = _projection_run(tmp, 1, ["--max-wall", "59"], "b-over")
    assert proc2.returncode == 8, ("projected 60 s == --max-wall 59 s + 1 must be "
                                   "refused, got %d\n%s"
                                   % (proc2.returncode, proc2.stdout[-3000:]))
    assert not os.path.exists(marker), "the runner was invoked past a 1 s refusal"


CHECKS = [
    ("a", "48 turns x 60 s -> 2880 s -> admitted (calibrated default)", check_a_default_admits_48_turns),
    ("b", "48 turns x 180 s -> 8640 s -> exit 8 (guard intact)", check_b_worst_case_still_refuses),
    ("c", "--projected-from uses the file's p90 and names the file", check_c_projected_from_uses_p90),
    ("d", "--turn-wall-cap still aborts a live turn", check_d_turn_wall_cap_still_aborts_a_live_turn),
    ("e", "price: every term and its source is printed", check_terms_with_sources),
    ("f", "hard ceiling printed beside (and labelled apart from) the fitted estimate",
     check_ceiling_is_printed_and_differs_from_estimate),
    ("g", "--thinking off keeps its calibrated 60.0 s/turn", check_thinking_off_keeps_60s_per_turn),
    ("h", "projected == max-wall admits, projected == max-wall + 1 refuses", check_boundary_is_exact),
]


def main():
    failures = 0
    for name, desc, fn in CHECKS:
        tmp = tempfile.mkdtemp(prefix="projcal-%s-" % name)
        try:
            fn(tmp)
        except Exception as exc:  # noqa: BLE001 — a check either passes or reports why
            failures += 1
            print("FAIL (%s) %s\n      %s: %s" % (name, desc, type(exc).__name__, exc))
        else:
            print("ok   (%s) %s" % (name, desc))
    print("%d/%d projection-calibration checks passed" % (len(CHECKS) - failures,
                                                          len(CHECKS)))
    return 1 if failures else 0


def test_projection_calibration_all():
    assert main() == 0


# The G2-BOUND-PRICE names, executable one by one (pytest collects these).
def test_projection_prints_terms_with_sources():
    with tempfile.TemporaryDirectory() as tmp:
        check_terms_with_sources(tmp)


def test_ceiling_is_printed_and_differs_from_estimate():
    with tempfile.TemporaryDirectory() as tmp:
        check_ceiling_is_printed_and_differs_from_estimate(tmp)


def test_thinking_off_keeps_60s_per_turn():
    with tempfile.TemporaryDirectory() as tmp:
        check_thinking_off_keeps_60s_per_turn(tmp)


def test_boundary_is_exact():
    with tempfile.TemporaryDirectory() as tmp:
        check_boundary_is_exact(tmp)


if __name__ == "__main__":
    sys.exit(main())

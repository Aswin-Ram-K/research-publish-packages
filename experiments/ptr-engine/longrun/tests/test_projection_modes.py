"""PROJECTION-MODE: the projection must refuse in the UNSAFE direction, per mode.

OFFLINE — zero inference requests. The runner is a stub; the ledger is a fixture; every
number comes from experiments/ptr-engine/measure/PROJECTION.json.

WHY: `--projected-from` defaulted to None and no non-test caller passed it, so a single
pooled 60 s/turn priced every cell. For thinking off that is safe (measured p50 2.9 s,
≈20x over-projection). For thinking auto/on it is unsafe: a 60-turn cell projected
3,600 s and was ADMITTED at --max-wall 3600 against a measured p50 of 13,092 s (3.6x) and
p90 of 40,962 s (11.4x). This module pins the mode-specific figure, the refusal for a mode
the artefact cannot price, the loud 180 s override, and the boundary.

Run: .venv/bin/python -m pytest experiments/ptr-engine/longrun/tests/test_projection_modes.py -q
"""

import glob
import json
import os
import subprocess
import sys
import tempfile

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
LONG = os.path.dirname(HERE)
# CELL_PATH lets the red->green demonstration run this suite against a NEUTERED copy of
# cell.py (the mode lookup forced back to the pooled default) without editing this file.
CELL = os.environ.get("CELL_PATH") or os.path.join(LONG, "cell.py")
PROJECTION = os.path.join(os.path.dirname(LONG), "measure", "PROJECTION.json")
FIXTURE = os.path.join(LONG, "tasks-v5", "runtime-v5", "LR-01.v5.json")
ARM = "transcript-grow"
PY = sys.executable
sys.path.insert(0, HERE)

import test_cell_gates as G  # noqa: E402  (offline ledger/runner/env fixtures)

DEFAULTS = json.load(open(PROJECTION, encoding="utf-8"))["defaults"]


# ------------------------------------------------------------------------ helpers
_ENVS = [0]


def _fake_runner(tmp, would_send, tag):
    """A stub whose offline dry-run reports the cell's OWN request count."""
    marker = os.path.join(tmp, "runner-invoked-%s.marker" % tag)
    path = os.path.join(tmp, "fake_runner-%s.py" % tag)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write("import os, sys\n"
                 "if '--dry-run' in sys.argv:\n"
                 "    print('  would_send_total=%d')\n"
                 "    sys.exit(0)\n"
                 "open(os.environ['CELL_MARKER'], 'w').write(' '.join(sys.argv))\n"
                 "sys.exit(0)\n" % would_send)
    return path, marker


def _env(tmp, projection=None, would_send=48):
    _ENVS[0] += 1
    ledger, _rows = G._fake_ledger(tmp, cap=4320, spent=0)
    runner, marker = _fake_runner(tmp, would_send, "%d-%d" % (_ENVS[0], would_send))
    env = G._env(tmp, ledger, runner, marker, projection=projection)
    env["CELL_RUNNER_PATH"] = runner
    env["CELL_MARKER"] = marker
    return env, marker


def _env_for(tmp, turns, projection=None):
    """Env whose runner reports ``turns`` requests: the projection's multiplier input."""
    return _env(tmp, projection=projection, would_send=turns)


def _cell(tmp, turns, extra, env, name="cell"):
    out = os.path.join(tmp, "out-" + name)
    os.makedirs(out, exist_ok=True)
    argv = [PY, CELL, "--arm", ARM, "--fixture", FIXTURE, "--turns", str(turns),
            "--reps", "1", "--budget", "1000", "--out-dir", out,
            "--no-cell-handoff",
            # GATE-CHAIN-FIX D2: an absent --hypothesis is refused, so this projection
            # probe must name the claim its cell (n=10..60) would make (H2 needs n >= 1).
            "--hypothesis", "H2"] + list(extra)
    proc = subprocess.run(argv, capture_output=True, text=True, env=env, cwd=LONG,
                          timeout=180)
    return proc, out


def _text(proc):
    return (proc.stdout or "") + (proc.stderr or "")


# ------------------------------------------------------- the card's reason to exist
def test_thinking_auto_60_turns_refused_at_3600():
    """THE case the pooled default wrongly admitted: 60 turns x 218.2 s = 13,092 s."""
    with tempfile.TemporaryDirectory() as tmp:
        env, marker = _env_for(tmp, 60)
        proc, _out = _cell(tmp, 60, ["--thinking", "auto", "--max-wall", "3600"], env)
        text = _text(proc)
        assert proc.returncode == 8, "expected exit 8, got %d\n%s" % (
            proc.returncode, text[-3000:])
        assert "projected-turn-wall=218.2" in text, text[-3000:]
        assert "thinking=auto" in text, text[-3000:]
        assert "projected_wall~=13092s" in text, text[-3000:]
        assert "G2 projection REFUSED" in text, text[-3000:]
        # the refusal surface still carries its five fields
        assert "computed 13092 s" in text and "limit 3600 s" in text
        assert "PROJECTION.json" in text and "--thinking" in text
        assert not os.path.exists(marker), "the runner was invoked past a G2 refusal"


def test_thinking_off_60_turns_still_admitted_at_3600():
    """The safe over-projection must not become a false refusal (60 x 60 = 3600)."""
    with tempfile.TemporaryDirectory() as tmp:
        env, marker = _env_for(tmp, 60)
        proc, _out = _cell(tmp, 60, ["--thinking", "off"], env, "off")
        assert proc.returncode != 8, _text(proc)[-3000:]
        assert "projected_wall~=3600s" in _text(proc), _text(proc)[-2000:]
        # absent (no --thinking) is the artefact's off/absent group, and the runner's
        # own default is off: it must be priced and run off, not into a refusal
        env2, marker2 = _env_for(tmp, 60, PROJECTION)
        proc2, _o2 = _cell(tmp, 60, [], env2, "absent")
        assert proc2.returncode != 8, _text(proc2)[-3000:]
        assert "thinking=absent" in _text(proc2), _text(proc2)[-2000:]
        assert os.path.exists(marker2), "an off/absent 60-turn cell must reach the runner"


def test_unknown_mode_refuses_exit_8_and_names_the_spellings():
    with tempfile.TemporaryDirectory() as tmp:
        env, marker = _env_for(tmp, 12)
        proc, _out = _cell(tmp, 12, ["--thinking", "thinking-auto"], env)
        text = _text(proc)
        assert proc.returncode == 8, "expected exit 8, got %d\n%s" % (
            proc.returncode, text[-3000:])
        assert "thinking mode='thinking-auto'" in text, text[-3000:]
        assert "mode in one of {absent, auto, off, on}" in text, text[-3000:]
        assert not os.path.exists(marker), "the runner was invoked with an unpriced mode"
        # an explicit override does NOT buy an unpriced mode a pass
        proc2, _o2 = _cell(tmp, 12, ["--thinking", "nope",
                                     "--projected-turn-wall", "1"], env, "nope2")
        assert proc2.returncode == 8, _text(proc2)[-2000:]


def test_mode_missing_from_the_artefact_refuses_rather_than_guessing():
    with tempfile.TemporaryDirectory() as tmp:
        doc = json.load(open(PROJECTION, encoding="utf-8"))
        for key in ("projected_turn_wall_s_by_mode", "projected_turn_wall_s_p90_by_mode"):
            doc["defaults"][key].pop("on", None)
        fake = os.path.join(tmp, "PROJECTION-no-on.json")
        json.dump(doc, open(fake, "w", encoding="utf-8"))
        env, marker = _env_for(tmp, 12, fake)
        proc, _out = _cell(tmp, 12, ["--thinking", "on"], env)
        text = _text(proc)
        assert proc.returncode == 8, text[-3000:]
        assert "not a calibrated mode" in text or "no calibrated per-turn wall" in text, \
            text[-3000:]
        assert "mode in one of {absent, auto, off}" in text, text[-3000:]
        assert not os.path.exists(marker)
        # a mode present for p50 but MISSING from the p90 table also refuses (exit 8):
        # --projected-from p90 must not fall back to the p50 figure
        doc2 = json.load(open(PROJECTION, encoding="utf-8"))
        doc2["defaults"]["projected_turn_wall_s_p90_by_mode"].pop("on", None)
        fake2 = os.path.join(tmp, "PROJECTION-no-on-p90.json")
        json.dump(doc2, open(fake2, "w", encoding="utf-8"))
        env2, marker2 = _env_for(tmp, 12, fake2)
        proc2, _o2 = _cell(tmp, 12, ["--thinking", "on", "--projected-from", "p90"],
                           env2, "no-on-p90")
        text2 = _text(proc2)
        assert proc2.returncode == 8, text2[-3000:]
        assert "no calibrated per-turn wall" in text2, text2[-3000:]
        assert "mode in one of {absent, auto, off}" in text2, text2[-3000:]
        assert not os.path.exists(marker2)


# ------------------------------------------------------- task 3: the 180 s regression
def test_projected_turn_wall_180_is_loud_not_silent():
    with tempfile.TemporaryDirectory() as tmp:
        env, marker = _env_for(tmp, 60)
        # auto: 180 s is BELOW the measured p50, the pre-repair worst case — at 60 turns
        # it projects 10,800 s and is still refused, but the override is now visible
        proc, _out = _cell(tmp, 60, ["--thinking", "auto", "--projected-turn-wall", "180"],
                           env, "loud")
        text = _text(proc)
        assert proc.returncode == 8, text[-3000:]
        assert "OVERRIDE" in text and "BELOW the measured p50" in text, text[-3000:]
        assert "projected_wall~=10800s" in text, text[-3000:]
        assert not os.path.exists(marker)
        # off: 180 s is a conservative override and the cell is admitted — the override
        # is recorded in the gate manifest, which is what makes it auditable
        env2, marker2 = _env_for(tmp, 20, PROJECTION)
        proc2, out2 = _cell(tmp, 20, ["--thinking", "off", "--projected-turn-wall", "180"],
                            env2, "manifest")
        assert proc2.returncode != 8, _text(proc2)[-3000:]
        assert os.path.exists(marker2)
        manifests = glob.glob(os.path.join(out2, "cell-*.gates.json"))
        assert manifests, "no gate manifest was written"
        doc = json.load(open(manifests[0], encoding="utf-8"))
        ov = doc.get("projection_override")
        assert ov is not None, "the override did not reach the manifest"
        assert ov["value"] == 180.0 and ov["reason_required"] is True
        assert ov["direction"] == "conservative", ov
        g2 = [v for v in doc["verdicts"] if v["gate"] == "G2"][0]
        assert g2["thinking_mode"] == "off"


# ------------------------------------------------------------------ boundary ±1 s
def test_boundary_is_exact_at_plus_or_minus_one_second():
    with tempfile.TemporaryDirectory() as tmp:
        env, marker = _env_for(tmp, 60)
        proc0, _o = _cell(tmp, 60, ["--thinking", "off", "--projected-turn-wall", "60"],
                          env, "eq")
        assert proc0.returncode != 8 and "projected_wall~=3600s" in _text(proc0), \
            _text(proc0)[-2000:]
        env1, m1 = _env_for(tmp, 60, PROJECTION)
        proc1, _o = _cell(tmp, 60, ["--thinking", "off",
                                    "--projected-turn-wall", "59.98"], env1, "under")
        assert proc1.returncode != 8 and "projected_wall~=3599s" in _text(proc1), \
            _text(proc1)[-2000:]
        env2, m2 = _env_for(tmp, 60, PROJECTION)
        proc2, _o = _cell(tmp, 60, ["--thinking", "off",
                                    "--projected-turn-wall", "60.02"], env2, "over")
        assert proc2.returncode == 8, _text(proc2)[-2000:]
        assert "projected_wall~=3601s" in _text(proc2), _text(proc2)[-2000:]
        assert not os.path.exists(m2)


# ------------------------------------------------------------- p90 selector + keys
def test_projected_from_p90_uses_the_modes_measured_tail():
    with tempfile.TemporaryDirectory() as tmp:
        env, _m = _env_for(tmp, 60)
        proc, _o = _cell(tmp, 60, ["--thinking", "auto", "--projected-from", "p90"], env,
                         "p90-auto")
        text = _text(proc)
        assert proc.returncode == 8, text[-3000:]
        assert "source=p90-default" in text and "projected_wall~=40962s" in text, \
            text[-3000:]
        env2, m2 = _env_for(tmp, 10, PROJECTION)
        proc2, _o2 = _cell(tmp, 10, ["--thinking", "off", "--projected-from", "p90"],
                           env2, "p90-off")
        assert proc2.returncode != 8, _text(proc2)[-2000:]
        assert "projected_wall~=381s" in _text(proc2), _text(proc2)[-2000:]
        assert os.path.exists(m2)


def test_artefact_carries_per_mode_keys_and_keeps_the_legacy_one():
    table = DEFAULTS["projected_turn_wall_s_by_mode"]
    p90 = DEFAULTS["projected_turn_wall_s_p90_by_mode"]
    assert set(table) >= {"absent", "off", "auto", "on"}
    assert set(p90) >= {"absent", "off", "auto", "on"}
    # the safe direction is an invariant: the off/absent default never sits below the
    # measured off tail (38.1 s), so an off cell is over-projected, never under
    assert table["off"] >= DEFAULTS["measured_p90_s_by_mode"]["off"]
    # the auto default is the measured p50 of the on/auto group, not the pooled scalar
    assert table["auto"] == pytest.approx(218.2)
    assert p90["auto"] == pytest.approx(682.7)
    # the legacy pooled key stays readable for one release and says it is no longer read
    assert DEFAULTS["projected_turn_wall_s"] == 60.0
    assert "LEGACY" in DEFAULTS["projected_turn_wall_s_status"]

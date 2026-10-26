"""RELEASE-SERVING red->green: every serving check must fail when its property is reverted.

A agreement test on a green artefact proves nothing on its own — this file reverts one property
at a time and asserts the SPECIFIC check that guards it goes red, while the artefact as shipped
stays green. `tools/release_serving_check.py --strict` is the green half; this is the red half.
"""
from __future__ import annotations

import copy
import importlib.util
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOOL = ROOT / "tools" / "release_serving_check.py"


def _load():
    spec = importlib.util.spec_from_file_location("release_serving_check", TOOL)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


MOD = _load()


def _record(setup: str) -> dict:
    return json.loads((ROOT / "state" / "config" / f"launch-{setup}.json").read_text())


def _best() -> dict:
    return json.loads((ROOT / "state" / "config" / "best-config.json").read_text())


def _release() -> dict:
    return json.loads((ROOT / "docs" / "prompt-system" / "RELEASE-v1.json").read_text())


def _check(name: str, rec: dict, setup: str) -> bool:
    """Run one check in isolation and return its verdict."""
    checks: list[tuple[str, bool, str]] = []
    best, rel = _best(), _release()
    if name == "IDENTITY":
        MOD.check_identity(rec, best, setup, checks)
    elif name == "ARGV":
        MOD.check_argv_identical(rec, best, setup, checks)
    elif name == "RELEASE":
        MOD.check_release_numbers(rec, rel, setup, checks)
    elif name == "COMMAND":
        MOD.check_command(rec, checks)
    elif name == "DIVERGENCE":
        MOD.check_divergence(rec, checks)
    elif name == "LAUNCHABLE":
        MOD.check_launchable(rec, checks)
    elif name == "NO_NULL":
        MOD.check_no_null(rec, checks)
    elif name == "NO_INVENT":
        MOD.check_no_invent(rec, checks)
    elif name == "V0_REDERIVED":
        MOD.check_v0_rederivable(rec, checks)
    else:
        raise AssertionError(name)
    assert checks and checks[0][0] == name, checks
    return checks[0][1]


# ---------------------------------------------------------------- the guard is green as shipped
def test_tool_is_green_as_shipped():
    r = subprocess.run([sys.executable, str(TOOL), "--strict"], capture_output=True, text=True, cwd=ROOT)
    assert r.returncode == 0, r.stdout + r.stderr
    assert "SERVING checks: 22 run, 0 failed" in r.stdout, r.stdout
    assert "CHECK serving launchable: True" in r.stdout


# ---------------------------------------------------------------- each property, reverted
def test_identity_fails_when_config_sha_drifts():
    rec = _record("O1")
    assert _check("IDENTITY", rec, "O1")
    rec["config_sha256"] = "0" * 64
    assert not _check("IDENTITY", rec, "O1")


def test_identity_fails_when_model_name_drifts():
    rec = _record("O4")
    rec["model"]["served_name"] = "qwen3.5-9b-instruct"
    assert not _check("IDENTITY", rec, "O4")


def test_argv_fails_when_one_flag_changes():
    rec = _record("O1")
    assert _check("ARGV", rec, "O1")
    i = rec["argv"].index("--mem-fraction-static")
    rec["argv"][i + 1] = "0.50"  # the documented crash-loop boundary
    assert not _check("ARGV", rec, "O1")


def test_release_fails_when_a_number_is_transcribed_wrong():
    rec = _record("O1")
    assert _check("RELEASE", rec, "O1")
    rec["v0_released"]["unc_per_turn"] = 522.72  # the rounded 'summary_unc', not the measurement
    assert not _check("RELEASE", rec, "O1")


def test_release_fails_when_the_ci_is_dropped():
    rec = _record("O4")
    rec["v0_released"]["t_ci95"] = [1536.25, 1792.45, 0]
    assert not _check("RELEASE", rec, "O4")


def test_command_fails_when_the_launcher_drops_the_argv():
    rec = _record("O4")
    assert _check("COMMAND", rec, "O4")
    rec["command"] = rec["command"][:5]  # a docker run with no server argv at all
    assert not _check("COMMAND", rec, "O4")


def test_command_fails_when_production_cmd_drifts_from_the_command():
    rec = _record("O1")
    assert _check("COMMAND", rec, "O1")
    rec["production_cmd"] = list(rec["production_cmd"])
    rec["production_cmd"][rec["production_cmd"].index("--page-size") + 1] = "64"
    assert not _check("COMMAND", rec, "O1")


def test_divergence_fails_when_a_deviation_is_hidden():
    """The real risk: a record that launches a superset but claims it is the pinned argv."""
    rec = _record("O1")
    assert _check("DIVERGENCE", rec, "O1")
    hidden = [d for d in rec["differs"] if d.get("flag") == "--page-size"]
    assert hidden, "O1 must declare the --page-size divergence"
    rec["differs"] = [d for d in rec["differs"] if d.get("flag") != "--page-size"]
    assert not _check("DIVERGENCE", rec, "O1")


def test_divergence_fails_when_an_absent_flag_is_not_declared():
    rec = _record("O1")
    rec["differs_absent_from_pinned"] = ["--mamba-track-interval"]  # drops seven others
    assert not _check("DIVERGENCE", rec, "O1")


def test_divergence_fails_when_harmless_setup_invents_one():
    rec = _record("O4")
    rec["differs"] = [{"flag": "--page-size", "pinned": 64, "production_cmd": 128}]
    assert not _check("DIVERGENCE", rec, "O4")


def test_launchable_fails_without_a_port():
    rec = _record("O4")
    assert _check("LAUNCHABLE", rec, "O4")
    i = rec["command"].index("--port")
    rec["command"] = rec["command"][:i] + rec["command"][i + 2:]
    assert not _check("LAUNCHABLE", rec, "O4")


def test_launchable_fails_without_a_preflight():
    rec = _record("O1")
    rec["preflight"] = {}
    assert not _check("LAUNCHABLE", rec, "O1")


def test_launchable_fails_with_two_placeholders():
    rec = _record("O4")
    rec["command"] = [t.replace("/model", "<MODEL_DIR>") for t in rec["command"]]
    assert not _check("LAUNCHABLE", rec, "O4")


def test_no_null_fails_when_a_required_position_empties():
    rec = _record("O4")
    assert _check("NO_NULL", rec, "O4")
    rec["serve_at"] = {}
    rec["serves_at"] = {"rewritten": ""}
    assert not _check("NO_NULL", rec, "O4")


def test_no_invent_fails_when_a_measured_number_is_wrong():
    rec = _record("O1")
    assert _check("NO_INVENT", rec, "O1")
    rec["measured"]["unc_per_turn"] = 700.0
    assert not _check("NO_INVENT", rec, "O1")


def test_no_invent_fails_when_the_rows_digest_does_not_match():
    rec = _record("O4")
    rec["measured"]["rows_sha256"] = "f" * 64
    assert not _check("NO_INVENT", rec, "O4")


def test_v0_rederived_fails_when_the_rule_is_z_instead_of_t():
    """A CI that used the normal limit instead of t(70) must be caught, not copied."""
    rec = _record("O1")
    assert _check("V0_REDERIVED", rec, "O1")
    rec["v0_released"]["t_ci95"] = [506.36, 539.08]  # the z=1.96 interval
    assert not _check("V0_REDERIVED", rec, "O1")


def test_v0_rederived_proves_the_t_rule_pins_the_release():
    """The release's own intervals are t(70)=1.994437 to the cent — not t(71), not z."""
    assert round(MOD.t95(71), 6) == 1.994437
    for setup in ("O1", "O4"):
        assert _check("V0_REDERIVED", _record(setup), setup)


def test_record_missing_is_red(tmp_path):
    """RECORD is what stops the release from shipping without a launch line again."""
    checks: list[tuple[str, bool, str]] = []
    assert MOD.check_record(_record("O1"), "O1", checks)
    checks = []
    assert not MOD.check_record(None, "O9", checks)
    assert "MISSING" in checks[0][2]

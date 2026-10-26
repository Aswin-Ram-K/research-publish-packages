"""The highest-value acceptance command in this project: `best_config_build.py --check`.

It must FAIL on a DERIVED mismatch, IGNORE a MEASURED field (an interval backfilled by a
sibling card is not a function of argv), and it must not let an unknown key escape silently.
"""
from __future__ import annotations

import copy
import importlib.util
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "tools" / "best_config_build.py"


def _load():
    spec = importlib.util.spec_from_file_location("best_config_build", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


MOD = _load()


def _built() -> dict:
    return MOD.build()


def _run(tmp_path: Path, mutate, *flags: str) -> subprocess.CompletedProcess:
    doc = copy.deepcopy(_built())
    mutate(doc)
    p = tmp_path / "cfg.json"
    p.write_text(json.dumps(doc, indent=2) + "\n")
    return subprocess.run(
        [sys.executable, str(SCRIPT), "--check", "--config", str(p), *flags],
        capture_output=True, text=True, cwd=ROOT,
        env={"PYTHONDONTWRITEBYTECODE": "1", "PATH": "/usr/bin:/bin"},
    )


def test_derived_mismatch_fails(tmp_path):
    """config_sha256 is a function of argv -> perturbing it must fail and name the field."""
    def mutate(d):
        d["setups"]["O1"]["config_sha256"] = "0" * 64
    r = _run(tmp_path, mutate)
    assert r.returncode == 1, r.stdout
    assert "FAIL O1.config_sha256" in r.stdout
    assert "CHECK setups identical to disk: False" in r.stdout


def test_derived_argv_mismatch_fails(tmp_path):
    def mutate(d):
        d["setups"]["O1"]["argv"] = ["sglang", "serve", "--port", "9999"]
    r = _run(tmp_path, mutate)
    assert r.returncode == 1, r.stdout
    assert "FAIL O1.argv" in r.stdout


def test_measured_fields_ignored_and_printed(tmp_path):
    """A backfilled interval must NOT fail the check, and must be printed as skipped."""
    def mutate(d):
        s = d["setups"]["O1"]
        s["unc_ci"] = [1.0, 2.0]
        s["ci_source"] = "never-invented-by-builder"
        s["n_rows"] = 1
        s["evidence"]["ci_method"] = "t-interval"
    r = _run(tmp_path, mutate)
    assert r.returncode == 0, r.stdout
    assert "CHECK setups identical to disk: True" in r.stdout
    skipped = [ln for ln in r.stdout.splitlines() if ln.startswith("SKIPPED measured fields")][0]
    for f in ("unc_ci", "ci_source", "n_rows", "evidence"):
        assert f in skipped


def test_unknown_key_warns_but_passes_without_strict(tmp_path):
    def mutate(d):
        d["setups"]["O1"]["invented"] = 1
    r = _run(tmp_path, mutate)
    assert r.returncode == 0, r.stdout
    assert "WARN O1.invented" in r.stdout
    assert "CHECK setups identical to disk: True" in r.stdout


def test_unknown_key_fails_with_strict(tmp_path):
    def mutate(d):
        d["setups"]["O1"]["invented"] = 1
    r = _run(tmp_path, mutate, "--strict")
    assert r.returncode == 1, r.stdout
    assert "WARN O1.invented" in r.stdout
    assert "STRICT: unknown key(s) present -> FAIL" in r.stdout


def test_key_sets_are_disjoint_and_cover_disk_config():
    """Every key the builder emits AND every key on disk is classified."""
    assert not (MOD.DERIVED & MOD.MEASURED), MOD.DERIVED & MOD.MEASURED
    disk = json.loads((ROOT / "state" / "config" / "best-config.json").read_text())
    for name, s in list(disk["setups"].items()) + list(_built()["setups"].items()):
        unknown = set(s) - MOD.DERIVED - MOD.MEASURED
        assert not unknown, f"{name}: {sorted(unknown)}"


def test_real_file_is_green_both_modes():
    for flags in (("-check",), ("-check", "-strict")):
        flags = tuple("--" + f.lstrip("-") for f in flags)
        r = subprocess.run([sys.executable, str(SCRIPT), *flags], capture_output=True, text=True,
                           cwd=ROOT, env={"PYTHONDONTWRITEBYTECODE": "1", "PATH": "/usr/bin:/bin"})
        assert r.returncode == 0, r.stdout
        assert "CHECK setups identical to disk: True" in r.stdout

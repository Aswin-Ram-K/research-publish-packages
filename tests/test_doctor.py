"""Offline tests for :mod:`resextract.doctor` (probes are monkeypatched).

Covers: all-green ⇒ exit 0; any core leg down ⇒ exit 2 naming that leg;
docling (optional) down ⇒ still exit 0; JSON output parses and carries per-leg
detail for every leg.
"""

from __future__ import annotations

import json

import pytest

from resextract import cli, doctor

CORE_NAMES = ("Occamy", "SearXNG", "crawl bridge", "graphify")
OPTIONAL_NAMES = ("docling bridge", "renderers", "dashboard port")


def _leg(name: str, klass: str, ok: bool, detail: str) -> dict:
    return {"leg": name, "class": klass, "ok": ok, "detail": detail}


@pytest.fixture()
def all_green(monkeypatch):
    """Patch every probe so no network/subprocess is touched."""
    green = {
        "probe_occamy": _leg("Occamy", "core", True, "model=occamy-1.0; completion HTTP 200 (thinking=off, max_tokens=8, 41 ms)"),
        "probe_searxng": _leg("SearXNG", "core", True, "HTTP 200, results=10"),
        "probe_crawl_bridge": _leg("crawl bridge", "core", True, "HTTP 200, ok=True"),
        "probe_graphify": _leg("graphify", "core", True, "graphify 0.9.80; openai 3.26.1"),
        "probe_docling": _leg("docling bridge", "optional", True, "HTTP 200, ok=True (optional)"),
        "probe_renderers": _leg("renderers", "optional", True, "missing: pdflatex, pandoc, tectonic"),
        "probe_dashboard_port": _leg("dashboard port", "optional", True, "127.0.0.1:8901 free"),
    }
    for attr, value in green.items():
        monkeypatch.setattr(doctor, attr, (lambda v: (lambda: v))(value))
    return green


def test_all_green_exits_zero(all_green):
    report = doctor.run_doctor()
    assert report["exit_code"] == 0
    assert report["ok"] is True
    assert report["core_down"] == [] and report["optional_down"] == []
    assert [l["leg"] for l in report["legs"]] == list(CORE_NAMES + OPTIONAL_NAMES)
    assert cli.main(["doctor"]) == 0


@pytest.mark.parametrize(
    ("probe_attr", "leg_name"),
    [
        ("probe_occamy", "Occamy"),
        ("probe_searxng", "SearXNG"),
        ("probe_crawl_bridge", "crawl bridge"),
        ("probe_graphify", "graphify"),
    ],
)
def test_one_core_leg_down_exits_two_and_names_it(all_green, monkeypatch, probe_attr, leg_name):
    broken = _leg(leg_name, "core", False, "connection refused")
    monkeypatch.setattr(doctor, probe_attr, lambda b=broken: b)
    report = doctor.run_doctor()
    assert report["exit_code"] == 2
    assert report["ok"] is False
    assert report["core_down"] == [leg_name]
    assert leg_name in doctor.format_table(report)
    assert cli.main(["doctor"]) == 2


def test_optional_leg_cannot_fail_the_doctor(all_green, monkeypatch):
    """RED→GREEN guard: an optional leg (docling) being down must not change exit.

    Reverted guard — ``run_doctor`` treating every down leg as fatal, i.e.
    ``"exit_code": 0 if not (core_down + optional_down) else 2``.  Real captured
    output of ``pytest tests/test_journal.py::test_tampering_is_detected_with_first_bad_seq
    tests/test_doctor.py::test_optional_leg_cannot_fail_the_doctor -q`` with that
    guard reverted (full log: ``state/logs/U0.3-redgreen.txt``)::

        ___________________ test_optional_leg_cannot_fail_the_doctor ___________________
        ...
            report = doctor.run_doctor()
        >       assert report["exit_code"] == 0
        E       assert 2 == 0

        tests/test_doctor.py:96: AssertionError
        =========================== short test summary info ============================
        FAILED tests/test_doctor.py::test_optional_leg_cannot_fail_the_doctor - asser...
        2 failed in 0.02s

    Restoring the guard turns this test green (see ``state/logs/U0.3-pytest.txt``).
    """
    monkeypatch.setattr(
        doctor,
        "probe_docling",
        lambda: _leg("docling bridge", "optional", False, "ConnectError: refused (optional)"),
    )
    report = doctor.run_doctor()
    assert report["exit_code"] == 0
    assert report["ok"] is True
    assert report["core_down"] == []
    assert report["optional_down"] == ["docling bridge"]
    assert cli.main(["doctor"]) == 0


def test_renderers_and_dashboard_port_are_optional_not_failures(all_green, monkeypatch):
    monkeypatch.setattr(
        doctor, "probe_renderers", lambda: _leg("renderers", "optional", True, "missing: pdflatex, pandoc, tectonic")
    )
    monkeypatch.setattr(
        doctor, "probe_dashboard_port", lambda: _leg("dashboard port", "optional", False, "8901 in use")
    )
    report = doctor.run_doctor()
    assert report["exit_code"] == 0
    assert report["optional_down"] == ["dashboard port"]


def test_json_output_parses_with_per_leg_detail(all_green, capsys):
    exit_code = cli.main(["doctor", "--json"])
    payload = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert payload["exit_code"] == 0
    assert payload["ok"] is True
    legs = {l["leg"]: l for l in payload["legs"]}
    assert set(legs) == set(CORE_NAMES + OPTIONAL_NAMES)
    assert all(legs[name]["detail"] for name in legs)
    assert legs["Occamy"]["detail"].startswith("model=occamy-1.0")
    assert "0.9.80" in legs["graphify"]["detail"]
    assert "pdflatex" in legs["renderers"]["detail"]
    assert legs["docling bridge"]["class"] == "optional"


def test_probe_exception_is_data_not_a_crash(all_green, monkeypatch):
    def boom():
        raise RuntimeError("probe exploded")

    monkeypatch.setattr(doctor, "probe_searxng", boom)
    report = doctor.run_doctor()
    assert report["exit_code"] == 2
    assert report["core_down"] == ["SearXNG"]  # declared leg name survives a raising probe
    assert "probe exploded" in dict((l["leg"], l["detail"]) for l in report["legs"])["SearXNG"]


def test_human_table_is_fixed_width_and_names_down_legs(all_green, monkeypatch):
    monkeypatch.setattr(doctor, "probe_occamy", lambda: _leg("Occamy", "core", False, "ConnectError: refused"))
    table = doctor.format_table(doctor.run_doctor())
    lines = table.splitlines()
    assert lines[0].startswith("LEG")
    assert lines[0].index("CLASS") == doctor.LEG_WIDTH + 1
    assert lines[0].index("STATUS") == doctor.LEG_WIDTH + doctor.CLASS_WIDTH + 2
    assert "Occamy" in lines[2] and "DOWN" in lines[2]
    assert "CORE DOWN: Occamy" in lines[-1]


def test_venv_tool_does_not_follow_the_python_symlink(tmp_path, monkeypatch):
    """Regression: sys.executable is a venv symlink; resolving it lost .venv/bin/graphify."""
    real_python = tmp_path / "usr" / "bin" / "python3.14"
    real_python.parent.mkdir(parents=True)
    real_python.write_text("#!/bin/sh\n")
    venv_bin = tmp_path / "venv" / "bin"
    venv_bin.mkdir(parents=True)
    (venv_bin / "tool").write_text("#!/bin/sh\n")
    (venv_bin / "python").symlink_to(real_python)

    monkeypatch.setattr(doctor.sys, "executable", str(venv_bin / "python"))
    monkeypatch.setattr(doctor.sys, "prefix", str(tmp_path / "venv"))
    monkeypatch.setattr(doctor.shutil, "which", lambda name: None)

    assert doctor._venv_tool("tool") == str(venv_bin / "tool")
    assert doctor._venv_tool("absent") is None


def test_live_graphify_probe_is_green_in_this_venv():
    """The real probe must find the venv console script (no network involved)."""
    result = doctor.probe_graphify()
    assert result["ok"] is True, result["detail"]
    assert "graphify" in result["detail"] and "openai" in result["detail"]


def test_default_probe_order_and_classes_are_declared():
    """The live probe list must exist with the documented core/optional split."""
    specs = doctor.default_probes()
    assert [name for name, _ in specs] == list(CORE_NAMES + OPTIONAL_NAMES)
    assert [fn.__name__ for _, fn in specs] == [
        "probe_occamy",
        "probe_searxng",
        "probe_crawl_bridge",
        "probe_graphify",
        "probe_docling",
        "probe_renderers",
        "probe_dashboard_port",
    ]
    assert doctor.DEFAULT_ENDPOINTS["occamy_model"] == "occamy-1.0"
    assert doctor.OCCAMY_COMPLETION_TIMEOUT == 30.0 and doctor.HTTP_TIMEOUT == 5.0

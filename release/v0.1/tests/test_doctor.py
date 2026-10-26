"""Offline tests for :mod:`resextract.doctor` (probes are monkeypatched).

Covers: all-green ⇒ exit 0; any core leg down ⇒ exit 2 naming that leg;
docling (optional) down ⇒ still exit 0; JSON output parses and carries per-leg
detail for every leg.

Also covers the **negative memory** added for the control-path stall: a DOWN
Occamy verdict is reused for at most ``negative_ttl_s()`` seconds (no new probe)
and ``run_doctor(force=True)`` always probes afresh.  All time is faked; the
tests never sleep and never touch the network.

Finally, **cost-bound pins and the slow/down classification** (U0.19, repaired by
U0.22): every blocking leg carries a finite per-leg timeout (so no leg is
unbounded) and each of the six non-Occamy legs is attempted exactly once per
fresh call -- they *do* re-probe every call, which is why a DOWN-only memory
cannot reduce their cost.  The bound **value** is unchanged (5.0 s).  What U0.22
changed is the **classification**: a leg whose full probe exceeds its bound while
a cheap liveness check still sees something accepting is ``state="slow"`` (a
visible degraded state, listed in ``core_slow``), never a false DOWN in
``core_down`` -- while a refused connection is still DOWN.  Two U0.19 latency constants (no digits
are restated here) were pinned to U0.19 log files (its ``searxng`` and
``measure`` JSON) that U0.22 confirmed **do not exist**, and are removed rather
than restated as fact; the live samples now cited are verifier V0.21's, in
``orchestration/handoffs/V0.21.json``.
"""

from __future__ import annotations

import json

import httpx
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


# --------------------------------------------------------------------------- #
# Negative memory: the DOWN model endpoint is not re-probed on every call
# --------------------------------------------------------------------------- #


class _FakeResponse:
    def __init__(self, status_code: int, payload: dict | None = None) -> None:
        self.status_code = status_code
        self._payload = payload if payload is not None else {}

    def json(self) -> dict:
        return self._payload


class _FakeOccamyClient:
    """Counting stand-in for ``httpx.Client``: deterministic DOWN/UP, no network.

    Every real HTTP attempt (GET /models and, when up, POST /chat/completions)
    increments ``state["probes"]`` -- so the count below is a *probe* count, not
    a call count.
    """

    def __init__(self, state: dict) -> None:
        self.state = state

    def __enter__(self) -> "_FakeOccamyClient":
        return self

    def __exit__(self, *exc: object) -> bool:
        return False

    def get(self, url: str, **kwargs: object) -> _FakeResponse:
        self.state["probes"] += 1
        if self.state["mode"] == "down":
            raise httpx.ConnectError("Connection refused")
        return _FakeResponse(200, {"data": [{"id": "occamy-1.0"}]})

    def post(self, url: str, **kwargs: object) -> _FakeResponse:
        self.state["probes"] += 1
        if self.state["mode"] == "down":
            raise httpx.ConnectError("Connection refused")
        return _FakeResponse(200, {"id": "chatcmpl-test"})


@pytest.fixture()
def occamy_fake(monkeypatch):
    """The *real* probe_occamy over a counting fake transport, with a fake clock."""
    state = {"mode": "down", "probes": 0, "now": 1000.0}
    monkeypatch.setattr(doctor.httpx, "Client", lambda *a, **k: _FakeOccamyClient(state))
    monkeypatch.setattr(doctor, "_clock", lambda: state["now"])
    monkeypatch.setattr(doctor, "_NEGATIVE_CACHE", {})
    monkeypatch.setattr(doctor, "negative_ttl_s", lambda: 30.0)
    return state


@pytest.fixture()
def others_green(monkeypatch):
    """Stub the six non-Occamy legs: run_doctor stays offline except the fake Occamy."""
    green = {
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


def test_second_call_reuses_cached_down_without_a_new_probe(occamy_fake, others_green):
    """A DOWN Occamy is re-reported from memory inside the TTL — no second probe.

    RED→GREEN guard (a) — cache reuse.  Reverted: ``reuse_down`` returns ``None``
    unconditionally (no memory at all; patch ``REDGREEN-A``).  Real captured
    output of ``pytest tests/test_doctor.py -q`` with that revert in place
    (full log: ``state/logs/U0.17-redgreen.txt``)::

        >       assert still["core_down"] == ["Occamy"], "a remembered DOWN must not silently become UP"
        E       AssertionError: a remembered DOWN must not silently become UP
        E       assert [] == ['Occamy']
        E         
        E         Right contains one more item: 'Occamy'
        E         Use -v to get more diff
        FAILED tests/test_doctor.py::test_second_call_reuses_cached_down_without_a_new_probe
        FAILED tests/test_doctor.py::test_probe_again_after_negative_ttl_expires - As...
        FAILED tests/test_doctor.py::test_cached_down_stays_down_then_recovery_is_seen
        3 failed, 17 passed in 0.54s

    Restoring the memory turns this test green (full log:
    ``state/logs/U0.17-pytest.txt``).
    """
    first = doctor.run_doctor()
    assert first["core_down"] == ["Occamy"]
    assert occamy_fake["probes"] == 1, "the first call must probe for real"

    second = doctor.run_doctor()
    assert second["core_down"] == ["Occamy"]
    assert occamy_fake["probes"] == 1, "a second immediate call must reuse, not re-probe"


def test_probe_again_after_negative_ttl_expires(occamy_fake, others_green):
    """Past the TTL the memory is dropped and a fresh probe happens (faked clock)."""
    doctor.run_doctor()
    assert occamy_fake["probes"] == 1

    occamy_fake["now"] += 29.0
    doctor.run_doctor()
    assert occamy_fake["probes"] == 1, "inside the 30 s bound the result is reused"

    occamy_fake["now"] += 1.5
    doctor.run_doctor()
    assert occamy_fake["probes"] == 2, "past the TTL a fresh probe is forced"


def test_force_bypasses_negative_memory(occamy_fake, others_green):
    """Explicit ``force=True`` always probes, even inside the TTL.

    RED→GREEN guard (b) — force bypass.  Reverted: ``reuse_down`` ignores its
    ``force`` argument and serves the cached DOWN anyway (patch ``REDGREEN-B``).
    Real captured output of ``pytest tests/test_doctor.py -q`` with that revert
    in place (full log: ``state/logs/U0.17-redgreen.txt``)::

        >       assert occamy_fake["probes"] == 2, "force=True must probe even inside the TTL"
        E       AssertionError: force=True must probe even inside the TTL
        E       assert 1 == 2
        FAILED tests/test_doctor.py::test_force_bypasses_negative_memory - AssertionE...
        1 failed, 19 passed in 0.56s

    Restoring the force check turns this test green (full log:
    ``state/logs/U0.17-pytest.txt``).
    """
    doctor.run_doctor()
    assert occamy_fake["probes"] == 1

    forced = doctor.run_doctor(force=True)
    assert occamy_fake["probes"] == 2, "force=True must probe even inside the TTL"
    assert forced["core_down"] == ["Occamy"]

    doctor.probe_occamy(force=True)
    assert occamy_fake["probes"] == 3, "force must reach the probe itself"


def test_cached_down_stays_down_then_recovery_is_seen(occamy_fake, others_green):
    """Directional correctness both ways: down stays down inside the TTL, up after it."""
    down = doctor.run_doctor()
    assert down["core_down"] == ["Occamy"] and down["exit_code"] == 2

    occamy_fake["mode"] = "up"  # the dependency recovers ...
    still = doctor.run_doctor()  # ... but this call is inside the TTL
    assert still["core_down"] == ["Occamy"], "a remembered DOWN must not silently become UP"
    assert still["exit_code"] == 2
    assert occamy_fake["probes"] == 1

    occamy_fake["now"] += 31.0
    recovered = doctor.run_doctor()
    assert recovered["core_down"] == [] and recovered["exit_code"] == 0
    assert occamy_fake["probes"] == 3, "recovery costs one GET + one completion POST"

    doctor.run_doctor()
    assert occamy_fake["probes"] == 5, "an UP verdict is never remembered"


def test_report_verdict_is_unchanged_and_still_lists_seven_legs(occamy_fake, others_green):
    """Fixed expectation: reuse changes *how often* we probe, never *what* we report."""
    report = doctor.run_doctor()
    assert [l["leg"] for l in report["legs"]] == list(CORE_NAMES + OPTIONAL_NAMES)
    assert len(report["legs"]) == 7
    assert report["core_down"] == ["Occamy"]
    assert report["optional_down"] == []
    assert report["exit_code"] == 2 and report["ok"] is False

    occamy = report["legs"][0]
    assert occamy["class"] == "core" and occamy["ok"] is False
    assert occamy["detail"] == "ConnectError: Connection refused"  # no "(cached)" rewrite
    assert "CORE DOWN: Occamy" in doctor.format_table(report)

    reused = doctor.run_doctor()
    assert reused["legs"] == report["legs"], "the reused leg dicts are identical to the probed ones"


def test_negative_ttl_is_configurable_with_a_sane_default(monkeypatch):
    """Default is 30 s; the env var overrides it; the toml key is honoured if present."""
    monkeypatch.delenv(doctor.NEGATIVE_TTL_ENV, raising=False)
    assert doctor.DEFAULT_NEGATIVE_TTL_S == 30.0
    assert doctor.negative_ttl_s() > 0.0  # 30.0 unless config sets [doctor] negative_ttl_s

    monkeypatch.setenv(doctor.NEGATIVE_TTL_ENV, "5")
    assert doctor.negative_ttl_s() == 5.0

    monkeypatch.setenv(doctor.NEGATIVE_TTL_ENV, "0")
    assert doctor.negative_ttl_s() == 0.0

    monkeypatch.setenv(doctor.NEGATIVE_TTL_ENV, "not-a-number")
    assert doctor.negative_ttl_s() > 0.0, "a bad env value falls back, it does not crash"


def test_zero_ttl_disables_reuse(occamy_fake, others_green, monkeypatch):
    """``negative_ttl_s() == 0`` is the documented escape hatch: always probe."""
    monkeypatch.setattr(doctor, "negative_ttl_s", lambda: 0.0)
    doctor.run_doctor()
    doctor.run_doctor()
    assert occamy_fake["probes"] == 2, "ttl 0 must disable the memory entirely"


# --------------------------------------------------------------------------- #
# Cost bound and the slow/down classification: every blocking leg has a finite
# per-leg timeout, the six non-Occamy legs re-probe every call, and a leg that
# exceeds its bound *while still reachable* is reported ``slow``, not DOWN.
# --------------------------------------------------------------------------- #

#: Live SearXNG samples (min / median / max, seconds) recorded by verifier V0.21
#: on this machine: 8/8 direct UP with a 20 s client.  Provenance: the existing
#: ``orchestration/handoffs/V0.21.json``.  U0.19's two latency constants are
#: **removed and not restated**: they were pinned to U0.19's ``searxng``/``measure`` JSON logs,
#: which do not exist (U0.19's handoff carries ``evidence: {}``).  The max here
#: is **above** ``HTTP_TIMEOUT``, so "every live
#: sample is below the bound" is false: the bound cannot be what separates a live
#: service from a dead one -- the classification does.
LIVE_LATENCY_SAMPLES_S = (0.75, 1.7584, 8.232)

#: Worst live sample seen while building U0.22 (fresh ``probe_searxng`` against
#: 127.0.0.1:8080: 3.536 s, HTTP 200), recorded in ``state/logs/U0.22-after.json``.
WORST_SAMPLE_THIS_UNIT_S = 3.536


class _RecordingClient:
    """Captures the ``timeout`` each probe hands to ``httpx.Client`` -- no network."""

    def __init__(self, calls: list, client_timeout: object = None) -> None:
        self.calls = calls
        # httpx applies the *Client-level* timeout to every request unless the
        # call overrides it -- and the legs bound at ``httpx.Client(timeout=...)``
        # construction, not per request.  A recorder that reads only the
        # per-request kwarg therefore sees ``None`` and manufactures a false red.
        self.client_timeout = client_timeout

    def __enter__(self) -> "_RecordingClient":
        return self

    def __exit__(self, *exc: object) -> bool:
        return False

    def _respond(self, url: str) -> _FakeResponse:
        if url.endswith("/models"):
            return _FakeResponse(200, {"data": [{"id": "occamy-1.0"}]})
        if url.endswith("/chat/completions"):
            return _FakeResponse(200, {"id": "chatcmpl-test"})
        if "/search" in url:
            return _FakeResponse(200, {"results": [1, 2, 3]})
        return _FakeResponse(200, {"ok": True})

    def _record(self, method: str, url: str, request_timeout: object) -> None:
        self.calls.append((method, url, request_timeout, self.client_timeout))

    def get(self, url: str, **kwargs: object) -> _FakeResponse:
        self._record("get", url, kwargs.get("timeout"))
        return self._respond(url)

    def post(self, url: str, **kwargs: object) -> _FakeResponse:
        self._record("post", url, kwargs.get("timeout"))
        return self._respond(url)


def test_every_blocking_leg_carries_a_finite_per_leg_timeout(monkeypatch):
    """No leg is unbounded: all four HTTP legs and both graphify subprocesses are capped.

    RED->GREEN guard (a) -- the per-leg bound, applied at ``httpx.Client(...)``
    construction (httpx then applies it to *every* request; the probes pass no
    per-request timeout).  Reverted: the Client-level bound is dropped from
    ``probe_searxng`` (``httpx.Client(timeout=None)``) -- the guard reads the
    effective bound (per-request kwarg, else Client kwarg), finds ``None``, and
    fails.  Real captured output with that revert in place (full log:
    ``state/logs/U0.20-redgreen.txt``)::

        E       AssertionError: get http://127.0.0.1:8080/search passes no per-leg timeout (None): an unbounded leg can dominate every run_doctor call (see state/logs/U0.20-measure.json)
        FAILED tests/test_doctor.py::test_every_blocking_leg_carries_a_finite_per_leg_timeout

    Restoring ``timeout=HTTP_TIMEOUT`` turns it green (full log:
    ``state/logs/U0.20-pytest.txt``).  ``expected`` values are the ones actually
    in force, measured in ``state/logs/U0.20-measure.json``.

    NOTE (U0.20): U0.19's version of this guard recorded only the *per-request*
    timeout and so failed on a tree where every leg was already bounded -- a
    false red.  The invariant is unchanged; only the recorder was repaired.
    """
    calls: list[tuple[str, str, object, object]] = []
    monkeypatch.setattr(
        doctor.httpx, "Client", lambda *a, **k: _RecordingClient(calls, k.get("timeout"))
    )
    monkeypatch.setattr(doctor, "_NEGATIVE_CACHE", {})

    doctor.probe_searxng()
    doctor.probe_crawl_bridge()
    doctor.probe_docling()
    doctor.probe_occamy(force=True)

    assert len(calls) == 5, f"3 plain GETs + Occamy GET + completion POST: {calls}"
    for method, url, request_timeout, client_timeout in calls:
        timeout = request_timeout if request_timeout is not None else client_timeout
        assert isinstance(timeout, (int, float)) and not isinstance(timeout, bool), (
            f"{method} {url} passes no per-leg timeout ({timeout!r}): an unbounded leg "
            "can dominate every run_doctor call (see state/logs/U0.20-measure.json)"
        )
        assert 0 < float(timeout) <= doctor.OCCAMY_COMPLETION_TIMEOUT
        expected = (
            doctor.OCCAMY_COMPLETION_TIMEOUT if url.endswith("/chat/completions") else doctor.HTTP_TIMEOUT
        )
        assert float(timeout) == expected, f"{method} {url} bound {timeout!r} != {expected}"

    procs: list[tuple[list, object]] = []

    class _Proc:
        def __init__(self, out: str) -> None:
            self.returncode = 0
            self.stdout = out
            self.stderr = ""

    def fake_run(cmd, **kwargs):
        procs.append((cmd, kwargs.get("timeout")))
        return _Proc("graphify 0.9.80" if "graphify" in " ".join(cmd) else "3.26.1")

    monkeypatch.setattr(doctor, "_venv_tool", lambda name: "/fake/graphify")
    monkeypatch.setattr(doctor.subprocess, "run", fake_run)
    result = doctor.probe_graphify()

    assert result["ok"] is True and "0.9.80" in result["detail"]
    assert len(procs) == 2, "graphify --version and the openai import are both subprocesses"
    for cmd, timeout in procs:
        assert isinstance(timeout, (int, float)) and 0 < float(timeout) <= doctor.HTTP_TIMEOUT, (
            f"graphify subprocess {cmd} has no per-leg timeout ({timeout!r})"
        )


def test_every_fresh_run_re_attempts_six_legs_and_reuses_only_the_down_one(occamy_fake, monkeypatch):
    """Measurement pin: the six non-Occamy legs are attempted on *every* call.

    This is the fact that bounds the value of any DOWN-only memory: the memory can
    only skip a probe for a leg that reported DOWN, while these six re-probe
    afresh each time (so a *slow-but-alive* leg is paid for every call).
    """
    attempts: dict[str, int] = {}
    green = {
        "probe_searxng": _leg("SearXNG", "core", True, "HTTP 200, results=10"),
        "probe_crawl_bridge": _leg("crawl bridge", "core", True, "HTTP 200, ok=True"),
        "probe_graphify": _leg("graphify", "core", True, "graphify 0.9.80; openai 3.26.1"),
        "probe_docling": _leg("docling bridge", "optional", True, "HTTP 200, ok=True (optional)"),
        "probe_renderers": _leg("renderers", "optional", True, "missing: pdflatex, pandoc, tectonic"),
        "probe_dashboard_port": _leg("dashboard port", "optional", True, "127.0.0.1:8901 free"),
    }
    for attr, value in green.items():
        def stub(v=value, a=attr):
            attempts[a] = attempts.get(a, 0) + 1
            return v

        monkeypatch.setattr(doctor, attr, stub)

    first = doctor.run_doctor()
    assert [l["leg"] for l in first["legs"]] == list(CORE_NAMES + OPTIONAL_NAMES)
    assert first["core_down"] == ["Occamy"] and first["exit_code"] == 2
    assert len(attempts) == 6 and set(attempts.values()) == {1}
    assert occamy_fake["probes"] == 1

    second = doctor.run_doctor()
    assert set(attempts.values()) == {2}, "each of the six legs is attempted again on the next call"
    assert occamy_fake["probes"] == 1, "only the remembered DOWN Occamy skips its probe"
    assert second["core_down"] == ["Occamy"] and second["exit_code"] == 2
    assert len(second["legs"]) == 7


def test_slow_but_alive_leg_stays_up_so_the_bound_is_not_tightened(monkeypatch):
    """Measurement pin: a leg that answers slowly is *alive*, whatever the bound.

    CITATION REPAIR (U0.22; digit literals scrubbed by U0.25): this test used
    to pin two U0.19 latency constants ("slowest UP" and "inferred worst UP") to
    U0.19's ``searxng``
    and ``measure`` JSON logs.  U0.22 confirmed **neither file exists**
    (``orchestration/handoffs/U0.19.json``
    carries ``evidence: {}``), so both numbers are **removed and not restated**.
    The samples now cited are verifier V0.21's
    (``orchestration/handoffs/V0.21.json``): 8/8 UP, min/median/max
    ``0.75 / 1.7584 / 8.232`` s.  The max is **above** ``HTTP_TIMEOUT`` (5.0), so
    the old "every live sample is under the existing 5 s bound" claim is FALSE;
    U0.22's fix is that the bound no longer decides slow-vs-down at all -- a leg
    over the bound that the cheap liveness check still reaches is
    ``state="slow"``, not DOWN.  RED->GREEN guard (a): reverting that
    classification puts the leg back in ``core_down`` and fails
    ``test_reachable_but_slow_leg_is_slow_not_down`` (full log:
    ``state/logs/U0.22-redgreen.txt``).
    """
    elapsed = {"t": 0.0}

    class _SlowClient:
        def __init__(self, *a: object, **k: object) -> None:
            pass

        def __enter__(self) -> "_SlowClient":
            return self

        def __exit__(self, *exc: object) -> bool:
            return False

        def get(self, url: str, **kwargs: object) -> _FakeResponse:
            elapsed["t"] += max(LIVE_LATENCY_SAMPLES_S)
            return _FakeResponse(200, {"results": [1, 2, 3]})

    monkeypatch.setattr(doctor.httpx, "Client", _SlowClient)
    result = doctor.probe_searxng()

    assert result["ok"] is True and result["result_count"] == 3
    assert result["state"] == doctor.UP
    assert elapsed["t"] == max(LIVE_LATENCY_SAMPLES_S)
    assert max(LIVE_LATENCY_SAMPLES_S) > doctor.HTTP_TIMEOUT, (
        "V0.21 measured a live SearXNG sample (8.232 s) ABOVE the 5.0 s bound: the bound alone "
        "cannot separate a live service from a dead one (orchestration/handoffs/V0.21.json)"
    )
    assert WORST_SAMPLE_THIS_UNIT_S < doctor.HTTP_TIMEOUT, (
        "the worst live sample U0.22 itself measured (3.536 s, state/logs/U0.22-after.json) is "
        "inside the unchanged bound"
    )
    assert doctor.HTTP_TIMEOUT == 5.0, "U0.22 changes the classification, never the bound value"


# --------------------------------------------------------------------------- #
# U0.22: slow vs down.  A reachable dependency that misses its bound is SLOW,
# not DOWN; a refused connection is still DOWN (so the fix is not a mask).
# --------------------------------------------------------------------------- #


def _timeout_client(exc: BaseException):
    """An ``httpx.Client`` double whose every request raises ``exc`` (no network)."""

    class _Client:
        def __init__(self, *a: object, **k: object) -> None:
            pass

        def __enter__(self) -> "_Client":
            return self

        def __exit__(self, *e: object) -> bool:
            return False

        def get(self, url: str, **kwargs: object) -> object:
            raise exc

        def post(self, url: str, **kwargs: object) -> object:
            raise exc

    return _Client


def _green_six() -> dict:
    """The six non-SearXNG legs green, so a report isolates the SearXNG leg."""
    return {
        "probe_occamy": _leg("Occamy", "core", True, "model=occamy-1.0; completion HTTP 200"),
        "probe_crawl_bridge": _leg("crawl bridge", "core", True, "HTTP 200, ok=True"),
        "probe_graphify": _leg("graphify", "core", True, "graphify 0.9.80; openai 3.26.1"),
        "probe_docling": _leg("docling bridge", "optional", True, "HTTP 200, ok=True (optional)"),
        "probe_renderers": _leg("renderers", "optional", True, "missing: pdflatex, pandoc, tectonic"),
        "probe_dashboard_port": _leg("dashboard port", "optional", True, "127.0.0.1:8901 free"),
    }


def test_reachable_but_slow_leg_is_slow_not_down(monkeypatch):
    """RED->GREEN guard (a): a leg over its bound but still reachable is not DOWN.

    Before U0.22 this exact situation produced a false DOWN: the reproduction in
    ``state/logs/U0.22-before.json`` (a local accept-and-delay stub, killed in the
    same shell) gave ``SearXNG -> ReadTimeout`` with
    ``core_down == ['Occamy', 'SearXNG']`` and exit 2.  Reverting the
    classification makes ``core_slow`` empty and moves 'SearXNG' back into
    ``core_down``, failing these assertions (full log:
    ``state/logs/U0.22-redgreen.txt``).
    """
    monkeypatch.setattr(doctor, "_NEGATIVE_CACHE", {})
    for attr, value in _green_six().items():
        monkeypatch.setattr(doctor, attr, (lambda v: (lambda: v))(value))
    monkeypatch.setattr(doctor.httpx, "Client", _timeout_client(httpx.ReadTimeout("timed out")))
    monkeypatch.setattr(doctor, "cheap_alive", lambda url, **k: (True, "TCP connect accepted within 0.5s"))

    probe = doctor.probe_searxng()
    assert probe["ok"] is False, "a leg that missed its bound is not proven green"
    assert probe["state"] == doctor.SLOW and probe["slow"] is True
    assert "reachable but slow" in probe["detail"]

    report = doctor.run_doctor()
    assert len(report["legs"]) == 7
    assert report["core_slow"] == ["SearXNG"], "the slow core leg must be VISIBLE, not swallowed"
    assert report["core_down"] == [], "a reachable-but-slow core leg must not be a false DOWN"
    assert report["optional_slow"] == []
    assert report["degraded"] is True
    table = doctor.format_table(report)
    assert "slow" in table and "SearXNG" in table and "CORE SLOW: SearXNG" in table


def test_a_refused_connection_is_still_down(monkeypatch):
    """RED->GREEN guard (b): the slow path must not excuse a dead dependency.

    A **timeout whose cheap liveness check also fails** is DOWN (nothing accepts
    there), and a plain connection-refused is DOWN without consulting the cheap
    check at all.  A fix that greyed out every timeout would pass guard (a) and
    fail this one.
    """
    for attr, value in _green_six().items():
        monkeypatch.setattr(doctor, attr, (lambda v: (lambda: v))(value))
    monkeypatch.setattr(doctor.httpx, "Client", _timeout_client(httpx.ReadTimeout("timed out")))
    monkeypatch.setattr(
        doctor, "cheap_alive", lambda url, **k: (False, "TCP connect failed (ConnectionRefusedError)")
    )
    probe = doctor.probe_searxng()
    assert probe["state"] == doctor.DOWN and probe["ok"] is False
    report = doctor.run_doctor()
    assert report["core_down"] == ["SearXNG"] and report["core_slow"] == []
    assert report["degraded"] is False
    assert report["exit_code"] == 2 and report["ok"] is False

    monkeypatch.setattr(doctor.httpx, "Client", _timeout_client(httpx.ConnectError("Connection refused")))
    refused = doctor.probe_searxng()
    assert refused["state"] == doctor.DOWN, "refused is never 'slow'"
    assert "Connection refused" in refused["detail"]


def test_a_slow_leg_is_never_remembered_as_down(monkeypatch):
    """Only DOWN is remembered (preserved): a transient slow verdict must not stick."""
    monkeypatch.setattr(doctor, "_NEGATIVE_CACHE", {})
    monkeypatch.setattr(doctor.httpx, "Client", _timeout_client(httpx.ReadTimeout("timed out")))
    monkeypatch.setattr(doctor, "cheap_alive", lambda url, **k: (True, "TCP connect accepted"))
    probe = doctor.probe_occamy(force=True)
    assert probe["state"] == doctor.SLOW
    assert doctor.reuse_down(doctor.OCCAMY_CACHE_KEY) is None, (
        "a slow verdict is transient: caching it would make a momentary stall sticky"
    )
    assert doctor._NEGATIVE_CACHE == {}


def test_cheap_liveness_check_is_short_and_reports_refusal(monkeypatch):
    """The cheap check is a bounded TCP connect -- cheap enough to run on a timeout."""
    seen: dict = {}

    class _Sock:
        def settimeout(self, value: float) -> None:
            seen["timeout"] = value

        def connect(self, target: tuple) -> None:
            seen["target"] = target
            raise ConnectionRefusedError(111, "Connection refused")

        def close(self) -> None:
            seen["closed"] = True

    monkeypatch.setattr(doctor.socket, "socket", lambda *a, **k: _Sock())
    alive, how = doctor.cheap_alive("http://127.0.0.1:9/")
    assert alive is False
    assert seen["target"] == ("127.0.0.1", 9)
    assert 0 < seen["timeout"] <= doctor.SLOW_LIVENESS_TIMEOUT
    assert seen["closed"] is True
    assert "refused" in how.lower()
    assert doctor._host_port("https://host.example/v1") == ("host.example", 443)

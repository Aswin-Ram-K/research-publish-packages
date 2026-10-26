"""U6.12 -- the read surface is not anonymous on a non-loopback bind.

Rule (one sentence)
-------------------
A non-loopback bind requires an **operator-chosen** token, and that same token
is then required for **every** route, reads included; loopback keeps anonymous
reads and ``--token auto``.

The exposure this closes, reproduced live *before* the fix from the machine's own
LAN address (not loopback), so it was reachability from off-host that was proved::

    $ .venv/bin/resextract serve --host serving-host --port 8941 --allow-remote --no-browser
    resextract serve: read routes are open on loopback; POST /api/control/* needs the token
    $ curl -s -m 20 -o /dev/null -w '%{http_code}' http://serving-host/api/status
    200
    $ curl -s -m 20 -o /dev/null -w '%{http_code}' http://serving-host/api/dockets
    200
    $ curl -s -m 20 -o /dev/null -w '%{http_code}' http://serving-host/api/graph
    200
    $ curl -s -m 20 -o /dev/null -w '%{http_code}' -X POST http://serving-host/api/control/rescan
    401

An unauthenticated LAN client could read the store summary (``db_path``,
``schema_version`` 4 and every table's row count), the docket list with slugs and
statuses, the journal/reasoning events and the 3 MB graph.

Two red->green guards back this file.  Both were run by reverting the fix,
purging **every** ``__pycache__`` (a narrow purge produced 5 spurious failures
for an earlier verifier) and re-running.

Guard (a) -- read gating.  Revert the ``if remote:`` middleware in
``resextract/dashboard/app.py`` (make it ``if False:``) and
``test_remote_bind_reads_are_refused_without_the_token`` fails because the
unauthenticated non-loopback read succeeds again::

    E           AssertionError: ('/', 200)
    E           assert 200 == 401
    E            +  where 200 = <Response [200 OK]>.status_code
    E       AssertionError: {'db_path': '<workspace>', 'schema_version': 4, 'generated_at': '2026-10-08T12:59:26.888Z', 'tables': {'runs': 4, 'targets': 0, 'candidates': 10, 'claims': 0, ...}, ...}
    E       assert {'candidates'...ated_at', ...} == {'error'}
    E

Guard (b) -- the remote bind needs an operator-chosen token.  Revert the token
requirement in ``cli._resolve_serve`` and ``dashboard/__main__.py`` (both
``if not is_loopback(...)`` checks to ``if False:``) and
``test_remote_bind_rejects_the_auto_token`` fails because a non-loopback bind
starts with no operator-chosen token::

    E       Failed: DID NOT RAISE ValueError
    FAILED tests/test_cli.py::test_remote_bind_rejects_the_auto_token - Failed: D...

The CLI-side halves of both rules live in ``tests/test_cli.py``; this file owns
the dashboard/app half.  ``tests/test_dashboard.py`` is owned by U6.11 and is
deliberately untouched.

U6.15 -- ``--token auto`` means ONE thing on both entry points
--------------------------------------------------------------
``python -m resextract.dashboard --token auto`` had no ``auto`` meaning at all,
so the literal four-character string became the secret of a real remote
listener.  Reproduced live before the fix, start+probe+kill in ONE bash call::

    $ .venv/bin/python -m resextract.dashboard --token auto --host serving-host \
        --allow-remote --port 8971 --store state/logs/U6.15-storecopy.sqlite
    WARNING: binding non-loopback host 'serving-host'; every route now requires the token
    INFO:     Uvicorn running on http://serving-host (Press CTRL+C to quit)
    $ curl -m 15 http://serving-host/                                    -> 401
    $ curl -m 15 -H 'x-dashboard-token: auto' http://serving-host/       -> 200

``auto`` now generates and prints a token on loopback and is refused (exit 2,
nothing bound) on a non-loopback bind, exactly as ``resextract serve`` does; the
literal ``auto`` is never a secret.

Guard (a) -- ``auto`` is never a literal secret.  Revert the ``auto`` handling in
``dashboard/__main__.py`` (make the non-loopback refusal ``if False:``) and
``test_module_auto_on_a_remote_bind_is_refused`` fails because the literal
``auto`` is accepted and the process serves instead of exiting 2::

    E   AssertionError: module bound a listener with --token auto on serving-host:PORT
    FAILED tests/test_dashboard_auth.py::test_module_auto_on_a_remote_bind_is_refused

Guard (b) -- socket-level refusal.  Same revert:
``test_module_auto_on_a_remote_bind_binds_nothing`` fails at the *socket*, not
merely at an argument, because a listener really binds and answers 200 to
``x-dashboard-token: auto``::

    E   AssertionError: module bound a listener with --token auto on serving-host:PORT
    FAILED tests/test_dashboard_auth.py::test_module_auto_on_a_remote_bind_binds_nothing

The existing in-process ``uvicorn.run``-sentinel tests are argument-level reds
(they would pass even if the code went on to bind); guard (b) exists to close
that gap.

U6.17 -- this file never reads the REAL store
---------------------------------------------
Every ``create_app(...)`` here (and ``main([...])`` for the module entry point)
used to fall through to the real ``state/state.sqlite``: no ``store_path`` was
passed, so ``api.DataLayer`` resolved ``resolve_store(None)`` to
``DEFAULT_DB_PATH``.  That made every auth assertion depend on the live store's
contents *and* emitted a pair of SQLite sidecars (``state.sqlite-wal`` 0 B,
``state.sqlite-shm`` 32768 B) -- reproduced by running this file ALONE.  One
module-scoped autouse fixture now aims ``RESEXTRACT_STATE_DB`` (the second rule
in ``resolve_store``'s precedence, U6.16) at a byte copy of the store for the
duration of this module and restores the variable afterwards, so no other test
file can be silently redirected.  The copy is made with ``shutil.copyfile`` --
never by opening the real database, because a ``mode=ro`` open is what creates
those sidecars.  ``test_every_app_resolves_to_the_isolated_copy_not_the_real_store``
asserts the resolved path from ``app.state.dashboard``, so the isolation fails
loudly if it is ever reverted.
"""

from __future__ import annotations

import os
import shutil
import socket
import subprocess
import sys
import urllib.request
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from resextract.dashboard import app as app_mod

TOKEN = "u6-12-operator-chosen-secret"

# The read routes that leak the most data.  The SSE stream, /api/doctor and
# /api/refresh are left out of the loop only because they stream or probe the
# (down) core; they are gated by the very same middleware.
REMOTE_GATED_READS = [
    "/",
    "/api/status",
    "/api/runs",
    "/api/findings",
    "/api/dockets",
    "/api/graph",
]


# --------------------------------------------------------------------------- #
# U6.17 -- never read the REAL store
# --------------------------------------------------------------------------- #
# ``_remote_app`` and every other construction below resolve their store through
# ``create_app -> api.DataLayer -> resolve_store`` (U6.16).  With no explicit
# ``store_path`` the fallback is the real ``state/state.sqlite``, so a per-module
# copy is installed as ``RESEXTRACT_STATE_DB`` -- rule two of that precedence --
# which redirects *every* construction here, including the in-process ``main()``
# calls and the spawned module, leaving no call site to forget.  It is a
# process-global, so it is set and restored by this one autouse fixture rather
# than left behind for another test file.
@pytest.fixture(scope="module", autouse=True)
def isolated_store(tmp_path_factory):
    """Point every app/layer this module builds at a throwaway store copy.

    ``shutil.copyfile`` is a plain byte copy: the original database is never
    opened, which is what keeps this fixture itself from creating the very
    ``-wal``/``-shm`` sidecars the isolation exists to prevent.
    """
    src = Path(app_mod.api.DEFAULT_DB_PATH)
    assert src.is_file(), f"real store missing: {src}"
    dst = tmp_path_factory.mktemp("u6.17-store") / "state-copy.sqlite"
    shutil.copyfile(src, dst)
    assert dst.stat().st_size == src.stat().st_size, (dst.stat().st_size, src.stat().st_size)

    previous = os.environ.get("RESEXTRACT_STATE_DB")
    os.environ["RESEXTRACT_STATE_DB"] = str(dst)
    try:
        yield dst
    finally:  # restored even when a test fails -- no leaked redirect
        if previous is None:
            os.environ.pop("RESEXTRACT_STATE_DB", None)
        else:
            os.environ["RESEXTRACT_STATE_DB"] = previous


def _remote_app(token: str | None = TOKEN):
    return app_mod.create_app(host="0.0.0.0", allow_remote=True, token=token)


def test_remote_bind_reads_are_refused_without_the_token():
    """CENTRAL: no token => 401 off-host; the same read with the token => 200."""
    client = TestClient(_remote_app())
    for route in REMOTE_GATED_READS:
        anon = client.get(route)
        assert anon.status_code == 401, (route, anon.status_code)
        assert "token" in anon.json()["error"], route
        ok = client.get(route, headers={"x-dashboard-token": TOKEN})
        assert ok.status_code == 200, (route, ok.status_code)


def test_remote_401_body_carries_no_data():
    """The gate answers before the handler: no store/docket payload leaks."""
    client = TestClient(_remote_app())
    body = client.get("/api/status").json()
    assert set(body) == {"error"}, body


def test_remote_bind_without_any_token_fails_closed():
    """``create_app(remote, token=None)`` stays constructible (U6.11 pins that)
    but grants nothing: reads answer 401 instead of falling back to open."""
    client = TestClient(_remote_app(token=None))
    for route in REMOTE_GATED_READS:
        assert client.get(route).status_code == 401, route


def test_remote_gate_accepts_a_bearer_header_too():
    client = TestClient(_remote_app())
    headers = {"authorization": f"Bearer {TOKEN}"}
    assert client.get("/api/status", headers=headers).status_code == 200


def test_loopback_reads_stay_anonymous_even_with_a_token_configured():
    """Local UX preserved: on loopback a configured token gates control only."""
    client = TestClient(app_mod.create_app(host="127.0.0.1", token=TOKEN))
    for route in REMOTE_GATED_READS:
        assert client.get(route).status_code == 200, route


def test_loopback_control_routes_are_unchanged():
    """Control routes keep their own gate: 401 anonymous, 200 with the token."""
    client = TestClient(app_mod.create_app(host="127.0.0.1", token=TOKEN))
    assert client.post("/api/control/rescan").status_code == 401
    rescan = client.post("/api/control/rescan", headers={"x-dashboard-token": TOKEN})
    assert rescan.status_code == 200, rescan.text[:200]


@pytest.mark.parametrize("host", ["0.0.0.0", "serving-host"])
def test_bind_decision_is_untouched(host):
    """check_bind_host is still THE single decision: no --allow-remote => refuse."""
    with pytest.raises(ValueError):
        app_mod.create_app(host=host)
    assert app_mod.check_bind_host(host, True) == host


def test_remote_gate_flag_is_exposed_for_operators():
    assert app_mod.create_app(host="0.0.0.0", allow_remote=True, token=TOKEN).state.dashboard[
        "remote_reads_gated"
    ] is True
    local = app_mod.create_app(host="127.0.0.1", token=TOKEN)
    assert local.state.dashboard["remote_reads_gated"] is False


# --------------------------------------------------------------------------- #
# U6.15 -- `--token auto` means one thing on both entry points
# --------------------------------------------------------------------------- #


def _lan_ip() -> str:
    """A real, bindable non-loopback IPv4 address of this machine, else skip.

    The address must be genuinely bindable, not merely non-loopback: guard (b)
    is only meaningful if the red case can really open the socket.
    """
    try:
        out = subprocess.run(
            ["ip", "-4", "-o", "addr", "show", "scope", "global"],
            capture_output=True,
            text=True,
            timeout=10,
        ).stdout
        for line in out.splitlines():
            fields = line.split()
            if len(fields) > 3:
                return fields[3].split("/")[0]
    except (OSError, subprocess.SubprocessError):
        pass
    try:  # routing table's notion of our outbound address; no packet is sent
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            sock.connect(("serving-host", 9))
            ip = str(sock.getsockname()[0])
        if not ip.startswith("127."):
            return ip
    except OSError:
        pass
    pytest.skip("no bindable non-loopback IPv4 address on this host")


def _free_port() -> int:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def _spawn_module_auto(lan: str, port: int) -> subprocess.Popen:
    return subprocess.Popen(
        [
            sys.executable,
            "-m",
            "resextract.dashboard",
            "--token",
            "auto",
            "--host",
            lan,
            "--allow-remote",
            "--port",
            str(port),
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
    )


def test_module_auto_on_a_remote_bind_is_refused():
    """CENTRAL: `auto` is never a literal secret on the module entry point.

    Non-loopback + ``--token auto`` must exit 2 with nothing bound, exactly as
    ``resextract serve`` does -- not start a remote listener whose secret is the
    four characters ``auto``.
    """
    lan, port = _lan_ip(), _free_port()
    proc = _spawn_module_auto(lan, port)
    try:
        try:
            rc = proc.wait(timeout=15)
        except subprocess.TimeoutExpired:
            raise AssertionError(f"module bound a listener with --token auto on {lan}:{port}")
        _out, err = proc.communicate()
        assert rc == 2, (rc, err[-400:])
        assert "explicit --token" in err and "'auto'" in err, err[-400:]
    finally:
        if proc.poll() is None:
            proc.kill()
            proc.wait(timeout=10)


def test_module_auto_on_a_remote_bind_binds_nothing():
    """SOCKET-LEVEL guard: a listener really must not bind on the refusal path.

    The in-process ``uvicorn.run`` sentinel tests are argument-level reds -- they
    would pass even if the code went on to bind.  This starts the real module as
    a subprocess and then proves, over TCP, that nothing answers on the port and
    that no request -- not even one carrying the literal ``auto`` -- gets 200.
    """
    lan, port = _lan_ip(), _free_port()
    proc = _spawn_module_auto(lan, port)
    try:
        try:
            proc.wait(timeout=15)
        except subprocess.TimeoutExpired:
            raise AssertionError(f"module bound a listener with --token auto on {lan}:{port}")
        _out, err = proc.communicate()
        assert proc.returncode == 2, (proc.returncode, err[-400:])
        with pytest.raises(OSError):
            socket.create_connection((lan, port), timeout=5)
        with pytest.raises(OSError):
            urllib.request.urlopen(
                urllib.request.Request(
                    f"http://{lan}:{port}/", headers={"x-dashboard-token": "auto"}
                ),
                timeout=5,
            )
    finally:
        if proc.poll() is None:
            proc.kill()
            proc.wait(timeout=10)


def test_module_auto_on_loopback_generates_and_prints_a_token(monkeypatch, capsys):
    """Loopback ``auto`` is usable: a strong token is generated AND printed."""
    import uvicorn

    from resextract.dashboard.__main__ import main

    calls: list = []
    monkeypatch.setattr(uvicorn, "run", lambda app, **kw: calls.append(app))
    rc = main(["--token", "auto", "--host", "127.0.0.1", "--port", "0"])
    assert rc == 0, rc
    assert len(calls) == 1, calls
    out = capsys.readouterr().out
    assert "control token: " in out, out
    token = out.split("control token: ", 1)[1].strip()
    assert token != "auto", token
    assert len(token) == 43, (len(token), token)  # secrets.token_urlsafe(32)

    client = TestClient(calls[0])
    assert client.post("/api/control/rescan").status_code == 401
    assert (
        client.post("/api/control/rescan", headers={"x-dashboard-token": "auto"}).status_code
        == 401
    ), "the literal 'auto' must never be the secret"
    assert (
        client.post("/api/control/rescan", headers={"x-dashboard-token": token}).status_code
        == 200
    )


def test_module_explicit_literal_token_still_works_on_loopback(monkeypatch, capsys):
    """An operator-chosen literal on loopback is a deliberate choice: it works.

    A short token warns (non-fatal), it does not refuse to serve.
    """
    import uvicorn

    from resextract.dashboard.__main__ import main

    calls: list = []
    monkeypatch.setattr(uvicorn, "run", lambda app, **kw: calls.append(app))
    rc = main(["--token", "hunter2", "--host", "127.0.0.1", "--port", "0"])
    assert rc == 0, rc
    assert len(calls) == 1, calls
    err = capsys.readouterr().err
    assert "hunter2" in err and "characters" in err, err

    client = TestClient(calls[0])
    assert client.post("/api/control/rescan").status_code == 401
    assert (
        client.post("/api/control/rescan", headers={"x-dashboard-token": "hunter2"}).status_code
        == 200
    )


# --------------------------------------------------------------------------- #
# U6.17 -- the isolation is asserted, not assumed
# --------------------------------------------------------------------------- #


def test_every_app_resolves_to_the_isolated_copy_not_the_real_store(isolated_store):
    """GUARD: the store this file builds against is the copy, observably.

    ``create_app`` publishes the resolved store path *and* its source into
    ``app.state.dashboard`` (U6.16) so containment can be asserted rather than
    inferred.  Revert the redirection and the auth assertions below still pass
    -- against the real store -- while this one fails.
    """
    real = str(app_mod.api.DEFAULT_DB_PATH)
    dashboard = app_mod.create_app(host="127.0.0.1", token=TOKEN).state.dashboard
    assert dashboard["store_path"] == str(isolated_store), dashboard["store_path"]
    assert dashboard["store_source"] == "env", dashboard["store_source"]
    assert dashboard["store_resolution"]["store_path"] == str(isolated_store)
    assert dashboard["store_resolution"]["store_source"] == "env"
    assert dashboard["store_path"] != real, "the real store was resolved again"
    assert Path(dashboard["store_path"]).resolve() != Path(real).resolve()
    assert dashboard["layer"].resolution()["store_path"] == str(isolated_store)


def test_remote_app_and_module_entry_point_resolve_to_the_copy(isolated_store, monkeypatch):
    """The remote app and ``main()``'s app both see the copy, never the store."""
    import uvicorn

    from resextract.dashboard.__main__ import main

    remote = _remote_app()
    assert remote.state.dashboard["store_path"] == str(isolated_store)
    assert remote.state.dashboard["store_source"] == "env"

    calls: list = []
    monkeypatch.setattr(uvicorn, "run", lambda app, **kw: calls.append(app))
    assert main(["--token", TOKEN, "--host", "127.0.0.1", "--port", "0"]) == 0, calls
    assert len(calls) == 1, calls
    assert calls[0].state.dashboard["store_path"] == str(isolated_store)
    assert calls[0].state.dashboard["store_source"] == "env"

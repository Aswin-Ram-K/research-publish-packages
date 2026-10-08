"""Regression guard for the ``resextract`` CLI placeholder owner strings (U0.7).

Defect fixed here
-----------------
``cli.py`` shipped 11 subcommand placeholders whose "owner" hints named *live
unit ids* (``U1.1``, ``U2.1``, ``U4.1``, ``U4.2``, ``U5.2``, ``U6.1``,
``U7.1``).  Those ids collide with real agents that have already finished and
been superseded -- ``target`` claimed ``U1.1``, the graphify integration gate --
so a fresh reader could not tell what was still pending.  The Batch-0
checkpoint rule (``orchestration/STATUS.md``) is: *placeholder owners are named
by batch, never by a live unit id.*

U5.3 change (deliberate)
------------------------
``materialize`` is no longer a placeholder: it is a real subcommand (lane →
copied material → assembled + verified docket), so the placeholder set is now
**10**.  This file no longer reads ``PLACEHOLDERS`` as the whole dispatcher
surface; it pins three things instead, without deleting an assertion:

1. every *remaining* placeholder names a batch and no bare unit id;
2. the set of implemented subcommands is exactly
   ``{doctor, status, materialize}`` (``cli.IMPLEMENTED``), and
   registered subcommands == implemented ∪ placeholders;
3. ``materialize`` is a real parser carrying its real flags.

That keeps the original regression guard (a stage cannot silently become a
placeholder) *and* adds the converse (a placeholder cannot be counted as
implemented).

U6.2 change (deliberate)
-----------------------
``serve`` is no longer a placeholder either: it is a real subcommand that
dispatches to ``resextract.dashboard.app.create_app``, so the placeholder set
is now **9**.  The same three invariants are pinned, with ``serve`` moved into
``IMPLEMENTED_SUBCOMMANDS``, plus two new tests: ``serve`` carries its real
flags and it refuses a non-loopback bind without the explicit ``--allow-remote``
opt-in.  No assertion was deleted -- only the data the assertions read moved.

Red -> green (evidence, pasted verbatim)
----------------------------------------
Reverting exactly one owner to the old unit-id form (``target`` ->
``"batch 1 (U1.1)"``) and running ``.venv/bin/python -m pytest tests/test_cli.py``::

    __________ test_placeholder_exits_3_and_owner_names_the_batch[target] __________

    name = 'target'
    capsys = <_pytest.capture.CaptureFixture object at 0x7e0084279850>

        @pytest.mark.parametrize("name", sorted(EXPECTED_PLACEHOLDERS))
        def test_placeholder_exits_3_and_owner_names_the_batch(name, capsys):
            # (docstring line elided so this quoted traceback stays inside the module docstring)
            code = cli.main([name])
            out = capsys.readouterr().out

            assert code == cli.EXIT_NOT_IMPLEMENTED == 3
            assert cli.PLACEHOLDERS[name] in out
            assert BATCH_RE.search(out), f"{name} owner does not name a batch: {out!r}"
    >       assert not UNIT_ID_RE.search(out), f"{name} owner names a bare unit id: {out!r}"
    E       AssertionError: target owner names a bare unit id: 'resextract target: not implemented yet \u2014 planned for batch 1 (U1.1)\n'
    E       assert not <re.Match object; span=(62, 66), match='U1.1'>
    E        +  where <re.Match object; span=(62, 66), match='U1.1'> = <built-in method search of re.Pattern object at 0x7e00843475b0>('resextract target: not implemented yet \u2014 planned for batch 1 (U1.1)\n')
    E        +    where <built-in method search of re.Pattern object at 0x7e00843475b0> = re.compile('U\\d+\\.\\d+[a-z]?').search

    tests/test_cli.py:96: AssertionError
    =========================== short test summary info ===========================
    FAILED tests/test_cli.py::test_placeholder_exits_3_and_owner_names_the_batch[target]
    1 failed, 13 passed in 1.42s

Restoring the batch-only owner makes the same file pass: **14 passed in 2.16s**
(full text in ``state/logs/U0.7_red.txt`` and ``state/logs/U0.7_green.txt``).

Runtime note (Occamy outage)
----------------------------
``doctor``'s contract (``doctor.py`` module docstring) is exit **0** when every
``core`` leg is green and **2** when any core leg is down; optional legs down
still exit 0.  Occamy is a **core** leg and its endpoint was down during this
unit, so the doctor assertion below checks the *documented* contract -- the
process exit code matches the reported ``core_down`` list -- rather than
hardcoding 0.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import sqlite3
from pathlib import Path

import pytest

from resextract import cli

# ---------------------------------------------------------------------------
# U6.18 -- a read-only open that creates files; and the last two unisolated
# CLI test sites in this file.
# ---------------------------------------------------------------------------
#
# FACTS (U6.18, established on copies -- the real store is never opened here):
#   * the store is **WAL** (header bytes 18/19 = 2/2);
#   * every SQL statement reachable through ``DataLayer._connect`` is a SELECT,
#     i.e. the dashboard's connections are read-only in practice, but the
#     pipeline writes the same store through ``store.connect()``, so readers and
#     writers are concurrent *by design*;
#   * opening it ``mode=ro`` therefore creates ``<store>-wal`` / ``<store>-shm``
#     beside it -- shared-memory bookkeeping, not a write: the store's bytes,
#     sha256 and mtime are unchanged.
#
# DECISION (item 1) = option (d), a documented non-fix: ``immutable=1`` would
# suppress the sidecars but silently loses committed WAL rows (proved below), and
# ``nolock=1`` cannot open the file at all.  The remedy belongs to the writer
# (``journal_mode=DELETE``) and is handed up, not applied.

REPO_ROOT = Path(__file__).resolve().parents[1]
REAL_STORE = REPO_ROOT / "state" / "state.sqlite"


@pytest.fixture(scope="module", autouse=True)
def isolated_store(tmp_path_factory):
    """Point EVERY app/layer this module builds at a throwaway store copy.

    U6.18, item 2.  Two constructions in this file --
    ``dapp.create_app(dockets_dir=...)`` with no ``store_path`` -- used to read
    the real ``state/state.sqlite``, so both their result *and* their file side
    effects depended on whatever the real store happened to hold.  This uses the
    pattern U6.17 proved in ``tests/test_dashboard_auth.py``: a module-scoped
    autouse ``RESEXTRACT_STATE_DB`` redirect (rule two of ``resolve_store``'s
    precedence, U6.16) covers *every* construction in the file -- including the
    ``create_app(host="0.0.0.0")`` loopback-refusal call and any site added
    later -- so there is no call site to forget.  An explicit ``store_path=`` at
    the two known sites would have missed both.

    ``shutil.copyfile`` is a plain byte copy: the real database is never opened,
    which is exactly what keeps this fixture from creating the ``-wal``/``-shm``
    sidecars the isolation exists to prevent.  The prior env value is restored
    in teardown, so the redirect cannot leak into another test file.
    """
    from resextract.dashboard import api as api_mod

    src = REAL_STORE if REAL_STORE.is_file() else Path(api_mod.DEFAULT_DB_PATH)
    assert src.is_file(), f"real store missing: {src}"
    dst = tmp_path_factory.mktemp("u6.18-store") / "state-copy.sqlite"
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


def test_every_app_in_this_file_resolves_to_the_isolated_copy(isolated_store):
    """ITEM 2 GUARD: the store this file builds against is observably the copy.

    GREEN (current): the autouse redirect makes ``store_source == "env"`` and
    the resolved path the copy, on the observable surface the app publishes
    (``app.state.dashboard``) *and* on ``DataLayer.resolution()``.
    RED (this fixture removed): ``store_source == "default"`` and the resolved
    path is the real store -> the first assertion fails, so a regression of the
    redirection cannot hide behind assertions that would also pass against the
    real store.

    OBSERVED RED (redirect disabled in this fixture; test_cli.py restored
    bit-identically from state/logs/U6.18-test_cli.bak):
        E   AssertionError: default
        E   assert 'default' == 'env'
        1 failed in 0.26s => store_source was default: the real store was resolved.
    OBSERVED GREEN: 2 passed in 0.29s; test_cli.py sha256 back to
    1beb687193187aca1060f66e526ddd071ab7c80c9853c4a630f614d1921032cd.
    """
    from resextract.dashboard import app as app_mod

    app = app_mod.create_app(dockets_dir=str(REPO_ROOT / "dockets"))
    dashboard = app.state.dashboard

    assert dashboard["store_source"] == "env", dashboard["store_source"]
    assert dashboard["store_path"] == str(isolated_store)
    assert dashboard["store_resolution"]["store_path"] == str(isolated_store)
    assert dashboard["layer"].resolution()["store_path"] == str(isolated_store)
    assert Path(dashboard["store_path"]).resolve() == Path(isolated_store).resolve()
    assert Path(dashboard["store_path"]).resolve() != REAL_STORE.resolve(), (
        "the real store was resolved again"
    )


def test_readonly_open_creates_wal_sidecars_but_never_writes_the_store(tmp_path):
    """ITEM 1 (documented non-fix): the boundary side effect, reproduced on a copy.

    U6.18 reproduced this on the real store: opening it read-only created
    ``state/state.sqlite-wal`` (0 B, mtime 08:48:43.578899285) and
    ``state/state.sqlite-shm`` (32768 B, mtime 08:48:43.579631691) while the
    store's sha256 stayed ``40e8aa0c...de78c3`` and its mtime stayed
    ``07:47:56.009682763``.  Here the same open is done on a *copy*, so the real
    store is never touched: the two sidecars appear and the database bytes are
    bit-identical afterwards.  That is the whole of option (d): the files are a
    WAL reader's shared memory, not evidence that the store was written.
    """
    from resextract.dashboard import api as api_mod

    assert REAL_STORE.is_file(), f"real store missing: {REAL_STORE}"
    dst = tmp_path / "copy.sqlite"
    shutil.copyfile(REAL_STORE, dst)
    before_sha = hashlib.sha256(dst.read_bytes()).hexdigest()
    before_mtime = dst.stat().st_mtime_ns

    layer = api_mod.DataLayer(store_path=str(dst))
    con, err = layer._connect()
    assert err is None and con is not None, err
    assert con.execute("SELECT COUNT(*) FROM sqlite_master").fetchone()[0] > 0
    con.close()

    created = sorted(p.name for p in tmp_path.iterdir() if p.name.startswith("copy.sqlite-"))
    assert created == ["copy.sqlite-shm", "copy.sqlite-wal"], created
    assert (tmp_path / "copy.sqlite-wal").stat().st_size == 0
    assert (tmp_path / "copy.sqlite-shm").stat().st_size > 0
    assert hashlib.sha256(dst.read_bytes()).hexdigest() == before_sha, "the store bytes changed"
    assert dst.stat().st_mtime_ns == before_mtime, "the store mtime changed"


def test_immutable_uri_would_silently_lose_committed_wal_rows(tmp_path):
    """ITEM 1 (why ``immutable=1`` is REJECTED): it does not read the WAL.

    The store is WAL mode and the pipeline writes it while a reader can be up.
    This builds a WAL database whose committed rows live only in ``-wal``
    (``wal_autocheckpoint=0``) and copies db + ``-wal`` to a fixture:

    * ``mode=ro`` returns all 1000 rows (creating the ``-shm`` it needs);
    * ``mode=ro&immutable=1`` returns **no such table** -- it never looks at the
      WAL, so it reports an empty database.  Applied to a live store that is
      silent data loss, and its change detection is off as well, so a checkpoint
      rewriting the file under the reader is not noticed.  That is what a
      sidecar-suppressing "boundary fix" would buy;
    * ``mode=ro&nolock=1`` cannot open the file at all.

    If a later unit is tempted to switch the boundary to ``immutable=1`` to make
    the sidecars go away, this test is the reason not to.
    """
    writer_dir = tmp_path / "writer"
    writer_dir.mkdir()
    db = writer_dir / "wal.sqlite"
    writer = sqlite3.connect(db)
    writer.execute("PRAGMA journal_mode=WAL")
    writer.execute("PRAGMA wal_autocheckpoint=0")
    writer.execute("CREATE TABLE t(x)")
    writer.executemany("INSERT INTO t VALUES(?)", [(i,) for i in range(1000)])
    writer.commit()
    assert writer.execute("SELECT COUNT(*) FROM t").fetchone()[0] == 1000

    fx_dir = tmp_path / "fx"
    fx_dir.mkdir()
    fx = fx_dir / "c.sqlite"
    shutil.copyfile(db, fx)
    shutil.copyfile(Path(str(db) + "-wal"), Path(str(fx) + "-wal"))  # NO -shm yet
    writer.close()

    def rows(uri):
        try:
            con = sqlite3.connect(uri, uri=True)
        except sqlite3.Error as exc:
            return None, str(exc)
        try:
            return con.execute("SELECT COUNT(*) FROM t").fetchone()[0], None
        except sqlite3.Error as exc:
            return None, str(exc)
        finally:
            con.close()

    n_ro, err_ro = rows(f"file:{fx}?mode=ro")
    assert err_ro is None and n_ro == 1000, (n_ro, err_ro)

    shm = Path(str(fx) + "-shm")
    if shm.exists():
        shm.unlink()
    n_imm, err_imm = rows(f"file:{fx}?mode=ro&immutable=1")
    assert n_imm != 1000, "immutable=1 must never be presented as a safe substitute"
    assert err_imm is not None or n_imm == 0, (n_imm, err_imm)

    if shm.exists():
        shm.unlink()
    n_nolock, err_nolock = rows(f"file:{fx}?mode=ro&nolock=1")
    assert n_nolock != 1000, "nolock=1 must never be presented as a safe substitute"


def test_read_only_fallback_is_not_a_write_open(tmp_path, monkeypatch):
    """ITEM 1 GUARD: the non-URI fallback path is read-only too.

    ``_connect`` prefers the ``mode=ro`` URI; when that open raises it falls
    back to a plain open.  That fallback used to be a read-WRITE open, so a
    layer whose entire contract is read-only could silently regain write access
    -- a containment hole.  GREEN: the fallback carries ``PRAGMA query_only=ON``
    and any write raises ``OperationalError``.  RED (fallback reverted to the
    bare ``sqlite3.connect(str(path))``): the INSERT succeeds and the
    ``pytest.raises`` fails.  The write is attempted against a *copy*.

    OBSERVED RED (PRAGMA query_only=ON dropped from the fallback; api.py
    restored bit-identically from state/logs/U6.18-api.bak):
        E   assert 0 == 1   (PRAGMA query_only after the fallback open)
        1 failed in 0.26s => the fallback was a write-capable open.
    OBSERVED GREEN: 2 passed in 0.29s; api.py sha256 back to
    d5df9b08505189eceb0cb89021ae9b21685bf96dfb30dbeb07a30ef5ad24a511.
    """
    from resextract.dashboard import api as api_mod

    dst = tmp_path / "fallback.sqlite"
    shutil.copyfile(REAL_STORE, dst)
    layer = api_mod.DataLayer(store_path=str(dst))

    real_connect = api_mod.sqlite3.connect

    def uri_hostile(*args, **kwargs):
        if args and isinstance(args[0], str) and args[0].startswith("file:"):
            raise sqlite3.OperationalError("forced for test: URI open unavailable")
        return real_connect(*args, **kwargs)

    monkeypatch.setattr(api_mod.sqlite3, "connect", uri_hostile)
    con, err = layer._connect()
    assert err is None and con is not None, err
    try:
        assert con.execute("PRAGMA query_only").fetchone()[0] == 1
        with pytest.raises(sqlite3.OperationalError):
            con.execute("INSERT INTO schema_version(version, applied_at) VALUES (9999, 'u6.18')")
    finally:
        con.close()

BATCH_RE = re.compile(r"batch \d+")
UNIT_ID_RE = re.compile(r"U\d+\.\d+[a-z]?")

# Canonical mapping: placeholder subcommand -> target batch number, per
# orchestration/STATUS.md "CLI placeholder -> target batch (8 placeholders
# after U5.3 implemented `materialize`, U6.2 implemented `serve` and U8.3
# implemented `run`)".
EXPECTED_PLACEHOLDERS = {
    "target": 1,
    "mine": 2,
    "assess": 4,
    "lanes": 4,
    "open": 5,
    "export": 5,
    "refresh": 7,
    "watch": 7,
}

#: Subcommands that really run.  `materialize` moved here from the placeholder
#: map in U5.3, `serve` in U6.2 and `run` in U8.3; the assertion below fails if
#: any of those moves is ever undone silently.
IMPLEMENTED_SUBCOMMANDS = {"doctor", "status", "materialize", "serve", "run"}


def _registered_subcommands() -> set[str]:
    registered: set[str] = set()
    for action in cli.build_parser()._subparsers._group_actions:  # type: ignore[attr-defined]
        registered.update(action.choices)
    return registered


def test_mapping_covers_exactly_the_placeholder_subcommands():
    """Adding a placeholder without an owner (or vice versa) must fail here."""
    assert set(cli.PLACEHOLDERS) == set(EXPECTED_PLACEHOLDERS)
    assert set(cli.IMPLEMENTED) == IMPLEMENTED_SUBCOMMANDS
    assert not (set(cli.IMPLEMENTED) & set(EXPECTED_PLACEHOLDERS))
    assert _registered_subcommands() == set(cli.IMPLEMENTED) | set(EXPECTED_PLACEHOLDERS)


def test_materialize_is_a_real_subcommand_with_real_flags():
    """U5.3: `materialize` left the placeholder map and took its flags with it."""
    assert "materialize" not in cli.PLACEHOLDERS
    assert "materialize" in cli.IMPLEMENTED

    parser = cli.build_parser()
    sub = None
    for action in parser._subparsers._group_actions:  # type: ignore[attr-defined]
        if "materialize" in action.choices:
            sub = action.choices["materialize"]
    assert sub is not None
    flags: set[str] = set()
    for action in sub._actions:
        flags.update(action.option_strings)
    assert {
        "--target",
        "--lane",
        "--lane-file",
        "--docket-root",
        "--dry-run",
        "--json",
    } <= flags


def test_serve_is_a_real_subcommand_with_real_flags():
    """U6.2: `serve` left the placeholder map and took its real flags with it."""
    assert "serve" not in cli.PLACEHOLDERS
    assert "serve" in cli.IMPLEMENTED

    parser = cli.build_parser()
    sub = None
    for action in parser._subparsers._group_actions:  # type: ignore[attr-defined]
        if "serve" in action.choices:
            sub = action.choices["serve"]
    assert sub is not None
    flags: set[str] = set()
    defaults: dict[str, object] = {}
    for action in sub._actions:
        flags.update(action.option_strings)
        defaults[action.dest] = action.default
    assert {"--host", "--port", "--token", "--no-browser", "--allow-remote"} <= flags
    # `--token auto` is the documented default and the port default must come
    # from the dashboard, so the CLI never hardcodes a second one.
    assert defaults["token"] == "auto"
    assert defaults["no_browser"] is False
    assert defaults["allow_remote"] is False


def test_serve_refuses_non_loopback_without_explicit_override(capsys):
    """U6.2: `--host 0.0.0.0` is refused (exit 2) unless `--allow-remote`."""
    code = cli.main(["serve", "--host", "0.0.0.0"])
    out = capsys.readouterr().out

    assert code == cli.EXIT_CORE_DOWN == 2
    assert "refusing to start" in out
    assert "0.0.0.0" in out

    # The CLI reuses the dashboard's own guard, and the explicit opt-in makes
    # the same bind legal -- checked without ever starting uvicorn.
    from resextract.dashboard.app import check_bind_host

    with pytest.raises(ValueError):
        check_bind_host("0.0.0.0", False)
    assert check_bind_host("0.0.0.0", True) == "0.0.0.0"
    host, port, token = cli._resolve_serve(
        argparse.Namespace(host="0.0.0.0", port=None, token="u6-12-pinned", allow_remote=True)
    )
    assert host == "0.0.0.0"
    assert port == 8901
    # U6.12: a non-loopback bind needs an operator-chosen secret; `auto` is not
    # one, so only an explicit --token reaches this branch (pinned below).
    assert token == "u6-12-pinned"


@pytest.mark.parametrize("name", sorted(EXPECTED_PLACEHOLDERS))
def test_placeholder_exits_3_and_owner_names_the_batch(name, capsys):
    """Every placeholder: exit 3, owner names the right batch, no bare unit id."""
    code = cli.main([name])
    out = capsys.readouterr().out

    assert code == cli.EXIT_NOT_IMPLEMENTED == 3
    assert cli.PLACEHOLDERS[name] in out
    assert BATCH_RE.search(out), f"{name} owner does not name a batch: {out!r}"
    assert not UNIT_ID_RE.search(out), f"{name} owner names a bare unit id: {out!r}"
    assert f"batch {EXPECTED_PLACEHOLDERS[name]} (" in out


def test_run_is_a_real_subcommand_with_real_flags():
    """U8.3: `run` left the placeholder map (9 -> 8) and took its flags with it."""
    assert "run" not in cli.PLACEHOLDERS
    assert "run" in cli.IMPLEMENTED
    assert len(cli.PLACEHOLDERS) == 8
    assert set(cli.PLACEHOLDERS) == set(EXPECTED_PLACEHOLDERS)

    parser = cli.build_parser()
    sub = None
    for action in parser._subparsers._group_actions:  # type: ignore[attr-defined]
        if "run" in action.choices:
            sub = action.choices["run"]
    assert sub is not None
    flags: set[str] = set()
    defaults: dict[str, object] = {}
    for action in sub._actions:
        flags.update(action.option_strings)
        defaults[action.dest] = action.default
    assert {
        "--target",
        "--stages",
        "--dry-run",
        "--allow-active",
        "--allow-replay",
        "--window",
        "--json",
    } <= flags
    # `run` chains a real pipeline: the target is required and the safe path is
    # the default (no --allow-active, no --allow-replay).
    target_action = next(a for a in sub._actions if "--target" in a.option_strings)
    assert target_action.required is True
    assert defaults["allow_active"] is False
    assert defaults["allow_replay"] is False
    assert defaults["dry_run"] is False
    assert defaults["json"] is False
    assert float(defaults["window"]) == 5.0


def test_run_refuses_unknown_stages_and_exits_3(capsys):
    """An unknown stage name is a request we cannot implement as asked."""
    code = cli.main(["run", "--target", "duval", "--stages", "nope", "--dry-run"])
    out = capsys.readouterr().out
    assert code == cli.EXIT_NOT_IMPLEMENTED == 3
    assert "unknown stage" in out
    assert "graph" in out


def test_status_json_is_untouched(capsys):
    """``status --json`` still exits 0 and prints a JSON object."""
    code = cli.main(["status", "--json"])
    out = capsys.readouterr().out

    assert code == 0
    assert isinstance(json.loads(out), dict)


def test_doctor_keeps_its_documented_core_leg_contract(capsys):
    """``doctor --json`` exits 0 iff no core leg is down (occamy is core)."""
    code = cli.main(["doctor", "--json"])
    out = capsys.readouterr().out
    report = json.loads(out)

    assert code == report["exit_code"]
    expected = 0 if not report["core_down"] else cli.EXIT_CORE_DOWN
    assert code == expected
    assert report["ok"] == (code == 0)


# --------------------------------------------------------------------------- #
# U6.7: `serve --docket-root PATH` -- serve a fixture/scratch dockets directory.
#
# Verifier V6B was blocked from a live corrupt-manifest check because `serve`
# could not be pointed at a scratch dockets tree without writing into the real,
# independently-verified `dockets/`.  These tests pin the new flag and, above
# all, that docket containment is enforced RELATIVE TO THE CONFIGURED ROOT.
# --------------------------------------------------------------------------- #


def _fixture_docket(root, slug):
    """Create one minimal docket (a MANIFEST.json at root/slug) and return it."""
    from pathlib import Path as _Path

    directory = _Path(root) / slug
    directory.mkdir(parents=True, exist_ok=True)
    (directory / "MANIFEST.json").write_text(
        json.dumps({"slug": slug, "status": "ok", "type": "replay", "lane": "duval", "target": "duval"}),
        encoding="utf-8",
    )
    return directory


def _serve_spy(monkeypatch):
    """Run `serve` without ever binding a socket, capturing create_app kwargs."""
    import resextract.dashboard.app as dapp

    real_create = dapp.create_app
    captured: dict[str, object] = {}

    def spy(*args, **kwargs):
        captured.update(kwargs)
        return real_create(*args, **kwargs)

    monkeypatch.setattr(dapp, "create_app", spy)
    monkeypatch.setattr("uvicorn.run", lambda *a, **k: None)
    return captured


def test_serve_docket_root_flag_parses_and_passes_through(tmp_path, monkeypatch, capsys):
    """U6.7: the flag parses and reaches create_app; a scratch root with one
    fixture docket lists exactly one docket (and the repo's three are absent)."""
    scratch = tmp_path / "scratch"
    _fixture_docket(scratch, "fixture")

    captured = _serve_spy(monkeypatch)
    code = cli.main(["serve", "--docket-root", str(scratch), "--no-browser"])
    out = capsys.readouterr().out

    assert code == cli.EXIT_OK == 0
    assert captured["dockets_dir"] == str(scratch.resolve())
    assert str(scratch.resolve()) in out  # the resolved root is reported

    from fastapi.testclient import TestClient

    import resextract.dashboard.app as dapp

    app = dapp.create_app(dockets_dir=captured["dockets_dir"])
    payload = TestClient(app).get("/api/dockets").json()
    assert payload["count"] == 1
    assert [d["slug"] for d in payload["dockets"]] == ["fixture"]


def test_serve_without_docket_root_uses_the_default_root(tmp_path, monkeypatch, capsys):
    """U6.7: no flag => default behaviour is unchanged: create_app is called with
    dockets_dir=None (the dashboard's own default) and start-up reports the
    resolved default `dockets/` root."""
    from pathlib import Path as _Path

    monkeypatch.chdir(tmp_path)
    captured = _serve_spy(monkeypatch)
    code = cli.main(["serve", "--no-browser"])
    out = capsys.readouterr().out

    assert code == 0
    assert captured["dockets_dir"] is None
    assert f"docket root: {(_Path('dockets').resolve())}" in out


def test_serve_nonexistent_docket_root_exits_2_and_names_the_path(tmp_path, capsys):
    """U6.7 RED->GREEN guard (a): a nonexistent root is a hard config failure.

    GREEN (current): exit 2, "docket root does not exist: <abs path>".
    RED (cli.py reverted to pre-U6.7): `--docket-root` is unknown, so argparse
    exits 2 with "unrecognized arguments: --docket-root ..." and THIS test fails
    on `"does not exist" not in out` -- exit 2 alone is not enough, which is why
    the message and the verbatim path are asserted.

    OBSERVED RED (cli.py sha256 d755f8d9... restored; reverted 1d362329cafc): 
        FAILED test_serve_nonexistent_docket_root_exits_2_and_names_the_path
        E   SystemExit: 2 / "error: unrecognized arguments: --docket-root <path>"
        => 7 failed, 16 passed (the 7 are exactly the U6.7 additions)
    OBSERVED GREEN: 23 passed; cli.py sha256 back to d755f8d9... (bit-identical).
    """
    missing = tmp_path / "no-such-root"
    code = cli.main(["serve", "--docket-root", str(missing)])
    out = capsys.readouterr().out

    assert code == cli.EXIT_CORE_DOWN == 2
    assert "does not exist" in out
    assert str(missing) in out


def test_serve_docket_root_that_is_a_file_exits_2(tmp_path, capsys):
    """U6.7: a file, not a directory, is refused with exit 2 and a clear message."""
    not_a_dir = tmp_path / "manifest.json"
    not_a_dir.write_text("{}", encoding="utf-8")

    code = cli.main(["serve", "--docket-root", str(not_a_dir)])
    out = capsys.readouterr().out

    assert code == cli.EXIT_CORE_DOWN == 2
    assert "not a directory" in out
    assert str(not_a_dir) in out


def test_serve_empty_docket_root_starts_and_reports_no_dockets(tmp_path, monkeypatch, capsys):
    """U6.7: an EMPTY directory is a valid root -- the server starts and reports
    no dockets explicitly (count 0 + note), never a crash or a 500."""
    empty = tmp_path / "empty"
    empty.mkdir()

    captured = _serve_spy(monkeypatch)
    code = cli.main(["serve", "--docket-root", str(empty), "--no-browser"])
    out = capsys.readouterr().out

    assert code == 0
    assert str(empty.resolve()) in out

    from fastapi.testclient import TestClient

    import resextract.dashboard.app as dapp

    app = dapp.create_app(dockets_dir=captured["dockets_dir"])
    response = TestClient(app).get("/api/dockets")
    assert response.status_code == 200
    payload = response.json()
    assert payload["count"] == 0
    assert payload["dockets"] == []
    assert payload["note"]  # explicit "holds no MANIFEST.json", not a bare crash


def test_serve_relative_docket_root_is_resolved_against_cwd(tmp_path, monkeypatch, capsys):
    """U6.7: a relative path resolves against the cwd and the ABSOLUTE path is
    reported in the start-up output."""
    monkeypatch.chdir(tmp_path)
    _fixture_docket(tmp_path / "reldock", "fixture")

    captured = _serve_spy(monkeypatch)
    code = cli.main(["serve", "--docket-root", "reldock", "--no-browser"])
    out = capsys.readouterr().out

    assert code == 0
    assert captured["dockets_dir"] == str((tmp_path / "reldock").resolve())
    assert str((tmp_path / "reldock").resolve()) in out


def test_docket_containment_is_relative_to_the_configured_root(tmp_path, monkeypatch, capsys):
    """U6.7 RED->GREEN guard (b): containment follows `--docket-root`.

    The CLI must hand the scratch root to create_app, and containment must be
    evaluated against THAT root: a symlinked docket inside the configured root
    whose realpath escapes it is refused, while the legitimate docket passes.

    GREEN (current): `captured["dockets_dir"] == <scratch>` and
    `safe_docket_slug("escape", <scratch>) is None` (realpath escape refused),
    `safe_docket_slug("good", <scratch>) == "good"`.
    RED (cli.py reverted to pre-U6.7): create_app is called without dockets_dir,
    so the configured-root assertion fails (`None != <scratch>`), i.e. the
    traversal guard is no longer tied to the root the operator asked for.  The
    final assertion shows the check is load-bearing: WITHOUT a root argument
    `safe_docket_slug("escape")` returns the slug (no containment at all).

    OBSERVED RED (cli.py sha256 d755f8d9... restored; reverted 1d362329cafc): 
        FAILED test_docket_containment_is_relative_to_the_configured_root
        E   SystemExit: 2 / "error: unrecognized arguments: --docket-root <scratch>"
        => captured["dockets_dir"] is never set: nothing is tied to the root.
    OBSERVED GREEN: 23 passed; cli.py sha256 back to d755f8d9... (bit-identical).
    """
    from resextract.dashboard import api

    scratch = tmp_path / "scratch"
    _fixture_docket(scratch, "good")
    outside = tmp_path / "outside"
    (outside / "escape").mkdir(parents=True)
    (outside / "escape" / "MANIFEST.json").write_text("{}", encoding="utf-8")
    (scratch / "escape").symlink_to(outside / "escape", target_is_directory=True)

    captured = _serve_spy(monkeypatch)
    code = cli.main(["serve", "--docket-root", str(scratch), "--no-browser"])
    capsys.readouterr()

    assert code == 0
    root = captured["dockets_dir"]
    assert root == str(scratch.resolve())  # <- red when the flag is not plumbed

    assert api.safe_docket_slug("good", root) == "good"
    assert api.safe_docket_slug("escape", root) is None
    assert api.safe_docket_slug("..", root) is None
    assert api.safe_docket_slug("../outside", root) is None

    # Demonstrably load-bearing: with no root there is no containment check.
    assert api.safe_docket_slug("escape") is not None


# ===========================================================================
# U6.9 -- ONE bind decision, honoured on every entry point
# ===========================================================================
# Defect found by U6.8's verifier and reproduced here: `python -m
# resextract.dashboard --host 0.0.0.0` folded "an explicit --host" into
# `allow_remote` and therefore BOUND every interface, serving the OPEN READ
# routes (store, journals, dockets, graph) to the network -- only the control
# routes are token-gated.  Meanwhile `resextract serve` and `python -m
# resextract.cli serve` refused the very same flag with exit 2.  U6.6 and U6.7
# were both right about *their* entry point; the dashboard module was the bypass.
#
# There was also no `python -m resextract` at all (no `__main__`: exit 1,
# "No module named resextract.__main__").  It now exists and hands off to
# `cli.main`, so it reaches the same decision.
#
# The single decision site is `resextract.dashboard.app.check_bind_host`.


def _repo_root():
    from pathlib import Path

    return Path(__file__).resolve().parents[1]


def _free_port() -> int:
    import socket

    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def _port_is_free(port: int) -> bool:
    import socket

    with socket.socket() as sock:
        sock.settimeout(0.5)
        return sock.connect_ex(("127.0.0.1", port)) != 0


def _lan_host() -> str:
    """A non-loopback, non-0.0.0.0 IP: $U6.9_LAN_IP, else a real interface IP.

    Falls back to TEST-NET-3 (203.0.113.7, RFC 5737) which is non-loopback and
    never a local address: the refusal is syntactic, so that still exercises the
    guard when no interface address is discoverable.
    """
    import os
    import socket

    override = os.environ.get("U6.9_LAN_IP")
    if override:
        return override
    candidates = []
    try:
        candidates.append(socket.gethostbyname(socket.gethostname()))
    except OSError:
        pass
    try:
        candidates += [info[4][0] for info in socket.getaddrinfo(socket.gethostname(), None, socket.AF_INET)]
    except OSError:
        pass
    for ip in candidates:
        if not ip.startswith("127."):
            return ip
    return "203.0.113.7"


def _entry_point_cmd(name: str, host: str, port: int) -> list:
    import sys

    root = _repo_root()
    if name == "console":
        return [
            str(root / ".venv" / "bin" / "resextract"), "serve",
            "--host", host, "--port", str(port), "--no-browser",
        ]
    if name == "module":
        return [
            sys.executable, "-m", "resextract", "serve",
            "--host", host, "--port", str(port), "--no-browser",
        ]
    if name == "module_cli":
        return [
            sys.executable, "-m", "resextract.cli", "serve",
            "--host", host, "--port", str(port), "--no-browser",
        ]
    if name == "dashboard":
        return [sys.executable, "-m", "resextract.dashboard", "--host", host, "--port", str(port)]
    raise AssertionError(f"unknown entry point {name!r}")


#: Every documented way to start the server.  A future entry point must be
#: added here -- and it will fail until it consults the shared guard.
ENTRY_POINTS = ["console", "module", "module_cli", "dashboard"]


@pytest.mark.parametrize("host", ["0.0.0.0", _lan_host()])
@pytest.mark.parametrize("name", ENTRY_POINTS)
def test_non_loopback_bind_is_refused_on_every_entry_point(name, host, tmp_path):
    """U6.9: a non-loopback host without --allow-remote is exit 2, nothing bound.

    Real subprocesses, real exit codes, and the port is probed afterwards so a
    process that bound and then died cannot pass.
    """
    import os
    import subprocess

    port = _free_port()
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
    proc = subprocess.run(
        _entry_point_cmd(name, host, port),
        capture_output=True, text=True, timeout=90, cwd=str(tmp_path), env=env,
    )
    combined = proc.stdout + proc.stderr
    assert proc.returncode == 2, f"{name} {host} exit={proc.returncode}: {combined}"
    assert "non-loopback" in combined, combined
    assert _port_is_free(port), f"{name} left {host}:{port} bound"


@pytest.mark.parametrize("name", ["cli", "dashboard"])
def test_allow_remote_opt_in_still_starts(name, monkeypatch):
    """U6.9 guard (b): the deliberate `--allow-remote` opt-in still starts.

    Red state (revert `check_bind_host` so it ignores `allow_remote`):

        E       assert 2 == 0
        E       assert 2 == 0
        FAILED tests/test_cli.py::test_allow_remote_opt_in_still_starts[cli] - assert...
        FAILED tests/test_cli.py::test_allow_remote_opt_in_still_starts[dashboard] - ...
    """
    import uvicorn

    calls = []
    monkeypatch.setattr(uvicorn, "run", lambda app, **kw: calls.append(kw))
    if name == "cli":
        code = cli.main(
            [
                "serve", "--host", "0.0.0.0", "--allow-remote",
                "--token", "u6-12-pinned", "--port", "8971", "--no-browser",
            ]
        )
    else:
        from resextract.dashboard import __main__ as dash_main

        code = dash_main.main(
            ["--host", "0.0.0.0", "--allow-remote", "--token", "u6-12-pinned", "--port", "8971"]
        )
    assert code == 0
    assert calls and calls[0]["host"] == "0.0.0.0", calls


@pytest.mark.parametrize("name", ["cli", "dashboard"])
def test_loopback_host_still_starts(name, monkeypatch):
    """U6.9: `--host 127.0.0.1` keeps working on both entry points."""
    import uvicorn

    calls = []
    monkeypatch.setattr(uvicorn, "run", lambda app, **kw: calls.append(kw))
    if name == "cli":
        code = cli.main(["serve", "--host", "127.0.0.1", "--port", "8971", "--no-browser"])
    else:
        from resextract.dashboard import __main__ as dash_main

        code = dash_main.main(["--host", "127.0.0.1", "--port", "8971"])
    assert code == 0
    assert calls and calls[0]["host"] == "127.0.0.1", calls


def test_no_entry_point_grants_remote_binding_by_itself(monkeypatch):
    """U6.9 guard (a): no entry point may authorise remote binding by itself.

    Both entry points must reach the SAME guard function object, and each must
    consult it with the user's own flag only -- never with a value it derived
    from an explicit `--host`.  This is the single-decision invariant: a future
    entry point that reintroduces the inference fails here, and a hard-coded
    "return 2" cannot pass either (the guard must actually be consulted).

    Red state (revert the `--main__` line to
    `allow_remote = args.allow_remote or (explicit_host and not is_loopback(host))`):

        E           subprocess.TimeoutExpired: Command '['/home/zer0null/reserach extarctor/.venv/bin/python', '-m', 'resextract.dashboard', '--host', '0.0.0.0', '--port', '44359']' timed out after 90 seconds
        E       AssertionError: dashboard 203.0.113.7 exit=3: WARNING: binding non-loopback host '203.0.113.7'; this exposes the dashboard
        E         INFO:     Started server process [34]
        E         INFO:     Waiting for application startup.
        E         INFO:     Application startup complete.
        E         ERROR:    could not bind on any address out of [('203.0.113.7', 46105)]
        E         INFO:     Waiting for application shutdown.
        E         INFO:     Application shutdown complete.
        E
        E       assert 3 == 2
        E        +  where 3 = CompletedProcess(args=['/home/zer0null/reserach extarctor/.venv/bin/python', '-m', 'resextract.dashboard', '--host', '... of [('203.0.113.7', 46105)]\nINFO:     Waiting for application shutdown.\nINFO:     Application shutdown complete.\n").returncode
        E       AssertionError: assert 0 == 2
        E        +  where 0 = <function main at 0x7417ddb35dd0>(['--host', '0.0.0.0'])
        E        +    where <function main at 0x7417ddb35dd0> = <module 'resextract.dashboard.__main__' from '/home/zer0null/reserach extarctor/src/resextract/dashboard/__main__.py'>.main
        FAILED tests/test_cli.py::test_non_loopback_bind_is_refused_on_every_entry_point[dashboard-0.0.0.0]
        FAILED tests/test_cli.py::test_non_loopback_bind_is_refused_on_every_entry_point[dashboard-203.0.113.7]
        FAILED tests/test_cli.py::test_no_entry_point_grants_remote_binding_by_itself
    """
    import uvicorn
    import resextract.dashboard.app as dapp
    from resextract.dashboard import __main__ as dash_main

    monkeypatch.setattr(uvicorn, "run", lambda *a, **k: None)
    assert dash_main.check_bind_host is dapp.check_bind_host, (
        "python -m resextract.dashboard must delegate to the shared guard"
    )

    real = dapp.check_bind_host
    seen = []

    def spy(host, allow_remote=False):
        seen.append((host, allow_remote))
        return real(host, allow_remote)

    monkeypatch.setattr(dapp, "check_bind_host", spy)
    monkeypatch.setattr(dash_main, "check_bind_host", spy)

    assert cli.main(["serve", "--host", "0.0.0.0", "--no-browser"]) == 2
    assert seen, "the CLI did not consult the shared bind guard"
    assert all(allow is False for _, allow in seen), f"the CLI granted remote itself: {seen}"

    seen.clear()
    assert dash_main.main(["--host", "0.0.0.0"]) == 2
    assert seen, "the dashboard entry point did not consult the shared bind guard"
    assert all(allow is False for _, allow in seen), (
        f"the dashboard entry point granted remote binding itself: {seen}"
    )


def test_no_source_infers_allow_remote_from_an_explicit_host():
    """U6.9: pin the bypass *shape*, so a new module cannot reintroduce it."""
    package = _repo_root() / "src" / "resextract"
    forbidden = re.compile(r"allow_remote\s*=[^\n]*(is_loopback|explicit_host)")
    offenders = [
        f"{path.relative_to(_repo_root())}:{lineno}: {line.strip()}"
        for path in sorted(package.rglob("*.py"))
        for lineno, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1)
        if forbidden.search(line)
    ]
    assert offenders == [], offenders


def test_create_app_refuses_non_loopback_by_default():
    """U6.9: `create_app`'s own default cannot grant a remote bind."""
    import inspect
    import resextract.dashboard.app as dapp

    assert inspect.signature(dapp.create_app).parameters["allow_remote"].default is False
    with pytest.raises(ValueError):
        dapp.create_app(host="0.0.0.0")


# ---------------------------------------------------------------------------
# U6.12 -- a remote bind needs an operator-chosen token, and reads are gated
# ---------------------------------------------------------------------------


def test_remote_bind_rejects_the_auto_token(capsys, monkeypatch):
    """U6.12 rule (b): `--token auto` is *usable* but not an operator CHOICE.

    Red state (revert the token requirement in `_resolve_serve` and
    `dashboard.__main__` -- both guards to `if False:`): the namespace below
    stops raising and `serve --host <lan> --allow-remote` starts on an
    auto-generated secret instead of exiting 2, so this test fails.
    """
    import uvicorn

    from resextract.dashboard import __main__ as dash_main

    calls = []
    # A sentinel: in the RED state this test must not really bind the LAN.
    monkeypatch.setattr(uvicorn, "run", lambda app, **kw: calls.append(kw))

    lan = _lan_host()
    with pytest.raises(ValueError):
        cli._resolve_serve(
            argparse.Namespace(host=lan, port=None, token="auto", allow_remote=True)
        )
    code = cli.main(["serve", "--host", lan, "--allow-remote", "--no-browser"])
    out = capsys.readouterr().out
    assert code == cli.EXIT_CORE_DOWN == 2
    assert "explicit --token" in out, out

    assert dash_main.main(["--host", lan, "--allow-remote"]) == 2
    assert calls == [], "a remote bind with no chosen token must never reach uvicorn"


@pytest.mark.parametrize("name", ["cli", "dashboard"])
def test_remote_bind_with_an_explicit_token_starts(name, monkeypatch):
    """The deliberate `--allow-remote --token <secret>` opt-in still starts."""
    import uvicorn

    from resextract.dashboard import __main__ as dash_main

    calls = []
    monkeypatch.setattr(uvicorn, "run", lambda app, **kw: calls.append((app, kw)))
    lan = _lan_host()
    if name == "cli":
        code = cli.main(
            ["serve", "--host", lan, "--allow-remote", "--token", "u6-12-pinned",
             "--port", "8973", "--no-browser"]
        )
    else:
        code = dash_main.main(
            ["--host", lan, "--allow-remote", "--token", "u6-12-pinned", "--port", "8973"]
        )
    assert code == 0, code
    assert calls, "uvicorn.run was never reached"
    app, kwargs = calls[0]
    assert kwargs["host"] == lan, calls
    assert app.state.dashboard["remote_reads_gated"] is True


def test_loopback_auto_token_still_generates_one():
    """`--token auto` on loopback is unchanged: generated, printed, control-only."""
    host, port, token = cli._resolve_serve(
        argparse.Namespace(host="127.0.0.1", port=None, token="auto", allow_remote=False)
    )
    assert host == "127.0.0.1"
    assert port == 8901
    assert isinstance(token, str) and token and token != "auto"

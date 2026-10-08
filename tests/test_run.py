"""``resextract run`` — the pipeline orchestrator's honesty contract (U8.3).

Offline: the model endpoint is DOWN, every test injects the doctor report (so no
network probe happens) and fakes the heavy no-model stages where they would
touch the real filesystem, while the code under test — the producer gate, the
blocked/`skipped` distinction, the sealed window and the exit-code mapping — is
the real implementation.  ``--allow-replay`` materialization is exercised with
the docket assembler stubbed; nothing is ever written into a target repo.

Two regression guards are pinned here, both proven red→green against the real
file (revert → the named test fails; restore → sha256 bit-identical,
``PYTHONDONTWRITEBYTECODE=1`` + ``__pycache__`` purge for every comparison):

**Guard (a) — blocked, never skipped, when the endpoint is down.**
Reverting ``_stage_mine``'s gate branch (``return StageResult(status="blocked")``
→ ``status="skipped"``) makes
``test_guard_a_blocked_not_skipped_for_a_down_endpoint`` fail with
``assert 'blocked' == 'skipped'`` — observed red:
``AssertionError: mine is 'skipped', expected blocked``.
sha256 of ``src/resextract/run.py`` before/after the revert-restore cycle is
identical (bit-identical restore, ``cmp`` clean):
``9efc0c32d807e5cb7670339dbdb725ba08b0867413b44183beeec3d7ba9a35a7``.

**Guard (b) — the producer gate skips materialize without ``--allow-replay``.**
Reverting ``_stage_materialize``'s
``if not ctx.allow_replay: return StageResult(status="skipped", ...)`` branch
(letting a replay-provenance lane materialize anyway) makes
``test_guard_b_producer_gate_skips_materialize_without_allow_replay`` fail with
``AssertionError: assert 'degraded' == 'skipped'`` (the gate reverted to
``if False:``, so the replay lane reached the docket assembler).
sha256 of ``src/resextract/run.py`` before/after is
``9efc0c32d807e5cb7670339dbdb725ba08b0867413b44183beeec3d7ba9a35a7``
(bit-identical restore).

Both experiments ran at that revision, under ``PYTHONDONTWRITEBYTECODE=1`` with
a ``__pycache__`` purge between every revert/restore; ``run.py`` has since
gained the needs-based core-leg preflight gate (the live run's SearXNG finding),
which touches neither guard.

**Guard (c) — U8.5: the plan matches the run.** The dry run and the real run now
share ``_reuse_candidate``, so with a usable graph on disk both report
``mode=reuse``; before the fix the dry run planned ``would run `graphify
extract``` while the real run reused the existing graph.  Revert the dry-run
branch ⇒ ``test_plan_matches_run_for_the_graph_stage`` fails:
``AssertionError: dry run planned mode='build', real run used mode='reuse'``.
sha256 of ``src/resextract/run.py`` before/after: ``18d8bc328a0ec8c3c667622dca16f8f5f7274af25edb08830f398ad6003cc8a1``.

**Guard (d) — U8.5: the run-scoped copy is clean and self-contained.** The
backup API copies the WAL header, so the copy used to be a WAL database whose
``-wal``/``-shm`` companions survived any connection a stage left open.  The
copy is now written into a rollback journal and finalised, so even a
deliberately leaked connection leaves no sidecars.  Revert the journal switch ⇒
``test_run_leaves_a_clean_self_contained_store_copy`` fails:
``AssertionError: sidecars left behind: ['state.sqlite-shm', 'state.sqlite-wal']``.
sha256 of ``src/resextract/run.py`` before/after: ``18d8bc328a0ec8c3c667622dca16f8f5f7274af25edb08830f398ad6003cc8a1``.

Both reverted-restored under ``PYTHONDONTWRITEBYTECODE=1`` with a **full**
``__pycache__`` purge between every revert and restore (a narrow purge is
untrustworthy: it was measured to produce spurious failures); restore was
``cmp``-clean and sha256 bit-identical.
"""

from __future__ import annotations

import dataclasses
import hashlib
import json
import sqlite3
import subprocess
from pathlib import Path
from types import SimpleNamespace

import pytest

from resextract import run as run_mod
from resextract import store
from resextract.run import (
    EXIT_DEGRADED,
    EXIT_HARD_DOWN,
    EXIT_NOTHING_RUNNABLE,
    EXIT_OK,
    MODEL_STAGES,
    STAGE_ORDER,
    StageResult,
    exit_code_for,
    run_pipeline,
)


# --------------------------------------------------------------------------- #
# Fixtures
# --------------------------------------------------------------------------- #


def _git(repo: Path, *args: str) -> str:
    return subprocess.run(
        ["git", "-C", str(repo), *args],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


@pytest.fixture()
def target_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    repo.mkdir()
    _git(repo, "init", "-q")
    _git(repo, "config", "user.email", "u8.3@example.invalid")
    _git(repo, "config", "user.name", "U8.3")
    (repo / "README.md").write_text("# demo\n\nsome material\n", encoding="utf-8")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "initial")
    return repo


@pytest.fixture()
def config_dir(tmp_path: Path, target_repo: Path) -> Path:
    cfg = tmp_path / "config"
    cfg.mkdir()
    (cfg / "targets.toml").write_text(
        "[targets.demo]\n"
        'slug = "demo"\n'
        f'path = "{target_repo}"\n'
        "read_only = true\n"
        'include = ["docs/"]\n'
        "assert_present = []\n",
        encoding="utf-8",
    )
    return cfg


@pytest.fixture()
def db_path(tmp_path: Path) -> Path:
    db = tmp_path / "state.sqlite"
    store.init_db(db)
    return db


def _seed_candidates(db: Path, producers: dict[str, int]) -> None:
    con = store.connect(db)
    try:
        for producer, count in producers.items():
            for index in range(count):
                store.insert_candidate(
                    con,
                    kind="finding",
                    title=f"{producer} candidate {index}",
                    summary="a summary",
                    provenance_json=[
                        {"ref": "README.md", "exists": True, "sha256": "a" * 8}
                    ],
                    graph_nodes_json=[],
                    score=1.0,
                    state="mined",
                    producer=producer,
                )
        con.commit()
    finally:
        con.close()


def _doctor(endpoint_ok: bool, *, extra_down: tuple[str, ...] = ()) -> dict:
    legs = [
        {
            "leg": "Occamy",
            "class": "core",
            "ok": endpoint_ok,
            "detail": "http 200 ok" if endpoint_ok else "http 000 (connection refused)",
        },
        {"leg": "graphify", "class": "core", "ok": "graphify" not in extra_down, "detail": "ok"},
        {"leg": "SearXNG", "class": "optional", "ok": False, "detail": "down"},
    ]
    for name in extra_down:
        if name != "graphify":
            legs.append({"leg": name, "class": "core", "ok": False, "detail": "down"})
    return {"legs": legs, "core_down": [], "optional_down": ["SearXNG"]}


def _ok_for(name: str):
    def _impl(ctx) -> StageResult:
        if name == "graph":
            ctx.graph_path = None
        return StageResult(name=name, status="ok", reason="fake ok")

    return _impl


_ALL_OK = {name: _ok_for(name) for name in STAGE_ORDER}

#: Only the heavy no-model stages are faked by default: the model stages and
#: `materialize` stay REAL, because they carry the gates under test.
_FAKE_NO_MODEL = {name: _ALL_OK[name] for name in ("graph", "staging", "refresh")}


@pytest.fixture()
def clean_preflight(monkeypatch: pytest.MonkeyPatch):
    """A preflight with a policy configured (so its absence is not a degradation)."""
    monkeypatch.setattr(
        "resextract.refresh.writer.policy_for_target", lambda _root: object()
    )
    monkeypatch.setattr(
        "resextract.kg.policy.policy_audit",
        lambda root, policy, **kw: SimpleNamespace(violations=[], admitted={"README.md": 10}),
    )


def _kwargs(tmp_path: Path, config_dir: Path, db_path: Path, **over) -> dict:
    kwargs = dict(
        stages=None,
        dry_run=False,
        allow_active=False,
        allow_replay=False,
        window_s=0.01,
        stage_impls=dict(_FAKE_NO_MODEL),
        doctor_report=_doctor(False),
        db_path=db_path,
        run_root=tmp_path / "run",
        config_dir=str(config_dir),
    )
    kwargs.update(over)
    return kwargs


# --------------------------------------------------------------------------- #
# Guard (a): blocked — not skipped — when the endpoint is down
# --------------------------------------------------------------------------- #


def test_guard_a_blocked_not_skipped_for_a_down_endpoint(
    tmp_path, config_dir, db_path, monkeypatch
):
    """RED→GREEN guard (a).

    Endpoint down ⇒ ``mine``/``claims``/``assess`` are ``blocked`` with the
    observed endpoint status in the reason, and the exit code is a degradation
    (1) — not 0.  Reverting the gate to ``skipped`` (or removing it) fails here:
    ``assert 'blocked' == 'skipped'``.  sha256 before/after: ``__SHA_A__``.
    """
    _seed_candidates(db_path, {"replay": 3})

    def _no_client(*_a, **_k):  # pragma: no cover - must never be reached
        raise AssertionError("no LLM client may be built while the endpoint is down")

    monkeypatch.setattr("resextract.llm.OccamyClient", _no_client)

    report = run_pipeline("demo", **_kwargs(tmp_path, config_dir, db_path))

    for name in MODEL_STAGES:
        stage = report.stage(name)
        assert stage is not None, f"{name} must appear in the stage table"
        assert stage.status == "blocked", f"{name} is {stage.status!r}, expected blocked"
        assert stage.status != "skipped"
        assert "000" in stage.reason
        assert "endpoint" in stage.reason.lower()
    assert report.exit_code == EXIT_DEGRADED == 1
    assert report.producer_gate["model_produced"] == 0
    assert report.producer_gate["by_producer"] == {"replay": 3}
    assert any("producer gate" in d for d in report.degradations)


# --------------------------------------------------------------------------- #
# Guard (b): the producer gate skips materialize without --allow-replay
# --------------------------------------------------------------------------- #


def test_guard_b_producer_gate_skips_materialize_without_allow_replay(
    tmp_path, config_dir, db_path, monkeypatch, clean_preflight
):
    """RED→GREEN guard (b).

    Replay-only candidates and no ``--allow-replay`` ⇒ ``materialize`` is
    ``skipped`` with exactly ``no model-produced candidates`` in the reason and
    the docket assembler is never called.  Reverting the gate fails here:
    ``AssertionError: materialize must not run on replay provenance``.
    sha256 before/after: ``__SHA_B__``.
    """
    _seed_candidates(db_path, {"replay": 2})
    from resextract.docket import materialize as mat_mod

    def _forbidden(*_a, **_k):  # pragma: no cover - must never be reached
        raise AssertionError("materialize must not run on replay provenance")

    monkeypatch.setattr(mat_mod, "materialize_lane", _forbidden)

    report = run_pipeline("demo", **_kwargs(tmp_path, config_dir, db_path))

    stage = report.stage("materialize")
    assert stage is not None
    assert stage.status == "skipped"
    assert "no model-produced candidates" in stage.reason
    assert report.exit_code == EXIT_DEGRADED


def test_allow_replay_materializes_and_says_replay_derived(
    tmp_path, config_dir, db_path, monkeypatch, clean_preflight
):
    """With ``--allow-replay`` the gate opens — and the reason admits provenance."""
    _seed_candidates(db_path, {"replay": 2})
    from resextract.docket import materialize as mat_mod

    calls: list[str] = []

    def _fake_materialize(spec, **kwargs):
        calls.append(spec.slug)
        return SimpleNamespace(
            docket_dir=str(tmp_path / "dockets" / spec.slug),
            window_sealed=True,
        )

    monkeypatch.setattr(mat_mod, "materialize_lane", _fake_materialize)

    report = run_pipeline(
        "demo", **_kwargs(tmp_path, config_dir, db_path, allow_replay=True)
    )

    stage = report.stage("materialize")
    assert stage is not None
    assert calls, "materialize_lane must have been called under --allow-replay"
    assert stage.status != "skipped"
    assert stage.counts["replay_derived"] is True
    assert "REPLAY-DERIVED" in stage.reason
    assert report.exit_code == EXIT_DEGRADED == 1
    assert any("replay" in d.lower() for d in report.degradations)


# --------------------------------------------------------------------------- #
# Preflight
# --------------------------------------------------------------------------- #


def test_preflight_failure_exits_2_and_runs_no_stage(tmp_path, config_dir, db_path):
    """A down *hard* core leg (graphify): exit 2, and not one stage ran."""
    calls: list[str] = []

    def _spy(name):
        def _impl(ctx):
            calls.append(name)
            return StageResult(name=name, status="ok", reason="should not run")

        return _impl

    report = run_pipeline(
        "demo",
        **_kwargs(
            tmp_path,
            config_dir,
            db_path,
            stage_impls={name: _spy(name) for name in STAGE_ORDER},
            doctor_report=_doctor(False, extra_down=("graphify",)),
        ),
    )

    assert report.exit_code == EXIT_HARD_DOWN == 2
    assert calls == [], f"no stage may run after a failed preflight (ran {calls})"
    assert report.preflight["ok"] is False
    assert any("graphify" in f for f in report.preflight["failures"])
    assert report.stages, "the plan must still name the stages"
    for stage in report.stages:
        assert stage.status == "skipped"
        assert "preflight failed" in stage.reason
    assert report.window_sealed is False


def test_preflight_failure_when_read_only_is_not_declared(tmp_path, target_repo, db_path):
    """A target that does not declare ``read_only`` cannot be run against."""
    cfg = tmp_path / "config"
    cfg.mkdir()
    (cfg / "targets.toml").write_text(
        "[targets.demo]\n"
        'slug = "demo"\n'
        f'path = "{target_repo}"\n'
        "read_only = false\n",
        encoding="utf-8",
    )
    report = run_pipeline(
        "demo",
        **_kwargs(tmp_path, cfg, db_path, stage_impls=dict(_ALL_OK)),
    )
    assert report.exit_code == EXIT_HARD_DOWN
    assert any("read_only" in f for f in report.preflight["failures"])


def test_policy_violations_fail_preflight(tmp_path, config_dir, db_path, monkeypatch):
    """The policy audit's assert_present violations are a hard gate."""
    monkeypatch.setattr(
        "resextract.refresh.writer.policy_for_target", lambda _root: object()
    )
    monkeypatch.setattr(
        "resextract.kg.policy.policy_audit",
        lambda root, policy, **kw: SimpleNamespace(
            violations=["docs/MISSING.md: asserted but not admitted"], admitted={}
        ),
    )
    report = run_pipeline("demo", **_kwargs(tmp_path, config_dir, db_path))
    assert report.exit_code == EXIT_HARD_DOWN
    assert report.preflight["policy_violations"]
    assert any("assert_present" in f for f in report.preflight["failures"])


# --------------------------------------------------------------------------- #
# Sealed window
# --------------------------------------------------------------------------- #


def test_sealed_window_detects_a_moved_head(tmp_path, config_dir, db_path, target_repo):
    """A target mutated mid-run: both heads recorded, a degradation, exit 1."""

    def _mutate(ctx):
        (ctx.target_root / "late.txt").write_text("moved\n", encoding="utf-8")
        _git(ctx.target_root, "add", "-A")
        _git(ctx.target_root, "commit", "-q", "-m", "moved mid-run")
        return StageResult(name="refresh", status="ok", reason="moved the target")

    impls = dict(_ALL_OK)
    impls["refresh"] = _mutate

    report = run_pipeline(
        "demo",
        **_kwargs(
            tmp_path,
            config_dir,
            db_path,
            stage_impls=impls,
            doctor_report=_doctor(False),
        ),
    )

    assert report.window_sealed is False
    assert report.head_before and report.head_after
    assert report.head_before != report.head_after
    assert any("NOT sealed" in d or "moved" in d for d in report.degradations)
    assert report.exit_code == EXIT_DEGRADED == 1


def test_window_sealed_when_the_target_is_quiet(
    tmp_path, config_dir, db_path, clean_preflight, monkeypatch
):
    """A quiet target and an identical HEAD: sealed, and exit 0."""
    _seed_candidates(db_path, {"model": 1})
    from resextract.docket import materialize as mat_mod

    monkeypatch.setattr(
        mat_mod,
        "materialize_lane",
        lambda spec, **kw: SimpleNamespace(
            docket_dir=str(tmp_path / "dockets" / spec.slug), window_sealed=True
        ),
    )
    # The injected doctor report says the endpoint is up; this offline test must
    # still never construct a real client.
    monkeypatch.setattr(run_mod, "_make_client", lambda ctx: (None, "offline test"))
    report = run_pipeline(
        "demo",
        **_kwargs(
            tmp_path,
            config_dir,
            db_path,
            doctor_report=_doctor(True),
            stage_impls=dict(_ALL_OK),
        ),
    )
    assert report.window_sealed is True
    assert report.head_before == report.head_after
    assert report.degradations == []
    assert report.exit_code == EXIT_OK == 0
    assert all(stage.status == "ok" for stage in report.stages)


def test_never_reports_sealed_when_quiescence_was_not_measured(
    tmp_path, config_dir, db_path, clean_preflight, monkeypatch
):
    """A run with no observable HEAD is never reported sealed."""
    from resextract.refresh import writer as writer_mod

    def _busy(*_a, **_k):
        raise writer_mod.TargetBusyError(
            writer_mod.WriterSignal(
                verdict="busy",
                head_before="a" * 40,
                head_after="b" * 40,
                dirty_before=(),
                dirty_after=(".lane-j-scratch/",),
                files_touched_in_window=3,
                newest_mtime_utc=None,
                worktree_dirs_present=0,
                note="foreign writer active",
                path=str(tmp_path / "repo"),
            )
        )

    monkeypatch.setattr(writer_mod, "assert_quiescent", _busy)
    _seed_candidates(db_path, {"model": 1})
    monkeypatch.setattr(run_mod, "_make_client", lambda ctx: (None, "offline test"))
    report = run_pipeline(
        "demo", **_kwargs(tmp_path, config_dir, db_path, doctor_report=_doctor(True))
    )
    assert report.window_sealed is False
    assert any("quiescent" in d for d in report.degradations)
    assert report.exit_code == EXIT_DEGRADED


# --------------------------------------------------------------------------- #
# Exit-code mapping (the whole table)
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize(
    "state,expected",
    [
        ("ok", EXIT_OK),
        ("degraded", EXIT_DEGRADED),
        ("hard_down", EXIT_HARD_DOWN),
        ("nothing_runnable", EXIT_NOTHING_RUNNABLE),
    ],
)
def test_exit_code_mapping_table(state, expected):
    """0 ok / 1 degraded / 2 hard-down / 3 nothing-runnable — deterministically."""
    ok = StageResult(name="graph", status="ok")
    blocked = StageResult(name="mine", status="blocked", reason="endpoint down")
    skipped = StageResult(name="claims", status="skipped", reason="nothing to do")
    if state == "ok":
        code = exit_code_for(stages=[ok], degradations=[])
    elif state == "degraded":
        code = exit_code_for(stages=[ok, blocked], degradations=["mine: blocked"])
    elif state == "hard_down":
        code = exit_code_for(preflight_failed=True, stages=[], degradations=[])
    else:
        code = exit_code_for(stages=[blocked, skipped], degradations=["nothing ran"])
    assert code == expected
    assert (EXIT_OK, EXIT_DEGRADED, EXIT_HARD_DOWN, EXIT_NOTHING_RUNNABLE) == (0, 1, 2, 3)


def test_exit_code_preflight_beats_nothing_runnable():
    assert exit_code_for(preflight_failed=True, stages=[]) == EXIT_HARD_DOWN
    assert exit_code_for(stages=[]) == EXIT_NOTHING_RUNNABLE
    assert exit_code_for(stages=[], dry_run=True) == EXIT_OK
    assert exit_code_for(stages=[StageResult(name="assess", status="blocked")]) == (
        EXIT_NOTHING_RUNNABLE
    )


def test_every_blocked_stage_is_reported_and_degrades(tmp_path, config_dir, db_path):
    """All stages blocked/skipped ⇒ 3 (nothing runnable), never 0."""
    report = run_pipeline(
        "demo",
        **_kwargs(
            tmp_path,
            config_dir,
            db_path,
            stage_impls={
                name: (lambda ctx, _n=name: StageResult(name=_n, status="skipped", reason="n/a"))
                for name in STAGE_ORDER
            },
        ),
    )
    assert report.exit_code == EXIT_NOTHING_RUNNABLE == 3


# --------------------------------------------------------------------------- #
# dry run
# --------------------------------------------------------------------------- #


def test_dry_run_writes_nothing_and_plans_the_stages(tmp_path, config_dir, db_path):
    """dry_run: preflight + plan, zero writes (no run dir, store untouched)."""
    _seed_candidates(db_path, {"replay": 4})
    before = hashlib.sha256(db_path.read_bytes()).hexdigest()
    run_root = tmp_path / "run"

    report = run_pipeline(
        "demo",
        **_kwargs(
            tmp_path,
            config_dir,
            db_path,
            dry_run=True,
            run_root=run_root,
            stage_impls={},  # the real implementations, in dry-run mode
        ),
    )

    assert not run_root.exists(), "a dry run must not create the run directory"
    after = hashlib.sha256(db_path.read_bytes()).hexdigest()
    assert before == after, "a dry run must not write the store"
    assert len(report.stages) == len(STAGE_ORDER)
    assert report.exit_code == EXIT_OK
    assert report.window_sealed is False
    for stage in report.stages:
        assert stage.status in {"skipped", "blocked"}
    graph_stage = report.stage("graph")
    assert "dry run" in graph_stage.reason
    assert report.producer_gate["by_producer"] == {"replay": 4}
    assert report.stage("mine").status == "blocked"


def test_core_leg_no_selected_stage_needs_is_a_degradation_not_fatal(
    tmp_path, config_dir, db_path, clean_preflight, monkeypatch
):
    """A down core leg the run would not have used must not refuse the run."""
    monkeypatch.setattr(run_mod, "_make_client", lambda ctx: (None, "offline test"))
    report = run_pipeline(
        "demo",
        **_kwargs(
            tmp_path,
            config_dir,
            db_path,
            doctor_report=_doctor(False, extra_down=("dashboard port",)),
        ),
    )
    assert report.preflight["ok"] is True
    assert report.exit_code != EXIT_HARD_DOWN
    assert "dashboard port" in report.preflight["degradable_core_down"]
    assert any("dashboard port" in d for d in report.degradations)


def test_unknown_stage_is_refused(tmp_path, config_dir, db_path):
    with pytest.raises(ValueError) as excinfo:
        run_pipeline("demo", **_kwargs(tmp_path, config_dir, db_path, stages=["nope"]))
    assert "unknown stage" in str(excinfo.value)


def test_stage_result_rejects_an_invented_status():
    with pytest.raises(ValueError):
        StageResult(name="mine", status="fine")
    for status in ("ok", "blocked", "skipped", "degraded", "failed"):
        assert StageResult(name="mine", status=status).status == status


# --------------------------------------------------------------------------- #
# U8.5 guard (a): the dry run's plan matches what the real run actually does
# --------------------------------------------------------------------------- #


def _graph_fixture(tmp_path: Path) -> Path:
    """A tiny but real ``graph.json`` at the path ``_graph_candidates`` probes."""
    graph = tmp_path / "state" / "kg" / "demo" / "graphify-out" / "graph.json"
    graph.parent.mkdir(parents=True, exist_ok=True)
    graph.write_text(
        json.dumps(
            {
                "nodes": [{"id": "n1", "source_file": "src/a.py", "type": "file"}],
                "links": [{"source": "n1", "target": "n1"}],
            }
        ),
        encoding="utf-8",
    )
    return graph


def test_plan_matches_run_for_the_graph_stage(
    tmp_path, config_dir, db_path, target_repo, monkeypatch
):
    """RED→GREEN guard (a) U8.5: the plan predicts the graph stage's real decision.

    With a usable graph on disk the real run *reuses* it; before the fix the dry
    run nonetheless planned ``would run `graphify extract``` — it described an
    action the run never takes.  Reverting the dry-run branch fails here:
    ``AssertionError: dry run planned mode='build', real run used mode='reuse'``.
    sha256 of ``src/resextract/run.py`` before/after the revert-restore cycle:
    ``18d8bc328a0ec8c3c667622dca16f8f5f7274af25edb08830f398ad6003cc8a1``.
    """
    _seed_candidates(db_path, {"replay": 2})
    monkeypatch.chdir(tmp_path)
    graph = _graph_fixture(tmp_path)
    sha_before = hashlib.sha256(db_path.read_bytes()).hexdigest()
    fakes = {name: _ALL_OK[name] for name in ("staging", "refresh")}

    dry = run_pipeline(
        "demo", **_kwargs(tmp_path, config_dir, db_path, dry_run=True, stage_impls=dict(fakes))
    )
    # the dry run writes nothing: no run dir, store untouched, target clean
    assert not (tmp_path / "run").exists()
    assert hashlib.sha256(db_path.read_bytes()).hexdigest() == sha_before
    assert _git(target_repo, "status", "--porcelain") == ""

    real = run_pipeline(
        "demo", **_kwargs(tmp_path, config_dir, db_path, stage_impls=dict(fakes))
    )

    dry_graph = dry.stage("graph")
    real_graph = real.stage("graph")
    assert dry_graph.counts.get("mode") == real_graph.counts.get("mode") == "reuse", (
        f"dry run planned mode={dry_graph.counts.get('mode')!r}, "
        f"real run used mode={real_graph.counts.get('mode')!r}"
    )
    assert dry_graph.counts["nodes"] == real_graph.counts["nodes"] == 1
    assert dry_graph.counts["sha256"] == real_graph.counts["sha256"]
    assert "would reuse" in dry_graph.reason
    assert "would run" not in dry_graph.reason
    assert str(graph.name) in real_graph.reason
    assert _git(target_repo, "status", "--porcelain") == ""


# --------------------------------------------------------------------------- #
# U8.5 guard (b): the run-scoped copy is clean, self-contained, consistent
# --------------------------------------------------------------------------- #


def test_run_leaves_a_clean_self_contained_store_copy(
    tmp_path, config_dir, db_path, target_repo
):
    """RED→GREEN guard (b) U8.5: one self-contained copy, no sidecars.

    The backup API copies the source's WAL header, so the run-scoped copy used to
    be a WAL database: any connection a stage leaves open (the real
    ``materialize``/``review`` modules call ``store.connect(ctx.db_path)``) kept
    ``state.sqlite-wal``/``-shm`` alive after the run.  The copy is now written
    into a rollback journal and finalised, so it opens read-only, passes
    ``PRAGMA integrity_check``, matches the source's row counts — and leaves no
    sidecars even with a connection deliberately leaked.  Reverting the journal
    switch fails here: ``AssertionError: sidecars left behind:
    ['state.sqlite-shm', 'state.sqlite-wal']``.  sha256 of
    ``src/resextract/run.py`` before/after: ``18d8bc328a0ec8c3c667622dca16f8f5f7274af25edb08830f398ad6003cc8a1``.
    """
    _seed_candidates(db_path, {"replay": 2})
    leaked: list = []

    def _leaky(ctx) -> StageResult:
        # what refresh/review/materialize really do: connect to the run store
        # and read it — a bare open never touches the file, but a real stage's
        # read is what materialises the -wal/-shm companions of a WAL copy.
        con = store.connect(ctx.db_path)
        con.execute("SELECT COUNT(*) FROM candidates").fetchone()
        leaked.append(con)
        return StageResult(name="lanes", status="ok", reason="leaky fake")

    impls = dict(_FAKE_NO_MODEL)
    impls["lanes"] = _leaky

    report = run_pipeline(
        "demo", **_kwargs(tmp_path, config_dir, db_path, stage_impls=impls)
    )
    copy = tmp_path / "run" / "demo" / "state.sqlite"
    assert copy.is_file(), "the run must leave its run-scoped copy"
    sidecars = sorted(p.name for p in copy.parent.glob("state.sqlite-*"))
    assert sidecars == [], f"sidecars left behind: {sidecars}"

    con = sqlite3.connect(f"file:{copy}?mode=ro", uri=True)
    try:
        assert con.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
        tabs = [
            r[0]
            for r in con.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
        ]
        copy_counts = {
            t: con.execute(f'SELECT COUNT(*) FROM "{t}"').fetchone()[0] for t in tabs
        }
    finally:
        con.close()
    src = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    try:
        stabs = [
            r[0]
            for r in src.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
        ]
        src_counts = {
            t: src.execute(f'SELECT COUNT(*) FROM "{t}"').fetchone()[0] for t in stabs
        }
    finally:
        src.close()
    assert copy_counts == src_counts, "the copy must match the source it was taken from"
    assert report.exit_code == EXIT_DEGRADED == 1
    assert _git(target_repo, "status", "--porcelain") == "", "target must stay untouched"
    for con_leak in leaked:
        con_leak.close()


# --------------------------------------------------------------------------- #
# U8.5 finding 3: ok/status are derived from exit_code — they cannot disagree
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize(
    "code, word",
    [
        (EXIT_OK, "ok"),
        (EXIT_DEGRADED, "degraded"),
        (EXIT_HARD_DOWN, "hard_down"),
        (EXIT_NOTHING_RUNNABLE, "nothing_runnable"),
    ],
)
def test_ok_and_status_cannot_disagree_with_exit_code(code, word):
    """The machine-readable status is a pure function of ``exit_code``.

    ``ok``/``status`` are *properties* — not stored fields — computed from the
    same ``exit_code`` that ``exit_code_for`` produced, so a machine consumer can
    read either without any chance of disagreement.  ``status_for`` covers all
    four genuinely reachable codes.
    """
    assert run_mod.EXIT_STATUS == {
        0: "ok",
        1: "degraded",
        2: "hard_down",
        3: "nothing_runnable",
    }
    report = run_mod.RunReport(target="demo", exit_code=code)
    assert report.status == word == run_mod.status_for(code)
    assert report.ok is (code == EXIT_OK)
    payload = report.as_dict()
    assert payload["exit_code"] == code
    assert payload["status"] == report.status
    assert payload["ok"] == report.ok
    # neither is stored, so nothing can drift away from the exit code
    stored = {f.name for f in dataclasses.fields(run_mod.RunReport)}
    assert "ok" not in stored and "status" not in stored


# --------------------------------------------------------------------------- #
# U8.6 guards (e) and (f): an unusable graph is not a reuse; planned_out is real
# --------------------------------------------------------------------------- #

_WORKSPACE = Path(__file__).resolve().parents[1]
_GENUINE_GRAPH = _WORKSPACE / "state" / "kg" / "duval" / "graphify-out" / "graph.json"
_GENUINE_SHA = (
    "4790bbb1111b76ea7cfb8024a98cfb3ec8c4b038beb23f6e5b6fa729fcdd897b"
)
_GENUINE_SHA12 = _GENUINE_SHA[:12]  # display abbreviation (_graph_digest is full, U8.11)

#: Every shape of "found at the candidate path, but not a usable graph".
_UNUSABLE_CASES = (
    "0-byte",
    "garbage",
    "empty-object",
    "zero-nodes",
    "directory",
    "dangling-symlink",
    "absent",
)


class _FakeGraphify:
    """Writes the artifact ``extract --out`` would write, without running graphify."""

    last_artifact: Path | None = None

    def __init__(self, cwd=None, timeout=None):
        self.cwd, self.timeout = cwd, timeout

    @staticmethod
    def graph_json(out_dir):
        return Path(out_dir) / "graphify-out" / "graph.json"

    def extract(self, target, *, code_only=False, out=None, token_budget=None, no_viz=False):
        artifact = self.graph_json(out)
        artifact.parent.mkdir(parents=True, exist_ok=True)
        artifact.write_text(
            json.dumps(
                {
                    "nodes": [
                        {"id": "built-1", "source_file": "src/built.py", "type": "file"}
                    ],
                    "links": [{"source": "built-1", "target": "built-1"}],
                }
            ),
            encoding="utf-8",
        )
        _FakeGraphify.last_artifact = artifact
        return SimpleNamespace(ok=True)


def _make_unusable_case(root: Path, case: str) -> Path:
    """Create the candidate path in the shape ``case`` and return it."""
    cand = root / "state" / "kg" / "demo" / "graph.json"
    cand.parent.mkdir(parents=True, exist_ok=True)
    if case == "0-byte":
        cand.write_bytes(b"")
    elif case == "garbage":
        cand.write_text("not json at all {{{", encoding="utf-8")
    elif case == "empty-object":
        cand.write_text("{}", encoding="utf-8")
    elif case == "zero-nodes":
        cand.write_text(json.dumps({"nodes": [], "links": []}), encoding="utf-8")
    elif case == "directory":
        cand.mkdir()
    elif case == "dangling-symlink":
        cand.symlink_to(cand.parent / "missing.json")
    elif case == "absent":
        pass
    else:  # pragma: no cover - guards a typo in the parametrisation
        raise AssertionError(f"unknown case {case!r}")
    return cand


def _graph_run(tmp_path, config_dir, db_path, *, dry_run, monkeypatch):
    """A pipeline run whose graph stage is REAL, with only graphify faked."""
    fakes = {name: _ALL_OK[name] for name in ("staging", "refresh")}
    return run_pipeline(
        "demo",
        **_kwargs(
            tmp_path,
            config_dir,
            db_path,
            dry_run=dry_run,
            stage_impls=dict(fakes),
        ),
    )


@pytest.mark.parametrize("case", _UNUSABLE_CASES)
def test_unusable_graph_is_never_reused_and_never_ok_with_zero_nodes(
    case, tmp_path, config_dir, db_path, target_repo, monkeypatch
):
    """RED→GREEN guard (e) U8.6: a found-but-unusable graph is not a reuse.

    Before the fix ``_reuse_candidate`` accepted *any* existing file, so a
    0-byte graph, garbage bytes, ``{}`` or ``{"nodes": []}`` was reused and the
    stage returned ``status="ok", nodes=0`` — an empty graph reported as
    success, with staging, lanes and materialize then running on nothing.
    Revert the validity check in ``_reuse_candidate`` (back to
    ``if candidate.is_file(): return candidate``) and this test fails on the
    0-byte case with ``AssertionError: ... unusable 0-byte candidate was not
    planned/built`` and the old ``status='ok' nodes=0`` shape.

    sha256 of ``src/resextract/run.py`` before/after the revert-restore cycle is
    bit-identical (``cmp`` clean, FULL ``__pycache__`` purge, no bytecode).
    """
    monkeypatch.chdir(tmp_path)
    _seed_candidates(db_path, {"replay": 1})
    cand = _make_unusable_case(tmp_path, case)
    monkeypatch.setattr("resextract.kg.Graphify", _FakeGraphify)

    dry = _graph_run(tmp_path, config_dir, db_path, dry_run=True, monkeypatch=monkeypatch)
    real = _graph_run(tmp_path, config_dir, db_path, dry_run=False, monkeypatch=monkeypatch)

    for label, report in (("plan", dry), ("run", real)):
        stage = report.stage("graph")
        assert stage.counts.get("mode") == "build", (
            f"{label}: unusable {case} candidate was not planned/built: {stage.as_dict()}"
        )
        assert not (
            stage.status == "ok" and int(stage.counts.get("nodes", 0) or 0) == 0
        ), f"{label}: {case} reported success on an empty graph: {stage.as_dict()}"

    # plan and run agree about the mode — the one shared decision function
    assert dry.stage("graph").counts["mode"] == real.stage("graph").counts["mode"] == "build"
    assert real.stage("graph").status == "ok"
    assert int(real.stage("graph").counts["nodes"]) >= 1

    # the bad file is reported and left in place — never silently removed
    if case != "absent":
        # the decision function reports the path as _graph_candidates named it
        # (relative to the run's cwd, which is tmp_path here)
        rel = str(cand.relative_to(Path.cwd()))
        assert any(rel in n for n in real.notes), real.notes
        assert any(
            rel in entry.get("path", "")
            for entry in real.stage("graph").counts["rejected_candidates"]
        )
        if case == "dangling-symlink":
            assert cand.is_symlink()
        else:
            assert cand.exists()
    # nothing was written into the target
    assert _git(target_repo, "status", "--porcelain") == ""


def test_build_plan_names_the_path_the_artifact_really_lands_at(
    tmp_path, config_dir, db_path, target_repo, monkeypatch
):
    """RED→GREEN guard (f) U8.6: ``planned_out`` is the artifact's real path.

    The build branch used to record ``<run_dir>/kg/graph.json`` while
    ``graphify extract --out`` writes ``<run_dir>/kg/graphify-out/graph.json``
    (``Graphify.graph_json``).  This asserts the plan against the artifact the
    real run actually produced — not a string literal — so the two cannot
    drift.  Revert ``planned = str(Graphify.graph_json(out_dir))`` to
    ``planned = str(out_dir / "graph.json")`` and this fails with
    ``AssertionError: plan says .../kg/graph.json, artifact landed at
    .../kg/graphify-out/graph.json``.

    sha256 of ``src/resextract/run.py`` before/after the revert-restore cycle is
    bit-identical (``cmp`` clean, FULL ``__pycache__`` purge, no bytecode).
    """
    monkeypatch.chdir(tmp_path)
    _seed_candidates(db_path, {"replay": 1})
    _make_unusable_case(tmp_path, "absent")  # no candidate: the plan must build
    monkeypatch.setattr("resextract.kg.Graphify", _FakeGraphify)

    dry = _graph_run(tmp_path, config_dir, db_path, dry_run=True, monkeypatch=monkeypatch)
    real = _graph_run(tmp_path, config_dir, db_path, dry_run=False, monkeypatch=monkeypatch)

    planned = Path(dry.stage("graph").counts["planned_out"])
    artifact = Path(real.stage("graph").artifacts[0])
    assert planned == artifact, f"plan says {planned}, artifact landed at {artifact}"
    assert artifact.is_file(), "the plan named a path where no artifact exists"
    assert artifact.parent.name == "graphify-out"
    assert artifact.name == "graph.json"
    assert planned != artifact.parent.parent / "graph.json"
    assert _git(target_repo, "status", "--porcelain") == ""


@pytest.mark.skipif(not _GENUINE_GRAPH.is_file(), reason="authoritative graph not present")
def test_genuine_graph_is_still_reused_by_plan_and_run(
    tmp_path, config_dir, db_path, target_repo, monkeypatch
):
    """The control: the authoritative graph *is* usable, so reuse survives.

    A validity rule that rejected the genuine artifact would be worse than the
    bug.  The repo's 3,188,231-byte, 2685-node graph (sha256 prefix
    ``4790bbb1111b``, mtime 05:26, 7102 links, no top-level ``communities``)
    is symlinked to the candidate path and must still be reused by plan and run
    alike, with real counts — proving ``communities`` is correctly optional.
    """
    monkeypatch.chdir(tmp_path)
    _seed_candidates(db_path, {"replay": 1})
    cand = tmp_path / "state" / "kg" / "demo" / "graph.json"
    cand.parent.mkdir(parents=True, exist_ok=True)
    cand.symlink_to(_GENUINE_GRAPH)
    monkeypatch.setattr("resextract.kg.Graphify", _FakeGraphify)  # must not be called

    dry = _graph_run(tmp_path, config_dir, db_path, dry_run=True, monkeypatch=monkeypatch)
    real = _graph_run(tmp_path, config_dir, db_path, dry_run=False, monkeypatch=monkeypatch)

    for report in (dry, real):
        stage = report.stage("graph")
        assert stage.counts["mode"] == "reuse", stage.as_dict()
        assert stage.counts["nodes"] == 2685
        assert stage.counts["edges"] == 7102
        assert stage.counts["sha256"] == _GENUINE_SHA  # full 64 hex (U8.11 item 2)
        assert stage.counts.get("rejected_candidates", []) == []
    assert real.stage("graph").status == "ok"
    assert dry.stage("graph").status == "skipped"
    assert _git(target_repo, "status", "--porcelain") == ""


def test_plan_and_run_share_the_single_reuse_decision(
    tmp_path, config_dir, db_path, target_repo, monkeypatch
):
    """One decision function: both plan and run call ``_reuse_candidate``.

    If a second validity check were added in only one path, the dry run and the
    real run would disagree about an unusable candidate; the spy proves the
    shared function is the one both report through (it is called twice and both
    callers see the same ``None``).
    """
    monkeypatch.chdir(tmp_path)
    _seed_candidates(db_path, {"replay": 1})
    _make_unusable_case(tmp_path, "zero-nodes")
    monkeypatch.setattr("resextract.kg.Graphify", _FakeGraphify)

    seen: list[Path | None] = []
    real_decision = run_mod._reuse_candidate

    def spy(ctx):
        decision = real_decision(ctx)
        seen.append(decision)
        return decision

    monkeypatch.setattr(run_mod, "_reuse_candidate", spy)
    _graph_run(tmp_path, config_dir, db_path, dry_run=True, monkeypatch=monkeypatch)
    _graph_run(tmp_path, config_dir, db_path, dry_run=False, monkeypatch=monkeypatch)
    assert seen == [None, None], f"decision function returned {seen}"


# --------------------------------------------------------------------------- #
# U8.7 guards (g) and (h): provenance is recorded, staleness is reported
# --------------------------------------------------------------------------- #
#
# Guard (g) — the staleness-report guard.  Before the fix ``_reuse_candidate``
# and ``_stage_graph`` never looked at ``built_at_commit``, so a graph built for
# a *different* revision of the target was reused with nothing in the plan or
# the run to say so.  Revert the provenance clause (drop the
# ``provenance = _graph_provenance(...)`` line and the ``_provenance_stamp``
# clause from the reuse branch) and
# ``test_stale_graph_is_reported_stale_by_plan_and_run`` fails with
# ``AssertionError: plan: {'mode': 'reuse', ...}`` / ``KeyError: 'provenance'``
# — the stale graph is reused silently again.
#
# Guard (h) — the missing-provenance guard.  Before the fix a graph carrying no
# recorded commit at all was presented exactly like a fresh one.  Revert the
# ``unverified`` branch of ``_graph_provenance`` (return ``fresh`` when nothing
# is recorded) and ``test_unrecorded_provenance_is_reported_unverified_not_fresh``
# fails with ``AssertionError: plan: unrecorded provenance was reported 'fresh'``.
#
# Both reverted-restored under ``PYTHONDONTWRITEBYTECODE=1`` with a FULL
# ``__pycache__`` purge between every revert and restore; restore was
# ``cmp``-clean and sha256 bit-identical (hashes in ``orchestration/handoffs/U8.7.json``).


def _graph_with_head(root: Path, *, built_at_head: str | None, nodes: int = 1) -> Path:
    """A usable graph at the candidate path, optionally carrying provenance."""
    cand = root / "state" / "kg" / "demo" / "graph.json"
    cand.parent.mkdir(parents=True, exist_ok=True)
    doc: dict = {
        "graph": {"schema_version": 1, "graphify_version": "0.9.80"},
        "nodes": [
            {"id": f"n{i}", "source_file": "src/x.py", "type": "file"} for i in range(nodes)
        ],
        "links": [{"source": "n0", "target": "n0"}],
    }
    if built_at_head is not None:
        doc["built_at_commit"] = built_at_head
    cand.write_text(json.dumps(doc), encoding="utf-8")
    return cand


def _real_graph_run(tmp_path, config_dir, db_path, *, dry_run, **over):
    """The graph stage is REAL here (only staging/refresh are faked)."""
    fakes = {name: _ALL_OK[name] for name in ("staging", "refresh")}
    return run_pipeline(
        "demo",
        **_kwargs(
            tmp_path, config_dir, db_path, dry_run=dry_run, stage_impls=dict(fakes), **over
        ),
    )


def test_stale_graph_is_reported_stale_by_plan_and_run(
    tmp_path, config_dir, db_path, target_repo, monkeypatch
):
    """RED→GREEN guard (g) U8.7: a valid-but-stale graph is no longer silent.

    The graph records ``built_at_commit = 40 * 'f'`` while the target's HEAD is
    the fixture repo's real commit, so it describes a revision that does not
    exist — the residual V8B named.  Both the plan and the run must say so, in
    the same words, and neither may describe a graphify build.  Reverting the
    provenance clause makes both stop reporting ``provenance``/``STALE`` and
    this test fails.
    """
    monkeypatch.chdir(tmp_path)
    _seed_candidates(db_path, {"replay": 1})
    head = _git(target_repo, "rev-parse", "HEAD")
    _graph_with_head(tmp_path, built_at_head="f" * 40)
    monkeypatch.setattr("resextract.kg.Graphify", _FakeGraphify)

    dry = _real_graph_run(tmp_path, config_dir, db_path, dry_run=True)
    real = _real_graph_run(tmp_path, config_dir, db_path, dry_run=False)

    stamp = f"built at {'f' * 12}, target head {head[:12]} — STALE"
    for label, report in (("plan", dry), ("run", real)):
        stage = report.stage("graph")
        assert stage.counts["mode"] == "reuse", f"{label}: {stage.as_dict()}"
        prov = stage.counts["provenance"]
        assert prov["state"] == "stale", f"{label}: {prov}"
        assert prov["built_at_head"] == "f" * 40, f"{label}: {prov}"
        assert prov["observed_target_head"] == head, f"{label}: {prov}"
        assert prov["tool_version"] == "0.9.80", f"{label}: {prov}"
        assert prov["built_at"] is None, f"{label}: a timestamp was invented: {prov}"
        assert int(prov["nodes"]) >= 1 and int(prov["edges"]) >= 1, f"{label}: {prov}"
        assert stamp in stage.reason, f"{label}: {stage.reason}"
        assert "would run" not in stage.reason, stage.reason

    # plan and run agree — one decision function, one graph line
    assert (
        dry.stage("graph").counts["provenance"]
        == real.stage("graph").counts["provenance"]
    )
    assert any("stale" in n for n in real.notes), real.notes
    assert _git(target_repo, "status", "--porcelain") == ""


def test_fresh_graph_is_not_cried_wolf_over(
    tmp_path, config_dir, db_path, target_repo, monkeypatch
):
    """The control: matching provenance is reported ``fresh``, with no warning."""
    monkeypatch.chdir(tmp_path)
    _seed_candidates(db_path, {"replay": 1})
    head = _git(target_repo, "rev-parse", "HEAD")
    _graph_with_head(tmp_path, built_at_head=head)
    monkeypatch.setattr("resextract.kg.Graphify", _FakeGraphify)

    dry = _real_graph_run(tmp_path, config_dir, db_path, dry_run=True)
    real = _real_graph_run(tmp_path, config_dir, db_path, dry_run=False)

    for label, report in (("plan", dry), ("run", real)):
        stage = report.stage("graph")
        assert stage.counts["mode"] == "reuse", f"{label}: {stage.as_dict()}"
        prov = stage.counts["provenance"]
        assert prov["state"] == "fresh", f"{label}: {prov}"
        assert "STALE" not in stage.reason, stage.reason
        assert "UNVERIFIED" not in stage.reason, stage.reason
        assert not any("stale" in n for n in report.notes), report.notes
    assert (
        dry.stage("graph").counts["provenance"]
        == real.stage("graph").counts["provenance"]
    )


def test_unrecorded_provenance_is_reported_unverified_not_fresh(
    tmp_path, config_dir, db_path, target_repo, monkeypatch
):
    """RED→GREEN guard (h) U8.7: no provenance is *unverified*, never fresh.

    The authoritative artifact in this repo records ``built_at_commit``, but a
    graph from an older graphify (or another writer) need not.  Missing
    provenance is not evidence of freshness: it is neither trusted as fresh nor
    refused — it is reused and reported ``UNVERIFIED``.  Reverting the
    ``unverified`` branch of ``_graph_provenance`` makes ``state`` read
    ``fresh`` and this test fails.
    """
    monkeypatch.chdir(tmp_path)
    _seed_candidates(db_path, {"replay": 1})
    _graph_with_head(tmp_path, built_at_head=None)
    monkeypatch.setattr("resextract.kg.Graphify", _FakeGraphify)

    dry = _real_graph_run(tmp_path, config_dir, db_path, dry_run=True)
    real = _real_graph_run(tmp_path, config_dir, db_path, dry_run=False)

    for label, report in (("plan", dry), ("run", real)):
        stage = report.stage("graph")
        assert stage.counts["mode"] == "reuse", f"{label}: {stage.as_dict()}"
        prov = stage.counts["provenance"]
        assert prov["state"] != "fresh", (
            f"{label}: unrecorded provenance was reported {prov['state']!r}"
        )
        assert prov["state"] == "unverified", f"{label}: {prov}"
        assert prov["built_at_head"] is None and prov["built_at"] is None, f"{label}: {prov}"
        assert "UNVERIFIED" in stage.reason, stage.reason
        assert "STALE" not in stage.reason, stage.reason
    assert any(n.startswith("graph: reuse provenance unverified") for n in real.notes), real.notes
    assert _git(target_repo, "status", "--porcelain") == ""


def test_require_fresh_graph_refuses_a_stale_graph_behind_the_flag(
    tmp_path, config_dir, db_path, target_repo, monkeypatch
):
    """The opt-in: with ``require_fresh_graph`` a stale graph is passed over.

    The default (flag absent) is report-only reuse — never a silent rebuild.
    With the flag the shared decision function refuses the stale candidate,
    reports it (``rejected_candidates``, reason starting ``stale``), leaves the
    artifact on disk untouched, and the stage builds instead.  Plan and run
    agree on ``mode=build``.
    """
    monkeypatch.chdir(tmp_path)
    _seed_candidates(db_path, {"replay": 1})
    cand = _graph_with_head(tmp_path, built_at_head="f" * 40)
    monkeypatch.setattr("resextract.kg.Graphify", _FakeGraphify)

    dry = _real_graph_run(
        tmp_path, config_dir, db_path, dry_run=True, require_fresh_graph=True
    )
    real = _real_graph_run(
        tmp_path, config_dir, db_path, dry_run=False, require_fresh_graph=True
    )

    for label, report in (("plan", dry), ("run", real)):
        stage = report.stage("graph")
        assert stage.counts["mode"] == "build", f"{label}: {stage.as_dict()}"
        reasons = " ".join(
            str(e.get("reason", "")) for e in stage.counts.get("rejected_candidates", [])
        )
        assert "stale" in reasons, f"{label}: {stage.as_dict()}"
    assert real.stage("graph").status == "ok"
    assert dry.stage("graph").counts["mode"] == real.stage("graph").counts["mode"]
    # refused, reported — never deleted, never rewritten
    assert cand.is_file()
    assert json.loads(cand.read_text(encoding="utf-8"))["built_at_commit"] == "f" * 40
    assert any("stale" in n for n in real.notes), real.notes
    assert _git(target_repo, "status", "--porcelain") == ""


def test_require_fresh_graph_decision_is_the_single_shared_function(
    tmp_path, config_dir, db_path, target_repo, monkeypatch
):
    """The flag lives inside ``_reuse_candidate``, so both callers see it.

    The spy pins exactly two calls (plan + run) and both must return ``None``
    for the same provably stale graph: if the flag were applied in only one
    path, plan and run would disagree about reusing it.
    """
    monkeypatch.chdir(tmp_path)
    _seed_candidates(db_path, {"replay": 1})
    _graph_with_head(tmp_path, built_at_head="f" * 40)
    monkeypatch.setattr("resextract.kg.Graphify", _FakeGraphify)

    seen: list[Path | None] = []
    real_decision = run_mod._reuse_candidate

    def spy(ctx):
        decision = real_decision(ctx)
        seen.append(decision)
        return decision

    monkeypatch.setattr(run_mod, "_reuse_candidate", spy)
    dry = _real_graph_run(
        tmp_path, config_dir, db_path, dry_run=True, require_fresh_graph=True
    )
    real = _real_graph_run(
        tmp_path, config_dir, db_path, dry_run=False, require_fresh_graph=True
    )
    assert seen == [None, None], f"decision function returned {seen}"
    assert dry.stage("graph").counts["mode"] == real.stage("graph").counts["mode"] == "build"


# --------------------------------------------------------------------------- #
# U8.8 guards (i) and (j): the artifact's BYTES are pinned OUTSIDE the artifact
#
# ``graph.json`` records ``built_at_commit`` but has no ``sha256`` field at all,
# and a digest written *inside* the artifact cannot vouch for it: the same
# writer writes both, so whoever alters the bytes can rewrite the digest.  U8.8
# pins the expected sha256 in a committed ``config/graph_pin.toml`` and evaluates
# it inside ``_reuse_candidate`` — the one decision function plan and run share.
#
# RED→GREEN evidence (sha256 of ``src/resextract/run.py`` before/after each
# revert-restore cycle: ``78c989a0a3307375959a5d03593b2e28518530f2bfab9a8db488e1e327f866c0``); see the two guard docstrings below.
# Both cycles ran under ``PYTHONDONTWRITEBYTECODE=1`` with a FULL ``__pycache__``
# purge between every revert and restore; restore was ``cmp``-clean and sha256
# bit-identical.
# --------------------------------------------------------------------------- #


def _pin(tmp_path: Path, *, rel: str, sha256: str | None) -> Path:
    """Write a committed-style pin under ``tmp_path/config`` (or remove it)."""
    cfg = tmp_path / "config"
    cfg.mkdir(parents=True, exist_ok=True)
    pin = cfg / "graph_pin.toml"
    if sha256 is None:
        pin.unlink(missing_ok=True)
        return pin
    pin.write_text(
        f'version = 1\n\n[graphs."{rel}"]\nsha256 = "{sha256}"\n', encoding="utf-8"
    )
    return pin


def _file_sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _digest_rejections(report) -> str:
    stage = report.stage("graph")
    assert stage is not None, report.as_dict()
    return " ".join(
        str(e.get("reason", "")) for e in stage.counts.get("rejected_candidates", [])
    )


def test_tampered_bytes_are_refused_when_the_pin_disagrees(
    tmp_path, config_dir, db_path, target_repo, monkeypatch
):
    """RED→GREEN guard (i) U8.8: a pinned graph whose BYTES changed is not reused.

    The graph records the target's real HEAD but its bytes hash to something the
    committed pin does not name — corruption or tampering, a *stronger* signal
    than staleness (a stale graph is honestly out of date; a mismatched digest
    means the bytes are not the bytes that were pinned).  By default it is
    unusable: plan and run both pass it over, say ``digest mismatch`` loudly in
    notes and ``rejected_candidates``, agree on ``mode == "build"``, and leave
    the refused file byte-identical on disk (never deleted, never rewritten).

    Reverting the fix (never consult the pin, i.e. ``pin = None``) makes the
    current code report ``mode == "reuse"`` for tampered bytes and this test
    fails with ``AssertionError: plan: a tampered graph was reused: {'mode':
    'reuse', ...}``.  sha256 of ``src/resextract/run.py`` before/after the
    revert-restore cycle: ``78c989a0a3307375959a5d03593b2e28518530f2bfab9a8db488e1e327f866c0`` (``cmp``-clean, bit-identical), full
    ``__pycache__`` purge + ``PYTHONDONTWRITEBYTECODE=1``.
    """
    monkeypatch.chdir(tmp_path)
    _seed_candidates(db_path, {"replay": 1})
    head = _git(target_repo, "rev-parse", "HEAD")
    cand = _graph_with_head(tmp_path, built_at_head=head, nodes=3)
    before = _file_sha(cand)
    _pin(tmp_path, rel="state/kg/demo/graph.json", sha256="0" * 64)  # not these bytes
    monkeypatch.setattr("resextract.kg.Graphify", _FakeGraphify)

    dry = _real_graph_run(tmp_path, config_dir, db_path, dry_run=True)
    real = _real_graph_run(tmp_path, config_dir, db_path, dry_run=False)

    for label, report in (("plan", dry), ("run", real)):
        stage = report.stage("graph")
        assert stage.counts["mode"] == "build", (
            f"{label}: a tampered graph was reused: {stage.as_dict()}"
        )
        assert "digest mismatch" in _digest_rejections(report), f"{label}: {report.notes}"
    assert dry.stage("graph").counts["mode"] == real.stage("graph").counts["mode"]
    assert any("digest mismatch" in n for n in real.notes), real.notes
    # refused, reported — kept on disk byte for byte, never deleted
    assert cand.is_file()
    assert _file_sha(cand) == before
    assert _git(target_repo, "status", "--porcelain") == ""


def test_matching_pin_reuses_the_graph_with_no_false_alarm(
    tmp_path, config_dir, db_path, target_repo, monkeypatch
):
    """The control: bytes that match the pin are reused, with no warning."""
    monkeypatch.chdir(tmp_path)
    _seed_candidates(db_path, {"replay": 1})
    head = _git(target_repo, "rev-parse", "HEAD")
    cand = _graph_with_head(tmp_path, built_at_head=head, nodes=2)
    digest = _file_sha(cand)
    _pin(tmp_path, rel="state/kg/demo/graph.json", sha256=digest)
    monkeypatch.setattr("resextract.kg.Graphify", _FakeGraphify)

    dry = _real_graph_run(tmp_path, config_dir, db_path, dry_run=True)
    real = _real_graph_run(tmp_path, config_dir, db_path, dry_run=False)

    clause = f"sha256 {digest[:12]} matches the pinned digest {digest[:12]}"
    for label, report in (("plan", dry), ("run", real)):
        stage = report.stage("graph")
        assert stage.counts["mode"] == "reuse", f"{label}: {stage.as_dict()}"
        prov = stage.counts["provenance"]
        assert prov["digest_state"] == "match", f"{label}: {prov}"
        assert prov["pin_sha256"] == digest, f"{label}: {prov}"
        assert prov["sha256"] == digest, f"{label}: {prov}"  # full 64 (U8.11 item 2)
        assert clause in stage.reason, f"{label}: {stage.reason}"
        assert "does not match" not in stage.reason.lower(), stage.reason
        assert "unverified" not in stage.reason.lower(), stage.reason
        assert not any("digest mismatch" in n for n in report.notes), report.notes
    # one decision, one line: the plan and the run carry the same provenance dict
    assert (
        dry.stage("graph").counts["provenance"]
        == real.stage("graph").counts["provenance"]
    )


def test_absent_pin_is_unverified_and_still_reused_never_a_hard_failure(
    tmp_path, config_dir, db_path, target_repo, monkeypatch
):
    """RED→GREEN guard (j) U8.8: a missing pin is not a hard failure.

    Pinning is an operator contract, not a preflight gate.  With no pin entry
    for the graph's path the bytes are ``unpinned``/``unverified`` — stated in
    the one shared line and in ``counts["provenance"]`` — and the graph is still
    reused exactly as before U8.8, so every existing setup keeps working.

    Reverting the fix so that *no pin* is treated as a mismatch (``_graph_pin``
    returns a bogus digest instead of ``None`` when the pin file is absent)
    makes the decision refuse a perfectly good graph and this test fails with
    ``AssertionError: plan: {'mode': 'build', ...}`` — i.e. the revert
    hard-fails a run that must proceed.  sha256 of ``src/resextract/run.py``
    before/after the revert-restore cycle: ``78c989a0a3307375959a5d03593b2e28518530f2bfab9a8db488e1e327f866c0`` (``cmp``-clean,
    bit-identical), full ``__pycache__`` purge + ``PYTHONDONTWRITEBYTECODE=1``.
    """
    monkeypatch.chdir(tmp_path)
    _seed_candidates(db_path, {"replay": 1})
    head = _git(target_repo, "rev-parse", "HEAD")
    _graph_with_head(tmp_path, built_at_head=head, nodes=1)
    _pin(tmp_path, rel="state/kg/demo/graph.json", sha256=None)  # no pin file at all
    monkeypatch.setattr("resextract.kg.Graphify", _FakeGraphify)

    dry = _real_graph_run(tmp_path, config_dir, db_path, dry_run=True)
    real = _real_graph_run(tmp_path, config_dir, db_path, dry_run=False)

    for label, report in (("plan", dry), ("run", real)):
        stage = report.stage("graph")
        assert stage.counts["mode"] == "reuse", f"{label}: {stage.as_dict()}"
        prov = stage.counts["provenance"]
        assert prov["digest_state"] == "unpinned", f"{label}: {prov}"
        assert prov["pin_sha256"] is None, f"{label}: {prov}"
        assert "no pin recorded" in stage.reason, f"{label}: {stage.reason}"
        assert "unverified" in stage.reason.lower(), f"{label}: {stage.reason}"
    assert real.stage("graph").status == "ok"
    assert _git(target_repo, "status", "--porcelain") == ""


def test_staleness_stays_report_only_with_a_matching_pin(
    tmp_path, config_dir, db_path, target_repo, monkeypatch
):
    """Staleness is unchanged: matching bytes never turn it into a refusal.

    The commit is stale (``40 * 'f'``) but the bytes match the pin, so the
    default stays report-only reuse with the ``STALE`` line — pinning the bytes
    must not silently change the policy chosen for a continuously moving target
    HEAD.  ``require_fresh_graph`` still refuses it, on the commit, not the
    digest.
    """
    monkeypatch.chdir(tmp_path)
    _seed_candidates(db_path, {"replay": 1})
    cand = _graph_with_head(tmp_path, built_at_head="f" * 40, nodes=1)
    _pin(tmp_path, rel="state/kg/demo/graph.json", sha256=_file_sha(cand))
    monkeypatch.setattr("resextract.kg.Graphify", _FakeGraphify)

    dry = _real_graph_run(tmp_path, config_dir, db_path, dry_run=True)
    stage = dry.stage("graph")
    assert stage.counts["mode"] == "reuse", stage.as_dict()
    prov = stage.counts["provenance"]
    assert prov["state"] == "stale", prov
    assert prov["digest_state"] == "match", prov
    assert "STALE" in stage.reason, stage.reason
    assert "matches the pinned digest" in stage.reason, stage.reason

    strict = _real_graph_run(
        tmp_path, config_dir, db_path, dry_run=True, require_fresh_graph=True
    )
    assert strict.stage("graph").counts["mode"] == "build", strict.stage("graph").as_dict()
    assert cand.is_file()


def test_digest_decision_is_the_single_shared_function(
    tmp_path, config_dir, db_path, target_repo, monkeypatch
):
    """The digest refusal lives inside ``_reuse_candidate``, so both callers see it.

    The spy pins exactly two calls (plan + run) and both must return ``None``
    for the same mismatched bytes: if the pin were consulted in only one path,
    plan and run would disagree about reusing a tampered graph.
    """
    monkeypatch.chdir(tmp_path)
    _seed_candidates(db_path, {"replay": 1})
    head = _git(target_repo, "rev-parse", "HEAD")
    cand = _graph_with_head(tmp_path, built_at_head=head, nodes=1)
    before = _file_sha(cand)
    _pin(tmp_path, rel="state/kg/demo/graph.json", sha256="0" * 64)
    monkeypatch.setattr("resextract.kg.Graphify", _FakeGraphify)

    seen: list[Path | None] = []
    real_decision = run_mod._reuse_candidate

    def spy(ctx):
        decision = real_decision(ctx)
        seen.append(decision)
        return decision

    monkeypatch.setattr(run_mod, "_reuse_candidate", spy)
    dry = _real_graph_run(tmp_path, config_dir, db_path, dry_run=True)
    real = _real_graph_run(tmp_path, config_dir, db_path, dry_run=False)

    assert seen == [None, None], f"decision function returned {seen}"
    assert (
        dry.stage("graph").counts["mode"]
        == real.stage("graph").counts["mode"]
        == "build"
    )
    assert _file_sha(cand) == before


# --------------------------------------------------------------------------- #
# U8.11 guards (k)-(n): closing the three V8C defects on the graph chain
#
# (k) non-object nodes were accepted (``nodes:[100k ints]`` => ``mode=reuse``,
#     ``status="ok"``, ``nodes=0``); (l) the pin was compared over only the first
#     12 hex chars (a wrong tail reported "matches the pinned digest"); (m) a
#     missing/malformed/unreadable/empty/mis-keyed pin degraded *silently* to
#     unpinned-and-reused; (n) ``require_fresh_graph`` did not refuse
#     ``unverified``.
#
# RED→GREEN evidence (sha256 of ``src/resextract/run.py`` before/after each
# revert-restore cycle: ``78c989a0a3307375959a5d03593b2e28518530f2bfab9a8db488e1e327f866c0``);
# see the guard docstrings below.  Every cycle ran under
# ``PYTHONDONTWRITEBYTECODE=1`` with a FULL ``__pycache__`` purge between every
# revert and restore; every restore was ``cmp``-clean and sha256 bit-identical to
# the fixed file
# (``78ae610127bb1de492782be23547d494086dad82c6d1d8286fdada5d28f94165``).
# The incoming (pre-U8.11) ``run.py`` was the pristine
# ``78c989a0a3307375959a5d03593b2e28518530f2bfab9a8db488e1e327f866c0``, confirmed
# byte for byte by reversing every replacement this unit applied.
# --------------------------------------------------------------------------- #


def _pin_text(tmp_path: Path, text: str | None) -> Path:
    """Write a raw pin document (or remove it) under ``tmp_path/config``."""
    cfg = tmp_path / "config"
    cfg.mkdir(parents=True, exist_ok=True)
    pin = cfg / "graph_pin.toml"
    if text is None:
        pin.unlink(missing_ok=True)
    else:
        pin.write_text(text, encoding="utf-8")
    return pin


def test_non_object_nodes_are_rejected_not_reused_as_ok_zero_nodes(
    tmp_path, config_dir, db_path, target_repo, monkeypatch
):
    """RED→GREEN guard (k) U8.11 item 1: ``nodes: [ints]`` is not a graph.

    ``nodes`` used to be checked only for non-emptiness, so a 100k-element array
    of integers parsed fine, the candidate was reused, ``graph_stats`` answered
    **0 nodes**, and the stage reported ``mode="reuse", status="ok"`` — the
    ok-with-zero-nodes signature U8.6 was meant to close, still reachable.  Now
    every element must be a JSON object, so the candidate is rejected (reported
    and kept) and the stage builds instead.

    Reverting the element walk in ``_graph_unusable_reason`` (delete the
    ``isinstance(node, dict)`` loop) makes plan and run reuse the int-array file
    and this test fails with ``AssertionError: plan: {'mode': 'reuse', ...,
    'nodes': 0, 'status': 'ok'}``.
    """
    monkeypatch.chdir(tmp_path)
    _seed_candidates(db_path, {"replay": 1})
    head = _git(target_repo, "rev-parse", "HEAD")
    cand = _graph_with_head(tmp_path, built_at_head=head, nodes=2)
    doc = json.loads(cand.read_text(encoding="utf-8"))
    doc["nodes"] = [1] * 100000          # non-empty ... but of non-objects
    cand.write_text(json.dumps(doc), encoding="utf-8")
    before = _file_sha(cand)
    _pin(tmp_path, rel="state/kg/demo/graph.json", sha256=_file_sha(cand))
    monkeypatch.setattr("resextract.kg.Graphify", _FakeGraphify)

    for label, dry_run in (("plan", True), ("run", False)):
        report = _real_graph_run(tmp_path, config_dir, db_path, dry_run=dry_run)
        stage = report.stage("graph")
        assert stage.counts["mode"] == "build", f"{label}: {stage.as_dict()}"
        assert "not an object" in _digest_rejections(report), f"{label}: {report.notes}"
    # refused, reported — kept on disk byte for byte, never deleted
    assert cand.is_file() and _file_sha(cand) == before


def test_every_object_node_still_reuses_including_the_genuine_graph(
    tmp_path, config_dir, db_path, target_repo, monkeypatch
):
    """The control for (k): the element check must not reject a real graph.

    All 2685 nodes of the authoritative artifact are JSON objects, and so are
    the fixture's, so the new walk is a no-op on both.  A check that rejected the
    genuine graph would be worse than the bug: the real 2685-node/7102-edge
    graph is symlinked to the candidate path and must still be reused.
    """
    monkeypatch.chdir(tmp_path)
    _seed_candidates(db_path, {"replay": 1})
    head = _git(target_repo, "rev-parse", "HEAD")
    cand = _graph_with_head(tmp_path, built_at_head=head, nodes=3)
    monkeypatch.setattr("resextract.kg.Graphify", _FakeGraphify)
    report = _real_graph_run(tmp_path, config_dir, db_path, dry_run=False)
    assert report.stage("graph").counts["mode"] == "reuse", report.stage("graph").as_dict()

    if _GENUINE_GRAPH.is_file():
        assert run_mod._graph_unusable_reason(_GENUINE_GRAPH) is None, (
            "the element-type check rejected the genuine artifact"
        )
        real = tmp_path / "state" / "kg" / "demo" / "graph.json"
        real.unlink()
        real.symlink_to(_GENUINE_GRAPH)
        report = _real_graph_run(tmp_path, config_dir, db_path, dry_run=False)
        stage = report.stage("graph")
        assert stage.counts["mode"] == "reuse", stage.as_dict()
        assert stage.counts["nodes"] == 2685, stage.as_dict()
        assert stage.counts["edges"] == 7102, stage.as_dict()


def test_wrong_tail_pin_is_a_mismatch_and_a_short_pin_is_loud(
    tmp_path, config_dir, db_path, target_repo, monkeypatch
):
    """RED→GREEN guard (l) U8.11 item 2: the pin is compared in FULL.

    The reported digest used to be truncated to 12 hex, so ``_same_digest``
    compared 12 characters: a pin whose *tail* was wrong but whose first 12 hex
    matched reported "matches the pinned digest" — 48 bits of strength, not 256.
    Now the full 64 hex are compared, so (1) a wrong tail is a ``digest
    mismatch`` (refused, reported, file kept); (2) the exact full digest matches
    and the reported digest is the full 64 characters; (3) an abbreviated 12-hex
    pin is still honoured but only with a loud ``PIN ABBREVIATED`` note and a
    ``REDUCED STRENGTH`` clause in the line — the backward-compatible choice that
    does not require rewriting the committed pin.

    Reverting ``_graph_digest`` to ``hexdigest()[:12]`` makes case (1) reuse the
    file and this test fails on ``assert stage.counts["mode"] == "build"``.
    """
    monkeypatch.chdir(tmp_path)
    _seed_candidates(db_path, {"replay": 1})
    head = _git(target_repo, "rev-parse", "HEAD")
    cand = _graph_with_head(tmp_path, built_at_head=head, nodes=2)
    digest = _file_sha(cand)
    monkeypatch.setattr("resextract.kg.Graphify", _FakeGraphify)
    rel = "state/kg/demo/graph.json"

    # (1) wrong TAIL, identical first 12 hex -> must NOT match
    tail = "0" if digest[12] != "0" else "1"
    wrong = digest[:12] + tail + digest[13:]
    assert wrong[:12] == digest[:12] and wrong != digest
    _pin(tmp_path, rel=rel, sha256=wrong)
    for label, dry_run in (("plan", True), ("run", False)):
        report = _real_graph_run(tmp_path, config_dir, db_path, dry_run=dry_run)
        stage = report.stage("graph")
        assert stage.counts["mode"] == "build", f"{label}: {stage.as_dict()}"
        assert "digest mismatch" in _digest_rejections(report), f"{label}: {report.notes}"
        assert "matches the pinned digest" not in stage.reason, stage.reason

    # (2) the exact full 64-hex digest -> matches, and the digest is the full one
    _pin(tmp_path, rel=rel, sha256=digest)
    for label, dry_run in (("plan", True), ("run", False)):
        report = _real_graph_run(tmp_path, config_dir, db_path, dry_run=dry_run)
        stage = report.stage("graph")
        prov = stage.counts["provenance"]
        assert stage.counts["mode"] == "reuse", f"{label}: {stage.as_dict()}"
        assert prov["digest_state"] == "match", f"{label}: {prov}"
        assert prov["pin_sha256"] == digest, f"{label}: {prov}"
        assert prov["sha256"] == digest, f"{label}: {prov}"
        assert len(prov["sha256"]) == 64, f"{label}: {prov}"
        assert f"matches the pinned digest {digest[:12]}" in stage.reason, stage.reason

    # (3) an abbreviated 12-hex pin still matches — loudly, never silently
    _pin(tmp_path, rel=rel, sha256=digest[:12])
    report = _real_graph_run(tmp_path, config_dir, db_path, dry_run=False)
    stage = report.stage("graph")
    assert stage.counts["mode"] == "reuse", stage.as_dict()
    assert stage.counts["provenance"]["digest_state"] == "match", stage.as_dict()
    assert any("PIN ABBREVIATED" in n for n in report.notes), report.notes
    assert "REDUCED STRENGTH" in stage.reason, stage.reason


def test_broken_pin_is_refused_and_absent_pin_is_loudly_unverified(
    tmp_path, config_dir, db_path, target_repo, monkeypatch
):
    """RED→GREEN guard (m) U8.11 item 3: a present-but-broken pin is NOT "no pin".

    Every pin failure mode used to return a bare ``None``, so a tampered graph
    was reused with the degradation only as a clause in the stage line and no
    note.  Now the states are distinct and loud:

    * absent, or a well-formed file with no entry for this path -> reused, but
      with a ``PIN DEGRADED`` run note and ``unpinned``/``unverified``;
    * malformed TOML, unreadable (mode 000), or an empty value -> the pin exists
      and cannot be honoured, so it is REFUSED like a digest mismatch, reported
      and kept.

    Reverting ``_graph_pin`` to a bare ``str | None`` (no state) makes every case
    reuse and this test fails on the first ``mode == "build"``.
    """
    import os

    monkeypatch.chdir(tmp_path)
    _seed_candidates(db_path, {"replay": 1})
    head = _git(target_repo, "rev-parse", "HEAD")
    cand = _graph_with_head(tmp_path, built_at_head=head, nodes=2)
    digest = _file_sha(cand)
    before = _file_sha(cand)
    monkeypatch.setattr("resextract.kg.Graphify", _FakeGraphify)
    rel = "state/kg/demo/graph.json"

    # (a) no pin file at all -> reused, and now a NOTE, not just a stage clause
    _pin_text(tmp_path, None)
    report = _real_graph_run(tmp_path, config_dir, db_path, dry_run=False)
    stage = report.stage("graph")
    assert stage.counts["mode"] == "reuse", stage.as_dict()
    assert stage.counts["provenance"]["digest_state"] == "unpinned", stage.as_dict()
    assert stage.counts["provenance"]["pin_state"] == "absent", stage.as_dict()
    assert any(
        "PIN DEGRADED" in n and "UNVERIFIED" in n for n in report.notes
    ), report.notes
    assert "no pin recorded" in stage.reason and "unverified" in stage.reason.lower()

    # (b) well-formed, but keyed on another path -> same loud unpinned reuse
    _pin_text(
        tmp_path,
        f'version = 1\n\n[graphs."state/kg/other/graph.json"]\nsha256 = "{digest}"\n',
    )
    report = _real_graph_run(tmp_path, config_dir, db_path, dry_run=False)
    stage = report.stage("graph")
    assert stage.counts["mode"] == "reuse", stage.as_dict()
    assert stage.counts["provenance"]["digest_state"] == "unpinned", stage.as_dict()
    assert stage.counts["provenance"]["pin_state"] == "no_entry", stage.as_dict()
    assert any("PIN DEGRADED" in n for n in report.notes), report.notes

    # (c) malformed TOML -> refused (the control exists and is broken)
    _pin_text(tmp_path, "this is not toml ===\n")
    for label, dry_run in (("plan", True), ("run", False)):
        report = _real_graph_run(tmp_path, config_dir, db_path, dry_run=dry_run)
        stage = report.stage("graph")
        assert stage.counts["mode"] == "build", f"{label}: {stage.as_dict()}"
        assert "pin malformed" in _digest_rejections(report), f"{label}: {report.notes}"

    # (d) empty value for this path -> refused
    _pin_text(tmp_path, f'version = 1\n\n[graphs."{rel}"]\nsha256 = ""\n')
    report = _real_graph_run(tmp_path, config_dir, db_path, dry_run=False)
    stage = report.stage("graph")
    assert stage.counts["mode"] == "build", stage.as_dict()
    assert "pin empty" in _digest_rejections(report), report.notes

    # (e) unreadable (mode 000) -> refused (skipped if we are root and can read it)
    if os.geteuid() != 0:
        pin = _pin_text(
            tmp_path, f'version = 1\n\n[graphs."{rel}"]\nsha256 = "{digest}"\n'
        )
        os.chmod(pin, 0o000)
        try:
            report = _real_graph_run(tmp_path, config_dir, db_path, dry_run=False)
            stage = report.stage("graph")
            assert stage.counts["mode"] == "build", stage.as_dict()
            assert "pin unreadable" in _digest_rejections(report), report.notes
        finally:
            os.chmod(pin, 0o644)

    # refused, reported — kept on disk byte for byte throughout
    assert cand.is_file() and _file_sha(cand) == before


def test_require_fresh_graph_now_refuses_an_unverified_graph_too(
    tmp_path, config_dir, db_path, target_repo, monkeypatch
):
    """RED→GREEN guard (n) U8.11 item 3b: the opt-in refuses ``unverified`` too.

    ``require_fresh_graph`` means "do not trust a graph I cannot vouch for"; a
    graph with no recorded provenance (or an unreadable target HEAD) is exactly
    that, and it was refused for ``stale`` only.  The default is untouched: with
    the flag absent the graph is still reused and reported ``UNVERIFIED``.

    Reverting the refusal to ``state == "stale"`` makes the ``strict`` run reuse
    the unverified graph and this test fails on ``mode == "build"``.
    """
    monkeypatch.chdir(tmp_path)
    _seed_candidates(db_path, {"replay": 1})
    cand = _graph_with_head(tmp_path, built_at_head=None)  # no recorded provenance
    _pin(tmp_path, rel="state/kg/demo/graph.json", sha256=_file_sha(cand))
    monkeypatch.setattr("resextract.kg.Graphify", _FakeGraphify)

    default = _real_graph_run(tmp_path, config_dir, db_path, dry_run=True)
    assert default.stage("graph").counts["mode"] == "reuse", default.stage("graph").as_dict()
    assert default.stage("graph").counts["provenance"]["state"] == "unverified"

    strict = _real_graph_run(
        tmp_path, config_dir, db_path, dry_run=True, require_fresh_graph=True
    )
    stage = strict.stage("graph")
    assert stage.counts["mode"] == "build", stage.as_dict()
    assert "unverified" in _digest_rejections(strict), stage.as_dict()
    assert any(
        "require_fresh_graph refused an unvouched-for graph" in n and "unverified" in n
        for n in strict.notes
    ), strict.notes
    assert cand.is_file()


# --------------------------------------------------------------------------- #
# U0.25: a slow (reachable, over-bound) core leg is surfaced as SLOW, not DOWN
# --------------------------------------------------------------------------- #


def test_slow_core_leg_is_surfaced_as_slow_not_reported_down(
    tmp_path, config_dir, db_path, clean_preflight, monkeypatch
):
    """A slow core leg is named in ``preflight["core_slow"]``, not called DOWN.

    Guard (U0.25): the run's preflight carries the doctor's ``state="slow"``
    leg as SLOW -- in a dedicated ``core_slow`` list and in the degradation
    text -- instead of the old "core leg SearXNG is DOWN" wording that filed a
    reachable service under ``degradable_core_down``.  Exit semantics are
    unchanged: a slow leg no selected stage needs stays a degradation, never a
    hard gate.  Red without the fix (``report.preflight["core_slow"]`` missing,
    the leg named DOWN)::

        E       KeyError: 'core_slow'
    """
    monkeypatch.setattr(run_mod, "_make_client", lambda ctx: (None, "offline test"))
    slow_leg = {
        "leg": "SearXNG",
        "class": run_mod.doctor.CORE,
        "ok": False,
        "state": "slow",
        "slow": True,
        "bound_s": run_mod.doctor.HTTP_TIMEOUT,
        "detail": "TimeoutError: timed out; TCP connect accepted within 0.5s "
        "-> reachable but slow (per-leg bound 5.0s)",
    }
    report = run_pipeline(
        "demo",
        **_kwargs(
            tmp_path,
            config_dir,
            db_path,
            doctor_report={
                "legs": [slow_leg],
                "ok": True,
                "exit_code": 0,
                "degraded": True,
                "core_down": [],
                "core_slow": ["SearXNG"],
                "optional_down": [],
            },
        ),
    )
    pf = report.preflight
    assert pf["core_slow"] == ["SearXNG"]
    assert "SearXNG" not in pf["degradable_core_down"]
    assert "SearXNG" not in pf["hard_core_down"]
    assert pf["ok"] is True, "a slow leg no selected stage needs must not gate the run"
    assert report.exit_code != run_mod.EXIT_HARD_DOWN
    note = " ".join(report.degradations)
    assert "SearXNG" in note and "SLOW" in note and "is DOWN" not in note


# --------------------------------------------------------------------------- #
# U8.19 — the pin's *reporting* is one rule, not a length threshold.
#
# Measured on the real graph (sha256 4790bbb1…897b, full 64 hex) with scratch
# pin copies in ``state/verify/U8.19/pins/`` — matches / notices:
#   len 12, 13, 20, 40, 63 -> match + PIN ABBREVIATED + REDUCED STRENGTH
#   len 64                 -> match, no notice
#   len 65, 100            -> match, NO NOTICE  <-- the defect
# The condition was ``len(pin) < DIGEST_HEX``, so the warning was keyed to being
# *shorter* than the digest and a longer pin slipped through with no report at
# all while only its first 64 characters were compared.
#
# RULE (short pins, one sentence — corrected by U8.24): a pin is reported as
# reduced at EVERY length in the COMPARABLE range, 12-63 hex — 63 hex is exactly
# as weak a control as 12, and a warning that fires only under some threshold is
# not a policy.  The range is *not* "every length below 64": ``_same_digest``
# requires ``width >= 12``, so a 1-11-hex pin cannot be compared at all and is
# REFUSED as a mismatch (fail-closed, pre-existing, and with no
# ``PIN ABBREVIATED`` note — the note is emitted only on the match branch).
#
# OVER-LONG DECISION: reject (a).  A sha256 is exactly 64 hex, so a longer value
# is not an abbreviation of a digest but a corrupted or mis-edited one; the old
# comparison honoured only its first 64 characters.  It is now refused like a
# malformed/unreadable/empty pin: not reused, noted ``PIN OVERLONG``, pin file
# kept byte-for-byte.  Rejected (b) ``validate-the-tail`` because that would move
# the comparison itself, which U8.11 fixed to the full digest and which must not
# change, and (c) ``accept-and-warn`` because a pin that "matches" on a 64-char
# prefix while carrying a corrupt tail is exactly the blessing this control
# exists to prevent.
#
# RED→GREEN: reverting this change (restoring the ``len(pin) < DIGEST_HEX``
# conditions and dropping ``_pin_is_overlong``) makes
# ``test_overlong_pin_is_refused_never_silently_blessed`` FAIL — the 65-hex pin
# is reused (``mode == "reuse"``) with no notice and only a 64-char prefix
# compared.  sha256 of ``src/resextract/run.py`` before the change
# ``7f0b6a659102b9d56ec25f0d12e856324387efe72f0eceb1858ffd29346ccd35``, after
# ``106661a289b66d2885fad4fc5c1cebd9cfcb8db53fade8f85bfc52e601a1d26a``; revert
# and restore were ``cmp``-clean and bit-identical, under
# ``PYTHONDONTWRITEBYTECODE=1`` with a FULL ``__pycache__`` purge.
# --------------------------------------------------------------------------- #
_ABBREV_LENGTHS = [12, 13, 20, 40, 63]


@pytest.mark.parametrize("length", _ABBREV_LENGTHS)
def test_abbreviated_pin_warns_at_every_length_from_12_to_63(
    length, tmp_path, config_dir, db_path, target_repo, monkeypatch
):
    """U8.19 step 1: a correct-prefix pin of 12-63 hex warns at EVERY such length.

    Below 12 hex there is no warning to make: ``_same_digest`` needs
    ``width >= 12``, so a 1-11-hex pin is refused as a mismatch (U8.24).

    The table is the evidence: 12, 13, 20, 40, 63 hex all match on their own
    width and all carry the same two notices.  Nothing in this range is
    length-gated.
    """
    monkeypatch.chdir(tmp_path)
    _seed_candidates(db_path, {"replay": 1})
    head = _git(target_repo, "rev-parse", "HEAD")
    cand = _graph_with_head(tmp_path, built_at_head=head, nodes=2)
    digest = _file_sha(cand)
    _pin(tmp_path, rel="state/kg/demo/graph.json", sha256=digest[:length])
    monkeypatch.setattr("resextract.kg.Graphify", _FakeGraphify)

    report = _real_graph_run(tmp_path, config_dir, db_path, dry_run=False)
    stage = report.stage("graph")
    assert stage.counts["mode"] == "reuse", (length, stage.as_dict())
    prov = stage.counts["provenance"]
    assert prov["digest_state"] == "match", (length, prov)
    assert prov["pin_sha256"] == digest[:length], (length, prov)
    # the REPORTED digest stays the full 64 even when the pin is short
    assert prov["sha256"] == digest and len(prov["sha256"]) == 64, (length, prov)
    assert any("PIN ABBREVIATED" in n for n in report.notes), (length, report.notes)
    assert f"pins only {length} hex" in " ".join(report.notes), (length, report.notes)
    assert "REDUCED STRENGTH" in stage.reason, (length, stage.reason)
    assert f"supplies {length} of 64 hex chars" in stage.reason, (length, stage.reason)


def test_exactly_full_pin_is_the_only_length_with_no_notice(
    tmp_path, config_dir, db_path, target_repo, monkeypatch
):
    """The control: exactly 64 hex matches with no abbreviation and no over-long note."""
    monkeypatch.chdir(tmp_path)
    _seed_candidates(db_path, {"replay": 1})
    head = _git(target_repo, "rev-parse", "HEAD")
    cand = _graph_with_head(tmp_path, built_at_head=head, nodes=2)
    digest = _file_sha(cand)
    _pin(tmp_path, rel="state/kg/demo/graph.json", sha256=digest)
    monkeypatch.setattr("resextract.kg.Graphify", _FakeGraphify)

    report = _real_graph_run(tmp_path, config_dir, db_path, dry_run=False)
    stage = report.stage("graph")
    assert stage.counts["mode"] == "reuse", stage.as_dict()
    assert stage.counts["provenance"]["digest_state"] == "match", stage.as_dict()
    assert "REDUCED STRENGTH" not in stage.reason, stage.reason
    assert not any("PIN ABBREVIATED" in n for n in report.notes), report.notes
    assert not any("PIN OVERLONG" in n for n in report.notes), report.notes


@pytest.mark.parametrize("length", [65, 100])
def test_overlong_pin_is_refused_never_silently_blessed(
    length, tmp_path, config_dir, db_path, target_repo, monkeypatch
):
    """RED→GREEN guard (n) U8.19: an over-long pin is REJECTED, not silently honoured.

    Decision (a): a sha256 is exactly 64 hex, so a 65- or 100-hex value with a
    correct first 64 is a corrupted or mis-edited pin, not an abbreviation.  The
    old code compared its first 64 characters and reported a bare
    ``matches the pinned digest`` with **no** note and an unvalidated tail; now
    it is refused exactly like a malformed/unreadable/empty pin — not reused,
    ``PIN OVERLONG`` in the run notes, ``pin overlong`` in the rejected
    candidates, the pin file kept byte-for-byte, and a fresh graph by default.

    Reverting to ``len(pin) < DIGEST_HEX`` (see the section comment) makes this
    test FAIL on ``mode == "build"``: the over-long pin is reused.
    """
    monkeypatch.chdir(tmp_path)
    _seed_candidates(db_path, {"replay": 1})
    head = _git(target_repo, "rev-parse", "HEAD")
    cand = _graph_with_head(tmp_path, built_at_head=head, nodes=2)
    digest = _file_sha(cand)
    rel = "state/kg/demo/graph.json"
    pin_file = _pin(tmp_path, rel=rel, sha256=digest + "a" * (length - 64))
    pin_before = _file_sha(pin_file)
    monkeypatch.setattr("resextract.kg.Graphify", _FakeGraphify)

    for label, dry_run in (("plan", True), ("run", False)):
        report = _real_graph_run(tmp_path, config_dir, db_path, dry_run=dry_run)
        stage = report.stage("graph")
        assert stage.counts["mode"] == "build", (length, label, stage.as_dict())
        assert "pin overlong" in _digest_rejections(report), (length, label, report.notes)
        assert any("PIN OVERLONG" in n for n in report.notes), (length, label, report.notes)
        assert "matches the pinned digest" not in stage.reason, (length, label, stage.reason)
    # refused and reported, but the pin file is never rewritten
    assert pin_file.is_file() and _file_sha(pin_file) == pin_before
    assert _git(target_repo, "status", "--porcelain") == ""


def test_wrong_tail_pin_still_does_not_match_after_u819(
    tmp_path, config_dir, db_path, target_repo, monkeypatch
):
    """U8.11's serious half must stay fixed: a wrong TAIL (same first 12) is a mismatch.

    Corollary check run alongside the over-long decision: fixing the reporting of
    LONG pins must not weaken the FULL-digest comparison for pins of exactly the
    digest's length.
    """
    monkeypatch.chdir(tmp_path)
    _seed_candidates(db_path, {"replay": 1})
    head = _git(target_repo, "rev-parse", "HEAD")
    cand = _graph_with_head(tmp_path, built_at_head=head, nodes=2)
    digest = _file_sha(cand)
    tail = "0" if digest[12] != "0" else "1"
    wrong = digest[:12] + tail + digest[13:]
    assert wrong[:12] == digest[:12] and wrong != digest and len(wrong) == 64
    _pin(tmp_path, rel="state/kg/demo/graph.json", sha256=wrong)
    monkeypatch.setattr("resextract.kg.Graphify", _FakeGraphify)

    report = _real_graph_run(tmp_path, config_dir, db_path, dry_run=False)
    stage = report.stage("graph")
    assert stage.counts["mode"] == "build", stage.as_dict()
    assert "digest mismatch" in _digest_rejections(report), report.notes
    assert "matches the pinned digest" not in stage.reason, stage.reason


# --------------------------------------------------------------------------- #
# U8.31 — pinning the corrected prose (V8.27: an accurate comment over
# unpinned behaviour can rot silently again).
#
# Measured in-process against the REAL package (``run.py`` sha256
# e778e967…) with scratch pins under ``state/verify/U8.31/``, using the real
# graph digest 4790bbb1…897b for the direct comparison probe:
#   len 0   -> refused, ``pin empty`` in rejected_candidates, _never compared_
#              (no ``digest mismatch``), no ``PIN ABBREVIATED`` note;
#   len 1   -> refused as ``digest mismatch``, no ``PIN ABBREVIATED`` note;
#   len 11  -> refused as ``digest mismatch``, no ``PIN ABBREVIATED`` note;
#   len 12  -> match + ``PIN ABBREVIATED`` + ``REDUCED STRENGTH``;
#   len 64  -> match, silent;
#   len 65  -> refused as ``PIN OVERLONG`` although ``_same_digest`` is True:
#              the over-long check runs BEFORE the comparison.
# The 0-hex notice the code emits is lowercase ``pin empty`` (the ``PIN_EMPTY``
# ``_graph_pin`` state via ``_note_unusable``'s ``f"pin {pin_state}: …"``);
# there is no uppercase ``PIN EMPTY`` string in ``run.py``.  The *state* is
# what is distinct, and that is what these guards pin.
#
# RED→GREEN: run against a COPY of the package (``state/verify/U8.31-red``) —
# ``width >= 12`` -> ``width >= 1``, the empty branch neutralised, and the
# over-long branch disabled in turn; verbatim failures in
# ``orchestration/handoffs/U8.31.json``.  The real tree is untouched
# (``run.py`` sha256 identical before and after).
# --------------------------------------------------------------------------- #
_SUB12_PIN_LENGTHS = [1, 11]


@pytest.mark.parametrize("length", _SUB12_PIN_LENGTHS)
def test_sub12_hex_pin_is_refused_as_a_mismatch_not_abbreviated(
    length, tmp_path, config_dir, db_path, target_repo, monkeypatch
):
    """U8.31: a 1-11-hex correct-prefix pin cannot be compared; it is a REFUSAL.

    ``_same_digest`` floors at ``width >= 12``, so a 1- or 11-hex pin returns
    False and the stage refuses the candidate as ``digest mismatch``.  It is
    never honoured at reduced strength and carries **no** ``PIN ABBREVIATED``
    note — that note is emitted only on the match branch, which these lengths
    cannot reach.  Pinning this stops the corrected comment (U8.24) from rotting
    back to "shorter than 12 is accepted but reported loudly".
    """
    monkeypatch.chdir(tmp_path)
    _seed_candidates(db_path, {"replay": 1})
    head = _git(target_repo, "rev-parse", "HEAD")
    cand = _graph_with_head(tmp_path, built_at_head=head, nodes=2)
    digest = _file_sha(cand)
    _pin(tmp_path, rel="state/kg/demo/graph.json", sha256=digest[:length])
    monkeypatch.setattr("resextract.kg.Graphify", _FakeGraphify)

    report = _real_graph_run(tmp_path, config_dir, db_path, dry_run=False)
    stage = report.stage("graph")
    assert stage.counts["mode"] == "build", (length, stage.as_dict())
    assert "digest mismatch" in _digest_rejections(report), (length, report.notes)
    assert not any("PIN ABBREVIATED" in n for n in report.notes), (length, report.notes)
    assert "REDUCED STRENGTH" not in stage.reason, (length, stage.reason)
    assert "matches the pinned digest" not in stage.reason, (length, stage.reason)


def test_zero_hex_pin_is_the_distinct_empty_state_never_a_mismatch(
    tmp_path, config_dir, db_path, target_repo, monkeypatch
):
    """U8.31: exactly-0 hex is ``pin empty`` — refused WITHOUT ever being compared.

    The prose ("shorter than 12 -> mismatch") is imprecise at 0: an entry that
    exists but carries no value is a *distinct* state (``PIN_EMPTY``), refused
    before any comparison, so the run reports ``pin empty`` and **not**
    ``digest mismatch``, and emits no ``PIN ABBREVIATED`` note either.  The
    emitted text is lowercase ``pin empty``; the *state* is what is distinct.
    """
    monkeypatch.chdir(tmp_path)
    _seed_candidates(db_path, {"replay": 1})
    head = _git(target_repo, "rev-parse", "HEAD")
    _graph_with_head(tmp_path, built_at_head=head, nodes=2)
    rel = "state/kg/demo/graph.json"
    _pin_text(tmp_path, f'version = 1\n\n[graphs."{rel}"]\nsha256 = ""\n')
    monkeypatch.setattr("resextract.kg.Graphify", _FakeGraphify)

    report = _real_graph_run(tmp_path, config_dir, db_path, dry_run=False)
    stage = report.stage("graph")
    rejected = _digest_rejections(report)
    assert stage.counts["mode"] == "build", stage.as_dict()
    assert "pin empty" in rejected, report.notes
    # THE DISTINCT STATE: refused before any comparison, so never a mismatch
    assert "digest mismatch" not in rejected, report.notes
    assert "pin overlong" not in rejected, report.notes
    assert not any("PIN ABBREVIATED" in n for n in report.notes), report.notes
    assert "REDUCED STRENGTH" not in stage.reason, stage.reason


def test_overlong_refusal_precedes_a_comparison_that_would_have_matched(
    tmp_path, config_dir, db_path, target_repo, monkeypatch
):
    """U8.31: the ordering fact made explicit — 65 hex would match, refused anyway.

    ``_same_digest`` truncates to ``min(len, 64)``, so a 65-hex pin whose first
    64 characters are correct returns **True**; the stage refuses it as
    ``PIN OVERLONG`` regardless, because ``_pin_is_overlong`` runs *before* the
    comparison.  ``test_overlong_pin_is_refused_never_silently_blessed`` pins
    the refusal only, so the precedence was implicit.  This asserts both halves.
    """
    monkeypatch.chdir(tmp_path)
    _seed_candidates(db_path, {"replay": 1})
    head = _git(target_repo, "rev-parse", "HEAD")
    cand = _graph_with_head(tmp_path, built_at_head=head, nodes=2)
    digest = _file_sha(cand)
    overlong = digest + "a"
    assert run_mod._same_digest(digest, overlong) is True
    assert run_mod._pin_is_overlong(overlong) is True
    _pin(tmp_path, rel="state/kg/demo/graph.json", sha256=overlong)
    monkeypatch.setattr("resextract.kg.Graphify", _FakeGraphify)

    report = _real_graph_run(tmp_path, config_dir, db_path, dry_run=False)
    stage = report.stage("graph")
    assert stage.counts["mode"] == "build", stage.as_dict()
    assert any("PIN OVERLONG" in n for n in report.notes), report.notes
    assert "pin overlong" in _digest_rejections(report), report.notes
    assert "matches the pinned digest" not in stage.reason, stage.reason

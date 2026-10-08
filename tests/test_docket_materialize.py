"""Offline tests for ``resextract materialize`` (U5.3).

A fixture *target repo* (plain files, read-only by convention) plus a fixture
*store* (a fresh SQLite file) — no network, no git, no model calls.  The tests
pin the whole contract: ref-shape resolution, the refusal guard (no half-docket),
partial resolution, containment, idempotency, ``dry_run``, and the CLI's exit
codes.

Contract change (U5.5), deliberately re-pinned here
---------------------------------------------------

``materialize_lane`` now defaults to ``source_mode="commit"`` and opens every run
with a quiescence window.  This fixture target is not a git repository, so its
material entries are now recorded ``resolved_from="working_tree"`` with
``unpinned=true`` and reason ``not_a_git_repo``; the copied bytes are unchanged.
The helper below passes ``window_s=0.0`` so the suite stays fast, and the
refusal/containment/idempotency assertions above are unchanged in meaning.  The
commit-pinned contract itself lives in ``tests/test_docket_materialize_pinned.py``
(a real temporary git repo).

Red → green (two guards, both pasted verbatim)
==============================================

Guard 1 — the **all-refs-unresolvable refusal** (``test_refusal_writes_no_docket``).
Revert = delete the `if not verifiable: raise MaterializeRefused(...)` block in
``materialize_lane``.  Running
``.venv/bin/python -m pytest tests/test_docket_materialize.py::test_refusal_writes_no_docket``::

    def test_refusal_writes_no_docket(tmp_path, target, graph_file, db):
        docket = docket_path(tmp_path, target, "refuse-lane")
        spec = lane(
            "refuse-lane",
            [mat.MemberSpec("M1", provenance_refs=["docs/NOPE.md", "graph:missing_node"])],
        )
>       with pytest.raises(mat.MaterializeRefused) as excinfo:
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
E       Failed: DID NOT RAISE MaterializeRefused

tests/test_docket_materialize.py:210: Failed
=========================== short test summary info ============================
FAILED tests/test_docket_materialize.py::test_refusal_writes_no_docket - Fail...
1 failed in 0.04s

(Full log: ``state/logs/U5.3_red1.txt``.)

Guard 2 — the **containment guard** (``test_containment_refs_are_never_emitted_as_requests``).
Revert = delete the `if not _contained(src, target_root): return None, UnresolvedRef(...)`
branch in ``_resolve_one``.  Running
``.venv/bin/python -m pytest tests/test_docket_materialize.py::test_containment_refs_are_never_emitted_as_requests``::

        plan = mat.refs_to_copy_requests(
            ["../outside/leak.md", "/etc/passwd", str(outside)],
            target_root=str(target),
        )
>       assert plan.requests == []
E       AssertionError: assert [CopyRequest(...excerpt=None)] == []
E         Left contains 2 more items, first extra item:
E         CopyRequest(src='/tmp/pytest-.../outside/leak.md', dest_rel='docs/leak.md',
E                     reason='materialize:../outside/leak.md', excerpt=None)

tests/test_docket_materialize.py:307: AssertionError
1 failed in 0.03s

(Full log: ``state/logs/U5.3_red2.txt``.)

Both guards are green on the shipped tree (see the module's own test run in
``state/logs/U5.3_tests.txt``).
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from resextract import cli, store
from resextract.docket import materialize as mat

# --------------------------------------------------------------------------- #
# fixtures
# --------------------------------------------------------------------------- #

GUIDE_LINES = [f"guide line {i}" for i in range(1, 41)]  # 40 lines
GUIDE = "\n".join(GUIDE_LINES) + "\n"
ALPHA = (
    "export const alpha = 1;\n"
    "export const beta = 2;\n"
    "export function run() {\n"
    "  return alpha + beta;\n"
    "}\n"
)
METRICS = '{\n  "score": 0.9,\n  "runs": 3\n}\n'
CITATION = "cff-version: 1.2.0\ntitle: Fixture Repo\n"
LEAK = "TOP SECRET — this file lives outside the target root\n"


@pytest.fixture
def target(tmp_path: Path) -> Path:
    root = tmp_path / "target"
    (root / "docs").mkdir(parents=True)
    (root / "src").mkdir()
    (root / "evals").mkdir()
    (root / "docs" / "GUIDE.md").write_text(GUIDE, encoding="utf-8")
    (root / "src" / "alpha.ts").write_text(ALPHA, encoding="utf-8")
    (root / "evals" / "baseline.json").write_text(METRICS, encoding="utf-8")
    (root / "CITATION.cff").write_text(CITATION, encoding="utf-8")
    return root


@pytest.fixture
def graph_file(tmp_path: Path) -> Path:
    path = tmp_path / "graph.json"
    path.write_text(
        json.dumps(
            {
                "directed": True,
                "multigraph": False,
                "graph": {},
                "nodes": [
                    {
                        "id": "src_alpha_alpha",
                        "label": "alpha",
                        "file_type": "code",
                        "source_file": "src/alpha.ts",
                        "source_location": "L3",
                    },
                    {
                        "id": "ext_html",
                        "label": "html",
                        "type": "external",
                        "file_type": "concept",
                        "source_file": "",
                    },
                ],
                "links": [],
            }
        ),
        encoding="utf-8",
    )
    return path


@pytest.fixture
def db(tmp_path: Path) -> Path:
    path = tmp_path / "state.sqlite"
    store.init_db(path)
    return path


@pytest.fixture
def outside(tmp_path: Path) -> Path:
    """A file *outside* the target root, holding a sentinel that must never leak."""
    leak = tmp_path / "outside" / "leak.md"
    leak.parent.mkdir(parents=True, exist_ok=True)
    leak.write_text(LEAK, encoding="utf-8")
    return leak


def lane(slug: str, members: list[mat.MemberSpec], **kw) -> mat.LaneSpec:
    return mat.LaneSpec(
        slug=slug,
        title="Fixture lane",
        thesis="Fixture thesis for materialization tests.",
        audience="test suite",
        type=kw.pop("type", "report"),
        members=members,
        target_slug=kw.pop("target_slug", ""),
        head_sha=kw.pop("head_sha", "fixture-head-sha"),
        **kw,
    )


def docket_path(tmp_path: Path, target: Path, slug: str) -> Path:
    return tmp_path / "dockets" / target.name / slug


def material_texts(docket: Path) -> str:
    out = []
    for path in sorted((docket / "material").rglob("*")):
        if path.is_file():
            out.append(path.read_bytes().decode("utf-8", errors="replace"))
    return "\n".join(out)


def run_lane(lane_spec, target, db, tmp_path, graph_file=None, **kw):
    # U5.5: the default source mode is now ``commit`` and every run opens with a
    # quiescence window.  This fixture target is *not* a git repository, so the
    # window is shortened to 0 s here; the window's own contract (and the pinned
    # path) is pinned against a real git repo in
    # tests/test_docket_materialize_pinned.py.  A non-git target now records every
    # material entry as ``unpinned=true`` with reason ``not_a_git_repo``.
    kw.setdefault("window_s", 0.0)
    return mat.materialize_lane(
        lane_spec,
        target_root=str(target),
        docket_root=str(tmp_path / "dockets"),
        graph_path=str(graph_file) if graph_file is not None else None,
        db_path=db,
        **kw,
    )


# --------------------------------------------------------------------------- #
# happy path
# --------------------------------------------------------------------------- #


def test_happy_path_copies_material_and_verifies(tmp_path, target, graph_file, db):
    spec = lane(
        "happy-lane",
        [
            mat.MemberSpec("M1", provenance_refs=["docs/GUIDE.md#L1-L5", "src/alpha.ts:L3"]),
            mat.MemberSpec("M2", provenance_refs=["src_alpha_alpha"]),
        ],
    )
    result = run_lane(spec, target, db, tmp_path, graph_file=graph_file)
    docket = Path(result.docket_dir)

    assert result.ok and result.verification.ok, result.verification.problems
    assert result.copy_report.copied_count == 2
    assert result.copy_report.refused_count == 0
    assert result.unresolved_refs == []
    assert (docket / "material" / "EXCERPTS.md").is_file()
    assert (docket / "material" / "docs" / "GUIDE.md").is_file()
    assert (docket / "material" / "code" / "alpha.ts").is_file()

    manifest = json.loads((docket / "MANIFEST.json").read_text(encoding="utf-8"))
    assert {i["dest"] for i in manifest["material"]} == {"docs/GUIDE.md", "code/alpha.ts"}
    # the manifest records the real source path the bytes came from
    by_dest = {i["dest"]: i for i in manifest["material"]}
    assert by_dest["docs/GUIDE.md"]["src"] == str((target / "docs" / "GUIDE.md").resolve())

    problems = mat.verify_docket(docket).problems
    assert problems == []

    con = store.connect(db)
    try:
        rows = con.execute("SELECT id, dir, source_head FROM dockets").fetchall()
    finally:
        con.close()
    assert len(rows) == 1
    assert rows[0]["source_head"] == "fixture-head-sha"


# --------------------------------------------------------------------------- #
# refusal guard — no half-docket
# --------------------------------------------------------------------------- #


def test_refusal_writes_no_docket(tmp_path, target, graph_file, db):
    docket = docket_path(tmp_path, target, "refuse-lane")
    spec = lane(
        "refuse-lane",
        [mat.MemberSpec("M1", provenance_refs=["docs/NOPE.md", "graph:missing_node"])],
    )
    with pytest.raises(mat.MaterializeRefused) as excinfo:
        run_lane(spec, target, db, tmp_path, graph_file=graph_file)

    reasons = " ".join(excinfo.value.reasons)
    assert "docs/NOPE.md" in reasons
    assert "missing_node" in reasons
    assert not docket.exists() or not any(docket.iterdir())


def test_refusal_for_a_lane_with_no_members_at_all(tmp_path, target, db):
    docket = docket_path(tmp_path, target, "empty-lane")
    with pytest.raises(mat.MaterializeRefused):
        run_lane(lane("empty-lane", []), target, db, tmp_path)
    assert not docket.exists() or not any(docket.iterdir())


# --------------------------------------------------------------------------- #
# partial resolution
# --------------------------------------------------------------------------- #


def test_partial_resolution_proceeds_and_names_the_bad_ref(tmp_path, target, db):
    spec = lane(
        "partial-lane",
        [mat.MemberSpec("M1", provenance_refs=["docs/GUIDE.md#L1-L5", "docs/MISSING.md"])],
    )
    result = run_lane(spec, target, db, tmp_path)

    assert result.ok
    assert result.copy_report.copied_count == 1
    assert len(result.unresolved_refs) == 1
    assert result.unresolved_refs[0].ref == "docs/MISSING.md"
    assert result.unresolved_refs[0].reason == "not_a_file_in_target"
    assert result.counts()["unresolved"] == 1


# --------------------------------------------------------------------------- #
# ref shapes
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize(
    "ref,dest,span",
    [
        ("docs/GUIDE.md#L2-L6", "docs/GUIDE.md", (2, 6)),
        ("docs/GUIDE.md#L7", "docs/GUIDE.md", (7, 7)),
        ("src/alpha.ts:L3", "code/alpha.ts", (3, 3)),
        ("src/alpha.ts:L1-L4", "code/alpha.ts", (1, 4)),
        ("src_alpha_alpha", "code/alpha.ts", (3, 3)),
        ("graph:src_alpha_alpha", "code/alpha.ts", (3, 3)),
        ("CITATION.cff", "docs/CITATION.cff", None),
        ("evals/baseline.json", "data/baseline.json", None),
    ],
)
def test_ref_shape_resolution(target, graph_file, ref, dest, span):
    import json as _json

    graph = None
    from resextract.kg import read_graph

    graph = read_graph(graph_file)
    plan = mat.refs_to_copy_requests([ref], target_root=str(target), graph=graph)

    assert plan.unresolved == []
    assert [r.dest_rel for r in plan.requests] == [dest]
    assert plan.requests[0].excerpt == span
    assert plan.by_ref[ref] == dest
    assert plan.requests[0].src.startswith(str(target.resolve()))
    assert _json.dumps(plan.to_dict())  # to_dict is JSON-serializable


def test_dedup_by_destination_keeps_the_cited_span(target):
    plan = mat.refs_to_copy_requests(
        ["docs/GUIDE.md", "docs/GUIDE.md#L3-L4"],
        target_root=str(target),
    )
    assert len(plan.requests) == 1
    assert plan.requests[0].excerpt == (3, 4)
    assert plan.by_ref["docs/GUIDE.md#L3-L4"] == "docs/GUIDE.md"


def test_span_past_eof_is_unresolved(target):
    plan = mat.refs_to_copy_requests(["docs/GUIDE.md#L1-L9999"], target_root=str(target))
    assert plan.requests == []
    assert plan.unresolved[0].reason == "span_past_eof"


# --------------------------------------------------------------------------- #
# containment
# --------------------------------------------------------------------------- #


def test_containment_refs_are_never_emitted_as_requests(target, outside):
    plan = mat.refs_to_copy_requests(
        ["../outside/leak.md", "/etc/passwd", str(outside)],
        target_root=str(target),
    )
    assert plan.requests == []
    assert {u.reason for u in plan.unresolved} == {"outside_target_root"}
    assert {u.ref for u in plan.unresolved} == {
        "../outside/leak.md",
        "/etc/passwd",
        str(outside),
    }


def test_containment_end_to_end_never_copies_the_leak(tmp_path, target, outside, db):
    spec = lane(
        "contain-lane",
        [mat.MemberSpec("M1", provenance_refs=["docs/GUIDE.md#L1-L5", "../outside/leak.md"])],
    )
    result = run_lane(spec, target, db, tmp_path)
    docket = Path(result.docket_dir)

    assert result.ok  # the resolvable ref carries the lane
    reasons = {u.ref: u.reason for u in result.unresolved_refs}
    assert reasons["../outside/leak.md"] == "outside_target_root"
    assert LEAK.strip() not in material_texts(docket)
    assert result.copy_report.copied_count == 1


# --------------------------------------------------------------------------- #
# idempotency
# --------------------------------------------------------------------------- #


def test_rerun_is_idempotent(tmp_path, target, db):
    spec = lane(
        "idem-lane",
        [mat.MemberSpec("M1", provenance_refs=["docs/GUIDE.md#L1-L5", "CITATION.cff"])],
    )
    first = run_lane(spec, target, db, tmp_path)
    docket = Path(first.docket_dir)
    assert first.copy_report.copied_count == 2

    history_one = (docket / "HISTORY.md").read_text(encoding="utf-8")
    assert "ITEM.md.r1" not in history_one

    second = run_lane(spec, target, db, tmp_path)
    assert second.ok
    assert second.copy_report.copied_count == 0
    assert second.copy_report.unchanged_count == 2

    assert (docket / "ITEM.md.r1").is_file()
    history_two = (docket / "HISTORY.md").read_text(encoding="utf-8")
    assert history_one.rstrip("\n") in history_two  # appended, never truncated

    con = store.connect(db)
    try:
        count = con.execute("SELECT COUNT(*) FROM dockets").fetchone()[0]
        row_id = con.execute("SELECT id FROM dockets").fetchone()[0]
    finally:
        con.close()
    assert count == 1
    assert second.dockets_row_id == first.dockets_row_id == row_id


# --------------------------------------------------------------------------- #
# dry run
# --------------------------------------------------------------------------- #


def test_dry_run_writes_nothing_and_reports_the_plan(tmp_path, target, graph_file, db):
    docket = docket_path(tmp_path, target, "dry-lane")
    spec = lane("dry-lane", [mat.MemberSpec("M1", provenance_refs=["docs/GUIDE.md#L1-L5"])])
    result = run_lane(spec, target, db, tmp_path, graph_file=graph_file, dry_run=True)

    assert result.dry_run is True
    assert result.plan is not None and len(result.plan.to_copy) == 1
    assert result.plan.total_bytes == len(GUIDE.encode("utf-8"))
    assert result.verification is None
    assert "material/docs/GUIDE.md" in result.files_written
    assert not docket.exists()

    con = store.connect(db)
    try:
        assert con.execute("SELECT COUNT(*) FROM dockets").fetchone()[0] == 0
    finally:
        con.close()


def test_dry_run_still_refuses_an_unresolvable_lane(tmp_path, target, db):
    spec = lane("dry-refuse", [mat.MemberSpec("M1", provenance_refs=["docs/NOPE.md"])])
    with pytest.raises(mat.MaterializeRefused):
        run_lane(spec, target, db, tmp_path, dry_run=True)
    assert not docket_path(tmp_path, target, "dry-refuse").exists()


# --------------------------------------------------------------------------- #
# from_store / from_json
# --------------------------------------------------------------------------- #


def test_from_store_reads_candidate_provenance(db):
    con = store.connect(db)
    try:
        store.upsert_lane(
            con, target="fixture", slug="store-lane", title="Store lane",
            thesis="t", audience="a", type="memo", status="draft",
        )
        lane_row = store.get_lane_by_slug(con, "fixture", "store-lane")
        store.insert_candidate(
            con,
            run_id=None,
            kind="novel_primitive",
            title="REPLAY thing",
            summary="summary",
            provenance_json=[
                {"kind": "graph_node", "ref": "src_alpha_alpha"},
                {"kind": "file_lines", "ref": "docs/GUIDE.md#L1-L5"},
            ],
            graph_nodes_json=["src_alpha_alpha"],
            score=0.5,
            state="mined",
        )
        rows = [dict(r) for r in con.execute("SELECT * FROM candidates").fetchall()]
    finally:
        con.close()

    spec = mat.LaneSpec.from_store(lane_row, rows)
    assert spec.slug == "store-lane"
    assert spec.target_slug == "fixture"
    assert len(spec.members) == 1
    assert spec.members[0].provenance_refs == [
        "src_alpha_alpha",
        "docs/GUIDE.md#L1-L5",
        "graph:src_alpha_alpha",
    ]
    assert spec.members[0].verification_state == "mined"


def test_from_json_roundtrip(tmp_path, target, db):
    spec = lane(
        "json-lane",
        [mat.MemberSpec("M1", provenance_refs=["docs/GUIDE.md#L1-L5"], summary="s")],
        target_slug="fixture",
    )
    path = tmp_path / "lane.json"
    path.write_text(json.dumps(spec.to_dict()), encoding="utf-8")
    loaded = mat.LaneSpec.from_json(path)

    assert loaded.slug == "json-lane"
    assert loaded.target_slug == "fixture"
    assert loaded.members[0].provenance_refs == ["docs/GUIDE.md#L1-L5"]
    assert loaded.type == "report"


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #


@pytest.fixture
def cli_env(tmp_path, target, db, monkeypatch):
    monkeypatch.setenv("RESEXTRACT_STATE_DB", str(db))
    monkeypatch.chdir(tmp_path)
    con = store.connect(db)
    try:
        store.upsert_target(con, slug="fixture", path=str(target), head_sha="fixture-head-sha")
    finally:
        con.close()
    spec = lane(
        "cli-lane",
        [mat.MemberSpec("M1", provenance_refs=["docs/GUIDE.md#L1-L5", "docs/GONE.md"])],
        target_slug="fixture",
    )
    spec_path = tmp_path / "cli_lane.json"
    spec_path.write_text(json.dumps(spec.to_dict()), encoding="utf-8")
    return {"spec": spec_path, "tmp": tmp_path}


def test_cli_materialize_dry_run_json_exits_0(cli_env, capsys):
    code = cli.main(
        [
            "materialize",
            "--target", "fixture",
            "--lane-file", str(cli_env["spec"]),
            "--docket-root", str(cli_env["tmp"] / "dockets"),
            "--dry-run",
            "--json",
        ]
    )
    out = capsys.readouterr().out
    payload = json.loads(out)

    assert code == cli.EXIT_OK == 0
    assert payload["dry_run"] is True
    assert payload["plan"]["total_bytes"] > 0
    assert payload["plan"]["to_copy"] == ["docs/GUIDE.md"]
    assert payload["counts"]["unresolved"] == 1
    assert not (cli_env["tmp"] / "dockets").exists()


def test_cli_unknown_lane_exits_3(cli_env, capsys):
    code = cli.main(["materialize", "--target", "fixture", "--lane", "nope", "--dry-run"])
    assert code == cli.EXIT_NOT_IMPLEMENTED == 3
    assert "not found" in capsys.readouterr().out


def test_cli_missing_target_exits_2(cli_env, capsys):
    code = cli.main(
        ["materialize", "--target", "ghost", "--lane-file", str(cli_env["spec"]), "--dry-run"]
    )
    assert code == cli.EXIT_CORE_DOWN == 2
    assert "not found" in capsys.readouterr().out


def test_cli_requires_a_lane_source(cli_env, capsys):
    code = cli.main(["materialize", "--target", "fixture", "--dry-run"])
    assert code == cli.EXIT_NOT_IMPLEMENTED == 3

"""Offline tests for :mod:`resextract.kg.graphify` against the real binary.

The ``kg-mini`` fixture repo is extracted **once** per module (module-scoped
fixture) with the local, API-key-free ``--code-only`` path.  No network, no LLM,
no Occamy.  Everything else reads that one graph.

Evidence for the proven command forms is in the test bodies: each asserts the
exact argv the wrapper built, so a future unit can copy it verbatim.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from resextract.kg.graphify import (
    DEFAULT_BINARY,
    GRAPH_DIR_NAME,
    GRAPH_FILE_NAME,
    Graph,
    Graphify,
    GraphifyError,
    GraphifyTimeout,
    GodNodesResult,
    QueryResult,
    graph_stats,
    read_graph,
    resolve_graph_path,
)

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "tests" / "fixtures" / "kg-mini"
OUT_DIR = ROOT / "state" / "kg-mini"
MISSING = ROOT / "tests" / "fixtures" / "_kg_mini_does_not_exist"


@pytest.fixture(scope="module")
def gf() -> Graphify:
    return Graphify(cwd=ROOT)


@pytest.fixture(scope="module")
def graph_file(gf: Graphify) -> Path:
    """Extract the fixture repo exactly once for the whole module."""
    assert DEFAULT_BINARY.exists(), f"graphify binary missing: {DEFAULT_BINARY}"
    result = gf.extract(FIXTURE, code_only=True, out=OUT_DIR)
    assert result.exit_code == 0
    assert "--code-only" in result.argv
    path = OUT_DIR / GRAPH_DIR_NAME / GRAPH_FILE_NAME
    assert path.is_file(), f"extract did not write {path}; stdout={result.stdout!r}"
    return path


# --------------------------------------------------------------------------- #
# extraction + graph shape
# --------------------------------------------------------------------------- #


def test_extract_writes_graphify_out_graph_json(gf: Graphify, graph_file: Path) -> None:
    """The real output path is ``<out>/graphify-out/graph.json`` — never assumed."""
    assert graph_file == OUT_DIR / "graphify-out" / "graph.json"
    assert resolve_graph_path(OUT_DIR) == graph_file
    assert resolve_graph_path(graph_file) == graph_file
    assert gf.graph_json(OUT_DIR) == graph_file


def test_graph_stats_nodes_edges_dirs(graph_file: Path) -> None:
    stats = graph_stats(graph_file)
    assert stats.nodes >= 5, stats
    assert stats.edges >= 1, stats
    assert stats.communities >= 1
    assert isinstance(stats.directed, bool)
    # kg-mini is a flat fixture: pkg/ plus three top-level files.
    assert stats.top_dirs.get("pkg", 0) >= 4, stats.top_dirs
    # 0.9.80 emits file_type, not type; node_kinds must still be populated.
    assert stats.node_kinds, stats.node_kinds
    assert "code" in stats.node_kinds


def test_read_graph_is_a_lazy_typed_view(graph_file: Path) -> None:
    graph = read_graph(graph_file)
    assert isinstance(graph, Graph)
    assert graph._nodes is None, "read_graph must not materialise nodes eagerly"
    nodes = graph.nodes
    assert len(nodes) == graph_stats(graph_file).nodes
    assert graph._nodes is not None, "the view should cache after first access"
    assert len(graph.links) >= 1
    sample = graph.by_id()["pkg_core_job"]
    assert sample.label == "Job"
    assert sample.source_file == "pkg/core.py"
    assert sample.source_location.startswith("L")
    assert sample.kind  # file_type fallback


def test_import_edge_from_main_to_pkg_core_is_in_the_link_list(graph_file: Path) -> None:
    """main.py -> pkg.core must appear as an import-ish link."""
    graph = read_graph(graph_file)
    by_id = graph.by_id()
    imports = [
        (by_id.get(link.source), link)
        for link in graph.links
        if link.relation in ("imports", "imports_from")
    ]
    assert imports, "no import edges found"
    from_main = [
        (node, link)
        for node, link in imports
        if node is not None and node.source_file == "main.py"
    ]
    assert from_main, [link.relation for _, link in imports]
    assert any(by_id.get(link.target, None) is not None for _, link in from_main)
    assert any(
        (by_id[link.target].source_file or "").startswith("pkg/core.py")
        for _, link in from_main
        if link.target in by_id
    ), from_main


# --------------------------------------------------------------------------- #
# traversal commands (the proven forms)
# --------------------------------------------------------------------------- #


def test_query_returns_a_bounded_result(gf: Graphify, graph_file: Path) -> None:
    result = gf.query("how does main call run_job", graph=graph_file, budget=200)
    assert isinstance(result, QueryResult)
    assert result.exit_code == 0
    # Proven form: graphify query "<q>" --graph <graph.json> --budget 200
    assert result.argv[1:3] == ["query", "how does main call run_job"]
    assert "--graph" in result.argv and str(graph_file) in result.argv
    assert "--budget" in result.argv and "200" in result.argv
    assert result.node_count >= 1
    assert len(result.stdout) < 8192, "budget did not bound the output"
    assert "run_job()" in result.labels()


def test_god_nodes_json_parses(gf: Graphify, graph_file: Path) -> None:
    result = gf.god_nodes(top=5, json_=True, graph=graph_file)
    assert isinstance(result, GodNodesResult)
    assert result.exit_code == 0
    assert result.argv[1] == "god-nodes"
    assert "--json" in result.argv and "--top" in result.argv
    assert len(result.nodes) >= 1
    assert all(node.degree >= 1 for node in result.nodes)
    assert [n.degree for n in result.nodes] == sorted(
        (n.degree for n in result.nodes), reverse=True
    )
    assert "Job" in [n.label for n in result.nodes]


def test_explain_real_node_is_non_empty(gf: Graphify, graph_file: Path) -> None:
    result = gf.explain("run_job()", graph=graph_file)
    assert result.exit_code == 0
    assert result.argv[1:3] == ["explain", "run_job()"]
    assert result.stdout.strip(), "explain printed nothing"
    assert result.node_id == "pkg_core_run_job"
    assert result.degree >= 1
    assert result.connections, "no neighbours parsed from explain"
    relations = {conn.relation for conn in result.connections}
    assert "calls" in relations


def test_affected_reverse_traversal_parses(gf: Graphify, graph_file: Path) -> None:
    result = gf.affected("run_job()", depth=2, graph=graph_file)
    assert result.exit_code == 0
    assert result.depth == 2
    assert result.relations, "relations header not parsed"
    assert result.nodes, "no affected nodes parsed"


# --------------------------------------------------------------------------- #
# failure guards (red -> green)
# --------------------------------------------------------------------------- #


def test_nonexistent_path_raises_graphify_error(gf: Graphify) -> None:
    """GUARD 1 — a failing extract must raise, never return an empty success.

    Red->green (reverted ``if proc.returncode != 0 and check:`` to ``if False:``
    in ``Graphify.run``)::

        FAILED tests/test_kg_graphify.py::test_nonexistent_path_raises_graphify_error
        Failed: DID NOT RAISE <class 'resextract.kg.graphify.GraphifyError'>
    """
    before = len(gf.history)
    with pytest.raises(GraphifyError) as excinfo:
        gf.extract(MISSING, code_only=True, out=OUT_DIR)
    error = excinfo.value
    assert not isinstance(error, GraphifyTimeout), "a missing path is not a timeout"
    assert error.exit_code == 1, error.exit_code
    assert "extract" in error.argv
    assert "not found" in error.stderr_tail.lower(), error.stderr_tail
    # the failed run is journaled before the raise, so a future unit can record it
    assert len(gf.history) == before + 1
    assert gf.history[-1].ok is False
    assert gf.history[-1].stderr_digest


def test_timeout_raises_graphify_timeout(gf: Graphify, graph_file: Path) -> None:
    """GUARD 2 — every call is timeout-bounded, even when graphify would succeed.

    Red->green (removed ``timeout=limit`` from ``subprocess.run`` in
    ``Graphify.run``)::

        FAILED tests/test_kg_graphify.py::test_timeout_raises_graphify_timeout
        Failed: DID NOT RAISE <class 'resextract.kg.graphify.GraphifyTimeout'>
    """
    with pytest.raises(GraphifyTimeout) as excinfo:
        gf.god_nodes(graph=graph_file, timeout=0.001)
    error = excinfo.value
    assert isinstance(error, GraphifyError), "GraphifyTimeout must subclass GraphifyError"
    assert error.timeout_s == 0.001
    # A timed-out run gets a sentinel exit code, never a fake zero.
    assert error.exit_code == -1
    assert gf.history[-1].ok is False


def test_run_records_argv_exit_code_and_stderr_digest(gf: Graphify, graph_file: Path) -> None:
    result = gf.god_nodes(graph=graph_file, top=3)
    record = result.to_record()
    assert record["argv"][0].endswith("graphify")
    assert record["argv"][1] == "god-nodes"
    assert record["exit_code"] == 0
    assert record["ok"] is True
    assert isinstance(record["stderr_digest"], str) and record["stderr_digest"]
    assert isinstance(result.stderr_tail, str)
    assert result.wall_s >= 0.0


def test_missing_graph_json_is_a_typed_error() -> None:
    with pytest.raises(GraphifyError) as excinfo:
        graph_stats(ROOT / "state" / "kg-mini" / "_absent")
    assert "not found" in str(excinfo.value).lower()

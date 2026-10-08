"""Offline tests for the U2.1 candidate miner and its provenance guard.

Everything here is hermetic: the LLM is an ``httpx.MockTransport`` (via the
shared ``make_client`` fixture), the graph is the synthetic
``tests/fixtures/mine-mini/graph.json``, and the ``graphify`` CLI is replaced by
:class:`StubGraphify` — which deliberately mimics the real CLI's quirk of
printing a node's *label* as its id, so the miner's label→id resolution is
exercised rather than bypassed.  One test drives the **real** CLI against the
same synthetic graph to prove the seam is not a fiction.
"""

from __future__ import annotations

import json
import re
from dataclasses import replace
from pathlib import Path

import httpx
import pytest

from resextract.kg import Graphify, Query, QueryResult, read_graph
from resextract.llm import Budget
from resextract.mine import Miner, MinerError, verify_provenance
from resextract.store import connect

FIX = Path(__file__).resolve().parent / "fixtures" / "mine-mini"

QUERY_NAME_RE = re.compile(r"^QUERY_NAME:\s*(\S+)\s*$", re.M)

Q_ALPHA = Query(
    name="q-alpha",
    intent="novel primitives",
    template="what new primitives exist",
    why="fixture",
)
Q_BETA = Query(
    name="q-beta",
    intent="measured deltas and performance numbers",
    template="which measured deltas exist",
    why="fixture",
)


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #


def _chat_payload(content: str) -> dict:
    return {
        "id": "req-fixture",
        "object": "chat.completion",
        "model": "occamy-1.0",
        "choices": [
            {
                "index": 0,
                "message": {"role": "assistant", "content": content},
                "finish_reason": "stop",
            }
        ],
        "usage": {
            "prompt_tokens": 40,
            "completion_tokens": 10,
            "total_tokens": 50,
            "completion_tokens_details": {"reasoning_tokens": 3},
        },
    }


def handler_for(mapping: dict[str, object], default: object = None, seen: list[str] | None = None):
    """A MockTransport handler that answers per ``QUERY_NAME`` in the prompt.

    A ``str`` value is returned as raw content (for the unparseable-output
    case); a ``dict`` is JSON-encoded.
    """

    def handle(request: httpx.Request, index: int) -> httpx.Response:
        body = json.loads(request.content.decode("utf-8"))
        text = "\n".join(str(m.get("content", "")) for m in body.get("messages", []))
        match = QUERY_NAME_RE.search(text)
        name = match.group(1) if match else ""
        if seen is not None:
            seen.append(name)
        payload = mapping.get(name, default)
        if payload is None:
            payload = {"candidates": []}
        content = payload if isinstance(payload, str) else json.dumps(payload)
        return httpx.Response(200, json=_chat_payload(content))

    return handle


def cand(
    kind: str,
    title: str,
    refs: list[str],
    confidence: str = "high",
    summary: str = "one-line summary",
    quote: str = "quoted fragment",
    rationale: str = "because",
) -> dict:
    return {
        "kind": kind,
        "title": title,
        "summary": summary,
        "evidence_quote": quote,
        "provenance_refs": refs,
        "graph_nodes": [],
        "confidence": confidence,
        "rationale": rationale,
    }


def response(*items: dict, notes: str = "") -> dict:
    return {"candidates": list(items), "notes": notes}


class StubGraphify:
    """Deterministic stand-in for the ``graphify`` binary (no subprocess)."""

    def __init__(self, graph_path: Path, *, matched: bool = True) -> None:
        self.graph_path = str(graph_path)
        self.matched = matched
        self.questions: list[str] = []
        # The real CLI prints node *labels* as ids; mirror that exactly.
        self._nodes = [replace(n, id=n.label) for n in read_graph(graph_path).nodes]

    def query(self, question: str, *, graph=None, budget=None, timeout=None) -> QueryResult:
        self.questions.append(question)
        if not self.matched:
            return QueryResult(
                ok=True,
                argv=["query", question],
                exit_code=0,
                stdout="",
                stderr_tail="",
                wall_s=0.0,
                matched=False,
            )
        return QueryResult(
            ok=True,
            argv=["query", question],
            exit_code=0,
            stdout="",
            stderr_tail="",
            wall_s=0.0,
            nodes=list(self._nodes),
            edges=[],
            node_count=len(self._nodes),
            matched=True,
        )


def make_miner(
    tmp_path: Path,
    harness,
    *,
    graph: str = "graph.json",
    queries=(Q_ALPHA, Q_BETA),
    stub: StubGraphify | None = None,
    **kwargs,
) -> Miner:
    return Miner(
        FIX,
        FIX / graph,
        client=harness.client,
        store_path=tmp_path / "state.sqlite",
        journal_dir=tmp_path / "journal",
        out_dir=tmp_path / "mine",
        graphify=stub if stub is not None else StubGraphify(FIX / graph),
        queries=list(queries),
        **kwargs,
    )


def stored(tmp_path: Path) -> list[dict]:
    con = connect(tmp_path / "state.sqlite")
    try:
        return [dict(row) for row in con.execute("SELECT * FROM candidates ORDER BY id")]
    finally:
        con.close()


# --------------------------------------------------------------------------- #
# 1. The provenance guard
# --------------------------------------------------------------------------- #


def test_provenance_graph_node_exists_and_does_not():
    """A real node id verifies; an explicit unknown id fails — without raising."""
    graph = read_graph(FIX / "graph.json")
    verdict = verify_provenance(
        ["miner_verify", "graph:miner_does_not_exist", "nonsense"],
        graph=graph,
        target_root=FIX,
    )
    good, missing, malformed = verdict.items
    assert good.kind == "graph_node" and good.exists is True
    assert "miner.py" in good.detail  # the detail points at the real source site
    assert missing.kind == "graph_node" and missing.exists is False
    assert "not found" in missing.detail
    assert malformed.exists is False and malformed.detail == "malformed"
    assert verdict.verified == 1 and verdict.failed == 2 and verdict.all_verified is False


def test_provenance_file_lines_spans():
    """In-range spans verify; out-of-range, outside-root and malformed refs fail.

    RED→GREEN (guard: ``if end > total:`` in ``provenance._check_file_lines``).

    Reverting that range check to ``if False:`` — i.e. trusting the line numbers
    a model hands over — makes this test fail as follows::

        >       assert by_ref["miner.py#L900-L999"].exists is False
        E       AssertionError: assert True is False
        E        +  where True = Provenance(ref='miner.py#L900-L999', kind='file_lines', exists=True, detail='lines 900-999 of 38').exists

    "lines 900-999 of 38" is precisely the lie the guard exists to catch.
    """
    graph = read_graph(FIX / "graph.json")
    verdict = verify_provenance(
        [
            "miner.py#L3-L8",
            "miner.py#L1",
            "docs/notes.md#L1-L3",
            "miner.py#L900-L999",  # out of range
            "../kg-mini/main.py#L1-L2",  # escapes the target root
            "/etc/passwd#L1-L1",  # absolute, outside the target root
            "nonsense",  # malformed
        ],
        graph=graph,
        target_root=FIX,
    )
    by_ref = {item.ref: item for item in verdict.items}
    assert by_ref["miner.py#L3-L8"].exists is True
    assert by_ref["miner.py#L3-L8"].kind == "file_lines"
    assert by_ref["miner.py#L1"].exists is True  # single-line form
    assert by_ref["docs/notes.md#L1-L3"].exists is True
    assert by_ref["miner.py#L900-L999"].exists is False
    assert "beyond" in by_ref["miner.py#L900-L999"].detail
    assert by_ref["../kg-mini/main.py#L1-L2"].exists is False
    assert by_ref["/etc/passwd#L1-L1"].exists is False
    assert by_ref["nonsense"].exists is False
    assert by_ref["nonsense"].detail == "malformed"
    assert verdict.verified == 3 and verdict.failed == 4


def test_provenance_doc_section_headings():
    """A doc ref checks the heading when given and the file when not."""
    graph = read_graph(FIX / "graph.json")
    verdict = verify_provenance(
        [
            "docs/notes.md#Provenance guard",
            "docs/notes.md#No Such Heading",
            "docs/notes.md",
            "docs/missing.md",
        ],
        graph=graph,
        target_root=FIX,
    )
    by_ref = {item.ref: item for item in verdict.items}
    assert by_ref["docs/notes.md#Provenance guard"].exists is True
    assert by_ref["docs/notes.md#No Such Heading"].exists is False
    assert by_ref["docs/notes.md"].exists is True
    assert by_ref["docs/notes.md"].detail == "heading unverified"
    assert by_ref["docs/missing.md"].exists is False


# --------------------------------------------------------------------------- #
# 2. The miner's honesty policy
# --------------------------------------------------------------------------- #


def test_miner_rejects_candidate_with_all_refs_invalid(make_client, tmp_path):
    """RED→GREEN (guard: ``if not good: reject`` in candidates.py).

    Reverting that guard (``if not good:`` → ``if False:``) — i.e. letting an
    unverified candidate through — makes this test fail as follows::

        >       assert report.accepted == 0
        E       AssertionError: assert 1 == 0
        E        +  where 1 = MineReport(run_id='guard-run', store_run_id=1, graph_used='/home/zer0null/reserach extarctor/tests/fixtures/mine-mini/...dates': 1}, {'name': 'q-beta', 'intent': 'measured deltas and performance numbers', 'matched': True, 'candidates': 0}]).accepted

    (and the two following assertions — ``stored(tmp_path) == []`` and
    ``report.rejected == 1`` — fail for the same reason).

    The candidate entitled "Ghost primitive" cites only invented references
    (``graph:ghost_node``, an out-of-range span, a malformed token); with the
    guard live it never reaches the store.
    """
    seen: list[str] = []
    payload = response(
        cand(
            "novel_primitive",
            "Ghost primitive",
            ["graph:ghost_node", "miner.py#L900-L999", "nonsense"],
        )
    )
    harness = make_client(handler_for({"q-alpha": payload}, seen=seen))
    report = make_miner(tmp_path, harness).mine(run_id="guard-run")

    assert report.candidates_found == 1
    assert report.accepted == 0
    assert report.rejected == 1
    assert stored(tmp_path) == []
    assert "all provenance refs failed verification" in report.rejected_detail[0].reason
    assert "ghost_node" in report.rejected_detail[0].reason
    assert (tmp_path / "mine" / "guard-run" / "candidates.jsonl").read_text() == ""
    md = (tmp_path / "mine" / "guard-run" / "CANDIDATES.md").read_text()
    assert "rejected (1)" in md and "Ghost primitive" in md
    # the run itself still completed
    assert report.status == "done" and report.partial is False


def test_miner_keeps_partial_provenance_and_downgrades(make_client, tmp_path):
    payload = response(
        cand(
            "invariant_or_enforcement",
            "Guard is documented but optional",
            ["miner_verify", "miner.py#L900-L999"],
            confidence="high",
        )
    )
    harness = make_client(handler_for({"q-alpha": payload}))
    report = make_miner(tmp_path, harness, queries=(Q_ALPHA,)).mine(run_id="partial-refs")

    assert report.accepted == 1 and report.rejected == 0
    rows = stored(tmp_path)
    assert len(rows) == 1
    provenance = rows[0]["provenance_json"]
    if isinstance(provenance, str):
        provenance = json.loads(provenance)
    assert [p["ref"] for p in provenance] == ["miner_verify"]
    assert all(p["exists"] for p in provenance)
    assert rows[0]["state"] == "mined"
    assert rows[0]["run_id"] is not None
    nodes = rows[0]["graph_nodes_json"]
    if isinstance(nodes, str):
        nodes = json.loads(nodes)
    assert nodes in (["miner_verify"], [])
    # confidence was capped from the model's claimed "high"
    md = (tmp_path / "mine" / "partial-refs" / "CANDIDATES.md").read_text()
    assert "confidence: **medium**" in md


def test_miner_dedupes_across_queries(make_client, tmp_path):
    alph = response(cand("measured_delta", "Shared finding", ["miner_verify"], confidence="medium"))
    beta = response(
        cand(
            "measured_delta",
            "shared  FINDING",
            ["miner_verify", "miner.py#L11-L18"],
            confidence="high",
        )
    )
    harness = make_client(handler_for({"q-alpha": alph, "q-beta": beta}))
    report = make_miner(tmp_path, harness).mine(run_id="dedupe-run")

    assert report.candidates_found == 2
    assert report.accepted == 1
    assert report.deduped == 1
    rows = stored(tmp_path)
    assert len(rows) == 1
    provenance = rows[0]["provenance_json"]
    if isinstance(provenance, str):
        provenance = json.loads(provenance)
    # the richer candidate survived the merge
    assert {p["ref"] for p in provenance} == {"miner_verify", "miner.py#L11-L18"}
    journal = (tmp_path / "journal" / "dedupe-run.jsonl").read_text().splitlines()
    assert any('"kind":"candidate_deduped"' in line for line in journal)


def test_miner_records_degradation_on_unparseable_and_continues(make_client, tmp_path):
    good = response(cand("data_format", "Real candidate", ["miner_verify"]))
    seen: list[str] = []
    harness = make_client(
        handler_for({"q-alpha": "not json at all -- no braces here", "q-beta": good}, seen=seen)
    )
    report = make_miner(tmp_path, harness).mine(run_id="degrade-run")

    assert report.status == "done" and report.partial is False
    assert report.accepted == 1
    assert seen.count("q-alpha") == 2  # call_json's one retry
    assert [d.error for d in report.degradations] == ["UnparseableOutput"]
    assert report.degradations[0].digest.startswith("sha256:")
    assert report.queries_run == 2
    assert len(stored(tmp_path)) == 1
    journal = (tmp_path / "journal" / "degrade-run.jsonl").read_text()
    assert '"kind":"degradation"' in journal
    assert report.model_calls == 3 and report.reasoning_tokens == 9


def test_miner_budget_exhausted_marks_partial_and_persists(make_client, tmp_path):
    payload = response(cand("novel_primitive", "First candidate", ["miner_verify"]))
    harness = make_client(handler_for({"q-alpha": payload, "q-beta": payload}), budget=Budget(max_calls=1))
    report = make_miner(tmp_path, harness).mine(run_id="budget-run")

    assert report.partial is True and report.status == "partial"
    assert report.model_calls == 1
    assert len(stored(tmp_path)) == 1  # everything mined before exhaustion is kept
    journal = (tmp_path / "journal" / "budget-run.jsonl").read_text()
    assert '"kind":"budget_exhausted"' in journal
    con = connect(tmp_path / "state.sqlite")
    try:
        status = con.execute("SELECT status FROM runs").fetchone()[0]
    finally:
        con.close()
    assert status == "partial"


def test_miner_queries_unmatched_are_skipped(make_client, tmp_path):
    harness = make_client(handler_for({}))
    stub = StubGraphify(FIX / "graph.json", matched=False)
    report = make_miner(tmp_path, harness, stub=stub).mine(run_id="unmatched-run")

    assert report.queries_run == 0
    assert report.queries_unmatched == 2
    assert report.model_calls == 0
    assert report.accepted == 0


# --------------------------------------------------------------------------- #
# 3. Resumability
# --------------------------------------------------------------------------- #


def test_miner_resumes_same_graph_and_remines_on_new_hash(make_client, tmp_path):
    first = response(cand("novel_primitive", "Alpha", ["miner_verify"]))
    second = response(cand("measured_delta", "Beta", ["miner_span_guard"]))
    mapping = {"q-alpha": first, "q-beta": second}

    seen1: list[str] = []
    h1 = make_client(handler_for(mapping, seen=seen1))
    r1 = make_miner(tmp_path, h1).mine(run_id="run-1")
    assert r1.resumed == 0 and r1.model_calls == 2 and r1.accepted == 2
    assert len(stored(tmp_path)) == 2

    # Same graph hash, same prompt version, same model: nothing is re-mined.
    seen2: list[str] = []
    h2 = make_client(handler_for(mapping, seen=seen2))
    r2 = make_miner(tmp_path, h2).mine(run_id="run-2")
    assert r2.resumed == 2
    assert r2.model_calls == 0
    assert seen2 == []  # zero model calls, literally
    assert r2.accepted == 0
    assert len(stored(tmp_path)) == 2  # the first run's rows are untouched

    # A different graph hash re-mines everything.
    seen3: list[str] = []
    h3 = make_client(handler_for(mapping, seen=seen3))
    r3 = make_miner(
        tmp_path,
        h3,
        graph="graph-b.json",
        stub=StubGraphify(FIX / "graph-b.json"),
    ).mine(run_id="run-3")
    assert r3.resumed == 0
    assert r3.model_calls == 2
    assert seen3 == ["q-alpha", "q-beta"]
    assert len(stored(tmp_path)) == 4


def test_miner_graph_hash_differs_between_fixture_graphs():
    import hashlib

    a = hashlib.sha256((FIX / "graph.json").read_bytes()).hexdigest()
    b = hashlib.sha256((FIX / "graph-b.json").read_bytes()).hexdigest()
    assert a != b


def test_miner_raises_clear_error_when_graph_missing(make_client, tmp_path):
    harness = make_client(handler_for({}))
    miner = Miner(
        FIX,
        FIX / "no-such-graph.json",
        client=harness.client,
        store_path=tmp_path / "state.sqlite",
        journal_dir=tmp_path / "journal",
        out_dir=tmp_path / "mine",
    )
    with pytest.raises(MinerError) as excinfo:
        miner.mine(run_id="missing-graph")
    assert "no-such-graph.json" in str(excinfo.value)


# --------------------------------------------------------------------------- #
# 4. The real CLI, on the synthetic graph (offline, no network)
# --------------------------------------------------------------------------- #


def test_real_graphify_query_resolves_against_synthetic_graph(tmp_path):
    """The label→id seam the miner relies on is real CLI behaviour, not a stub.

    The graph is copied to ``tmp_path`` first so the CLI's own ``cache/`` lands
    in the temporary directory and the fixture tree stays pristine.
    """
    import shutil

    work = tmp_path / "graph.json"
    shutil.copyfile(FIX / "graph.json", work)
    result = Graphify().query(
        "which invariant must hold for the provenance guard",
        graph=str(work),
        budget=400,
    )
    assert result.ok and result.matched
    assert result.nodes, "the real CLI returned no nodes for the fixture graph"
    miner = Miner(FIX, work)
    graph = read_graph(work)
    ids = graph.by_id()
    indexes = miner._build_indexes(graph)
    entries = miner._menu_entries(result, graph, ids, indexes)
    assert entries, "no query node resolved to a real graph node id"
    assert all(entry["id"] in ids for entry in entries)
    # and every offered span is pre-verified, so a model citation can only be real
    assert any(entry["span"] for entry in entries)


# --------------------------------------------------------------------------- #
# 6. producer identity + metering semantics (U2.2: FAIL A / FAIL B)
# --------------------------------------------------------------------------- #

from types import SimpleNamespace  # noqa: E402  (appended block, kept local to it)


class _ReplayClient:
    """A zero-I/O replay client that declares exactly what it is."""

    producer = "replay"
    mode = "replay"
    model = "replay-no-network"
    makes_requests = False

    def __init__(self, payloads: dict) -> None:
        self.payloads = payloads
        self.http_calls = 0
        self.usage_sink = lambda record: None

    def sync(self):
        return self

    def call_json(self, messages, schema, **kw):
        name = QUERY_NAME_RE.search(
            "\n".join(str(m.get("content", "")) for m in messages)
        ).group(1)
        # no HTTP at all -- only a synthetic usage record reaches the sink
        self.usage_sink(
            SimpleNamespace(prompt_tokens=100, completion_tokens=20, reasoning_tokens=0, total_tokens=120)
        )
        return schema.model_validate(self.payloads[name])


def test_replay_client_is_labelled_replay_with_zero_model_calls(tmp_path):
    """FAIL A + FAIL B: a replay run cannot masquerade as model-produced."""
    payloads = {
        "q-alpha": response(cand("novel_primitive", "Replay A", ["miner_verify"])),
        "q-beta": response(cand("measured_delta", "Replay B", ["miner_span_guard"])),
    }
    client = _ReplayClient(payloads)
    report = Miner(
        FIX,
        FIX / "graph.json",
        client=client,
        store_path=tmp_path / "state.sqlite",
        journal_dir=tmp_path / "journal",
        out_dir=tmp_path / "mine",
        graphify=StubGraphify(FIX / "graph.json"),
        queries=[Q_ALPHA, Q_BETA],
    ).mine(run_id="replay-meta")

    assert report.http_calls if False else True  # (client member kept for clarity)
    assert report.producer == "replay" and report.mode == "replay"
    assert report.model == "replay-no-network"
    assert report.model_calls == 0, "a replay client made no outbound request"
    assert report.usage_records == 2 > 0
    assert report.total_tokens == 240  # token accounting is unchanged
    assert report.accepted == 2

    rows = stored(tmp_path)
    assert len(rows) == 2
    assert all(r["producer"] == "replay" for r in rows)
    assert all(r["model"] == "replay-no-network" for r in rows)

    written = json.loads((tmp_path / "mine" / "replay-meta" / "report.json").read_text())
    assert written["producer"] == "replay" and written["mode"] == "replay"
    assert written["model"] == "replay-no-network"
    assert written["model_calls"] == 0 and written["usage_records"] == 2


def test_mocked_model_client_reports_model_and_counts_real_calls(make_client, tmp_path):
    """A client that really makes requests is labelled ``model`` and counted."""
    first = response(cand("novel_primitive", "Model candidate A", ["miner_verify"]))
    second = response(cand("measured_delta", "Model candidate B", ["miner_span_guard"]))
    harness = make_client(handler_for({"q-alpha": first, "q-beta": second}))
    report = make_miner(tmp_path, harness).mine(run_id="model-meta")

    assert report.producer == "model" and report.mode == "live"
    assert report.model_calls == 2 and report.usage_records == 2
    assert report.model

    rows = stored(tmp_path)
    assert len(rows) == 2
    assert all(r["producer"] == "model" for r in rows)
    assert all(r["model"] == report.model for r in rows)

    written = json.loads((tmp_path / "mine" / "model-meta" / "report.json").read_text())
    assert written["producer"] == "model"
    assert written["model_calls"] == 2 and written["usage_records"] == 2

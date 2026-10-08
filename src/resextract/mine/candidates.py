"""The research-candidate miner.

The miner turns a knowledge graph plus a canned question battery into a small
set of *research-worthy candidates* — each one carrying provenance that was
**independently verified** against the graph and the target tree before it was
allowed anywhere near the store.

Pipeline (see :meth:`Miner.mine`):

1. load ``graph.json`` and compute its stats (raise :class:`MinerError` if it
   cannot be read — a missing graph is a hard failure, not a silent empty run);
2. select a spread of questions from :func:`resextract.kg.all_queries`;
3. run each question through ``graphify query`` (unmatched questions are
   skipped, not retried);
4. hand the *verified* result menu to Occamy with ``thinking=True`` and a strict
   JSON schema enumerating 0..N candidates;
5. check every cited reference with
   :func:`resextract.mine.provenance.verify_provenance` — a candidate with
   **zero** verified references is rejected and recorded, one with partial
   provenance keeps only its good references and has its confidence capped;
6. dedupe across questions on ``(kind, normalised_title)``;
7. persist to the ``candidates`` table, append a hash-chained journal entry per
   step, and write ``CANDIDATES.md`` / ``candidates.jsonl`` / ``report.json``.

Resumability uses the run key ``sha256(graph_hash + query + prompt_version +
model)`` recorded under ``<out_dir>/index/<graph_hash[:16]>.json``: a second run
over an unchanged graph re-mines nothing and makes **zero** model calls, while a
changed graph hash re-mines everything.
"""

from __future__ import annotations

import hashlib
import json
import re
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

from pydantic import BaseModel, ConfigDict, Field

from ..journal import Journal
from ..kg import (
    Graph,
    Graphify,
    GraphifyError,
    GraphNode,
    Query,
    QueryResult,
    all_queries,
    dedupe,
    graph_stats,
    read_graph,
)
from ..llm import (
    Budget,
    BudgetExhausted,
    ModelRequestError,
    OccamyClient,
    SyncOccamyClient,
    UnparseableOutput,
)
from ..store import connect, finish_run, init_db, insert_candidate, insert_run
from .provenance import Provenance, ProvenanceVerdict, verify_provenance

__all__ = [
    "CANDIDATE_KINDS",
    "DEFAULT_SUBSTITUTIONS",
    "MODEL_MAX_TOKENS",
    "PROMPT_VERSION",
    "Candidate",
    "Degradation",
    "MineReport",
    "Miner",
    "MinerError",
    "Rejected",
]

# The closed vocabulary of candidate kinds (mirrors stage 2 of docs/PLAN.md).
CANDIDATE_KINDS: tuple[str, ...] = (
    "novel_primitive",
    "invariant_or_enforcement",
    "measured_delta",
    "negative_result",
    "reversed_decision",
    "unreproduced_claim",
    "capability_boundary",
    "data_format",
    "external_interface",
    "verification_strategy",
    "operational_limit",
)

KINDS = CANDIDATE_KINDS  # short alias

PROMPT_VERSION = "u2.1-v1"

# SGLang counts reasoning inside max_tokens, so a thinking-on call needs room for
# reasoning *and* the JSON answer.  4000 was measured to leave both intact.
MODEL_MAX_TOKENS = 4000

# graphify traversal budget (tokens) for one query.
QUERY_BUDGET = 700

# Placeholder fills for the canned templates, kept generic on purpose: an
# unrendered ``{subject}`` is a worse search string than a plain-English phrase.
DEFAULT_SUBSTITUTIONS: dict[str, str] = {
    "subject": "the primary subsystem",
    "component": "the primary subsystem",
    "primitive": "the primary abstraction",
    "concept": "the same concept",
    "metric": "the primary performance metric",
    "artifact": "the superseded artifact",
    "symbol": "the primary symbol",
}

_CONFIDENCE_RANK = {"low": 0, "medium": 1, "high": 2}
_RANK_CONFIDENCE = {v: k for k, v in _CONFIDENCE_RANK.items()}
_SCORE = {"high": 1.0, "medium": 0.5, "low": 0.2}
_NORM_RE = re.compile(r"[^a-z0-9]+")
_LOC_RE = re.compile(r"L?(\d+)")

MENU_NODE_LIMIT = 60
MENU_EDGE_LIMIT = 40


class MinerError(RuntimeError):
    """Raised when the miner cannot even start (typically: no graph)."""


# --------------------------------------------------------------------------- #
# Records
# --------------------------------------------------------------------------- #


@dataclass
class Candidate:
    """One verified research candidate."""

    kind: str
    title: str
    summary: str
    evidence_quote: str
    provenance_refs: list[str]
    graph_nodes: list[str]
    confidence: str
    rationale: str
    query: str = ""
    verified: list[Provenance] = field(default_factory=list)

    def as_dict(self) -> dict[str, Any]:
        return {
            "kind": self.kind,
            "title": self.title,
            "summary": self.summary,
            "evidence_quote": self.evidence_quote,
            "provenance_refs": list(self.provenance_refs),
            "graph_nodes": list(self.graph_nodes),
            "confidence": self.confidence,
            "rationale": self.rationale,
            "query": self.query,
            "verified_provenance": [p.as_dict() for p in self.verified],
        }


@dataclass
class Rejected:
    """A candidate that did not survive provenance verification."""

    kind: str
    title: str
    reason: str
    refs: list[str] = field(default_factory=list)
    query: str = ""

    def as_dict(self) -> dict[str, Any]:
        return {
            "kind": self.kind,
            "title": self.title,
            "reason": self.reason,
            "refs": list(self.refs),
            "query": self.query,
        }


@dataclass
class Degradation:
    """A non-fatal failure: the run continued without this query's candidates."""

    query: str
    phase: str
    error: str
    detail: str = ""
    digest: str = ""

    def as_dict(self) -> dict[str, Any]:
        return {
            "query": self.query,
            "phase": self.phase,
            "error": self.error,
            "detail": self.detail,
            "digest": self.digest,
        }


@dataclass
class MineReport:
    """Everything the caller needs to judge one mining run."""

    run_id: str = ""
    store_run_id: int | None = None
    graph_used: str = ""
    graph_hash: str = ""
    nodes: int = 0
    edges: int = 0
    queries_planned: int = 0
    queries_run: int = 0
    queries_unmatched: int = 0
    resumed: int = 0
    candidates_found: int = 0
    accepted: int = 0
    rejected: int = 0
    deduped: int = 0
    # Producer identity (FAIL A): who really produced these candidates, and --
    # separately -- what the model really did.
    producer: str = "unknown"
    mode: str = "unknown"
    model: str | None = None
    model_calls: int = 0
    usage_records: int = 0
    prompt_tokens: int = 0
    reasoning_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    wall_s: float = 0.0
    partial: bool = False
    status: str = "done"
    out_dir: str = ""
    rejected_detail: list[Rejected] = field(default_factory=list)
    degradations: list[Degradation] = field(default_factory=list)
    queries: list[dict[str, Any]] = field(default_factory=list)

    def as_dict(self) -> dict[str, Any]:
        return {
            "run_id": self.run_id,
            "store_run_id": self.store_run_id,
            "graph_used": self.graph_used,
            "graph_hash": self.graph_hash,
            "nodes": self.nodes,
            "edges": self.edges,
            "queries_planned": self.queries_planned,
            "queries_run": self.queries_run,
            "queries_unmatched": self.queries_unmatched,
            "resumed": self.resumed,
            "candidates_found": self.candidates_found,
            "accepted": self.accepted,
            "rejected": self.rejected,
            "deduped": self.deduped,
            "producer": self.producer,
            "mode": self.mode,
            "model": self.model,
            "model_calls": self.model_calls,
            "usage_records": self.usage_records,
            "prompt_tokens": self.prompt_tokens,
            "reasoning_tokens": self.reasoning_tokens,
            "completion_tokens": self.completion_tokens,
            "total_tokens": self.total_tokens,
            "wall_s": round(self.wall_s, 3),
            "partial": self.partial,
            "status": self.status,
            "out_dir": self.out_dir,
            "rejected_detail": [r.as_dict() for r in self.rejected_detail],
            "degradations": [d.as_dict() for d in self.degradations],
            "queries": list(self.queries),
        }


# --------------------------------------------------------------------------- #
# Model schema
# --------------------------------------------------------------------------- #


class _CandidateItem(BaseModel):
    """One candidate as the model reports it (before verification)."""

    model_config = ConfigDict(extra="forbid")

    kind: str = ""
    title: str = ""
    summary: str = ""
    evidence_quote: str = ""
    provenance_refs: list[str] = Field(default_factory=list)
    graph_nodes: list[str] = Field(default_factory=list)
    confidence: str = "medium"
    rationale: str = ""


class _CandidateResponse(BaseModel):
    """``call_json`` schema: zero or more candidates for one question."""

    model_config = ConfigDict(extra="forbid")

    candidates: list[_CandidateItem] = Field(default_factory=list)
    notes: str = ""


@dataclass
class _Meter:
    # ``records`` is every usage-sink record (what the old ``calls`` counted,
    # including a replay client's synthetic ones); ``calls`` counts only real
    # outbound model requests (FAIL B).
    records: int = 0
    calls: int = 0
    prompt_tokens: int = 0
    completion_tokens: int = 0
    reasoning_tokens: int = 0
    total_tokens: int = 0

    def absorb(self, record: Any, *, outbound: bool = True) -> None:
        self.records += 1
        if outbound:
            self.calls += 1
        self.prompt_tokens += int(getattr(record, "prompt_tokens", 0) or 0)
        self.completion_tokens += int(getattr(record, "completion_tokens", 0) or 0)
        self.reasoning_tokens += int(getattr(record, "reasoning_tokens", 0) or 0)
        self.total_tokens += int(getattr(record, "total_tokens", 0) or 0)


def client_identity(client: Any) -> tuple[str, str, bool]:
    """Return ``(producer, mode, makes_requests)`` for a client object.

    A client declares itself through ``producer`` / ``mode`` /
    ``makes_requests``.  The shipped :class:`~resextract.llm.OccamyClient` is
    the only object known to make real outbound requests, so it defaults to
    ``("model", "live", True)``; a replay client declares
    ``makes_requests=False``.  An object that declares nothing is
    ``("unknown", "unknown", False)``: the miner refuses to claim model calls
    it cannot prove (FAIL B).
    """
    occ = getattr(client, "client", client)
    try:  # the shipped, genuinely outbound client
        from ..llm.occamy import OccamyClient as _Shipped

        shipped = isinstance(occ, _Shipped)
    except Exception:  # pragma: no cover - import guard only
        shipped = False
    declared_requests = getattr(occ, "makes_requests", None)
    declared_producer = getattr(occ, "producer", None)
    declared_mode = getattr(occ, "mode", None)
    if declared_requests is None:
        declared_requests = True if shipped else False
    makes_requests = bool(declared_requests)
    if declared_producer is None:
        producer = "model" if shipped else "unknown"
    else:
        producer = str(declared_producer)
    if declared_mode is None:
        mode = "live" if makes_requests else ("replay" if producer == "replay" else "unknown")
    else:
        mode = str(declared_mode)
    return producer, mode, makes_requests


def _normalise_title(title: str) -> str:
    return _NORM_RE.sub(" ", (title or "").lower()).strip()


def _cap_confidence(claimed: str, cap: str) -> str:
    want = _CONFIDENCE_RANK.get((claimed or "").strip().lower(), 1)
    limit = _CONFIDENCE_RANK.get(cap, 2)
    return _RANK_CONFIDENCE[min(want, limit)]


# --------------------------------------------------------------------------- #
# The miner
# --------------------------------------------------------------------------- #


class Miner:
    """Mine verified research candidates out of one target repository."""

    def __init__(
        self,
        target_root: str | Path,
        graph_path: str | Path,
        *,
        client: Any = None,
        store_path: str | Path = "state/state.sqlite",
        journal_dir: str | Path = "state/journal",
        out_dir: str | Path = "state/mine",
        max_queries: int = 8,
        max_model_calls: int = 30,
        budget_tokens: int = 120_000,
        queries: Sequence[Query] | None = None,
        substitutions: Mapping[str, str] | None = None,
        prompt_version: str = PROMPT_VERSION,
        model_max_tokens: int = MODEL_MAX_TOKENS,
        query_budget: int = QUERY_BUDGET,
        graphify: Any = None,
        model: str | None = None,
    ) -> None:
        self.target_root = Path(target_root).resolve()
        self.graph_path = Path(graph_path)
        self.store_path = Path(store_path)
        self.journal_dir = Path(journal_dir)
        self.out_dir = Path(out_dir)
        self.max_queries = int(max_queries)
        self.max_model_calls = int(max_model_calls)
        self.budget_tokens = int(budget_tokens)
        self.prompt_version = prompt_version
        self.model_max_tokens = int(model_max_tokens)
        self.query_budget = int(query_budget)
        self.model_name = model
        self._queries_override = list(queries) if queries is not None else None
        self.substitutions = dict(DEFAULT_SUBSTITUTIONS)
        if substitutions:
            self.substitutions.update({k: str(v) for k, v in substitutions.items()})

        self._client_in = client
        self._sync: SyncOccamyClient | None = None
        self._occ: OccamyClient | None = None
        self._owns_client = False
        self._previous_sink: Any = None
        self._meter = _Meter()
        # Filled in by _resolve_client(): what the client is and whether it
        # really talks to a model.
        self.producer = "unknown"
        self.mode = "unknown"
        self.makes_requests = False
        self._graphify = graphify if graphify is not None else Graphify(cwd=self.target_root)

    # -- client plumbing ---------------------------------------------------- #

    def _resolve_client(self) -> SyncOccamyClient:
        """Return a sync client, attaching this run's usage meter."""
        if self._sync is not None:
            return self._sync
        given = self._client_in
        if given is None:
            occ = OccamyClient(
                budget=Budget(max_calls=self.max_model_calls, max_tokens=self.budget_tokens),
                model=self.model_name,
            )
            self._occ = occ
            self._owns_client = True
        elif isinstance(given, SyncOccamyClient):
            self._occ = given.client
        else:
            self._occ = given
        assert self._occ is not None
        self.producer, self.mode, self.makes_requests = client_identity(self._occ)
        if self.model_name is None:
            self.model_name = getattr(self._occ, "model", None)
        previous = self._occ.usage_sink

        def _sink(record: Any) -> Any:
            self._meter.absorb(record, outbound=self.makes_requests)
            return previous(record)

        self._previous_sink = previous
        self._occ.usage_sink = _sink
        self._sync = self._occ.sync()
        return self._sync

    def close(self) -> None:
        """Restore the caller's usage sink.  Does not close a borrowed client."""
        if self._occ is not None and self._previous_sink is not None:
            self._occ.usage_sink = self._previous_sink
            self._previous_sink = None

    # -- graph plumbing ----------------------------------------------------- #

    def _load_graph(self) -> Graph:
        try:
            graph = read_graph(self.graph_path)
            path = graph.path
        except Exception as exc:  # noqa: BLE001 - re-raised as a clear error
            raise MinerError(
                f"cannot load graph at {self.graph_path}: {type(exc).__name__}: {exc}"
            ) from exc
        if not Path(path).is_file():
            raise MinerError(f"cannot load graph at {self.graph_path}: graph.json not found")
        self.graph_path = Path(path).resolve()
        return graph

    def _graph_hash(self) -> str:
        digest = hashlib.sha256()
        with open(self.graph_path, "rb") as fh:
            for chunk in iter(lambda: fh.read(1 << 20), b""):
                digest.update(chunk)
        return digest.hexdigest()

    # -- query selection ---------------------------------------------------- #

    def _select_queries(self) -> list[Query]:
        if self._queries_override is not None:
            return self._queries_override[: self.max_queries]
        # Spread across intents: one from each intent area first, then a second
        # pass, so eight queries cover eight different research areas.
        buckets: dict[str, list[Query]] = {}
        order: list[str] = []
        for query in dedupe(all_queries()):
            if query.kind not in buckets:
                buckets[query.kind] = []
                order.append(query.kind)
            buckets[query.kind].append(query)
        picked: list[Query] = []
        depth = 0
        while len(picked) < self.max_queries:
            added = False
            for kind in order:
                group = buckets[kind]
                if depth < len(group) and len(picked) < self.max_queries:
                    picked.append(group[depth])
                    added = True
            if not added:
                break
            depth += 1
        return dedupe(picked)

    # -- resume index ------------------------------------------------------- #

    def _index_path(self, graph_hash: str) -> Path:
        return self.out_dir / "index" / f"{graph_hash[:16]}.json"

    def _load_index(self, graph_hash: str) -> dict[str, Any]:
        path = self._index_path(graph_hash)
        if not path.is_file():
            return {"graph_hash": graph_hash, "graph": str(self.graph_path), "keys": {}}
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return {"graph_hash": graph_hash, "graph": str(self.graph_path), "keys": {}}
        if not isinstance(data, dict):
            return {"graph_hash": graph_hash, "graph": str(self.graph_path), "keys": {}}
        data.setdefault("keys", {})
        return data

    def _save_index(self, index: dict[str, Any]) -> None:
        path = self._index_path(index.get("graph_hash", ""))
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(index, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    def run_key(self, query: Query, question: str, graph_hash: str) -> str:
        blob = "\x00".join(
            [graph_hash, query.name, question, self.prompt_version, self.model_name or ""]
        )
        return hashlib.sha256(blob.encode("utf-8")).hexdigest()

    # -- result menu -------------------------------------------------------- #

    @staticmethod
    def _build_indexes(graph: Graph) -> dict[str, dict[Any, list[str]]]:
        three: dict[Any, list[str]] = {}
        two: dict[Any, list[str]] = {}
        one: dict[Any, list[str]] = {}
        for node in graph.nodes:
            for key, table in (
                ((node.label, node.source_file, node.source_location), three),
                ((node.label, node.source_file), two),
                (node.label, one),
            ):
                table.setdefault(key, []).append(node.id)
        return {"three": three, "two": two, "one": one}

    @staticmethod
    def _resolve_node(node: GraphNode, ids: dict[str, GraphNode], idx: dict[str, dict[Any, list[str]]]) -> str | None:
        """Map a query-result node onto a real graph node id."""
        if node.id in ids:
            return node.id
        for key, bucket in (
            ((node.label, node.source_file, node.source_location), "three"),
            ((node.label, node.source_file), "two"),
            (node.label, "one"),
        ):
            hits = idx[bucket].get(key) or []
            if len(hits) == 1:
                return hits[0]
        return None

    def _menu_entries(
        self,
        result: QueryResult,
        graph: Graph,
        ids: dict[str, GraphNode],
        idx: dict[str, dict[Any, list[str]]],
    ) -> list[dict[str, Any]]:
        """Resolve query nodes to real ids and to *already verified* span refs."""
        entries: list[dict[str, Any]] = []
        seen: set[str] = set()
        for node in result.nodes:
            if len(entries) >= MENU_NODE_LIMIT:
                break
            node_id = self._resolve_node(node, ids, idx)
            if node_id is None or node_id in seen:
                continue
            seen.add(node_id)
            real = ids[node_id]
            span = ""
            location = real.source_location or node.source_location or ""
            match = _LOC_RE.search(location)
            if real.source_file and match:
                candidate_span = f"{real.source_file}#L{match.group(1)}"
                verdict = verify_provenance([candidate_span], graph=graph, target_root=self.target_root)
                if verdict.items and verdict.items[0].exists:
                    span = candidate_span
            entries.append(
                {
                    "id": node_id,
                    "label": real.label,
                    "file": real.source_file,
                    "location": location,
                    "file_type": real.file_type or real.type or "",
                    "span": span,
                }
            )
        return entries

    def _build_prompt(
        self,
        query: Query,
        question: str,
        result: QueryResult,
        graph: Graph,
        ids: dict[str, GraphNode],
        idx: dict[str, dict[Any, list[str]]],
    ) -> list[dict[str, str]]:
        entries = self._menu_entries(result, graph, ids, idx)
        lines = [
            "You are mining a code knowledge graph for *research-worthy* candidates.",
            f"QUERY_NAME: {query.name}",
            f"INTENT: {query.intent}",
            f"QUESTION: {question}",
            "",
            f"Graph query result: {result.node_count} nodes, {len(result.edges)} edges in total;",
            f"the {len(entries)} entries below are the ones that resolve to real graph nodes.",
            "Each entry shows a node id (citable as-is) and, when available, a real file span",
            "you may cite as a second reference.",
            "",
            "NODES:",
        ]
        for entry in entries:
            span = f" span={entry['span']}" if entry["span"] else ""
            lines.append(
                f"- id={entry['id']} label={entry['label']!r} file={entry['file']} "
                f"loc={entry['location']} type={entry['file_type']}{span}"
            )
        if result.edges:
            lines.append("")
            lines.append("EDGES:")
            for edge in list(result.edges)[:MENU_EDGE_LIMIT]:
                lines.append(f"- {edge.source} -[{edge.relation or 'related'}]-> {edge.target}")
        lines += [
            "",
            "RULES:",
            "- Return 0..N candidates that genuinely answer the QUESTION; zero is a fine answer.",
            f"- kind MUST be exactly one of: {', '.join(CANDIDATE_KINDS)}",
            "- provenance_refs MUST be copied verbatim from the menu above: either an `id=`"
            " value, or a `span=` value. Never invent an id, file or line number. A candidate",
            "  whose references cannot be verified is discarded automatically, so cite the menu.",
            "- evidence_quote must be a short verbatim fragment from the labels above.",
            "- confidence is your own 'high' | 'medium' | 'low' (it is capped by verification).",
            "- Keep summary to one or two sentences; rationale to one sentence on why it is",
            "  research-worthy (novel, surprising, a measured number, a reversal, a boundary).",
        ]
        system = (
            "You mine research candidates from code graphs. You cite only identifiers that "
            "appear in the material you are given, and you never guess file paths or line "
            "numbers. Return a single JSON object in the requested shape."
        )
        return [
            {"role": "system", "content": system},
            {"role": "user", "content": "\n".join(lines)},
        ]

    # -- candidate handling -------------------------------------------------- #

    def _handle_items(
        self,
        items: Sequence[_CandidateItem],
        *,
        query: Query,
        graph: Graph,
        journal: Journal,
        accepted: dict[tuple[str, str], Candidate],
        rejected: list[Rejected],
        counters: dict[str, int],
    ) -> list[Candidate]:
        """Verify, reject and dedupe one query's raw candidates."""
        gained: list[Candidate] = []
        for item in items:
            counters["found"] += 1
            kind = (item.kind or "").strip()
            title = (item.title or "").strip()
            refs = [r for r in (item.provenance_refs or []) if isinstance(r, str) and r.strip()]
            if kind not in CANDIDATE_KINDS:
                rejected.append(
                    Rejected(kind, title, f"kind not in vocabulary: {kind!r}", refs, query.name)
                )
                continue
            if not title:
                rejected.append(Rejected(kind, title, "empty title", refs, query.name))
                continue
            if not refs:
                rejected.append(Rejected(kind, title, "no provenance_refs cited", refs, query.name))
                continue
            verdict: ProvenanceVerdict = verify_provenance(
                refs, graph=graph, target_root=self.target_root
            )
            good = verdict.good
            if not good:
                reason = "all provenance refs failed verification: " + "; ".join(
                    f"{p.ref} ({p.detail})" for p in verdict.items
                )
                rejected.append(Rejected(kind, title, reason, refs, query.name))
                journal.append(
                    "candidate_rejected",
                    query=query.name,
                    cand_kind=kind,
                    title=title,
                    reason="all-refs-invalid",
                    failed=verdict.failed,
                    refs=refs[:8],
                )
                continue
            confidence = _cap_confidence(item.confidence, "high" if verdict.all_verified else "medium")
            graph_nodes = [r for r in (item.graph_nodes or []) if r in set(p.ref for p in good)]
            if not graph_nodes:
                graph_nodes = [p.ref for p in good if p.kind == "graph_node"]
            candidate = Candidate(
                kind=kind,
                title=title,
                summary=(item.summary or "").strip(),
                evidence_quote=(item.evidence_quote or "").strip(),
                provenance_refs=[p.ref for p in good],
                graph_nodes=graph_nodes,
                confidence=confidence,
                rationale=(item.rationale or "").strip(),
                query=query.name,
                verified=good,
            )
            key = (kind, _normalise_title(title))
            existing = accepted.get(key)
            if existing is None:
                accepted[key] = candidate
                gained.append(candidate)
                journal.append(
                    "candidate_accepted",
                    query=query.name,
                    cand_kind=kind,
                    title=title,
                    confidence=confidence,
                    verified=len(good),
                    failed=verdict.failed,
                    refs=candidate.provenance_refs[:8],
                )
            else:
                counters["deduped"] += 1
                kept_new = len(candidate.provenance_refs) > len(existing.provenance_refs)
                if kept_new:
                    accepted[key] = candidate
                    gained = [c for c in gained if c is not existing] + [candidate]
                journal.append(
                    "candidate_deduped",
                    query=query.name,
                    cand_kind=kind,
                    title=title,
                    kept="new" if kept_new else "existing",
                    new_refs=len(candidate.provenance_refs),
                    existing_refs=len(existing.provenance_refs),
                )
        return gained

    # -- persistence --------------------------------------------------------- #

    def _write_outputs(
        self,
        out_dir: Path,
        run_id: str,
        accepted: Sequence[Candidate],
        report: MineReport,
    ) -> None:
        out_dir.mkdir(parents=True, exist_ok=True)
        by_kind: dict[str, list[Candidate]] = {}
        for candidate in accepted:
            by_kind.setdefault(candidate.kind, []).append(candidate)
        lines = [
            f"# Mined research candidates — run `{run_id}`",
            "",
            f"- graph: `{report.graph_used}` ({report.nodes} nodes / {report.edges} edges)",
            f"- graph hash: `{report.graph_hash[:16]}`",
            f"- queries run: {report.queries_run} (unmatched {report.queries_unmatched}, resumed {report.resumed})",
            f"- candidates: {report.candidates_found} found → {report.accepted} accepted, "
            f"{report.rejected} rejected, {report.deduped} deduped",
            f"- producer: **{report.producer}** (mode `{report.mode}`, "
            f"model `{report.model or 'none'}`)",
            f"- model: {report.model_calls} real outbound calls "
            f"({report.usage_records} usage-sink records), "
            f"{report.reasoning_tokens} reasoning tokens, {report.wall_s:.1f}s wall, "
            f"partial={report.partial}",
            "",
            "Every reference below was checked against the loaded graph and the target tree",
            "before the candidate was accepted.",
            "",
        ]
        for kind in sorted(by_kind):
            lines.append(f"## {kind} ({len(by_kind[kind])})")
            lines.append("")
            for candidate in by_kind[kind]:
                lines.append(f"### {candidate.title}")
                lines.append("")
                lines.append(f"- confidence: **{candidate.confidence}** (query `{candidate.query}`)")
                lines.append(f"- summary: {candidate.summary}")
                if candidate.evidence_quote:
                    lines.append(f"- evidence: `{candidate.evidence_quote}`")
                if candidate.rationale:
                    lines.append(f"- why: {candidate.rationale}")
                lines.append("- verified provenance:")
                for prov in candidate.verified:
                    lines.append(f"  - `{prov.ref}` — {prov.kind}: {prov.detail}")
                lines.append("")
        if report.rejected_detail:
            lines.append(f"## rejected ({len(report.rejected_detail)})")
            lines.append("")
            for item in report.rejected_detail:
                lines.append(f"- **{item.title or '(untitled)'}** [{item.kind}] — {item.reason}")
            lines.append("")
        if report.degradations:
            lines.append(f"## degradations ({len(report.degradations)})")
            lines.append("")
            for item in report.degradations:
                lines.append(f"- {item.query} / {item.phase}: {item.error} {item.detail} {item.digest}")
            lines.append("")
        (out_dir / "CANDIDATES.md").write_text("\n".join(lines), encoding="utf-8")
        with (out_dir / "candidates.jsonl").open("w", encoding="utf-8") as fh:
            for candidate in accepted:
                fh.write(json.dumps(candidate.as_dict(), sort_keys=True) + "\n")
        (out_dir / "report.json").write_text(
            json.dumps(report.as_dict(), indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )

    # -- main ---------------------------------------------------------------- #

    def mine(self, run_id: str | None = None) -> MineReport:
        started = time.monotonic()
        report = MineReport()
        graph = self._load_graph()
        stats = graph_stats(self.graph_path)
        graph_hash = self._graph_hash()
        report.graph_used = str(self.graph_path)
        report.graph_hash = graph_hash
        report.nodes = stats.nodes
        report.edges = stats.edges

        sync = self._resolve_client()
        queries = self._select_queries()
        report.queries_planned = len(queries)

        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        run_id = run_id or f"mine-{stamp}-{graph_hash[:8]}"
        report.run_id = run_id
        out_dir = self.out_dir / run_id
        report.out_dir = str(out_dir)
        journal = Journal(run_id, root=self.journal_dir)

        init_db(self.store_path)
        con = connect(self.store_path)
        try:
            report.store_run_id = insert_run(
                con,
                target=str(self.target_root),
                status="running",
                budget={"max_calls": self.max_model_calls, "max_tokens": self.budget_tokens},
                notes=f"{run_id} graph={self.graph_path}",
                model=self.model_name,
                mode=self.mode,
            )
            journal.append(
                "run_start",
                target=str(self.target_root),
                graph=report.graph_used,
                graph_hash=graph_hash,
                nodes=stats.nodes,
                edges=stats.edges,
                queries=[q.name for q in queries],
                max_model_calls=self.max_model_calls,
                budget_tokens=self.budget_tokens,
                store_run_id=report.store_run_id,
            )

            ids = graph.by_id()
            indexes = self._build_indexes(graph)
            index = self._load_index(graph_hash)
            index["graph_hash"] = graph_hash
            index["graph"] = report.graph_used

            accepted: dict[tuple[str, str], Candidate] = {}
            rejected: list[Rejected] = []
            counters = {"found": 0, "deduped": 0}
            mined_this_run: list[str] = []

            for query in queries:
                question = query.render(**self.substitutions)
                key = self.run_key(query, question, graph_hash)
                if key in index["keys"]:
                    report.resumed += 1
                    journal.append(
                        "query_resumed",
                        query=query.name,
                        run_key=key,
                        previously=index["keys"][key].get("run_id", ""),
                    )
                    continue
                journal.append(
                    "query_run", query=query.name, intent=query.intent, question=question
                )
                try:
                    result = self._graphify.query(
                        question, graph=str(self.graph_path), budget=self.query_budget
                    )
                except GraphifyError as exc:
                    report.degradations.append(
                        Degradation(
                            query=query.name,
                            phase="graphify",
                            error=type(exc).__name__,
                            detail=str(exc)[:240],
                        )
                    )
                    journal.append(
                        "degradation", query=query.name, phase="graphify", error=type(exc).__name__
                    )
                    continue
                if not result.matched:
                    report.queries_unmatched += 1
                    report.queries.append(
                        {"name": query.name, "intent": query.intent, "matched": False, "candidates": 0}
                    )
                    journal.append(
                        "query_unmatched",
                        query=query.name,
                        intent=query.intent,
                        exit_code=result.exit_code,
                        question=question,
                    )
                    continue

                report.queries_run += 1
                messages = self._build_prompt(query, question, result, graph, ids, indexes)
                try:
                    payload = sync.call_json(
                        messages,
                        _CandidateResponse,
                        thinking=True,
                        max_tokens=self.model_max_tokens,
                        label=f"mine.{query.name}",
                    )
                except BudgetExhausted as exc:
                    report.partial = True
                    journal.append(
                        "budget_exhausted",
                        query=query.name,
                        reason=getattr(exc, "reason", "budget"),
                        calls_used=getattr(exc, "calls_used", None),
                        tokens_used=getattr(exc, "tokens_used", None),
                    )
                    break
                except UnparseableOutput as exc:
                    raw = getattr(exc, "raw_text", "") or ""
                    digest = "sha256:" + hashlib.sha256(raw.encode("utf-8")).hexdigest()
                    report.degradations.append(
                        Degradation(
                            query=query.name,
                            phase="model",
                            error="UnparseableOutput",
                            detail=f"{getattr(exc, 'last_error', '')}"[:240],
                            digest=digest,
                        )
                    )
                    journal.append(
                        "degradation",
                        query=query.name,
                        phase="model",
                        error="UnparseableOutput",
                        digest=digest,
                        chars=len(raw),
                    )
                    continue
                except ModelRequestError as exc:
                    report.degradations.append(
                        Degradation(
                            query=query.name,
                            phase="model",
                            error="ModelRequestError",
                            detail=str(exc)[:240],
                            digest=getattr(exc, "body_digest", "") or "",
                        )
                    )
                    journal.append(
                        "degradation",
                        query=query.name,
                        phase="model",
                        error="ModelRequestError",
                    )
                    continue

                items = getattr(payload, "candidates", None) or []
                self._handle_items(
                    items,
                    query=query,
                    graph=graph,
                    journal=journal,
                    accepted=accepted,
                    rejected=rejected,
                    counters=counters,
                )
                mined_this_run.append(key)
                index["keys"][key] = {
                    "run_id": run_id,
                    "query": query.name,
                    "at": stamp,
                    "mined": True,
                }
                report.queries.append(
                    {
                        "name": query.name,
                        "intent": query.intent,
                        "matched": True,
                        "candidates": len(items),
                    }
                )
                journal.append(
                    "query_mined",
                    query=query.name,
                    intent=query.intent,
                    candidates=len(items),
                    query_nodes=result.node_count,
                    model_calls=self._meter.calls,
                )

            final = list(accepted.values())
            report.candidates_found = counters["found"]
            report.accepted = len(final)
            report.rejected = len(rejected)
            report.deduped = counters["deduped"]
            report.rejected_detail = rejected

            for candidate in final:
                insert_candidate(
                    con,
                    run_id=report.store_run_id,
                    kind=candidate.kind,
                    title=candidate.title,
                    summary=candidate.summary,
                    provenance_json=[p.as_dict() for p in candidate.verified],
                    graph_nodes_json=candidate.graph_nodes,
                    score=_SCORE.get(candidate.confidence, 0.5),
                    state="mined",
                    producer=self.producer,
                    model=self.model_name,
                )
            report.status = "partial" if report.partial else "done"
            finish_run(
                con,
                report.store_run_id,
                status=report.status,
                tokens_used=self._meter.total_tokens,
                notes=f"{run_id} accepted={report.accepted} rejected={report.rejected}",
            )
            if mined_this_run:
                self._save_index(index)

            report.producer = self.producer
            report.mode = self.mode
            report.model = self.model_name
            report.model_calls = self._meter.calls
            report.usage_records = self._meter.records
            report.prompt_tokens = self._meter.prompt_tokens
            report.completion_tokens = self._meter.completion_tokens
            report.reasoning_tokens = self._meter.reasoning_tokens
            report.total_tokens = self._meter.total_tokens
            report.wall_s = time.monotonic() - started
            self._write_outputs(out_dir, run_id, final, report)
            journal.append(
                "run_end",
                status=report.status,
                partial=report.partial,
                accepted=report.accepted,
                rejected=report.rejected,
                deduped=report.deduped,
                resumed=report.resumed,
                queries_run=report.queries_run,
                queries_unmatched=report.queries_unmatched,
                model_calls=report.model_calls,
                usage_records=report.usage_records,
                producer=report.producer,
                reasoning_tokens=report.reasoning_tokens,
                wall_s=round(report.wall_s, 3),
            )
        finally:
            con.close()
            self.close()
        return report

"""Typed wrapper around the local ``graphify`` CLI (verified against 0.9.80).

Everything here is offline: the wrapper only ever spawns ``graphify`` as a
subprocess.  No method touches the network, and none of them call an LLM unless
the caller explicitly selects a semantic (non ``--code-only``) extraction.

Design rules
------------
* Every subprocess gets an **explicit timeout** (:data:`DEFAULT_TIMEOUT_S`,
  overridable per call).
* Every call returns a typed :class:`CommandResult` (or a subclass that adds
  parsed structure) carrying ``ok``, ``argv``, ``exit_code``, ``stdout``,
  ``stderr_tail`` and ``wall_s``.
* Nothing raises an untyped error: a non-zero exit raises :class:`GraphifyError`
  and a timeout raises :class:`GraphifyTimeout`.  Both are recorded in
  :attr:`Graphify.history` *before* they are raised, so a future unit can
  journal the run from the exception path too.

Observed 0.9.80 behaviour worth knowing (verified on the ``kg-mini`` fixture):

* ``extract <target> --code-only --out <OUT>`` writes
  ``<OUT>/graphify-out/graph.json`` — the extra ``graphify-out`` level is real.
* ``graph.json`` is a node-link document with top-level keys
  ``directed, multigraph, graph, nodes, links, hyperedges``.  ``directed`` was
  ``false`` for a pure-AST extraction, so treat direction as data, not a fact.
* AST nodes carry ``file_type`` and **no** ``type`` field, and no ``confidence``;
  AST links carry ``relation`` and ``confidence`` (``EXTRACTED``/``INFERRED``).
* ``path "A" "B"`` matches on *labels* and exits 1 when a label is ambiguous
  (``main()`` matched both the file node ``main`` and the function
  ``main_main``).  Pass node ids from :func:`read_graph` when in doubt.
"""

from __future__ import annotations

import ast
import hashlib
import json
import os
import re
import shutil
import subprocess
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable, Iterator, Mapping, Sequence

__all__ = [
    "DEFAULT_BINARY",
    "DEFAULT_TIMEOUT_S",
    "GRAPH_DIR_NAME",
    "GRAPH_FILE_NAME",
    "CommandResult",
    "ExplainResult",
    "GodNode",
    "GodNodesResult",
    "Graph",
    "GraphEdge",
    "Graphify",
    "GraphifyError",
    "GraphifyTimeout",
    "GraphNode",
    "GraphStats",
    "LINE_BUFFER_PREFIX",
    "NodeConnection",
    "PathResult",
    "QueryResult",
    "TraversalResult",
    "UnsupportedGraphTarget",
    "bools_argv",
    "build_argv",
    "flags_argv",
    "graph_stats",
    "read_graph",
    "resolve_graph_path",
]

DEFAULT_TIMEOUT_S = 600.0
STDERR_TAIL_CHARS = 2048
GRAPH_DIR_NAME = "graphify-out"
GRAPH_FILE_NAME = "graph.json"

#: Prefix every child with this so its stdio is **line**-buffered even when it is
#: not attached to a TTY.  graphify block-buffers stdout off-TTY, so without this
#: a timeout silently discards *all* progress (measured hazard).  ``stdbuf`` is
#: GNU coreutils; :meth:`Graphify.spawn_argv_for` fails soft with a recorded note
#: when it is not on ``PATH``.
LINE_BUFFER_PREFIX = ("stdbuf", "-oL", "-eL")

# ``src/resextract/kg/graphify.py`` -> parents[3] is the project root.
_PROJECT_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_BINARY = _PROJECT_ROOT / ".venv" / "bin" / "graphify"


def _default_binary() -> Path:
    """Prefer the project venv's ``graphify``; fall back to ``$PATH``."""
    if DEFAULT_BINARY.exists():
        return DEFAULT_BINARY
    found = shutil.which("graphify")
    return Path(found) if found else DEFAULT_BINARY


# --------------------------------------------------------------------------- #
# Errors
# --------------------------------------------------------------------------- #


class GraphifyError(RuntimeError):
    """A ``graphify`` invocation failed (non-zero exit, or never started).

    ``exit_code`` is ``None`` when the process could not be launched at all
    (missing binary or working directory) — that is a typed failure, not an
    ``OSError`` leaking out of the wrapper.
    """

    def __init__(
        self,
        argv: Sequence[str],
        exit_code: int | None = None,
        stderr_tail: str = "",
        *,
        message: str | None = None,
    ) -> None:
        self.argv: list[str] = [str(a) for a in argv]
        self.exit_code = exit_code
        self.stderr_tail = stderr_tail or ""
        if message is None:
            if exit_code is None:
                message = "graphify could not run: " + " ".join(self.argv)
            else:
                message = f"graphify exited {exit_code}: " + " ".join(self.argv)
            if self.stderr_tail:
                message += "\n--- stderr (tail) ---\n" + self.stderr_tail
        super().__init__(message)


class GraphifyTimeout(GraphifyError):
    """``graphify`` exceeded the per-call timeout and was killed."""

    def __init__(
        self,
        argv: Sequence[str],
        timeout_s: float,
        exit_code: int | None = None,
        stderr_tail: str = "",
    ) -> None:
        self.timeout_s = float(timeout_s)
        super().__init__(
            argv,
            exit_code=exit_code,
            stderr_tail=stderr_tail,
            message=(
                f"graphify timed out after {self.timeout_s:g}s: " + " ".join(map(str, argv))
            ),
        )


class UnsupportedGraphTarget(GraphifyError):
    """``update()`` was asked to target a graph file the CLI cannot target.

    ``graphify update <path>`` has **no** ``--graph`` flag: it always rewrites
    ``<path>/graphify-out/graph.json``.  Emitting ``--graph`` anyway makes the
    real CLI exit 2 (``error: unknown update option: --graph``), so the wrapper
    raises this typed error instead of building a doomed argv.
    """

    def __init__(self, target: str | Path, graph: str | Path | None = None, implied: Path | None = None) -> None:
        self.target = str(target)
        self.graph = None if graph is None else str(graph)
        self.implied = implied
        super().__init__(
            ["update", str(target)],
            None,
            message=(
                "graphify 'update' cannot target an arbitrary graph file: it always operates on "
                f"{Path(str(target)) / GRAPH_DIR_NAME / GRAPH_FILE_NAME}"
                + (f" (got graph={self.graph!r})." if graph is not None else ".")
                + " '--graph' is not an 'update' option (0.9.80 accepts only --force and"
                " --no-cluster there); it is accepted by cluster-only/query/explain/path/"
                "affected/god-nodes/diagnose multigraph/tree/export/reflect instead."
            ),
        )


# --------------------------------------------------------------------------- #
# Pure argv construction (offline-testable: no process is ever spawned)
# --------------------------------------------------------------------------- #


def flags_argv(**kwargs: Any) -> list[str]:
    """``{"no_cluster": True}`` -> ``["--no-cluster"]``; other values pass through.

    ``None``/``False`` values are dropped, so a flag is only emitted when the
    caller actually asked for it.  Keys are normalised by :func:`_flag`, so
    ``global_``/``json_``/``type_`` become ``--global``/``--json``/``--type``.
    """
    out: list[str] = []
    for key, value in kwargs.items():
        if value is None or value is False:
            continue
        if value is True:
            out.append(_flag(key))
        else:
            out += [_flag(key), str(value)]
    return out


def bools_argv(**kwargs: Any) -> list[str]:
    """``{"no_cluster": True}`` -> ``["--no-cluster"]``; falsy values are dropped."""
    return [_flag(key) for key, value in kwargs.items() if value]


def build_argv(
    command: str | Sequence[str],
    *positional: Any,
    flags: Mapping[str, Any] | None = None,
    bools: Mapping[str, bool] | None = None,
    repeat: Mapping[str, Sequence[Any] | None] | None = None,
) -> list[str]:
    """Pure builder for one ``graphify`` argv (no binary, no ``stdbuf``, no I/O).

    ``command`` is one or more literal subcommand words (``("global", "add")``
    for the two-word forms).  ``positional`` are the subcommand's positional
    arguments.  ``flags`` emits ``--flag VALUE`` for non-``None`` values,
    ``bools`` emits bare ``--flag``, and ``repeat`` emits ``--flag VALUE`` once
    per item (for ``--context`` / ``--relation`` / ``--nodes``).

    Every wrapper method that emits flags funnels through this function, so a
    test can inspect a method's argv without running graphify.
    """
    words = [command] if isinstance(command, str) else [str(word) for word in command]
    parts: list[str] = [*words, *[str(item) for item in positional]]
    parts += flags_argv(**dict(flags or {}))
    parts += bools_argv(**dict(bools or {}))
    for key, values in (repeat or {}).items():
        for value in values or ():
            parts += [_flag(key), str(value)]
    return parts


# --------------------------------------------------------------------------- #
# Results
# --------------------------------------------------------------------------- #


@dataclass(frozen=True)
class CommandResult:
    """Outcome of one ``graphify`` subprocess."""

    ok: bool
    argv: list[str]
    exit_code: int
    stdout: str
    stderr_tail: str
    wall_s: float
    stderr_digest: str = ""
    stderr_bytes: int = 0
    stdout_bytes: int = 0
    #: The argv actually handed to the runner: ``argv`` prefixed with
    #: :data:`LINE_BUFFER_PREFIX` when line buffering is on.  ``argv`` stays the
    #: logical ``graphify`` command (a long-standing contract that callers index
    #: into), so the effective command gets its own field.
    spawn_argv: tuple[str, ...] = ()

    # -- convenience ------------------------------------------------------- #

    def lines(self) -> list[str]:
        return [line for line in self.stdout.splitlines() if line.strip()]

    def json(self, default: Any = None) -> Any:
        """Parse ``stdout`` as JSON, returning ``default`` when it is not JSON."""
        try:
            return json.loads(self.stdout)
        except (ValueError, TypeError):
            return default

    def to_record(self) -> dict[str, Any]:
        """Journal-ready record: argv, exit code and a stderr digest (no payload)."""
        return {
            "argv": list(self.argv),
            "spawn_argv": list(self.spawn_argv),
            "exit_code": self.exit_code,
            "ok": self.ok,
            "wall_s": round(self.wall_s, 4),
            "stdout_bytes": self.stdout_bytes,
            "stderr_bytes": self.stderr_bytes,
            "stderr_digest": self.stderr_digest,
        }

    def __str__(self) -> str:  # pragma: no cover - debugging aid
        return f"<{'ok' if self.ok else 'fail'} exit={self.exit_code} {self.wall_s:.2f}s>"


@dataclass(frozen=True)
class GraphNode:
    """A graph node, as emitted by graphify 0.9.80."""

    id: str
    label: str
    source_file: str = ""
    source_location: str = ""
    type: str | None = None
    file_type: str | None = None
    community: int | str | None = None
    confidence: float | None = None
    raw: Mapping[str, Any] = field(default_factory=dict, repr=False, compare=False)

    @property
    def kind(self) -> str | None:
        """``type`` when the extractor emits one, else 0.9.80's ``file_type``."""
        return self.type or self.file_type


@dataclass(frozen=True)
class GraphEdge:
    """A graph link, as emitted by graphify 0.9.80."""

    source: str
    target: str
    relation: str = ""
    confidence: str | float | None = None
    confidence_score: float | None = None
    context: str | None = None
    source_file: str = ""
    source_location: str = ""
    raw: Mapping[str, Any] = field(default_factory=dict, repr=False, compare=False)


@dataclass(frozen=True)
class GraphStats:
    """Cheap summary of a ``graph.json`` (streamed, no full materialisation)."""

    path: Path
    nodes: int
    edges: int
    communities: int
    directed: bool
    top_dirs: dict[str, int]
    node_kinds: dict[str, int]
    relations: dict[str, int] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        return {
            "path": str(self.path),
            "nodes": self.nodes,
            "edges": self.edges,
            "communities": self.communities,
            "directed": self.directed,
            "top_dirs": dict(self.top_dirs),
            "node_kinds": dict(self.node_kinds),
            "relations": dict(self.relations),
        }


@dataclass(frozen=True)
class Graph:
    """Lazy typed view of a ``graph.json`` document.

    ``nodes``/``links`` are only read when first accessed, then cached on the
    instance.
    """

    path: Path
    directed: bool = False
    _nodes: tuple[GraphNode, ...] | None = field(default=None, repr=False, compare=False)
    _links: tuple[GraphEdge, ...] | None = field(default=None, repr=False, compare=False)

    @property
    def nodes(self) -> tuple[GraphNode, ...]:
        if self._nodes is None:
            object.__setattr__(
                self, "_nodes", tuple(_node_from_raw(d) for d in _stream_array(self.path, "nodes"))
            )
        return self._nodes

    @property
    def links(self) -> tuple[GraphEdge, ...]:
        if self._links is None:
            object.__setattr__(
                self, "_links", tuple(_link_from_raw(d) for d in _stream_array(self.path, "links"))
            )
        return self._links

    # Alias used by some graphify outputs / callers.
    edges = links

    def by_id(self) -> dict[str, GraphNode]:
        return {n.id: n for n in self.nodes}

    def stats(self) -> GraphStats:
        return graph_stats(self.path)

    def links_from(self, node_id: str) -> list[GraphEdge]:
        return [link for link in self.links if link.source == node_id]

    def links_to(self, node_id: str) -> list[GraphEdge]:
        return [link for link in self.links if link.target == node_id]


@dataclass(frozen=True)
class QueryResult(CommandResult):
    """``graphify query`` plus the parsed node/edge lines it printed."""

    header: str = ""
    start: list[str] = field(default_factory=list)
    nodes: list[GraphNode] = field(default_factory=list)
    edges: list[GraphEdge] = field(default_factory=list)
    node_count: int = 0
    matched: bool = True

    def labels(self) -> list[str]:
        return [n.label for n in self.nodes]


@dataclass(frozen=True)
class GodNode:
    """One entry of ``god-nodes`` output."""

    id: str
    label: str
    degree: int


@dataclass(frozen=True)
class GodNodesResult(CommandResult):
    """``graphify god-nodes`` (text or ``--json``)."""

    nodes: list[GodNode] = field(default_factory=list)


@dataclass(frozen=True)
class NodeConnection:
    """One neighbour line from ``graphify explain``."""

    direction: str
    label: str
    relation: str
    confidence: str = ""
    location: str = ""
    incoming: bool = False


@dataclass(frozen=True)
class ExplainResult(CommandResult):
    """``graphify explain`` plus the node header and neighbour list."""

    node: str = ""
    node_id: str = ""
    source: str = ""
    node_type: str = ""
    community: str = ""
    degree: int = 0
    connections: list[NodeConnection] = field(default_factory=list)


@dataclass(frozen=True)
class PathResult(CommandResult):
    """``graphify path A B``."""

    found: bool = False
    steps: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class TraversalResult(CommandResult):
    """``graphify affected X`` (reverse traversal) and similar list outputs."""

    relations: list[str] = field(default_factory=list)
    depth: int | None = None
    nodes: list[dict[str, str]] = field(default_factory=list)


# --------------------------------------------------------------------------- #
# JSON reading (streaming)
# --------------------------------------------------------------------------- #

_TOP_LEVEL_SCALARS = ("directed", "multigraph")


def resolve_graph_path(path: str | Path) -> Path:
    """Return the ``graph.json`` for ``path``.

    Accepts a graph file, an ``out`` directory, or the target directory itself
    (``extract --out DIR`` writes ``DIR/graphify-out/graph.json``).
    """
    p = Path(path).expanduser()
    if p.is_file():
        return p
    candidate = p / GRAPH_DIR_NAME / GRAPH_FILE_NAME
    if candidate.is_file():
        return candidate
    direct = p / GRAPH_FILE_NAME
    if direct.is_file():
        return direct
    return candidate  # non-existent; callers get a clear error


def _stream_array(path: Path, key: str, chunk_size: int = 1 << 20) -> Iterator[Any]:
    """Yield each element of the top-level JSON array ``key`` in ``path``.

    Streams so a 30 MB graph never needs two full in-memory copies; only one
    element is decoded at a time.
    """
    decoder = json.JSONDecoder()
    needle = f'"{key}"'
    with open(path, "r", encoding="utf-8") as fh:
        buf = ""
        # Phase 1: find the start of the array.
        while True:
            piece = fh.read(chunk_size)
            if not piece:
                return
            buf += piece
            at = buf.find(needle)
            if at >= 0:
                bracket = buf.find("[", at + len(needle))
                if bracket >= 0:
                    buf = buf[bracket + 1 :]
                    break
            if len(buf) > len(needle) + 8:
                buf = buf[-(len(needle) + 8) :]
        # Phase 2: decode elements one at a time.
        while True:
            buf = buf.lstrip()
            if buf.startswith(","):
                buf = buf[1:].lstrip()
            if not buf:
                piece = fh.read(chunk_size)
                if not piece:
                    return
                buf += piece
                continue
            if buf.startswith("]"):
                return
            try:
                value, end = decoder.raw_decode(buf)
            except ValueError:
                piece = fh.read(chunk_size)
                if not piece:
                    return
                buf += piece
                continue
            yield value
            buf = buf[end:]


def _read_scalar(path: Path, key: str, default: Any = None) -> Any:
    """Read a small top-level scalar without parsing the whole document."""
    pattern = re.compile(r'"%s"\s*:\s*(true|false|null|-?\d+(?:\.\d+)?)' % re.escape(key))
    with open(path, "r", encoding="utf-8") as fh:
        head = fh.read(8192)
    match = pattern.search(head)
    if not match:
        return default
    token = match.group(1)
    if token in ("true", "false"):
        return token == "true"
    if token == "null":
        return None
    return float(token) if "." in token else int(token)


def _first_component(source_file: str) -> str:
    text = (source_file or "").strip().lstrip("./")
    if not text:
        return "<unknown>"
    return text.split("/", 1)[0]


def _node_from_raw(raw: Mapping[str, Any]) -> GraphNode:
    community = raw.get("community")
    return GraphNode(
        id=str(raw.get("id", "")),
        label=str(raw.get("label") or raw.get("id") or ""),
        source_file=str(raw.get("source_file") or ""),
        source_location=str(raw.get("source_location") or ""),
        type=raw.get("type"),
        file_type=raw.get("file_type"),
        community=community,
        confidence=raw.get("confidence"),
        raw=raw,
    )


def _link_from_raw(raw: Mapping[str, Any]) -> GraphEdge:
    return GraphEdge(
        source=str(raw.get("source", "")),
        target=str(raw.get("target", "")),
        relation=str(raw.get("relation") or ""),
        confidence=raw.get("confidence"),
        confidence_score=raw.get("confidence_score"),
        context=raw.get("context"),
        source_file=str(raw.get("source_file") or ""),
        source_location=str(raw.get("source_location") or ""),
        raw=raw,
    )


def graph_stats(graph_path: str | Path, top_dirs_limit: int = 20) -> GraphStats:
    """Summarise ``graph.json`` by streaming it (no whole-document load).

    ``top_dirs`` counts nodes by the first path component of ``source_file``;
    ``node_kinds`` counts the node ``type`` field when the extractor emits one
    and otherwise falls back to 0.9.80's ``file_type``.
    """
    path = resolve_graph_path(graph_path)
    if not path.is_file():
        raise GraphifyError(["graph_stats", str(path)], None, f"graph.json not found: {path}")

    nodes = 0
    communities: set[Any] = set()
    dir_counts: dict[str, int] = {}
    kind_counts: dict[str, int] = {}
    typed = False
    for raw in _stream_array(path, "nodes"):
        if not isinstance(raw, Mapping):
            continue
        nodes += 1
        community = raw.get("community")
        if community is not None:
            communities.add(community)
        bucket = _first_component(str(raw.get("source_file") or ""))
        dir_counts[bucket] = dir_counts.get(bucket, 0) + 1
        if raw.get("type") is not None:
            typed = True
            kind = str(raw.get("type"))
        elif raw.get("file_type") is not None:
            kind = str(raw.get("file_type"))
        else:
            kind = "<none>"
        kind_counts[kind] = kind_counts.get(kind, 0) + 1

    edges = 0
    relations: dict[str, int] = {}
    for raw in _stream_array(path, "links"):
        if not isinstance(raw, Mapping):
            continue
        edges += 1
        relation = str(raw.get("relation") or "")
        relations[relation] = relations.get(relation, 0) + 1

    top_dirs = dict(sorted(dir_counts.items(), key=lambda kv: (-kv[1], kv[0]))[:top_dirs_limit])
    return GraphStats(
        path=path,
        nodes=nodes,
        edges=edges,
        communities=len(communities),
        directed=bool(_read_scalar(path, "directed", False)),
        top_dirs=top_dirs,
        node_kinds=dict(sorted(kind_counts.items(), key=lambda kv: (-kv[1], kv[0]))),
        relations=dict(sorted(relations.items(), key=lambda kv: (-kv[1], kv[0]))),
    )


def read_graph(graph_path: str | Path) -> Graph:
    """Return a lazy typed view of ``graph.json``.

    Nothing is read until ``.nodes`` / ``.links`` is first touched, so
    :meth:`Graph.stats` on a 30 MB graph stays cheap.
    """
    path = resolve_graph_path(graph_path)
    if not path.is_file():
        raise GraphifyError(["read_graph", str(path)], None, f"graph.json not found: {path}")
    return Graph(path=path, directed=bool(_read_scalar(path, "directed", False)))


# --------------------------------------------------------------------------- #
# Output parsers
# --------------------------------------------------------------------------- #

_NODE_LINE = re.compile(
    r"^NODE\s+(?P<label>.+?)\s+\[src=(?P<src>[^\s\]]*)\s+loc=(?P<loc>[^\s\]]*)"
    r"\s+community=(?P<community>[^\]]*)\]$"
)
_EDGE_LINE = re.compile(
    r"^EDGE\s+(?P<src>.+?)\s+--(?P<relation>\S+)\s+\[(?P<conf_inner>[^\]]*)\]"
    r"\s*-->\s*(?P<dst>.+?)(?:\s+at=(?P<at>\S+))?$"
)
_START_LINE = re.compile(r"Start:\s*\[(?P<items>[^\]]*)\]")
_COUNT_LINE = re.compile(r"(?P<count>\d+)\s+nodes?\s+found")
_GOD_JSON_KEYS = ("id", "label", "degree")
_GOD_TEXT = re.compile(r"^\s*\d+\.\s+(?P<label>.+?)\s+-\s+(?P<degree>\d+)\s+edges?$")
_CONN_LINE = re.compile(
    r"^\s*(?P<arrow><--|-->)\s+(?P<label>.+?)\s+\[(?P<relation>[^\]]+)\]"
    r"(?:\s+\[(?P<confidence>[^\]]+)\])?(?:\s+(?P<at>\S+))?$"
)
_AFFECTED_LINE = re.compile(
    r"^-\s+(?P<label>.+?)\s+\[(?P<relation>[^\]]+)\](?:\s+(?P<at>\S+))?$"
)


def _parse_query(result: CommandResult) -> QueryResult:
    nodes: list[GraphNode] = []
    edges: list[GraphEdge] = []
    start: list[str] = []
    header = ""
    node_count = 0
    for line in result.stdout.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.startswith("Graph:"):
            header = stripped
            match = _START_LINE.search(stripped)
            if match:
                try:
                    parsed = ast.literal_eval("[" + match.group("items") + "]")
                    start = [str(x) for x in parsed]
                except (ValueError, SyntaxError):
                    start = []
            count = _COUNT_LINE.search(stripped)
            if count:
                node_count = int(count.group("count"))
            continue
        node_match = _NODE_LINE.match(stripped)
        if node_match:
            community: Any = node_match.group("community")
            try:
                community = int(community)
            except ValueError:
                pass
            nodes.append(
                GraphNode(
                    id=node_match.group("label"),
                    label=node_match.group("label"),
                    source_file=node_match.group("src"),
                    source_location=node_match.group("loc"),
                    community=community,
                )
            )
            continue
        edge_match = _EDGE_LINE.match(stripped)
        if edge_match:
            conf_inner = edge_match.group("conf_inner").strip()
            confidence = conf_inner.split(" ", 1)[0] if conf_inner else ""
            context = None
            ctx = re.search(r"context=(\S+)", conf_inner)
            if ctx:
                context = ctx.group(1)
            edges.append(
                GraphEdge(
                    source=edge_match.group("src"),
                    target=edge_match.group("dst"),
                    relation=edge_match.group("relation"),
                    confidence=confidence,
                    context=context,
                    source_location=edge_match.group("at") or "",
                )
            )
    if not node_count:
        node_count = len(nodes)
    return QueryResult(
        ok=result.ok,
        argv=result.argv,
        exit_code=result.exit_code,
        stdout=result.stdout,
        stderr_tail=result.stderr_tail,
        wall_s=result.wall_s,
        stderr_digest=result.stderr_digest,
        stderr_bytes=result.stderr_bytes,
        stdout_bytes=result.stdout_bytes,
        spawn_argv=result.spawn_argv,
        header=header,
        start=start,
        nodes=nodes,
        edges=edges,
        node_count=node_count,
        matched=node_count > 0,
    )


def _parse_god_nodes(result: CommandResult, as_json: bool) -> GodNodesResult:
    nodes: list[GodNode] = []
    if as_json:
        payload = result.json(default=[])
        if isinstance(payload, list):
            for entry in payload:
                if isinstance(entry, Mapping):
                    nodes.append(
                        GodNode(
                            id=str(entry.get("id", "")),
                            label=str(entry.get("label") or entry.get("id") or ""),
                            degree=int(entry.get("degree") or 0),
                        )
                    )
    else:
        for line in result.stdout.splitlines():
            match = _GOD_TEXT.match(line)
            if match:
                nodes.append(
                    GodNode(
                        id=match.group("label"),
                        label=match.group("label"),
                        degree=int(match.group("degree")),
                    )
                )
    return GodNodesResult(
        ok=result.ok,
        argv=result.argv,
        exit_code=result.exit_code,
        stdout=result.stdout,
        stderr_tail=result.stderr_tail,
        wall_s=result.wall_s,
        stderr_digest=result.stderr_digest,
        stderr_bytes=result.stderr_bytes,
        stdout_bytes=result.stdout_bytes,
        spawn_argv=result.spawn_argv,
        nodes=nodes,
    )


def _parse_explain(result: CommandResult) -> ExplainResult:
    node = node_id = source = node_type = community = ""
    degree = 0
    connections: list[NodeConnection] = []
    in_connections = False
    for line in result.stdout.splitlines():
        stripped = line.strip()
        if stripped.startswith("Node:"):
            node = stripped.split(":", 1)[1].strip()
        elif stripped.startswith("ID:"):
            node_id = stripped.split(":", 1)[1].strip()
        elif stripped.startswith("Source:"):
            source = stripped.split(":", 1)[1].strip()
        elif stripped.startswith("Type:"):
            node_type = stripped.split(":", 1)[1].strip()
        elif stripped.startswith("Community:"):
            community = stripped.split(":", 1)[1].strip()
        elif stripped.startswith("Degree:"):
            try:
                degree = int(stripped.split(":", 1)[1].strip())
            except ValueError:
                degree = 0
        elif stripped.startswith("Connections"):
            in_connections = True
        elif in_connections:
            match = _CONN_LINE.match(line)
            if match:
                connections.append(
                    NodeConnection(
                        direction=match.group("arrow"),
                        label=match.group("label"),
                        relation=match.group("relation"),
                        confidence=match.group("confidence") or "",
                        location=match.group("at") or "",
                        incoming=match.group("arrow") == "<--",
                    )
                )
    return ExplainResult(
        ok=result.ok,
        argv=result.argv,
        exit_code=result.exit_code,
        stdout=result.stdout,
        stderr_tail=result.stderr_tail,
        wall_s=result.wall_s,
        stderr_digest=result.stderr_digest,
        stderr_bytes=result.stderr_bytes,
        stdout_bytes=result.stdout_bytes,
        spawn_argv=result.spawn_argv,
        node=node,
        node_id=node_id,
        source=source,
        node_type=node_type,
        community=community,
        degree=degree,
        connections=connections,
    )


def _parse_path(result: CommandResult) -> PathResult:
    stdout = result.stdout
    found = bool(result.ok) and "no path" not in stdout.lower() and bool(stdout.strip())
    steps: list[str] = []
    for line in stdout.splitlines():
        stripped = line.strip()
        if "-->" in stripped or "->" in stripped:
            steps.append(stripped)
    return PathResult(
        ok=result.ok,
        argv=result.argv,
        exit_code=result.exit_code,
        stdout=stdout,
        stderr_tail=result.stderr_tail,
        wall_s=result.wall_s,
        stderr_digest=result.stderr_digest,
        stderr_bytes=result.stderr_bytes,
        stdout_bytes=result.stdout_bytes,
        spawn_argv=result.spawn_argv,
        found=found,
        steps=steps,
    )


def _parse_affected(result: CommandResult) -> TraversalResult:
    relations: list[str] = []
    depth: int | None = None
    nodes: list[dict[str, str]] = []
    for line in result.stdout.splitlines():
        stripped = line.strip()
        if stripped.startswith("Relations:"):
            relations = [part.strip() for part in stripped.split(":", 1)[1].split(",") if part.strip()]
        elif stripped.startswith("Depth:"):
            try:
                depth = int(stripped.split(":", 1)[1].strip())
            except ValueError:
                depth = None
        else:
            match = _AFFECTED_LINE.match(stripped)
            if match:
                nodes.append(
                    {
                        "label": match.group("label"),
                        "relation": match.group("relation"),
                        "location": match.group("at") or "",
                    }
                )
    return TraversalResult(
        ok=result.ok,
        argv=result.argv,
        exit_code=result.exit_code,
        stdout=result.stdout,
        stderr_tail=result.stderr_tail,
        wall_s=result.wall_s,
        stderr_digest=result.stderr_digest,
        stderr_bytes=result.stderr_bytes,
        stdout_bytes=result.stdout_bytes,
        spawn_argv=result.spawn_argv,
        relations=relations,
        depth=depth,
        nodes=nodes,
    )


# --------------------------------------------------------------------------- #
# The wrapper
# --------------------------------------------------------------------------- #

_EXPORT_KINDS = (
    "html",
    "callflow-html",
    "obsidian",
    "wiki",
    "svg",
    "graphml",
    "neo4j",
    "falkordb",
)


def _flag(name: str) -> str:
    return "--" + name.rstrip("_").replace("_", "-")


class Graphify:
    """Typed, timeout-bounded wrapper around the ``graphify`` binary.

    ``cwd`` is the working directory for every invocation (relative ``--out``
    paths resolve against it).  ``history`` records one
    :class:`CommandResult` per :meth:`run`, including failed and timed-out runs.
    """

    def __init__(
        self,
        binary: str | Path | None = None,
        cwd: str | Path | None = None,
        timeout: float = DEFAULT_TIMEOUT_S,
        *,
        line_buffer: bool = True,
        dry_run: bool = False,
    ) -> None:
        self.binary: Path = Path(binary).expanduser().resolve() if binary else _default_binary().resolve()
        self.cwd: Path = Path(cwd).expanduser().resolve() if cwd else _PROJECT_ROOT
        self.timeout: float = float(timeout)
        self.history: list[CommandResult] = []
        #: Prefix every child with :data:`LINE_BUFFER_PREFIX` (line-buffered stdio).
        self.line_buffer: bool = bool(line_buffer)
        #: Build argv without spawning anything (offline flag auditing).
        self.dry_run: bool = bool(dry_run)
        #: ``stdbuf`` on ``PATH``, or ``None`` when unavailable (fail soft).
        self.stdbuf: str | None = shutil.which("stdbuf")
        #: Non-fatal degradations (e.g. a missing ``stdbuf``) for the journal.
        self.notes: list[str] = []
        if self.line_buffer and not self.stdbuf:
            self.notes.append(
                "stdbuf is not on PATH: child output will stay block-buffered off-TTY, "
                "so a timeout may discard progress (PYTHONUNBUFFERED=1 is still set)"
            )

    # -- low level --------------------------------------------------------- #

    def logical_argv(self, *args: str | Path) -> list[str]:
        """The ``graphify`` command as the caller means it (no ``stdbuf``)."""
        return [str(self.binary), *[str(a) for a in args]]

    def spawn_argv_for(
        self, argv: Sequence[str], *, line_buffer: bool | None = None
    ) -> list[str]:
        """The argv the runner actually receives: ``argv`` under ``stdbuf``.

        Line buffering is applied **once, here**, for every method.  Pass
        ``line_buffer=False`` (per call) or ``Graphify(line_buffer=False)``
        (per instance) to opt out; when ``stdbuf`` is missing the child is
        spawned unprefixed and :attr:`notes` records why.
        """
        buffered = self.line_buffer if line_buffer is None else bool(line_buffer)
        if not buffered or not self.stdbuf:
            return list(argv)
        return [*LINE_BUFFER_PREFIX, *argv]

    def run(
        self,
        *args: str | Path,
        timeout: float | None = None,
        check: bool = True,
        line_buffer: bool | None = None,
    ) -> CommandResult:
        """Execute ``graphify <args>``, never raising anything but a typed error.

        Records the run in :attr:`history` before raising, so the journal sees
        failed runs too.  ``check=False`` returns the failing result instead of
        raising.

        The child is wrapped in ``stdbuf -oL -eL`` (see :meth:`spawn_argv_for`)
        so its progress streams instead of being block-buffered off-TTY.
        ``dry_run=True`` on the instance builds the argv without spawning.
        """
        argv = self.logical_argv(*args)
        spawn = self.spawn_argv_for(argv, line_buffer=line_buffer)
        limit = float(self.timeout if timeout is None else timeout)
        started = time.monotonic()

        if self.dry_run:
            return self._record(
                CommandResult(
                    ok=True,
                    argv=argv,
                    exit_code=0,
                    stdout="",
                    stderr_tail="",
                    wall_s=0.0,
                    spawn_argv=tuple(spawn),
                )
            )
        if not self.binary.exists():
            result = self._record(
                self._failure(argv, None, f"graphify binary not found: {self.binary}", started, spawn)
            )
            if check:
                raise GraphifyError(argv, None, result.stderr_tail)
            return result
        if not self.cwd.is_dir():
            result = self._record(
                self._failure(argv, None, f"working directory not found: {self.cwd}", started, spawn)
            )
            if check:
                raise GraphifyError(argv, None, result.stderr_tail)
            return result

        # PYTHONUNBUFFERED is the second half of the buffering fix: ``stdbuf``
        # only reaches C stdio, while graphify's own stdout is a Python
        # TextIOWrapper that block-buffers off-TTY.
        env = {**os.environ, "PYTHONUNBUFFERED": "1"}
        try:
            proc = subprocess.run(
                spawn,
                cwd=str(self.cwd),
                capture_output=True,
                text=True,
                timeout=limit,
                env=env,
            )
        except subprocess.TimeoutExpired as exc:
            tail = _tail(exc.stderr)
            partial_stdout = _tail(exc.stdout, limit=10**9)
            result = self._record(
                CommandResult(
                    ok=False,
                    argv=argv,
                    exit_code=-1,
                    stdout=partial_stdout,
                    stderr_tail=tail,
                    wall_s=time.monotonic() - started,
                    stderr_digest=_digest(exc.stderr),
                    stderr_bytes=_nbytes(exc.stderr),
                    spawn_argv=tuple(spawn),
                )
            )
            if check:
                raise GraphifyTimeout(argv, limit, exit_code=-1, stderr_tail=tail) from exc
            return result
        except OSError as exc:  # untyped OS failure -> typed GraphifyError
            result = self._record(
                self._failure(argv, None, f"{type(exc).__name__}: {exc}", started, spawn)
            )
            if check:
                raise GraphifyError(argv, None, result.stderr_tail) from exc
            return result

        result = self._record(
            CommandResult(
                ok=proc.returncode == 0,
                argv=argv,
                exit_code=proc.returncode,
                stdout=proc.stdout or "",
                stderr_tail=_tail(proc.stderr),
                wall_s=time.monotonic() - started,
                stderr_digest=_digest(proc.stderr),
                stderr_bytes=_nbytes(proc.stderr),
                stdout_bytes=_nbytes(proc.stdout),
                spawn_argv=tuple(spawn),
            )
        )
        if proc.returncode != 0 and check:
            raise GraphifyError(argv, proc.returncode, result.stderr_tail)
        return result

    def _record(self, result: CommandResult) -> CommandResult:
        self.history.append(result)
        return result

    @staticmethod
    def _failure(
        argv: list[str],
        exit_code: int | None,
        message: str,
        started: float,
        spawn: Sequence[str] = (),
    ) -> CommandResult:
        return CommandResult(
            ok=False,
            argv=argv,
            exit_code=exit_code if exit_code is not None else -1,
            stdout="",
            stderr_tail=message,
            wall_s=time.monotonic() - started,
            stderr_digest=_digest(message),
            stderr_bytes=_nbytes(message),
            spawn_argv=tuple(spawn),
        )

    # -- graph readers ----------------------------------------------------- #

    @staticmethod
    def graph_json(out_dir: str | Path) -> Path:
        """``<out_dir>/graphify-out/graph.json`` — the path ``extract --out`` uses."""
        return Path(out_dir) / GRAPH_DIR_NAME / GRAPH_FILE_NAME

    def graph_stats(self, graph_path: str | Path, **kwargs: Any) -> GraphStats:
        return graph_stats(graph_path, **kwargs)

    def read_graph(self, graph_path: str | Path) -> Graph:
        return read_graph(graph_path)

    # -- extraction -------------------------------------------------------- #

    def extract(
        self,
        target: str | Path,
        *,
        backend: str | None = None,
        model: str | None = None,
        max_concurrency: int | None = None,
        token_budget: int | None = None,
        code_only: bool = False,
        out: str | Path | None = None,
        global_: bool = False,
        as_: str | None = None,
        no_viz: bool = False,
        no_cluster: bool = False,
        mode: str | None = None,
        api_timeout: float | None = None,
        max_workers: int | None = None,
        force: bool = False,
        google_workspace: bool = False,
        postgres: str | None = None,
        cargo: bool = False,
        no_gitignore: bool = False,
        timeout: float | None = None,
    ) -> CommandResult:
        """``extract <target>`` — headless extraction (AST with ``code_only``).

        ``out`` defaults to graphify's own default (``<target>``); the graph
        always lands in ``<out>/graphify-out/graph.json``.

        Note: 0.9.80's ``extract`` help does **not** list ``--no-viz`` (it is
        documented for ``cluster-only``), so ``no_viz`` is only passed when
        explicitly requested.  That deliberate opt-in deviation is pinned by
        ``tests/test_kg_graphify_flags.py``.
        """
        args = build_argv(
            "extract",
            target,
            flags={
                "backend": backend,
                "model": model,
                "max_concurrency": max_concurrency,
                "token_budget": token_budget,
                "out": out,
                "mode": mode,
                "api_timeout": api_timeout,
                "max_workers": max_workers,
                "postgres": postgres,
                "as": as_ if as_ else None,
            },
            bools={
                "code_only": code_only,
                "global": global_,
                "no_cluster": no_cluster,
                "no_gitignore": no_gitignore,
                "force": force,
                "google_workspace": google_workspace,
                "cargo": cargo,
                "no_viz": no_viz,
            },
        )
        return self.run(*args, timeout=timeout)

    def cluster_only(
        self,
        target: str | Path,
        *,
        no_viz: bool = False,
        graph: str | Path | None = None,
        no_label: bool = False,
        backend: str | None = None,
        model: str | None = None,
        max_concurrency: int | None = None,
        batch_size: int | None = None,
        timeout: float | None = None,
    ) -> CommandResult:
        """``cluster-only <path>`` — re-cluster an existing graph (``no_label`` = local)."""
        args = build_argv(
            "cluster-only",
            target,
            flags={
                "graph": graph,
                "backend": backend,
                "model": model,
                "max_concurrency": max_concurrency,
                "batch_size": batch_size,
            },
            bools={"no_viz": no_viz, "no_label": no_label},
        )
        return self.run(*args, timeout=timeout)

    def update(
        self,
        target: str | Path,
        *,
        force: bool = False,
        no_cluster: bool = False,
        graph: str | Path | None = None,
        timeout: float | None = None,
    ) -> CommandResult:
        """``update <path>`` — re-extract code files into an existing graph.

        ``graphify update`` accepts **only** ``--force`` and ``--no-cluster``
        (0.9.80, verified): it always rewrites ``<path>/graphify-out/graph.json``
        and has no ``--graph`` flag.  Emitting one makes the real CLI exit 2 with
        ``error: unknown update option: --graph``, so ``--graph`` is never built.

        ``graph`` is kept for backward compatibility only: passing the implied
        default (``<target>/graphify-out/graph.json``) is a no-op, and passing
        any other location raises :class:`UnsupportedGraphTarget` rather than
        silently shipping a flag the CLI rejects.
        """
        implied = Path(str(target)) / GRAPH_DIR_NAME / GRAPH_FILE_NAME
        if graph is not None:
            given = Path(str(graph))
            same = given == implied
            if not same:
                try:
                    same = given.resolve() == implied.resolve()
                except OSError:  # pragma: no cover - unresolvable path
                    same = False
            if not same:
                raise UnsupportedGraphTarget(target, graph, implied)
        args = build_argv("update", target, bools={"force": force, "no_cluster": no_cluster})
        return self.run(*args, timeout=timeout)

    def label(
        self,
        target: str | Path,
        *,
        backend: str | None = None,
        model: str | None = None,
        batch_size: int | None = None,
        max_concurrency: int | None = None,
        missing_only: bool = False,
        timeout: float | None = None,
    ) -> CommandResult:
        """``label <path>`` — LLM community naming (not used by offline units)."""
        args = build_argv(
            "label",
            target,
            flags={
                "backend": backend,
                "model": model,
                "batch_size": batch_size,
                "max_concurrency": max_concurrency,
            },
            bools={"missing_only": missing_only},
        )
        return self.run(*args, timeout=timeout)

    # -- traversal --------------------------------------------------------- #

    def query(
        self,
        question: str,
        *,
        graph: str | Path | None = None,
        budget: int | None = None,
        dfs: bool = False,
        context: Sequence[str] | None = None,
        timeout: float | None = None,
    ) -> QueryResult:
        """``query "<question>"`` — BFS/DFS traversal, parsed into nodes and edges."""
        args = build_argv(
            "query",
            question,
            flags={"graph": graph, "budget": budget},
            bools={"dfs": dfs},
            repeat={"context": context},
        )
        return _parse_query(self.run(*args, timeout=timeout))

    def explain(
        self,
        node: str,
        *,
        graph: str | Path | None = None,
        timeout: float | None = None,
    ) -> ExplainResult:
        """``explain "X"`` — a node plus its neighbours, parsed."""
        args = build_argv("explain", node, flags={"graph": graph})
        return _parse_explain(self.run(*args, timeout=timeout))

    def path(
        self,
        source: str,
        target: str,
        *,
        graph: str | Path | None = None,
        timeout: float | None = None,
    ) -> PathResult:
        """``path "A" "B"`` — shortest path (**node ids** are unambiguous)."""
        args = build_argv("path", source, target, flags={"graph": graph})
        return _parse_path(self.run(*args, timeout=timeout))

    def affected(
        self,
        node: str,
        *,
        depth: int | None = None,
        relation: Sequence[str] | None = None,
        graph: str | Path | None = None,
        timeout: float | None = None,
    ) -> TraversalResult:
        """``affected "X"`` — reverse traversal of things impacted by ``X``."""
        args = build_argv(
            "affected",
            node,
            flags={"depth": depth, "graph": graph},
            repeat={"relation": relation},
        )
        return _parse_affected(self.run(*args, timeout=timeout))

    def god_nodes(
        self,
        *,
        top: int | None = None,
        json_: bool = False,
        graph: str | Path | None = None,
        timeout: float | None = None,
    ) -> GodNodesResult:
        """``god-nodes`` — most-connected nodes (``--json`` parses cleanly)."""
        args = build_argv(
            "god-nodes",
            flags={"top": top, "graph": graph},
            bools={"json": json_},
        )
        return _parse_god_nodes(self.run(*args, timeout=timeout), as_json=json_)

    def diagnose_multigraph(
        self,
        graph: str | Path | None = None,
        *,
        json_: bool = False,
        max_examples: int | None = None,
        directed: bool = False,
        undirected: bool = False,
        extract_path: str | Path | None = None,
        timeout: float | None = None,
    ) -> CommandResult:
        """``diagnose multigraph`` — same-endpoint edge collapse risk."""
        args = build_argv(
            ("diagnose", "multigraph"),
            flags={"graph": graph, "max_examples": max_examples, "extract_path": extract_path},
            bools={"json": json_, "directed": directed, "undirected": undirected},
        )
        return self.run(*args, timeout=timeout)

    # -- corpus ------------------------------------------------------------ #

    def add_url(
        self,
        url: str,
        *,
        dir: str | Path | None = None,
        author: str | None = None,
        contributor: str | None = None,
        timeout: float | None = None,
    ) -> CommandResult:
        """``add <url>`` — fetch a URL into the corpus and update the graph."""
        args = build_argv(
            "add", url, flags={"dir": dir, "author": author, "contributor": contributor}
        )
        return self.run(*args, timeout=timeout)

    def global_add(
        self,
        graph_json: str | Path,
        *,
        as_: str | None = None,
        timeout: float | None = None,
    ) -> CommandResult:
        args = build_argv(
            ("global", "add"), graph_json, flags={"as": as_ if as_ else None}
        )
        return self.run(*args, timeout=timeout)

    def global_list(self, *, timeout: float | None = None) -> CommandResult:
        return self.run("global", "list", timeout=timeout)

    def global_path(self, *, timeout: float | None = None) -> CommandResult:
        return self.run("global", "path", timeout=timeout)

    def global_remove(self, tag: str, *, timeout: float | None = None) -> CommandResult:
        return self.run("global", "remove", tag, timeout=timeout)

    # -- git hooks --------------------------------------------------------- #

    def hook_install(self, *, timeout: float | None = None) -> CommandResult:
        return self.run("hook", "install", timeout=timeout)

    def hook_uninstall(self, *, timeout: float | None = None) -> CommandResult:
        return self.run("hook", "uninstall", timeout=timeout)

    def hook_status(self, *, timeout: float | None = None) -> CommandResult:
        return self.run("hook", "status", timeout=timeout)

    # -- memory feedback loop ---------------------------------------------- #

    def save_result(
        self,
        question: str,
        answer: str,
        *,
        type_: str = "query",
        nodes: Sequence[str] | None = None,
        outcome: str | None = None,
        correction: str | None = None,
        memory_dir: str | Path | None = None,
        timeout: float | None = None,
    ) -> CommandResult:
        """``save-result`` — park a Q&A outcome in the graph memory dir."""
        args = build_argv(
            "save-result",
            flags={
                "question": question,
                "answer": answer,
                "type": type_,
                "outcome": outcome,
                "correction": correction,
                "memory_dir": memory_dir,
            },
            repeat={"nodes": nodes},
        )
        return self.run(*args, timeout=timeout)

    def reflect(
        self,
        *,
        memory_dir: str | Path | None = None,
        out: str | Path | None = None,
        graph: str | Path | None = None,
        analysis: str | Path | None = None,
        labels: str | Path | None = None,
        half_life_days: int | None = None,
        min_corroboration: int | None = None,
        timeout: float | None = None,
    ) -> CommandResult:
        """``reflect`` — aggregate saved outcomes into ``LESSONS.md``."""
        args = build_argv(
            "reflect",
            flags={
                "memory_dir": memory_dir,
                "out": out,
                "graph": graph,
                "analysis": analysis,
                "labels": labels,
                "half_life_days": half_life_days,
                "min_corroboration": min_corroboration,
            },
        )
        return self.run(*args, timeout=timeout)

    # -- export ------------------------------------------------------------ #

    def export(
        self,
        kind: str,
        *,
        graph: str | Path | None = None,
        labels: str | Path | None = None,
        output: str | Path | None = None,
        dir: str | Path | None = None,
        node_limit: int | None = None,
        no_viz: bool = False,
        push: str | None = None,
        user: str | None = None,
        password: str | None = None,
        timeout: float | None = None,
        **extra: Any,
    ) -> CommandResult:
        """``export <kind>`` for one of :data:`_EXPORT_KINDS`; ``extra`` adds flags."""
        if kind not in _EXPORT_KINDS:
            raise ValueError(f"unknown export kind {kind!r}; expected one of {', '.join(_EXPORT_KINDS)}")
        extra_flags: dict[str, Any] = {
            "graph": graph,
            "labels": labels,
            "output": output,
            "dir": dir,
            "node_limit": node_limit,
            "push": push,
            "user": user,
            "password": password,
        }
        extra_flags.update(extra)
        args = build_argv(("export", kind), flags=extra_flags, bools={"no_viz": no_viz})
        return self.run(*args, timeout=timeout)

    # -- repo plumbing ----------------------------------------------------- #

    def clone(
        self,
        url: str,
        *,
        branch: str | None = None,
        out: str | Path | None = None,
        timeout: float | None = None,
    ) -> CommandResult:
        args = build_argv("clone", url, flags={"branch": branch, "out": out})
        return self.run(*args, timeout=timeout)

    def merge_graphs(
        self,
        graphs: Sequence[str | Path],
        *,
        out: str | Path | None = None,
        previous: str | Path | None = None,
        timeout: float | None = None,
    ) -> CommandResult:
        """``merge-graphs <g1> <g2> ...`` — cross-repo graph union."""
        args = build_argv("merge-graphs", *graphs, flags={"out": out, "previous": previous})
        return self.run(*args, timeout=timeout)

    def benchmark(
        self,
        graph_json: str | Path | None = None,
        *,
        timeout: float | None = None,
    ) -> CommandResult:
        """``benchmark [graph.json]`` — token reduction vs the naive corpus."""
        args: list[str | Path] = ["benchmark"]
        if graph_json is not None:
            args.append(graph_json)
        return self.run(*args, timeout=timeout)

    def tree(
        self,
        *,
        graph: str | Path | None = None,
        output: str | Path | None = None,
        root: str | Path | None = None,
        max_children: int | None = None,
        top_k_edges: int | None = None,
        label: str | None = None,
        timeout: float | None = None,
    ) -> CommandResult:
        args = build_argv(
            "tree",
            flags={
                "graph": graph,
                "output": output,
                "root": root,
                "max_children": max_children,
                "top_k_edges": top_k_edges,
                "label": label,
            },
        )
        return self.run(*args, timeout=timeout)

    def check_update(self, target: str | Path, *, timeout: float | None = None) -> CommandResult:
        return self.run("check-update", target, timeout=timeout)

    def watch(self, target: str | Path, *, timeout: float | None = None) -> CommandResult:
        """``watch <path>`` — long-running; always pass an explicit timeout."""
        return self.run("watch", target, timeout=timeout)

    def provider(self, action: str = "list", *args: str, timeout: float | None = None) -> CommandResult:
        """``provider list|show|add|remove`` — passthrough for the remaining argv."""
        return self.run("provider", action, *args, timeout=timeout)

    # -- flag plumbing ----------------------------------------------------- #

    @staticmethod
    def _flags(**kwargs: Any) -> list[str]:
        """``{"no_cluster": True}`` -> ``["--no-cluster"]`` (see :func:`flags_argv`)."""
        return flags_argv(**kwargs)

    @staticmethod
    def _bools(**kwargs: bool) -> list[str]:
        return bools_argv(**kwargs)


def _tail(text: str | bytes | None, limit: int = STDERR_TAIL_CHARS) -> str:
    if text is None:
        return ""
    if isinstance(text, bytes):
        text = text.decode("utf-8", "replace")
    return text[-limit:]


def _digest(text: str | bytes | None) -> str:
    if text is None:
        return hashlib.sha256(b"").hexdigest()[:16]
    data = text if isinstance(text, bytes) else text.encode("utf-8", "replace")
    return hashlib.sha256(data).hexdigest()[:16]


def _nbytes(text: str | bytes | None) -> int:
    if text is None:
        return 0
    return len(text if isinstance(text, bytes) else text.encode("utf-8", "replace"))

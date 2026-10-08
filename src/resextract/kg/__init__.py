"""Knowledge-graph access for ``resextract``.

Two pieces, both offline:

* :mod:`resextract.kg.graphify` — a typed, timeout-bounded wrapper around the
  local ``graphify`` CLI plus streaming readers for ``graph.json``.
* :mod:`resextract.kg.queries` — the canned, data-driven research query battery.

Import either module directly (``from resextract.kg import graphify``) or the
handful of names re-exported here.
"""

from __future__ import annotations

from .graphify import (
    DEFAULT_BINARY,
    DEFAULT_TIMEOUT_S,
    GRAPH_DIR_NAME,
    GRAPH_FILE_NAME,
    CommandResult,
    ExplainResult,
    GodNode,
    GodNodesResult,
    Graph,
    GraphEdge,
    Graphify,
    GraphifyError,
    GraphifyTimeout,
    GraphNode,
    GraphStats,
    NodeConnection,
    PathResult,
    QueryResult,
    TraversalResult,
    graph_stats,
    read_graph,
    resolve_graph_path,
)
from .queries import (
    BATTERY,
    KINDS,
    Query,
    all_queries,
    dedupe,
    queries_for,
    render,
)
from . import policy
from .policy import (
    ADMISSION_SOURCES,
    GRAPHIFY_SOURCES,
    Admission,
    AssertionResult,
    PolicyAudit,
    PolicyDiff,
    PolicyError,
    PolicyWideningError,
    TargetPolicy,
    policy_audit,
    policy_diff,
)
from . import staging
from .staging import (
    DOC_EXTENSIONS,
    MANIFEST_NAME,
    MergedResult,
    SemanticResult,
    StagedFile,
    StagingCorpus,
    build_staging_corpus,
    combined_graph_report,
    merge_with_code_graph,
    normalize_xml,
    resolve_provenance,
    semantic_argv,
    semantic_ingest,
    staging_summary,
)

__all__ = [
    # graphify wrapper
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
    "NodeConnection",
    "PathResult",
    "QueryResult",
    "TraversalResult",
    "graph_stats",
    "read_graph",
    "resolve_graph_path",
    # query battery
    "BATTERY",
    "KINDS",
    "Query",
    "all_queries",
    "dedupe",
    "queries_for",
    "render",
    # staging + semantic ingest (U1.5)
    "staging",
    "DOC_EXTENSIONS",
    "MANIFEST_NAME",
    "StagedFile",
    "StagingCorpus",
    "SemanticResult",
    "MergedResult",
    "build_staging_corpus",
    "normalize_xml",
    "resolve_provenance",
    "staging_summary",
    "semantic_argv",
    "semantic_ingest",
    "merge_with_code_graph",
    "combined_graph_report",
    # admission policy (U1.7)
    "policy",
    "ADMISSION_SOURCES",
    "GRAPHIFY_SOURCES",
    "Admission",
    "AssertionResult",
    "PolicyAudit",
    "PolicyDiff",
    "PolicyError",
    "PolicyWideningError",
    "TargetPolicy",
    "policy_audit",
    "policy_diff",
]

"""Staleness & refresh engine (unit U7.1).

* :mod:`resextract.refresh.staleness` — measure the target, judge freshness.
* :mod:`resextract.refresh.review` — run the refresh: graph copy, link re-checks,
  manifest/history rewrites.
* :mod:`resextract.refresh.backlog` — turn findings into specific rework entries.

Every entry produced here is ``model_suggested=False`` unless it came from an
explicitly supplied LLM proposal: a measured fact must never be mistaken for a
model's suggestion.
"""

from .backlog import (
    BACKLOG_NAME,
    WORK_SUGGESTIONS_NAME,
    ReworkEntry,
    append_backlog,
    persist_rework,
    rework_entries,
    work_suggestions_text,
    write_work_suggestions,
)
from .review import (
    DocketRefresh,
    GraphRefresh,
    LinkCheck,
    RefreshReport,
    check_cited_links,
    classify_fetch,
    refresh_target,
)
from .staleness import (
    CHANGE_KINDS,
    FRESHNESS_STATES,
    ChangeReport,
    Freshness,
    TargetState,
    claim_provenance_files,
    detect_change,
    freshness_for,
    read_target_state,
)

__all__ = [
    "check_cited_links",
    "BACKLOG_NAME",
    "CHANGE_KINDS",
    "FRESHNESS_STATES",
    "WORK_SUGGESTIONS_NAME",
    "ChangeReport",
    "DocketRefresh",
    "Freshness",
    "GraphRefresh",
    "LinkCheck",
    "RefreshReport",
    "ReworkEntry",
    "TargetState",
    "append_backlog",
    "check_cited_links",
    "claim_provenance_files",
    "classify_fetch",
    "detect_change",
    "freshness_for",
    "persist_rework",
    "read_target_state",
    "refresh_target",
    "rework_entries",
    "work_suggestions_text",
    "write_work_suggestions",
]

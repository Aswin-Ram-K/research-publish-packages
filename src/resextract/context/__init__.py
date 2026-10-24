"""Context-state primitives for the context-cache experiment (unit U1).

Public surface (other units build on exactly these names):

* :class:`~.nodes.StateNode` -- immutable content-addressed state node.
* :func:`~.salt.make_salt` -- deterministic per-cell prefix salt.
* :class:`~.render.RenderPolicy`, :func:`~.render.render`,
  :func:`~.render.render_bytes` -- chain -> OpenAI messages.
* :class:`~.budget.CompactionPolicy`, :func:`~.budget.needs_compaction`,
  :func:`~.budget.compact` -- budget check and compaction (injected summariser).
* :class:`~.meter.CacheRow`, :class:`~.meter.CacheMeter`,
  :func:`~.meter.normalise_cache` -- metering rows and cache normalisation.
"""

from __future__ import annotations

from .budget import (
    CompactionPolicy,
    compact,
    default_est_tokens,
    is_fork_chain,
    needs_compaction,
)
from .meter import CacheMeter, CacheRow, normalise_cache, rows_from_jsonl
from .nodes import KINDS, StateNode, canonical_bytes, digest
from .render import RenderPolicy, first_message_bytes, render, render_bytes
from .salt import make_salt, salted

__all__ = [
    "KINDS",
    "StateNode",
    "canonical_bytes",
    "digest",
    "make_salt",
    "salted",
    "RenderPolicy",
    "render",
    "render_bytes",
    "first_message_bytes",
    "CompactionPolicy",
    "needs_compaction",
    "compact",
    "default_est_tokens",
    "is_fork_chain",
    "CacheRow",
    "CacheMeter",
    "normalise_cache",
    "rows_from_jsonl",
]
